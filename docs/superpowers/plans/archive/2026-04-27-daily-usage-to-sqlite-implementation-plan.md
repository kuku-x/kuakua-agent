# Daily Usage to SQLite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将每日软件使用情况（手机 UsageStats + 电脑 ActivityWatch）写入 `kuakua_agent.db`，并生成可喂给 LLM 的“日画像摘要”，用于更贴合的夸夸/建议。

**Architecture:** 复用现有 `kuakua_agent/services/memory/database.py` 的 SQLite，在 `/api/phone/sync` 接收入口双写（文件+SQLite），再基于 SQLite 生成 `daily_usage_summary`，由 `ContextBuilder` 读取最近 7 天摘要注入 prompt。

**Tech Stack:** FastAPI + sqlite3（现有）+ ActivityWatch（现有）+ Pydantic（现有）

---

## 文件结构规划

**Modify:**
- `kuakua_agent/services/memory/database.py`（扩表）
- `kuakua_agent/services/phone_usage_service.py`（双写入库）
- `kuakua_agent/services/brain/context.py`（注入日画像摘要）
- `kuakua_agent/services/brain/prompt.py`（模板新增“日画像摘要”块）
- `kuakua_agent/api/app.py`（注册新路由）

**Create:**
- `kuakua_agent/services/usage/phone_usage_db.py`
- `kuakua_agent/services/usage/daily_summary_db.py`
- `kuakua_agent/services/usage/daily_summarizer.py`
- `kuakua_agent/services/usage/retention.py`
- `kuakua_agent/api/usage_summary_routes.py`

---

## Task 1: SQLite 扩表（usage 相关表）

**Files:**
- Modify: `kuakua_agent/services/memory/database.py`

- [ ] **Step 1: 添加表与索引**
  - `phone_usage_events`
  - `phone_daily_usage`
  - `daily_usage_summary`

- [ ] **Step 2: 运行后端编译检查**

Run: `python -m compileall kuakua_agent`  
Expected: exit_code 0

---

## Task 2: 手机同步入口双写（文件 + SQLite）

**Files:**
- Create: `kuakua_agent/services/usage/phone_usage_db.py`
- Modify: `kuakua_agent/services/phone_usage_service.py`

- [ ] **Step 1: 实现 `PhoneUsageDb`**
  - `insert_events(batch_id, device_id, device_name, entries, received_at)`
  - `upsert_daily(device_id, entry, updated_at)`
  - `get_daily(device_id, date)` / `get_daily_all_devices(date)`（给聚合/摘要用）

- [ ] **Step 2: 在 `PhoneUsageService.sync_entries` 中写入 SQLite**
  - 保持现有文件落地不变（兜底）
  - 若 SQLite 写入失败：记录日志但不阻塞接口成功（v1 容错）

---

## Task 3: 日画像摘要生成与查询 API

**Files:**
- Create: `kuakua_agent/services/usage/daily_summary_db.py`
- Create: `kuakua_agent/services/usage/daily_summarizer.py`
- Create: `kuakua_agent/api/usage_summary_routes.py`
- Modify: `kuakua_agent/api/app.py`

- [ ] **Step 1: 实现 `DailyUsageSummaryDb`**
  - `get(date)` / `upsert(date, payload_json)`
  - `list_recent(days)`

- [ ] **Step 2: 实现 `DailyUsageSummarizer.rebuild(date)`**
  - phone: 从 `phone_daily_usage` 聚合 total/top_apps
  - computer: 复用 `SummaryService.get_summary(date)` 拿 top_apps 与 focus_score
  - combined: 汇总秒数（work/entertainment/other 尽可能复用现有分类）
  - insights: 1-3 条短洞察（规则化生成，避免大模型依赖）

- [ ] **Step 3: 新增 API**
  - `GET /api/usage/daily-summary?date=...`（缺失则重建）
  - `GET /api/usage/daily-summary/recent?days=...`
  - `POST /api/jobs/daily-summary/rebuild?date=...`

---

## Task 4: ContextBuilder 接入日画像摘要（LLM 只读摘要）

**Files:**
- Modify: `kuakua_agent/services/brain/context.py`
- Modify: `kuakua_agent/services/brain/prompt.py`

- [ ] **Step 1: `ContextBuilder` 读取最近 7 天摘要并格式化为短文本块**
- [ ] **Step 2: Prompt 模板新增“最近使用节奏画像”区块**

---

## Task 5: 365 天保留清理（可重复执行）

**Files:**
- Create: `kuakua_agent/services/usage/retention.py`
- Modify: `kuakua_agent/services/usage/daily_summarizer.py`（重建后 best-effort 触发一次清理）

- [ ] **Step 1: 实现 `cleanup_older_than(days=365)`**
- [ ] **Step 2: 触发策略**
  - 在 `rebuild(date)` 成功后调用（带内存节流：例如 12 小时最多一次）

---

## Task 6: 验证

- [ ] **Step 1: 编译检查**

Run: `python -m compileall kuakua_agent`  
Expected: exit_code 0

- [ ] **Step 2: 端到端手工验收（命令）**

1) 手机同步（用 curl 模拟）：`POST /api/phone/sync`（带 `batch_id`）  
2) 查询日画像：`GET /api/usage/daily-summary?date=YYYY-MM-DD`  
3) 再次用相同 `batch_id` 重试：响应应一致且不重复写入  

---

