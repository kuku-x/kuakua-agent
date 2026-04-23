# 夸夸Agent桌面应用 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建完整的夸夸Agent桌面应用，包含前端(Electron+Vue3)和后端(FastAPI)，实现电脑行为监控、每日AI夸夸总结、聊天陪伴功能。

**Architecture:** 项目采用前后端分离架构：
- **后端 (Python FastAPI)**: 提供 REST API 和 WebSocket，管理数据存储、调用 ActivityWatch API 和豆包 API
- **前端 (Electron + Vue3)**: 桌面客户端 UI，展示夸夸卡片、时间图表、聊天界面
- **ActivityWatch**: 独立运行的数据源，提供 Windows 使用行为数据

**Tech Stack:**
- 后端: FastAPI, SQLAlchemy, aiosqlite, httpx, websockets
- 前端: Electron, Vue 3, TypeScript, Pinia, Chart.js
- AI: 豆包 API (OpenAI 兼容格式)
- 存储: SQLite

---

## Phase 1: 后端核心架构

### Task 1: 后端项目初始化

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "kuakua-backend"
version = "0.1.0"
requires-python = ">=3.10"

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.109.0"
uvicorn = { extras = ["standard"], version = "^0.27.0" }
httpx = "^0.26.0"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
sqlalchemy = "^2.0.25"
aiosqlite = "^0.19.0"
python-multipart = "^0.0.6"
websockets = "^12.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.23.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

- [ ] **Step 2: 创建 requirements.txt**

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.25
aiosqlite==0.19.0
python-multipart==0.0.6
websockets==12.0
python-dotenv==1.0.0
```

- [ ] **Step 3: 创建 app/__init__.py**

```python
"""夸夸Agent后端"""
__version__ = "0.1.0"
```

- [ ] **Step 4: 创建 app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, summary, chat, settings

app = FastAPI(title="夸夸Agent后端", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "electron://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["健康检查"])
app.include_router(summary.router, prefix="/api", tags=["每日总结"])
app.include_router(chat.router, prefix="/api", tags=["聊天"])
app.include_router(settings.router, prefix="/api", tags=["设置"])

@app.get("/")
def root():
    return {"message": "夸夸Agent后端运行中"}
```

- [ ] **Step 5: 提交**

```bash
cd backend
git init (if not already)
git add pyproject.toml requirements.txt app/__init__.py app/main.py
git commit -m "feat: 后端项目初始化，添加FastAPI入口"
```

---

### Task 2: 核心配置模块

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/exceptions.py`

- [ ] **Step 1: 创建 core/__init__.py**

```python
"""核心配置和异常"""
```

- [ ] **Step 2: 创建 core/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础
    app_name: str = "夸夸Agent"
    debug: bool = True

    # ActivityWatch API
    aw_server_url: str = "http://127.0.0.1:5600"
    aw_api_key: str = ""

    # 豆包 API (火山方舟)
    doubao_api_key: str = ""
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    doubao_model: str = "doubao-pro-32k"

    # 本地存储
    db_path: str = "kuakua.db"
    log_path: str = "logs"

    # 用户ID (单用户本地应用)
    user_id: str = "local_user"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: 创建 core/exceptions.py**

```python
class KuakuaException(Exception):
    """基础异常"""
    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AWNotRunningError(KuakuaException):
    """ActivityWatch未运行"""
    def __init__(self, message: str = "ActivityWatch服务未运行"):
        super().__init__(message, code="AW_NOT_RUNNING")


class LLMCallError(KuakuaException):
    """大模型调用失败"""
    def __init__(self, message: str = "AI服务调用失败"):
        super().__init__(message, code="LLM_ERROR")


class ConfigMissingError(KuakuaException):
    """配置缺失"""
    def __init__(self, message: str = "缺少必要配置"):
        super().__init__(message, code="CONFIG_MISSING")


class DataNotFoundError(KuakuaException):
    """数据不存在"""
    def __init__(self, message: str = "请求的数据不存在"):
        super().__init__(message, code="DATA_NOT_FOUND")
```

- [ ] **Step 4: 提交**

```bash
git add app/core/
git commit -m "feat: 添加核心配置和自定义异常模块"
```

---

### Task 3: 数据模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/schemas.py`
- Create: `backend/app/models/models.py`

- [ ] **Step 1: 创建 models/__init__.py**

```python
"""数据模型"""
from app.models.schemas import *
from app.models.models import *
```

- [ ] **Step 2: 创建 models/schemas.py (Pydantic请求/响应模型)**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ===== 健康检查 =====
class HealthResponse(BaseModel):
    status: str
    activitywatch: str
    storage: str


# ===== 每日总结 =====
class SummaryData(BaseModel):
    date: str
    total_hours: float = Field(description="总使用时长(小时)")
    work_hours: float = Field(description="工作时长(小时)")
    entertainment_hours: float = Field(description="娱乐时长(小时)")
    other_hours: float = Field(description="其他时长(小时)")
    top_apps: List[dict] = Field(default_factory=list, description="Top应用")
    focus_score: int = Field(default=0, description="专注分数 0-100")
    praise_text: str = Field(default="", description="夸夸文本")
    suggestions: List[str] = Field(default_factory=list, description="建议列表")


class SummaryResponse(BaseModel):
    status: str  # success | pending | error
    data: Optional[SummaryData] = None
    message: Optional[str] = None


class SummaryRequest(BaseModel):
    date: Optional[str] = None  # 不传则默认今天


# ===== 聊天 =====
class ChatRequest(BaseModel):
    chat_id: str = Field(description="会话ID")
    message: str = Field(description="用户消息")
    user_context: Optional[dict] = Field(default=None, description="用户上下文数据")


class ChatResponse(BaseModel):
    chat_id: str
    reply: str
    history: List[dict] = Field(default_factory=list)


# ===== 设置 =====
class SettingsRequest(BaseModel):
    doubao_api_key: Optional[str] = None
    aw_server_url: Optional[str] = None
    data_masking: Optional[bool] = None


class SettingsResponse(BaseModel):
    doubao_api_key_set: bool
    aw_server_url: str
    data_masking: bool
```

- [ ] **Step 3: 创建 models/models.py (SQLAlchemy ORM模型)**

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Summary(Base):
    """每日总结缓存"""
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    date = Column(String(20), nullable=False)
    data = Column(Text, nullable=False)  # JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uix_user_date'),
    )


class ChatMessage(Base):
    """聊天记录"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user | assistant
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    """用户设置"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uix_user_key'),
    )
```

- [ ] **Step 4: 提交**

```bash
git add app/models/
git commit -m "feat: 添加Pydantic和SQLAlchemy数据模型"
```

---

### Task 4: 存储层

**Files:**
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/base.py`
- Create: `backend/app/storage/sqlite.py`
- Create: `backend/app/storage/cache.py`

- [ ] **Step 1: 创建 storage/__init__.py**

```python
"""存储层"""
from app.storage.base import StorageBase
from app.storage.sqlite import SQLiteStorage
from app.storage.cache import Cache

