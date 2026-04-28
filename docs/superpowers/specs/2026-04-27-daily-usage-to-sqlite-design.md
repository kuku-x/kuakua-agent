# 每日软件使用情况入库与 LLM 日画像（SQLite）技术设计

**日期**：2026-04-27  
**目标版本**：v1（先可用、可验证、可迭代）  
**范围**：Kuakua Agent 后端（FastAPI + 本地 SQLite `kuakua_agent.db`）+ 手机使用统计同步数据接入 + 日画像摘要生成 + LLM 上下文接入  

---

## 1. 背景与目标

你希望 Kuakua Agent **每天落地保存“软件使用情况”到数据库**，并通过“日画像摘要”让大模型更了解你，从而更适合你（更贴合的夸夸/建议/偏好）。

### 1.1 已确认的产品边界

- **安卓端定位**：手机端是“软件使用统计采集与同步器”，不在手机端生成夸夸内容、不在手机端维护聊天历史。
- **LLM 喂入粒度**：只喂 **每日/每周汇总摘要**，不把原始明细事件直接塞进 prompt。
- **保留策略**：保存 **365 天**，自动清理过期数据。

### 1.2 成功标准（验收）

- **数据入库**：每天的手机 UsageStats（按 App 聚合）与电脑 ActivityWatch（按 App 聚合）都能写入 SQLite。
- **可追溯**：手机端每次上报的原始条目可查（用于排障与重算）。
- **幂等**：手机端同一 `batch_id` 重试时，服务端不会重复写入“事件/聚合视图”。
- **可重复计算**：能从 `phone_usage_events` 重算 `phone_daily_usage`，结果稳定。
- **LLM 上下文可控**：`ContextBuilder` 读取最近 7–14 天摘要，长度受控、字段稳定、默认低敏。
- **可靠性**：写入失败不应破坏其它功能；接口返回明确错误信息。

---

## 2. 现状盘点（仓库真实实现）

### 2.1 已有 SQLite（记忆层）

`kuakua_agent/services/memory/database.py` 负责初始化 `kuakua_agent.db`，当前表包含：
- `milestones`（里程碑）
- `praise_history`（夸夸历史）
- `user_preferences`（偏好）
- `scene_profiles`（场景画像）
- `feedback_logs`（反馈）
- `chat_history`（聊天记录）

### 2.2 已有“每日电脑使用摘要”

`kuakua_agent/services/summary_service.py` 可从 ActivityWatch 计算某天：
- 总时长、类别（work/entertainment/other）
- top apps
- focus_score
- praise_text / suggestions

### 2.3 手机端数据接入现状

- 接口：`POST /api/phone/sync`（`kuakua_agent/api/phone_routes.py`）
- 请求已支持 `batch_id`（幂等重试）+ 回执字段（accepted/duplicate/failed）
- 当前落地：`kuakua_agent/services/phone_usage_service.py` 写 `data/phone_usage/`，同时维护 `events/` append-only（可追溯）

> 本设计的核心是：在保持现有文件落地可用的前提下，**引入 SQLite 的“权威存储”**，并按阶段迁移读写路径。

---

## 3. 总体架构（推荐方案）

### 3.1 推荐：复用现有 `kuakua_agent.db` 扩表

原因：
- 单机 FastAPI 最稳的持久化选择：事务、索引、去重、查询、清理都成熟。
- 与 `ContextBuilder`/偏好/里程碑同库，拼上下文更简单。
- 可渐进迁移：先“双写”（文件 + SQLite），再切读路径。

---

## 4. 数据模型（SQLite 表）

> 原则：**明细入库（用于追溯与重算），LLM 只读摘要（低敏且可控）**。

### 4.1 `phone_usage_events`（append-only 原始上报事件）

用途：保留每次同步上来的每条 App 记录，便于排障、对账、重算聚合视图。

字段（建议）：
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `device_id TEXT NOT NULL`
- `device_name TEXT NOT NULL`
- `usage_date TEXT NOT NULL`（YYYY-MM-DD）
- `package_name TEXT NOT NULL`
- `app_name TEXT NOT NULL`
- `duration_seconds INTEGER NOT NULL`
- `last_used TEXT NULL`（ISO string）
- `event_count INTEGER NOT NULL`
- `received_at INTEGER NOT NULL`（unix秒）
- `batch_id TEXT NULL`

索引：
- `idx_phone_events_device_date`：`(device_id, usage_date)`
- `idx_phone_events_received_at`：`(received_at)`
- 可选：`idx_phone_events_batch`：`(batch_id)`

幂等策略（v1）：
- 以 `batch_id` 为幂等粒度：同一 `batch_id` 重试直接返回缓存回执，不再重复写入事件表。

### 4.2 `phone_daily_usage`（手机按天聚合视图）

用途：快速查询某天某设备 top apps（给 UI/API），不依赖全表扫描。

字段（建议）：
- `device_id TEXT NOT NULL`
- `usage_date TEXT NOT NULL`
- `package_name TEXT NOT NULL`
- `app_name TEXT NOT NULL`
- `duration_seconds INTEGER NOT NULL`
- `last_used TEXT NULL`
- `event_count INTEGER NOT NULL`
- `updated_at INTEGER NOT NULL`（unix秒）

主键/唯一约束：
- `PRIMARY KEY (device_id, usage_date, package_name)`

聚合规则（与当前上报模型匹配）：
- `duration_seconds`：取 `max()`（因为手机上报的是“累计时长”，重试/补发不应该累加）
- `event_count`：取 `max()`（同理视作累计打开次数）
- `last_used`：取最新非空值
- `app_name`：取最新非空值

