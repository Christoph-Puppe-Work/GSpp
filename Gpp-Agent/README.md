# Grundschutz++ Multi-Agent Tooling (`Gpp-Agent`)

ADK-basiertes Multi-Agent-System, das die Workflows der
[`../One-Page-Apps`](../One-Page-Apps) auf Server-Seite reproduziert,
**Peer Review** zur Qualitätssicherung einsetzt und Kundendaten pro
**Informationsverbund** in einem GCS-Bucket persistiert.

Dieses Verzeichnis ist eines von vier Subprojekten im
[`GSpp` Monorepo](../README.md). Es interagiert mit den folgenden Geschwistern:

- [`../GSpp_MCP`](../GSpp_MCP) – BSI Grundschutz++ MCP-Server, der den
  Anwenderkatalog als Tool-Surface bereitstellt. Der Agent ist sein Hauptkonsument.
- [`../One-Page-Apps`](../One-Page-Apps) – Browser-Tools, deren Workflow-Logik
  hier serverseitig nachgebaut wird. Prompts und Schemas werden konzeptionell
  abgeglichen, aber nicht im Code geteilt (Browser-JS ↔ Python-Backend).
- [`../hilfsdateien`](../hilfsdateien),
  [`../zielobjektkategorien`](../zielobjektkategorien),
  [`../beispiel-kataloge`](../beispiel-kataloge),
  [`../kataloge`](../kataloge) – referenzielle Datenbestände, die der MCP-Server
  konsumiert und der Agent indirekt darüber bekommt.
- [`../Gpp-ai-tool`](../Gpp-ai-tool) – ältere Python-Pipeline für Ed2023→G++
  Migration. Eigenständig, nicht in den Multi-Agent integriert. Dient als
  Konzept-Referenz für deterministische Mapping-Logik.

> **Build-Hinweis für Jules:** Diese README ist die Spezifikation für die
> Weiterentwicklung dieses Subprojekts. Verzeichnisstruktur, Modul-Grenzen und
> öffentliche Schnittstellen sind verbindlich. Code-Skizzen sind Vorlagen, keine
> fertigen Implementierungen. Der bestehende Stand ist in [`./tasks.md`](./tasks.md)
> dokumentiert; offene Punkte stehen in § 12 dieser README.

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
   │ (SequentialAgent)    │  │ (SequentialAgent)    │  │ (SequentialAgent +   │
   │                      │  │                      │  │  ParallelAgent)      │
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
                │  • BSI G++ MCPToolset → ../GSpp_MCP          │
                │  • GcsArtifactService  (IV-namespaced)       │
                │  • SessionService      (IV-namespaced)       │
                └──────────────────────────────────────────────┘
```

### Kernprinzipien

1. **Deterministisches getrennt von LLM-Reasoning.** OSCAL-Emitter, JSON-Validierung
   und Schema-Mapping sind Python-Tools. LLM nur für Klassifikation, semantisches
   Matching und Zusammenfassung.
2. **Peer Review per Loop.** Jeder Domain-Workflow hat einen Producer und einen
   Reviewer. Reviewer setzt `tool_context.actions.escalate = True`, sobald das
   Artefakt die Qualitätskriterien erfüllt – sonst max. `MAX_REVIEW_ITERATIONS`
   Runden.
3. **Multi-Tenancy über Informationsverbund-ID.** Alle Sessions, States und
   Artefakte werden unter einer `informationsverbund_id` namensraumiert.
   Kein Cross-Tenant-Zugriff.
4. **MCP als Domain-Boundary.** G++-Wissen kommt ausschließlich über den
   `../GSpp_MCP`-Server. Der Agent kennt keine direkten Catalog-JSONs.

---

## 2. Aktueller Stand und Verzeichnisstruktur

Was bereits existiert (siehe auch [`./tasks.md`](./tasks.md)):

```
Gpp-Agent/
├── README.md                            # diese Datei
├── tasks.md                             # IST-Stand und Backlog
├── pyproject.toml                       # Dependencies
├── requirements.txt                     # gepinnte Versionen
│
├── orchestrator/
│   ├── __init__.py
│   └── agent.py                         # ✅ root_agent (LlmAgent) mit IV-Resolution
│
├── agents/
│   ├── __init__.py
│   ├── cis_oscal/
│   │   ├── workflow.py                  # ✅ SequentialAgent + LoopAgent
│   │   ├── producer.py                  # ⚠️ Prompt inline (TODO: nach shared/prompts/)
│   │   ├── reviewer.py                  # ⚠️ Prompt inline (TODO: nach shared/prompts/)
│   │   └── tools.py                     # ⚠️ Mocks (TODO: echtes GCS-Loading)
│   ├── vendor_evidence/                 # ✅ Struktur + Stubs
│   └── policy_generator/                # ✅ ParallelAgent über 17 Domänen
│
├── tools/
│   ├── bsi_gpp_mcp.py                   # ✅ MCPToolset Factory (stdio + sse)
│   └── exit_loop.py                     # ✅ Reviewer-Approval-Tool
│
├── services/
│   ├── artifact_service.py              # ✅ IV-namespaced GcsArtifactService
│   └── session_service.py               # ✅ IV-namespaced SessionService
│
├── shared/                              # nur Agent-intern, kein cross-project shared
│   ├── schemas.py                       # ⚠️ OscalComponentDefinition simplistisch (TODO: full 1.1.2)
│   ├── review_criteria.py               # ⚠️ TODO: pro Domain ausformulieren
│   └── prompts/                         # ❌ FEHLT (TODO: Prompts hierhin auslagern)
│
├── deployment/
│   ├── Dockerfile
│   └── cloud_run.yaml
│
└── tests/
    ├── unit/                            # ✅ artifact_service, session_service, tools
    └── integration/                     # ⚠️ Smoke-Tests, TODO: Loop + Tenant-Isolation
