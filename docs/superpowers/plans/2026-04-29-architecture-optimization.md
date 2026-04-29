# 夸夸 Agent 架构优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three incremental architecture improvements: (1) SQLite synchronous → async, (2) HTTP-only → HTTP + WebSocket real-time, (3) verify and consolidate business logic in main process.

**Architecture:**

- Step 1-8: Replace `sqlite3` + `contextmanager` with `aiosqlite` + async context manager in `Database`, propagate async through all memory stores.
- Step 9-14: Add `WebSocketManager` singleton, register `/ws` route in FastAPI, update scheduler to push praise events over WebSocket, add frontend `useWebSocket.ts` hook.
- Step 15-18: Audit main process for business logic leakage, migrate any remaining TTS/ActivityWatch calls to backend services, confirm scheduler runs in FastAPI.

**Tech Stack:** aiosqlite, FastAPI WebSocket, asyncio, Vue 3 Composition API

---

## 全局前置：添加依赖

**File:** `pyproject.toml`

- [ ] **Step 1: Add aiosqlite dependency**

```toml
dependencies = [
  "fastapi>=0.110,<1.0",
  "uvicorn[standard]>=0.27,<1.0",
  "pydantic-settings>=2.2,<3.0",
  "httpx>=0.27,<1.0",
  "numpy>=1.26,<3.0",
  "kokoro",
  "misaki[zh]",
  "aiosqlite>=0.20,<1.0",
]
```

Run: `pip install aiosqlite`

---

## Phase 1: SQLite 同步 → 异步

### Task 1: Rewrite `database.py` — async context manager

**Files:**
- Modify: `kuakua_agent/services/memory/database.py`

```python
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent.parent.parent.parent
DB_PATH = ROOT_DIR / "kuakua_agent.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_recalled BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS praise_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    context_snapshot TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scene_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene TEXT UNIQUE NOT NULL,
    weight REAL DEFAULT 0.5,
    keywords TEXT DEFAULT '[]',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    praise_id INTEGER,
    reaction TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praise_id) REFERENCES praise_history(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_milestones_occurred ON milestones(occurred_at);
CREATE INDEX IF NOT EXISTS idx_praise_history_created ON praise_history(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_praise ON feedback_logs(praise_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_chat_id ON chat_history(chat_id);

CREATE TABLE IF NOT EXISTS phone_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    package_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    last_used TEXT,
    event_count INTEGER NOT NULL,
    received_at INTEGER NOT NULL,
    batch_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_phone_events_device_date ON phone_usage_events(device_id, usage_date);
CREATE INDEX IF NOT EXISTS idx_phone_events_received_at ON phone_usage_events(received_at);
CREATE INDEX IF NOT EXISTS idx_phone_events_batch_id ON phone_usage_events(batch_id);

CREATE TABLE IF NOT EXISTS phone_processed_events (
    event_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    processed_at INTEGER NOT NULL,
    batch_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_phone_processed_device_date ON phone_processed_events(device_id, usage_date);
CREATE INDEX IF NOT EXISTS idx_phone_processed_processed_at ON phone_processed_events(processed_at);

CREATE TABLE IF NOT EXISTS phone_daily_usage (
    device_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    package_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    last_used TEXT,
    event_count INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (device_id, usage_date, package_name)
);

CREATE INDEX IF NOT EXISTS idx_phone_daily_date ON phone_daily_usage(usage_date);
CREATE INDEX IF NOT EXISTS idx_phone_daily_device_date ON phone_daily_usage(device_id, usage_date);

CREATE TABLE IF NOT EXISTS daily_usage_summary (
    date TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_summary_updated_at ON daily_usage_summary(updated_at);
"""


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH

    @asynccontextmanager
    async def _get_conn(self):
        conn = await aiosqlite.connect(str(self.db_path))
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()

    async def init_db(self) -> None:
        async with self._get_conn() as conn:
            await conn.executescript(SCHEMA)
            await conn.commit()
```

- [ ] **Step 2: Add `init_db()` call to `main.py` startup**

**Files:**
- Modify: `kuakua_agent/main.py`

