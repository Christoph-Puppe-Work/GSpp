provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_storage_bucket" "oscal_storage" {
  name     = "${var.project_id}-oscal-storage"
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = false
}

resource "google_artifact_registry_repository" "gpp_backend_mcp" {
  location      = var.region
  repository_id = "mcp-server-repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.required_apis]
}

resource "null_resource" "build_and_push_image" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit ${path.module}/../.. \
        --project ${var.project_id} \
        --config ${path.module}/cloudbuild.yaml \
        --substitutions=_TAG=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gpp_backend_mcp.repository_id}/gpp-backend-mcp:latest
    EOT
  }

  depends_on = [
    google_artifact_registry_repository.gpp_backend_mcp,
    google_project_service.required_apis
  ]
}

resource "google_service_account" "mcp_runtime_sa" {
  account_id   = "gpp-mcp-runtime"
  display_name = "G++ MCP Runtime Service Account"
}

resource "google_storage_bucket_iam_member" "mcp_storage_admin" {
  bucket = google_storage_bucket.oscal_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mcp_runtime_sa.email}"
}

resource "google_cloud_run_v2_service" "mcp_service" {
  name     = "gpp-backend-mcp"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.mcp_runtime_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gpp_backend_mcp.repository_id}/gpp-backend-mcp:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "BUCKET_NAME"
        value = google_storage_bucket.oscal_storage.name
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    null_resource.build_and_push_image
  ]
}

# Security: Only allow authorized Agent identities to invoke this MCP server.
# Ensure Gpp-Agent's service account is added here.
resource "google_cloud_run_v2_service_iam_member" "invoker" {
  location = google_cloud_run_v2_service.mcp_service.location
  name     = google_cloud_run_v2_service.mcp_service.name
  role     = "roles/run.invoker"
  member   = var.agent_service_account != "" ? "serviceAccount:${var.agent_service_account}" : "allUsers"
}
