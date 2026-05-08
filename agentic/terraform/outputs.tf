output "backend_mcp_url" {
  value       = google_cloud_run_v2_service.backend_mcp_service.uri
  description = "The URL of the Backend MCP server"
}

output "gspp_mcp_url" {
  value       = google_cloud_run_v2_service.gspp_mcp_service.uri
  description = "The URL of the GSpp MCP server"
}

output "oscal_storage_bucket" {
  value       = google_storage_bucket.oscal_storage.name
  description = "The name of the GCS bucket used for OSCAL storage"
}

output "gpp_agent_service_account_email" {
  value       = google_service_account.gpp_agent_sa.email
  description = "The email address of the gpp_agent's dedicated Service Account"
}

output "gpp_agent_url" {
  value       = google_cloud_run_v2_service.gpp_agent_service.uri
  description = "The URL of the gpp_agent ADK API Server"
}

output "frontend_url" {
  value       = google_cloud_run_v2_service.frontend_service.uri
  description = "The public URL of the G++ Frontend Dashboard"
}

output "project_id" {
  value       = var.project_id
  description = "The configured GCP Project ID"
}

output "region" {
  value       = var.region
  description = "The configured GCP Region"
}
