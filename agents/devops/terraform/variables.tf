variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "devops-agent"
}

variable "bedrock_model_id" {
  description = "Bedrock foundation model ID (e.g. anthropic.claude-3-haiku-20240307-v1:0)"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "enable_write_actions" {
  description = "Whether to deploy the write-action tool (requires approval gate). Set false for read-only mode."
  type        = bool
  default     = false
}

variable "approval_slack_webhook" {
  description = "Slack webhook URL for approval notifications (optional; leave empty to skip)"
  type        = string
  default     = ""
  sensitive   = true
}
