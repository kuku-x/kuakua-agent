# 夸夸 Agent 目录结构重构设计方案

> **Date:** 2026-04-29
> **Status:** Draft

---

## 1. 背景与目标

### 1.1 问题现状

| 问题类别 | 具体表现 |
|---------|---------|
| 命名抽象难懂 | `brain/`、`memory/`、`output/`、`usage/` 命名晦涩，新人难以理解职责 |
| 后端根目录不一致 | CLAUDE.md 写 `backend/`，实际代码在 `kuakua_agent/` |
| 服务拆分过细 | `services/` 下 9 个子目录，部分职责重叠，层级过深 |
| 前端组件散落 | `components/` 根目录有 6 个未归类组件 |
| 文档污染 | `docs/superpowers/plans/` 下 12 个带日期的零散规划文档 |
| data/ 含日志 | `data/phone_usage/` 下有 `aw_proxy.err.log`、`.out.log` 待清理 |
| tools 命名非标准 | 应为行业通用 `scripts/` |
| 服务层散落文件 | `services/` 根有 7 个独立 `.py` 文件未归类 |

### 1.2 重构原则

1. **命名语义化**：全部使用小写蛇形（snake_case），目录名见名知意
2. **层级扁平化**：能二级解决绝不三级，减少嵌套深度
3. **业务域聚合**：按领域合并拆分过细的模块
4. **零不动代码逻辑**：仅做目录重组，不改变任何业务代码

---

## 2. 重命名对照表

### 2.1 后端服务目录重命名

| 原路径 | 新路径 | 理由 |
|-------|-------|------|
| `services/brain/` | `services/ai_engine/` | AI 引擎更直观：模型调度、Prompt、上下文 |
| `services/memory/` | `services/storage_layer/` | 存储层更直观：数据库、聊天历史、用户数据 |
| `services/output/` | `services/notification/` | 通知更直观：系统通知、TTS 语音播报 |
| `services/usage/` | `services/user_behavior/` | 用户行为更直观：应用使用、手机使用统计 |

### 2.2 工具与顶层目录

| 原路径 | 新路径 | 理由 |
|-------|-------|------|
| `tools/` | `scripts/` | 行业标准命名 |

### 2.3 前端组件归类

| 原路径 | 新路径 | 理由 |
|-------|-------|------|
| `components/ChatBubble.vue` | `components/business/ChatBubble.vue` | 业务组件 |
| `components/DailyQuote.vue` | `components/business/DailyQuote.vue` | 业务组件 |
| `components/SummaryCard.vue` | `components/business/SummaryCard.vue` | 业务组件 |
| `components/WeatherCard.vue` | `components/business/WeatherCard.vue` | 业务组件 |
| `components/GlobalError.vue` | `components/widgets/GlobalError.vue` | 通用小部件 |
| `components/TimePieChart.vue` | `components/widgets/TimePieChart.vue` | 通用小部件 |

---

## 3. 后端服务层重构（四大业务域）

### 3.1 聚合方案

将原来 9 个子目录 + 7 个散落文件，重组为 4 个明确业务域 + 2 个跨域服务：

```
services/
├── ai_engine/              # 原 brain/ - AI 模型调度
│   ├── adapter.py           # 模型适配器
│   ├── context.py           # 上下文构建
│   ├── prompt.py           # Prompt 管理
│   ├── router.py           # AI 路由
│   ├── nightly_summary_generator.py  # 夜间总结生成
│   └── chat_service.py     # 聊天服务（原散落）
│
├── storage_layer/           # 原 memory/ - 数据持久化
│   ├── database.py         # 异步数据库
│   ├── chat_history.py    # 聊天历史
│   ├── milestone.py        # 里程碑
│   ├── preference.py       # 用户偏好
│   ├── profile.py          # 用户画像
│   ├── feedback.py         # 反馈记录
│   ├── history.py          # 历史记录
│   └── models.py           # 数据模型
│
├── monitor/                # 原 activitywatch/ + scheduler/ 合并
│   ├── activitywatch/     # ActivityWatch 行为监控
│   │   ├── client.py
│   │   ├── detector.py
│   │   └── scheduler.py
│   ├── scheduler/          # 夸夸调度器
│   │   ├── scheduler.py
│   │   ├── cooldown.py
│   │   ├── events.py
│   │   └── rules.py
│   ├── nightly_summary_scheduler.py  # 夜间总结调度（原散落）
│   ├── phone_usage_service.py        # 手机使用服务（原散落）
│   └── summary_service.py            # 总结服务（原散落）
│
├── notification/           # 原 output/ - 通知与输出
│   ├── base.py            # 通知基类
│   ├── notifier.py        # 系统通知
│   ├── tts.py             # TTS 语音播报
│   └── weather.py         # 天气信息（原散落）
│
├── integrations/          # 第三方集成（保持不变）
├── settings_service.py   # 设置服务（跨域，保留原地）
└── websocket_manager.py   # WebSocket 管理（跨域，保留原地）
```

