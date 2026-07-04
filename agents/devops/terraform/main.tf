# ─────────────────────────────────────────────────────────────────────────────
# Core infrastructure: API Gateway, DynamoDB audit table, orchestrator Lambda.
# ─────────────────────────────────────────────────────────────────────────────

# ── DynamoDB audit log ───────────────────────────────────────────────────────

resource "aws_dynamodb_table" "audit" {
  name         = "${var.project}-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  range_key    = "timestamp"

  attribute {
    name = "request_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = { Project = var.project }
}

# ── API Gateway (HTTP API — lightweight, low-cost) ───────────────────────────

resource "aws_apigatewayv2_api" "agent" {
  name          = var.project
  protocol_type = "HTTP"
  description   = "DevOps Agent API — invoke via natural language"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.agent.id
  name        = "$default"
  auto_deploy = true
}

# ── Orchestrator Lambda (receives requests, invokes Bedrock Agent) ────────────

data "archive_file" "orchestrator" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/orchestrator"
  output_path = "${path.module}/.build/orchestrator.zip"
}

resource "aws_lambda_function" "orchestrator" {
  function_name    = "${var.project}-orchestrator"
  role             = aws_iam_role.tool_readonly.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256
  filename         = data.archive_file.orchestrator.output_path
  source_code_hash = data.archive_file.orchestrator.output_base64sha256

  environment {
    variables = {
      AGENT_ID       = aws_bedrockagent_agent.devops.id
      AGENT_ALIAS_ID = aws_bedrockagent_agent_alias.live.agent_alias_id
      AUDIT_TABLE    = aws_dynamodb_table.audit.name
      KILL_SWITCH    = aws_ssm_parameter.enabled.name
    }
  }

  tags = { Project = var.project }
}

resource "aws_lambda_permission" "apigw" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orchestrator.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.agent.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "orchestrator" {
  api_id                 = aws_apigatewayv2_api.agent.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.orchestrator.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "invoke" {
  api_id    = aws_apigatewayv2_api.agent.id
  route_key = "POST /ask"
  target    = "integrations/${aws_apigatewayv2_integration.orchestrator.id}"
}
