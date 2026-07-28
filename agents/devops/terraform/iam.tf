# ─────────────────────────────────────────────────────────────────────────────
# IAM — the security backbone. Every role is scoped to exactly what it needs.
# ─────────────────────────────────────────────────────────────────────────────

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.region
}

# ── Bedrock Agent execution role ─────────────────────────────────────────────
# What the agent itself can do. Read-only by default; write goes through
# a separate assumed role (approval-gated).

resource "aws_iam_role" "agent" {
  name = "${var.project}-agent"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = local.account_id }
      }
    }]
  })
}

resource "aws_iam_role_policy" "agent_invoke_tools" {
  name = "invoke-tool-lambdas"
  role = aws_iam_role.agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = "arn:aws:lambda:${local.region}:${local.account_id}:function:${var.project}-*"
    }]
  })
}

# ── Tool Lambda execution role (read-only tools) ─────────────────────────────

resource "aws_iam_role" "tool_readonly" {
  name = "${var.project}-tool-readonly"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "tool_readonly_logs" {
  role       = aws_iam_role.tool_readonly.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "tool_readonly_ops" {
  name = "read-only-ops"
  role = aws_iam_role.tool_readonly.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DescribeInfra"
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "ecs:Describe*", "ecs:List*",
          "rds:Describe*",
          "lambda:List*", "lambda:GetFunction",
          "codedeploy:GetDeployment", "codedeploy:List*",
          "elasticloadbalancing:Describe*",
          "autoscaling:Describe*",
        ]
        Resource = "*"
      },
      {
        Sid    = "QueryLogs"
        Effect = "Allow"
        Action = [
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
        ]
        Resource = "arn:aws:logs:${local.region}:${local.account_id}:log-group:*"
      },
      {
        Sid      = "ReadSSMParam"
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:${local.region}:${local.account_id}:parameter/${var.project}/*"
      },
    ]
  })
}

# ── Audit log: DynamoDB write from tools ─────────────────────────────────────

resource "aws_iam_role_policy" "tool_readonly_audit" {
  name = "write-audit-log"
  role = aws_iam_role.tool_readonly.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem"]
      Resource = aws_dynamodb_table.audit.arn
    }]
  })
}

# ── Kill switch (SSM Parameter) ──────────────────────────────────────────────

resource "aws_ssm_parameter" "enabled" {
  name  = "/${var.project}/enabled"
  type  = "String"
  value = "true"

  description = "Set to 'false' to instantly disable the DevOps Agent (kill switch)"
}

# The orchestrator Lambda needs bedrock:InvokeAgent to call the Bedrock Agent.
resource "aws_iam_role_policy" "tool_readonly_bedrock" {
  name = "invoke-bedrock-agent"
  role = aws_iam_role.tool_readonly.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["bedrock:InvokeAgent"]
      Resource = "arn:aws:bedrock:${data.aws_region.current.region}:${local.account_id}:agent-alias/${aws_bedrockagent_agent.devops.id}/*"
    }]
  })
}

# The Bedrock Agent needs to invoke the foundation model.
resource "aws_iam_role_policy" "agent_invoke_model" {
  name = "invoke-foundation-model"
  role = aws_iam_role.agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
      Resource = "arn:aws:bedrock:${data.aws_region.current.region}::foundation-model/${var.bedrock_model_id}"
    }]
  })
}
