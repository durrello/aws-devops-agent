"""Tool: triage_findings — queries Security Hub for active CRITICAL/HIGH findings."""
import json
import os
from datetime import datetime

import boto3

sh = boto3.client("securityhub")
ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    severity = params.get("severity", "CRITICAL,HIGH").upper().split(",")
    max_results = int(params.get("max_results", "15"))

    try:
        filters = {
            "SeverityLabel": [{"Value": s.strip(), "Comparison": "EQUALS"} for s in severity],
            "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
            "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
        }
        resp = sh.get_findings(Filters=filters, MaxResults=max_results,
                               SortCriteria=[{"Field": "SeverityLabel", "SortOrder": "desc"}])
        findings = resp.get("Findings", [])
        if not findings:
            result = f"No active {'/'.join(severity)} findings in Security Hub. ✅"
        else:
            lines = [f"🔴 {len(findings)} active finding(s) ({'/'.join(severity)}):"]
            for f in findings:
                title = f.get("Title", "Untitled")[:80]
                sev = f.get("Severity", {}).get("Label", "?")
                resource = (f.get("Resources") or [{}])[0].get("Id", "?")[:60]
                lines.append(f"  [{sev}] {title}\n         Resource: {resource}")
            result = "\n".join(lines)
    except Exception as e:
        result = f"Error querying Security Hub: {str(e)}"

    try:
        ddb.put_item(Item={"request_id": context.aws_request_id,
                           "timestamp": datetime.utcnow().isoformat(),
                           "tool": "triage_findings", "params": json.dumps(params),
                           "result_preview": result[:500]})
    except Exception:
        pass
    return {"response": result}
