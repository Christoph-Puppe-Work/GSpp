# Grundschutz++ Multi-Agent Tooling

ADK-basiertes Multi-Agent-System, das die Workflows der NTT DATA One-Page-Apps
[(Grundschutz-Plus-Plus-Tools / One-Page-Apps)](https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/tree/main/One-Page-Apps)
auf Server-Seite reproduziert, **Peer Review** zur Qualitätssicherung einsetzt und Kundendaten
pro **Informationsverbund** in einem GCS-Bucket persistiert.

> **Build-Hinweis für Jules:** Diese README ist die Spezifikation. Module, Klassen-Signaturen
> und Verzeichnisstruktur sind verbindlich. Code-Skizzen sind Vorlagen, keine fertigen
> Implementierungen – sie müssen ausimplementiert, getestet und in `pyproject.toml` /
> `requirements.txt` mit Versionen gepinnt werden.

---

## 1. Architektur

```
                              ┌──────────────────────────┐
                              │   Root Orchestrator      │
                              │   (LlmAgent)             │
                              │                          │
User ─▶ adk run / Cloud Run ─▶│   - parses request       │
                              │   - resolves IV-context  │
                              │   - delegates to domain  │
                              └────────────┬─────────────┘
                                           │
                ┌──────────────────────────┼──────────────────────────┐
                ▼                          ▼                          ▼
   ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
   │ CIS→OSCAL Workflow   │  │ Vendor Evidence WF   │  │ Policy Generator WF  │
   │ (SequentialAgent)    │  │ (SequentialAgent)    │  │ (SequentialAgent)    │
   │                      │  │                      │  │                      │
   │ ┌──────────────────┐ │  │ ┌──────────────────┐ │  │ ┌──────────────────┐ │
   │ │  Review Loop     │ │  │ │  Review Loop     │ │  │ │  Review Loop     │ │
   │ │  (LoopAgent)     │ │  │ │  (LoopAgent)     │ │  │ │  (LoopAgent)     │ │
   │ │                  │ │  │ │                  │ │  │ │                  │ │
   │ │  Producer ──┐    │ │  │ │  Producer ──┐    │ │  │ │  Producer ──┐    │ │
   │ │             ▼    │ │  │ │             ▼    │ │  │ │             ▼    │ │
   │ │           Reviewer│ │  │ │           Reviewer│ │  │ │           Reviewer│ │
   │ └──────────────────┘ │  │ └──────────────────┘ │  │ └──────────────────┘ │
   └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘
              │                         │                         │
              └─────────────────────────┼─────────────────────────┘
                                        ▼
                ┌──────────────────────────────────────────────┐
                │ Shared Infrastructure                        │
                │                                              │
                │  • BSI G++ MCPToolset  (extern, separat)     │
                │  • GcsArtifactService  (IV-namespaced)       │
                │  • SessionService      (IV-namespaced)       │
                └──────────────────────────────────────────────┘
```

### Kernprinzipien

1. **Deterministisches getrennt von LLM-Reasoning.** OSCAL-Emitter, JSON-Validierung,
   Schema-Mapping sind Python-Tools. LLM nur für Klassifikation, semantisches Matching,
   Zusammenfassung.
2. **Peer Review per Loop.** Jeder Domain-Workflow hat einen Producer und einen Reviewer.
   Reviewer setzt `tool_context.actions.escalate = True`, sobald das Artefakt die
   Qualitätskriterien erfüllt – sonst max. `MAX_REVIEW_ITERATIONS` Runden.
3. **Multi-Tenancy über Informationsverbund-ID.** Alle Sessions, States und Artefakte werden
   unter einem `informationsverbund_id` (IV-ID) namensraumiert. Kein Cross-Tenant-Zugriff.
