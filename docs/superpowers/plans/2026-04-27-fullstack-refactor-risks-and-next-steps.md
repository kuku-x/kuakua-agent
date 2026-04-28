# Fullstack Refactor Risks and Next Steps

> Purpose: make current residual risks explicit and define actionable follow-up iterations.

## 1) Residual Risks (Current)

### R1. JSON parsing on Android sync response is regex-based
- **Impact:** fragile when response JSON formatting changes.
- **Current mitigation:** backend response structure is stable and smoke script validates basic path.
- **Next action:** switch to typed JSON parsing (`JSONObject` or serialization library).

### R2. SQLite migration strategy is schema-on-startup only
- **Impact:** long-term schema evolution may become risky without explicit migration versions.
- **Current mitigation:** `CREATE IF NOT EXISTS` keeps backward compatibility.
- **Next action:** introduce migration version table and incremental migration scripts.

### R3. Partial success semantics are not yet end-to-end surfaced in all UI screens
- **Impact:** user-facing diagnostics may still be coarse in some views.
- **Current mitigation:** worker status now shows accepted/duplicate/failed counts.
- **Next action:** expose these metrics in monitoring details/history UI.

### R4. LLM fallback is deterministic but not quality-ranked
- **Impact:** fallback quality may vary by context richness.
- **Current mitigation:** fallback ensures continuity and avoids silent failures.
- **Next action:** add fallback templates by scenario (coding/focus/discipline).

### R5. Integration tests are still script-driven, not CI pipeline steps
- **Impact:** regression detection depends on manual execution discipline.
- **Current mitigation:** smoke script and acceptance checklist added.
- **Next action:** add automated CI job for compile + smoke checks.

## 2) Prioritized Iteration Plan

## Iteration A (High Priority, 1-2 days)
- [ ] Replace Android response regex parsing with typed parser.
- [ ] Add backend API contract tests for sync response fields.
- [ ] Add explicit validation for response `should_retry` consistency.

## Iteration B (High Priority, 2-3 days)
- [ ] Introduce SQLite schema version table and migration runner.
- [ ] Move current schema additions into numbered migration files.
- [ ] Add migration rollback notes for local recovery.

## Iteration C (Medium Priority, 2 days)
- [ ] Add fallback templates by scene (coding/focus/discipline/general).
- [ ] Add fallback usage counters in summary/diagnostic endpoint.

## Iteration D (Medium Priority, 1-2 days)
- [ ] Add CI pipeline tasks: backend compile, android compile, smoke script dry-run.
- [ ] Publish release gate policy linked to acceptance checklist.

## 3) Release Recommendation

- **Can release internal preview:** Yes (local-only environment, core flows are resilient and verified).
- **Recommended before wider rollout:** finish Iteration A + B.
- **Documentation status:** architecture, execution log, smoke script, acceptance checklist, and risk roadmap are all present.