### 4.3 `daily_usage_summary`（给 LLM 的日画像摘要）

用途：提供一个稳定、低敏、长度可控的“日画像”输入，供 LLM 在夸夸/建议时参考。

字段（建议）：
- `date TEXT PRIMARY KEY`（YYYY-MM-DD）
- `payload_json TEXT NOT NULL`
- `created_at INTEGER NOT NULL`（unix秒）
- `updated_at INTEGER NOT NULL`（unix秒）

`payload_json` 建议结构（v1）：
```json
{
  "date": "2026-04-27",
  "phone": {
    "device_ids": ["..."],
    "total_seconds": 12345,
    "top_apps": [{"name": "微信", "seconds": 3600, "category": "other"}]
  },
  "computer": {
    "total_seconds": 23456,
    "top_apps": [{"name": "Visual Studio Code", "seconds": 7200, "category": "work"}],
    "focus_score": 78
  },
  "combined": {
    "total_seconds": 35801,
    "work_seconds": 20000,
    "entertainment_seconds": 8000,
    "other_seconds": 7801
  },
  "insights": [
    "今天的工作类应用占比更高，节奏比较稳。",
    "手机端主要碎片时间集中在通讯与短视频。"
  ]
}
```

---

## 5. 数据流与计算链路

```mermaid
flowchart TD
  Android[AndroidApp_UsageStats] -->|POST_/api/phone/sync(batch_id)| PhoneSyncApi[FastAPI_phone_routes]
  PhoneSyncApi --> PhoneUsageService[PhoneUsageService]

  PhoneUsageService -->|dual_write_v1| FileStore[data/phone_usage_events_json]
  PhoneUsageService -->|insert_events| SqlitePhoneEvents[(SQLite_phone_usage_events)]
  PhoneUsageService -->|upsert_daily| SqlitePhoneDaily[(SQLite_phone_daily_usage)]

  ActivityWatch[ActivityWatchClient] --> SummaryService[SummaryService]
  SummaryService -->|computer_daily| ComputerDaily[ComputerDailyStats]

  SqlitePhoneDaily --> DailySummarizer[DailyUsageSummarizer]
  ComputerDaily --> DailySummarizer
  DailySummarizer --> DailySummary[(SQLite_daily_usage_summary)]

  DailySummary --> ContextBuilder[ContextBuilder]
  ContextBuilder --> LLM[ModelAdapter]
```

---

## 6. API 设计（最小集）

> 目标：让桌面端/调试能查到 daily summary，并支持重算。

### 6.1 获取指定日期日画像

- `GET /api/usage/daily-summary?date=YYYY-MM-DD`
- 行为：
  - 若 `daily_usage_summary` 已存在：直接返回
  - 若不存在：调用 `DailyUsageSummarizer.rebuild(date)` 生成并写入后返回

### 6.2 获取最近 N 天日画像

- `GET /api/usage/daily-summary/recent?days=14`

### 6.3 重算某天（可选）

- `POST /api/jobs/daily-summary/rebuild?date=YYYY-MM-DD`

---

## 7. LLM 上下文接入（ContextBuilder）

接入点：`kuakua_agent/services/brain/context.py`

策略：
- 读取最近 7–14 天 `daily_usage_summary`（默认 7 天）
- 将摘要压缩成 **短文本块**（例如每天下面 3 行以内）
- 限制总长度（例如 600–1200 字），避免 prompt 膨胀

建议文本格式（示例）：
```
## 最近7天使用节奏画像（软件使用）
- 04-27：总活跃 10.8h（工作 6.5h / 娱乐 2.8h）Top: VSCode, Chrome, 微信
- 04-26：总活跃 9.2h（工作 5.1h / 娱乐 3.0h）Top: Cursor, Edge, 抖音
...
```

---

## 8. 保留策略与清理（365 天）

清理对象：
- `phone_usage_events`
- `phone_daily_usage`
- `daily_usage_summary`

清理方式：
- 每天或每周执行一次 `DELETE ... WHERE usage_date/date < (today - 365d)`。
- 清理任务应可重复执行（幂等），失败不影响核心功能。

---

## 9. 分阶段实施（逐步完成）

### 阶段 1：SQLite 扩表 + 双写（低风险）
- 扩展 `kuakua_agent/services/memory/database.py` 的 `SCHEMA`，创建新表与索引
- 在 `PhoneUsageService` 接收入口写入：
  - 仍保留现有文件落地（稳定兜底）
  - 同时写 SQLite（权威数据源雏形）

### 阶段 2：读路径切到 SQLite
- 聚合查询（如 `/api/usage/aggregate`）优先从 SQLite 读手机数据
- 文件落地逐渐降级为“备份/排障”用途

### 阶段 3：日画像生成与 API
- `DailyUsageSummarizer`：合并手机 daily + 电脑 daily（SummaryService）生成 `daily_usage_summary`
- 增加查询/重算接口

### 阶段 4：接入 ContextBuilder + 清理任务
- ContextBuilder 拼入最近 N 天摘要
- 定期清理任务上线并验证

---

## 10. 风险与缓解

- **SQLite 与现有 memory 同库耦合**：通过表命名与索引隔离，且写入失败需捕获并降级（不影响聊天/夸夸）。
- **幂等仅 batch 粒度**：v1 足够；后续如需事件级幂等可引入 `entry_id` 并加唯一约束。
- **日摘要 prompt 膨胀**：强制长度限制 + 最近 N 天窗口。

---

**文档结束**。

