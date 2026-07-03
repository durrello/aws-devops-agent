"""Tool: query_cloudwatch_logs — searches recent log events for errors/patterns."""
import json
import os
import time
from datetime import datetime

import boto3

ddb = boto3.resource("dynamodb").Table(os.environ["AUDIT_TABLE"])
logs = boto3.client("logs")


def lambda_handler(event, context):
    params = event.get("parameters", [])
    param_map = {p["name"]: p["value"] for p in params}
    log_group = param_map.get("log_group", "")
    pattern = param_map.get("pattern", "ERROR")
    minutes_back = int(param_map.get("minutes_back", "30"))

    if not log_group:
        return {"response": "Please specify a 'log_group' to search."}

    try:
        end_time = int(time.time() * 1000)
        start_time = end_time - (minutes_back * 60 * 1000)

        resp = logs.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            filterPattern=pattern,
            limit=20,
        )
        events = resp.get("events", [])
        if not events:
            result = f"No log events matching '{pattern}' in {log_group} (last {minutes_back} min)."
        else:
            lines = [f"Found {len(events)} event(s) matching '{pattern}' in {log_group}:"]
            for e in events[:10]:
                ts = datetime.fromtimestamp(e["timestamp"] / 1000).strftime("%H:%M:%S")
                msg = e["message"].strip()[:200]
                lines.append(f"  [{ts}] {msg}")
            if len(events) > 10:
                lines.append(f"  ... and {len(events) - 10} more")
            result = "\n".join(lines)
    except Exception as e:
        result = f"Error querying logs: {str(e)}"

    # Audit
    try:
        ddb.put_item(Item={
            "request_id": context.aws_request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tool": "query_logs",
            "params": json.dumps(param_map),
            "result_preview": result[:500],
        })
    except Exception:
        pass

    return {"response": result}
