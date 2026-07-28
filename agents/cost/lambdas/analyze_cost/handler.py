"""Tool: analyze_cost — queries Cost Explorer for spend by service/period."""

import json
import os
from datetime import datetime, timedelta

import boto3

ce = boto3.client("ce")
ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    days_back = int(params.get("days_back", "30"))
    granularity = params.get("granularity", "MONTHLY")

    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity=granularity,
            Metrics=["BlendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        # Aggregate by service
        services = {}
        for period in resp.get("ResultsByTime", []):
            for group in period.get("Groups", []):
                svc = group["Keys"][0]
                amt = float(group["Metrics"]["BlendedCost"]["Amount"])
                services[svc] = services.get(svc, 0) + amt

        # Sort by spend
        ranked = sorted(services.items(), key=lambda x: x[1], reverse=True)[:10]
        total = sum(services.values())
        lines = [f"AWS spend last {days_back} days: ${total:.2f}", "Top services:"]
        for svc, amt in ranked:
            pct = (amt / total * 100) if total > 0 else 0
            lines.append(f"  ${amt:.2f} ({pct:.0f}%) — {svc}")
        result = "\n".join(lines)
    except Exception as e:
        result = f"Error querying Cost Explorer: {str(e)}"

    # Audit
    try:
        ddb.put_item(
            Item={
                "request_id": context.aws_request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tool": "analyze_cost",
                "params": json.dumps(params),
                "result_preview": result[:500],
            }
        )
    except Exception:
        pass
    return {"response": result}