```python
from kuakua_agent.api.app import create_app
from kuakua_agent.services.scheduler import PraiseScheduler
from kuakua_agent.services.activitywatch import ActivityWatchScheduler
from kuakua_agent.services.nightly_summary_scheduler import NightlySummaryScheduler
from kuakua_agent.services.memory import get_database

app = create_app()

scheduler: PraiseScheduler | None = None
aw_scheduler: ActivityWatchScheduler | None = None
nightly_summary_scheduler: NightlySummaryScheduler | None = None


@app.on_event("startup")
async def startup():
    global scheduler, aw_scheduler, nightly_summary_scheduler
    # Initialize async database before any service starts
    db = get_database()
    await db.init_db()
    scheduler = PraiseScheduler()
    await scheduler.start()
    aw_scheduler = ActivityWatchScheduler()
    await aw_scheduler.start()
    nightly_summary_scheduler = NightlySummaryScheduler()
    await nightly_summary_scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    if scheduler:
        await scheduler.stop()
    if aw_scheduler:
        await aw_scheduler.stop()
    if nightly_summary_scheduler:
        await nightly_summary_scheduler.stop()
```

- [ ] **Step 3: Rewrite `MilestoneStore` — async methods**

**Files:**
- Modify: `kuakua_agent/services/memory/milestone.py`

```python
from datetime import datetime, timedelta, timezone
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import Milestone


def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


class MilestoneStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    async def add(self, event_type: str, title: str, description: str | None = None, occurred_at: datetime | None = None) -> Milestone:
        occurred = _to_utc_naive(occured_at) if occurred_at else datetime.utcnow()
        async with self._db._get_conn() as conn:
            cursor = await conn.execute(
                "INSERT INTO milestones (event_type, title, description, occurred_at) VALUES (?, ?, ?, ?)",
                (event_type, title, description, occurred.isoformat()),
            )
            await conn.commit()
            row = await conn.execute_fetchone("SELECT * FROM milestones WHERE id = ?", (cursor.lastrowid,))
            if row is None:
                raise ValueError(f"Milestone not found after insert: id={cursor.lastrowid}")
            return Milestone.from_row(row)

    async def get_recent(self, hours: int = 24, limit: int = 10) -> list[Milestone]:
        cutoff = datetime.now() - timedelta(hours=hours)
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM milestones WHERE occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ) as cursor:
                rows = await cursor.fetchall()
            return [Milestone.from_row(r) for r in rows]

    async def get_unrecalled(self, hours: int = 72, limit: int = 5) -> list[Milestone]:
        cutoff = datetime.now() - timedelta(hours=hours)
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM milestones WHERE is_recalled = FALSE AND occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ) as cursor:
                rows = await cursor.fetchall()
            return [Milestone.from_row(r) for r in rows]

    async def mark_recalled(self, milestone_id: int) -> None:
        async with self._db._get_conn() as conn:
            await conn.execute("UPDATE milestones SET is_recalled = TRUE WHERE id = ?", (milestone_id,))
            await conn.commit()

    async def get_all(self, limit: int = 50) -> list[Milestone]:
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM milestones ORDER BY occurred_at DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [Milestone.from_row(r) for r in rows]
```

- [ ] **Step 4: Rewrite `PreferenceStore` — async methods**

**Files:**
- Modify: `kuakua_agent/services/memory/preference.py`

```python
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import UserPreference


class PreferenceStore:
    DEFAULT_PREFS = {
        "praise_auto_enable": "true",
        "tts_enable": "false",
        "tts_voice": "default",
        "kokoro_voice": "zf_001",
        "kokoro_model_path": "./ckpts/kokoro-v1.1",
        "tts_speed": "1.0",
        "fish_audio_model": "s2-pro",
        "openweather_location": "Shanghai,CN",
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
        "nightly_summary_enable": "true",
        "nightly_summary_time": "21:30",
        "nightly_summary_last_sent_date": "",
        "nightly_summary_latest_date": "",
        "nightly_summary_latest_content": "",
        "nightly_summary_latest_read": "true",
    }

    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    async def _init_defaults(self) -> None:
        async with self._db._get_conn() as conn:
            for key, value in self.DEFAULT_PREFS.items():
                await conn.execute(
                    "INSERT OR IGNORE INTO user_preferences (key, value) VALUES (?, ?)",
                    (key, value),
                )
            await conn.commit()

    async def get(self, key: str) -> str | None:
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
            return row["value"] if row else None

    async def set(self, key: str, value: str) -> None:
        async with self._db._get_conn() as conn:
            await conn.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat()),
            )
            await conn.commit()

    async def get_all(self) -> dict[str, str]:
        async with self._db._get_conn() as conn:
            async with conn.execute("SELECT key, value FROM user_preferences") as cursor:
                rows = await cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}

    async def get_bool(self, key: str) -> bool:
        v = await self.get(key)
        return v.lower() in ("true", "1", "yes") if v else False

    async def get_int(self, key: str, default: int = 0) -> int:
        v = await self.get(key)
        if not v:
            return default
        try:
            return int(v)
        except ValueError:
            return default

    async def get_float(self, key: str, default: float = 1.0) -> float:
        v = await self.get(key)
        if not v:
            return default
        try:
            return float(v)
        except ValueError:
            return default
```

