output "api_endpoint" {
  description = "API Gateway endpoint — POST /ask with {\"input\": \"your question\"}"
  value       = "${aws_apigatewayv2_api.agent.api_endpoint}/ask"
}

output "agent_id" {
  description = "Bedrock Agent ID"
  value       = aws_bedrockagent_agent.devops.id
}

output "agent_alias_id" {
  description = "Bedrock Agent Alias ID (for invoke-agent calls)"
  value       = aws_bedrockagent_agent_alias.live.id
}

output "audit_table" {
  description = "DynamoDB audit log table name"
  value       = aws_dynamodb_table.audit.name
}

output "kill_switch_param" {
  description = "SSM parameter to disable the agent (set to 'false')"
  value       = aws_ssm_parameter.enabled.name
}
