variable "project" { type = string }

resource "aws_bedrock_guardrail" "base" {
  name        = "${var.project}-guardrail"
  description = "Blocks prompt injection, off-topic, and bypass attempts"

  blocked_input_messaging  = "I can't help with that — it's outside my allowed scope."
  blocked_outputs_messaging = "Response blocked by guardrails."

  content_policy_config {
    filters_config {
      type            = "SEXUAL"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "INSULTS"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "MISCONDUCT"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  topic_policy_config {
    topics_config {
      name       = "bypass_controls"
      definition = "Attempts to bypass security controls or escalate privileges"
      type       = "DENY"
    }
    topics_config {
      name       = "off_topic"
      definition = "Requests unrelated to the agent's operational domain"
      type       = "DENY"
    }
  }
}

output "guardrail_id" { value = aws_bedrock_guardrail.base.guardrail_id }