4. **MCP als externe Abhängigkeit.** Der BSI-G++-MCP-Server liegt in einem separaten Repo
   und wird als `MCPToolset` eingebunden. Tool-Surface siehe [§ 6](#6-mcp-server-anbindung).

---

## 2. Projektstruktur

```
grundschutz_pp_agents/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── orchestrator/
│   ├── __init__.py
│   └── agent.py                  # root_agent (LlmAgent)
│
├── agents/
│   ├── __init__.py
│   ├── cis_oscal/
│   │   ├── __init__.py
│   │   ├── workflow.py           # SequentialAgent + LoopAgent
│   │   ├── producer.py           # LlmAgent (CIS→OSCAL Mapper)
│   │   ├── reviewer.py           # LlmAgent (Peer Reviewer)
│   │   └── tools.py              # deterministische Tools (oscal_emit, validate, ...)
│   ├── vendor_evidence/
│   │   └── ...                   # gleiche Struktur
│   └── policy_generator/
│       └── ...                   # gleiche Struktur
│
├── tools/
│   ├── __init__.py
│   ├── bsi_gpp_mcp.py            # MCPToolset Factory
│   └── exit_loop.py              # Reviewer-Approval-Tool
│
├── services/
│   ├── __init__.py
│   ├── artifact_service.py       # IV-namespaced GcsArtifactService
│   └── session_service.py        # IV-namespaced SessionService
│
├── shared/
│   ├── __init__.py
│   ├── schemas.py                # Pydantic-Schemas für Producer-Outputs
│   ├── review_criteria.py        # Reviewer-Checklisten pro Domain
│   └── prompts/
│       ├── orchestrator.md
│       ├── cis_oscal_producer.md
│       ├── cis_oscal_reviewer.md
│       └── ...
│
├── deployment/
│   ├── Dockerfile
│   └── cloud_run.yaml
│
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 3. Voraussetzungen

| Komponente | Version | Zweck |
|---|---|---|
| Python | ≥ 3.10 | ADK-Anforderung |
| `google-adk` | aktuelle stable | Agent Framework |
| `google-cloud-storage` | ≥ 2.x | Bucket-Zugriff |
| `pydantic` | ≥ 2.x | Schema-Validierung |
| `mcp` | aktuelle stable | MCP-Client (bei stdio) |
| GCP Project | – | mit aktivierten APIs: Vertex AI, Cloud Storage, (optional) Cloud Run |
| GCS Bucket | – | z.B. `gs-pp-tooling-{env}` |
| BSI-G++-MCP-Server | extern | aus separatem Repo, lokal lauffähig oder als Cloud-Run-Service |

---

## 4. Konfiguration

`.env.example` (in `.env` kopieren, dann anpassen):

```bash
# Google AI / Vertex
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=ntt-de-grundschutz-dev
GOOGLE_CLOUD_LOCATION=europe-west3

# Storage
GCS_BUCKET_NAME=gs-pp-tooling-dev

# MCP Server (Option A: stdio, lokal)
BSI_GPP_MCP_MODE=stdio
BSI_GPP_MCP_COMMAND=python
BSI_GPP_MCP_ARGS=-m bsi_gpp_mcp_server

# MCP Server (Option B: HTTP/SSE, deployed)
# BSI_GPP_MCP_MODE=sse
# BSI_GPP_MCP_URL=https://bsi-gpp-mcp-xxx.a.run.app/sse

# Modelle
ORCHESTRATOR_MODEL=gemini-2.5-pro
PRODUCER_MODEL=gemini-2.5-pro
REVIEWER_MODEL=gemini-2.5-pro

# Workflow
MAX_REVIEW_ITERATIONS=3
```

---

## 5. Multi-Informationsverbund (Multi-Tenancy)

### Konzept

Jeder Kundenkontext ist ein **Informationsverbund** mit einer eindeutigen ID
(Format: `iv-{slug}`, z.B. `iv-stadtwerke-erfurt-prod`). Sessions, States und
Artefakte sind strikt nach IV-ID getrennt – Agenten sehen niemals Daten eines
anderen IV.

### State-Schlüssel (verbindlich)

| Key | Quelle | Zweck |
|---|---|---|
| `informationsverbund_id` | User-Input via Orchestrator | Tenant-Schlüssel, in **jeder** Session erforderlich |
| `informationsverbund_label` | optional | menschenlesbarer Name |
| `informationsverbund_metadata` | optional | dict (Branche, Schutzbedarf, …) |

### GCS-Layout

```
gs://{GCS_BUCKET_NAME}/
├── iv-stadtwerke-erfurt-prod/
│   ├── sessions/
│   │   └── {session_id}.json                          # Session-State (JSON)
│   ├── artifacts/
│   │   └── {session_id}/
│   │       ├── cis_oscal/
│   │       │   ├── component_definition.json/         # ADK-Versioned
│   │       │   │   ├── 0
│   │       │   │   └── 1
│   │       │   └── review_log.md/...
│   │       ├── vendor_evidence/...
│   │       └── policy_generator/...
│   └── inputs/                                        # User-Uploads (CIS-CSVs, etc.)
└── iv-other-customer/
    └── ...
```

### Implementierung: IV-namespaced Artifact Service

`services/artifact_service.py`:

```python
from google.adk.artifacts import GcsArtifactService
from google.adk.tools import ToolContext


class InformationsverbundGcsArtifactService(GcsArtifactService):
    """
    Wraps GcsArtifactService so all artifact paths are prefixed with the
    informationsverbund_id from session state. Prevents cross-tenant access.
    """

    def _build_blob_name(
        self, app_name: str, user_id: str, session_id: str, filename: str, version: int
    ) -> str:
        # ADK default: {app_name}/{user_id}/{session_id}/{filename}/{version}
        # We override to: {iv_id}/artifacts/{session_id}/{filename}/{version}
        # iv_id is encoded into user_id by the orchestrator before runner.run()
        iv_id = self._extract_iv_id(user_id)
        return f"{iv_id}/artifacts/{session_id}/{filename}/{version}"

    @staticmethod
    def _extract_iv_id(user_id: str) -> str:
        # Convention: user_id = "{caller}::iv::{informationsverbund_id}"
        if "::iv::" not in user_id:
            raise ValueError(
                f"user_id must encode informationsverbund_id: {user_id}"
            )
        return user_id.split("::iv::", 1)[1]
```

> **Jules:** Die exakte Methoden-Signatur kann je nach ADK-Version abweichen. Falls die
> Override-Stelle in `GcsArtifactService` anders heißt, an gleicher semantischer Stelle
> einhaken. Tests dafür sind in `tests/unit/test_artifact_service.py` Pflicht.

### Implementierung: IV-namespaced Session Service

Analog für `services/session_service.py` – Sessions werden unter
`{iv_id}/sessions/{session_id}.json` gespeichert. Wenn die ADK-stable-Version keine
GCS-basierte SessionService-Klasse mitliefert, das `BaseSessionService`-Interface
implementieren (`create_session`, `get_session`, `list_sessions`, `delete_session`,
`append_event`).

### IV-Resolution im Orchestrator

Der Orchestrator muss bei **jedem** ersten Turn prüfen, ob `informationsverbund_id`
bereits im State liegt. Wenn nicht: User danach fragen, validieren (Regex
`^iv-[a-z0-9-]{3,40}$`), in State schreiben, dann erst delegieren.

---

## 6. MCP-Server-Anbindung

Der BSI-G++-MCP-Server liegt in einem **separaten Repository** und wird hier nur
konsumiert. Tool-Surface (verbindlich, vom MCP-Server bereitgestellt):

| Tool | Zweck |
|---|---|
| `catalog_info()` | Metadata-Block, Version, Counts |
| `list_groups()` | Tree of `{id, title, control_count}` |
| `list_controls(group_id?, prop?, value?, limit?)` | IDs + Titel, keine Bodies |
| `get_control(id, include=["statement"], resolve_params=true, include_enhancements=false)` | Vollständiges Control |
| `search_controls(query, group_id?, limit=20)` | Ranked IDs (inverted index) |
| `get_parameter(id)` | Param + Label + Select Values |
| `find_referencing_controls(id)` | Backrefs |
| `apply_profile(profile_uri)` | (Stub) baseline-resolved Catalogs |

### Einbindung als ADK-Tool

`tools/bsi_gpp_mcp.py`:

```python
import os
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioServerParameters,
    SseServerParams,
)