__all__ = ["StorageBase", "SQLiteStorage", "Cache"]
```

- [ ] **Step 2: 创建 storage/base.py**

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Any


class StorageBase(ABC):
    """存储抽象基类"""

    @abstractmethod
    async def save_summary(self, user_id: str, date: str, data: dict) -> None:
        """保存每日总结"""
        pass

    @abstractmethod
    async def get_summary(self, user_id: str, date: str) -> Optional[dict]:
        """获取每日总结"""
        pass

    @abstractmethod
    async def save_chat_message(self, chat_id: str, role: str, message: str) -> None:
        """保存聊天消息"""
        pass

    @abstractmethod
    async def get_chat_history(self, chat_id: str, limit: int = 10) -> List[dict]:
        """获取聊天历史"""
        pass

    @abstractmethod
    async def save_setting(self, user_id: str, key: str, value: str) -> None:
        """保存设置"""
        pass

    @abstractmethod
    async def get_setting(self, user_id: str, key: str) -> Optional[str]:
        """获取设置"""
        pass

    @abstractmethod
    async def delete_all_data(self) -> None:
        """删除所有数据"""
        pass
```

- [ ] **Step 3: 创建 storage/sqlite.py**

```python
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import get_settings
from app.models.models import Base, Summary, ChatMessage, Setting
from app.storage.base import StorageBase

logger = logging.getLogger(__name__)


class SQLiteStorage(StorageBase):
    """SQLite存储实现"""

    def __init__(self):
        settings = get_settings()
        db_path = settings.db_path

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 异步引擎
        self.async_engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=settings.debug,
        )
        self.async_session = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """初始化数据库表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save_summary(self, user_id: str, date: str, data: dict) -> None:
        async with self.async_session() as session:
            # 检查是否已存在
            stmt = select(Summary).where(
                Summary.user_id == user_id,
                Summary.date == date
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.data = json.dumps(data, ensure_ascii=False)
            else:
                summary = Summary(
                    user_id=user_id,
                    date=date,
                    data=json.dumps(data, ensure_ascii=False)
                )
                session.add(summary)

            await session.commit()

    async def get_summary(self, user_id: str, date: str) -> Optional[dict]:
        async with self.async_session() as session:
            stmt = select(Summary).where(
                Summary.user_id == user_id,
                Summary.date == date
            )
            result = await session.execute(stmt)
            summary = result.scalar_one_or_none()

            if summary:
                return json.loads(summary.data)
            return None

    async def save_chat_message(self, chat_id: str, role: str, message: str) -> None:
        async with self.async_session() as session:
            msg = ChatMessage(
                chat_id=chat_id,
                role=role,
                message=message
            )
            session.add(msg)
            await session.commit()

    async def get_chat_history(self, chat_id: str, limit: int = 10) -> List[dict]:
        async with self.async_session() as session:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.chat_id == chat_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()

            # 返回最近的消息（按时间正序）
            return [
                {
                    "role": msg.role,
                    "message": msg.message,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]

    async def save_setting(self, user_id: str, key: str, value: str) -> None:
        async with self.async_session() as session:
            stmt = select(Setting).where(
                Setting.user_id == user_id,
                Setting.key == key
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = value
            else:
                setting = Setting(user_id=user_id, key=key, value=value)
                session.add(setting)

            await session.commit()

    async def get_setting(self, user_id: str, key: str) -> Optional[str]:
        async with self.async_session() as session:
            stmt = select(Setting).where(
                Setting.user_id == user_id,
                Setting.key == key
            )
            result = await session.execute(stmt)
            setting = result.scalar_one_or_none()
            return setting.value if setting else None

    async def delete_all_data(self) -> None:
        async with self.async_session() as session:
            await session.execute(delete(Summary))
            await session.execute(delete(ChatMessage))
            await session.commit()
```

- [ ] **Step 4: 创建 storage/cache.py**

```python
import logging
from typing import Optional, Dict
from datetime import datetime

from app.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class Cache:
    """缓存层 - 内存缓存 + SQLite持久化"""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage
        # 内存缓存: {(user_id, date): data}
        self._memory_cache: Dict[tuple, dict] = {}

    async def get_cached_summary(self, user_id: str, date: str) -> Optional[dict]:
        """获取缓存的总结"""
        key = (user_id, date)

        # 先查内存
        if key in self._memory_cache:
            logger.debug(f"缓存命中(内存): {key}")
            return self._memory_cache[key]

        # 查数据库
        data = await self.storage.get_summary(user_id, date)
        if data:
            self._memory_cache[key] = data
            logger.debug(f"缓存命中(DB): {key}")

        return data

    async def set_cached_summary(self, user_id: str, date: str, data: dict) -> None:
        """设置总结缓存"""
        key = (user_id, date)
        self._memory_cache[key] = data
        await self.storage.save_summary(user_id, date, data)
        logger.debug(f"缓存已更新: {key}")

    def clear_memory_cache(self) -> None:
        """清空内存缓存"""
        self._memory_cache.clear()
```

- [ ] **Step 5: 更新 app/main.py 添加启动初始化**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.storage.sqlite import SQLiteStorage
from app.storage.cache import Cache

# 全局存储实例
storage: SQLiteStorage = None
cache: Cache = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global storage, cache
    storage = SQLiteStorage()
    await storage.init_db()
    cache = Cache(storage)
    yield


app = FastAPI(title="夸夸Agent后端", lifespan=lifespan)
```

- [ ] **Step 6: 提交**

```bash
git add app/storage/
git commit -m "feat: 添加存储层 (SQLite + 缓存)"
```

---

## Phase 2: 后端服务层

### Task 5: 数据采集器 (ActivityWatch)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/collector_base.py`
- Create: `backend/app/services/activitywatch.py`

- [ ] **Step 1: 创建 services/__init__.py**

```python
"""服务层"""
```

- [ ] **Step 2: 创建 services/collector_base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import date


class DataCollector(ABC):
    """数据采集器抽象基类"""

    @abstractmethod
    async def get_daily_data(self, target_date: date) -> Dict:
        """
        获取指定日期的电脑使用数据
        返回格式:
        {
            "date": "2026-04-23",
            "total_hours": 8.5,
            "apps": [
                {"name": "VSCode", "duration": 3600, "category": "work"},
                ...
            ],
            "categories": {
                "work": 5.0,
                "entertainment": 2.0,
                "other": 1.5
            }
        }
        """
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """检查数据源是否可用"""
        pass

    def categorize_app(self, app_name: str) -> str:
        """根据应用名判断类别"""
        work_keywords = ["code", "idea", "webstorm", "pycharm", "vscode",
                         "word", "excel", "ppt", "pdf", "notion", "obsidian"]
        entertainment_keywords = ["youtube", "netflix", "game", "steam",
                                   "netease", "music", "spotify", "bili"]

        app_lower = app_name.lower()
        for kw in work_keywords:
            if kw in app_lower:
                return "work"
        for kw in entertainment_keywords:
            if kw in app_lower:
                return "entertainment"
        return "other"
```

- [ ] **Step 3: 创建 services/activitywatch.py**

```python
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List

import httpx