```

Legende: ✅ implementiert · ⚠️ vorhanden, aber unvollständig · ❌ fehlt

> **Abgrenzung zu V1 dieser README:** In einer früheren Version dieses Dokuments
> war ein repo-weiter `shared/`-Layer zwischen Agent, MCP und One-Page-Apps
> vorgesehen. Dieser Ansatz wurde verworfen, weil (a) Browser-JS und Python kein
> Modul ohne Build-Step teilen können, (b) die Subprojekte unterschiedliche
> Python-Versionen nutzen (`GSpp_MCP` ist 3.12, `Gpp-Agent` ist 3.10+), und (c)
> der MCP-Server bereits die G++-Domain-Boundary darstellt. Konsistenz wird über
> den MCP-Vertrag hergestellt, nicht über geteilten Code.

---

## 3. Voraussetzungen

| Komponente | Pin / Version | Zweck |
|---|---|---|
| Python | ≥ 3.10 | aus `pyproject.toml` |
| `google-adk` | `==1.32.0` | Agent Framework (gepinnt) |
| `google-cloud-storage` | `==3.10.1` | Bucket-Zugriff |
| `pydantic` | `==2.13.3` | Schema-Validierung |
| `mcp` | `==1.27.0` | MCP-Client |
| `python-dotenv` | `==1.2.2` | `.env`-Loading lokal |
| `../GSpp_MCP` | running | als Sidecar-Container, Cloud-Run-Service oder lokal via stdio |
| GCP Project | – | mit aktivierten APIs: Vertex AI, Cloud Storage, Cloud Run |
| GCS Bucket | – | z.B. `gs-pp-agent-{env}` |

> **Versions-Disclaimer für Jules:** Vor jedem `dependencies`-Update prüfen, ob
> die ADK-Override-Punkte in `services/artifact_service.py` (`_get_blob_name`,
> `_get_blob_prefix`) sich nicht geändert haben. ADK ist <2.0 noch in aktiver
> Entwicklung; eine Methoden-Umbenennung schlägt sonst Multi-Tenancy still aus.

---

## 4. Konfiguration

`.env.example` (in `.env` kopieren, dann anpassen):

```bash
# Google AI / Vertex
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=ntt-de-grundschutz-dev
GOOGLE_CLOUD_LOCATION=europe-west3

# Storage
GCS_BUCKET_NAME=gs-pp-agent-dev

# MCP Server (Option A: stdio, GSpp_MCP lokal)
BSI_GPP_MCP_MODE=stdio
BSI_GPP_MCP_COMMAND=python
BSI_GPP_MCP_ARGS=-m server.main          # ../GSpp_MCP/server/main.py