### 3.2 散落文件归类明细

| 散落文件 | 归属域 | 理由 |
|---------|-------|------|
| `services/chat_service.py` | `ai_engine/` | 核心 AI 聊天逻辑 |
| `services/nightly_summary_scheduler.py` | `monitor/` | 调度相关 |
| `services/phone_usage_service.py` | `monitor/` | 手机使用监控 |
| `services/summary_service.py` | `monitor/` | 统计总结 |
| `services/weather.py` | `notification/` | 通知输出 |

---

## 4. 前端组件重构

### 4.1 组件分层

```
components/
├── base/           # 基础 UI 组件（已有）
│   ├── KuButton.vue
│   ├── KuCard.vue
│   ├── KuInput.vue
│   └── KuSpinner.vue
│
├── layout/         # 布局组件（已有）
│   ├── AppLayout.vue
│   └── Sidebar.vue
│
├── settings/       # 设置相关（已有）
│   ├── SettingsPanel.vue
│   ├── SettingsPanelContent.vue
│   └── SettingsTrigger.vue    # 原散落 → 现已归入 settings/
│
├── business/       # 业务组件（新建）
│   ├── ChatBubble.vue         # 原散落
│   ├── DailyQuote.vue         # 原散落
│   ├── SummaryCard.vue        # 原散落
│   └── WeatherCard.vue        # 原散落
│
└── widgets/        # 通用小部件（新建）
    ├── GlobalError.vue        # 原散落
    └── TimePieChart.vue      # 原散落
```

---

## 5. 文档归档方案

### 5.1 归档策略

`docs/superpowers/plans/` 下按日期归档，只保留最新核心规划：

**保留（2 个）：**
- `2026-04-29-agent-capability-enhancement.md`
- `2026-04-28-kuakua-agent-optimization-roadmap.md`

**归档到 `plans/archive/`（10 个）：**
- `2026-04-23-kuakua-agent-implementation.md`
- `2026-04-24-kuakua-agent-frontend-refactor-plan.md`
- `2026-04-24-kuakua-agent-implementation-plan.md`
- `2026-04-25-phone-usage-sync.md`
- `2026-04-26-phone-stats-ui-plan.md`
- `2026-04-27-daily-usage-to-sqlite-implementation-plan.md`
- `2026-04-27-fullstack-refactor-acceptance-checklist.md`
- `2026-04-27-fullstack-refactor-auto-execution-log.md`
- `2026-04-27-fullstack-refactor-execution-plan.md`
- `2026-04-27-fullstack-refactor-risks-and-next-steps.md`
- `2026-04-27-phone-stats-monitor-enhancement-plan.md`
- `2026-04-28-local-tts-migration-plan.md`

### 5.2 specs 目录

`docs/superpowers/specs/` 下设计文档全部保留（架构设计资产）：
- `2026-04-23-kuakua-agent-design.md`
- `2026-04-24-kuakua-agent-architecture-design.md`
- `2026-04-24-kuakua-agent-frontend-refactor-design.md`
- `2026-04-25-phone-stats-sync-design.md`
- `2026-04-26-phone-stats-ui-design.md`
- `2026-04-27-daily-usage-to-sqlite-design.md`
- `2026-04-27-fullstack-refactor-architecture.md`

---

## 6. data/ 目录清理

### 6.1 日志文件删除

以下文件为运行时日志，可直接删除：
- `data/aw_proxy.err.log`
- `data/aw_proxy.out.log`

