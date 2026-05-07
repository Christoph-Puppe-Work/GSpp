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
    "storage.googleapis.com",
    "firestore.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Unified Artifact Registry for all Agentic components
resource "google_artifact_registry_repository" "agentic_repo" {
  location      = var.region
  repository_id = "agentic-repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.required_apis]
}

# --- Database ---
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# --- Shared Storage ---
resource "google_storage_bucket" "oscal_storage" {
  name     = "${var.project_id}-oscal-storage"
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = false
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

# 3. Gpp-Agent (ADK) Service Account
resource "google_service_account" "gpp_agent_sa" {
  account_id   = "gpp-agent-sa"
  display_name = "G++ Agent (ADK) Service Account"
}

# Allow authorized users to generate tokens for the Gpp-Agent service account
# This effectively grants them the identity of the agent when interacting via ADK
resource "google_service_account_iam_binding" "agent_token_creator" {
  service_account_id = google_service_account.gpp_agent_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"

  members = [
    for email in var.allowed_user_emails : "user:${email}"
  ]
}

# Grant the Gpp-Agent SA read/write access to Firestore
resource "google_project_iam_member" "agent_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.gpp_agent_sa.email}"
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
    google_project_service.required_apis
  ]
}

resource "google_cloud_run_v2_service" "backend_mcp_service" {
  name     = "gpp-backend-mcp"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
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

  depends_on = [
    google_project_service.required_apis,
    null_resource.build_and_push_backend_mcp
  ]
}

# Security: Only allow the ADK Agent identity to invoke the Backend MCP server.
resource "google_cloud_run_v2_service_iam_member" "backend_mcp_invoker" {
  location = google_cloud_run_v2_service.backend_mcp_service.location
  name     = google_cloud_run_v2_service.backend_mcp_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.gpp_agent_sa.email}"
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
    google_project_service.required_apis
  ]
}

resource "google_cloud_run_v2_service" "gspp_mcp_service" {
  name     = "gs-plus-plus-mcp"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
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

  depends_on = [
    google_project_service.required_apis,
    null_resource.build_and_push_gspp_mcp
  ]
}

# Security: Only allow the ADK Agent identity to invoke the GSpp MCP server.
resource "google_cloud_run_v2_service_iam_member" "gspp_mcp_invoker" {
  location = google_cloud_run_v2_service.gspp_mcp_service.location
  name     = google_cloud_run_v2_service.gspp_mcp_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.gpp_agent_sa.email}"
}

# --- Gpp-Agent Deployment ---
resource "null_resource" "build_and_push_agent" {
  triggers = { always_run = timestamp() }
  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit ${path.module}/../Gpp-Agent \
        --project ${var.project_id} \
        --tag ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-agent:latest
    EOT
  }
  depends_on = [google_artifact_registry_repository.agentic_repo, google_project_service.required_apis]
}

resource "google_cloud_run_v2_service" "gpp_agent_service" {
  name     = "gpp-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.gpp_agent_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-agent:latest"
      ports { container_port = 8000 }
      resources { limits = { cpu = "2", memory = "2Gi" } }
      env {
        name  = "ANWENDER_MCP_URL"
        value = google_cloud_run_v2_service.gspp_mcp_service.uri
      }
      env {
        name  = "BACKEND_MCP_URL"
        value = google_cloud_run_v2_service.backend_mcp_service.uri
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
    }
  }
  depends_on = [null_resource.build_and_push_agent]
}

# 4. Frontend Service Account
resource "google_service_account" "frontend_sa" {
  account_id   = "gpp-frontend-sa"
  display_name = "G++ Frontend Service Account"
}

# Security: Only Frontend can invoke ADK Agent
resource "google_cloud_run_v2_service_iam_member" "agent_invoker" {
  location = google_cloud_run_v2_service.gpp_agent_service.location
  name     = google_cloud_run_v2_service.gpp_agent_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.frontend_sa.email}"
}

# --- Frontend Deployment ---
resource "null_resource" "build_and_push_frontend" {
  triggers = { always_run = timestamp() }
  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit ${path.module}/../frontend \
        --project ${var.project_id} \
        --tag ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-frontend:latest
    EOT
  }
  depends_on = [google_artifact_registry_repository.agentic_repo, google_project_service.required_apis]
}

resource "google_cloud_run_v2_service" "frontend_service" {
  name     = "gpp-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.frontend_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentic_repo.repository_id}/gpp-frontend:latest"
      ports { container_port = 3000 }
      resources { limits = { cpu = "1", memory = "512Mi" } }
      env {
        name  = "AGENT_URL"
        value = "${google_cloud_run_v2_service.gpp_agent_service.uri}/copilotkit"
      }
    }
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