# MCP Server (Option B: HTTP/Streamable, GSpp_MCP deployed)
# BSI_GPP_MCP_MODE=sse
# BSI_GPP_MCP_URL=https://gs-plus-plus-mcp-xxx.a.run.app/mcp

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
│   │   └── {session_id}.json                      # Session-State (JSON)
│   ├── artifacts/
│   │   └── {session_id}/
│   │       ├── cis_oscal/
│   │       │   ├── component_definition.json/     # ADK-Versioned
│   │       │   │   ├── 0
│   │       │   │   └── 1
│   │       │   └── review_log.md/...
│   │       ├── vendor_evidence/...
│   │       └── policy_generator/...
│   └── inputs/                                    # User-Uploads (CIS-CSVs etc.)
└── iv-other-customer/
    └── ...
```

### Implementierung (bereits vorhanden, hier zur Referenz)

`services/artifact_service.py` hookt sich in `_get_blob_name` und
`_get_blob_prefix` ein und prefixed alle Pfade mit der IV-ID, die per Konvention
`{caller}::iv::{informationsverbund_id}` ins `user_id`-Feld kodiert wird:

```python
class InformationsverbundGcsArtifactService(GcsArtifactService):
    def _get_blob_name(self, app_name, user_id, filename, version, session_id=None):
        iv_id = self._extract_iv_id(user_id)
        if session_id is None:
            return f"{iv_id}/artifacts/no_session/{filename}/{version}"
        return f"{iv_id}/artifacts/{session_id}/{filename}/{version}"

    @staticmethod
    def _extract_iv_id(user_id: str) -> str:
        if "::iv::" not in user_id:
            return "default-iv"          # nur für Tests
        return user_id.split("::iv::", 1)[1]
```

`services/session_service.py` macht dasselbe für Sessions unter
`{iv_id}/sessions/{session_id}.json`.

### IV-Resolution im Orchestrator

Bei jedem ersten Turn prüft der Orchestrator, ob `informationsverbund_id` im
State liegt. Wenn nicht: User danach fragen, validieren (`^iv-[a-z0-9-]{3,40}$`),
in State schreiben, dann erst delegieren.

### Härtung (TODO)

Der `default-iv`-Fallback im Artifact-Service ist nur für Tests gedacht. Vor
Produktivbetrieb muss der Fallback in `services/` entfernt und durch ein
`raise ValueError` ersetzt werden, sobald der Tenant-Isolation-Test grün ist.

---

## 6. MCP-Server-Anbindung

Der MCP-Server ist [`../GSpp_MCP`](../GSpp_MCP) – siehe dessen README für
Tool-Surface, Catalog-Source-of-Truth und Cloud-Run-Deployment. Die für den
Agent relevanten Tools sind (Auswahl):

| Tool | Zweck |
|---|---|
| `catalog_info()` | Metadata, OSCAL-Version, Catalog-SHA |
| `list_groups()` | Gruppenhierarchie |
| `list_controls(group_id?, modalverb?, stufe?)` | gefilterte ID/Title-Liste |
| `get_control(id, include=[…])` | vollständiges Control |
| `search_controls(query, group_id?, limit=20)` | inverted-index-Ranking |
| `get_parameter(id)` | Parameter + Select-Werte |
| `find_referencing_controls(id)` | Backrefs |
| `list_zielobjektkategorien()` | Asset-Kategorien |
| `controls_for_zielobjekt(category)` | Controls pro Kategorie |

Stubs (für spätere Konsumption): `apply_profile`, `crosswalk_legacy`.

### Einbindung im Agent

`tools/bsi_gpp_mcp.py` ist als Factory implementiert und liest den Modus aus
`BSI_GPP_MCP_MODE`. Stdio-Modus für lokales Hacking, Streamable-HTTP für die
deployte Variante:

```python
def get_bsi_gpp_toolset() -> MCPToolset:
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

> **TODO Tool-Filtering:** Aktuell bekommen alle Sub-Agents alle MCP-Tools. Pro
> Workflow filtern (z.B. Reviewer braucht nur lesende Tools, kein
> `apply_profile`). Realisierung über `tool_filter` oder einen dünnen Wrapper.

---

## 7. Peer-Review-Pattern (Qualitätssicherung)

Jeder Domain-Workflow hat genau diese Topologie:

