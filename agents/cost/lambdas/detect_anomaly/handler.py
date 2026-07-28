"""Tool: detect_anomaly — queries AWS Cost Anomaly Detection for unusual charges."""

import json
import os
from datetime import datetime, timedelta

import boto3

ce = boto3.client("ce")
ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    days_back = int(params.get("days_back", "7"))

    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        resp = ce.get_anomalies(
            DateInterval={"StartDate": start, "EndDate": end},
            MaxResults=10,
        )
        anomalies = resp.get("Anomalies", [])
        if not anomalies:
            result = f"No cost anomalies detected in the last {days_back} days. ✅"
        else:
            lines = [
                f"⚠️ {len(anomalies)} cost anomaly/anomalies detected (last {days_back} days):"
            ]
            for a in anomalies:
                impact = a.get("Impact", {})
                total = impact.get("TotalImpact", 0)
                svc = a.get("RootCauses", [{}])[0].get("Service", "Unknown")
                lines.append(
                    f"  ${total:.2f} unexpected spend — {svc} ({a.get('AnomalyId', '')[:8]})"
                )
            result = "\n".join(lines)
    except Exception as e:
        result = f"Error querying anomalies: {str(e)}"

    try:
        ddb.put_item(
            Item={
                "request_id": context.aws_request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tool": "detect_anomaly",
                "params": json.dumps(params),
                "result_preview": result[:500],
            }
        )
    except Exception:
        pass
    return {"response": result}
