# Gpp-Agent: Implementierungs-Roadmap (Clean Slate)

Diese TODO-Liste basiert auf den Spezifikationen der neuen `README.md` und dient als zentraler Leitfaden für die Neuerstellung des Agenten-Systems von Grund auf.

## 1. Projekt-Setup & Infrastruktur
- [ ] Initialisierung des Python-Projekts (z. B. `pyproject.toml`, `requirements.txt`).
- [ ] Definition der grundlegenden Verzeichnisstruktur (`agents/`, `tools/`, `services/`, `schemas/`).
- [ ] Setup der Umgebungs-Variablen (`.env` für GCP-Credentials, MCP-URLs, API-Keys).

## 2. Kern-Services (Services Layer)
- [ ] **GCS-Storage-Service:**
  - [ ] Implementierung der GCP Bucket Anbindung.
  - [ ] Logik für Mandanten-Trennung (Unterverzeichnisse pro Informationsverbund).
  - [ ] Logik für versionierte Savepoints (Speicherstände).
  - [ ] Funktionen zum Laden und Speichern von JSON-Dateien.
- [ ] **MCP-Client-Service:**
  - [ ] Anbindung an den `GSpp_MCP` Server zum Abruf des Anwenderkatalogs.
  - [ ] Bereitstellung der Katalog-Daten als Tools für die Agenten.
- [ ] **Schema-Validator:**
  - [ ] Einbindung der OSCAL-Schemas aus `hilfsdateien`.
  - [ ] Implementierung eines strikten JSON-Validators (wird zwingend vor jedem GCS-Save aufgerufen).

## 3. Agenten-Architektur (Sub-Agents & Peer Review)
- [ ] **Orchestrator-Agent:** 
  - [ ] Routet User-Intents, verwaltet den aktiven Informationsverbund und delegiert an Sub-Agenten.
- [ ] **Producer-Agenten:**
  - [ ] Implementierung spezialisierter Prompts/Tools für SSP-Generierung, Risikoanalyse, etc.
- [ ] **Reviewer-Agent (Maker-Checker):**
  - [ ] Implementierung der Prüflogik (Validierung gegen MCP-Katalog und formale OSCAL-Richtigkeit).
  - [ ] Feedback-Loop-Logik (Rückgabe an Producer bei Mängeln).
- [ ] **Human-in-the-Loop (HITL) Controller:**
  - [ ] Logik für das Pausieren des Workflows an kritischen Entscheidungspunkten.
  - [ ] Schnittstelle für manuelles User-Feedback und Override vor dem finalen Speichern im Bucket.

## 4. Workflows (Umsetzung der 4 Phasen)
- [ ] **Phase 1: SSP-Generator (Modellierung)**
  - [ ] Profil-Erstellung & Asset-Integration (Multimodaler Upload von Listen).
  - [ ] Risikoanalyse-Modul (Custom Controls).
  - [ ] Tailoring-Funktionen.
- [ ] **Phase 2: SSP-Ausfüllen (Grundschutzcheck)**
  - [ ] Erfassung des Umsetzungsstatus.
  - [ ] KI-Assistenz für Control-Verständnis & Risikofokus (Referenzierung BSI Edition 2023).
- [ ] **Phase 3: Assessment Plan & Results**
  - [ ] Generierung des Assessment Plans (AP).
  - [ ] KI-Befundvorschlag & Reifegrad-Prüfungshandlungen.
  - [ ] Export der Assessment Results (AR).
- [ ] **Phase 4: POA&M-Generator**
  - [ ] Mängel-Import aus AR.
  - [ ] Meilenstein-Planung & Dashboard-Datenstruktur.

## 5. Testing & Qualitätssicherung
- [ ] Unit-Tests für den GCS-Storage-Service (Strikte Isolierung der Informationsverbünde prüfen).
- [ ] Unit-Tests für den Schema-Validator (gegen BSI Schemas).
- [ ] Integration-Tests für den Producer-Reviewer-Feedback-Loop.
- [ ] Mock-Tests für die MCP-Server Anbindung.
