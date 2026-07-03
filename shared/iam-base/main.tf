variable "project" { type = string }
variable "region" { type = string }
variable "account_id" { type = string }

# Agent execution role (Bedrock → invoke tool Lambdas)
resource "aws_iam_role" "agent" {
  name = "${var.project}-agent"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "bedrock.amazonaws.com" }, Action = "sts:AssumeRole",
      Condition = { StringEquals = { "aws:SourceAccount" = var.account_id } } }]
  })
}

resource "aws_iam_role_policy" "agent_invoke" {
  name = "invoke-tools"
  role = aws_iam_role.agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "lambda:InvokeFunction",
      Resource = "arn:aws:lambda:${var.region}:${var.account_id}:function:${var.project}-*" }]
  })
}

# Tool Lambda execution role (read-only baseline + audit write)
resource "aws_iam_role" "tool" {
  name = "${var.project}-tool"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "tool_logs" {
  role       = aws_iam_role.tool.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Kill switch
resource "aws_ssm_parameter" "enabled" {
  name  = "/${var.project}/enabled"
  type  = "String"
  value = "true"
  description = "Set to 'false' to instantly disable this agent"
}

output "agent_role_arn" { value = aws_iam_role.agent.arn }
output "tool_role_arn" { value = aws_iam_role.tool.arn }
output "tool_role_name" { value = aws_iam_role.tool.name }
output "kill_switch_name" { value = aws_ssm_parameter.enabled.name }
