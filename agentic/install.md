# gpp-agentic Ecosystem Installation Guide

This document details the setup of the entire `agentic` architecture on a local development machine. The system consists of three central Python components and a React/Next.js frontend.

## Architecture Overview

1. **`GSpp_MCP`**: The User MCP Server. Provides read-only access to BSI Grundschutz catalogs, controls, and OSCAL schemas.
2. **`GS_backend_MCP`**: The Backend MCP Server. Manages state, stores artifacts (via Google Cloud Storage - GCS), and performs strict OSCAL JSON validations.
3. **`gpp-agent`**: The central ADK (Agent Development Kit) Multi-Agent System that orchestrates workflows (such as the SSP Generator).
4. **`Frontend`** (CopilotKit / AG-UI): The interactive Human-in-the-Loop Web-Interface.

---

## Prerequisites

- **Python**: Version 3.12 or higher.
- **Node.js**: Version 20+ (for the future CopilotKit Frontend and ADK CLI Tools).
- **Google Cloud SDK (gcloud)**: For authentication against GCS and Cloud Trace.
- **uv (recommended)** or `pip` for fast Python dependency management.

---

## Step 1: Local Google Cloud Authentication

Since the `GS_backend_MCP` stores artifacts in the GCP Bucket and sends OpenTelemetry data to Cloud Trace, local Application Default Credentials (ADC) must be set.

```bash
# Login to Google Cloud and create application_default_credentials.json
gcloud auth application-default login

# Set project (replace YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID
```

---

## Step 2: Set up GSpp_MCP (User Catalog)

1. **Change to the directory**:
   ```bash
   cd agentic/GSpp_MCP
   ```
2. **Install dependencies**:
   Use `uv` for the best performance (or `pip install -e .`):
   ```bash
   uv venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/Mac:
   source .venv/bin/activate
   
   uv pip install -e .
   ```
3. **Configuration**:
   Create a `.env` file (if needed) based on a `.env.example`.
4. **Start the server**:
   Start the MCP Server in SSE mode (Server-Sent Events) for communication over HTTP (default port is usually 8080).
   ```bash
   # (Depending on the entry point defined in pyproject.toml)
   # Example:
   python -m server.main --transport sse --port 8080
   ```
5. **Verify installation**:
   Run the test script to ensure all MCP tools (user catalog) are functioning correctly.
   *(To do this, open a new terminal in the `GSpp_MCP` directory)*:
   ```bash
   ./scripts/test_all_tools.sh
   ```

---

## Step 3: Set up GS_backend_MCP (State & Storage)

1. **Change to the directory**:
   Open a new terminal.
   ```bash
   cd agentic/GS_backend_MCP
   ```
2. **Install dependencies**:
   ```bash
   uv venv
   # Windows:
   .venv\Scripts\activate
   
   uv pip install -e .
   ```
3. **Configuration**:
   Create a `.env` file:
   ```env
   # IMPORTANT: Define your GCP Bucket name here
   GCP_BUCKET_NAME=my-gspp-agent-bucket
   ```
4. **Start the server**:
   Start the Backend MCP Server in SSE mode on a different port (e.g. 8081).
   ```bash
   python -m myserver.main --transport sse --port 8081
   ```
5. **Verify installation**:
   Run the test script to test GCS storage and OSCAL schema validation.
   *(To do this, open a new terminal in the `GS_backend_MCP` directory)*:
   ```bash
   ./scripts/test_all_tools.sh
   ```

---

## Step 4: Set up gpp-agent (ADK System)

The gpp-agent connects to the two running MCP servers and executes the workflows.

1. **Change to the directory**:
   Open a third terminal.
   ```bash
   cd agentic/gpp-agent
   ```
2. **Install dependencies**:
   ```bash
   uv venv
   # Windows:
   .venv\Scripts\activate
   
   # This installs google-adk, pydantic, mcp[cli], etc.
   uv pip install -e .
   ```
3. **Configuration**:
   Copy the `.env.example` to `.env` and adjust the URLs:
   ```bash
   cp .env.example .env
   ```
   **Contents of `.env` (Example)**:
   ```env
   # MCP Server Endpoints (SSE)
   ANWENDER_MCP_URL=http://localhost:8080
   BACKEND_MCP_URL=http://localhost:8081
   
   # Agent Models
   ORCHESTRATOR_MODEL=gemini-3-flash-preview
   PRODUCER_MODEL=gemini-3.1-pro-preview
   REVIEWER_MODEL=gemini-3-flash-preview
   
   # API Keys
   GOOGLE_API_KEY=your-gemini-api-key
   
   # OpenTelemetry Project
   GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
   ```
