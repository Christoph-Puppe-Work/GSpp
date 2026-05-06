# Gpp-Agent Tasks & Progress

## Erledigte Aufgaben (Completed)
- [x] **Projekt-Setup & Infrastruktur:**
  - [x] `pyproject.toml` mit Abhängigkeiten (`google-adk`, `mcp`, `pydantic`, etc.) erstellt.
  - [x] `.env.example` Vorlage erstellt.
  - [x] Verzeichnisstruktur (`agents/`, `services/`, `tools/`, `shared/`, `tests/`) initialisiert.
  - [x] `__init__.py` Dateien zur Paket-Erkennung hinzugefügt.
- [x] **Kern-Services:**
  - [x] Duale `McpClientService`-Architektur (`GSpp_MCP` für BSI-Katalog und `GS_backend_MCP` für State & Speicherung) implementiert.
  - [x] Lokaler `temp_file_service` für sicheres Handling von Datei-Uploads implementiert.
  - [x] GCS und Schema-Validierung an den `GS_backend_MCP` ausgelagert.
- [x] **Infrastruktur & Shared:**
  - [x] `EscalationBarrier` zur ADK-Loop-Steuerung implementiert.
  - [x] `exit_loop` Utility für saubere Loop-Terminierung.
  - [x] OpenTelemetry Observability Setup vorbereitet.
  - [x] Zentraler Prompt-Loader für Markdown-Templates.
  - [x] Gemeinsame Pydantic-Schemas (`ReviewCriteria`).
- [x] **Agenten & Workflows:**
  - [x] `Orchestrator-Agent` zur Intent-Steuerung implementiert.
  - [x] `Phase 1: SSP-Generator` (Producer/Reviewer Maker-Checker Loop) implementiert.
- [x] **Qualitätssicherung:**
  - [x] Unit-Tests für Orchestrator und Prompt-Loading erfolgreich durchgeführt.

## Offene Aufgaben (To Do)
- [ ] **Erweiterung SSP-Generator:**
  - [ ] Implementierung des Human-in-the-Loop (HITL) Controllers (siehe Frontend-Integration).
  - [ ] Multimodaler Upload von Asset-Listen über temporäre lokale Dateien verfeinern.
- [ ] **ADK Best Practice Refactoring (Review Findings):**
  - [ ] **Session & State Management:** Manuelles Parsing der `user_id` durch das ADK `Firestore Session Service` Plugin ersetzen, um Multi-Tenancy (iv_id) und Gesprächshistorien nativ und persistiert zu verwalten.
  - [ ] **Error Recovery (Reflect and Retry):** ADK's `Reflect and Retry` Plugin für die strict JSON OSCAL-Validierung integrieren, damit der Agent Schema-Fehler selbstständig korrigieren kann, bevor er fehlschlägt.
- [ ] **Frontend Integration (CopilotKit & AG-UI):**
  - [ ] Scaffold eines Next.js/React Frontends mit `npx copilotkit@latest create -f adk`.
  - [ ] Implementierung der Chat-UI zur Kommunikation mit dem Gpp-Agenten (`adk web` nur noch für Backend-Dev nutzen).
  - [ ] Integration von **Generative UI** Komponenten für Tool-Calls (z.B. visuelle Darstellung und Freigabe-Formulare für erstellte SSPs).
  - [ ] Umsetzung von Shared State zwischen ADK-Agent und CopilotKit Frontend, um den Human-in-the-Loop (HITL) Approval-Prozess interaktiv abzubilden.
- [ ] **Weitere Phasen implementieren:**
  - [ ] Phase 2: SSP-Ausfüllen (Umsetzungsstatus & KI-Assistent).
  - [ ] Phase 3: Assessment Plan & Results.
  - [ ] Phase 4: POA&M-Generator.
- [ ] **Testing:**
  - [ ] Integration-Tests mit den beiden realem/mocked MCP-Servern (`GSpp_MCP` & `GS_backend_MCP`).
  - [ ] Red-Team Tests (Prompt Injection, Tenant Isolation).

## Offene Fragen & Klärungspunkte
1. **MCP Transport:** Welcher Transport-Typ wird für die MCP Server in der Zielumgebung primär genutzt (SSE/HTTP oder Stdio)? Aktuell ist SSE/HTTP als Standard hinterlegt.
2. **HITL Interface:** Da nun CopilotKit & AG-UI als Frontend-Stack vorgesehen sind, muss definiert werden, wie der Freigabe-Workflow in der Generative UI exakt aussehen soll (z.B. Diff-View für OSCAL JSON).
3. **Authentifizierung:** Wie werden die `user_id` Credentials (`caller_principal`) an den Agenten übergeben, um die IV-Namespacing Logik beim Backend sicher zu befeuern?