- [ ] **Step 5: Rewrite remaining memory stores — async**

**Files:**
- Modify: `kuakua_agent/services/memory/history.py`
- Modify: `kuakua_agent/services/memory/feedback.py`
- Modify: `kuakua_agent/services/memory/profile.py`
- Modify: `kuakua_agent/services/memory/chat_history.py`

For each store, replace all `with self._db._get_conn() as conn:` + `conn.execute()` / `conn.commit()` with `async with self._db._get_conn() as conn:` + `await conn.execute()` / `await conn.commit()`. Change all method signatures from `def` to `async def`.

Key pattern for all async stores:
```python
# Before (sync):
with self._db._get_conn() as conn:
    rows = conn.execute("SELECT ...").fetchall()
    conn.commit()

# After (async):
async with self._db._get_conn() as conn:
    async with conn.execute("SELECT ...") as cursor:
        rows = await cursor.fetchall()
    await conn.commit()
```

- [ ] **Step 6: Update `memory/__init__.py` — add async `init_database()`**

**Files:**
- Modify: `kuakua_agent/services/memory/__init__.py`

```python
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.milestone import MilestoneStore
from kuakua_agent.services.memory.preference import PreferenceStore
from kuakua_agent.services.memory.profile import ProfileStore
from kuakua_agent.services.memory.feedback import FeedbackStore
from kuakua_agent.services.memory.history import PraiseHistoryStore

__all__ = [
    "Database",
    "MilestoneStore",
    "PreferenceStore",
    "ProfileStore",
    "FeedbackStore",
    "PraiseHistoryStore",
]

_db_instance: Database | None = None

def get_database() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
```

- [ ] **Step 7: Update `cooldown.py` — async PreferenceStore calls**

**Files:**
- Modify: `kuakua_agent/services/scheduler/cooldown.py`

```python
from datetime import datetime
from kuakua_agent.services.memory import PreferenceStore


class CooldownManager:
    def __init__(self, pref_store: PreferenceStore | None = None):
        self._pref = pref_store or PreferenceStore()

    async def is_global_enabled(self) -> bool:
        return await self._pref.get_bool("praise_auto_enable")

    async def is_in_do_not_disturb(self) -> bool:
        now = datetime.now()
        start_str = await self._pref.get("do_not_disturb_start") or "22:00"
        end_str = await self._pref.get("do_not_disturb_end") or "08:00"
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
        cur = now.time()
        if start_t <= end_t:
            return start_t <= cur <= end_t
        else:
            return cur >= start_t or cur <= end_t

    async def can_praise(self) -> bool:
        if not await self.is_global_enabled():
            return False
        if await self.is_in_do_not_disturb():
            return False
        return True

    async def record_praise(self) -> None:
        pass
```

- [ ] **Step 8: Update `scheduler.py` — await async cooldown calls**

**Files:**
- Modify: `kuakua_agent/services/scheduler/scheduler.py`

Replace all `self._cooldown.can_praise()` with `await self._cooldown.can_praise()`, `self._cooldown.is_global_enabled()` with `await self._cooldown.is_global_enabled()`, etc.

Also update the call to `context_builder.build_proactive_context` and `self._model.complete_async` — these may already be async but need verification.

---

## Phase 2: WebSocket 实时通信