### 6.2 保留内容

`data/phone_usage/` 下所有 `.json` 文件为业务数据，保留不动。

---

## 7. 完整规范化目录树

```
kuakua-agent/
├── CLAUDE.md                  # 项目说明
├── README.md
├── pyproject.toml
├── .env                       # 环境变量
├── .gitignore
│
├── kuakua_agent/             # 后端根目录（统一命名）
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 配置
│   │
│   ├── api/                   # API 路由层
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── errors.py
│   │   ├── phone_routes.py
│   │   ├── activitywatch_proxy_routes.py
│   │   └── usage_summary_routes.py
│   │
│   ├── core/                  # 核心基础设施
│   │   ├── logging.py
│   │   ├── tracing.py
│   │   └── errors.py
│   │
│   ├── schemas/               # Pydantic 数据模型
│   │   ├── chat.py
│   │   ├── common.py
│   │   ├── integration.py
│   │   ├── nightly_summary.py
│   │   ├── phone_usage.py
│   │   ├── praise.py
│   │   ├── settings.py
│   │   └── summary.py
│   │
│   ├── services/              # 业务服务层（四大域）
│   │   ├── ai_engine/         # AI 引擎：模型调度、Prompt、上下文
│   │   │   ├── adapter.py
│   │   │   ├── context.py
│   │   │   ├── prompt.py
│   │   │   ├── router.py
│   │   │   ├── nightly_summary_generator.py
│   │   │   └── chat_service.py
│   │   │
│   │   ├── storage_layer/     # 存储层：数据库、聊天历史、用户数据
│   │   │   ├── database.py
│   │   │   ├── chat_history.py
│   │   │   ├── milestone.py
│   │   │   ├── preference.py
│   │   │   ├── profile.py
│   │   │   ├── feedback.py
│   │   │   ├── history.py
│   │   │   └── models.py
│   │   │
│   │   ├── monitor/           # 监控：ActivityWatch、调度器、使用统计
│   │   │   ├── activitywatch/
│   │   │   │   ├── client.py
│   │   │   │   ├── detector.py
│   │   │   │   └── scheduler.py
│   │   │   ├── scheduler/
│   │   │   │   ├── scheduler.py
│   │   │   │   ├── cooldown.py
│   │   │   │   ├── events.py
│   │   │   │   └── rules.py
│   │   │   ├── nightly_summary_scheduler.py
│   │   │   ├── phone_usage_service.py
│   │   │   └── summary_service.py
│   │   │
│   │   ├── notification/     # 通知：系统通知、TTS 语音、天气
│   │   │   ├── base.py
│   │   │   ├── notifier.py
│   │   │   ├── tts.py
│   │   │   └── weather.py
│   │   │
│   │   ├── integrations/     # 第三方集成
│   │   │   ├── base.py
│   │   │   ├── providers.py
│   │   │   └── registry.py
│   │   │
│   │   ├── settings_service.py  # 跨域设置服务
│   │   └── websocket_manager.py  # 跨域 WebSocket 管理
│   │
│   └── utils/                 # 工具函数
│
├── desktop/                   # Electron 桌面应用
│   ├── package.json
│   └── src/
│       ├── main/              # Electron 主进程
│       ├── preload/           # 预加载脚本
│       └── renderer/          # Vue 渲染进程
│           ├── main.ts
│           ├── App.vue
│           ├── api/            # API 调用
│           │   ├── index.ts
│           │   └── praise.ts
│           ├── components/    # UI 组件
│           │   ├── base/      # 基础组件：按钮、卡片、输入框、加载
│           │   ├── layout/    # 布局：主布局、侧边栏
│           │   ├── settings/  # 设置面板、触发器
│           │   ├── business/  # 业务组件：聊天、总结、天气
│           │   └── widgets/   # 通用部件：饼图、错误提示
│           ├── hooks/         # Vue 组合式函数
│           ├── router/        # 路由配置
│           ├── store/         # 状态管理
│           ├── types/         # TypeScript 类型
│           ├── utils/         # 工具函数
│           ├── views/         # 页面视图
│           ├── constants/     # 常量配置
│           └── styles/        # 全局样式
│
├── scripts/                   # 工具脚本（原 tools/）
│   ├── activitywatch_lan_proxy.py
│   └── smoke_phone_sync.py
│
├── tests/                     # 测试代码
│   ├── api/
│   │   └── test_praise_settings_routes.py
│   └── services/
│       ├── brain/
│       │   └── test_context.py
│       ├── memory/
│       │   ├── test_milestone.py
│       │   └── test_preference.py
│       ├── output/
│       │   └── test_tts.py
│       ├── scheduler/
│       │   ├── test_cooldown.py
│       │   └── test_rules.py
│       └── test_settings_service.py
│
├── docs/                      # 项目文档
│   ├── PROJECT_DOC.md
│   └── superpowers/
│       ├── specs/             # 架构设计文档（保留全部）
│       │   ├── 2026-04-23-kuakua-agent-design.md
│       │   ├── 2026-04-24-kuakua-agent-architecture-design.md
│       │   ├── 2026-04-24-kuakua-agent-frontend-refactor-design.md
│       │   ├── 2026-04-25-phone-stats-sync-design.md
│       │   ├── 2026-04-26-phone-stats-ui-design.md
│       │   ├── 2026-04-27-daily-usage-to-sqlite-design.md
│       │   └── 2026-04-27-fullstack-refactor-architecture.md
│       └── plans/            # 规划文档
│           ├── 2026-04-28-kuakua-agent-optimization-roadmap.md
│           ├── 2026-04-29-agent-capability-enhancement.md
│           └── archive/      # 历史规划归档
│               ├── 2026-04-23-kuakua-agent-implementation.md
│               ├── 2026-04-24-kuakua-agent-frontend-refactor-plan.md
│               ├── 2026-04-24-kuakua-agent-implementation-plan.md
│               ├── 2026-04-25-phone-usage-sync.md
│               ├── 2026-04-26-phone-stats-ui-plan.md
│               ├── 2026-04-27-daily-usage-to-sqlite-implementation-plan.md
│               ├── 2026-04-27-fullstack-refactor-acceptance-checklist.md
│               ├── 2026-04-27-fullstack-refactor-auto-execution-log.md
│               ├── 2026-04-27-fullstack-refactor-execution-plan.md
│               ├── 2026-04-27-fullstack-refactor-risks-and-next-steps.md
│               ├── 2026-04-27-phone-stats-monitor-enhancement-plan.md
│               └── 2026-04-28-local-tts-migration-plan.md
│
├── data/                      # 运行时业务数据
│   └── phone_usage/          # 手机使用 JSON 数据
│       ├── events/
│       ├── 1aa3757210535b67_2026-04-25.json
│       ├── 1aa3757210535b67_2026-04-26.json
│       ├── 1aa3757210535b67_2026-04-28.json
│       ├── android_mi_001_2026-04-25.json
│       ├── dev123_2026-04-27.json
│       ├── dev999_2026-04-27.json
│       ├── smoke-dev-001_2026-04-28.json
│       └── _idempotency.json
│
└── kuakua_agent.db           # SQLite 数据库
```

