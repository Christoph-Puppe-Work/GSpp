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
  description = "The email address of the Gpp-Agent's dedicated Service Account"
}