from app.core.config import get_settings
from app.core.exceptions import AWNotRunningError
from app.services.collector_base import DataCollector

logger = logging.getLogger(__name__)


class ActivityWatchCollector(DataCollector):
    """ActivityWatch数据采集器"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.aw_server_url.rstrip("/")

    async def check_connection(self) -> bool:
        """检查ActivityWatch是否运行"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/0")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"ActivityWatch连接检查失败: {e}")
            return False

    async def get_daily_data(self, target_date: date) -> Dict:
        """获取指定日期的数据"""
        if not await self.check_connection():
            raise AWNotRunningError("ActivityWatch服务未运行，请先启动ActivityWatch")

        # ActivityWatch API 获取当日活动
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        buckets = await self._get_buckets()
        events = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for bucket_id in buckets:
                url = f"{self.base_url}/api/0/buckets/{bucket_id}/events"
                params = {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                }
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        events.extend(response.json())
                except Exception as e:
                    logger.warning(f"获取bucket {bucket_id} 失败: {e}")

        # 按应用聚合
        app_durations: Dict[str, int] = {}
        for event in events:
            if "data" in event and "app" in event.get("data", {}):
                app_name = event["data"]["app"]
                duration = event.get("duration", 0)
                if duration and duration > 0:
                    app_durations[app_name] = app_durations.get(app_name, 0) + duration

        # 转换为小时
        total_seconds = sum(app_durations.values())
        total_hours = total_seconds / 3600

        # 分类统计
        categories = {"work": 0.0, "entertainment": 0.0, "other": 0.0}
        apps = []

        for app_name, seconds in app_durations.items():
            hours = seconds / 3600
            category = self.categorize_app(app_name)
            categories[category] += hours
            apps.append({
                "name": app_name,
                "duration": hours,
                "category": category
            })

        # 按使用时长排序
        apps.sort(key=lambda x: x["duration"], reverse=True)

        return {
            "date": target_date.isoformat(),
            "total_hours": round(total_hours, 2),
            "apps": apps,
            "categories": {k: round(v, 2) for k, v in categories.items()}
        }

    async def _get_buckets(self) -> List[str]:
        """获取ActivityWatch的buckets"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/0/buckets")
                if response.status_code == 200:
                    buckets = response.json()
                    return [b["id"] for b in buckets if b.get("type") == "app"]
        except Exception as e:
            logger.error(f"获取buckets失败: {e}")
        return []
```

- [ ] **Step 4: 提交**

```bash
git add app/services/
git commit -m "feat: 添加ActivityWatch数据采集器"
```

---

### Task 6: 数据分析器

**Files:**
- Create: `backend/app/services/analyzer.py`

- [ ] **Step 1: 创建 services/analyzer.py**

```python
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class Analyzer:
    """数据分析器 - 分析电脑使用数据生成结构化摘要"""

    def __init__(self):
        pass

    def analyze(self, raw_data: Dict) -> Dict:
        """
        分析原始数据，生成结构化摘要

        raw_data格式:
        {
            "date": "2026-04-23",
            "total_hours": 8.5,
            "apps": [...],
            "categories": {"work": 5.0, "entertainment": 2.0, "other": 1.5}
        }
        """
        total_hours = raw_data.get("total_hours", 0)
        categories = raw_data.get("categories", {})
        apps = raw_data.get("apps", [])

        # 计算专注分数 (0-100)
        focus_score = self._calculate_focus_score(total_hours, categories)

        # 提取Top应用
        top_apps = apps[:5] if len(apps) > 5 else apps

        # 生成建议
        suggestions = self._generate_suggestions(total_hours, categories, apps)

        return {
            "date": raw_data.get("date"),
            "total_hours": total_hours,
            "work_hours": categories.get("work", 0),
            "entertainment_hours": categories.get("entertainment", 0),
            "other_hours": categories.get("other", 0),
            "top_apps": top_apps,
            "focus_score": focus_score,
            "suggestions": suggestions
        }

    def _calculate_focus_score(self, total_hours: float, categories: Dict) -> int:
        """计算专注分数"""
        if total_hours < 1:
            return 20

        work_ratio = categories.get("work", 0) / total_hours if total_hours > 0 else 0

        # 基础分数
        score = int(work_ratio * 100)

        # 奖励: 总时长适中 (4-10小时)
        if 4 <= total_hours <= 10:
            score = min(100, score + 10)

        # 惩罚: 总时长过长 (>12小时) 或过短 (<2小时)
        if total_hours > 12:
            score = max(0, score - 20)
        if total_hours < 2:
            score = max(0, score - 30)

        return max(0, min(100, score))

    def _generate_suggestions(self, total_hours: float,
                               categories: Dict,
                               apps: List[Dict]) -> List[str]:
        """生成建议"""
        suggestions = []

        # 久坐建议
        if total_hours > 6:
            suggestions.append("今天使用电脑时间较长，记得每40-50分钟站起来活动一下，保护眼睛和颈椎～")

        # 工作/娱乐平衡
        entertainment_ratio = categories.get("entertainment", 0) / total_hours if total_hours > 0 else 0
        if entertainment_ratio > 0.5:
            suggestions.append("娱乐时间占比有点高，明天可以试试把娱乐时间控制在总时长的30%以内哦")
        elif entertainment_ratio < 0.2 and total_hours > 4:
            suggestions.append("今天几乎没有摸鱼！专注力很强，不过也要注意适当休息")

        # 碎片化时间检测
        if len(apps) > 15:
            suggestions.append("今天切换了很多应用，可能是碎片化时间比较多，试试用番茄工作法提升专注")

        # 特定应用建议
        app_names = [a["name"].lower() for a in apps]
        if any("wechat" in n or "dingtalk" in n for n in app_names):
            if any("code" in n or "idea" in n for n in app_names):
                suggestions.append("同时开了通讯工具和开发环境，注意不要被消息打断思路哦")

        # 默认建议
        if not suggestions:
            suggestions.append("继续保持，今天的使用状态很健康！")

        return suggestions[:3]  # 最多3条建议

    def extract_highlights(self, raw_data: Dict) -> List[str]:
        """提取今日亮点（用于夸夸）"""
        highlights = []
        categories = raw_data.get("categories", {})
        apps = raw_data.get("apps", [])
        total_hours = raw_data.get("total_hours", 0)

        # 工作时长亮点
        work_hours = categories.get("work", 0)
        if work_hours > 6:
            highlights.append(f"今天工作了{work_hours:.1f}小时，真的很努力！")
        elif work_hours > 3:
            highlights.append(f"有效工作时长{work_hours:.1f}小时，给自己点个赞")

        # 专注亮点
        if apps:
            top_app = apps[0]
            if top_app.get("category") == "work" and top_app.get("duration", 0) > 2:
                highlights.append(f"在{top_app['name']}上专注了{top_app['duration']:.1f}小时，效率很高")

        # 应用切换亮点
        if len(apps) <= 10 and total_hours > 4:
            highlights.append("今天应用切换不多，说明注意力比较集中，做得好！")

        return highlights
```

- [ ] **Step 2: 提交**

```bash
git add app/services/analyzer.py
git commit -m "feat: 添加数据分析器"
```

---

### Task 7: LLM服务 (豆包API)

**Files:**
- Create: `backend/app/services/llm.py`

- [ ] **Step 1: 创建 services/llm.py**

```python
import logging
from typing import List, Dict, Optional

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMCallError, ConfigMissingError

logger = logging.getLogger(__name__)


class LLMService:
    """豆包API服务（OpenAI兼容格式）"""

    def __init__(self):
        self.settings = get_settings()

    def _check_config(self):
        """检查配置"""
        if not self.settings.doubao_api_key:
            raise ConfigMissingError("未配置豆包API密钥，请在设置页配置")

    async def generate_praise(self, summary_data: Dict, highlights: List[str]) -> str:
        """
        生成夸夸文本

        summary_data: 结构化总结数据
        highlights: 今日亮点列表
        """
        self._check_config()

        system_prompt = """你是一个温暖治愈的AI夸夸助手，专门根据用户真实的电脑使用数据来夸奖用户。

