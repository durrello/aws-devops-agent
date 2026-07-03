# Incident Agent — AI-powered alarm triage & context gathering

An AI agent for SRE/incident response — triages CloudWatch alarms, gathers relevant context
(logs, metrics, recent changes), and drafts initial runbook steps.

## Tools

| Tool | What it does |
|------|-------------|
| `triage_alarm` | Reads a CloudWatch alarm state, pulls recent datapoints, assesses severity |
| `gather_context` | Given an alarm, pulls related logs + recent deployments for correlation |

## Example queries
- "Alarm X just fired — what's happening?"
- "Gather context for the high-CPU alarm on the API service"
- "What changed in the last hour that could have caused this?"
