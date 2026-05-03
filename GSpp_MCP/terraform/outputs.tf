output "service_url" {
  value = google_cloud_run_v2_service.mcp_service.uri
}

output "artifact_registry_repo" {
  value = google_artifact_registry_repository.mcp_repo.name
}

output "service_account_email" {
  value = google_service_account.mcp_runtime_sa.email
}