def get_bsi_gpp_toolset() -> MCPToolset:
    """Factory for the BSI G++ MCP toolset. Reads mode from env."""
    mode = os.environ.get("BSI_GPP_MCP_MODE", "stdio")

    if mode == "stdio":
        return MCPToolset(
            connection_params=StdioServerParameters(
                command=os.environ["BSI_GPP_MCP_COMMAND"],
                args=os.environ["BSI_GPP_MCP_ARGS"].split(),
            ),
        )
    elif mode == "sse":
        return MCPToolset(
            connection_params=SseServerParams(
                url=os.environ["BSI_GPP_MCP_URL"],
            ),
        )
    raise ValueError(f"Unknown BSI_GPP_MCP_MODE: {mode}")
```

Empfehlung: nicht alle MCP-Tools allen Agenten geben, sondern pro Agent filtern
(über `tool_filter` Parameter oder eigenen Wrapper). Beispiel: der Producer im
Policy-Generator braucht `list_groups`, `get_control`, `get_parameter` – aber nicht
`apply_profile`.

---

## 7. Peer-Review-Pattern (Qualitätssicherung)

Jeder Domain-Workflow hat genau diese Topologie:

```
SequentialAgent("cis_oscal_workflow")
 ├── input_loader            (custom tool agent)
 ├── catalog_resolver        (LlmAgent + MCP)
 ├── LoopAgent("review_loop", max_iterations=MAX_REVIEW_ITERATIONS)
 │    ├── producer           (LlmAgent, output_key="draft_artifact")
 │    └── reviewer           (LlmAgent, tools=[exit_loop])
 └── artifact_writer         (custom tool agent: validates + writes to GCS)
