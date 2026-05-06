variable "project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "region" {
  type        = string
  description = "The GCP region to deploy to"
  default     = "europe-west3"
}

variable "allowed_user_emails" {
  type        = list(string)
  description = "A list of email addresses allowed to interact with the ADK agent via impersonation"
  default     = []
}
