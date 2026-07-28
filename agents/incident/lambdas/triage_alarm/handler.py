"""Tool: triage_alarm — reads a CloudWatch alarm state + recent datapoints."""

import json
import os
from datetime import datetime, timedelta

import boto3

cw = boto3.client("cloudwatch")
ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    alarm_name = params.get("alarm_name", "")

    if not alarm_name:
        return {"response": "Please specify an 'alarm_name' to triage."}

    try:
        alarms = cw.describe_alarms(AlarmNames=[alarm_name]).get("MetricAlarms", [])
        if not alarms:
            return {"response": f"Alarm '{alarm_name}' not found."}

        alarm = alarms[0]
        state = alarm["StateValue"]
        metric = alarm.get("MetricName", "?")
        namespace = alarm.get("Namespace", "?")
        threshold = alarm.get("Threshold", "?")

        # Get recent datapoints
        end = datetime.utcnow()
        start = end - timedelta(hours=1)
        stats = cw.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric,
            StartTime=start,
            EndTime=end,
            Period=300,
            Statistics=["Average", "Maximum"],
            Dimensions=alarm.get("Dimensions", []),
        )
        datapoints = sorted(stats.get("Datapoints", []), key=lambda d: d["Timestamp"])

        lines = [
            f"Alarm: {alarm_name}",
            f"  State: {state}",
            f"  Metric: {namespace}/{metric}",
            f"  Threshold: {threshold} ({alarm.get('ComparisonOperator', '?')})",
            f"  Last {len(datapoints)} datapoints (1h, 5m intervals):",
        ]
        for dp in datapoints[-6:]:
            ts = dp["Timestamp"].strftime("%H:%M")
            lines.append(
                f"    {ts} — avg: {dp.get('Average', 0):.2f}, max: {dp.get('Maximum', 0):.2f}"
            )

        if state == "ALARM":
            lines.append(f"\n  ⚠️ ACTIVE — metric is breaching threshold ({threshold}).")
        else:
            lines.append(f"\n  ✅ Currently {state}.")
        result = "\n".join(lines)
    except Exception as e:
        result = f"Error triaging alarm: {str(e)}"

    try:
        ddb.put_item(
            Item={
                "request_id": context.aws_request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tool": "triage_alarm",
                "params": json.dumps(params),
                "result_preview": result[:500],
            }
        )
    except Exception:
        pass
    return {"response": result}