```

### Producer

- Liest Input + Kontext aus State.
- Schreibt strukturierten Output (Pydantic-Schema!) nach `state["draft_artifact"]`.
- Nutzt MCP-Tools für G++-Lookups.

### Reviewer

- Liest `state["draft_artifact"]` + Original-Input.
- Prüft gegen domain-spezifische Checkliste aus `shared/review_criteria.py`
  (z.B. für CIS→OSCAL: valides OSCAL JSON, alle Controls aufgelöst, keine
  Halluzinationen bei IDs, Statement-Felder gefüllt).
- Wenn OK: ruft `exit_loop` Tool → Loop endet.
- Wenn nicht OK: schreibt strukturiertes Feedback nach `state["review_feedback"]`,
  Loop läuft erneut, Producer sieht Feedback und korrigiert.

### Exit-Loop-Tool

`tools/exit_loop.py`:

```python
from google.adk.tools import ToolContext


def exit_loop(reason: str, tool_context: ToolContext) -> dict:
    """
    Signal that the reviewed artifact is approved and the review loop
    can exit. Set reason to a short human-readable approval rationale.
    """
    tool_context.actions.escalate = True
    return {"status": "approved", "reason": reason}
```

### Review-Kriterien-Schema

`shared/review_criteria.py` enthält pro Domain eine Pydantic-Klasse mit den
Checks, die der Reviewer durchgehen muss. Diese Klasse wird im Reviewer-Prompt
als Strukturvorgabe eingesetzt – nicht als Pflichtschema des Outputs, aber als
verbindliche Checkliste.

Beispiel (Skizze):

```python
class CisOscalReviewCriteria(BaseModel):
    oscal_json_valid: bool
    component_definition_metadata_complete: bool
    all_controls_resolvable_via_mcp: bool
    no_hallucinated_control_ids: bool
    statements_match_cis_recommendations: bool
    parameters_have_valid_select_values: bool
    overall_verdict: Literal["approve", "request_changes"]
    findings: list[ReviewFinding]
```

### Failure-Mode

Wenn `MAX_REVIEW_ITERATIONS` erreicht wird, ohne Approval: der `artifact_writer`
schreibt das letzte Draft + das gesamte Review-Log als Artefakt nach GCS und
markiert den State mit `state["review_status"] = "failed"`. Der Orchestrator
meldet das dem User.

---

## 8. Agenten-Spezifikationen

### 8.1 Root Orchestrator (`orchestrator/agent.py`)

- `LlmAgent`, `model=ORCHESTRATOR_MODEL`
- Sub-Agents: `cis_oscal_workflow`, `vendor_evidence_workflow`, `policy_generator_workflow`
- Tools: keine direkten Domain-Tools, nur Delegation und IV-Verwaltung-Tools
  (`set_informationsverbund`, `list_my_informationsverbuende`, `load_session`)
- Verhalten: erfragt IV bei jedem neuen Kontext, delegiert an Sub-Agent passend zur
  User-Intent.

### 8.2 CIS→OSCAL Workflow (`agents/cis_oscal/`)

Pipeline: `INPUT → CATALOG → MATCH → EMIT` (entspricht der bestehenden One-Page-App).

- `input_loader`: liest CIS-CSV/JSON aus dem IV-`inputs/` GCS-Prefix
- `catalog_resolver`: bestimmt G++-Bausteine via `search_controls` + `list_controls`
- `producer`: erstellt OSCAL Component Definition (gegen OSCAL-1.1.2-Metaschema)
- `reviewer`: prüft gegen `CisOscalReviewCriteria`
- `artifact_writer`: schreibt finale `component_definition.json` ins
  `iv-{id}/artifacts/{session_id}/cis_oscal/` Prefix

### 8.3 Vendor Evidence Workflow (`agents/vendor_evidence/`)

Pipeline: Batch-Extraktion aus Hersteller-Dokumenten.

- `input_loader`: liest hochgeladene PDFs/Docs
- `producer`: extrahiert Evidence-Statements + mappt auf G++-Anforderungen via MCP
- `reviewer`: prüft Coverage, Quellzuordnung, keine erfundenen Zitate
- `artifact_writer`: CSV + Ground-Truth-Export

### 8.4 Policy Generator Workflow (`agents/policy_generator/`)

Pipeline: 17 Control-Domänen, pro Domain eigener Sub-Step (`ParallelAgent` über die 17
Domänen, dann Aggregation, dann Review).

- `producer`: pro Domain eine Policy als Markdown
- `reviewer`: prüft Konsistenz, G++-Mapping, Vollständigkeit
- `artifact_writer`: pro Domain ein PDF + ein zusammengefasstes PDF

---

## 9. Lokal ausführen

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # und Werte setzen

# GCP Auth
gcloud auth application-default login

# BSI-G++-MCP-Server starten (separates Repo, in eigenem Terminal)
# z.B. python -m bsi_gpp_mcp_server

# Agent starten – CLI
adk run orchestrator

# Agent starten – Web UI (nur dev, NICHT für Produktion)
adk web --port 8000
```

