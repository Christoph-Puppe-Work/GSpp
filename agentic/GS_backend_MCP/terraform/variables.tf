variable "project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "region" {
  type        = string
  description = "The GCP region to deploy to"
  default     = "europe-west3"
}

variable "agent_service_account" {
  type        = string
  description = "The service account email of the Gpp-Agent to allow invocation"
  default     = ""
}
