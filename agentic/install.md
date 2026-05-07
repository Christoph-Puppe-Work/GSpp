# Gpp-Agentic Ecosystem Installation Guide

Dieses Dokument beschreibt detailliert die Einrichtung der gesamten `agentic` Architektur auf einer lokalen Entwicklungsmaschine. Das System besteht aus drei zentralen Python-Komponenten und (zukünftig) einem React/Next.js Frontend.

## Architektur-Überblick

1. **`GSpp_MCP`**: Der Anwender MCP Server. Stellt read-only Zugriff auf BSI Grundschutz Kataloge, Controls und OSCAL Schemas bereit.
2. **`GS_backend_MCP`**: Der Backend MCP Server. Verwaltet den Status (State), speichert Artefakte (via Google Cloud Storage - GCS) und führt strikte OSCAL JSON-Validierungen aus.
3. **`Gpp-Agent`**: Das zentrale ADK (Agent Development Kit) Multi-Agenten-System, das Workflows (wie den SSP-Generator) orchestriert.
4. **`Frontend`** (CopilotKit / AG-UI): Das interaktive Human-in-the-Loop Web-Interface (noch zu implementieren).

---

## Voraussetzungen

- **Python**: Version 3.12 oder höher.
- **Node.js**: Version 20+ (für das zukünftige CopilotKit Frontend und ADK CLI Tools).
- **Google Cloud SDK (gcloud)**: Zur Authentifizierung gegen GCS und Cloud Trace.
- **uv (empfohlen)** oder `pip` für schnelles Python Dependency Management.

---

## Schritt 1: Lokale Google Cloud Authentifizierung

Da der `GS_backend_MCP` Artefakte im GCP Bucket ablegt und OpenTelemetry-Daten an Cloud Trace gesendet werden, müssen lokale Application Default Credentials (ADC) gesetzt werden.

```bash
# Login in Google Cloud und Erstellung der application_default_credentials.json
gcloud auth application-default login

# Projekt setzen (ersetze DEIN_PROJEKT_ID)
gcloud config set project DEIN_PROJEKT_ID
```

---

## Schritt 2: GSpp_MCP (Anwenderkatalog) einrichten

1. **In das Verzeichnis wechseln**:
   ```bash
   cd agentic/GSpp_MCP
   ```
2. **Abhängigkeiten installieren**:
   Nutze `uv` für die beste Performance (oder `pip install -e .`):
   ```bash
   uv venv
   # Unter Windows:
   .venv\Scripts\activate
   # Unter Linux/Mac:
   source .venv/bin/activate
   
   uv pip install -e .
   ```
3. **Konfiguration**:
   Erstelle eine `.env` (falls benötigt) basierend auf einer `.env.example`.
4. **Server starten**:
   Starten des MCP Servers im SSE-Modus (Server-Sent Events) für die Kommunikation über HTTP (Standard-Port ist üblicherweise 8080).
   ```bash
   # (Abhängig vom in pyproject.toml definierten Entrypoint)
   # Beispiel:
   python -m server.main --transport sse --port 8080
   ```
5. **Installation verifizieren**:
   Führe das Test-Skript aus, um sicherzustellen, dass alle MCP-Tools (Anwenderkatalog) korrekt funktionieren.
   *(Öffne dazu ein neues Terminal im `GSpp_MCP` Verzeichnis)*:
   ```bash
   ./scripts/test_all_tools.sh
   ```

---

## Schritt 3: GS_backend_MCP (State & Storage) einrichten

1. **In das Verzeichnis wechseln**:
   Öffne ein neues Terminal.
   ```bash
   cd agentic/GS_backend_MCP
   ```
2. **Abhängigkeiten installieren**:
   ```bash
   uv venv
   # Windows:
   .venv\Scripts\activate
   
   uv pip install -e .
   ```
3. **Konfiguration**:
   Erstelle eine `.env` Datei:
   ```env
   # WICHTIG: Definiere hier deinen GCP Bucket Namen
   GCP_BUCKET_NAME=mein-gspp-agent-bucket
   ```
4. **Server starten**:
   Starten des Backend MCP Servers im SSE-Modus auf einem anderen Port (z.B. 8081).
   ```bash
   python -m myserver.main --transport sse --port 8081
   ```
5. **Installation verifizieren**:
   Führe das Test-Skript aus, um die GCS-Speicherung und OSCAL-Schema Validierung zu testen.
   *(Öffne dazu ein neues Terminal im `GS_backend_MCP` Verzeichnis)*:
   ```bash
   ./scripts/test_all_tools.sh
   ```

---

## Schritt 4: Gpp-Agent (ADK System) einrichten

Der Gpp-Agent verbindet sich mit den beiden laufenden MCP Servern und führt die Workflows aus.

1. **In das Verzeichnis wechseln**:
   Öffne ein drittes Terminal.
   ```bash
   cd agentic/Gpp-Agent
   ```
2. **Abhängigkeiten installieren**:
   ```bash
   uv venv
   # Windows:
   .venv\Scripts\activate
   
   # Dies installiert google-adk, pydantic, mcp[cli], etc.
   uv pip install -e .
   ```
