# AWS DevOps Agents

A collection of **production-ready AI agents for cloud operations** — built on AWS Bedrock with
proper security guardrails. Each agent is self-contained, scoped to a specific operations domain,
and follows the same safe-by-default architecture.

> **Not toy demos.** Every agent has: least-privilege IAM, an audit trail (DynamoDB), a kill switch
> (SSM Parameter), Bedrock Guardrails (content filtering + topic blocking), and read-only defaults.
> Write actions require explicit human approval.

## The Agent Roster

| Agent | Domain | What it does |
|-------|--------|-------------|
| [`devops`](agents/devops/) | Infrastructure Ops | Check deployments, query logs, describe resources |
| [`cost`](agents/cost/) | FinOps | Analyze spend, detect anomalies, recommend savings |
| [`security`](agents/security/) | Security Ops | Triage Security Hub findings, analyze GuardDuty alerts |
| [`incident`](agents/incident/) | SRE / Incident Response | Triage CloudWatch alarms, gather context, draft runbook |
| [`iac-review`](agents/iac-review/) | IaC Safety | Review Terraform plans, flag risky changes before apply |

## Shared Architecture

All agents follow the same pattern:

```
User → API Gateway → Orchestrator Lambda → Bedrock Agent (Claude 3)
                                                 ↓
                                          Tool Lambdas (domain-specific)
                                                 ↓
                                          DynamoDB audit + CloudTrail
```

**Shared modules** (in `shared/`) provide reusable Terraform for:
- `audit-table/` — DynamoDB table for agent action logging
- `guardrails/` — base Bedrock Guardrail configuration
- `iam-base/` — common IAM patterns (read-only tool role, agent role)

## Security model (applies to ALL agents)

| Layer | Control |
|-------|---------|
| IAM | Read-only by default; write via a separate approval-gated role |
| Bedrock Guardrails | Block prompt injection, off-topic, and bypass attempts |
| Approval gate | Destructive actions pause for human confirmation |
| Audit log | Every invocation + tool call → DynamoDB + CloudTrail |
| Kill switch | SSM parameter → instantly disable any agent |

## When to use / when NOT to

### ✅ Good use cases
- Triage and diagnosis (read, analyze, suggest — the agent thinks, the human acts)
- Off-hours first response (agent gathers context; on-call engineer approves with one click)
- Onboarding (new team members ask natural-language questions about the infra)
- Routine sweeps (scheduled "is anything unhealthy / overspending / exposed?")

### ❌ When NOT to
- Without guardrails deployed (an ungated agent is an unaudited root user)
- As a replacement for understanding (you must be able to verify its answers)
- In automated tight loops (each Bedrock call costs ~$0.003–0.01; loops get expensive)
- For compliance sign-off (the agent assists; a human signs)

## Quick start

The **devops** agent has full Terraform ready to deploy. The remaining agents (cost, security,
incident, iac-review) include their Lambda code and documentation; Terraform for those is planned.

```bash
cd agents/devops/terraform
terraform init
terraform plan -var="region=us-east-1"
terraform apply
```

## Cost estimate (per agent, low-traffic)

| Resource | ~Monthly |
|----------|----------|
| Bedrock (Claude 3 Haiku, ~100 calls/day) | $3–5 |
| Lambda | ~$0 (free tier) |
| DynamoDB | ~$0 (free tier) |
| API Gateway | ~$0 (free tier) |
| Total | **~$4–6/agent** |

## Repo structure

```
aws-devops-agent/
├── README.md               ← this file
├── shared/                 ← reusable Terraform modules
│   ├── audit-table/
│   ├── guardrails/
│   └── iam-base/
├── agents/
│   ├── devops/             ← infrastructure operations
│   ├── cost/               ← FinOps / cost analysis
│   ├── security/           ← Security Hub / GuardDuty triage
│   ├── incident/           ← alarm triage + context
│   └── iac-review/         ← Terraform plan review
└── docs/
    ├── ARCHITECTURE.md
    ├── SECURITY.md
    └── WHEN-TO-USE.md
```

## Related

- [AWS Security Done Right](https://durrellgemuh.com/blog/aws-security-done-right-services-and-habits/)
- [When AI Agents Get Production Access](https://devops.com/when-ai-agents-get-production-access-the-next-big-devops-risk/) (DevOps.com)
- [AWS Bedrock Agents docs](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

## License

MIT

---

---

<div align="center">

### Built by

**Durrell Gemuh** - Founder @ NextGen Playground | DevOps & Cloud Infrastructure Engineer | AWS Community Builder

[![Portfolio](https://img.shields.io/badge/Portfolio-durrellgemuh.com-000?style=flat-square&logo=vercel)](https://durrellgemuh.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-durrello-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/durrello/)
[![Dev.to](https://img.shields.io/badge/Dev.to-durrello-0A0A0A?style=flat-square&logo=devdotto)](https://dev.to/durrello)
[![X](https://img.shields.io/badge/X-@durrelloo-000?style=flat-square&logo=x)](https://x.com/durrelloo)
[![GitHub](https://img.shields.io/badge/GitHub-durrello-181717?style=flat-square&logo=github)](https://github.com/durrello)
[![Email](https://img.shields.io/badge/Email-durrell.gemuh.a@gmail.com-EA4335?style=flat-square&logo=gmail)](mailto:durrell.gemuh.a@gmail.com)

---

⭐ **Star this repo** if you found it useful - it helps others discover it!

</div>
