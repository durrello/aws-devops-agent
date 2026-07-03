"""Tool: gather_context — pulls logs + recent deployments to correlate with an alarm."""
import json
import os
import time
from datetime import datetime, timedelta

import boto3

logs = boto3.client("logs")
codedeploy = boto3.client("codedeploy")
ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    log_group = params.get("log_group", "")
    minutes_back = int(params.get("minutes_back", "60"))

    sections = []

    # Recent error logs
    if log_group:
        try:
            end_time = int(time.time() * 1000)
            start_time = end_time - (minutes_back * 60 * 1000)
            resp = logs.filter_log_events(
                logGroupName=log_group, startTime=start_time, endTime=end_time,
                filterPattern="ERROR", limit=10,
            )
            events = resp.get("events", [])
            if events:
                lines = [f"Recent errors in {log_group} (last {minutes_back}m):"]
                for e in events[:5]:
                    ts = datetime.fromtimestamp(e["timestamp"] / 1000).strftime("%H:%M:%S")
                    lines.append(f"  [{ts}] {e['message'].strip()[:150]}")
                sections.append("\n".join(lines))
            else:
                sections.append(f"No ERROR logs in {log_group} (last {minutes_back}m).")
        except Exception as e:
            sections.append(f"Log query failed: {e}")

    # Recent deployments (CodeDeploy)
    try:
        apps = codedeploy.list_applications().get("applications", [])[:3]
        for app in apps:
            deploys = codedeploy.list_deployments(
                applicationName=app, includeOnlyStatuses=["InProgress", "Succeeded", "Failed"],
                createTimeRange={"start": datetime.utcnow() - timedelta(hours=2)},
            ).get("deployments", [])[:2]
            if deploys:
                info = codedeploy.batch_get_deployments(deploymentIds=deploys)["deploymentsInfo"]
                for d in info:
                    sections.append(
                        f"Recent deploy: {app} → {d['status']} "
                        f"({d.get('completeTime', d.get('createTime', '?'))})")
    except Exception:
        pass  # CodeDeploy not in use — skip silently.

    result = "\n\n".join(sections) if sections else "No additional context found."

    try:
        ddb.put_item(Item={"request_id": context.aws_request_id,
                           "timestamp": datetime.utcnow().isoformat(),
                           "tool": "gather_context", "params": json.dumps(params),
                           "result_preview": result[:500]})
    except Exception:
        pass
    return {"response": result}