要求：
1. 夸奖必须基于用户真实数据，不编造
2. 语言温柔、真诚、不油腻
3. 突出用户今日的努力和闪光点
4. 适当提及具体应用和时间（如果数据支持）
5. 结尾可以给予正向鼓励和建议
6. 长度适中，3-5句话为宜"""

        user_prompt = self._build_praise_prompt(summary_data, highlights)

        return await self._call_llm(system_prompt, user_prompt)

    async def chat(self, message: str, history: List[Dict],
                   user_context: Optional[Dict] = None) -> str:
        """
        聊天对话

        message: 用户消息
        history: 对话历史 [{"role": "user", "content": "..."}, ...]
        user_context: 用户上下文（当日行为数据）
        """
        self._check_config()

        system_prompt = """你是一个温暖的AI陪伴助手，擅长：
1. 倾听用户的倾诉和烦恼
2. 给予情绪支持和安慰
3. 在适当时候给予正向鼓励
4. 保持对话轻松、自然、有温度

注意：
- 不要过于说教或给出太多建议，用户可能只是需要倾诉
- 语言要温暖但不过度夸张
- 如果用户提到具体的烦恼，可以适当回应"""

        # 拼接上下文
        user_prompt = message
        if user_context:
            context_str = f"\n\n用户今日概况：\n- 总使用电脑: {user_context.get('total_hours', 0)}小时\n- 工作: {user_context.get('work_hours', 0)}小时\n- 娱乐: {user_context.get('entertainment_hours', 0)}小时"
            user_prompt = f"{context_str}\n\n用户说：{message}"

        return await self._call_llm(system_prompt, user_prompt, history)

    async def validate_api_key(self, api_key: str) -> bool:
        """验证API密钥是否有效"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.settings.doubao_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.settings.doubao_model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 10
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"API密钥验证失败: {e}")
            return False

    async def _call_llm(self, system_prompt: str, user_prompt: str,
                        history: List[Dict] = None) -> str:
        """调用LLM API"""
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史
        if history:
            for h in history[-10:]:  # 最多10条历史
                messages.append({
                    "role": h.get("role", "user"),
                    "content": h.get("message", h.get("content", ""))
                })

        messages.append({"role": "user", "content": user_prompt})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.doubao_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.doubao_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.settings.doubao_model,
                        "messages": messages,
                        "temperature": 0.8,
                        "max_tokens": 1000
                    }
                )

                if response.status_code != 200:
                    logger.error(f"LLM API错误: {response.status_code} - {response.text}")
                    raise LLMCallError(f"AI服务调用失败: {response.status_code}")

                result = response.json()
                return result["choices"][0]["message"]["content"]

        except LLMCallError:
            raise
        except Exception as e:
            logger.error(f"LLM调用异常: {e}")
            raise LLMCallError(f"AI服务调用异常: {str(e)}")

    def _build_praise_prompt(self, summary_data: Dict, highlights: List[str]) -> str:
        """构建夸夸prompt"""
        date = summary_data.get("date", "今天")
        total = summary_data.get("total_hours", 0)
        work = summary_data.get("work_hours", 0)
        entertainment = summary_data.get("entertainment_hours", 0)
        focus_score = summary_data.get("focus_score", 0)
        suggestions = summary_data.get("suggestions", [])

        prompt = f"""请根据以下用户今日电脑使用数据，写一段温暖的夸夸：

日期：{date}
- 总使用时长：{total}小时
- 工作时长：{work}小时
- 娱乐时长：{entertainment}小时
- 专注分数：{focus_score}/100

今日亮点：
{chr(10).join(f"- {h}" for h in highlights) if highlights else "- 今天也有在使用电脑"}

请写一段温暖真诚的夸夸，语言要自然、不油腻，突出用户的努力和闪光点。"""

        return prompt
```

- [ ] **Step 2: 提交**

```bash
git add app/services/llm.py
git commit -m "feat: 添加豆包LLM服务"
```

---

### Task 8: 路由层

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/health.py`
- Create: `backend/app/routers/summary.py`
- Create: `backend/app/routers/chat.py`
- Create: `backend/app/routers/settings.py`

- [ ] **Step 1: 创建 routers/__init__.py**

```python
"""路由层"""
from app.routers import health, summary, chat, settings
```

- [ ] **Step 2: 创建 routers/health.py**

```python
from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.main import storage

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    # 检查ActivityWatch
    from app.services.activitywatch import ActivityWatchCollector
    collector = ActivityWatchCollector()
    aw_status = "connected" if await collector.check_connection() else "disconnected"

    # 检查存储
    storage_status = "ok"
    try:
        await storage.storage.get_summary("test", "1970-01-01")
    except Exception:
        storage_status = "error"

    return HealthResponse(
        status="ok" if aw_status == "connected" and storage_status == "ok" else "degraded",
        activitywatch=aw_status,
        storage=storage_status
    )
```

- [ ] **Step 3: 创建 routers/summary.py**

