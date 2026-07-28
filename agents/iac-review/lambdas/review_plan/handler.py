"""Tool: review_plan — analyzes a Terraform plan JSON for risky changes."""

import json
import os
from datetime import datetime

import boto3

ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))

# Risk patterns to flag
RISKY_ACTIONS = {"delete", "destroy"}
RISKY_RESOURCE_TYPES = {
    "aws_iam_policy",
    "aws_iam_role_policy",
    "aws_iam_role",
    "aws_security_group",
    "aws_security_group_rule",
    "aws_s3_bucket_policy",
    "aws_s3_bucket_public_access_block",
    "aws_cloudtrail",
    "aws_guardduty_detector",
    "aws_config_configuration_recorder",
    "aws_kms_key",
    "aws_db_instance",
    "aws_rds_cluster",
}


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    plan_json = params.get("plan_json", "")

    if not plan_json:
        return {
            "response": "Please provide the Terraform plan JSON (output of `terraform show -json plan.tfplan`)."
        }

    try:
        plan = json.loads(plan_json) if isinstance(plan_json, str) else plan_json
        changes = plan.get("resource_changes", [])
        if not changes:
            return {"response": "No resource changes in this plan. Nothing to review."}

        findings = []
        summary = {"create": 0, "update": 0, "delete": 0}

        for rc in changes:
            actions = rc.get("change", {}).get("actions", [])
            res_type = rc.get("type", "")
            address = rc.get("address", "")

            for action in actions:
                if action in summary:
                    summary[action] += 1

            # Flag deletions
            if "delete" in actions:
                findings.append(
                    f"🔴 DELETE: {address} ({res_type}) — verify this is intentional"
                )

            # Flag sensitive resource changes
            if res_type in RISKY_RESOURCE_TYPES and any(
                a in ("update", "create") for a in actions
            ):
                after = rc.get("change", {}).get("after", {}) or {}
                # Check for IAM wildcards
                if "policy" in str(after).lower() and '"*"' in str(after):
                    findings.append(
                        f"⚠️ IAM WILDCARD: {address} — policy contains '*' (review scope)"
                    )
                elif res_type in ("aws_security_group_rule", "aws_security_group"):
                    if "0.0.0.0/0" in str(after):
                        findings.append(
                            f"⚠️ OPEN SG: {address} — opens to 0.0.0.0/0 (review port scope)"
                        )
                else:
                    findings.append(
                        f"⚠️ SENSITIVE CHANGE: {address} ({res_type}) — review carefully"
                    )

        lines = [
            f"Plan summary: +{summary['create']} ~{summary['update']} -{summary['delete']}"
        ]
        if not findings:
            lines.append("\n✅ No risky patterns detected. Plan looks safe to apply.")
        else:
            lines.append(f"\n{len(findings)} risk(s) flagged:")
            lines.extend(f"  {f}" for f in findings)
            lines.append("\nRecommendation: review each flagged item before applying.")

        result = "\n".join(lines)
    except json.JSONDecodeError:
        result = "Error: could not parse the plan JSON. Ensure it's the output of `terraform show -json`."
    except Exception as e:
        result = f"Error reviewing plan: {str(e)}"

    try:
        ddb.put_item(
            Item={
                "request_id": context.aws_request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tool": "review_plan",
                "findings_count": str(len(findings) if "findings" in dir() else 0),
                "result_preview": result[:500],
            }
        )
    except Exception:
        pass
    return {"response": result}
