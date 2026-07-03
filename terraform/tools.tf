# ─────────────────────────────────────────────────────────────────────────────
# Tool Lambdas — each is a capability the agent can invoke.
# All share the read-only execution role. Audit every call.
# ─────────────────────────────────────────────────────────────────────────────

# ── check_deployment ─────────────────────────────────────────────────────────

data "archive_file" "check_deployment" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/check_deployment"
  output_path = "${path.module}/.build/check_deployment.zip"
}

resource "aws_lambda_function" "check_deployment" {
  function_name    = "${var.project}-check-deployment"
  role             = aws_iam_role.tool_readonly.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.check_deployment.output_path
  source_code_hash = data.archive_file.check_deployment.output_base64sha256

  environment {
    variables = {
      AUDIT_TABLE = aws_dynamodb_table.audit.name
    }
  }
  tags = { Project = var.project }
}

# ── query_logs ───────────────────────────────────────────────────────────────

data "archive_file" "query_logs" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/query_logs"
  output_path = "${path.module}/.build/query_logs.zip"
}

resource "aws_lambda_function" "query_logs" {
  function_name    = "${var.project}-query-logs"
  role             = aws_iam_role.tool_readonly.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.query_logs.output_path
  source_code_hash = data.archive_file.query_logs.output_base64sha256

  environment {
    variables = {
      AUDIT_TABLE = aws_dynamodb_table.audit.name
    }
  }
  tags = { Project = var.project }
}

# ── describe_infra ───────────────────────────────────────────────────────────

data "archive_file" "describe_infra" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/describe_infra"
  output_path = "${path.module}/.build/describe_infra.zip"
}

resource "aws_lambda_function" "describe_infra" {
  function_name    = "${var.project}-describe-infra"
  role             = aws_iam_role.tool_readonly.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.describe_infra.output_path
  source_code_hash = data.archive_file.describe_infra.output_base64sha256

  environment {
    variables = {
      AUDIT_TABLE = aws_dynamodb_table.audit.name
    }
  }
  tags = { Project = var.project }
}