```python
import logging
from datetime import date
from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect
from websockets import broadcast

from app.models.schemas import SummaryResponse, SummaryData
from app.main import storage, cache
from app.services.activitywatch import ActivityWatchCollector
from app.services.analyzer import Analyzer
from app.services.llm import LLMService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket连接管理
active_connections: dict = {}


async def generate_summary_task(user_id: str, target_date: date, websocket: WebSocket = None):
    """异步生成总结任务"""
    try:
        # 1. 获取原始数据
        collector = ActivityWatchCollector()
        raw_data = await collector.get_daily_data(target_date)

        # 2. 分析数据
        analyzer = Analyzer()
        analyzed_data = analyzer.analyze(raw_data)

        # 3. 提取亮点
        highlights = analyzer.extract_highlights(raw_data)

        # 4. 生成夸夸
        llm = LLMService()
        try:
            praise_text = await llm.generate_praise(analyzed_data, highlights)
        except Exception as e:
            logger.warning(f"LLM调用失败，使用默认夸夸: {e}")
            praise_text = f"今天的你很棒！工作了{analyzed_data['work_hours']:.1f}小时，继续加油！"

        analyzed_data["praise_text"] = praise_text

        # 5. 保存到缓存
        await cache.set_cached_summary(user_id, target_date.isoformat(), analyzed_data)

        # 6. 推送结果
        if websocket:
            await websocket.send_json({
                "status": "success",
                "data": analyzed_data
            })

    except Exception as e:
        logger.error(f"生成总结失败: {e}")
        error_msg = str(e)
        if websocket:
            await websocket.send_json({
                "status": "error",
                "message": error_msg
            })


@router.get("/summary/{date_str}", response_model=SummaryResponse)
async def get_summary(date_str: str, background_tasks: BackgroundTasks):
    """获取指定日期的总结"""
    settings = get_settings()
    user_id = settings.user_id

    # 解析日期
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return SummaryResponse(status="error", message="无效的日期格式")

    # 检查缓存
    cached = await cache.get_cached_summary(user_id, date_str)
    if cached:
        return SummaryResponse(status="success", data=SummaryData(**cached))

    # 无缓存，触发异步生成
    # 注意：这里直接等待结果（简化实现）
    collector = ActivityWatchCollector()
    try:
        raw_data = await collector.get_daily_data(target_date)
    except Exception as e:
        return SummaryResponse(status="error", message=str(e))

    analyzer = Analyzer()
    analyzed_data = analyzer.analyze(raw_data)
    highlights = analyzer.extract_highlights(raw_data)

    llm = LLMService()
    try:
        praise_text = await llm.generate_praise(analyzed_data, highlights)
    except Exception as e:
        logger.warning(f"LLM调用失败: {e}")
        praise_text = f"今天的你很棒！工作了{analyzed_data['work_hours']:.1f}小时，继续加油！"

    analyzed_data["praise_text"] = praise_text

    # 保存缓存
    await cache.set_cached_summary(user_id, date_str, analyzed_data)

    return SummaryResponse(status="success", data=SummaryData(**analyzed_data))


@router.get("/summary/today")
async def get_today_summary():
    """获取今日总结"""
    return await get_summary(date.today().isoformat())
```

- [ ] **Step 4: 创建 routers/chat.py**

```python
from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.main import storage
from app.services.llm import LLMService
from app.core.exceptions import ConfigMissingError, LLMCallError
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    user_id = "local_user"

    # 获取聊天历史
    history = await storage.get_chat_history(request.chat_id, limit=10)

    # 获取用户上下文（可选）
    user_context = None
    if request.user_context:
        user_context = request.user_context

    # 调用LLM
    llm = LLMService()
    try:
        reply = await llm.chat(
            message=request.message,
            history=history,
            user_context=user_context
        )
    except ConfigMissingError:
        return ChatResponse(
            chat_id=request.chat_id,
            reply="请先在设置中配置豆包API密钥哦～",
            history=history
        )
    except LLMCallError as e:
        logger.error(f"聊天LLM调用失败: {e}")
        return ChatResponse(
            chat_id=request.chat_id,
            reply="抱歉，AI服务暂时不可用，请稍后再试～",
            history=history
        )

    # 保存对话
    await storage.save_chat_message(request.chat_id, "user", request.message)
    await storage.save_chat_message(request.chat_id, "assistant", reply)

    # 更新history
    history.append({"role": "user", "message": request.message})
    history.append({"role": "assistant", "message": reply})

    return ChatResponse(
        chat_id=request.chat_id,
        reply=reply,
        history=history[-10:]  # 返回最近10条
    )
```

- [ ] **Step 5: 创建 routers/settings.py**

```python
from fastapi import APIRouter, HTTPException

from app.models.schemas import SettingsRequest, SettingsResponse
from app.main import storage
from app.services.llm import LLMService
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """获取设置"""
    settings = get_settings()
    user_id = settings.user_id

    doubao_key = await storage.get_setting(user_id, "doubao_api_key")
    aw_url = await storage.get_setting(user_id, "aw_server_url") or settings.aw_server_url
    masking = await storage.get_setting(user_id, "data_masking") or "false"

    return SettingsResponse(
        doubao_api_key_set=bool(doubao_key),
        aw_server_url=aw_url,
        data_masking=masking.lower() == "true"
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsRequest):
    """更新设置"""
    settings = get_settings()
    user_id = settings.user_id

    if request.doubao_api_key is not None:
        # 验证API key
        llm = LLMService()
        valid = await llm.validate_api_key(request.doubao_api_key)
        if not valid:
            raise HTTPException(status_code=400, detail="豆包API密钥无效")
        await storage.save_setting(user_id, "doubao_api_key", request.doubao_api_key)

    if request.aw_server_url is not None:
        await storage.save_setting(user_id, "aw_server_url", request.aw_server_url)

    if request.data_masking is not None:
        await storage.save_setting(user_id, "data_masking", str(request.data_masking))

    return await get_settings()


@router.delete("/settings/data")
async def delete_all_data():
    """删除所有数据"""
    await storage.delete_all_data()
    return {"message": "所有数据已删除"}
```

- [ ] **Step 6: 提交**

```bash
git add app/routers/
git commit -m "feat: 添加所有路由 (health, summary, chat, settings)"
```

---

## Phase 3: 前端项目初始化

### Task 9: Electron + Vue3 项目初始化

**Files:**
- Create: `electron/package.json`
- Create: `electron/vite.config.ts`
- Create: `electron/tsconfig.json`
- Create: `electron/src/main/index.ts`
- Create: `electron/src/preload/index.ts`
- Create: `electron/src/renderer/index.html`
- Create: `electron/src/renderer/main.ts`
- Create: `electron/src/renderer/App.vue`

- [ ] **Step 1: 创建 electron/package.json**

```json
{
  "name": "kuakua-agent",
  "version": "0.1.0",
  "description": "专属行为感知AI夸夸Agent",
  "main": "dist/main/index.js",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "electron:dev": "concurrently \"vite\" \"electron .\"",
    "electron:build": "vite build && electron-builder"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "chart.js": "^4.4.0",
    "vue-chartjs": "^5.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.0",
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0",
    "concurrently": "^8.2.0",
    "@types/node": "^20.10.0"
  },
  "build": {
    "appId": "com.kuakua.agent",
    "productName": "夸夸Agent",
    "directories": {
      "output": "release"
    },
    "files": [
      "dist/**/*"
    ],
    "win": {
      "target": "nsis",
      "icon": "public/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
```

- [ ] **Step 2: 创建 electron/vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  base: './',
  root: 'src/renderer',
  build: {
    outDir: '../../dist/renderer',
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src/renderer'),
    },
  },
  server: {
    port: 5173,
  },
})
```

- [ ] **Step 3: 创建 electron/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/renderer/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: 创建 electron/src/main/index.ts (Electron主进程)**

```typescript
import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'

let mainWindow: BrowserWindow | null = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    title: '夸夸Agent',
  })

  // 开发模式加载vite dev server
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

// IPC示例
ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})
```

- [ ] **Step 5: 创建 electron/src/preload/index.ts**

```typescript
import { contextBridge, ipcRenderer } from 'electron'