### Task 2: Create `WebSocketManager` singleton

**Files:**
- Create: `kuakua_agent/services/websocket_manager.py`

```python
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    _instance: "WebSocketManager | None" = None

    def __new__(cls) -> "WebSocketManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: list[WebSocket] = []
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self._connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, ensure_ascii=False)
        async with self._lock:
            dead: list[WebSocket] = []
            for ws in self._connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in self._connections:
                    self._connections.remove(ws)

    async def send_praise(self, content: str, trigger: str) -> None:
        await self.broadcast({
            "type": "praise_push",
            "data": {
                "content": content,
                "trigger": trigger,
            }
        })

    async def send_summary_progress(self, date: str, progress: str) -> None:
        await self.broadcast({
            "type": "summary_progress",
            "data": {
                "date": date,
                "progress": progress,
            }
        })

    async def send_chat_stream(self, chat_id: str, chunk: str, done: bool) -> None:
        await self.broadcast({
            "type": "chat_stream",
            "data": {
                "chat_id": chat_id,
                "chunk": chunk,
                "done": done,
            }
        })

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()
```

- [ ] **Step 9: Add WebSocket route to `app.py`**

**Files:**
- Modify: `kuakua_agent/api/app.py`

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from kuakua_agent.api.errors import register_exception_handlers
from kuakua_agent.api.activitywatch_proxy_routes import router as activitywatch_proxy_router
from kuakua_agent.api.routes import router
from kuakua_agent.api.phone_routes import router as phone_router
from kuakua_agent.api.usage_summary_routes import (
    usage_router as usage_summary_router,
    jobs_router as usage_jobs_router,
)
from kuakua_agent.core.logging import configure_logging, get_logger
from kuakua_agent.core.tracing import TRACE_ID_HEADER, new_trace_id
from kuakua_agent.services.websocket_manager import ws_manager

logger = get_logger(__name__)

# ... (TraceIdMiddleware and create_app remain the same up to app.include_router calls)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages from client (e.g. ping)
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
```

Add `import json` to the top.

- [ ] **Step 10: Update scheduler to push praise via WebSocket**

**Files:**
- Modify: `kuakua_agent/services/scheduler/scheduler.py`

Add to imports:
```python
from kuakua_agent.services.websocket_manager import ws_manager
```

In `trigger_now()`, after `self._cooldown.record_praise()` and before the return, add:
```python
await ws_manager.send_praise(
    content=praise_content,
    trigger=event.trigger_type.value,
)
```

Also update the milestone store call to be awaited:
```python
# Before
history_store.add(...)

# After
await history_store.add(...)
```

And `MilestoneStore` `mark_recalled` must also be awaited:
```python
ms = MilestoneStore()
await ms.mark_recalled(event.data["milestone_id"])
```

- [ ] **Step 11: Create `useWebSocket.ts` frontend hook**

**Files:**
- Create: `desktop/src/renderer/hooks/useWebSocket.ts`

```typescript
import { onMounted, onUnmounted, ref } from 'vue'

export interface PraisePushEvent {
  type: 'praise_push'
  data: { content: string; trigger: string }
}

export interface SummaryProgressEvent {
  type: 'summary_progress'
  data: { date: string; progress: string }
}

export interface ChatStreamEvent {
  type: 'chat_stream'
  data: { chat_id: string; chunk: string; done: boolean }
}

export type WsMessage = PraisePushEvent | SummaryProgressEvent | ChatStreamEvent

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const messages = ref<WsMessage[]>([])
  let reconnectTimer: number | null = null

  const listeners = new Map<string, Set<(event: WsMessage) => void>>()

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      connected.value = true
      console.log('[WS] Connected')
    }

    ws.value.onclose = () => {
      connected.value = false
      console.log('[WS] Disconnected, reconnecting in 3s...')
      reconnectTimer = window.setTimeout(connect, 3000)
    }

    ws.value.onerror = (err) => {
      console.error('[WS] Error', err)
    }

    ws.value.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage
        messages.value.push(msg)
        listeners.get(msg.type)?.forEach(cb => cb(msg))
        listeners.get('*')?.forEach(cb => cb(msg))
      } catch {
        // ignore parse errors
      }
    }
  }

  function on(type: string, callback: (event: WsMessage) => void) {
    if (!listeners.has(type)) {
      listeners.set(type, new Set())
    }
    listeners.get(type)!.add(callback)
  }

  function off(type: string, callback: (event: WsMessage) => void) {
    listeners.get(type)?.delete(callback)
  }

  function disconnect() {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws.value?.close()
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { connected, messages, on, off, disconnect }
}
```

- [ ] **Step 12: Update `AppLayout.vue` to listen for praise pushes via WebSocket**

**Files:**
- Modify: `desktop/src/renderer/components/layout/AppLayout.vue`

Add to script imports:
```typescript
import { useWebSocket } from '@/hooks/useWebSocket'
```

Add inside `setup()`:
```typescript
const { on } = useWebSocket()