---

## 8. 执行步骤

> 顺序很重要，步骤 1-4 可以并行，步骤 5-6 必须在步骤 4 之后，步骤 7 最后执行。

### Phase 0：准备

- [ ] **Step 0.1：** 确认 git 工作区 clean（无未提交更改）

### Phase 1：归档与清理（可并行）

- [ ] **Step 1.1：** 创建归档目录 `docs/superpowers/plans/archive/`
- [ ] **Step 1.2：** 将 12 个旧计划文档移动到 `archive/`
- [ ] **Step 1.3：** 删除日志文件 `data/aw_proxy.err.log`、`data/aw_proxy.out.log`

### Phase 2：顶层目录重命名

- [ ] **Step 2.1：** `tools/` → `scripts/`

### Phase 3：后端服务重命名与聚合（核心步骤）

- [ ] **Step 3.1：** `services/brain/` → `services/ai_engine/`
- [ ] **Step 3.2：** `services/memory/` → `services/storage_layer/`
- [ ] **Step 3.3：** `services/output/` → `services/notification/`
- [ ] **Step 3.4：** `services/usage/` → `services/user_behavior/`
- [ ] **Step 3.5：** `services/activitywatch/` 移入 `services/monitor/`
- [ ] **Step 3.6：** `services/scheduler/` 移入 `services/monitor/`
- [ ] **Step 3.7：** 散落文件归类：
  - `services/chat_service.py` → `services/ai_engine/`
  - `services/nightly_summary_scheduler.py` → `services/monitor/`
  - `services/phone_usage_service.py` → `services/monitor/`
  - `services/summary_service.py` → `services/monitor/`
  - `services/weather.py` → `services/notification/`