// 暴露给渲染进程的API
contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  // 后续可以添加更多IPC调用
})

// 类型声明
declare global {
  interface Window {
    electronAPI: {
      getAppVersion: () => Promise<string>
    }
  }
}
```

- [ ] **Step 6: 创建 electron/src/renderer/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>夸夸Agent</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 7: 创建 electron/src/renderer/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
```

- [ ] **Step 8: 创建 electron/src/renderer/App.vue**

```vue
<template>
  <div id="app">
    <nav class="nav">
      <router-link to="/">每日夸夸</router-link>
      <router-link to="/chat">聊天陪伴</router-link>
      <router-link to="/settings">设置</router-link>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav {
  display: flex;
  gap: 20px;
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.nav a {
  text-decoration: none;
  color: #666;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav a:hover,
.nav a.router-link-active {
  background: #e8f4ff;
  color: #1890ff;
}

.main-content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
```

- [ ] **Step 9: 创建 electron/src/renderer/router/index.ts**

```typescript
import { createRouter, createWebHashHistory } from 'vue-router'
import DailySummary from '@/views/DailySummary.vue'
import ChatCompanion from '@/views/ChatCompanion.vue'
import Settings from '@/views/Settings.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: DailySummary },
    { path: '/chat', component: ChatCompanion },
    { path: '/settings', component: Settings },
  ],
})

export default router
```

- [ ] **Step 10: 提交**

```bash
cd electron
git init
git add package.json vite.config.ts tsconfig.json src/
git commit -m "feat: Electron + Vue3项目初始化"
```

---

## Phase 4: 前端页面和组件

### Task 10: API层和Pinia Store

**Files:**
- Create: `electron/src/renderer/api/index.ts`
- Create: `electron/src/renderer/store/summary.ts`
- Create: `electron/src/renderer/store/chat.ts`

- [ ] **Step 1: 创建 electron/src/renderer/api/index.ts**

```typescript
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// 健康检查
export const healthCheck = () => api.get('/health')

// 每日总结
export const getSummary = (date: string) => api.get(`/summary/${date}`)
export const getTodaySummary = () => api.get('/summary/today')

// 聊天
export const sendChat = (data: { chat_id: string; message: string; user_context?: any }) =>
  api.post('/chat', data)

// 设置
export const getSettings = () => api.get('/settings')
export const updateSettings = (data: any) => api.put('/settings', data)
export const deleteAllData = () => api.delete('/settings/data')

export default api
```

- [ ] **Step 2: 创建 electron/src/renderer/store/summary.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTodaySummary, getSummary } from '@/api'

export interface SummaryData {
  date: string
  total_hours: number
  work_hours: number
  entertainment_hours: number
  other_hours: number
  top_apps: Array<{ name: string; duration: number; category: string }>
  focus_score: number
  praise_text: string
  suggestions: string[]
}

