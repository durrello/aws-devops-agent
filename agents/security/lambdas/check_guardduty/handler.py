"""Tool: check_guardduty — pulls recent GuardDuty findings with severity + action guidance."""
import json
import os
from datetime import datetime

import boto3

gd = boto3.client("guardduty")
ddb = boto3.resource("dynamodb").Table(os.environ.get("AUDIT_TABLE", ""))


def lambda_handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}

    try:
        # Get the detector ID (there's usually one per region)
        detectors = gd.list_detectors().get("DetectorIds", [])
        if not detectors:
            return {"response": "GuardDuty is not enabled in this region."}

        detector_id = detectors[0]
        # Get recent findings (sorted by severity)
        finding_ids = gd.list_findings(
            DetectorId=detector_id,
            SortCriteria={"AttributeName": "severity", "OrderBy": "DESC"},
            MaxResults=10,
        ).get("FindingIds", [])

        if not finding_ids:
            return {"response": "No active GuardDuty findings. ✅"}

        findings = gd.get_findings(DetectorId=detector_id, FindingIds=finding_ids).get("Findings", [])
        lines = [f"⚠️ {len(findings)} GuardDuty finding(s):"]
        for f in findings:
            sev = f.get("Severity", 0)
            sev_label = "HIGH" if sev >= 7 else "MEDIUM" if sev >= 4 else "LOW"
            title = f.get("Title", "")[:80]
            resource_type = f.get("Resource", {}).get("ResourceType", "?")
            lines.append(f"  [{sev_label} ({sev:.1f})] {title}\n         Resource: {resource_type}")
        result = "\n".join(lines)
    except Exception as e:
        result = f"Error querying GuardDuty: {str(e)}"

    try:
        ddb.put_item(Item={"request_id": context.aws_request_id,
                           "timestamp": datetime.utcnow().isoformat(),
                           "tool": "check_guardduty", "params": json.dumps(params),
                           "result_preview": result[:500]})
    except Exception:
        pass
    return {"response": result}