### Phase 4：前端组件归类

- [ ] **Step 4.1：** 创建 `components/business/` 目录
- [ ] **Step 4.2：** 创建 `components/widgets/` 目录
- [ ] **Step 4.3：** 移动业务组件到 `business/`：ChatBubble、DailyQuote、SummaryCard、WeatherCard
- [ ] **Step 4.4：** 移动通用部件到 `widgets/`：GlobalError、TimePieChart

### Phase 5：更新 import 路径（关键）

- [ ] **Step 5.1：** 扫描所有 `.py` 文件中的 `from kuakua_agent.services.brain` → `from kuakua_agent.services.ai_engine`
- [ ] **Step 5.2：** `from kuakua_agent.services.memory` → `from kuakua_agent.services.storage_layer`
- [ ] **Step 5.3：** `from kuakua_agent.services.output` → `from kuakua_agent.services.notification`
- [ ] **Step 5.4：** `from kuakua_agent.services.usage` → `from kuakua_agent.services.user_behavior`
- [ ] **Step 5.5：** `from kuakua_agent.services.activitywatch` → `from kuakua_agent.services.monitor.activitywatch`
- [ ] **Step 5.6：** `from kuakua_agent.services.scheduler` → `from kuakua_agent.services.monitor.scheduler`
- [ ] **Step 5.7：** 更新 `services/*/__init__.py` 中的 `__all__` 导出
- [ ] **Step 5.8：** 更新前端 `import` 路径（组件移动后）

### Phase 6：验证

- [ ] **Step 6.1：** 运行 pytest：`pytest tests/ -v --tb=short`
- [ ] **Step 6.2：** 启动 FastAPI：`python -m uvicorn kuakua_agent.main:app --reload --port 18000`
- [ ] **Step 6.3：** 构建桌面应用：`cd desktop && npm run build`
- [ ] **Step 6.4：** Git 提交：`git add -A && git commit -m "refactor: restructure project directories"`

---

## 9. 风险与注意事项

### 9.1 import 路径变更风险

所有 Python import 路径变更后必须逐一验证，尤其是：
- `kuakua_agent/main.py` 中的服务初始化
- `kuakua_agent/api/app.py` 中的 router 注册
- 各 `__init__.py` 的 `__all__` 导出
- 测试文件中的 import

### 9.2 前端组件路径

Vue 组件移动后需要检查：
- `router/index.ts` 中的懒加载路径
- `App.vue` 中的直接 import
- `components/settings/SettingsPanel.vue` 中对 `SettingsTrigger` 的引用（现已归入 settings/）

### 9.3 不涉及变更的内容

- 所有业务逻辑代码本身不变
- 数据库 schema 不变
- API 接口不变
- Electron 主进程逻辑不变

---

## 10. 外部依赖独立管理

以下外部依赖已从项目目录中移出，统一存放在 `D:\project\External-ependencies\`：

| 依赖 | 项目内原位置 | 外部新位置 |
|------|------------|-----------|
| ActivityWatch 本体 | `deps/activitywatch/` | `D:\project\External-ependencies\activitywatch` |
| Kokoro-82M 模型权重 | `ckpts/kokoro-v1.1/`（规划中的建议路径） | `D:\project\External-ependencies\kokoro-v1.1` |

### 10.1 说明

- **ActivityWatch**：指 ActivityWatch 服务端本体（aw-server、aw-watcher-window 等），不是项目内的 Python 客户端代码（`services/monitor/activitywatch/` 中的 client.py 等文件仍保留在项目内）。
- **Kokoro-82M 模型**：模型权重文件（~350MB）和音色文件存储在外部路径，项目通过配置项 `kokoro_model_path` 引用该路径。
- 后续如需添加其他大型二进制依赖，也优先放至 `External-ependencies/` 目录。|