export const useSummaryStore = defineStore('summary', () => {
  const summary = ref<SummaryData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTodaySummary() {
    loading.value = true
    error.value = null
    try {
      const response = await getTodaySummary()
      if (response.data.status === 'success' && response.data.data) {
        summary.value = response.data.data
      } else {
        error.value = response.data.message || '获取总结失败'
      }
    } catch (e: any) {
      error.value = e.message || '网络错误'
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(date: string) {
    loading.value = true
    error.value = null
    try {
      const response = await getSummary(date)
      if (response.data.status === 'success' && response.data.data) {
        summary.value = response.data.data
      } else {
        error.value = response.data.message || '获取总结失败'
      }
    } catch (e: any) {
      error.value = e.message || '网络错误'
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, error, fetchTodaySummary, fetchSummary }
})
```

- [ ] **Step 3: 创建 electron/src/renderer/store/chat.ts**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendChat } from '@/api'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const chatId = ref(`chat_${Date.now()}`)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const groupedMessages = computed(() => {
    const groups: { date: string; messages: ChatMessage[] }[] = []
    let currentDate = ''

    for (const msg of messages.value) {
      const msgDate = msg.timestamp.toDateString()
      if (msgDate !== currentDate) {
        currentDate = msgDate
        groups.push({ date: msgDate, messages: [] })
      }
      groups[groups.length - 1].messages.push(msg)
    }

    return groups
  })

  async function sendMessage(content: string, userContext?: any) {
    if (!content.trim()) return

    // 添加用户消息
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date(),
    })

    loading.value = true
    error.value = null

    try {
      const response = await sendChat({
        chat_id: chatId.value,
        message: content,
        user_context: userContext,
      })

      // 添加AI回复
      messages.value.push({
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date(),
      })
    } catch (e: any) {
      error.value = e.message || '发送失败'
    } finally {
      loading.value = false
    }
  }

  function resetChat() {
    messages.value = []
    chatId.value = `chat_${Date.now()}`
  }

  return { messages, chatId, loading, error, groupedMessages, sendMessage, resetChat }
})
```

- [ ] **Step 4: 提交**

```bash
git add src/renderer/api/ src/renderer/store/
git commit -m "feat: 前端API层和Pinia Store"
```

---

### Task 11: 视图组件

**Files:**
- Create: `electron/src/renderer/views/DailySummary.vue`
- Create: `electron/src/renderer/views/ChatCompanion.vue`
- Create: `electron/src/renderer/views/Settings.vue`

- [ ] **Step 1: 创建 electron/src/renderer/views/DailySummary.vue**

```vue
<template>
  <div class="daily-summary">
    <h1>今日夸夸</h1>

    <div v-if="loading" class="loading">
      <p>正在生成今日夸夸～</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchSummary">重试</button>
    </div>

    <div v-else-if="summary" class="summary-content">
      <SummaryCard :summary="summary" />

      <div class="charts">
        <TimePieChart :data="summary" />
      </div>

      <div class="apps-list">
        <h3>今日应用</h3>
        <div class="app-item" v-for="app in summary.top_apps" :key="app.name">
          <span class="app-name">{{ app.name }}</span>
          <span class="app-duration">{{ app.duration.toFixed(1) }}h</span>
          <span class="app-category" :class="app.category">{{ app.category }}</span>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无数据，请确保ActivityWatch正在运行</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useSummaryStore } from '@/store/summary'
import SummaryCard from '@/components/SummaryCard.vue'
import TimePieChart from '@/components/TimePieChart.vue'

const store = useSummaryStore()

onMounted(() => {
  store.fetchTodaySummary()
})

function fetchSummary() {
  store.fetchTodaySummary()
}
</script>

<style scoped>
.daily-summary {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
}

.loading {
  color: #666;
}

.error {
  color: #ff4d4f;
}

button {
  margin-top: 16px;
  padding: 8px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.charts {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
}

.apps-list {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
}

.apps-list h3 {
  margin-bottom: 16px;
}

.app-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.app-item:last-child {
  border-bottom: none;
}

.app-name {
  flex: 1;
}

.app-duration {
  color: #666;
  margin-right: 12px;
}

.app-category {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.app-category.work {
  background: #e6f7ff;
  color: #1890ff;
}

.app-category.entertainment {
  background: #fff7e6;
  color: #fa8c16;
}

.app-category.other {
  background: #f5f5f5;
  color: #999;
}
</style>
```

- [ ] **Step 2: 创建 electron/src/renderer/views/ChatCompanion.vue**

```vue
<template>
  <div class="chat-companion">
    <h1>聊天陪伴</h1>

    <div class="chat-container">
      <div class="messages" ref="messagesRef">
        <div v-if="store.messages.length === 0" class="empty-messages">
          <p>有什么想聊的吗？我在这里陪你～</p>
        </div>

        <div
          v-for="(msg, index) in store.messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="bubble">{{ msg.content }}</div>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputMessage"
          placeholder="说点什么吧..."
          @keydown.enter.exact.prevent="sendMessage"
          rows="2"
        ></textarea>
        <button @click="sendMessage" :disabled="store.loading">
          {{ store.loading ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

const store = useChatStore()
const summaryStore = useSummaryStore()
const inputMessage = ref('')
const messagesRef = ref<HTMLElement | null>(null)

async function sendMessage() {
  const msg = inputMessage.value.trim()
  if (!msg) return

  inputMessage.value = ''

  // 获取用户上下文（如果有今日总结的话）
  const context = summaryStore.summary ? {
    total_hours: summaryStore.summary.total_hours,
    work_hours: summaryStore.summary.work_hours,
    entertainment_hours: summaryStore.summary.entertainment_hours,
  } : undefined

  await store.sendMessage(msg, context)

  // 滚动到底部
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-companion {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

h1 {
  text-align: center;
  margin-bottom: 24px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-messages {
  text-align: center;
  color: #999;
  padding: 40px;
}

.message {
  display: flex;
  margin-bottom: 16px;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
}

.message.user .bubble {
  background: #1890ff;
  color: #fff;
}

.message.assistant .bubble {
  background: #f5f5f5;
  color: #333;
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  resize: none;
  font-size: 14px;
}

textarea:focus {
  outline: none;
  border-color: #1890ff;
}

button {
  padding: 8px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 3: 创建 electron/src/renderer/views/Settings.vue**

```vue
<template>
  <div class="settings">
    <h1>设置</h1>

    <div class="settings-form">
      <div class="form-item">
        <label>豆包API密钥</label>
        <input
          type="password"
          v-model="settings.doubao_api_key"
          placeholder="请输入API密钥"
        />
        <span class="hint">用于调用AI生成夸夸和聊天</span>
      </div>

      <div class="form-item">
        <label>ActivityWatch地址</label>
        <input
          type="text"
          v-model="settings.aw_server_url"
          placeholder="http://127.0.0.1:5600"
        />
        <span class="hint">ActivityWatch服务的地址</span>
      </div>

      <div class="form-item">
        <label>
          <input type="checkbox" v-model="settings.data_masking" />
          启用数据脱敏
        </label>
        <span class="hint">隐藏具体应用名称，保护隐私</span>
      </div>

      <div class="form-actions">
        <button @click="saveSettings" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>

      <div v-if="saveMessage" class="save-message" :class="saveSuccess ? 'success' : 'error'">
        {{ saveMessage }}
      </div>
    </div>

    <div class="danger-zone">
      <h3>危险区域</h3>
      <button class="danger-btn" @click="confirmDelete">
        删除所有数据
      </button>
      <span class="hint">删除后无法恢复</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings, deleteAllData } from '@/api'

const settings = ref({
  doubao_api_key: '',
  aw_server_url: 'http://127.0.0.1:5600',
  data_masking: false,
})

const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

onMounted(async () => {
  try {
    const response = await getSettings()
    const data = response.data
    settings.value.aw_server_url = data.aw_server_url
    settings.value.data_masking = data.data_masking
    // 不显示已设置的密钥
    if (data.doubao_api_key_set) {
      settings.value.doubao_api_key = '********'
    }
  } catch (e) {
    console.error('获取设置失败', e)
  }
})

async function saveSettings() {
  saving.value = true
  saveMessage.value = ''

  try {
    const payload: any = {
      aw_server_url: settings.value.aw_server_url,
      data_masking: settings.value.data_masking,
    }

    // 如果不是********，才更新API密钥
    if (settings.value.doubao_api_key && settings.value.doubao_api_key !== '********') {
      payload.doubao_api_key = settings.value.doubao_api_key
    }

    await updateSettings(payload)
    saveSuccess.value = true
    saveMessage.value = '设置保存成功'

    if (settings.value.doubao_api_key === '********') {
      settings.value.doubao_api_key = ''
    }
  } catch (e: any) {
    saveSuccess.value = false
    saveMessage.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!confirm('确定要删除所有数据吗？此操作不可恢复。')) {
    return
  }

  try {
    await deleteAllData()
    alert('所有数据已删除')
  } catch (e) {
    alert('删除失败')
  }
}
</script>

<style scoped>
.settings {
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 32px;
}

.settings-form {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
}

.form-item {
  margin-bottom: 24px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: #1890ff;
}

.hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.form-actions {
  margin-top: 32px;
}

button {
  padding: 10px 32px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.save-message {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.save-message.success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.save-message.error {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.danger-zone {
  margin-top: 48px;
  padding: 24px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #ffccc7;
}

.danger-zone h3 {
  color: #ff4d4f;
  margin-bottom: 16px;
}

.danger-btn {
  background: #ff4d4f;
}

.danger-btn:hover {
  background: #ff7875;
}

.danger-zone .hint {
  margin-left: 12px;
}
</style>
```

- [ ] **Step 4: 提交**

```bash
git add src/renderer/views/
git commit -m "feat: 添加前端视图组件 (DailySummary, ChatCompanion, Settings)"
```

---

### Task 12: 通用组件

**Files:**
- Create: `electron/src/renderer/components/SummaryCard.vue`
- Create: `electron/src/renderer/components/TimePieChart.vue`
- Create: `electron/src/renderer/components/ChatBubble.vue`

- [ ] **Step 1: 创建 electron/src/renderer/components/SummaryCard.vue**

```vue
<template>
  <div class="summary-card">
    <div class="praise-section">
      <div class="praise-icon">✨</div>
      <p class="praise-text">{{ summary.praise_text }}</p>
    </div>

    <div class="stats-section">
      <div class="stat-item">
        <div class="stat-value">{{ summary.total_hours }}</div>
        <div class="stat-label">总时长(h)</div>
      </div>
      <div class="stat-item work">
        <div class="stat-value">{{ summary.work_hours }}</div>
        <div class="stat-label">工作(h)</div>
      </div>
      <div class="stat-item entertainment">
        <div class="stat-value">{{ summary.entertainment_hours }}</div>
        <div class="stat-label">娱乐(h)</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ summary.focus_score }}</div>
        <div class="stat-label">专注分</div>
      </div>
    </div>

    <div class="suggestions-section" v-if="summary.suggestions?.length">
      <h4>💡 建议</h4>
      <ul>
        <li v-for="(suggestion, index) in summary.suggestions" :key="index">
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SummaryData } from '@/store/summary'

defineProps<{
  summary: SummaryData
}>()
</script>

<style scoped>
.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.praise-section {
  text-align: center;
  margin-bottom: 32px;
}

.praise-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.praise-text {
  font-size: 20px;
  line-height: 1.6;
  font-weight: 500;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.2);
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 4px;
}

.suggestions-section {
  background: rgba(255, 255, 255, 0.15);
  padding: 20px;
  border-radius: 12px;
}

.suggestions-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
}

