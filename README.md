# AWS DevOps Agent — AI-Powered Infrastructure Operations (with Guardrails)

A production-grade reference implementation of an **AI agent that can execute DevOps operations
on AWS** — check deployments, query logs, describe infrastructure, and run approved actions —
all through natural language, with proper security guardrails baked in.

> **This is NOT a toy demo.** It addresses the real question: "What happens when AI agents get
> production access?" The answer: they need the same controls as any other operator — least
> privilege, audit trails, approval gates, and kill switches.

## Why this exists

AI agents in production infrastructure are inevitable. The question isn't whether teams will
use them — it's whether they'll be deployed safely or recklessly. This project demonstrates
the responsible path: an agent that's genuinely useful while being auditable, scoped, and
human-supervised for anything destructive.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  User (Slack / CLI / API Gateway)                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ natural language request
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator Lambda                                             │
│  - Authenticates the caller (IAM / API key)                      │
│  - Invokes Bedrock Agent with the request                        │
│  - Enforces guardrails before returning/acting                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AWS Bedrock Agent (Claude 3 / Titan)                            │
│  - Interprets the request                                        │
│  - Selects which tool(s) to call                                 │
│  - Generates a response / action plan                            │
└───────────┬───────────┬───────────┬───────────┬─────────────────┘
            │           │           │           │
            ▼           ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐
│ Tool:        │ │ Tool:        │ │ Tool:        │ │ Tool:             │
│ check_deploy │ │ query_logs   │ │ describe_    │ │ run_action        │
│ (read-only)  │ │ (read-only)  │ │ infra        │ │ (APPROVAL GATE)   │
│              │ │              │ │ (read-only)  │ │ → human confirms  │
└─────────────┘ └─────────────┘ └─────────────┘ └──────────────────┘

All tool executions → DynamoDB audit log + CloudTrail
```

## Security model (the guardrails)

| Layer | What it does | Why |
|-------|-------------|-----|
| **IAM (least privilege)** | Agent's execution role has read-only by default; write actions go through a separate, scoped role assumed only after approval | A compromised agent can't modify anything without the approval gate |
| **Bedrock Guardrails** | Content filters block prompt injection, toxic output, and requests to bypass controls | The agent can't be tricked into acting outside its scope |
| **Approval gate** | Any write/destructive action (restart, scale, deploy) pauses and requires human confirmation (Slack button / API call) | Humans stay in the loop for anything irreversible |
| **Audit log** | Every agent invocation, tool call, and action is logged to DynamoDB + CloudTrail | Full traceability — who asked, what the agent did, when |
| **Kill switch** | A single SSM parameter (`/devops-agent/enabled`) can disable the agent instantly | Circuit breaker for incidents or unexpected behavior |

## Tools the agent can use

| Tool | Access | What it does |
|------|--------|-------------|
| `check_deployment_status` | Read | Checks CodeDeploy / ECS service status |
| `query_cloudwatch_logs` | Read | Searches recent logs for errors/patterns |
| `describe_infrastructure` | Read | Lists EC2, ECS, RDS, Lambda resources + health |
| `suggest_fix` | Read | Analyzes an error and suggests remediation (no action) |
| `run_approved_action` | Write (gated) | Executes an approved action (scale, restart, rollback) — **requires human confirmation** |

## When to use this (and when NOT to)

### ✅ Good use cases
- **Triage**: "What's failing in prod right now?" — agent queries logs + deployment status, surfaces the answer in seconds instead of you clicking through 5 consoles.
- **Onboarding**: new team members ask natural-language questions about the infrastructure.
- **Off-hours first response**: agent diagnoses and *proposes* a fix; on-call engineer approves with one click instead of full investigation.
- **Routine checks**: "Is anything unhealthy?" — a scheduled sweep that reports to Slack.

### ❌ When NOT to use this
- **No guardrails deployed**: if you skip the approval gate, the agent becomes an unaudited root user. Don't.
- **Compliance-heavy environments (initially)**: until you prove the audit trail satisfies your auditors, keep the agent read-only.
- **As a replacement for understanding**: the agent is a tool, not a team member. If nobody understands the infrastructure it's operating on, you can't verify its answers.
- **Cost-sensitive tight loops**: every Bedrock invocation costs ~$0.003–0.01. A chatty integration calling the agent 1000x/day = $3–10/day. Fine for humans asking questions; expensive for automated loops.

### The risk spectrum

```
SAFE ──────────────────────────────────────────────────── DANGEROUS

Read-only     Read + suggest     Read + approved-write    Auto-write
(this default) (with guardrails)  (human in loop)         (NO guardrails)
                                                          ← never do this
```

This project defaults to read-only. Write access is opt-in, gated, and logged.

## Cost estimate

| Resource | Monthly cost (low-traffic) |
|----------|--------------------------|
| Bedrock (Claude 3 Haiku, ~100 invocations/day) | ~$3–5 |
| Lambda (orchestrator + tools) | ~$0 (free tier) |
| DynamoDB (audit log) | ~$0 (free tier) |
| API Gateway | ~$0 (free tier) |
| CloudWatch Logs | ~$0.50 |
| **Total** | **~$4–6/month** |

For a team of 5 engineers using it a few times daily. Scales linearly with usage.

## Project structure

```
devops-agent/
├── README.md                     # this file
├── terraform/                    # IaC for the full stack
│   ├── main.tf                   # orchestrator, API Gateway, DynamoDB
│   ├── bedrock.tf                # Bedrock Agent + Guardrails
│   ├── tools.tf                  # tool Lambda functions
│   ├── iam.tf                    # least-privilege roles
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── lambdas/                      # tool implementations (Python)
│   ├── orchestrator/
│   ├── check_deployment/
│   ├── query_logs/
│   ├── describe_infra/
│   └── run_action/
├── docs/
│   ├── SECURITY.md               # detailed security model + threat model
│   ├── WHEN-TO-USE.md            # expanded guidance
│   └── COST-ANALYSIS.md
└── .github/workflows/
    └── validate.yml              # CI: lint + terraform validate
```

## Quick start

```bash
cd terraform
terraform init
terraform plan -var="region=us-east-1"
terraform apply
```

Then invoke:
```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id $(terraform output -raw agent_id) \
  --session-id "test-1" \
  --input-text "What's failing in production right now?"
```

## Related

- Blog: [When AI Agents Get Production Access](https://devops.com/when-ai-agents-get-production-access-the-next-big-devops-risk/) (DevOps.com)
- Blog: [AWS Security Done Right](https://durrellgemuh.com/blog/aws-security-done-right-services-and-habits/)
- AWS docs: [Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

## License

MIT

---

*Built by [Durrell Gemuh](https://durrellgemuh.com) — DevOps & Cloud Infrastructure Engineer,
AWS Community Builder (Cloud Operations). Demonstrating that AI in production operations requires
the same rigor as any other privileged access: least privilege, audit trails, and human oversight.*
