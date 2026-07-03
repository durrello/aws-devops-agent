# Security Model & Threat Model

## Threat: prompt injection
An attacker crafts input that makes the agent ignore its instructions and execute unintended actions.

**Mitigations:**
- Bedrock Guardrails with `PROMPT_ATTACK` filter (HIGH sensitivity)
- Topic denial rules blocking "bypass controls" and "escalate privileges"
- Tools are scoped: even if the agent is tricked, the Lambda can only do what its IAM role allows
- Write actions require human confirmation (the agent can't auto-execute them)

## Threat: over-privileged agent
The agent's IAM role is too broad, so a compromised or confused agent can access/modify too much.

**Mitigations:**
- Tool Lambda roles are **read-only by default** — no modify/delete permissions
- Each tool has its own Lambda (and could have its own role if needed)
- Write actions go through a **separate role** assumed only after approval
- Resource ARNs are scoped (not `*`) wherever the API supports it

## Threat: unaudited actions
The agent does something unexpected and nobody can trace what happened.

**Mitigations:**
- Every invocation → DynamoDB audit (semantic: what was asked, what was done)
- Every API call → CloudTrail (technical: which AWS APIs were called)
- Both together give full traceability

## Threat: agent enabled when it shouldn't be
During an incident or unexpected behavior, the agent needs to be stopped instantly.

**Mitigations:**
- SSM Parameter kill switch: set to `false` → agent returns 503 on next call
- Can be automated: a CloudWatch alarm could trigger a Lambda that flips the switch

## Threat: cost runaway
The agent is invoked in a loop (accidental or malicious), running up Bedrock costs.

**Mitigations:**
- API Gateway throttling (configurable requests/second)
- Bedrock has per-model invocation quotas (adjustable in Service Quotas)
- The audit table makes volume visible; set a CloudWatch alarm on DynamoDB writes
- Budget alerts in AWS Budgets catch unexpected spend early

## The residual risk (be honest about this)
- The agent can return wrong/hallucinated information. It's a tool, not an authority.
- Read-only access still exposes infrastructure details to anyone who can invoke the API.
  → Secure the API (IAM auth, VPC-only, or at minimum an API key).
- Bedrock Guardrails are strong but not perfect. Novel jailbreaks appear regularly.
  → Defense in depth (guardrails + IAM + audit + kill switch) means no single bypass is fatal.
