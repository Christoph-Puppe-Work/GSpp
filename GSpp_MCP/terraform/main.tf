resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "mcp_repo" {
  location      = var.region
  repository_id = "mcp-server-repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.required_apis]
}

resource "google_service_account" "mcp_runtime_sa" {
  account_id   = "gs-mcp-runtime"
  display_name = "GSpp MCP Runtime Service Account"
}

resource "google_cloud_run_v2_service" "mcp_service" {
  name     = "gs-plus-plus-mcp"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.mcp_runtime_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.mcp_repo.repository_id}/gs-plus-plus-mcp:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "CATALOG_PATH"
        value = "/app/GSpp_MCP/data/Grundschutz++-catalog.json"
      }
      env {
        name  = "MAPPING_PATH"
        value = "/app/GSpp_MCP/data/zielobjekt_controls.json"
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Public access for the MCP service.
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.mcp_service.location
  name     = google_cloud_run_v2_service.mcp_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