```
SequentialAgent("cis_oscal_workflow")
 ├── input_loader            (LlmAgent + GCS-Loader-Tool)
 ├── LoopAgent("review_loop", max_iterations=MAX_REVIEW_ITERATIONS)
 │    ├── producer           (LlmAgent, output_key="draft_artifact")
 │    └── reviewer           (LlmAgent, tools=[exit_loop])
 └── artifact_writer         (LlmAgent + GCS-Writer-Tool)
```

### Producer

- Liest Input + Kontext aus State
- Schreibt strukturierten Output (Pydantic-Schema aus `shared/schemas.py`!)
  nach `state["draft_artifact"]`
- Nutzt MCP-Tools für G++-Lookups

### Reviewer

- Liest `state["draft_artifact"]` + Original-Input
- Prüft gegen domain-spezifische Checkliste aus `shared/review_criteria.py`
- Wenn OK: ruft `exit_loop` Tool → Loop endet
- Wenn nicht OK: schreibt strukturiertes Feedback nach `state["review_feedback"]`,
  Loop läuft erneut, Producer sieht Feedback und korrigiert

### Exit-Loop-Tool (existiert)

`tools/exit_loop.py`:

```python
def exit_loop(reason: str, tool_context: ToolContext) -> dict:
    """Signal that the reviewed artifact is approved and the loop can exit."""
    tool_context.actions.escalate = True
    return {"status": "approved", "reason": reason}
```

### Review-Kriterien (TODO ausformulieren)

`shared/review_criteria.py` enthält pro Domain eine Pydantic-Klasse mit Checks.
Wird im Reviewer-Prompt als Strukturvorgabe verwendet. Skizze:

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

Wenn `MAX_REVIEW_ITERATIONS` erreicht wird, ohne Approval: `artifact_writer`
schreibt das letzte Draft + das gesamte Review-Log als Artefakt nach GCS und
markiert State mit `state["review_status"] = "failed"`. Orchestrator meldet
das dem User.

---

## 8. Workflow-Spezifikationen

### 8.1 Root Orchestrator (`orchestrator/agent.py`)

- `LlmAgent`, `model=ORCHESTRATOR_MODEL`
- Sub-Agents: `cis_oscal_workflow`, `vendor_evidence_workflow`, `policy_generator_workflow`
- Tools: nur Delegation und IV-Verwaltung (`set_informationsverbund`,
  `list_my_informationsverbuende`, `load_session`)
- Verhalten: erfragt IV bei jedem neuen Kontext, delegiert an Sub-Agent passend
  zur User-Intent

### 8.2 CIS→OSCAL Workflow (`agents/cis_oscal/`)

Pipeline `INPUT → CATALOG → MATCH → EMIT` (entspricht der bestehenden
One-Page-App `c5-oscal-converter.html`):

- `input_loader`: liest CIS-CSV/JSON aus dem IV-`inputs/`-GCS-Prefix
- `catalog_resolver`: bestimmt G++-Bausteine via MCP (`search_controls`,
  `list_controls`)
- `producer`: erstellt OSCAL Component Definition gegen OSCAL-1.1.2-Metaschema
- `reviewer`: prüft gegen `CisOscalReviewCriteria`
- `artifact_writer`: schreibt finale `component_definition.json`

### 8.3 Vendor Evidence Workflow (`agents/vendor_evidence/`)

Pipeline: Batch-Extraktion aus Hersteller-Dokumenten – analog zur One-Page-App
`pruefung_ap_ar.html` (Befundvorschlag-Funktion).

- `input_loader`: liest hochgeladene PDFs/Docs
- `producer`: extrahiert Evidence-Statements + mappt auf G++-Anforderungen via MCP
- `reviewer`: prüft Coverage, Quellzuordnung, keine erfundenen Zitate
- `artifact_writer`: CSV + Ground-Truth-Export

### 8.4 Policy Generator Workflow (`agents/policy_generator/`)

Pipeline: 17 Control-Domänen, pro Domain eigener Sub-Step (`ParallelAgent` über
die Domänen, dann Aggregation, dann Review). Zielausgabe analog zu
`blaupausen_generator.html` (Profil + Muster-SSP).

- `input_loader`: zieht Default-Profile aus
  [`../zielobjektkategorien/profile/`](../zielobjektkategorien/profile) und
  Default-Komponenten aus
  [`../zielobjektkategorien/komponenten/`](../zielobjektkategorien/komponenten);
  IV-spezifische Custom-Profile aus dem GCS-`inputs/`-Prefix überschreiben sie
