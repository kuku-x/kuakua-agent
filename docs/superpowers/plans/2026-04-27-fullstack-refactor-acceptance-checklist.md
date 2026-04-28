# Fullstack Refactor Acceptance Checklist

> Use this checklist to sign off refactor quality before release.

## A. Architecture and Boundaries

- [ ] Backend modules follow `api -> application -> domain -> infrastructure` dependency direction.
- [ ] Android modules follow `feature -> application -> domain -> infrastructure` direction.
- [ ] Cross-cutting concerns (`config/error/log/tracing`) are centralized and reused.
- [ ] No direct SQL in API routes, no direct network/DB in Android UI layer.

## B. Sync Protocol and Transport Reliability

- [ ] Request payload includes `protocol_version`, `batch_id`, and per-entry `event_id`.
- [ ] Backend rejects unsupported protocol versions with explicit error.
- [ ] Batch retry with same `batch_id` returns stable result.
- [ ] Event-level duplicates are detected and reported via `duplicate_keys`.
- [ ] Temporary backend failures expose retry hints (`Retry-After`, `should_retry`).

## C. Storage and Data Integrity

- [ ] SQLite schema includes usage event tables and event idempotency tracking.
- [ ] Core write paths are transactional and indexes exist for primary queries.
- [ ] Daily usage aggregation remains available after sync writes.
- [ ] Retention/cleanup strategy exists and is documented.

## D. LLM and Agent Reliability

- [ ] Prompt version can be selected by config (`praise_prompt_version`).
- [ ] LLM timeout/max_tokens/temperature are configurable.
- [ ] LLM failures have deterministic fallback response paths.
- [ ] Chat/LLM logs include latency and fallback status.

## E. Observability and Error Handling

- [ ] API error payload includes `trace_id` and `retryable`.
- [ ] Request trace id is propagated through `X-Trace-Id`.
- [ ] Structured logs include module/event/error_code/duration fields.
- [ ] Critical sync and chat paths have success/failure logs.

## F. Verification Commands

- [ ] `python -m compileall kuakua_agent` succeeds.
- [ ] `.\gradlew.bat :app:compileDebugKotlin` succeeds.
- [ ] `python tools/smoke_phone_sync.py --help` succeeds.
- [ ] `python tools/smoke_phone_sync.py --base-url <local_backend_url>` passes in local env.

## G. Release Readiness

- [ ] Refactor execution log is updated with verification evidence.
- [ ] Known limitations and follow-up tasks are documented.
- [ ] Demo flow (sync -> summary -> praise) is reproducible from clean startup.
- [ ] Risk roadmap document exists (`2026-04-27-fullstack-refactor-risks-and-next-steps.md`).