4. **Test the agent via ADK Web**:
   Since the final frontend is still missing, we use the integrated ADK Web interface for local development tests.
   ```bash
   adk web --port 3000
   ```
   The agent is now accessible at `http://localhost:3000`.

---

## Step 5: Frontend Integration (CopilotKit / AG-UI) - *Future*

*Once the Next.js frontend is implemented, the steps will be:*

1. Change to a new directory in the root (e.g. `agentic/frontend`).
2. Install dependencies: `npm install`
3. Store connection URLs to the ADK Agent Server (`http://localhost:8000` by default via AG-UI/FastAPI) in the `.env.local`.
4. Start with `npm run dev`.

---

## Infrastructure Deployment (Terraform & Vertex AI)

If you want to deploy the system into production on the Google Cloud, use the provided Terraform scripts in the `agentic/terraform` directory.

The Terraform script automatically provisions the infrastructure. It builds the Docker images of the three Web/MCP components (`GSpp_MCP`, `GS_backend_MCP`, and `frontend`), pushes them to a new Artifact Registry, and deploys them as secure, independently scaling **Cloud Run Services**. The AI agent (`gpp-agent`) is deployed directly to **Vertex AI Agent Engine (Reasoning Engine)** using the Google ADK framework.

**IMPORTANT**: In a new subscription, the resource management API must first be enabled:

```bash
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com
```

In addition, dedicated Service Accounts, a GCS Bucket for the OSCAL artifacts, and precise IAM bindings are created following the *Zero Trust* principle:
- Only the agent is allowed to call the MCP servers.
- Only the frontend is allowed to call the agent.
- Only the frontend is publicly accessible (`allUsers`).

1. **Check prerequisites for Terraform**:
   Ensure that `terraform` is installed locally and that you are still logged into gcloud (`gcloud auth application-default login`).
2. **Change to the Terraform directory**:
   ```bash
   cd agentic/terraform
   ```
3. **Adjust variables**:
   Check the `variables.tf` (or create a `terraform.tfvars` file) and strictly set your `project_id`, `region`, and `allowed_user_emails` (users who are allowed to run the agent locally with cloud permissions).
4. **Initialize and apply Terraform**:
   ```bash
   terraform init
   
   # Shows which resources (Cloud Run, Buckets, SAs) will be created
   terraform plan
   
   # Executes the deployment (Docker builds are triggered via Cloud Build)
   terraform apply
   ```
5. **After Deployment (Deploy Real Agent & Configure Environment)**:
   After a successful `terraform apply`, the Reasoning Engine is initialized with a dummy source to break circular dependencies. To deploy your actual agent code and configure its connection to the newly created MCP services, run:
   ```bash
   ./scripts/deploy_gpp_agent.sh
   ```
   This script automatically reads the outputs from Terraform and deploys your local `app/` folder with the correct MCP URLs.

   To develop or test the agent locally while accessing the real, cloud-hosted MCP services, update the `.env` file in your local `agentic/gpp-agent` directory to point to the Cloud Run URLs:
   ```env
   ANWENDER_MCP_URL=https://gs-plus-plus-mcp-...a.run.app
   BACKEND_MCP_URL=https://gpp-backend-mcp-...a.run.app
   ```
   Since the Terraform code grants you (`allowed_user_emails`) the `roles/iam.serviceAccountTokenCreator` role on the agent service account, you can continue to run/develop the agent locally, but it now securely accesses the real, cloud-hosted backend systems.

---

## Fast Code Deployments (Without Terraform)

Terraform is ideal for the initial setup and changes to the infrastructure (IAM, databases, buckets). However, if you **only update the code** of a container, use the provided deployment scripts in the `agentic/scripts/` folder.

These scripts securely build your container image in the pre-configured `agentic-repo` and enforce an immediate new revision in the Cloud Run Service – without overwriting the Terraform state.

**Available Scripts:**
- `./scripts/deploy_frontend.sh`
- `./scripts/deploy_gpp_agent.sh`
- `./scripts/deploy_GS_backend_MCP.sh`
- `./scripts/deploy_GSpp_MCP.sh`

**Example: Frontend Update**
```bash
cd agentic
./scripts/deploy_frontend.sh
```
