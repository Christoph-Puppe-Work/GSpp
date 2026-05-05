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
  - **Root Orchestrator**: Implementiert mit IV-Resolution-Logik und Delegation an Sub-Workflows (`orchestrator/agent.py`).
  - **CIS→OSCAL Workflow**: Implementiert als `SequentialAgent` mit integriertem `LoopAgent` für Peer-Reviews (`agents/cis_oscal/`).
  - **Vendor Evidence Workflow**: Struktur für Extraktion und Mapping steht (`agents/vendor_evidence/`).
  - **Policy Generator Workflow**: Implementiert mit `ParallelAgent` zur gleichzeitigen Bearbeitung der 17 Kontroll-Domänen (`agents/policy_generator/`).
- **Tools & Integration**:
  - **BSI G++ MCP Toolset**: Factory-Funktion unterstützt `stdio` und `sse` Modi (`tools/bsi_gpp_mcp.py`).
  - **Review-Mechanismus**: `exit_loop`-Tool ermöglicht es dem Reviewer-Agenten, den Workflow bei Erfolg abzuschließen (`tools/exit_loop.py`).
- **Qualitätssicherung**:
  - Unit-Tests für Artifact-Service, Session-Service und Orchestrator-Tools erfolgreich implementiert (`tests/unit/`).
  - Integration-Smoke-Tests zur Validierung der Agenten-Initialisierung (`tests/integration/test_smoke.py`).

## ❌ Offen (To Do / Missing)

- **Fachliche Implementierung (Logik)**:
  - **Prompts auslagern**: Die Instruktionen in den `producer.py` und `reviewer.py` der jeweiligen Domänen sind derzeit inline hardcodiert (als Platzhalter). Diese müssen als YAML-Frontmatter nach `shared/prompts/{domain}/{producer|reviewer}.md` ausgelagert werden.
  - **GCS Input Loading**: Die Tools zum Laden und Schreiben von Dateien (z.B. in `agents/cis_oscal/tools.py`) nutzen derzeit Mocks. Die reale Anbindung an den GCS-Bucket (Lesen aus `iv-{id}/inputs/`, Schreiben nach `iv-{id}/artifacts/{session_id}/{domain}/`) muss finalisiert werden.
  - **OSCAL-Vollständigkeit**: Das `OscalComponentDefinition`-Schema in `shared/schemas.py` ist nur vereinfacht. Eine vollständige Abbildung gegen das offizielle OSCAL-1.1.2-Metaschema steht aus (inkl. Validator).
  - **Review-Kriterien**: Diese sind als Pydantic-Modelle in `shared/review_criteria.py` vorhanden, müssen aber noch tiefgehend ausformuliert und im Prompt-Context korrekt verwendet werden.
  - **PDF-Generierung**: Der Policy-Generator exportiert aktuell Markdown-Entwürfe. Die Konvertierung in finale PDFs (z.B. via `weasyprint`) ist noch nicht integriert.
- **Infrastruktur & Betrieb**:
  - **Authentifizierung**: Die Integration eines Auth-Providers (z.B. GCP IAP oder in-app via Bearer-Token) vor dem Orchestrator ist noch offen.
  - **Audit Logging**: Ein persistentes Audit-Log der Agenten-Entscheidungen außerhalb des Session-States (z.B. separates Cloud-Logging-Sink mit `iv_id`-Label) fehlt noch.
  - **MCP Tool-Filtering**: Verfeinerung der Tool-Verfügbarkeit pro Agent. Aktuell bekommen alle Agents alle Tools von `get_bsi_gpp_toolset()`. Reviewer sollten z.B. keine schreibenden/teuren Tools erhalten.
  - **Sicherheit & Härtung**: Der `default-iv`-Fallback in `services/artifact_service.py` und `services/session_service.py` muss durch `raise ValueError` ersetzt werden (sobald Tests laufen).
- **Observability & Evaluation (gemäß README §11.5)**:
  - **Trajectory-Tracing-Module**: `tools/observability.py` fehlt komplett (Einbindung von ADK Callbacks, Export nach Cloud Trace).
  - **Cost-Metric**: Generierung von Metriken (z.B. `gpp_agent/tokens_per_run`) in Cloud Monitoring.
  - **Eval-Snapshots**: Einrichtung in `tests/eval_snapshots/`.
  - **Alerts**: Cloud-Monitoring-Alert für Loop-Eskalation.
- **Tests & Validierung**:
  - **Tenant-Isolation Test**: Ein automatisierter Test, der zwei parallele IV-Sessions simuliert und auf Null-Leckage prüft.
  - **End-to-End Loop Test**: Vollständiger Durchlauf inkl. Simulation von abgelehnten Review-Iterationen (Mock-Reviewer lehnt 1. Iteration ab, approved 2. Iteration).
  - **MCP-Sidecar-Test**: Container-basiertes Setup im CI mit echtem `../GSpp_MCP`.
  - **Red-Team-Suite**: Strukturierte Tests für Angriffsvektoren (Prompt Injection, Unauthorized Tool Use, Cross-IV-Exfiltration, Token-Exhaustion).

## 💡 Decisions to Make (Offene Punkte zur Klärung)

Gemäß `README.md` §13 müssen vor dem ersten Build folgende Fragen (mit Christoph) geklärt werden:

1. **Workflow-Reihenfolge der Vervollständigung:** Empfehlung ist *Vendor Evidence* zuerst, da es die einfachste Pipeline-Topologie hat.
2. **`apply_profile` im MCP:** Derzeit ein Stub in `GSpp_MCP`. Soll der Agent das Stub-Verhalten bereits konsumieren oder auf eine echte Implementierung warten?
3. **AuthN-Architektur:** IAP (Identity-Aware Proxy) davor schalten (zero-code) oder in-app via Bearer-Token validieren? (Empfehlung: IAP).
4. **Audit-Logging-Strategie:** Ein separates Cloud-Logging-Sink (zero-code, gut für Compliance) oder Speicherung über `state["audit_log"]` in der Session (testbarer)?
5. **Beispielkataloge (DSGVO, KRITIS):** Sollen diese als Demo-Inputs in E2E-Tests eingebaut werden?
6. **Multi-Judge Review:** Ab wann (welches Kriterium) soll von Single-Reviewer auf Multi-Judge-Review umgestellt werden? (Vorschlag: nach > 100 produktiven Runs).
7. **Eval-Snapshot-Pflege:** Wer aktualisiert `tests/eval_snapshots/`? Vorgeschlagener Prozess: wer den Producer-Prompt ändert, aktualisiert die Snapshots im selben PR.