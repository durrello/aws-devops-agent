"""Tool: check_deployment_status — queries CodeDeploy or ECS service deployments."""

import json
import os
from datetime import datetime

import boto3

ddb = boto3.resource("dynamodb").Table(os.environ["AUDIT_TABLE"])
codedeploy = boto3.client("codedeploy")
ecs = boto3.client("ecs")


def lambda_handler(event, context):
    """Bedrock Agent tool invocation — receives parameters, returns findings."""
    params = event.get("parameters", [])
    param_map = {p["name"]: p["value"] for p in params}
    service_type = param_map.get("service_type", "ecs")  # "ecs" or "codedeploy"
    cluster = param_map.get("cluster", "")
    service = param_map.get("service", "")

    try:
        if service_type == "ecs" and cluster and service:
            resp = ecs.describe_services(cluster=cluster, services=[service])
            svcs = resp.get("services", [])
            if not svcs:
                result = f"No ECS service '{service}' found in cluster '{cluster}'."
            else:
                s = svcs[0]
                result = (
                    f"ECS service '{s['serviceName']}' in cluster '{cluster}':\n"
                    f"  Status: {s['status']}\n"
                    f"  Running tasks: {s['runningCount']} / desired: {s['desiredCount']}\n"
                    f"  Latest deployment: {s['deployments'][0]['status'] if s.get('deployments') else 'N/A'}\n"
                    f"  Health: {'HEALTHY' if s['runningCount'] == s['desiredCount'] else 'DEGRADED'}"
                )
        elif service_type == "codedeploy":
            deploys = codedeploy.list_deployments(
                applicationName=param_map.get("application", ""),
                includeOnlyStatuses=["InProgress", "Succeeded", "Failed"],
            )
            ids = deploys.get("deployments", [])[:3]
            if not ids:
                result = "No recent CodeDeploy deployments found."
            else:
                details = codedeploy.batch_get_deployments(deploymentIds=ids)[
                    "deploymentsInfo"
                ]
                lines = []
                for d in details:
                    lines.append(
                        f"  {d['deploymentId']}: {d['status']} ({d.get('completeTime', 'in progress')})"
                    )
                result = "Recent CodeDeploy deployments:\n" + "\n".join(lines)
        else:
            result = "Please specify service_type ('ecs' or 'codedeploy') and relevant parameters."
    except Exception as e:
        result = f"Error checking deployment: {str(e)}"

    # Audit
    try:
        ddb.put_item(
            Item={
                "request_id": context.aws_request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tool": "check_deployment",
                "params": json.dumps(param_map),
                "result_preview": result[:500],
            }
        )
    except Exception:
        pass

    return {"response": result}
