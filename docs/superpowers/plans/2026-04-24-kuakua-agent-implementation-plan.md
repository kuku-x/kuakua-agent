# 夸夸Agent 分层架构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为夸夸Agent实现 Claudio 风格的四层分层架构（memory/brain/scheduler/output），在不破坏现有功能的前提下，赋予系统记忆能力、意图分流、智能调度和多模态输出。

**Architecture:** 单体分层架构，所有新增模块置于 `kuakua_agent/services/` 下，复用现有 FastAPI 路由和 SQLite 数据库。四层通过清晰接口通信，调度器使用 asyncio 后台循环。

**Tech Stack:** Python asyncio, SQLite (复用现有), httpx, plyer (桌面通知), Fish Audio API

---

## 文件结构总览

```
kuakua_agent/
├── services/
│   ├── memory/              # [新建]
│   │   ├── __init__.py
│   │   ├── database.py      # SQLite连接 + 表初始化
│   │   ├── models.py        # 数据行对象（dataclass）
│   │   ├── milestone.py     # 里程碑CRUD
│   │   ├── preference.py    # 用户偏好CRUD
│   │   ├── profile.py       # 场景画像CRUD
│   │   └── feedback.py      # 反馈记忆CRUD
│   ├── brain/               # [新建]
│   │   ├── __init__.py
│   │   ├── router.py        # 意图分流
│   │   ├── context.py       # 上下文组装（含去重）
│   │   ├── prompt.py        # Prompt模板
│   │   └── adapter.py       # Ark API调用适配器
│   ├── scheduler/           # [新建]
│   │   ├── __init__.py
│   │   ├── events.py        # 调度事件类型定义
│   │   ├── rules.py         # 触发规则定义
│   │   ├── cooldown.py      # 冷却/上限/免打扰
│   │   └── scheduler.py     # 调度循环（后台）
│   └── output/              # [新建]
│       ├── __init__.py
│       ├── base.py          # OutputChannel抽象基类
│       ├── notifier.py      # 桌面系统通知
│       └── tts.py           # Fish Audio TTS（含兜底）
├── api/routes.py            # [扩展] 新增夸夸配置/记忆/反馈接口
├── schemas/
│   └── praise.py            # [新建] 夸夸相关Pydantic模型
└── main.py                  # [修改] 启动调度器
```

---

## Task 1: memory 层 — 数据库初始化与基础 CRUD

### 依赖文件

- Create: `kuakua_agent/services/memory/__init__.py`
- Create: `kuakua_agent/services/memory/database.py`
- Create: `kuakua_agent/services/memory/models.py`
- Create: `kuakua_agent/services/memory/milestone.py`
- Create: `kuakua_agent/services/memory/preference.py`
- Create: `kuakua_agent/services/memory/profile.py`
- Create: `kuakua_agent/services/memory/feedback.py`
- Create: `tests/services/memory/test_milestone.py`
- Create: `tests/services/memory/test_preference.py`

### 实现步骤

- [ ] **Step 1: 创建 services/memory/ 目录和 __init__.py**

Create: `kuakua_agent/services/memory/__init__.py`

```python
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.milestone import MilestoneStore
from kuakua_agent.services.memory.preference import PreferenceStore
from kuakua_agent.services.memory.profile import ProfileStore
from kuakua_agent.services.memory.feedback import FeedbackStore

__all__ = [
    "Database",
    "MilestoneStore",
    "PreferenceStore",
    "ProfileStore",
    "FeedbackStore",
]

_db_instance: Database | None = None

def get_database() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
```

- [ ] **Step 2: 创建 database.py — SQLite 连接与表初始化**

Create: `kuakua_agent/services/memory/database.py`

```python
import sqlite3
from pathlib import Path
from contextlib import contextmanager

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

CREATE INDEX IF NOT EXISTS idx_milestones_occurred ON milestones(occurred_at);
CREATE INDEX IF NOT EXISTS idx_praise_history_created ON praise_history(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_praise ON feedback_logs(praise_id);
"""


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
```

- [ ] **Step 3: 创建 models.py — 数据行对象定义**

Create: `kuakua_agent/services/memory/models.py`

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Milestone:
    id: int | None
    event_type: str
    title: str
    description: str | None
    occurred_at: datetime
    created_at: datetime
    is_recalled: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Milestone":
        return cls(
            id=row["id"],
            event_type=row["event_type"],
            title=row["title"],
            description=row["description"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]) if isinstance(row["occurred_at"], str) else row["occurred_at"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            is_recalled=bool(row["is_recalled"]),
        )


@dataclass
class PraiseHistory:
    id: int | None
    content: str
    trigger_type: str
    context_snapshot: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PraiseHistory":
        return cls(
            id=row["id"],
            content=row["content"],
            trigger_type=row["trigger_type"],
            context_snapshot=row["context_snapshot"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        )


@dataclass
class UserPreference:
    id: int | None
    key: str
    value: str
    updated_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserPreference":
        return cls(
            id=row["id"],
            key=row["key"],
            value=row["value"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
        )


@dataclass
class SceneProfile:
    id: int | None
    scene: str
    weight: float
    keywords: list[str]
    updated_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SceneProfile":
        import json
        return cls(
            id=row["id"],
            scene=row["scene"],
            weight=row["weight"],
            keywords=json.loads(row["keywords"] or "[]"),
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
        )


@dataclass
class FeedbackLog:
    id: int | None
    praise_id: int | None
    reaction: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "FeedbackLog":
        return cls(
            id=row["id"],
            praise_id=row["praise_id"],
            reaction=row["reaction"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        )
```

- [ ] **Step 4: 创建 milestone.py — 里程碑 CRUD**

Create: `kuakua_agent/services/memory/milestone.py`

```python
import sqlite3
from datetime import datetime, timedelta
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import Milestone


class MilestoneStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add(self, event_type: str, title: str, description: str | None = None, occurred_at: datetime | None = None) -> Milestone:
        occurred = occurred_at or datetime.now()
        with self._db._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO milestones (event_type, title, description, occurred_at) VALUES (?, ?, ?, ?)",
                (event_type, title, description, occurred.isoformat()),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM milestones WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return Milestone.from_row(row)

    def get_recent(self, hours: int = 24, limit: int = 10) -> list[Milestone]:
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones WHERE occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ).fetchall()
            return [Milestone.from_row(r) for r in rows]

    def get_unrecalled(self, hours: int = 72, limit: int = 5) -> list[Milestone]:
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones WHERE is_recalled = FALSE AND occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ).fetchall()
            return [Milestone.from_row(r) for r in rows]

    def mark_recalled(self, milestone_id: int) -> None:
        with self._db._get_conn() as conn:
            conn.execute("UPDATE milestones SET is_recalled = TRUE WHERE id = ?", (milestone_id,))
            conn.commit()

    def get_all(self, limit: int = 50) -> list[Milestone]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones ORDER BY occurred_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [Milestone.from_row(r) for r in rows]
```

- [ ] **Step 5: 创建 preference.py — 用户偏好 CRUD**

Create: `kuakua_agent/services/memory/preference.py`

```python
import json
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import UserPreference


class PreferenceStore:
    DEFAULT_PREFS = {
        "praise_auto_enable": "true",
        "tts_enable": "false",
        "tts_voice": "default",
        "tts_speed": "1.0",
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
        "max_praises_per_day": "10",
        "global_cooldown_minutes": "30",
    }

    def __init__(self, db: Database | None = None):
        self._db = db or Database()
        self._init_defaults()

    def _init_defaults(self) -> None:
        with self._db._get_conn() as conn:
            for key, value in self.DEFAULT_PREFS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO user_preferences (key, value) VALUES (?, ?)",
                    (key, value),
                )
            conn.commit()

    def get(self, key: str) -> str | None:
        with self._db._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat()),
            )
            conn.commit()

    def get_all(self) -> dict[str, str]:
        with self._db._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM user_preferences").fetchall()
            return {r["key"]: r["value"] for r in rows}

    def get_bool(self, key: str) -> bool:
        v = self.get(key)
        return v.lower() in ("true", "1", "yes") if v else False

    def get_int(self, key: str, default: int = 0) -> int:
        v = self.get(key)
        return int(v) if v else default

    def get_float(self, key: str, default: float = 1.0) -> float:
        v = self.get(key)
        return float(v) if v else default
