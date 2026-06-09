# issues.md — Global Code Review of `agentic/`

Review date: 2026-06-09 (agentic-only review, live deployment in `gpp-agentic-3` / `europe-west3` inspected).
Updated 2026-06-09 (evening): P0-1 resolved; new findings from the first real playground run added
(P0-4, P1-20…22, P2-23) plus an architecture review summary.

**Verified working (so you don't chase ghosts):**

- Both MCP servers on Cloud Run are healthy and answer correctly when called with a
  proper Streamable-HTTP handshake + IAM identity token. `initialize`, `tools/list`
  and `tools/call` all succeed. Backend tenant isolation works: calls without
  `X-Gpp-User-Id` are rejected, calls with `X-Gpp-User-Id: probe::iv::iv-test-001`
  succeed.
- The workspace lock (`agentic/uv.lock`) pins `google-adk==2.0.0b1`; `uv export --locked`
  produces correct requirements. The whole agent graph (`app.agent`, `app.agent_runtime_app`)
  imports and builds cleanly against it, including `McpToolset(header_provider=…)`,
  `Workflow`, `Event`, `RequestInput`, `ResumabilityConfig`.
- `gpp-agent` unit + integration tests: **16 passed, 1 skipped** (needs
  `GOOGLE_CLOUD_PROJECT` set, see P2-13).
- Terraform infra is deployed and consistent: 3 Cloud Run services Ready, reasoning
  engine exists, MCP env vars on the engine point at the right Cloud Run URLs.

---

## P0 — Blockers (this is why "nothing answers")

### P0-1: ~~The deployed Agent Engine is still the Terraform *dummy placeholder*~~ — **RESOLVED 2026-06-09**

`scripts/deploy_gpp_agent.sh` was run; the real agent now answers in the Agent Engine
playground and engine logs show it connecting to the MCP servers. **Keep the procedure:**
after every `terraform destroy`/recreate of the engine, the dummy source is live again
until `scripts/deploy_gpp_agent.sh` is re-run. Original finding kept below for the record.

**Evidence:**

- `terraform/service.tf` creates the engine from `dummy_source.b64` ("You are a
  placeholder agent … Please deploy the real agent via CI/CD."). The live engine
  `7181464594865455104` was created 2026-06-09 20:01 by Terraform.
- Engine startup logs (20:04) show `proceeding without Google GenAI instrumentation,
  because opentelemetry-instrumentation-google-genai has not been installed` — that
  package is pinned by the real app but absent from the dummy's requirements. The
  running code is the dummy.
- `gpp-agent/deployment_metadata.json` points at engine `5410846253867073536`
  (deployed 2026-05-25) which **no longer exists** — terraform destroy/recreate left
  the metadata stale and the real code was never re-deployed to the new engine.

**Impact:** The dummy agent has no MCP toolsets. Nothing ever calls the MCP servers —
this is the primary cause of "the MCP servers do not answer". They answer fine; nobody calls them.

**Fix:**

1. Run `scripts/deploy_gpp_agent.sh` (i.e. `agents-cli deploy` from `gpp-agent/`).
   Verified: agents-cli matches the engine by display name (`gpp-agent`), so it will
   *update* the Terraform engine, not create a second one. The stale metadata file is
   overwritten on success.
2. After every `terraform destroy`/recreate of the engine, the real source **must** be
   re-deployed. Add this as a documented post-apply step, or have Terraform trigger
   the deploy (e.g. a `null_resource` calling the deploy script), so the dummy can
   never linger.
3. Verify after deploy: engine logs must show the OTel GenAI instrumentation loading,
   and `ANWENDER_MCP_URL`/`BACKEND_MCP_URL` env vars are preserved (the deploy script
   passes them via `--update-env-vars` — confirm the update doesn't drop the
   Terraform-set env block).

### P0-2: Frontend ↔ Agent protocol mismatch — no user request can reach the agent

**Evidence:**

- `frontend/app/api/copilotkit/route.ts` registers `AGENT_URL` as a CopilotKit
  `remoteEndpoints` entry. CopilotKit remote endpoints speak the CopilotKit
  runtime/AG-UI protocol (`/info`, action discovery, event streams).
- Terraform sets `AGENT_URL` to
  `https://europe-west3-aiplatform.googleapis.com/v1beta1/projects/...:query` — the
  Agent Engine REST endpoint, which speaks neither CopilotKit nor AG-UI. The comment in
  `terraform/main.tf` even admits this ("don't expose a /copilotkit route").
- Auth is also wrong for that URL: the route fetches a **Cloud Run identity token**
  from the metadata server with `audience = origin`. `aiplatform.googleapis.com`
  requires an **OAuth2 access token** (plus `roles/aiplatform.user` on the caller),
  and `gpp-frontend-sa` is granted no AI Platform role anywhere in `terraform/iam.tf`.

**Impact:** Even with the real agent deployed (P0-1), the frontend cannot talk to it.
End-to-end chat is structurally broken.

**Fix — decide one architecture and align everything:**

- **Option A (matches `architecture.md`):** run gpp-agent as its own Cloud Run FastAPI
  service using `ag_ui_adk.add_adk_fastapi_endpoint` (`/copilotkit`), point
  `AGENT_URL` at it, keep Cloud Run-to-Cloud Run identity-token auth (the current
  route.ts auth code is correct for that case). Note: `ag-ui-adk` is currently not a
  dependency anywhere — it must be added, and its ADK 2.0 compatibility verified.
- **Option B (keep Agent Runtime):** put a translation layer in the Next.js API route
  (or a small backend) that converts CopilotKit messages to
  `reasoningEngines.streamQuery` calls with a proper OAuth access token
  (`google-auth-library` `getAccessToken`, SA needs `roles/aiplatform.user`), and maps
  ADK events (incl. `RequestInput` interrupts) back to CopilotKit.
- Whichever option: grant the required IAM to `gpp-frontend-sa` and delete the stray
  `terraform/route.ts` draft (see P2-17).

### P0-3: Tenant-isolation chain is broken at the source — backend tools will fail for every real user

**Evidence:**

- `architecture.md` §3: frontend must set `user_id = {caller}::iv::{iv_id}`; an
  app-level callback must extract `iv_id` into state. Neither exists:
  - `frontend/app/page.tsx` / `route.ts` never set any user id or IV.
  - `gpp-agent/app/agent.py` constructs `App(...)` with no `before_run_callback` /
    user-id plumbing; there is no IV validation (`^iv-[a-z0-9-]{3,40}$`) anywhere in
    the agent.
- `app/mcp_clients.py` forwards `session.user_id` as `X-Gpp-User-Id` — correct — but
  the session user id will never contain `::iv::` because nothing upstream sets it.
- Live-verified: backend MCP rejects tool calls without the header
  (`Tenant isolation violation: Missing or malformed iv_id in context`).

**Impact:** Once P0-1/P0-2 are fixed, *every* backend MCP tool call will return the
tenant-isolation error. From the user's perspective: "the MCP server does not answer".

**Fix:**

1. Frontend: add an Informationsverbund selector (or config) and send
   `userId = {caller}::iv::{iv_id}` with each request (CopilotKit forwards properties /
   or embed in the runtime call for Option B).
2. Agent: validate the IV format on entry (App-level callback per architecture.md) and
   write it to `state["informationsverbund_id"]`.
3. Add the architecture-mandated `test_tenant_isolation` integration test.

### P0-4: The workflow has no path that can *create* an SSP

**Evidence:**

- The classifier prompt routes "create a new SSP" to Phase 1 / `govern` — pinned by
  `tests/unit/test_dummy.py::test_classifier_prompt_routes_new_ssp_to_govern`.
- Phase 1's `_BACKEND_TOOLS` allow-list (`app/agents/phase1_governance.py`) is
  read-only: `get_ssp_inventory`, `get_ssp_implementation`, `get_oscal_model_raw`,
  `list_oscal_models`.
- `create_oscal_model` / `update_oscal_model` are allow-listed only in Phase 4
  (gatekeeper — itself odd, a reviewer with write tools violates architecture.md §7)
  and Phase 5 (remediation).

**Impact:** Every phase assumes the SSP already exists in GCS. The most common first
user request — "lege ein SSP an" — structurally cannot succeed: Phase 1 reads nothing,
finds nothing, and reports "the SSP could not be retrieved" (observed in the playground
2026-06-09). The backend MCP itself creates SSPs fine (verified live); the *graph*
never asks it to.

**Fix (pick one):**

- Extend Phase 1 with `create_oscal_model`/`update_oscal_model` and prompt it to
  bootstrap a schema-valid skeleton SSP (the OSCAL 1.2.2 schema requires `uuid`,
  `metadata`, `import-profile`, `system-characteristics`, `system-implementation`,
  `control-implementation`; backend validation errors flow back verbatim, so the model
  can iterate), or
- add a dedicated `intake` phase + classifier route that owns SSP creation, keeping
  Phase 1 read-only.

Update the graph-structure tests in `tests/integration/test_agent.py` accordingly.

---

## P1 — High: will bite immediately after P0 is fixed

### P1-4: Every phase agent combines `tools=[…]` with `output_schema=…`

`app/agents/phase1…phase5` all set both. `architecture.md` §4 explicitly forbids this
("Gemini models do not emit reliable tool calls when a responseSchema is active — split
into inspector + judge"). ADK 2.0.0b1 accepts the combination silently (verified), but
the model is likely to emit the structured answer **without ever calling the MCP
tools** — the second contributor to "MCP servers don't answer", and it will produce
hallucinated findings instead of data-driven ones.

**Fix:** per phase, split into a tool-using inspector (free text / `output_key`) and a
schema-bound judge, or drop `output_schema` and validate the JSON downstream. Then add
an eval case asserting that the phase actually called e.g. `get_ssp_inventory`
(tool-trajectory metric in `agents-cli eval`).

### P1-5: `classifier_route` is never cleared from session state

`classify_router` (`app/agents/orchestrator.py`) reads
`ctx.session.state.get("classifier_route")` and routes whenever it is set. The
classifier tool writes it but nothing ever deletes it. On the next user turn in the
same session, the router will see the *previous* turn's route and dispatch a phase
even if the classifier just asked a clarifying question.

**Fix:** clear it when consumed, e.g. return
`Event(route=…, state={"classifier_route": None, "current_phase": …})`.

### P1-6: HITL gates and the frontend speak different mechanisms

The Workflow gates yield ADK `RequestInput` interrupts (`gate_phase1…5`), while the
frontend only registers a CopilotKit `useCopilotAction("approve_artifact")` —
a client-side tool the agent never calls (no `AGUIToolset` anywhere, contrary to
`architecture.md` §5). No code path renders the gate prompts or returns
`continue|stop` / `cleared|blocked` to the workflow, so every workflow run will hang
at the first gate.

**Fix:** decide the HITL transport as part of P0-2: either AG-UI client tools
(`AGUIToolset` + `useCopilotAction` names matching the gate semantics) or explicit
handling of ADK resumability interrupts in the bridge. Then add the
`test_agui_resumability_pause` test required by architecture.md §10.

### P1-7: Stateful MCP sessions on autoscaling Cloud Run

Both FastMCP servers run session-based Streamable-HTTP (`stateless_http=True` is
commented out in `GSpp_MCP/server/main.py`; backend identical). Cloud Run has no
session affinity configured and no max-instance pin, so as soon as a service scales
past one instance, follow-up requests carrying `Mcp-Session-Id` land on instances
that don't know the session → 404s that look exactly like "MCP doesn't answer"
intermittently. Works today only because traffic is ~zero.

**Fix:** both servers are effectively stateless (read-only catalog / per-call GCS
state) — enable `stateless_http=True` on both `FastMCP(...)` constructors. Alternatively
pin `max_instance_count = 1` and enable session affinity in Terraform, but stateless is
the right call here.

### P1-8: ID-token fetch failures are silently swallowed in the agent

`app/mcp_clients.py:_id_token_for` returns `None` on *any* exception. If
`fetch_id_token` fails inside Agent Engine (ADC quirks, audience issues), every MCP
request goes out unauthenticated, Cloud Run returns 401/403, and the only symptom is
"tools don't work". Also: `from google.auth import compute_engine, default` is unused.

**Fix:** log the exception at ERROR with the audience URL (no secrets), and consider
failing fast for non-localhost URLs instead of degrading to anonymous. Remove the dead
imports. Add a startup self-check that does an MCP `initialize` against both servers
and logs the result.

### P1-9: Default model wiring contradicts the docs and is expensive

- All six agent factories default to `ORCHESTRATOR_MODEL` → `gemini-3.1-pro-preview`,
  while `architecture.md` §8 and `.env.example` say the orchestrator/classifier should
  run on Flash (`gemini-3-flash-preview`).
- The live engine has **no model env vars at all** (verified via REST), so after P0-1
  everything — including the classifier — runs on 3.1 Pro.

**Fix:** set the per-role env vars in `terraform/service.tf` (engine `env` block) and
align code defaults with architecture.md (classifier/Flash, producers/Pro).

### P1-20: MCP cold-start race breaks tool discovery (observed live)

**Evidence (engine + Cloud Run logs, 2026-06-09 20:33):**

- Backend MCP had scaled to zero. Cloud Run started a new instance at 20:33:35
  ("Reason: AUTOSCALING"); the container then spent ~7 s doing `uv` dependency work
  *at startup* ("Building gpp-context-mcp", "Installed 6 packages") before uvicorn was
  ready at 20:33:42.
- The engine's tool listing hit that window: 20:33:40
  `Failed to get tools from toolset McpToolset: Failed to create MCP session:` —
  with an **empty** error message — followed by
  `Error on session runner task: unhandled errors in a TaskGroup`.
- A retry at 20:33:52 connected fine (session created, `ListToolsRequest` processed),
  but the model had already answered "backend tool access is currently unavailable".

**Impact:** Any first request after an idle period sees "no backend tools" — looks
identical to an outage. This was the actual cause of the first playground failure.

**Fix:**

1. `terraform/main.tf`: `min_instance_count = 1` (template `scaling` block) for both
   `backend_mcp_service` and `gspp_mcp_service`.
2. `app/mcp_clients.py`: pass explicit generous `timeout` / `sse_read_timeout` to
   `StreamableHTTPConnectionParams` (e.g. 30 s) to survive cold starts.
3. `GS_backend_MCP/Dockerfile.mcp`: finish `uv sync` at build time and `exec` the
   venv's python directly in CMD — no `uv run` dependency resolution at container
   start.
4. Make the empty-error logging loud (overlaps P1-8): log the MCP URL and underlying
   exception when session creation fails.

### P1-21: Playground testing has no tenant — backend tools always rejected

The Agent Engine playground runs with `userId=user` (no `::iv::` suffix), so even with
a working MCP connection every backend tool call returns
`Tenant isolation violation: Missing or malformed iv_id in context` (verified live).

**Dev-only workaround (code support already exists in
`GS_backend_MCP/myserver/utils.py`):** set on the backend MCP Cloud Run service:

```
GPP_BACKEND_ALLOW_DEV_IV_FALLBACK=1
GPP_BACKEND_DEV_IV_ID=iv-dev-playground
```

Set it in the Terraform env block (one owner — see P2-23), clearly marked dev-only,
and remove it before any non-dev exposure. The real fix remains P0-3.

### P1-22: `scripts/deploy_frontend.sh` is broken and contradicts Terraform

The script reads `terraform output -raw gpp_agent_url` — **that output does not
exist** in `terraform/outputs.tf`, so the script aborts via `set -e`. It also appends
`/copilotkit` to the URL, i.e. it was written for the Cloud-Run-FastAPI architecture
(Option A), while `terraform/main.tf` wires the Agent-Engine `:query` URL (Option B)
into the same service. Two halves of two different architectures. Fold the fix into
the P0-2 transport decision; until then the script is dead code.

---

## P2 — Medium: hygiene, drift, and broken dev workflows

### P2-10: Stale nested lockfiles pin ADK 1.31.1

`gpp-agent/uv.lock` and `GS_backend_MCP/uv.lock` are leftovers from before the uv
workspace existed. `gpp-agent/uv.lock` records `google-adk >=1.15.0,<2.0.0` →
`1.31.1`, which cannot import `google.adk.Workflow`. uv ignores them (workspace root
lock wins — verified), but any tool or human resolving from the member directory will
get a broken environment. **Delete both nested `uv.lock` files.**

### P2-11: Two parallel Terraform/CI-CD trees

`agentic/terraform/` is the live infra. `gpp-agent/deployment/terraform/{cicd,single-project}`
plus `gpp-agent/.cloudbuild/*.yaml` are the unused agents-cli scaffold (GitHub
connection, triggers, its own engine, its own buckets). Keeping both invites someone
to apply the wrong one.

**Fix:** delete the scaffolded tree (or move it to `docs/reference/`), or commit to it
and fold `agentic/terraform` into it. Document the choice in `install.md`.

### P2-12: Duplicate/broken Dockerfile in GS_backend_MCP

`GS_backend_MCP/cloudbuild.yaml` builds `Dockerfile.mcp` (correct). The sibling
`Dockerfile` is broken for that build context (`COPY GS_backend_MCP/pyproject.toml`
does not exist inside the context) and is not referenced by anything. Delete or fix it —
right now it's a trap for anyone building manually.

### P2-13: MCP server test suites don't run at all; packaging metadata is wrong

- `uv run pytest GSpp_MCP/tests GS_backend_MCP/tests` fails collection:
  `ModuleNotFoundError: No module named 'GS_backend_MCP'` / `'myserver'`. The packages
  aren't importable from the workspace venv and there's no `pythonpath` config.
- Two backend test modules import `myserver.*`, the rest `GS_backend_MCP.myserver.*` —
  inconsistent.
- Both MCP `pyproject.toml`s declare hatch wheel packages that don't match the layout
  (`packages = ["GS_backend_MCP", "myserver"]` resp. `["GSpp_MCP"]` — neither path
  exists relative to its project root).
- `gpp-agent/tests/integration/test_agent_runtime_app.py` errors at collection unless
  `GOOGLE_CLOUD_PROJECT` is set — should skip gracefully like the live-LLM test does.

**Fix:** restructure both servers to a normal src layout (e.g. package `gspp_mcp`,
`gpp_backend_mcp`), fix the hatch `packages`, unify test imports, add
`[tool.pytest.ini_options] pythonpath` and make the runtime-app test env-guarded. Then
wire the suites into CI.

### P2-14: `run_local_GS_backend_MCP.sh` passes ignored (and forbidden) flags

The script execs `python -m GS_backend_MCP.myserver.main --transport sse --port "$PORT"`,
but `main.py` parses no argv — the flags are silently ignored, and SSE is explicitly
forbidden by `architecture.md` §2 anyway. The server actually runs streamable-http on
`$PORT` via env. Remove the misleading arguments.

### P2-15: `architecture.md` has massively diverged from the implementation

The binding rules document mandates: maker-checker `LoopAgent` + `EscalationBarrier`,
`services/mcp_client_service.py`, `shared/` + `agents/<domain>/` layout,
`tools/observability.py` with span enrichment + arg hashing, model env vars
`PRODUCER_MODEL`/`REVIEWER_MODEL`/`TOOL_AGENT_MODEL`, `AGUIToolset`, and a DoD test
list (§10). The implementation is a different (and legitimate) ADK 2.0 Workflow-graph
design with none of those pieces, different env var names, no observability module,
and `verify_oscal_json` still living in the user MCP (§6 flags the migration as due).
Today the "source of truth for code reviewers" describes a system that doesn't exist.

**Fix:** rewrite architecture.md around the Workflow-graph design (keep §3 tenant
rules, §8 model rules, §10 DoD tests — they still apply), or explicitly mark the
sections that are aspirational. Track the still-valid DoD tests (§10) as a checklist.

### P2-16: `resolver.resolve_profile` ignores its `profile_id` argument

`GS_backend_MCP/myserver/resolver.py` always loads the tenant's single stored PROFILE
model regardless of the `profile_id` the agent passes; the in-memory
`RESOLVED_CATALOG_CACHE` is unbounded and never evicted (per-instance only). Either
remove the misleading parameter from the tool signature or implement multi-profile
storage; add a simple cache cap.

### P2-17: Stray and dead files

- `terraform/route.ts` — an alternative draft of the frontend route sitting in the
  Terraform directory (uses `google-auth-library` instead of raw metadata calls — it's
  actually the cleaner implementation; merge it into the frontend or delete it).
- `gpp-agent/test_schema.py`, `test_schema2.py`, `test_session.py`, `print_edges.py` —
  ad-hoc debug scripts at the project root; move into `tests/` or delete.
- `frontend/logs.run.txt` — committed log file.
- `agentic/venv/` (plain, broken venv with only pip) next to the real `.venv` —
  delete; the scripts use `agentic/.venv` via `uv sync --all-packages`.
- `app/prompts.py` parses YAML frontmatter but `yaml` import result is unused
  (`# Optional: frontmatter = yaml.safe_load(...)`) — fine, but then drop the import.

### P2-18: `agent_runtime_app.py` ordering / dead code

`AgentEngineApp.set_up()` references the module-global `gemini_location` defined 14
lines *below* the class (works at runtime, reads as a bug), and re-exports the same
value `GOOGLE_CLOUD_LOCATION` already holds — `app/agent.py` has meanwhile forced
`GOOGLE_CLOUD_LOCATION="global"` at import time, so the set_up block is a no-op that
suggests region control which doesn't exist. Clean up: one place decides the Gemini
location (and document that Gemini 3 preview models require the `global` endpoint).

### P2-19: Catalog data duplication

`GSpp_MCP/data/Grundschutz++-catalog.json` and `GS_backend_MCP/assets/Grundschutz++-catalog.json`
are independent copies of the catalog that also lives in the GSpp repo proper, and
`resolver.py` hard-codes a GitHub raw URI fragment for the "official" import match.
Define one source of truth (e.g. build step copies from the repo root) so catalog
updates can't desynchronize the two MCP servers.

### P2-23: Config drift — services co-managed by Terraform and `gcloud run deploy` scripts

`scripts/deploy_GS_backend_MCP.sh`, `deploy_GSpp_MCP.sh` and `deploy_frontend.sh` each
run `gcloud run deploy … --set-env-vars` against services that Terraform also manages.
Terraform only `ignore_changes`-es the container image, so the next `terraform apply`
reverts any env-var or scaling change made by a script (and vice versa, scripts clobber
Terraform-set values like the frontend's `AGENT_URL`). Pick one owner per concern —
recommended: Terraform owns service config (env, scaling, IAM), scripts only build/push
images and roll a new revision (`gcloud run services update --image` without touching
env vars).

---

## Architecture review summary (2026-06-09)

**Sound — keep these decisions:**

- **Two-MCP split** (public read-only catalog vs. tenant-state backend with GCS) —
  clean separation of concerns, least privilege per service account.
- **Trust boundary in the right place**: tenant isolation and OSCAL schema validation
  are enforced server-side in the backend MCP, never delegated to the LLM. Verified
  live.
- **Graph-enforced control flow**: "Phase 5 only via Phase 4 `cleared`" lives in the
  Workflow structure and is covered by tests — not a prompt promise.
- **IAM topology**: MCPs private (agent SA is sole invoker), frontend public,
  versioned GCS artifacts per IV.

**Structurally broken / missing (not bugs — design gaps):**

1. **Frontend↔agent seam = two half-built architectures** (P0-2 + P1-22): Terraform
   wires Agent-Engine `:query` into the frontend, the deploy script expects Cloud Run
   + `/copilotkit`, architecture.md mandates Option A (Cloud Run + ag-ui-adk). Decide
   once, then align frontend, Terraform, scripts and HITL handling (P1-6) together.
2. **No end-user identity anywhere**: the frontend is `allUsers`, there is no login,
   and the tenant claim (`X-Gpp-User-Id`) is fabricated by code, not derived from an
   authenticated principal. Once the pipe works, any visitor could address any IV.
   Needs user authn (e.g. IAP) plus a user→IV authorization mapping; no current
   component owns this.
3. **The workflow cannot create its own subject matter** (P0-4): all five phases
   assume an existing SSP; there's no intake/bootstrap path.
4. **Maker-checker was dropped, not replaced**: architecture.md's producer/reviewer
   LoopAgent quality mechanism doesn't exist in the Workflow rewrite — phase outputs
   go straight to HITL gates, and with `tools`+`output_schema` combined (P1-4) those
   outputs may not even be grounded in tool data.
5. **Stateful MCP protocol on scale-to-zero serverless** (P1-7 + P1-20): session-based
   Streamable-HTTP plus autoscaling/cold starts is a protocol/infrastructure mismatch;
   make the servers stateless and keep one instance warm.
6. **Duplicated validation paths**: GSpp_MCP's `verify_oscal_json` and the backend's
   write-time validation use separate schema copies and separate code — they can
   drift and disagree (architecture.md §6 already flags the migration as due).

---

## P3 — Low / nice-to-have

- **Eval is scaffold-only.** `tests/eval/evalsets/basic.evalset.json` is the template
  smoke case. After P0/P1, build a real evalset per phase (classifier routing,
  tool-trajectory for phase agents, gate behavior) and run `agents-cli eval run` as the
  acceptance gate — this is the project's actual Definition of Done (§10).
- **Cost:** engine `min_instances = 1` with 4 CPU / 8 GiB runs 24/7; fine for a demo
  phase, revisit before idle periods.
- **`.env.example` drift:** mentions `MAX_REVIEW_ITERATIONS` (no review loop exists)
  and `SANDBOX_RESOURCE_NAME` (unused); `GCS_BUCKET_NAME` is unused by the agent
  (backend MCP owns GCS via `BUCKET_NAME`).
- **`load_test/load_test.py`** targets the scaffold's default endpoints — revisit after
  the frontend/agent transport decision.
- **agents-cli 0.1.3 → 0.3.1** update available (`uv tool upgrade google-agents-cli`);
  check the changelog before upgrading mid-flight since deploy behavior (engine
  matching, env-var handling) is load-bearing here.

---

## Suggested order of attack

1. ~~**P0-1**: redeploy real agent~~ — **done 2026-06-09**, agent answers in the playground.
2. **P1-20 + P1-21** (unblocks all playground testing): MCP min-instances + client
   timeouts + fast container start, and the dev IV fallback env on the backend MCP.
3. **P1-8**: make MCP auth/session failures loud, then verify in the playground that
   phase agents actually call MCP tools end-to-end.
4. **P0-4**: give the workflow an SSP-creation path (extend Phase 1 or add an intake
   phase); update graph tests.
5. **P0-3**: real IV propagation (frontend → user_id → header) + app-level validation;
   remove the dev fallback.
6. **P0-2 + P1-6 + P1-22**: pick Option A (Cloud Run + ag-ui-adk, matches
   architecture.md) or Option B (Agent Engine bridge); implement transport + HITL +
   frontend deploy script together — they're the same decision.
7. **P1-4, P1-5, P1-9**: agent-quality fixes (inspector/judge split, route clearing,
   model wiring).
8. **P1-7**: `stateless_http=True` on both MCP servers (one-line each + redeploy).
9. **P2 block**: locks, dead files, test packaging, config-drift ownership, docs —
   one cleanup PR.
