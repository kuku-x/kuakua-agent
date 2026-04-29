# 夸夸 Agent 目录结构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将夸夸 Agent 项目目录结构从混乱状态重构为规范化层级：后端服务重命名为语义化域名、聚合散落文件、归档文档、清理日志、前端组件归类。

**Architecture:** 通过系统化目录重命名 + 文件移动 + import 路径批量替换完成，零业务逻辑改动。

**Tech Stack:** Git mv, Bash mv/find/sed, Python/JS import 更新

---

## 前置检查

- [ ] **Step 0.1:** 确认工作区状态（当前有未提交更改，将一并纳入）

---

## Phase 1：归档旧计划文档

- [ ] **Step 1.1:** 创建归档目录

```bash
mkdir -p docs/superpowers/plans/archive
```

- [ ] **Step 1.2:** 移动 12 个旧计划文档到 archive/

```bash
git mv docs/superpowers/plans/2026-04-23-kuakua-agent-implementation.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-24-kuakua-agent-frontend-refactor-plan.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-24-kuakua-agent-implementation-plan.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-25-phone-usage-sync.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-26-phone-stats-ui-plan.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-27-daily-usage-to-sqlite-implementation-plan.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-27-fullstack-refactor-acceptance-checklist.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-27-fullstack-refactor-auto-execution-log.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-27-fullstack-refactor-execution-plan.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-27-fullstack-refactor-risks-and-next-steps.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-27-phone-stats-monitor-enhancement-plan.md docs/superpowers/plans/archive/
git mv docs/superpowers/plans/2026-04-28-local-tts-migration-plan.md docs/superpowers/plans/archive/
```

---

## Phase 2：清理日志文件

- [ ] **Step 2.1:** 删除 data/ 下日志文件

```bash
git rm -f data/aw_proxy.err.log data/aw_proxy.out.log
```

- [ ] **Step 2.2:** 确认 data/phone_usage/ 下 .json 业务数据保留

---

## Phase 3：重命名 tools → scripts

- [ ] **Step 3.1:** 重命名顶层目录

```bash
git mv tools/ scripts/
```

---

## Phase 4：后端服务目录重命名与聚合

### Task 1: brain → ai_engine

- [ ] **Step 4.1.1:** 重命名 brain → ai_engine

```bash
git mv kuakua_agent/services/brain kuakua_agent/services/ai_engine
```

### Task 2: memory → storage_layer

- [ ] **Step 4.2.1:** 重命名 memory → storage_layer

```bash
git mv kuakua_agent/services/memory kuakua_agent/services/storage_layer
```

### Task 3: output → notification

- [ ] **Step 4.3.1:** 重命名 output → notification

```bash
git mv kuakua_agent/services/output kuakua_agent/services/notification
```

### Task 4: usage → user_behavior

- [ ] **Step 4.4.1:** 重命名 usage → user_behavior

```bash
git mv kuakua_agent/services/usage kuakua_agent/services/user_behavior
```

### Task 5: activitywatch + scheduler 移入 monitor/

- [ ] **Step 4.5.1:** 创建 monitor 目录

```bash
mkdir -p kuakua_agent/services/monitor
```

- [ ] **Step 4.5.2:** 移动 activitywatch → monitor/activitywatch

```bash
git mv kuakua_agent/services/activitywatch kuakua_agent/services/monitor/activitywatch
```

- [ ] **Step 4.5.3:** 移动 scheduler → monitor/scheduler

```bash
git mv kuakua_agent/services/scheduler kuakua_agent/services/monitor/scheduler
```

### Task 6: 散落文件归类

- [ ] **Step 4.6.1:** chat_service.py → ai_engine/

```bash
git mv kuakua_agent/services/chat_service.py kuakua_agent/services/ai_engine/chat_service.py
```

- [ ] **Step 4.6.2:** nightly_summary_scheduler.py → monitor/

```bash
git mv kuakua_agent/services/nightly_summary_scheduler.py kuakua_agent/services/monitor/nightly_summary_scheduler.py
```

- [ ] **Step 4.6.3:** phone_usage_service.py → monitor/

```bash
git mv kuakua_agent/services/phone_usage_service.py kuakua_agent/services/monitor/phone_usage_service.py
```

- [ ] **Step 4.6.4:** summary_service.py → monitor/

```bash
git mv kuakua_agent/services/summary_service.py kuakua_agent/services/monitor/summary_service.py
```

- [ ] **Step 4.6.5:** weather.py → notification/

```bash
git mv kuakua_agent/services/weather.py kuakua_agent/services/notification/weather.py
```

---

## Phase 5：前端组件归类

### Task 7: business 目录

- [ ] **Step 5.1.1:** 创建 business 目录

```bash
mkdir -p desktop/src/renderer/components/business
```

- [ ] **Step 5.1.2:** 移动 ChatBubble.vue

```bash
git mv desktop/src/renderer/components/ChatBubble.vue desktop/src/renderer/components/business/ChatBubble.vue
```

- [ ] **Step 5.1.3:** 移动 DailyQuote.vue

```bash
git mv desktop/src/renderer/components/DailyQuote.vue desktop/src/renderer/components/business/DailyQuote.vue
```

- [ ] **Step 5.1.4:** 移动 SummaryCard.vue

```bash
git mv desktop/src/renderer/components/SummaryCard.vue desktop/src/renderer/components/business/SummaryCard.vue
```

