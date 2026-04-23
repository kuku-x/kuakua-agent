# 夸夸Agent桌面应用 设计规格文档

## 1. 概述

本软件基于开源项目 ActivityWatch 二次独立开发，搭建专属 AI 智能 Agent。能够自动记录用户电脑全天使用行为，结合大模型进行数据分析、每日总结、个性化暖心夸赞、时间管理建议，并附带情绪陪伴聊天功能，实现真实化、个性化、不空洞的 AI 陪伴与正向鼓励。

### 技术栈

- **前端**: Electron + Vue 3 + TypeScript
- **后端**: Python FastAPI
- **数据源**: ActivityWatch API（独立运行）
- **AI**: 豆包 API（火山方舟，OpenAI 兼容格式）
- **存储**: SQLite（本地持久化）
- **平台**: Windows

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户电脑 (Windows)                              │
│                                                                       │
│  ┌──────────────┐      ┌─────────────────────────────────────────┐  │
│  │ActivityWatch │      │           FastAPI Backend               │  │
│  │ aw-server    │◄────►│  ┌─────────┐  ┌─────────┐  ┌────────┐ │  │
│  │ (独立运行)    │      │  │Collector│  │ Analyzer│  │  LLM   │ │  │
│  └──────────────┘      │  └────┬────┘  └────┬────┘  └────┬───┘ │  │
│                         │       │            │            │     │  │
│                         │  ┌────▼────────────▼────────────▼───┐ │  │
│                         │  │         Storage (SQLite)        │ │  │
│                         │  │  - 每日总结缓存                    │ │  │
│                         │  │  - 聊天记录                        │ │  │
│                         │  │  - 用户配置                        │ │  │
│                         │  └───────────────────────────────────┘ │  │
│                         └─────────────────────────────────────────┘  │
│                                      │                                │
│                              ┌───────▼───────┐                       │
│                              │   豆包 API    │                       │
│                              │  (火山方舟)    │                       │
│                              └───────────────┘                       │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Electron + Vue3 UI                          │  │
│  │   - DailySummary (可视化图表 + 夸夸展示)                        │  │
│  │   - ChatCompanion (上下文记忆对话)                              │  │
│  │   - Settings (API配置 + 数据管理)                               │  │
│  │   - WebSocket 接收实时推送                                      │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 数据流向

1. ActivityWatch 后台服务监控采集电脑使用数据
2. FastAPI 后端定时/按需调用 ActivityWatch API 获取数据
3. FastAPI 后端调用豆包 API 生成夸夸内容
4. Electron + Vue3 桌面客户端展示结果、与用户交互

---

## 3. 目录结构

```
kuakua-agent/
├── electron/
│   ├── src/
│   │   ├── main/
│   │   │   └── index.ts          # Electron 主进程
│   │   ├── preload/
│   │   │   └── index.ts          # 预加载脚本（桥接IPC）
│   │   └── renderer/
│   │       ├── App.vue
│   │       ├── main.ts
│   │       ├── views/
│   │       │   ├── DailySummary.vue    # 每日总结页（含图表）
│   │       │   ├── ChatCompanion.vue   # 聊天陪伴页
│   │       │   └── Settings.vue       # 设置页
│   │       ├── components/
│   │       │   ├── SummaryCard.vue    # 夸夸卡片
│   │       │   ├── TimePieChart.vue    # 时间饼图
│   │       │   ├── TrendChart.vue      # 趋势图
│   │       │   └── ChatBubble.vue      # 聊天气泡
│   │       ├── store/
│   │       │   ├── summary.ts          # Pinia 总结状态
│   │       │   └── chat.ts             # Pinia 聊天状态
│   │       ├── api/
│   │       │   └── index.ts            # 调用后端 API
│   │       ├── hooks/
│   │       │   ├── useSummary.ts       # 总结相关逻辑
│   │       │   └── useChat.ts         # 聊天相关逻辑
│   │       ├── utils/
│   │       │   ├── format.ts           # 时间格式化
│   │       │   └── error.ts           # 错误处理
│   │       └── constants/
│   │           └── index.ts            # API路径、错误提示等
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 入口
│   │   ├── core/
│   │   │   ├── config.py          # 统一配置管理
│   │   │   └── exceptions.py      # 自定义异常
│   │   ├── routers/
│   │   │   ├── summary.py         # 每日总结路由
│   │   │   ├── chat.py            # 聊天路由
│   │   │   ├── settings.py        # 设置路由
│   │   │   └── health.py          # 健康检查
│   │   ├── services/
│   │   │   ├── activitywatch.py   # AW 数据采集（实现DataCollector）
│   │   │   ├── analyzer.py        # 数据分析
│   │   │   ├── llm.py             # 豆包 API 调用（含上下文管理）
│   │   │   └── collector_base.py  # DataCollector 抽象基类
│   │   ├── models/
│   │   │   ├── schemas.py         # Pydantic 请求/响应模型
│   │   │   └── models.py          # 数据库 ORM 模型
│   │   └── storage/
│   │       ├── base.py            # 存储抽象类
│   │       ├── sqlite.py          # SQLite 实现
│   │       └── cache.py           # 缓存逻辑
│   ├── requirements.txt
│   └── pyproject.toml
│
└── docs/
    └── specs/
```

