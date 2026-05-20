# GSpp MCP Server Installation Guide

Welcome! This guide is designed to help you deploy the **BSI Grundschutz++ MCP Server** to Google Cloud Platform (GCP), even if you're a beginner.

This setup provides a fully serverless, secure (IAM-protected) endpoint for your AI agents to interact with the BSI Anwenderkatalog Grundschutz++.

---

## 🛠 Prerequisites

Before we start, you need a few things set up on your machine and on GCP:

1. **Google Cloud Account**: You need an active GCP account.
2. **GCP Project**: A dedicated GCP Project (e.g., `my-mcp-project-123`).
3. **Billing Enabled**: Cloud Run and Cloud Build require an active billing account linked to your project. (Don't worry, a single low-traffic instance easily fits in the free tier!)
4. **Google Cloud CLI (`gcloud`)**: [Install the gcloud CLI](https://cloud.google.com/sdk/docs/install) on your computer.
5. **Terraform**: [Install Terraform](https://developer.hashicorp.com/terraform/downloads) to automate the deployment. (We highly recommend this path, and it's what this guide focuses on).

---

## 🚀 Step 1: Authentication & Project Setup

First, we need to tell your local `gcloud` and `terraform` tools who you are and which project to use.

Open your terminal and run:

```bash
# Log in to your Google Cloud account
gcloud auth login

# Log in specifically for application tools (like Terraform)
gcloud auth application-default login

# Set your current project (replace with your actual project ID)
gcloud config set project your-project-id
```

---

## 🔌 Step 2: Ensure the Cloud Resource Manager API is Enabled

To allow Terraform or automated deployments to manage APIs in your project, you must first enable the **Cloud Resource Manager API** manually.

Run this command:

```bash
gcloud services enable cloudresourcemanager.googleapis.com
```

> **Note:** API enablement can take 1-2 minutes to propagate through Google's systems. If you encounter an error in the next steps, just wait a minute and try again.

---

## 🏗 Step 3: Deploying the Server

You have two options to deploy the MCP server: **Option A (Terraform)** which is fully automated, or **Option B (gcloud CLI)** which is faster if you prefer typing direct commands.

### Option A: Deployment via Terraform (Recommended)

We have provided a Terraform configuration that does **everything** for you:
1. Enables necessary APIs (`run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com`, etc.)
2. Creates an Artifact Registry to hold your Docker image.
3. **Automatically builds and pushes** the Docker image from your local source code.
4. Deploys the container to Cloud Run with a secure Service Account.

### Instructions:

1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```

2. Initialize Terraform (this downloads the necessary Google Cloud provider plugins):
   ```bash
   terraform init
   ```

3. Review the execution plan. Terraform will ask you for your `project_id` and the `region` (we recommend `europe-west3` for Frankfurt / EU Data Residency):
   ```bash
   terraform plan
   ```

4. Apply the configuration. You will be prompted for your variables again, and then asked to type `yes` to confirm:
   ```bash
   terraform apply
   ```

> **What happens during `terraform apply`?**
> You'll see Terraform creating the Artifact Registry, and then it will kick off a `gcloud builds submit` command. This packages up the code in the parent folder, sends it to Google Cloud Build, creates a container image, and saves it. Once the build finishes, Terraform continues and deploys the Cloud Run service.

When the process finishes, Terraform will output the secure URL of your new MCP server!

### Option B: Deployment via gcloud CLI

If you don't want to use Terraform, you can use the gcloud CLI to deploy directly from the source code.

1. Ensure the required APIs are enabled:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iam.googleapis.com
   ```

2. Create the necessary Service Account:
   ```bash
   gcloud iam service-accounts create gs-mcp-runtime \
     --display-name="GSpp MCP Runtime Service Account"
   ```

3. Deploy the service directly from the root of the GSpp_MCP directory (this uses Cloud Build behind the scenes):
   ```bash
   gcloud run deploy gs-plus-plus-mcp \
     --source . \
     --region europe-west3 \
     --allow-unauthenticated=false \
     --service-account gs-mcp-runtime@your-project-id.iam.gserviceaccount.com \
     --set-env-vars CATALOG_PATH=/app/data/Grundschutz++-catalog.json \
     --set-env-vars MAPPING_PATH=/app/data/zielobjekt_controls.json
   ```
   *(Be sure to replace `your-project-id` with your actual project ID)*

When the deployment is complete, gcloud will output the service URL.

---

## 🐛 Step 4: Troubleshooting Common Issues

### Error: `Error 403: Cloud Resource Manager API has not been used...`
**Cause:** Terraform is trying to enable APIs for you, but it doesn't have the permission to manage APIs yet.
**Fix:** Run `gcloud services enable cloudresourcemanager.googleapis.com`, wait a minute, and run `terraform apply` again.

### Error: `Image '...:latest' not found`
**Cause:** The Cloud Run service tried to deploy before the container image was built and stored in Artifact Registry.
**Fix:** We have updated the Terraform scripts to build the image automatically. If you still see this, ensure that your user account has permissions to use Cloud Build (`roles/cloudbuild.builds.editor`), and that the build step in Terraform didn't error out.

### Error: `Permission denied` when accessing the Cloud Run URL
**Cause:** By default, this service is **secure** and does not allow unauthenticated traffic.
**Fix:** This is intentional! Your agent/client will need to provide a Bearer Token (Identity Token) to call this service. You can test it locally using:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://YOUR_CLOUD_RUN_URL/healthz
```

---

## 🎉 You're Done!

You now have a running, securely deployed instance of the Grundschutz++ MCP Server. Your AI agents can now connect to it by passing the proper authentication tokens.