.suggestions-section ul {
  list-style: none;
  padding: 0;
}

.suggestions-section li {
  padding: 8px 0;
  font-size: 14px;
  opacity: 0.95;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.suggestions-section li:last-child {
  border-bottom: none;
}
</style>
```

- [ ] **Step 2: 创建 electron/src/renderer/components/TimePieChart.vue**

```vue
<template>
  <div class="time-pie-chart">
    <h3>时间分布</h3>
    <div class="chart-container">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { SummaryData } from '@/store/summary'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  data: SummaryData
}>()

const chartData = computed(() => ({
  labels: ['工作', '娱乐', '其他'],
  datasets: [
    {
      data: [
        props.data.work_hours,
        props.data.entertainment_hours,
        props.data.other_hours,
      ],
      backgroundColor: ['#1890ff', '#fa8c16', '#999'],
      borderWidth: 0,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
  },
}
</script>

<style scoped>
.time-pie-chart h3 {
  margin-bottom: 16px;
}

.chart-container {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
```

- [ ] **Step 3: 创建 electron/src/renderer/components/ChatBubble.vue**

```vue
<template>
  <div class="chat-bubble" :class="role">
    <div class="avatar">{{ role === 'user' ? '🙂' : '🤖' }}</div>
    <div class="content">{{ content }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.chat-bubble.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
}

.user .content {
  background: #1890ff;
  color: #fff;
}

.assistant .content {
  background: #f5f5f5;
  color: #333;
}
</style>
```

- [ ] **Step 4: 提交**

```bash
git add src/renderer/components/
git commit -m "feat: 添加通用组件 (SummaryCard, TimePieChart, ChatBubble)"
```

---

## Phase 5: 工具函数和常量

### Task 13: 工具函数和常量

**Files:**
- Create: `electron/src/renderer/constants/index.ts`
- Create: `electron/src/renderer/utils/format.ts`
- Create: `electron/src/renderer/utils/error.ts`
- Create: `electron/src/renderer/hooks/useSummary.ts`
- Create: `electron/src/renderer/hooks/useChat.ts`

- [ ] **Step 1: 创建 constants/index.ts**

```typescript
// API配置
export const API_BASE_URL = 'http://localhost:8000/api'

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查后端服务是否启动',
  ACTIVITYWATCH_NOT_RUNNING: 'ActivityWatch未运行，请先启动',
  API_KEY_NOT_SET: '请先在设置中配置API密钥',
  UNKNOWN_ERROR: '发生未知错误，请稍后重试',
}

// 分类关键词
export const APP_CATEGORIES = {
  work: ['code', 'idea', 'webstorm', 'pycharm', 'vscode', 'word', 'excel', 'ppt', 'pdf', 'notion', 'obsidian'],
  entertainment: ['youtube', 'netflix', 'game', 'steam', 'netease', 'music', 'spotify', 'bili'],
}
```

- [ ] **Step 2: 创建 utils/format.ts**

```typescript
export function formatDuration(hours: number): string {
  if (hours < 1) {
    return `${Math.round(hours * 60)}分钟`
  }
  return `${hours.toFixed(1)}小时`
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })
}

export function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return '今天'
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  }
  return formatDate(dateStr)
}
```

- [ ] **Step 3: 创建 utils/error.ts**

```typescript
import { ERROR_MESSAGES } from '@/constants'

export function handleApiError(error: any): string {
  if (!error.response) {
    // 网络错误
    return ERROR_MESSAGES.NETWORK_ERROR
  }

  const status = error.response.status
  const data = error.response.data

  switch (status) {
    case 400:
      return data?.detail || '请求参数错误'
    case 401:
      return ERROR_MESSAGES.API_KEY_NOT_SET
    case 404:
      return ERROR_MESSAGES.ACTIVITYWATCH_NOT_RUNNING
    case 500:
      return ERROR_MESSAGES.UNKNOWN_ERROR
    default:
      return data?.detail || ERROR_MESSAGES.UNKNOWN_ERROR
  }
}

export function showError(message: string) {
  console.error(message)
  // 可以替换为更友好的错误提示UI
  alert(message)
}
```

- [ ] **Step 4: 创建 hooks/useSummary.ts**

```typescript
import { computed } from 'vue'
import { useSummaryStore, type SummaryData } from '@/store/summary'

export function useSummary() {
  const store = useSummaryStore()

  const formattedSummary = computed(() => {
    if (!store.summary) return null

    const s = store.summary
    return {
      ...s,
      totalHours: `${s.total_hours}小时`,
      workHours: `${s.work_hours}小时`,
      entertainmentHours: `${s.entertainment_hours}小时`,
      otherHours: `${s.other_hours}小时`,
      focusScore: `${s.focus_score}分`,
    }
  })

  const hasSummary = computed(() => !!store.summary)

  return {
    summary: store.summary,
    formattedSummary,
    loading: store.loading,
    error: store.error,
    hasSummary,
    fetchTodaySummary: store.fetchTodaySummary,
    fetchSummary: store.fetchSummary,
  }
}
```

- [ ] **Step 5: 创建 hooks/useChat.ts**

```typescript
import { computed } from 'vue'
import { useChatStore } from '@/store/chat'

export function useChat() {
  const store = useChatStore()

  const canSend = computed(() => !store.loading)

  const lastMessage = computed(() => {
    if (store.messages.length === 0) return null
    return store.messages[store.messages.length - 1]
  })

  return {
    messages: store.messages,
    groupedMessages: store.groupedMessages,
    chatId: store.chatId,
    loading: store.loading,
    error: store.error,
    canSend,
    lastMessage,
    sendMessage: store.sendMessage,
    resetChat: store.resetChat,
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add src/renderer/constants/ src/renderer/utils/ src/renderer/hooks/
git commit -m "feat: 添加工具函数和Hooks"
```

---

## Phase 6: 集成测试

### Task 14: 集成验证

- [ ] **Step 1: 验证后端启动**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 访问 http://localhost:8000/docs 查看API文档
```

- [ ] **Step 2: 验证前端启动**

```bash
cd electron
npm install
npm run dev
# 访问 http://localhost:5173
```

- [ ] **Step 3: 提交所有代码**

```bash
git add -A
git commit -m "feat: 完成夸夸Agent全部功能"
```

---

## 自检清单

- [ ] 设计文档已写入 `docs/superpowers/specs/`
- [ ] 所有Task都已完成并提交
- [ ] 后端 FastAPI 可正常启动
- [ ] 前端 Vue3 可正常启动
- [ ] API 端点可正常调用

---

## 执行方式选择

**Plan complete and saved to `docs/superpowers/plans/2026-04-23-kuakua-agent-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
