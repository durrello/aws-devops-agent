# Architecture — Shared Patterns Across All Agents

## The core pattern (every agent follows this)

```
Input (text) → Orchestrator → Bedrock Agent → Tool Lambdas → Response + Audit
                    ↓                              ↓
              Kill switch check              Guardrail filter
```

## Design decisions

| Decision | Rationale |
|----------|-----------|
| **One agent per domain** (not one mega-agent) | Smaller instruction set = more accurate tool selection. Easier to scope IAM per domain. |
| **Read-only by default** | The risk of an AI modifying prod is high. Start read-only; add write via an explicit opt-in + approval gate. |
| **DynamoDB for audit (not just CloudTrail)** | CloudTrail gives API-level logs; DynamoDB gives the *semantic* log: what was asked, what the agent decided, what it returned. Both are needed. |
| **SSM kill switch** | Faster than redeploying. One parameter change = agent disabled in seconds. |
| **Bedrock Guardrails** | Defense in depth: even if the agent's system prompt is bypassed, the guardrail layer blocks dangerous patterns at the model level. |
| **Claude 3 Haiku** | Cost-effective for operational queries ($0.00025/1K input tokens). Switch to Sonnet for complex analysis if needed. |
| **Lambda per tool** (not one monolith) | Each tool has its own IAM permission boundary. A compromised log-query Lambda can't touch deployments. |

## Adding a new agent

1. Create `agents/<name>/` with `terraform/`, `lambdas/`, `README.md`.
2. Define tool Lambdas (one per capability). Use the shared `audit-table` and `iam-base` modules.
3. Create the Bedrock Agent with an instruction specific to the domain.
4. Wire the Bedrock Guardrail (shared module).
5. Add to the root README table.

## Cost model

Bedrock pricing (Claude 3 Haiku, as of 2026):
- Input: $0.00025 / 1K tokens
- Output: $0.00125 / 1K tokens
- A typical query (500 input + 300 output tokens) ≈ $0.0005

100 queries/day × 30 days = $1.50/month in Bedrock alone. The rest (Lambda, DynamoDB, API GW) is free-tier.