---

## 4. 核心模块设计

### 4.1 后端模块

| 模块 | 职责 | 对外接口 |
|------|------|----------|
| `collector_base.py` | DataCollector 抽象基类，定义数据采集接口 | `get_daily_data(date)`, `get_apps()` |
| `activitywatch.py` | 实现 DataCollector，调用 AW API | 继承抽象基类 |
| `analyzer.py` | 分析数据生成结构化摘要 | `analyze_day(data)` |
| `llm.py` | 调用豆包 API，含上下文管理 | `generate_praise(data)`, `chat(message, history)` |
| `storage/base.py` | 存储抽象基类 | `save()`, `get()`, `delete()` |
| `storage/sqlite.py` | SQLite 实现 | 继承存储基类 |
| `storage/cache.py` | 缓存逻辑 | `get_cached()`, `set_cached()` |
| `routers/summary.py` | 每日总结 HTTP 路由 | `GET /api/summary/{date}`, `WebSocket /ws/summary/{date}` |
| `routers/chat.py` | 聊天 HTTP 路由 | `POST /api/chat` |
| `routers/settings.py` | 设置 HTTP 路由 | `GET/PUT /api/settings` |
| `routers/health.py` | 健康检查 | `GET /api/health` |
| `core/config.py` | 统一配置（API密钥、AW地址、存储路径） | 环境变量读取 |
| `core/exceptions.py` | 自定义异常 | `AWNotRunning`, `LLMCallFailed`, `ConfigMissing` |

### 4.2 前端模块

| 模块 | 职责 |
|------|------|
| `DailySummary.vue` | 展示每日夸夸总结、时间分配图表 |
| `ChatCompanion.vue` | 聊天陪伴界面，含上下文记忆 |
| `Settings.vue` | API 配置、监控开关、数据管理 |
| `SummaryCard.vue` | 夸夸内容展示卡片 |
| `TimePieChart.vue` | 工作/娱乐/其他时间饼图 |
| `TrendChart.vue` | 专注时长趋势图 |
| `ChatBubble.vue` | 聊天气泡组件 |
| `store/summary.ts` | Pinia 存储每日总结数据 |
| `store/chat.ts` | Pinia 存储聊天记录和上下文 |
| `api/index.ts` | 封装后端 API 调用 |
| `hooks/useSummary.ts` | 总结相关逻辑复用 |
| `hooks/useChat.ts` | 聊天相关逻辑复用 |

---

## 5. 数据流设计

### 5.1 每日总结生成流程

```
用户打开App
  │
  ▼
GET /api/summary/today
  │
  ├─► 查本地 SQLite 缓存
  │     │
  │     ├─ 有缓存 ──► 直接返回
  │     │
  │     └─ 无缓存 ──► 触发异步生成
  │                      │
  │                      ▼
  │              BackgroundTasks:
  │              1. 调用 AW API 拉取数据
  │              2. 分析数据
  │              3. 调用豆包 API 生成夸夸
  │              4. 存入 SQLite
  │              5. 通过 WebSocket 推送结果
  │
  ▼
前端接收 WebSocket 推送，渲染展示
```