- `producer`: pro Domain eine Policy als Markdown
- `reviewer`: prüft Konsistenz, G++-Mapping, Vollständigkeit
- `artifact_writer`: pro Domain ein PDF + ein zusammengefasstes PDF (TODO:
  WeasyPrint-Integration; aktuell nur Markdown)

### 8.5 Profile-Templates aus dem Geschwister-Verzeichnis

[`../zielobjektkategorien/`](../zielobjektkategorien) liefert OSCAL-Profile und
-Komponenten pro G++-Zielobjektkategorie (Administrierende, Cloud-Dienste,
Daten, IT-Systeme, Webserver, WLANs, …). Diese Artefakte sind:

- **Default-Eingangsmaterial** für Workflows, die Profile/Komponenten brauchen –
  insbesondere der Policy Generator und potenziell ein zukünftiger
  SSP-Building-Workflow.
- **Lifecycle-gekoppelt an den G++-Katalog:** Bei jedem neuen Katalog-Release
  müssen sie regeneriert werden, sonst funktionieren auch die
  [`../One-Page-Apps`](../One-Page-Apps) nicht mehr (die laden sie als
  Ressource). Das ist nicht-optionale Hygiene, nicht Roadmap.
- **Öffentliche Ressource** – die Artefakte sind bewusst Teil des Repos, damit
  externe Anwender sie für eigene Modellierungen nutzen können.

IV-spezifische Custom-Profile (z.B. ein angepasstes
`it-systeme_profile.json` für einen konkreten Kunden) kommen aus dem
GCS-`iv-{id}/inputs/`-Prefix und überlagern die Defaults pro Workflow-Run.
Default-Templates werden also nie pro IV verändert; alles IV-Spezifische lebt
ausschließlich in GCS.

> **Future Workflow (Roadmap):** Ein dedizierter `catalog_refresh_workflow`,
> der die Templates in `../zielobjektkategorien/` nach einem G++-Katalog-Update
> automatisch neu erzeugt. Aktuell ist das ein manueller Schritt – die Logik
> dafür existiert teilweise schon in
> [`../Gpp-ai-tool`](../Gpp-ai-tool) (Stages `match_bausteine`, `gpp`,
> `component`) und könnte als ADK-Workflow portiert werden.

---

## 9. Lokal ausführen

```bash
# Setup (im Gpp-Agent/-Verzeichnis)
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # und Werte setzen

# GCP Auth
gcloud auth application-default login

# MCP-Server starten (eigenes Terminal, im ../GSpp_MCP/-Verzeichnis)
cd ../GSpp_MCP && uv run python -m server.main

# Agent starten – CLI
adk run orchestrator

# Agent starten – Web UI (nur dev, NICHT für Produktion)
adk web --port 8000
```

---

## 10. Deployment

Ziel: Cloud Run für den Orchestrator, MCP-Server separat unter `../GSpp_MCP`
deployt. Der Agent bekommt die MCP-URL über `BSI_GPP_MCP_URL` und ruft sie mit
einem Google-Bearer-Token (Cloud Run IAM, `roles/run.invoker`) auf.

```bash
adk deploy cloud-run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service-name=grundschutz-pp-agent \
  orchestrator
```

`deployment/Dockerfile` enthält:
- Python 3.11-slim
- `google-adk`, `google-cloud-storage`, `mcp`
- ENV-Vars aus Cloud-Run-Konfiguration (nicht aus `.env`!)

Service-Account-Rollen für den Agent:
- `roles/storage.objectAdmin` auf `gs-pp-agent-{env}` Bucket
- `roles/aiplatform.user`
- `roles/run.invoker` auf den GSpp_MCP-Service

