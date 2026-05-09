# Unified Artifact Registry for all Agentic components
resource "google_artifact_registry_repository" "agentic_repo" {
  location      = var.region
  repository_id = "agentic-repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

# --- Shared Storage ---
resource "google_storage_bucket" "oscal_storage" {
  name                        = "${var.project_id}-oscal-storage"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
}

# --- Service Accounts ---

# 1. Backend MCP Service Account
resource "google_service_account" "backend_mcp_sa" {
  account_id   = "gpp-backend-mcp-sa"
  display_name = "G++ Backend MCP Service Account"
}

# Backend MCP needs RW access to the storage bucket
resource "google_storage_bucket_iam_member" "mcp_storage_admin" {
  bucket = google_storage_bucket.oscal_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend_mcp_sa.email}"
}

# 2. GSpp MCP Service Account
resource "google_service_account" "gspp_mcp_sa" {
  account_id   = "gspp-mcp-sa"
  display_name = "GSpp MCP Service Account"
}

# --- Backend MCP Deployment ---
resource "null_resource" "build_and_push_backend_mcp" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit ${path.module}/../GS_backend_MCP \
        --project ${var.project_id} \
        --config ${path.module}/../GS_backend_MCP/cloudbuild.yaml \
        --substitutions=_TAG=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-backend-mcp:latest
    EOT
  }

  depends_on = [
    google_artifact_registry_repository.agentic_repo,
    google_project_service.services
  ]
}

resource "google_cloud_run_v2_service" "backend_mcp_service" {
  name                = "gpp-backend-mcp"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.backend_mcp_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-backend-mcp:latest"

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

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [
    google_project_service.services,
    null_resource.build_and_push_backend_mcp
  ]
}

# Security: Only allow the ADK Agent identity to invoke the Backend MCP server.
resource "google_cloud_run_v2_service_iam_member" "backend_mcp_invoker" {
  location = google_cloud_run_v2_service.backend_mcp_service.location
  name     = google_cloud_run_v2_service.backend_mcp_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.app_sa.email}"
}

# --- GSpp MCP Deployment ---
resource "null_resource" "build_and_push_gspp_mcp" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit ${path.module}/../GSpp_MCP \
        --project ${var.project_id} \
        --tag ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gs-plus-plus-mcp:latest
    EOT
  }

  depends_on = [
    google_artifact_registry_repository.agentic_repo,
    google_project_service.services
  ]
}

resource "google_cloud_run_v2_service" "gspp_mcp_service" {
  name                = "gs-plus-plus-mcp"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.gspp_mcp_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gs-plus-plus-mcp:latest"

      ports {
        container_port = 8080
      }

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

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [
    google_project_service.services,
    null_resource.build_and_push_gspp_mcp
  ]
}

# Security: Only allow the ADK Agent identity to invoke the GSpp MCP server.
resource "google_cloud_run_v2_service_iam_member" "gspp_mcp_invoker" {
  location = google_cloud_run_v2_service.gspp_mcp_service.location
  name     = google_cloud_run_v2_service.gspp_mcp_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.app_sa.email}"
}

# --- Frontend Deployment ---
# 4. Frontend Service Account
resource "google_service_account" "frontend_sa" {
  account_id   = "gpp-frontend-sa"
  display_name = "G++ Frontend Service Account"
}

resource "null_resource" "build_and_push_frontend" {
  triggers = { always_run = timestamp() }
  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit ${path.module}/../frontend \
        --project ${var.project_id} \
        --tag ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-frontend:latest
    EOT
  }
  depends_on = [google_artifact_registry_repository.agentic_repo, google_project_service.services]
}

resource "google_cloud_run_v2_service" "frontend_service" {
  name                = "gpp-frontend"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.frontend_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-frontend:latest"
      ports { container_port = 3000 }
      resources { limits = { cpu = "1", memory = "512Mi" } }
      env {
        name = "AGENT_URL"
        # Reasoning engine agents deployed with ADK framework don't expose a /copilotkit route
        # automatically, but assuming ADK agent has logic for it or frontend logic changes later
        value = "https://${var.region}-aiplatform.googleapis.com/v1beta1/projects/${var.project_id}/locations/${var.region}/reasoningEngines/${google_vertex_ai_reasoning_engine.app.name}:query"
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [null_resource.build_and_push_frontend]
}

# Public access to Frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  location = google_cloud_run_v2_service.frontend_service.location
  name     = google_cloud_run_v2_service.frontend_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
