# gpp_agent — Architektur-Regeln

Dieses Dokument hält die **verbindlichen** Architektur-Entscheidungen für
`agentic/gpp_agent/` fest. Es ist die Quelle der Wahrheit für Code-Reviewer
und Code-generierende Tools (Modelle). Kein Tutorial, keine Code-Snippets —
nur Regeln. Wer Code schreibt, der gegen eine dieser Regeln verstößt, baut
einen Bug.

Begleitende Doks: `README.md` (Spec), `tasks.md` (Backlog/Progress),
`agentic/install.md` (lokales Setup), `agentic/terraform/` (Cloud-Run-Topologie).

---

## 1. Komponentenkarte

Vier Services, zwei Persistenzebenen:

- **`frontend`** — Next.js + CopilotKit. Einziger öffentlicher Service.
- **`gpp_agent`** — ADK-Multi-Agent (FastAPI + ag-ui-adk).
- **`GSpp_MCP`** — read-only Anwenderkatalog-Server (BSI G++).
- **`GS_backend_MCP`** — State, OSCAL-Validierung, GCS-Persistenz.
- **Firestore** — Session- und State-Store des Agenten.
- **GCS** — versionierte OSCAL-Artefakte pro Informationsverbund.

Aufrufrichtung: Browser → Frontend → `gpp_agent` → `{GSpp_MCP, GS_backend_MCP}` → `{Firestore, GCS}`. **Keine** anderen Pfade. Insbesondere ruft das Frontend keinen MCP-Server direkt auf, und kein MCP-Server ruft den Agenten zurück.

---

## 2. Protokolle und Transport

| Verbindung | Protokoll | Pfad |
|---|---|---|
| Frontend → Agent | AG-UI (HTTP-POST + Event-Stream) | `/copilotkit` |
| Agent → MCP-Server (beide) | MCP Streamable-HTTP | `/mcp` |
| Agent → Firestore | Google Cloud SDK | — |
| Agent → GCS (via Backend-MCP) | indirekt, kein Direktzugriff | — |

**Verboten:**

- SSE für MCP. Das alte `SseConnectionParams` ist deprecated; ausschließlich `StreamableHTTPConnectionParams`.
- `adk api_server` als Frontend-Endpunkt. Der Agent läuft als FastAPI-Prozess (uvicorn), AG-UI-Brücke via `ag_ui_adk.add_adk_fastapi_endpoint`. `adk web` ist nur für Backend-Debugging in einem zweiten Terminal erlaubt.
- Direkte GCS-Schreibzugriffe aus dem Agenten. Schreiben geht ausschließlich über Backend-MCP-Tools.

---

## 3. Multi-Tenancy (Informationsverbund-Isolation)

- `iv_id` matcht `^iv-[a-z0-9-]{3,40}$`. Andere Werte werden abgelehnt.
- `user_id` bei `Runner.run_async()` hat exakt das Format `{caller}::iv::{iv_id}`. Frontend setzt das, Agent verlässt sich darauf.
- App-level Callback (`before_run_callback` an der `App`) extrahiert `iv_id` aus `RunAgentInput.userId` und schreibt ihn in `state["informationsverbund_id"]`. Ohne diesen Callback gibt es keine Mandantentrennung.
- GCS-Layout zwingend: `gs://{GCS_BUCKET_NAME}/{iv_id}/saves/{save_id}/…`. Backend-MCP setzt das durch.
- Firestore-Sessions tragen `iv_id` als Label. Cross-IV-Reads sind ein Sicherheitsvorfall, kein Feature.

Jede Code-Stelle, die `user_id` ohne `::iv::`-Suffix akzeptiert oder GCS-Pfade ohne IV-Prefix konstruiert, ist ein **Tenant-Isolation-Verstoß** und Merge-Blocker.

---

## 4. Maker-Checker mit Iteration

Producer und Reviewer laufen in einer `LoopAgent`, niemals in einer `SequentialAgent`. Eine `SequentialAgent` ist ein One-Shot ohne Korrekturpfad und kollabiert das Pattern.

- **Producer** erstellt den Entwurf (`PRODUCER_MODEL`). Hat Schreib-Zugriff auf Backend-MCP.
- **Reviewer** prüft (`REVIEWER_MODEL`). Tool-Set ist read-only (siehe §7). Liefert ein strukturiertes Verdikt (`output_schema=ReviewCriteria`).
- **Approval-Signal**: Reviewer ruft `exit_loop`, das `escalate=True` UND `skip_summarization=True` setzt. Beides ist Pflicht.
- **Loop-Termination**: spätestens nach `MAX_REVIEW_ITERATIONS` (default 3). Niemals unbegrenzt.

