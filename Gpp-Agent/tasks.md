# Projektstatus: Grundschutz++ Multi-Agent Tooling

## ✅ Erledigt (Done)

- **Basis-Infrastruktur**:
  - Komplette Verzeichnisstruktur gemäß Spezifikation angelegt.
  - `pyproject.toml` und `requirements.txt` mit fixierten Abhängigkeiten (`google-adk`, `mcp`, `pydantic`, etc.).
  - Deployment-Konfiguration (`Dockerfile`, `cloud_run.yaml`) und `.env.example` erstellt.
- **Multi-Tenancy & Sicherheit**:
  - `InformationsverbundGcsArtifactService`: Pfad-Namespacing implementiert, um Datenlecks zwischen Informationsverbünden (IV) zu verhindern.
  - `InformationsverbundSessionService`: GCS-basierte Session-Persistenz mit strikter IV-Trennung.
- **Agenten-Architektur**:
  - **Root Orchestrator**: Implementiert mit IV-Resolution-Logik und Delegation an Sub-Workflows.
  - **CIS→OSCAL Workflow**: Implementiert als `SequentialAgent` mit integriertem `LoopAgent` für Peer-Reviews.
  - **Vendor Evidence Workflow**: Struktur für Extraktion und Mapping steht.
  - **Policy Generator Workflow**: Implementiert mit `ParallelAgent` zur gleichzeitigen Bearbeitung der 17 Kontroll-Domänen.
- **Tools & Integration**:
  - **BSI G++ MCP Toolset**: Factory-Funktion unterstützt `stdio` und `sse` Modi.
  - **Review-Mechanismus**: `exit_loop`-Tool ermöglicht es dem Reviewer-Agenten, den Workflow bei Erfolg abzuschließen.
- **Qualitätssicherung**:
  - Unit-Tests für Artifact-Service, Session-Service und Orchestrator-Tools erfolgreich implementiert.
  - Integration-Smoke-Tests zur Validierung der Agenten-Initialisierung.

## ❌ Offen (To Do / Missing)

- **Fachliche Implementierung (Logik)**:
  - **GCS Input Loading**: Die Tools zum Laden von Dateien (z.B. `load_cis_input`) nutzen derzeit Mocks. Die reale Anbindung an den GCS-Bucket für User-Uploads muss finalisiert werden.
  - **Prompt Engineering**: Die Instruktionen in den `producer.py`-Dateien sind derzeit Platzhalter. Diese müssen in `shared/prompts/` ausgelagert und für die spezifischen Domänen (CIS-Mapping, Evidence-Extraktion) optimiert werden.
  - **OSCAL-Vollständigkeit**: Die `OscalComponentDefinition`-Schemas sind vereinfachte Pydantic-Modelle. Eine vollständige Abbildung gegen das offizielle OSCAL-Metaschema (1.1.2) steht noch aus.
  - **PDF-Generierung**: Der Policy-Generator exportiert aktuell Markdown-Entwürfe. Die Konvertierung in finale PDFs (z.B. via `weasyprint`) ist noch nicht integriert.
- **Infrastruktur & Betrieb**:
  - **Authentifizierung**: Die Integration eines Auth-Providers (z.B. GCP IAP) vor dem Orchestrator ist noch offen.
  - **Audit Logging**: Ein persistentes Audit-Log der Agenten-Entscheidungen außerhalb des Session-States fehlt noch.
  - **MCP Tool-Filtering**: Verfeinerung der Tool-Verfügbarkeit pro Agent (z.B. Reviewer benötigt keine Schreibrechte), um die Tool-Surface zu minimieren.
- **Tests & Validierung**:
  - **Tenant-Isolation Test**: Ein automatisierter Test, der zwei parallele IV-Sessions simuliert und auf Null-Leckage prüft.
  - **End-to-End Integration**: Vollständiger Durchlauf mit einem echten/gemockten BSI-G++-MCP-Server zur Validierung der semantischen Korrektheit des Mappings.
