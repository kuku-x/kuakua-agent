# Fullstack Refactor Execution Plan (14 Days)

> For agentic workers: use this plan as the single source of truth and execute tasks in order. Update task status checkbox after each verified step.

**Goal:** Complete fullstack refactor across Android, transport, backend, SQLite, LLM, and shared utilities with incremental safety.

**Execution Strategy:** No big-bang rewrite. Deliver in 4 milestones, keep system running at each checkpoint.

---

## Milestone M1 (Day 1-3): Foundation and Standards

**Files/Areas:**
- `docs/superpowers/specs/*` (architecture and standards docs)
- `kuakua_agent/*` config/error/log layers
- `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/*` core config/error/log layers

- [ ] Define and freeze naming/structure/error/logging standards.
- [ ] Centralize runtime config and remove obvious hardcoded constants.
- [ ] Add unified error model and route-level error mapping on backend.
- [ ] Add structured logging baseline and trace id propagation conventions.
- [ ] Confirm no new module violates dependency direction.

**Verification:**
- Run: `python -m compileall kuakua_agent`
- Run: Android assemble command used by project
- Expected: compile/build success

---

## Milestone M2 (Day 4-7): Data Pipeline Hardening

**Files/Areas:**
- Android sync/monitor modules
- backend ingestion routes/services
- SQLite ingestion tables and indexes

- [ ] Version sync protocol and define required fields.
- [ ] Ensure Android local outbox persistence exists and is used for uploads.
- [ ] Add retry with exponential backoff + jitter in sync workflow.
- [ ] Implement backend idempotent batch ingestion by `event_id`.
- [ ] Return accepted/rejected feedback from backend API.
- [ ] Add ingestion transaction boundaries and indexes.

**Verification:**
- [ ] Duplicate-batch test: same payload twice, no duplicate rows.
- [ ] Offline/online sync test: eventual success after reconnect.
- [ ] Large batch smoke test (for example 10k events) with acceptable latency.

---

## Milestone M3 (Day 8-11): Domain + LLM Refactor

**Files/Areas:**
- usage summarizer/profile modules
- prompt/context and LLM provider modules

- [ ] Refactor summary/profile calculations into pure functions where possible.
- [ ] Version prompt templates and separate them from orchestration logic.
- [ ] Add LLM output schema checks.
- [ ] Add timeout/retry policy for model invocation.
- [ ] Add deterministic fallback for LLM failures.
- [ ] Persist generation metadata (mode, latency, fallback reason).

**Verification:**
- [ ] Unit tests for summary/profile calculations.
- [ ] LLM timeout simulation triggers fallback correctly.
- [ ] Prompt version selection works by config.

---

## Milestone M4 (Day 12-14): Stabilization and Acceptance

**Files/Areas:**
- integration tests
- docs and operational runbook
- cleanup/retention jobs

- [ ] Add end-to-end regression scenarios for core pipeline.
- [ ] Validate retention jobs and SQLite cleanup behavior.
- [ ] Document troubleshooting runbook and module ownership.
- [ ] Prepare final acceptance report with known risks.

**Verification:**
- [ ] Full lint/test/build pipeline passes.
- [ ] End-to-end happy path validated.
- [ ] Degraded path validated (network failure, db lock, llm timeout).

---

## Cross-Cutting Rules (Always On)

- [ ] No direct DB/network call in UI layer.
- [ ] No router-level SQL in backend API layer.
- [ ] No hardcoded retries/timeouts in feature modules.
- [ ] Every recoverable failure has explicit retry/degrade path.
- [ ] Every critical operation logs trace id and duration.

---

## Daily Work Rhythm

1) Pick 1-3 tasks from current milestone.
2) Implement with smallest safe slice.
3) Run verification commands.
4) Update checklist and changelog.
5) Commit only after passing checks.

