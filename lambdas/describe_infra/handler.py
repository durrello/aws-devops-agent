"""Tool: describe_infrastructure — lists EC2, ECS, RDS, Lambda resources + health."""
import json
import os
from datetime import datetime

import boto3

ddb = boto3.resource("dynamodb").Table(os.environ["AUDIT_TABLE"])
ec2 = boto3.client("ec2")
ecs_client = boto3.client("ecs")
rds = boto3.client("rds")
lam = boto3.client("lambda")


def lambda_handler(event, context):
    params = event.get("parameters", [])
    param_map = {p["name"]: p["value"] for p in params}
    resource_type = param_map.get("resource_type", "all")

    sections = []

    try:
        if resource_type in ("all", "ec2"):
            instances = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}],
                MaxResults=20,
            )
            items = []
            for r in instances.get("Reservations", []):
                for i in r["Instances"]:
                    name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "—")
                    items.append(f"  {i['InstanceId']} ({i['InstanceType']}) — {i['State']['Name']} — {name}")
            sections.append(f"EC2 ({len(items)} instances):\n" + ("\n".join(items) or "  (none)"))

        if resource_type in ("all", "ecs"):
            clusters = ecs_client.list_clusters().get("clusterArns", [])
            sections.append(f"ECS: {len(clusters)} cluster(s): {', '.join(c.split('/')[-1] for c in clusters) or '(none)'}")

        if resource_type in ("all", "rds"):
            dbs = rds.describe_db_instances().get("DBInstances", [])
            items = [f"  {d['DBInstanceIdentifier']} ({d['Engine']}) — {d['DBInstanceStatus']}" for d in dbs]
            sections.append(f"RDS ({len(dbs)} instances):\n" + ("\n".join(items) or "  (none)"))

        if resource_type in ("all", "lambda"):
            fns = lam.list_functions(MaxItems=20).get("Functions", [])
            sections.append(f"Lambda: {len(fns)} function(s)")

        result = "\n\n".join(sections) or "No resources found."
    except Exception as e:
        result = f"Error describing infrastructure: {str(e)}"

    # Audit
    try:
        ddb.put_item(Item={
            "request_id": context.aws_request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tool": "describe_infra",
            "params": json.dumps(param_map),
            "result_preview": result[:500],
        })
    except Exception:
        pass

    return {"response": result}