```

- [ ] **Step 6: 创建 profile.py — 场景画像 CRUD**

Create: `kuakua_agent/services/memory/profile.py`

```python
import json
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import SceneProfile


class ProfileStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()
        self._init_defaults()

    def _init_defaults(self) -> None:
        defaults = [
            ("work", 0.6, ["工作", "会议", "报告", "邮件"]),
            ("dev", 0.8, ["开发", "代码", "IDE", "Git"]),
            ("rest", 0.4, ["休息", "午休", "放空"]),
            ("entertainment", 0.3, ["视频", "游戏", "社交"]),
        ]
        with self._db._get_conn() as conn:
            for scene, weight, keywords in defaults:
                conn.execute(
                    "INSERT OR IGNORE INTO scene_profiles (scene, weight, keywords) VALUES (?, ?, ?)",
                    (scene, weight, json.dumps(keywords, ensure_ascii=False)),
                )
            conn.commit()

    def get_all(self) -> list[SceneProfile]:
        with self._db._get_conn() as conn:
            rows = conn.execute("SELECT * FROM scene_profiles ORDER BY weight DESC").fetchall()
            return [SceneProfile.from_row(r) for r in rows]

    def get_by_scene(self, scene: str) -> SceneProfile | None:
        with self._db._get_conn() as conn:
            row = conn.execute("SELECT * FROM scene_profiles WHERE scene = ?", (scene,)).fetchone()
            return SceneProfile.from_row(row) if row else None

    def update_weight(self, scene: str, weight: float) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "UPDATE scene_profiles SET weight = ?, updated_at = ? WHERE scene = ?",
                (weight, datetime.now().isoformat(), scene),
            )
            conn.commit()

    def update_keywords(self, scene: str, keywords: list[str]) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "UPDATE scene_profiles SET keywords = ?, updated_at = ? WHERE scene = ?",
                (json.dumps(keywords, ensure_ascii=False), datetime.now().isoformat(), scene),
            )
            conn.commit()
```

- [ ] **Step 7: 创建 feedback.py — 反馈记忆 CRUD**

Create: `kuakua_agent/services/memory/feedback.py`

```python
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import FeedbackLog, PraiseHistory


class FeedbackStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add(self, praise_id: int, reaction: str) -> FeedbackLog:
        with self._db._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO feedback_logs (praise_id, reaction) VALUES (?, ?)",
                (praise_id, reaction),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM feedback_logs WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return FeedbackLog.from_row(row)

    def get_reactions_for_praise(self, praise_id: int) -> list[FeedbackLog]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM feedback_logs WHERE praise_id = ? ORDER BY created_at DESC",
                (praise_id,),
            ).fetchall()
            return [FeedbackLog.from_row(r) for r in rows]

    def get_liked_praise_ids(self, limit: int = 10) -> list[int]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """SELECT DISTINCT praise_id FROM feedback_logs
                   WHERE reaction = 'liked' ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [r["praise_id"] for r in rows]
```

- [ ] **Step 8: 创建 praise_history 辅助函数（在 database.py 同目录新建 history.py）**

Create: `kuakua_agent/services/memory/history.py`

```python
import json
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import PraiseHistory


class PraiseHistoryStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add(self, content: str, trigger_type: str, context_snapshot: dict | None = None) -> PraiseHistory:
        with self._db._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO praise_history (content, trigger_type, context_snapshot) VALUES (?, ?, ?)",
                (content, trigger_type, json.dumps(context_snapshot or {}, ensure_ascii=False)),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM praise_history WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return PraiseHistory.from_row(row)

    def get_recent(self, limit: int = 20) -> list[PraiseHistory]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM praise_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [PraiseHistory.from_row(r) for r in rows]

    def get_today_count(self) -> int:
        today = datetime.now().date().isoformat()
        with self._db._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM praise_history WHERE date(created_at) = ?",
                (today,),
            ).fetchone()
            return row["cnt"] if row else 0
```

在 `__init__.py` 中补充导入:

```python
from kuakua_agent.services.memory.history import PraiseHistoryStore
```

- [ ] **Step 9: 写 milestone 单元测试**

Create: `tests/services/memory/test_milestone.py`

```python
import pytest
import tempfile
import os
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.milestone import MilestoneStore

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path=path)
    yield db
    os.unlink(path)

def test_add_and_get_recent(temp_db):
    store = MilestoneStore(db=temp_db)
    m = store.add("focus", "连续工作1小时", "番茄工作法完成")
    assert m.id is not None
    assert m.event_type == "focus"

    recent = store.get_recent(hours=1)
    assert len(recent) == 1
    assert recent[0].title == "连续工作1小时"

def test_mark_recalled(temp_db):
    store = MilestoneStore(db=temp_db)
    m = store.add("coding", "首次提交")
    assert m.is_recalled is False
    store.mark_recalled(m.id)
    unrecalled = store.get_unrecalled(hours=72)
    assert all(x.is_recalled for x in unrecalled) or len(unrecalled) == 0
```

- [ ] **Step 10: 验证测试通过**

Run: `cd d:/project/kuakua-agent && python -m pytest tests/services/memory/test_milestone.py -v`
Expected: PASS (2 tests)

- [ ] **Step 11: 提交**

```bash
git add kuakua_agent/services/memory/ tests/services/memory/
git commit -m "feat(memory): add SQLite-based memory layer with milestone/preference/profile/feedback CRUD"
```

---

## Task 2: brain 层 — 意图分流、Prompt模板、上下文组装、模型适配

### 依赖文件

- Create: `kuakua_agent/services/brain/__init__.py`
- Create: `kuakua_agent/services/brain/router.py`
- Create: `kuakua_agent/services/brain/prompt.py`
- Create: `kuakua_agent/services/brain/context.py`
- Create: `kuakua_agent/services/brain/adapter.py`
- Modify: `kuakua_agent/services/memory/__init__.py` (补充 PraiseHistoryStore 导入)
- Create: `tests/services/brain/test_context.py`

### 实现步骤

- [ ] **Step 1: 创建 brain/__init__.py**

Create: `kuakua_agent/services/brain/__init__.py`

```python
from kuakua_agent.services.brain.router import IntentRouter, Intent
from kuakua_agent.services.brain.prompt import PraisePromptManager
from kuakua_agent.services.brain.context import ContextBuilder
from kuakua_agent.services.brain.adapter import ModelAdapter

__all__ = [
    "IntentRouter",
    "Intent",
    "PraisePromptManager",
    "ContextBuilder",
    "ModelAdapter",
]
```

- [ ] **Step 2: 创建 router.py — 意图分流**

Create: `kuakua_agent/services/brain/router.py`

```python
from enum import Enum
from dataclasses import dataclass


class Intent(Enum):
    CHAT = "chat"              # 用户发起聊天
    SETTING = "setting"        # 设置类指令
    QUERY_MEMORY = "query_memory"  # 查询记忆
    FEEDBACK = "feedback"     # 反馈
    PROACTIVE_PRAISE = "proactive_praise"  # 主动夸夸触发
    UNKNOWN = "unknown"


@dataclass
class IntentRouter:
    """
    解析用户输入，识别意图。
    系统事件通过 route_event() 直接路由。
    """

    def route(self, text: str) -> Intent:
        text = text.strip().lower()
        if text.startswith(("设置", "关闭", "开启", "配置")):
            return Intent.SETTING
        if any(k in text for k in ["查一下", "看看", "我的记录", "里程碑"]):
            return Intent.QUERY_MEMORY
        if any(k in text for k in ["喜欢", "不喜欢", "夸得好", "太敷衍"]):
            return Intent.FEEDBACK
        return Intent.CHAT

    def route_event(self, event_type: str) -> Intent:
        if event_type.startswith("proactive_"):
            return Intent.PROACTIVE_PRAISE
        return Intent.UNKNOWN
```

- [ ] **Step 3: 创建 prompt.py — 夸夸 Prompt 模板管理**

Create: `kuakua_agent/services/brain/prompt.py`

```python
from dataclasses import dataclass


PRAISE_SYSTEM_PROMPT = """你是一个温暖治愈的AI夸夸助手，名为"夸夸"。

你的职责是：
1. 温柔倾听用户的倾诉和心情
2. 给予正向鼓励和心理支持
3. 夸具体、夸真实行为，不夸空洞的外貌或套话
4. 语气温柔亲切，像朋友一样陪伴
5. 不评判、不说教，只是陪伴和倾听
6. 结合用户的历史记录和当前场景，夸出个性化、有延续性的内容
7. 回复简洁温暖，每条不超过120字
8. 同风格文案近期出现超过2次时，必须换一个角度或方式夸

重要原则：
- 提到用户里程碑时，用自然的方式提起，不要像在完成任务
- 结合当前时段（早间/日间/晚间）和场景（工作/开发/休息）来调整语气
- 夸奖要具体到事件和行为，避免"你真棒""太厉害了"这类无内容的夸"""

PRAISE_USER_TEMPLATE = """## 当前时间与场景
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 用户最近里程碑（3天内）
{recent_milestones}

## 用户画像
{praise_history_summary}

## 用户本次输入
{user_message}

请根据以上信息，给用户一段温暖、具体、不重复的夸夸。"""


PRAISE_PROACTIVE_TEMPLATE = """## 触发信息
触发类型: {trigger_type}
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 用户最近里程碑（3天内，未被提起过的）
{unrecalled_milestones}

## 用户画像
{praise_history_summary}

## 当前环境上下文
{env_context}

