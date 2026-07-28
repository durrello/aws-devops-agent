variable "project" { type = string }

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

output "table_name" { value = aws_dynamodb_table.audit.name }
output "table_arn" { value = aws_dynamodb_table.audit.arn }
