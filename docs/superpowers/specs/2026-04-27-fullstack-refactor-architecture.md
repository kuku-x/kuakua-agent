# Fullstack Refactor Architecture Design

> Scope: kuakua-agent full project (Android app + transport + desktop backend + SQLite + LLM/Agent).
>
> Goal: turn the project from tightly coupled code into a layered, maintainable, testable local-first architecture.

## 1. Core Problems (Current State)

1) Mixed responsibilities: UI, collection, transport, storage, and business logic are mixed in the same modules.
2) Contract drift: Android and backend payload fields evolve without strict versioned schema.
3) Scattered configuration: retry policy, timeout, thresholds, and prompt constants are hardcoded in multiple files.
4) Weak resilience: network retries, deduplication, and fallback paths are incomplete across layers.
5) Data-layer risk: SQLite operations are not consistently transactional and index strategy is unclear.
6) Low observability: missing unified trace id and error code mapping across Android -> backend -> LLM chain.

## 2. Target Architecture (Layered + Ports/Adapters)

### 2.1 Android

- `feature/*`: UI and ViewModel only
- `application/*`: use cases (sync sessions, collect usage, rebuild summaries)
- `domain/*`: entities and repository interfaces
- `infrastructure/*`: Room DB, network client, system adapters
- `core/*`: config, logging, errors, time, retry utilities

### 2.2 Desktop Backend (FastAPI)

- `api/*`: routes, request/response schemas, HTTP error mapping
- `application/*`: orchestration services and jobs
- `domain/*`: core models, rules, and error types
- `infrastructure/*`: SQLite repositories, file storage, LLM providers
- `core/*`: config, logging, tracing, utilities

### 2.3 Shared Contract

- `contracts/*`: protocol schemas and examples
- Mandatory protocol metadata:
  - `protocol_version`
  - `batch_id`
  - `device_id`
  - `event_id` (idempotency key)

## 3. Data and Control Flow

1) Android collection writes to local outbox (persistent queue).
2) Sync worker sends batch payload to backend.
3) Backend validates contract and does idempotent transactional upsert.
4) Summarizer job computes daily aggregates and profile features.
5) LLM module generates praise using profile + summary with fallback.
6) Results are stored and served to UI/query APIs.

## 4. Module Responsibilities and Boundaries

### 4.1 Android Monitor Module
- Collect app usage events with minimal side effects.
- No direct network logic in collector classes.

### 4.2 Sync Transport Module
- Build payload, attach protocol version, handle retry policy.
- Exponential backoff with jitter and bounded retry count.

### 4.3 Backend Ingestion Module
- Validate request schema.
- Persist events in transaction.
- Return per-event accepted/rejected result.

### 4.4 Usage Analytics Module
- Compute day-level metrics from normalized events.
- Expose deterministic pure functions for core calculations.

### 4.5 LLM/Agent Module
- Prompt versioning (`praise_v1`, `praise_v2`).
- Output schema validation.
- Fallback to rule-based text on timeout/errors.

## 5. Unified Standards

### 5.1 Naming
- Python: `snake_case` functions/variables, `PascalCase` classes.
- Kotlin: `camelCase` functions/variables, `PascalCase` classes.
- Constants: `UPPER_SNAKE_CASE`.
- DTO suffixes: `Request`, `Response`, `Dto`, `Command`, `Result`.

### 5.2 Errors
- Every domain/service error must include:
  - `error_code`
  - `message`
  - `retryable`
  - optional `cause`

### 5.3 Logs
- Structured logs only.
- Required fields:
  - `trace_id`
  - `module`
  - `event`
  - `duration_ms`
  - `error_code` (if any)

### 5.4 Config
- No magic numbers in business modules.
- All runtime configs live in centralized settings classes.

## 6. SQLite Design Principles

1) Idempotency: `event_id` unique constraint.
2) Query performance:
   - index `(device_id, started_at)`
   - index `(date, device_id)` for daily rollups.
3) Transaction safety: batch ingestion and summary upserts must be transactional.
4) Retention: scheduled cleanup (for example 365 days) with job logs.

## 7. LLM Reliability Design

1) Prompt templates versioned and stored in dedicated module.
2) Strict timeout and retry budgets.
3) Schema check on model output.
4) Degrade gracefully to deterministic templates.
5) Persist both successful and fallback generation metadata.

## 8. Acceptance Baseline

- Clear module boundaries and dependency direction.
- Stable protocol with retries and idempotency.
- Unified logging and error handling.
- Daily summary and LLM generation remain functional under partial failures.