请根据以上信息，主动给用户一段温暖、恰如其分、有延续性的夸夸。
主动夸夸要自然流露，不要生硬。长度控制在80字以内。"""


@dataclass
class PraisePromptManager:
    def build_user_prompt(
        self,
        user_message: str,
        time_of_day: str,
        scene_context: str,
        recent_milestones: str,
        praise_history_summary: str,
        weather: str = "未知",
    ) -> str:
        return PRAISE_USER_TEMPLATE.format(
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_milestones,
            praise_history_summary=praise_history_summary,
            user_message=user_message,
            weather=weather,
        )

    def build_proactive_prompt(
        self,
        trigger_type: str,
        time_of_day: str,
        scene_context: str,
        unrecalled_milestones: str,
        praise_history_summary: str,
        env_context: str,
        weather: str = "未知",
    ) -> str:
        return PRAISE_PROACTIVE_TEMPLATE.format(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            scene_context=scene_context,
            unrecalled_milestones=unrecalled_milestones,
            praise_history_summary=praise_history_summary,
            env_context=env_context,
            weather=weather,
        )

    def get_system_prompt(self) -> str:
        return PRAISE_SYSTEM_PROMPT
```

- [ ] **Step 4: 创建 context.py — 上下文组装（含防重复）**

Create: `kuakua_agent/services/brain/context.py`

```python
import json
from datetime import datetime, timedelta
from kuakua_agent.services.memory import (
    MilestoneStore,
    PraiseHistoryStore,
    PreferenceStore,
    ProfileStore,
)
from kuakua_agent.services.brain.prompt import PraisePromptManager


def get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return "早间"
    elif 9 <= hour < 18:
        return "日间"
    else:
        return "晚间"


def summarize_praise_history(history: list, max_chars: int = 300) -> str:
    """压缩夸夸历史，标注重复风格，避免近期同风格文案"""
    if not history:
        return "暂无夸夸历史"
    parts = []
    seen_styles: set[str] = set()
    for h in history[:10]:
        style_key = h.content[:10]
        if style_key in seen_styles and len(seen_styles) >= 2:
            continue
        seen_styles.add(style_key)
        parts.append(f"- {h.content[:80]}")
    summary = "\n".join(parts)
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."
    return summary


def deduplicate_milestones(milestones: list, within_hours: int = 1) -> list:
    """1小时内同类型里程碑只保留最新一条"""
    seen: dict[str, tuple] = {}
    for m in milestones:
        key = (m.event_type, m.occurred_at.replace(minute=0, second=0, microsecond=0))
        if key not in seen or m.occurred_at > seen[key][1]:
            seen[key] = (m, m.occurred_at)
    return [v[0] for v in seen.values()]


class ContextBuilder:
    def __init__(
        self,
        milestone_store: MilestoneStore | None = None,
        history_store: PraiseHistoryStore | None = None,
        pref_store: PreferenceStore | None = None,
        profile_store: ProfileStore | None = None,
    ):
        self._ms = milestone_store or MilestoneStore()
        self._hs = history_store or PraiseHistoryStore()
        self._pref = pref_store or PreferenceStore()
        self._profile = profile_store or ProfileStore()
        self._prompt_mgr = PraisePromptManager()

    def build_user_context(
        self,
        user_message: str,
        weather: str = "未知",
    ) -> tuple[list[dict], str]:
        """返回 messages 列表和本次夸夸内容（用于存入历史）"""
        time_of_day = get_time_of_day()

        # 近期里程碑（去重）
        recent = self._ms.get_recent(hours=72, limit=10)
        recent = deduplicate_milestones(recent)
        recent_str = (
            "\n".join(
                f"- [{m.event_type}] {m.title}: {m.description or ''}"
                for m in recent
            )
            or "暂无近期里程碑"
        )

        # 夸夸历史摘要
        history = self._hs.get_recent(limit=20)
        history_summary = summarize_praise_history(history)

        # 场景
        profiles = self._profile.get_all()
        top_scene = profiles[0].scene if profiles else "一般"
        scene_context = f"主要场景: {top_scene}"

        # 组装
        user_prompt_text = self._prompt_mgr.build_user_prompt(
            user_message=user_message,
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_str,
            praise_history_summary=history_summary,
            weather=weather,
        )

        messages = [
            {"role": "system", "content": self._prompt_mgr.get_system_prompt()},
            {"role": "user", "content": user_prompt_text},
        ]
        return messages, user_prompt_text

    def build_proactive_context(
        self,
        trigger_type: str,
        env_context: str = "",
        weather: str = "未知",
    ) -> tuple[list[dict], str]:
        """主动夸夸上下文"""
        time_of_day = get_time_of_day()

        # 未被提起的里程碑
        unrecalled = self._ms.get_unrecalled(hours=72, limit=5)
        unrecalled_str = (
            "\n".join(
                f"- [{m.event_type}] {m.title}: {m.description or ''}"
                for m in unrecalled
            )
            or "暂无新鲜里程碑"
        )

        # 夸夸历史摘要
        history = self._hs.get_recent(limit=20)
        history_summary = summarize_praise_history(history)

        # 场景
        profiles = self._profile.get_all()
        top_scene = profiles[0].scene if profiles else "一般"
        scene_context = f"主要场景: {top_scene}"

        user_prompt_text = self._prompt_mgr.build_proactive_prompt(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            scene_context=scene_context,
            unrecalled_milestones=unrecalled_str,
            praise_history_summary=history_summary,
            env_context=env_context,
            weather=weather,
        )

        messages = [
            {"role": "system", "content": self._prompt_mgr.get_system_prompt()},
            {"role": "user", "content": user_prompt_text},
        ]
        return messages, user_prompt_text
```

- [ ] **Step 5: 创建 adapter.py — Ark API 适配器**

Create: `kuakua_agent/services/brain/adapter.py`

```python
import httpx
from kuakua_agent.config import settings


class ModelAdapter:
    def __init__(self):
        self.base_url = settings.ark_base_url
        self.api_key = settings.ark_api_key
        self.model_id = settings.ark_model_id

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    async def complete_async(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
```

- [ ] **Step 6: 写 context 单元测试（防重复逻辑）**

Create: `tests/services/brain/test_context.py`

```python
import pytest
from datetime import datetime
from kuakua_agent.services.memory.models import Milestone, PraiseHistory
from kuakua_agent.services.brain.context import deduplicate_milestones, summarize_praise_history


def test_deduplicate_milestones_same_hour():
    now = datetime.now()
    milestones = [
        Milestone(1, "focus", "专注1", None, now, now, False),
        Milestone(2, "focus", "专注2", None, now, now, False),
        Milestone(3, "coding", "编码1", None, now, now, False),
    ]
    result = deduplicate_milestones(milestones)
    assert len(result) == 2  # focus deduped to latest
    assert result[0].title == "专注2"  # later one kept


def test_summarize_praise_history_dedup():
    history = [
        PraiseHistory(1, "你今天工作很努力", "active", None, datetime.now()),
        PraiseHistory(2, "你今天工作很努力", "active", None, datetime.now()),
        PraiseHistory(3, "休息一下吧", "proactive", None, datetime.now()),
    ]
    summary = summarize_praise_history(history, max_chars=200)
    # Two identical start strings should be deduped
    lines = [l for l in summary.split("\n") if l.startswith("-")]
    assert len(lines) <= 3
```

- [ ] **Step 7: 运行测试**

Run: `cd d:/project/kuakua-agent && python -m pytest tests/services/brain/test_context.py -v`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add kuakua_agent/services/brain/ tests/services/brain/
git commit -m "feat(brain): add router/context/prompt/adapter brain layer"
```

---

## Task 3: output 层 — 桌面通知 + Fish Audio TTS（含静默兜底）

### 依赖文件

- Create: `kuakua_agent/services/output/__init__.py`
- Create: `kuakua_agent/services/output/base.py`
- Create: `kuakua_agent/services/output/notifier.py`
- Create: `kuakua_agent/services/output/tts.py`
- Create: `tests/services/output/test_tts.py`

### 实现步骤

- [ ] **Step 1: 创建 output/__init__.py**

Create: `kuakua_agent/services/output/__init__.py`

```python
from kuakua_agent.services.output.base import OutputChannel, OutputManager
from kuakua_agent.services.output.notifier import SystemNotifier
from kuakua_agent.services.output.tts import FishTTS

__all__ = [
    "OutputChannel",
    "OutputManager",
    "SystemNotifier",
    "FishTTS",
]
```

- [ ] **Step 2: 创建 base.py — 输出基类与统一管理器**

Create: `kuakua_agent/services/output/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio


@dataclass
class OutputResult:
    success: bool
    channel: str
    content: str
    error: str | None = None


class OutputChannel(ABC):
    @abstractmethod
    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        """发送内容，返回结果"""
        ...

    @abstractmethod
    def supports(self, channel_type: str) -> bool:
        """是否支持该通道类型"""
        ...


class OutputManager:
    def __init__(self):
        self._channels: list[OutputChannel] = []

    def register(self, channel: OutputChannel) -> None:
        self._channels.append(channel)

    async def dispatch(self, content: str, channel_types: list[str] | None = None, metadata: dict | None = None) -> list[OutputResult]:
        """
        向所有已注册通道分发内容。
        channel_types 为空表示所有通道；否则只发指定的。
        异常通道不中断流程，直接记录错误。
        """
        results = []
        tasks = []
        for ch in self._channels:
            if channel_types and not any(ch.supports(ct) for ct in channel_types):
                continue
            tasks.append(self._safe_send(ch, content, metadata or {}))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, OutputResult) else OutputResult(success=False, channel="unknown", content=content, error=str(r)) for r in results]

    async def _safe_send(self, channel: OutputChannel, content: str, metadata: dict) -> OutputResult:
        try:
            return await channel.send(content, metadata)
        except Exception as e:
            return OutputResult(success=False, channel=type(channel).__name__, content=content, error=str(e))
```

- [ ] **Step 3: 创建 notifier.py — 桌面通知**

Create: `kuakua_agent/services/output/notifier.py`

```python
import asyncio
import sys
from kuakua_agent.services.output.base import OutputChannel, OutputResult


class SystemNotifier(OutputChannel):
    def supports(self, channel_type: str) -> bool:
        return channel_type in ("notification", "notifier", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        title = (metadata or {}).get("title", "夸夸")
        try:
            if sys.platform == "win32":
                await self._win_notify(title, content)
            elif sys.platform == "darwin":
                await self._mac_notify(title, content)
            else:
                await self._linux_notify(title, content)
            return OutputResult(success=True, channel="notifier", content=content)
        except Exception as e:
            return OutputResult(success=False, channel="notifier", content=content, error=str(e))

    async def _win_notify(self, title: str, content: str) -> None:
        # 使用 asyncio + PowerShell 实现 Windows 通知
        script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{content}")) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("kuakua-agent").Show($toast)
        '''
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _mac_notify(self, title: str, content: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", f'display notification "{content}" with title "{title}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _linux_notify(self, title: str, content: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "notify-send", title, content,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
```

- [ ] **Step 4: 创建 tts.py — Fish Audio TTS（含静默兜底）**

Create: `kuakua_agent/services/output/tts.py`

```python
import asyncio
import hashlib
import httpx
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from kuakua_agent.services.output.base import OutputChannel, OutputResult
from kuakua_agent.services.memory import PreferenceStore


class FishTTS(OutputChannel):
    # Fish Audio API 地址（可配置）
    DEFAULT_API_URL = "https://api.fish.audio/v1/tts"

    def __init__(self, pref_store: PreferenceStore | None = None):
        self._pref = pref_store or PreferenceStore()
        self._cache_dir = Path(tempfile.gettempdir()) / "kuakua_tts"
        self._cache_dir.mkdir(exist_ok=True)

    def supports(self, channel_type: str) -> bool:
        return channel_type in ("tts", "voice", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        if not self._pref.get_bool("tts_enable"):
            return OutputResult(success=False, channel="tts", content=content, error="TTS未开启")

        api_url = (metadata or {}).get("api_url", self.DEFAULT_API_URL)
        voice_id = self._pref.get("tts_voice") or "default"
        speed = self._pref.get_float("tts_speed", 1.0)

        cache_key = hashlib.md5(f"{content}:{voice_id}:{speed}".encode()).hexdigest()
        cached = self._cache_dir / f"{cache_key}.mp3"

        try:
            if cached.exists():
                await self._play_audio(str(cached))
            else:
                audio_data = await self._fetch_tts(content, api_url, voice_id, speed)
                cached.write_bytes(audio_data)
                await self._play_audio(str(cached))
            return OutputResult(success=True, channel="tts", content=content)
        except Exception as e:
            # 静默兜底：TTS异常降级为纯通知，不向主流程抛异常
            return OutputResult(success=False, channel="tts", content=content, error=f"TTS静默失败: {e}")

    async def _fetch_tts(self, text: str, api_url: str, voice_id: str, speed: float) -> bytes:
        payload = {
            "model": voice_id,
            "text": text,
            "speed": speed,
        }
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fish Audio API失败: {response.status_code}")
        return response.content

    async def _play_audio(self, filepath: str) -> None:
        """根据平台播放音频文件"""
        if sys.platform == "win32":
            # 使用 mpv 或直接用 powershell 播放
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command",
                f'(New-Object System.Media.SoundPlayer "{filepath}").PlaySync()',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        elif sys.platform == "darwin":
            proc = await asyncio.create_subprocess_exec(
                "afplay", filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        else:
            proc = await asyncio.create_subprocess_exec(
                "mpg123", filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
```

- [ ] **Step 5: 提交**

```bash
git add kuakua_agent/services/output/
git commit -m "feat(output): add notifier + Fish TTS with silent fallback"
```

---

## Task 4: scheduler 层 — 触发规则 + 冷却控制 + 调度循环

### 依赖文件

- Create: `kuakua_agent/services/scheduler/__init__.py`
- Create: `kuakua_agent/services/scheduler/events.py`
- Create: `kuakua_agent/services/scheduler/rules.py`
- Create: `kuakua_agent/services/scheduler/cooldown.py`
- Create: `kuakua_agent/services/scheduler/scheduler.py`
- Modify: `kuakua_agent/main.py` (注册调度器)
- Create: `tests/services/scheduler/test_rules.py`

### 实现步骤

- [ ] **Step 1: 创建 scheduler/__init__.py**

Create: `kuakua_agent/services/scheduler/__init__.py`

```python
from kuakua_agent.services.scheduler.events import SchedulerEvent, TriggerType
from kuakua_agent.services.scheduler.rules import TriggerRule, TimeCondition, BehaviorCondition
from kuakua_agent.services.scheduler.cooldown import CooldownManager
from kuakua_agent.services.scheduler.scheduler import PraiseScheduler

__all__ = [
    "SchedulerEvent",
    "TriggerType",
    "TriggerRule",
    "TimeCondition",
    "BehaviorCondition",
    "CooldownManager",
    "PraiseScheduler",
]
```

- [ ] **Step 2: 创建 events.py — 调度事件定义**

Create: `kuakua_agent/services/scheduler/events.py`

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TriggerType(Enum):
    SCHEDULED = "scheduled"       # 定时触发
    BEHAVIOR_DETECTED = "behavior_detected"  # 行为检测触发
    FIRST_AWAKE = "first_awake"   # 首次亮屏
    FOCUS_MILESTONE = "focus_milestone"  # 专注里程碑达成
    CUSTOM = "custom"


@dataclass
class SchedulerEvent:
    trigger_type: TriggerType
    occurred_at: datetime
    data: dict | None = None
    rule_name: str | None = None
```

- [ ] **Step 3: 创建 rules.py — 触发规则定义**

Create: `kuakua_agent/services/scheduler/rules.py`

```python
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Literal


@dataclass
class TimeCondition:
    """时间条件"""
    type: Literal["time_range", "moment"]
    # time_range 类型
    start: str | None = None  # "07:00"
    end: str | None = None    # "09:00"
    days: list[int] | None = None  # [1,2,3,4,5] 工作日
    # moment 类型
    moment: str | None = None  # "first_awake"


@dataclass
class BehaviorCondition:
    """行为条件"""
    type: Literal["focus_duration", "app_category", "event_type"]
    min_minutes: int = 0
    category: str | None = None
    event_type: str | None = None


@dataclass
class TriggerRule:
    name: str
    time_conditions: list[TimeCondition] = field(default_factory=list)
    behavior_conditions: list[BehaviorCondition] = field(default_factory=list)
    cooldown_minutes: int = 30
    max_per_day: int = 10
    enabled: bool = True

    def evaluate_time(self, now: datetime) -> bool:
        """检查时间条件是否满足"""
        if not self.time_conditions:
            return True
        # 全部满足（AND）
        return all(self._eval_single_time(tc, now) for tc in self.time_conditions)

    def _eval_single_time(self, tc: TimeCondition, now: datetime) -> bool:
        if tc.type == "time_range":
            if tc.days and now.isoweekday() not in tc.days:
                return False
            start_t = datetime.strptime(tc.start, "%H:%M").time()
            end_t = datetime.strptime(tc.end, "%H:%M").time()
            cur = now.time()
            if start_t <= end_t:
                return start_t <= cur <= end_t
            else:
                return cur >= start_t or cur <= end_t
        if tc.type == "moment":
            if tc.moment == "first_awake":
                return 5 <= now.hour < 9
        return True

    def evaluate_behavior(self, behavior_data: dict) -> bool:
        """检查行为条件是否满足"""
        if not self.behavior_conditions:
            return True
        return all(self._eval_single_behavior(bc, behavior_data) for bc in self.behavior_conditions)

    def _eval_single_behavior(self, bc: BehaviorCondition, data: dict) -> bool:
        if bc.type == "focus_duration":
            return data.get("focus_minutes", 0) >= bc.min_minutes
        if bc.type == "app_category":
            return data.get("category_minutes", {}).get(bc.category, 0) >= bc.min_minutes
        if bc.type == "event_type":
            return data.get("last_event") == bc.event_type
        return True


# 内置默认规则
DEFAULT_RULES = [
    TriggerRule(
        name="早间专注夸",
        time_conditions=[
            TimeCondition(type="time_range", start="07:00", end="09:00", days=[1, 2, 3, 4, 5]),
            TimeCondition(type="moment", moment="first_awake"),
        ],
        behavior_conditions=[
            BehaviorCondition(type="focus_duration", min_minutes=30),
        ],
        cooldown_minutes=60,
    ),
    TriggerRule(
        name="午后工作鼓励",
        time_conditions=[
            TimeCondition(type="time_range", start="13:00", end="14:00", days=[1, 2, 3, 4, 5]),
        ],
        behavior_conditions=[
            BehaviorCondition(type="focus_duration", min_minutes=60),
        ],
        cooldown_minutes=120,
    ),
    TriggerRule(
        name="晚间休息提醒",
        time_conditions=[
            TimeCondition(type="time_range", start="18:00", end="20:00"),
        ],
        behavior_conditions=[
            BehaviorCondition(type="app_category", category="development", min_minutes=45),
        ],
        cooldown_minutes=45,
    ),
]
```

- [ ] **Step 4: 创建 cooldown.py — 冷却/上限/免打扰**

Create: `kuakua_agent/services/scheduler/cooldown.py`

```python
from datetime import datetime, time
from kuakua_agent.services.memory import PreferenceStore


class CooldownManager:
    def __init__(self, pref_store: PreferenceStore | None = None):
        self._pref = pref_store or PreferenceStore()
        self._last_praise: datetime | None = None
        self._daily_count: int = 0
        self._daily_reset_date: str | None = None

    def _check_daily_reset(self) -> None:
        today = datetime.now().date().isoformat()
        if self._daily_reset_date != today:
            self._daily_count = 0
            self._daily_reset_date = today

    def is_global_enabled(self) -> bool:
        """全局开关：praise_auto_enable"""
        return self._pref.get_bool("praise_auto_enable")

    def is_in_do_not_disturb(self) -> bool:
        """检查当前是否在免打扰时段"""
        now = datetime.now()
        start_str = self._pref.get("do_not_disturb_start") or "22:00"
        end_str = self._pref.get("do_not_disturb_end") or "08:00"
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
        cur = now.time()
        if start_t <= end_t:
            return start_t <= cur <= end_t
        else:
            return cur >= start_t or cur <= end_t

    def is_in_cooldown(self) -> bool:
        """全局冷却检查"""
        if self._last_praise is None:
            return False
        cooldown_min = self._pref.get_int("global_cooldown_minutes", 30)
        elapsed = (datetime.now() - self._last_praise).total_seconds() / 60
        return elapsed < cooldown_min

    def is_daily_limit_reached(self) -> bool:
        """每日上限检查"""
        self._check_daily_reset()
        max_per_day = self._pref.get_int("max_praises_per_day", 10)
        return self._daily_count >= max_per_day

    def can_praise(self) -> bool:
        """综合判断是否可以夸"""
        if not self.is_global_enabled():
            return False
        if self.is_in_do_not_disturb():
            return False
        if self.is_in_cooldown():
            return False
        if self.is_daily_limit_reached():
            return False
        return True

    def record_praise(self) -> None:
        """记录一次夸夸，更新计数"""
        self._last_praise = datetime.now()
        self._check_daily_reset()
        self._daily_count += 1
```

- [ ] **Step 5: 创建 scheduler.py — 调度循环（后台）**

Create: `kuakua_agent/services/scheduler/scheduler.py`

```python
import asyncio
import logging
from datetime import datetime
from kuakua_agent.services.scheduler.events import SchedulerEvent, TriggerType
from kuakua_agent.services.scheduler.rules import TriggerRule, DEFAULT_RULES
from kuakua_agent.services.scheduler.cooldown import CooldownManager
from kuakua_agent.services.brain import ContextBuilder, ModelAdapter
from kuakua_agent.services.memory import MilestoneStore, PraiseHistoryStore
from kuakua_agent.services.output import OutputManager, SystemNotifier, FishTTS

logger = logging.getLogger(__name__)


class PraiseScheduler:
    POLL_INTERVAL = 30  # 秒，轻量化轮询

    def __init__(
        self,
        cooldown_mgr: CooldownManager | None = None,
        rules: list[TriggerRule] | None = None,
    ):
        self._cooldown = cooldown_mgr or CooldownManager()
        self._rules = rules or DEFAULT_RULES
        self._running = False
        self._task: asyncio.Task | None = None
        self._output_mgr = OutputManager()
        self._output_mgr.register(SystemNotifier())
        self._output_mgr.register(FishTTS())
        self._context_builder = ContextBuilder()
        self._model = ModelAdapter()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("夸夸调度器已启动")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("夸夸调度器已停止")

    async def trigger_now(self, event: SchedulerEvent) -> str | None:
        """立即触发一次夸夸，返回夸夸内容"""
        if not self._cooldown.can_praise():
            logger.info("触发被冷却拦截")
            return None

        messages, _ = self._context_builder.build_proactive_context(
            trigger_type=event.trigger_type.value,
            env_context=str(event.data or {}),
        )

        try:
            praise_content = await self._model.complete_async(messages)
        except Exception as e:
            logger.error(f"生成夸夸失败: {e}")
            return None

        # 存入历史
        history_store = PraiseHistoryStore()
        history_store.add(content=praise_content, trigger_type=event.trigger_type.value, context_snapshot=event.data)

        # 标记里程碑为已提起
        if event.data and "milestone_id" in event.data:
            ms = MilestoneStore()
            ms.mark_recalled(event.data["milestone_id"])

        # 输出
        await self._output_mgr.dispatch(praise_content, metadata={"trigger": event.trigger_type.value})
        self._cooldown.record_praise()
        logger.info(f"主动夸夸已发送: {praise_content[:30]}...")
        return praise_content

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._check_rules()
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
            await asyncio.sleep(self.POLL_INTERVAL)

    async def _check_rules(self) -> None:
        if not self._cooldown.can_praise():
            return

        now = datetime.now()
        milestone_store = MilestoneStore()

        for rule in self._rules:
            if not rule.enabled:
                continue
            if not rule.evaluate_time(now):
                continue

            # 获取行为数据（目前从 milestones 推断）
            recent = milestone_store.get_recent(hours=2)
            focus_minutes = sum(
                25 for m in recent
                if m.event_type == "focus" and (now - m.occurred_at).total_seconds() < 7200
            )
            behavior_data = {"focus_minutes": focus_minutes}

            if rule.evaluate_behavior(behavior_data):
                event = SchedulerEvent(
                    trigger_type=TriggerType.SCHEDULED,
                    occurred_at=now,
                    data=behavior_data,
                    rule_name=rule.name,
                )
                await self.trigger_now(event)
                break  # 一轮只触发一次
```

- [ ] **Step 6: 修改 main.py — 注册调度器**

Read first: `kuakua_agent/main.py`

```python
# 在 main.py 的 lifespan 或 startup 事件中启动调度器
from kuakua_agent.services.scheduler import PraiseScheduler

scheduler: PraiseScheduler | None = None

@app.on_event("startup")
async def startup():
    global scheduler
    scheduler = PraiseScheduler()
    await scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    if scheduler:
        await scheduler.stop()
```

- [ ] **Step 7: 写 rules 单元测试**

Create: `tests/services/scheduler/test_rules.py`

```python
import pytest
from datetime import datetime
from kuakua_agent.services.scheduler.rules import TriggerRule, TimeCondition, BehaviorCondition


def test_time_range_weekday():
    rule = TriggerRule(
        name="test",
        time_conditions=[
            TimeCondition(type="time_range", start="09:00", end="17:00", days=[1, 2, 3, 4, 5]),
        ],
    )
    monday_10 = datetime(2026, 4, 27, 10, 0)  # Monday
    saturday_10 = datetime(2026, 4, 25, 10, 0)  # Saturday
    assert rule.evaluate_time(monday_10) is True
    assert rule.evaluate_time(saturday_10) is False


def test_behavior_focus_duration():
    rule = TriggerRule(
        name="test",
        behavior_conditions=[BehaviorCondition(type="focus_duration", min_minutes=60)],
    )
    assert rule.evaluate_behavior({"focus_minutes": 90}) is True
    assert rule.evaluate_behavior({"focus_minutes": 30}) is False


def test_combined_conditions():
    rule = TriggerRule(
        name="combined",
        time_conditions=[TimeCondition(type="time_range", start="09:00", end="17:00", days=[1, 2, 3, 4, 5])],
        behavior_conditions=[BehaviorCondition(type="focus_duration", min_minutes=30)],
    )
    monday = datetime(2026, 4, 27, 10, 0)
    assert rule.evaluate_time(monday) is True
    assert rule.evaluate_behavior({"focus_minutes": 60}) is True
    # 单独时间满足但行为不满足
    assert rule.evaluate_behavior({"focus_minutes": 10}) is False
```

- [ ] **Step 8: 运行测试**

Run: `cd d:/project/kuakua-agent && python -m pytest tests/services/scheduler/test_rules.py -v`
Expected: PASS (3 tests)

- [ ] **Step 9: 提交**

```bash
git add kuakua_agent/services/scheduler/ kuakua_agent/main.py tests/services/scheduler/
git commit -m "feat(scheduler): add trigger rules + cooldown + background scheduler loop"
```

---

## Task 5: 接入现有项目 — 路由扩展 + 服务对接

### 依赖文件

- Create: `kuakua_agent/schemas/praise.py`
- Modify: `kuakua_agent/api/routes.py`
- Modify: `kuakua_agent/services/memory/__init__.py` (补充 PraiseHistoryStore)

### 实现步骤

- [ ] **Step 1: 创建 schemas/praise.py — 夸夸相关 Pydantic 模型**

Create: `kuakua_agent/schemas/praise.py`

```python
from pydantic import BaseModel, Field


class PraiseConfig(BaseModel):
    praise_auto_enable: bool = True
    tts_enable: bool = False
    tts_voice: str = "default"
    tts_speed: float = 1.0
    do_not_disturb_start: str = "22:00"
    do_not_disturb_end: str = "08:00"
    max_praises_per_day: int = 10
    global_cooldown_minutes: int = 30


class MilestoneCreate(BaseModel):
    event_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    occurred_at: str | None = None  # ISO格式


class MilestoneResponse(BaseModel):
    id: int
    event_type: str
    title: str
    description: str | None
    occurred_at: str
    is_recalled: bool


class ProfileResponse(BaseModel):
    scene: str
    weight: float
    keywords: list[str]


class FeedbackCreate(BaseModel):
    praise_id: int
    reaction: str = Field(pattern="^(liked|disliked|neutral)$")
```

- [ ] **Step 2: 修改 routes.py — 新增夸夸接口**

Read first: `kuakua_agent/api/routes.py`

在 routes.py 中新增导入:
```python
from kuakua_agent.schemas.praise import PraiseConfig, MilestoneCreate, MilestoneResponse, ProfileResponse, FeedbackCreate
from kuakua_agent.services.memory import MilestoneStore, PraiseHistoryStore, PreferenceStore, ProfileStore, FeedbackStore
from kuakua_agent.services.brain import ContextBuilder, ModelAdapter
```

在路由初始化时实例化 stores 和 brain 组件。

新增路由函数：

```python
# GET /settings/praise
@router.get("/settings/praise", response_model=PraiseConfig)
async def get_praise_config() -> PraiseConfig:
    pref = PreferenceStore()
    return PraiseConfig(
        praise_auto_enable=pref.get_bool("praise_auto_enable"),
        tts_enable=pref.get_bool("tts_enable"),
        tts_voice=pref.get("tts_voice") or "default",
        tts_speed=pref.get_float("tts_speed", 1.0),
        do_not_disturb_start=pref.get("do_not_disturb_start") or "22:00",
        do_not_disturb_end=pref.get("do_not_disturb_end") or "08:00",
        max_praises_per_day=pref.get_int("max_praises_per_day", 10),
        global_cooldown_minutes=pref.get_int("global_cooldown_minutes", 30),
    )

# PUT /settings/praise
@router.put("/settings/praise", response_model=ApiResponse[PraiseConfig])
async def update_praise_config(payload: PraiseConfig) -> ApiResponse[PraiseConfig]:
    pref = PreferenceStore()
    pref.set("praise_auto_enable", str(payload.praise_auto_enable).lower())
    pref.set("tts_enable", str(payload.tts_enable).lower())
    pref.set("tts_voice", payload.tts_voice)
    pref.set("tts_speed", str(payload.tts_speed))
    pref.set("do_not_disturb_start", payload.do_not_disturb_start)
    pref.set("do_not_disturb_end", payload.do_not_disturb_end)
    pref.set("max_praises_per_day", str(payload.max_praises_per_day))
    pref.set("global_cooldown_minutes", str(payload.global_cooldown_minutes))
    return ApiResponse(data=payload)

# GET /memory/milestones
@router.get("/memory/milestones", response_model=list[MilestoneResponse])
async def get_milestones() -> list[MilestoneResponse]:
    store = MilestoneStore()
    milestones = store.get_all()
    return [
        MilestoneResponse(
            id=m.id,
            event_type=m.event_type,
            title=m.title,
            description=m.description,
            occurred_at=m.occurred_at.isoformat(),
            is_recalled=m.is_recalled,
        )
        for m in milestones
    ]

# POST /memory/milestones
@router.post("/memory/milestones", response_model=ApiResponse[MilestoneResponse])
async def create_milestone(payload: MilestoneCreate) -> ApiResponse[MilestoneResponse]:
    from datetime import datetime
    occurred = datetime.fromisoformat(payload.occurred_at) if payload.occurred_at else None
    store = MilestoneStore()
    m = store.add(event_type=payload.event_type, title=payload.title, description=payload.description, occurred_at=occurred)
    return ApiResponse(data=MilestoneResponse(
        id=m.id, event_type=m.event_type, title=m.title,
        description=m.description, occurred_at=m.occurred_at.isoformat(), is_recalled=m.is_recalled,
    ))

# GET /memory/profiles
@router.get("/memory/profiles", response_model=list[ProfileResponse])
async def get_profiles() -> list[ProfileResponse]:
    store = ProfileStore()
    profiles = store.get_all()
    return [ProfileResponse(scene=p.scene, weight=p.weight, keywords=p.keywords) for p in profiles]

# POST /feedback
@router.post("/feedback", response_model=ApiResponse[dict])
async def submit_feedback(payload: FeedbackCreate) -> ApiResponse[dict]:
    store = FeedbackStore()
    store.add(praise_id=payload.praise_id, reaction=payload.reaction)
    return ApiResponse(data={"recorded": True})
```

- [ ] **Step 3: 提交**

```bash
git add kuakua_agent/schemas/praise.py kuakua_agent/api/routes.py kuakua_agent/services/memory/__init__.py
git commit -m "feat(api): add praise config/milestone/profile/feedback endpoints"
```

---

## Task 6: 前端对接（Electron/Vue 桌面端）

> 前端任务较独立，可在 backend 实现完成后单独进行。此处先定义接口和数据结构。

### 依赖文件

- Modify: `desktop/src/renderer/constants/index.ts` — 新增夸夸配置常量
- Modify: `desktop/src/renderer/store/chat.ts` — 新增反馈方法
- Create: `desktop/src/renderer/api/praise.ts` — 夸夸 API 调用
- Modify: `desktop/src/renderer/views/Settings.vue` — 新增夸夸配置面板

### 实现步骤（前端独立完成，此处定义接口）

前端需对接以下 API：

```
GET  /settings/praise         → PraiseConfig
PUT  /settings/praise          → PraiseConfig
GET  /memory/milestones        → MilestoneResponse[]
POST /memory/milestones        → MilestoneResponse
GET  /memory/profiles          → ProfileResponse[]
POST /feedback                 → { recorded: true }
```

---

## Task 核对清单（开发完成后自检）

- [ ] memory 层 5 张表全部创建，CRUD 可独立运行测试
- [ ] brain 层 context 去重逻辑有单元测试覆盖
- [ ] output 层 TTS 异常走静默兜底，不抛异常到主流程
- [ ] scheduler 轮询间隔 30 秒，全局开关关闭后轮询停止
- [ ] 所有新增 API 路由在 routes.py 中注册
- [ ] 原有 `/chat` 接口不受影响
- [ ] 所有模块通过 `python -m pytest` 测试

---

## 注意事项

1. **Task 1 (memory)** 是所有层的基础，先完成并测试通过再继续
2. **Task 3 (output)** 的 TTS 静默兜底是关键约束，测试时需要 mock 网络异常
3. **Task 4 (scheduler)** 的 `_loop` 在 FastAPI 的 `lifespan` 事件中注册，不在请求周期内运行
4. **Task 5 (接入)** 只需要扩展 routes，原有 `chat_service.py` 不修改
5. **前端任务 (Task 6)** 独立于 backend，可并行或后续单独做