---

## 10. Deployment

Ziel: Cloud Run für den Orchestrator (HTTP-Frontend), MCP-Server separat als
eigener Cloud-Run-Service mit SSE-Endpoint.

```bash
adk deploy cloud-run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service-name=grundschutz-pp-orchestrator \
  orchestrator
```

`deployment/Dockerfile` muss enthalten:
- Python 3.11-slim
- `google-adk`, `google-cloud-storage`, `mcp`
- ENV-Vars aus Cloud-Run-Konfiguration (nicht aus `.env`!)
- Service-Account mit Rollen: `roles/storage.objectAdmin` auf den Bucket,
  `roles/aiplatform.user`

---

## 11. Tests

- **Unit:** Pydantic-Schemas, IV-Namespacing-Logik, exit_loop Tool, Review-Kriterien
- **Integration:** End-to-End mit Mock-MCP-Server und einem Test-IV gegen einen
  Test-Bucket. Mindestens ein vollständiger CIS→OSCAL-Run mit Review-Loop, der
  in der ersten Iteration scheitert und in der zweiten approved wird – um den
  Loop-Mechanismus tatsächlich zu validieren.
- **Tenant-Isolation-Test:** Pflicht. Zwei IVs schreiben parallel, beide Sessions
  dürfen sich nicht sehen.

---

## 12. Definition of Done für Jules

- [ ] Verzeichnisstruktur aus § 2 vollständig angelegt
- [ ] `pyproject.toml` mit gepinnten Versionen aller Dependencies aus § 3
- [ ] `InformationsverbundGcsArtifactService` implementiert + Unit-Test
- [ ] IV-namespaced SessionService implementiert + Unit-Test
- [ ] BSI-G++-MCPToolset-Factory implementiert (stdio + sse Modi)
- [ ] CIS→OSCAL-Workflow vollständig (Producer, Reviewer, Loop, Writer)
- [ ] Vendor-Evidence-Workflow vollständig
- [ ] Policy-Generator-Workflow vollständig
- [ ] Root Orchestrator mit IV-Verwaltung
- [ ] `exit_loop` Tool + Reviewer-Approval-Pfad funktioniert (Integrationstest grün)
- [ ] Tenant-Isolation-Test grün
- [ ] `adk run orchestrator` startet ohne Fehler bei korrekt gesetztem `.env`
- [ ] README, falls etwas signifikant abweichend implementiert wurde, entsprechend ergänzt
- [ ] Dockerfile + Cloud-Run-Config in `deployment/`

---

## 13. Open Points (vor erstem Build mit Christoph klären)

1. Welche der drei Workflows wird zuerst gebaut? Empfehlung: **Vendor Evidence**
   (einfachste Pipeline-Topologie, schneller End-to-End-Smoke-Test).
2. Soll `apply_profile` im MCP bereits konsumiert werden oder erst nach Stub-Auflösung?
3. Authentifizierung der User vor dem Orchestrator – fällt das in diese Codebasis
   oder davor (z.B. via IAP)?
4. Audit-Logging: separat oder über `state["audit_log"]`?