- [ ] **Step 5.1.5:** 移动 WeatherCard.vue

```bash
git mv desktop/src/renderer/components/WeatherCard.vue desktop/src/renderer/components/business/WeatherCard.vue
```

### Task 8: widgets 目录

- [ ] **Step 5.2.1:** 创建 widgets 目录

```bash
mkdir -p desktop/src/renderer/components/widgets
```

- [ ] **Step 5.2.2:** 移动 GlobalError.vue

```bash
git mv desktop/src/renderer/components/GlobalError.vue desktop/src/renderer/components/widgets/GlobalError.vue
```

- [ ] **Step 5.2.3:** 移动 TimePieChart.vue

```bash
git mv desktop/src/renderer/components/TimePieChart.vue desktop/src/renderer/components/widgets/TimePieChart.vue
```

- [ ] **Step 5.2.4:** SettingsTrigger.vue 移入 settings/（已在 settings 目录下，确认）

---

## Phase 6：更新 import 路径

### Task 9: Python import 更新

- [ ] **Step 6.1.1:** 更新 ai_engine 相关 import

```bash
# 使用 sed 批量替换，-i.bak 备份
# 替换 from kuakua_agent.services.brain → from kuakua_agent.services.ai_engine
# 替换 from kuakua_agent.services.memory → from kuakua_agent.services.storage_layer
# 替换 from kuakua_agent.services.output → from kuakua_agent.services.notification
# 替换 from kuakua_agent.services.usage → from kuakua_agent.services.user_behavior
# 替换 from kuakua_agent.services.activitywatch → from kuakua_agent.services.monitor.activitywatch
# 替换 from kuakua_agent.services.scheduler → from kuakua_agent.services.monitor.scheduler

grep -rl "kuakua_agent.services.brain" kuakua_agent/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.brain|kuakua_agent.services.ai_engine|g'
grep -rl "kuakua_agent.services.memory" kuakua_agent/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.memory|kuakua_agent.services.storage_layer|g'
grep -rl "kuakua_agent.services.output" kuakua_agent/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.output|kuakua_agent.services.notification|g'
grep -rl "kuakua_agent.services.usage" kuakua_agent/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.usage|kuakua_agent.services.user_behavior|g'
grep -rl "kuakua_agent.services.activitywatch" kuakua_agent/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.activitywatch|kuakua_agent.services.monitor.activitywatch|g'
grep -rl "kuakua_agent.services.scheduler" kuakua_agent/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.scheduler|kuakua_agent.services.monitor.scheduler|g'
```

- [ ] **Step 6.1.2:** 删除 .bak 备份文件

```bash
find kuakua_agent/ -name "*.bak" -delete
```

- [ ] **Step 6.1.3:** 更新 __init__.py 导出（检查 ai_engine/storage_layer/notification/user_behavior/monitor/__init__.py）

```bash
# 检查并更新所有 services/*/__init__.py 的 __all__ 列表
```

### Task 10: TypeScript import 更新

- [ ] **Step 6.2.1:** 更新前端组件引用路径（Vue 组件移动后）

```bash
# 组件移动后，查找仍引用旧路径的文件
grep -rl "@/components/ChatBubble" desktop/src/renderer/ --include="*.ts" --include="*.vue" | xargs sed -i.bak 's|@/components/ChatBubble|@/components/business/ChatBubble|g'
# 依此类推其他组件...
```

- [ ] **Step 6.2.2:** 删除 .bak 备份

```bash
find desktop/ -name "*.bak" -delete
```

### Task 11: 测试文件 import 更新

- [ ] **Step 6.3.1:** 更新 tests/ 下 import

```bash
grep -rl "kuakua_agent.services.brain" tests/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.brain|kuakua_agent.services.ai_engine|g'
grep -rl "kuakua_agent.services.memory" tests/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.memory|kuakua_agent.services.storage_layer|g'
grep -rl "kuakua_agent.services.output" tests/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.output|kuakua_agent.services.notification|g'
grep -rl "kuakua_agent.services.usage" tests/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.usage|kuakua_agent.services.user_behavior|g'
grep -rl "kuakua_agent.services.activitywatch" tests/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.activitywatch|kuakua_agent.services.monitor.activitywatch|g'
grep -rl "kuakua_agent.services.scheduler" tests/ --include="*.py" | xargs sed -i.bak 's|kuakua_agent.services.scheduler|kuakua_agent.services.monitor.scheduler|g'
find tests/ -name "*.bak" -delete
```

---

## Phase 7：验证

- [ ] **Step 7.1:** 运行 pytest

```bash
pytest tests/ -v --tb=short
```

- [ ] **Step 7.2:** 启动 FastAPI

```bash
python -m uvicorn kuakua_agent.main:app --reload --port 18000
```

- [ ] **Step 7.3:** 构建桌面应用

```bash
cd desktop && npm run build
```

- [ ] **Step 7.4:** Git 提交

```bash
git add -A && git commit -m "refactor: restructure project directories - services/四大域聚合、前端组件归类、文档归档"
```

---

## 依赖关系

```
Phase 1 (归档) ──┐
Phase 2 (日志) ──┤──► Phase 3 (tools→scripts) ──► Phase 4 (后端重命名) ──► Phase 5 (前端归类) ──► Phase 6 (import) ──► Phase 7 (验证)
                  │                              │
                  └──────────────────────────────┘
                         (Phase 1-2 可并行)
```