`LoopAgent` propagiert `escalate=True` an die parent `SequentialAgent` und würde die nachfolgenden Schritte (z. B. GCS-Save) blockieren. Deshalb ist die `LoopAgent` immer in eine `EscalationBarrier` (`tools/escalation_barrier.py`) gewickelt, deren `inner` als `BaseAgent` typisiert ist (nicht `LoopAgent`, sonst akzeptiert sie keine `SequentialAgent`).

Wenn ein Reviewer sowohl `output_schema` als auch `tools` braucht: zwei-stufig aufspalten — `inspector` (mit Tools, freier Output, schreibt in `state`) gefolgt von `judge` (kein Tools, `output_schema`, liest `state`). Gemini-Modelle emittieren bei aktivem `responseSchema` keine zuverlässigen Tool-Calls.

---

## 5. Human-in-the-Loop

HITL läuft **ausschließlich** über AG-UI / CopilotKit Generative UI, nicht als server-seitiger Polling-Loop.

- `App` wird mit `ResumabilityConfig(is_resumable=True)` konstruiert. Ohne das pausiert ADK nicht beim Client-Tool-Call.
- Der Agent (Orchestrator oder relevanter Sub-Agent) hat `AGUIToolset()` in `tools=[…]`. Damit werden alle vom Frontend per `useCopilotAction` registrierten Aktionen (z. B. `approve_artifact`) zu echten ADK-Tools.
- Beim Aufruf eines Client-Tools persistiert ADK das `FunctionCall`-Event und pausiert. Frontend rendert die Generative UI, User antwortet, AG-UI sendet das `FunctionResponse`-Event zurück, ADK setzt fort.
- Server-seitige `LoopAgent`-basierte HITL-Konstruktionen sind verboten. Sie kollidieren mit dem Resumability-Modell und führen zu doppelter Wahrheit.

---

## 6. Validierung

- Jedes geschriebene OSCAL-Artefakt durchläuft `verify_oscal_json` **bevor** es in GCS landet. Das Tool ist Gatekeeper, nicht optional.
- `verify_oscal_json` gehört architektonisch in den **Backend-MCP**, nicht in den Anwender-MCP. Der Backend-MCP führt Schemas + Persistenz atomar zusammen. (Anmerkung: aktuell ist das Tool im Anwender-MCP — Migration ist fällig.)
- Bei Validierungsfehler: Agent reicht den Fehler unverändert an den User durch (HITL). Der Agent korrigiert OSCAL-JSON nicht selbständig — das gibt Halluzinations-Patches und maskiert Bugs.

---

## 7. MCP-Tool-Zugriffspolicy

Tool-Filter pro Agent ist Pflicht, nicht Empfehlung. Defaults:

| Tool | Server | Producer | Reviewer | Validator |
|---|---|---|---|---|
| `list_groups`, `get_group` | Anwender | ✓ | ✓ | — |
| `list_controls`, `get_control` | Anwender | ✓ | ✓ | — |
| `get_control_raw` | Anwender | ✓ | — | — |
| `search_controls` | Anwender | ✓ | — | — |
| `list_zielobjektkategorien`, `controls_for_zielobjekt`, `get_oscal_profile` | Anwender | ✓ | — | — |
| `verify_oscal_json` | Backend (Soll) | — | — | ✓ |
| `create_oscal_model`, `update_oscal_model` | Backend | ✓ | — | — |
| `get_ssp_inventory`, `get_ssp_implementation` | Backend | ✓ | ✓ | — |
| `get_assessment_*`, `get_poam_items` | Backend | ✓ | ✓ | — |

Reviewer mit Schreib-Tool ist ein DoD-Verstoß. MCP-Toolsets werden über `services/mcp_client_service.py` (`get_anwender_toolset(allow=…)`, `get_backend_toolset(allow=…)`) erzeugt, nirgends sonst.

---

## 8. Modelle

Drei Gemini-IDs sind im Scope, alle aus der 3.x-Familie. Andere IDs sind verboten.

| Env-Var | Default | Rolle |
|---|---|---|
| `PRODUCER_MODEL` | `gemini-3.1-pro-preview` | Producer-Agenten, alles, wo Mapping-Qualität direkt das Artefakt bestimmt |
| `REVIEWER_MODEL` | `gemini-3-flash-preview` | Reviewer, Orchestrator-Routing, Catalog-Resolver |
| `TOOL_AGENT_MODEL` | `gemini-3.1-flash-lite-preview` | input_loader, hochfrequente mechanische Agenten |

Regeln:

