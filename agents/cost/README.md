# Cost Agent — AI-powered FinOps on AWS Bedrock

An AI agent that analyzes your AWS spend, detects anomalies, and recommends cost optimizations
through natural language — backed by the Cost Explorer API with guardrails.

## Tools

| Tool | What it does |
|------|-------------|
| `analyze_cost` | Pulls Cost Explorer data for a service/period, summarizes spend + trends |
| `detect_anomaly` | Queries Cost Anomaly Detection for unusual charges |
| `recommend_savings` | Identifies unused resources + reservation/savings plan opportunities |

## Example queries
- "What are my top 3 spending services this month?"
- "Are there any cost anomalies in the last 7 days?"
- "Which EC2 instances are underutilized?"

## Deploy

> **Note:** Terraform for this agent is planned. Currently only the
> [devops agent](../devops/) has full Terraform. The Lambda code here is ready to integrate
> into the shared architecture.
