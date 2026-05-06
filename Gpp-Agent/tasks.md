# Gpp-Agent Tasks & Progress

## Erledigte Aufgaben (Completed)
- [x] **Projekt-Setup & Infrastruktur:**
  - [x] `pyproject.toml` mit Abhängigkeiten (`google-adk`, `mcp`, `pydantic`, etc.) erstellt.
  - [x] `.env.example` Vorlage erstellt.
  - [x] Verzeichnisstruktur (`agents/`, `services/`, `tools/`, `shared/`, `tests/`) initialisiert.
  - [x] `__init__.py` Dateien zur Paket-Erkennung hinzugefügt.
- [x] **Kern-Services:**
  - [x] `GcsStorageService` für mandantenfähige Speicherung (IV-namespacing) implementiert.
  - [x] `McpClientService` für BSI-Katalog-Integration implementiert.
  - [x] `SchemaValidator` für OSCAL-Validierung implementiert.
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
  - [ ] Implementierung des Human-in-the-Loop (HITL) Controllers.
  - [ ] Integration des `GcsStorageService` als Writer am Ende des Workflows.
  - [ ] Multimodaler Upload von Asset-Listen.
- [ ] **Weitere Phasen implementieren:**
  - [ ] Phase 2: SSP-Ausfüllen (Umsetzungsstatus & KI-Assistent).
  - [ ] Phase 3: Assessment Plan & Results.
  - [ ] Phase 4: POA&M-Generator.
- [ ] **Testing:**
  - [ ] Integration-Tests mit realem/mocked MCP-Server.
  - [ ] Red-Team Tests (Prompt Injection, Tenant Isolation).
  - [ ] Schema-Validierungstests gegen echte BSI-Schemas.

## Offene Fragen & Klärungspunkte
1. **MCP Transport:** Welcher Transport-Typ wird für den `GSpp_MCP` Server in der Zielumgebung primär genutzt (SSE/HTTP oder Stdio)? Aktuell ist SSE/HTTP als Standard in `McpClientService` hinterlegt.
2. **Schema-Pfad:** Wo genau liegen die OSCAL-Schemas in der Produktionsumgebung? (`GSpp_MCP/OSCAL_schemas/` vs `hilfsdateien/`).
3. **HITL Interface:** Wie erfolgt die Interaktion im HITL-Schritt? (Web-UI Integration vs. CLI-Prompting).
4. **Authentifizierung:** Wie werden die `user_id` Credentials (`caller_principal`) an den Agenten übergeben, um die IV-Namespacing Logik sicher zu befeuern?