3. **Konfiguration**:
   Kopiere die `.env.example` zu `.env` und passe die URLs an:
   ```bash
   cp .env.example .env
   ```
   **Inhalt der `.env` (Beispiel)**:
   ```env
   # MCP Server Endpoints (SSE)
   ANWENDER_MCP_URL=http://localhost:8080
   BACKEND_MCP_URL=http://localhost:8081
   
   # Agent Modelle
   ORCHESTRATOR_MODEL=gemini-3-flash-preview
   PRODUCER_MODEL=gemini-3.1-pro-preview
   REVIEWER_MODEL=gemini-3-flash-preview
   
   # API Keys
   GOOGLE_API_KEY=dein-gemini-api-key
   
   # OpenTelemetry Projekt
   GOOGLE_CLOUD_PROJECT=DEIN_PROJEKT_ID
   ```
4. **Testen des Agenten via ADK Web**:
   Da das finale Frontend noch fehlt, nutzen wir die integrierte ADK Web-Oberfläche für lokale Entwicklungstests.
   ```bash
   adk web --port 3000
   ```
   Der Agent ist nun unter `http://localhost:3000` erreichbar.

---

## Schritt 5: Frontend Integration (CopilotKit / AG-UI) - *Zukünftig*

*Sobald das Next.js Frontend implementiert ist, lauten die Schritte:*

1. In ein neues Verzeichnis im Root (z.B. `agentic/frontend`) wechseln.
2. Abhänigkeiten installieren: `npm install`
3. Verbindungs-URLs zum ADK Agent Server (`http://localhost:8000` standardmäßig über AG-UI/FastAPI) in der `.env.local` hinterlegen.
4. Starten mit `npm run dev`.

---

## Infrastruktur Deployment (Terraform & Cloud Run)

Wenn du das System produktiv in die Google Cloud deployen möchtest, nutze die bereitgestellten Terraform-Skripte im Verzeichnis `agentic/terraform`.

Das Terraform-Skript baut automatisch die Docker-Images aller vier Komponenten (`GSpp_MCP`, `GS_backend_MCP`, `Gpp-Agent` und `frontend`), pusht sie in eine neue Artifact Registry und deployed sie als sichere, unabhängig skalierende **Cloud Run Services**. 

**WICHTIG**: In einer neues Subscription muss erst die ressource management API aktiviert werden:

```bash
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com
```

Zudem werden dedizierte Service Accounts, ein GCS Bucket für die OSCAL Artefakte und präzise IAM-Bindungen erstellt nach dem *Zero Trust* Prinzip:
- Nur der Agent darf die MCP-Server aufrufen.
- Nur das Frontend darf den Agent aufrufen.
- Nur das Frontend ist öffentlich (`allUsers`) erreichbar.

1. **Voraussetzungen für Terraform prüfen**:
   Stelle sicher, dass `terraform` lokal installiert ist und du weiterhin in gcloud eingeloggt bist (`gcloud auth application-default login`).
2. **In das Terraform-Verzeichnis wechseln**:
   ```bash
   cd agentic/terraform
   ```
3. **Variablen anpassen**:
   Prüfe die `variables.tf` (bzw. erstelle eine `terraform.tfvars` Datei) und setze zwingend deine `project_id`, `region` und `allowed_user_emails` (Nutzer, die den Agenten lokal mit Cloud-Rechten ausführen dürfen).
4. **Terraform initialisieren und anwenden**:
   ```bash
   terraform init
   
   # Zeigt an, welche Ressourcen (Cloud Run, Buckets, SAs) erstellt werden
   terraform plan
   
   # Führt das Deployment durch (Docker Builds werden via Cloud Build getriggert)
   terraform apply
   ```
5. **Nach dem Deployment (Agent konfigurieren)**:
   Nach erfolgreichem `terraform apply` erhältst du (via `outputs.tf`) die Cloud Run URLs für beide MCP Server.
   Aktualisiere die `.env` Datei in deinem lokalen `Gpp-Agent` Verzeichnis, um nicht mehr auf localhost, sondern auf die Cloud Run Services zu verweisen:
   ```env
   ANWENDER_MCP_URL=https://gs-plus-plus-mcp-...a.run.app
   BACKEND_MCP_URL=https://gpp-backend-mcp-...a.run.app
   ```
   Da der Terraform-Code dir (`allowed_user_emails`) das Recht `roles/iam.serviceAccountTokenCreator` auf den `gpp_agent_sa` gibt, kannst du den Agenten weiterhin lokal via `adk web` entwickeln, aber er greift nun sicher auf die echten, in der Cloud gehosteten Backend-Systeme zu.

---

## Schnelle Code-Deployments (Ohne Terraform)

Terraform ist ideal für das initiale Setup und Änderungen an der Infrastruktur (IAM, Datenbanken, Buckets). Wenn du jedoch **nur den Code** eines Containers (z. B. Agent oder Frontend) aktualisierst, ist `terraform apply` sehr langsam. Zudem wird eine bestehende `:latest` Version in Cloud Run durch Terraform oft nicht neu gezogen, wenn sich der Tag-Name nicht ändert.

Nutze für schnelle Entwicklungszyklen (Fast-Deployments) den direkten `gcloud` Befehl. Dieser lädt deinen Code hoch, baut das Image via Cloud Build und erzwingt eine sofortige neue Revision im Cloud Run Service – ohne den Terraform-State zu überschreiben (Terraform ignoriert Image-Updates dank spezieller `lifecycle` Blöcke in der `main.tf`).

**Beispiel: Update des Gpp-Agenten**
```bash
cd agentic/Gpp-Agent
gcloud run deploy gpp-agent --source . --region europe-west3
```

**Beispiel: Update des Frontends**
```bash
cd agentic/frontend
gcloud run deploy gpp-frontend --source . --region europe-west3
```

*(Passe die `--region` an, falls du nicht in `europe-west3` deployt hast).*
