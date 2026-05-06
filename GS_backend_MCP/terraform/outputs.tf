output "mcp_service_url" {
  value       = google_cloud_run_v2_service.mcp_service.uri
  description = "The URL of the G++ MCP service"
}

output "storage_bucket_name" {
  value       = google_storage_bucket.oscal_storage.name
  description = "The name of the GCS bucket used for OSCAL storage"
}