Region-Empfehlung: **`europe-west3` (Frankfurt)** – konsistent mit
[`../GSpp_MCP`](../GSpp_MCP/README.md#region) für EU-Datenresidenz.

---

## 11. Tests

- **Unit:** Pydantic-Schemas, IV-Namespacing-Logik, exit_loop-Tool, Review-Kriterien
- **Integration:** End-to-End mit Mock-MCP-Server (oder dem realen ../GSpp_MCP
  als Sidecar) und einem Test-IV gegen einen Test-Bucket. **Mindestens ein
  vollständiger CIS→OSCAL-Run mit Review-Loop, der in der ersten Iteration
  scheitert und in der zweiten approved wird** – um den Loop-Mechanismus
  tatsächlich zu validieren.
- **Tenant-Isolation-Test (Pflicht):** Zwei IVs schreiben parallel, beide
  Sessions dürfen sich nicht sehen.

---

## 12. Definition of Done für Jules

Schließt direkt an [`./tasks.md`](./tasks.md) an. Dort ist der IST-Zustand
dokumentiert; hier sind die nächsten Schritte.

### Fachliche Implementierung

- [ ] **Prompts auslagern** nach `shared/prompts/{domain}/{producer|reviewer}.md`
  mit YAML-Frontmatter (`id`, `version`, `output_schema`). Producer/Reviewer-Code
  lädt sie via Helper-Funktion in `shared/__init__.py`.
- [ ] **GCS Input Loading** in `agents/*/tools.py` – Mocks durch echte
  `google-cloud-storage`-Aufrufe ersetzen. Lesen aus `iv-{id}/inputs/`,
  Schreiben nach `iv-{id}/artifacts/{session_id}/{domain}/`.
- [ ] **OSCAL-Vollständigkeit:** `OscalComponentDefinition` in
  `shared/schemas.py` gegen das offizielle OSCAL-1.1.2-Metaschema vervollständigen.
  Validator in `shared/validators.py`, der gegen das Metaschema validiert (z.B.
  via `jsonschema`).
- [ ] **Review-Kriterien pro Domain** in `shared/review_criteria.py` ausformulieren
  (CisOscalReviewCriteria, VendorEvidenceReviewCriteria, PolicyReviewCriteria).
- [ ] **PDF-Generierung** im Policy-Generator: WeasyPrint-Integration im
  `artifact_writer`, pro Domain ein PDF und ein Gesamt-PDF.
- [ ] **MCP Tool-Filtering** pro Sub-Agent (Reviewer braucht keine
  schreibenden/teuren Tools).

### Sicherheit & Härtung

- [ ] **`default-iv`-Fallback entfernen** in `services/artifact_service.py`
  und `services/session_service.py` – durch `raise ValueError` ersetzen,
  sobald Tenant-Isolation-Test grün ist.
- [ ] **AuthN-Entscheidung:** IAP vor dem Cloud-Run-Service oder
  in-app via Bearer-Token? (Empfehlung: IAP, weil zero-code).
- [ ] **Audit-Log** persistent außerhalb des Session-States, z.B. als
  separates Cloud-Logging-Sink mit `iv_id`-Label.

### Tests

- [ ] **Tenant-Isolation-Test:** zwei parallele IV-Sessions, prüft Null-Leckage.
- [ ] **End-to-End-Loop-Test:** Mock-Reviewer lehnt 1. Iteration ab, approved
  2. Iteration; finales Artefakt liegt korrekt im IV-Prefix.
- [ ] **MCP-Sidecar-Test:** Container-basiertes Setup im CI mit echtem
  `../GSpp_MCP` als Sidecar.

### Dokumentation

- [ ] Diese README aktualisieren, falls signifikante Abweichungen entstehen.
- [ ] [`./tasks.md`](./tasks.md) am Ende des Sprints fortschreiben.

---

## 13. Open Points (vor erstem Build mit Christoph klären)

1. **Workflow-Reihenfolge der Vervollständigung?** Empfehlung weiterhin:
   **Vendor Evidence zuerst**, weil einfachste Pipeline-Topologie und
   schnellster End-to-End-Smoke-Test.
2. **`apply_profile` im MCP** ist Stub. Soll der Agent das Stub-Verhalten
   bereits konsumieren (mit Fallback) oder erst nach echter Implementierung
   in `../GSpp_MCP` ansprechen?
3. **AuthN:** IAP davor oder in-app? Bei IAP: keine Code-Änderungen, dafür
   weniger Flexibilität bei Service-zu-Service-Calls.
4. **Audit-Logging:** separates Cloud-Logging-Sink (zero-code, gute
   Compliance-Story) oder über `state["audit_log"]` in der Session
   (testbarer, aber muss aktiv geschrieben werden)?
5. **Beispielkataloge:** [`../beispiel-kataloge/`](../beispiel-kataloge/)
   (DSGVO, KRITIS) – als Demo-Inputs für E2E-Tests einbauen?
