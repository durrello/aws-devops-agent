# IaC Review Agent — AI-powered Terraform plan analysis

An AI agent that reviews Terraform plans before `apply` — flags risky changes (IAM wildcards,
security group openings, resource deletions) and explains the risk in plain language.

## Tools

| Tool | What it does |
|------|-------------|
| `review_plan` | Parses a Terraform plan JSON, identifies risky resource changes, explains each |

## Example queries
- "Review this plan — is it safe to apply?"
- "What resources are being destroyed?"
- "Are there any IAM policy changes I should worry about?"

## How it works
1. Run `terraform plan -out=plan.tfplan && terraform show -json plan.tfplan > plan.json`
2. Upload `plan.json` to the agent (via API or S3 trigger)
3. The agent analyzes the JSON, flags risks, and explains each in natural language

## Risk patterns it detects
- IAM policies with `*` actions or `*` resources
- Security groups opening 0.0.0.0/0 on sensitive ports
- Resource deletions (especially databases, KMS keys)
- Changes to CloudTrail, GuardDuty, or Config (disabling guardrails)
- S3 bucket policy changes that could expose data
