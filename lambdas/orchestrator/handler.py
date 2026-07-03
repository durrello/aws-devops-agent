"""Orchestrator Lambda — receives HTTP requests, checks the kill switch, invokes the
Bedrock Agent, and logs the interaction to DynamoDB."""
import json
import os
import uuid
from datetime import datetime

import boto3

AGENT_ID = os.environ["AGENT_ID"]
ALIAS_ID = os.environ["AGENT_ALIAS_ID"]
AUDIT_TABLE = os.environ["AUDIT_TABLE"]
KILL_SWITCH = os.environ["KILL_SWITCH"]

bedrock = boto3.client("bedrock-agent-runtime")
ssm = boto3.client("ssm")
ddb = boto3.resource("dynamodb").Table(AUDIT_TABLE)


def lambda_handler(event, context):
    # Kill switch check
    try:
        enabled = ssm.get_parameter(Name=KILL_SWITCH)["Parameter"]["Value"]
        if enabled.lower() != "true":
            return respond(503, {"error": "DevOps Agent is currently disabled (kill switch)."})
    except Exception:
        pass  # If we can't read the switch, proceed (fail-open for reads; tighten if needed).

    # Parse input
    body = json.loads(event.get("body") or "{}")
    user_input = body.get("input", "").strip()
    if not user_input:
        return respond(400, {"error": "Missing 'input' field."})

    request_id = str(uuid.uuid4())
    session_id = body.get("session_id", request_id)

    # Invoke Bedrock Agent
    try:
        response = bedrock.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=session_id,
            inputText=user_input,
        )
        # Stream the response chunks
        output_text = ""
        for event_chunk in response.get("completion", []):
            chunk = event_chunk.get("chunk", {})
            if "bytes" in chunk:
                output_text += chunk["bytes"].decode("utf-8")
    except Exception as e:
        output_text = f"Agent error: {str(e)}"

    # Audit log
    try:
        ddb.put_item(Item={
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "input": user_input[:1000],
            "output": output_text[:2000],
            "source_ip": event.get("requestContext", {}).get("http", {}).get("sourceIp", "unknown"),
        })
    except Exception:
        pass  # Don't fail the request if audit write fails (log it separately).

    return respond(200, {"request_id": request_id, "output": output_text})


def respond(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
