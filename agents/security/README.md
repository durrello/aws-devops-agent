# Security Agent — AI-powered Security Hub & GuardDuty triage

An AI agent that triages Security Hub findings and GuardDuty alerts through natural language —
prioritize what to fix, understand the risk, and get remediation guidance.

## Tools

| Tool | What it does |
|------|-------------|
| `triage_findings` | Queries Security Hub for active CRITICAL/HIGH findings, groups + explains them |
| `check_guardduty` | Pulls recent GuardDuty findings, assesses severity + recommended actions |

## Example queries
- "What are my critical Security Hub findings?"
- "Are there any active GuardDuty threats?"
- "Explain finding X and how to fix it"

## Deploy

> **Note:** Terraform for this agent is planned. Currently only the
> [devops agent](../devops/) has full Terraform. The Lambda code here is ready to integrate
> into the shared architecture.