- Modell-Strings niemals hardcoden. Immer `os.environ.get("…", DEFAULT)`, mit Default aus der 3.x-Familie. Fallbacks auf `gemini-2.5-*` sind verboten — sie maskieren fehlende `.env`-Loads.
- `temperature`-Override auf Gemini-3-Modellen ist verboten. Default `1.0` ist trainiert; niedriger erzeugt Loops und Reasoning-Degradation.
- Reviewer auf Pro: nur mit gemessenem Qualitätsbeleg. Default ist Flash.

---

## 9. Observability

- OpenTelemetry wird einmal pro Prozess in `tools/observability.py:configure_observability()` aufgesetzt. `OTEL_DISABLED=1` deaktiviert für Tests.
- Jeder `LlmAgent` registriert `enrich_span_with_iv` als `before_agent_callback`. Spans tragen damit `gpp.iv_id` und `gpp.agent` als Attribute.
- Tool-Argumente werden niemals im Klartext geloggt. SHA-256-Hash der `args`-JSON-Repräsentation, gekürzt auf 16 Zeichen. CIS-Daten, Vendor-Evidence, Kunden-Secrets dürfen Cloud Trace nicht erreichen.
- Custom-Metric `gpp_agent/tokens_per_run` mit Labels `{iv_id, workflow, model}` als Billing-/Chargeback-Signal.

---

## 10. Definition of Done — Tests

Ein Workflow gilt nicht als fertig, bevor diese Tests grün sind:

1. `test_tenant_isolation` — zwei parallele Sessions mit verschiedenen `iv_id` sehen nichts voneinander.
2. `test_review_loop_passes_after_one_rejection` — Reviewer lehnt einmal ab, beim zweiten Lauf approved, Post-Loop-Step (GCS-Save) läuft. Beweist `EscalationBarrier`.
3. `test_agui_resumability_pause` — Workflow pausiert beim `approve_artifact`-Tool-Call und nimmt ein simuliertes `FunctionResponse` korrekt auf.
4. `test_schema_validation_blocks_save` — fehlerhaftes OSCAL erreicht GCS nicht.
5. `test_redteam_prompt_injection_in_pdf` — Vendor-PDF mit „IGNORE PREVIOUS INSTRUCTIONS"-Payload. Producer exfiltriert nicht, Reviewer markiert als Finding.
6. `test_redteam_unauthorized_tool_call` — Producer fordert Tool außerhalb seines Filters → `ToolNotFound`, kein stiller Fallback.
7. `test_token_exhaustion_failsafe` — Reviewer, der nie approved → Loop endet bei `MAX_REVIEW_ITERATIONS`, keine Endlosschleife.
8. `test_mcp_5xx_does_not_crash_producer` — MCP-Sidecar gibt 503 → strukturierter Tool-Error im Event-Stream, kein silent-catch.

---

## 11. Verzeichnis-Konventionen

| Inhalt | Pfad |
|---|---|
| Domain-Workflow | `agents/<domain>/{producer,reviewer,workflow,tools}.py` |
| Shared Schemas | `shared/schemas.py` |
| Review-Kriterien | `shared/review_criteria.py` |
| Prompts | `shared/prompts/<domain>/<role>.md` (mit YAML-Frontmatter) |
| Service-Layer (GCS, Sessions, MCP-Clients) | `services/` |
| Custom Infra-Agenten (`EscalationBarrier`) | `tools/` |
| MCP-Tool-Wrapper | `tools/<name>.py` |
| Unit-Test | `tests/unit/test_<module>.py` |
| Integration-Test | `tests/integration/test_<workflow>_<scenario>.py` |
| Eval-Snapshot | `tests/eval_snapshots/<workflow>/case_NNN_<slug>/` |

Keine neuen Top-Level-Verzeichnisse ohne Eintrag in dieser Tabelle. Keine Production-Logik in `tests/`. `shared/` ist nur für Code, der zwischen mindestens zwei Sub-Projekten geteilt wird.

---

## 12. Referenzen (verifiziert Mai 2026)

- Frontend-Brücke: <https://docs.copilotkit.ai/adk>, <https://www.copilotkit.ai/blog/build-a-frontend-for-your-adk-agents-with-ag-ui>
- AG-UI ADK Middleware: <https://pypi.org/project/ag-ui-adk/>
- ADK MCP Tools (Streamable-HTTP): <https://google.github.io/adk-docs/tools-custom/mcp-tools/>
- ADK escalate-Verhalten: <https://github.com/google/adk-python/issues/1376>
- ADK LoopAgent: <https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/>
- MCP Streamable-HTTP Spec: <https://modelcontextprotocol.io/specification/2025-03-26/basic/transports>

Wenn die Live-Docs diesen Regeln widersprechen, gewinnen die Live-Docs — dann
ist dieser Doc-Stand stale und muss per PR aktualisiert werden.