// Listen for proactive praise pushes
on('praise_push', (event) => {
  if (event.type === 'praise_push') {
    window.electronAPI?.showSystemNotification?.({
      title: '夸夸 Agent',
      body: event.data.content,
    })
  }
})
```

---

## Phase 3: 业务逻辑下沉后端

### Task 3: Audit main process for business logic

- [ ] **Step 13: Audit `desktop/src/main/index.ts` for business logic**

Read `desktop/src/main/index.ts` and check if it contains any of:
- Direct calls to ActivityWatch API
- Direct calls to Kokoro TTS
- Direct SQLite reads/writes
- Scheduler logic

If any of these exist, move them to the backend service layer.

The backend already has:
- `services/activitywatch/` — ActivityWatch polling
- `services/output/tts.py` — Kokoro TTS
- `services/scheduler/` — PraiseScheduler

Verify from `main.py` that `PraiseScheduler`, `ActivityWatchScheduler`, and `NightlySummaryScheduler` are all initialized from FastAPI backend, not from Electron main process.

- [ ] **Step 14: Verify IPC bridge is only for UI concerns**

`desktop/src/main/index.ts` should only:
- Create BrowserWindow
- Set up tray
- Register global shortcuts
- Expose IPC for `showSystemNotification`, `openExternal`, etc. (UI-level capabilities)

If any business logic is found in main process, refactor it to call the FastAPI backend via HTTP/WebSocket instead.

---

## Phase 4: 修复并验证

- [ ] **Step 15: Verify all async calls are properly awaited**

Run a grep across `kuakua_agent/services/` for any remaining `with self._db._get_conn()` (sync pattern) — there should be zero matches.

```bash
grep -r "with self._db._get_conn" kuakua_agent/services/
```

Expected: no output.

- [ ] **Step 16: Test API startup**

Run:
```bash
cd d:\project\kuakua-agent
python -m uvicorn kuakua_agent.main:app --reload --port 18000
```

Expected: App starts without errors, async DB schema initialized.

- [ ] **Step 17: Run existing tests**

```bash
cd d:\project\kuakua-agent
pytest tests/ -v --tb=short
```

Expected: All tests pass. Fix any broken imports or async signature mismatches.

- [ ] **Step 18: Build Electron app**

```bash
cd desktop && npm run build
```

Expected: Build succeeds.

---

## 文件变更汇总

| 操作 | 文件 |
|---|---|
| Modify | `pyproject.toml` |
| Modify | `kuakua_agent/services/memory/database.py` |
| Modify | `kuakua_agent/services/memory/__init__.py` |
| Modify | `kuakua_agent/services/memory/milestone.py` |
| Modify | `kuakua_agent/services/memory/preference.py` |
| Modify | `kuakua_agent/services/memory/history.py` |
| Modify | `kuakua_agent/services/memory/feedback.py` |
| Modify | `kuakua_agent/services/memory/profile.py` |
| Modify | `kuakua_agent/services/memory/chat_history.py` |
| Modify | `kuakua_agent/services/scheduler/cooldown.py` |
| Modify | `kuakua_agent/services/scheduler/scheduler.py` |
| Modify | `kuakua_agent/main.py` |
| Create | `kuakua_agent/services/websocket_manager.py` |
| Modify | `kuakua_agent/api/app.py` |
| Create | `desktop/src/renderer/hooks/useWebSocket.ts` |
| Modify | `desktop/src/renderer/components/layout/AppLayout.vue` |