**缓存策略：**
- 同一日期只生成一次，重复请求直接读缓存
- 缓存 key：`summary:{user_id}:{date}`

### 5.2 聊天流程

```
用户发送消息
  │
  ▼
POST /api/chat
{
  "chat_id": "user_20260423",     # 会话标识
  "message": "我今天写了3小时代码",
  "user_context": {...}            # 可选：当日行为摘要（让AI更懂用户）
}
  │
  ▼
1. 根据 chat_id 从 SQLite 读取最近 N 轮对话
2. 拼接上下文，调用豆包 API
3. 保存新对话到 SQLite
4. 返回 AI 回复
```

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|----------|
| ActivityWatch 未运行 | 返回友好提示 + 前端引导启动 |
| 豆包 API 调用失败 | 降级返回安慰文案 + 记录错误日志 |
| API 返回格式异常 | Pydantic 校验失败，记录日志，返回"服务暂时不可用" |
| 用户未配置密钥 | Settings 页保存时调用轻量接口验证 |
| 网络超时 | 前端显示重试按钮 |
| 数据不足 | 提示用户监控时长不够 |

**日志机制：**
- 后端用 `logging` + `rotating_file` 记录关键操作
- 错误日志单独文件 `error.log`

---

## 7. 用户体验设计

| 功能 | 说明 |
|------|------|
| **可视化图表** | 时间饼图（工作/娱乐/其他）、专注时长趋势图 |
| **情绪感知** | 根据行为数据主动关怀（如检测到连续娱乐1小时，主动问"要不要休息一下"） |
| **数据脱敏** | Settings 可开关，隐藏具体应用名 |
| **一键分享** | 夸夸内容可复制/截图 |
| **数据管理** | Settings 页可清理历史数据 |

---

## 8. API 设计

### 8.1 每日总结

```
GET /api/summary/{date}
Response:
{
  "status": "success" | "pending" | "error",
  "data": {
    "date": "2026-04-23",
    "total_hours": 8.5,
    "work_hours": 5.0,
    "entertainment_hours": 2.0,
    "other_hours": 1.5,
    "top_apps": [...],
    "praise_text": "今天的你真的很棒...",
    "suggestions": ["建议每40分钟休息一下"]
  }
}

WebSocket /ws/summary/{date}
- 推送生成进度和结果
```

### 8.2 聊天

```
POST /api/chat
Request:
{
  "chat_id": "user_20260423",
  "message": "我今天写了3小时代码",
  "user_context": {} // 可选
}

Response:
{
  "chat_id": "user_20260423",
  "reply": "太厉害了，3小时的专注真的很有毅力！",
  "history": [...]
}
```

### 8.3 设置

```
GET /api/settings
PUT /api/settings
Request:
{
  "doubao_api_key": "...",
  "aw_server_url": "http://127.0.0.1:5600",
  "data_masking": false
}
DELETE /api/settings/data // 清理数据
```

### 8.4 健康检查

```
GET /api/health
Response:
{
  "status": "ok",
  "activitywatch": "connected" | "disconnected",
  "storage": "ok"
}
```

---

## 9. 数据库设计

### 9.1 SQLite 表

```sql
-- 每日总结缓存
CREATE TABLE summaries (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- 聊天记录
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' | 'assistant'
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户设置
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    UNIQUE(user_id, key)
);
```

---

## 10. 部署方案

### 10.1 开发模式

```bash
# Terminal 1: 启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: 启动前端
cd electron
npm run dev
```

### 10.2 生产打包

- Electron 前端用 `electron-builder` 打包为 exe
- FastAPI 后端用 `gunicorn` + `uvicorn` 多进程运行
- 打包为一个安装包，用户一键安装

---

## 11. 后续扩展方向

- 支持 Wakatime 等其他数据源
- 多端数据同步
- 自定义夸夸风格
- 多语言支持
