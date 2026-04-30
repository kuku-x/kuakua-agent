# Kuakua Agent 项目规范

## 项目概述

AI 夸夸 Agent 桌面软件 - 基于 ActivityWatch 的电脑行为监控与 AI 智能分析助手。

## 技术架构

- **后端**: Python FastAPI (`kuakua_agent/`)
- **桌面应用**: Electron + Vue 3 + TypeScript (`desktop/`)
- **外部依赖**: ActivityWatch (`deps/activitywatch/`)
- **语音合成**: Fish Audio（云端高质量，主用）+ Kokoro-82M（本地离线，备用）

## 目录结构

```
kuakua-agent/
├── CLAUDE.md              # 本文件
├── pyproject.toml         # Python 项目配置
│
├── kuakua_agent/           # Python FastAPI 后端
│   ├── main.py
│   ├── config.py
│   ├── api/               # API 路由（routes + 子路由模块）
│   ├── core/              # 核心基础设施（logging, tracing, errors）
│   ├── schemas/           # Pydantic 数据模型
│   ├── services/          # 业务逻辑服务
│   │   ├── ai_engine/     # AI 引擎（模型适配、聊天、上下文、晚间总结、LangGraph 工作流）
│   │   ├── storage_layer/ # 持久化层（SQLite, milestone, preference, 聊天历史）
│   │   ├── monitor/       # 行为监控（ActivityWatch 调度、行为检测、总结、手机使用）
│   │   ├── notification/  # 通知与语音（系统通知、FishTTS、KokoroTTS、FallbackTTS）
│   │   ├── mcp/           # MCP 工具协议客户端/服务端
│   │   ├── integrations/  # 集成健康检查（ActivityWatch, Kokoro, Weather）
│   │   └── user_behavior/ # 用户行为持久化与汇总
│   └── utils/             # 共享工具函数（分类、时间解析、App 名称规范化）
│
├── desktop/               # Electron 桌面应用
│   ├── src/
│   │   ├── main/         # Electron 主进程
│   │   ├── preload/      # 预加载脚本
│   │   └── renderer/     # Vue 渲染进程
│   │       ├── api/       # API 调用层
│   │       ├── components/# UI 组件（base/, layout/, settings/, business/, widgets/）
│   │       ├── constants/  # 常量配置
│   │       ├── hooks/     # Vue Hooks
│   │       ├── router/    # 路由配置
│   │       ├── store/     # 状态管理（Pinia）
│   │       ├── styles/    # 全局样式
│   │       ├── types/     # TypeScript 类型定义
│   │       ├── utils/     # 工具函数（格式化、错误处理、数据校验）
│   │       └── views/     # 页面视图
│   └── package.json
│
├── data/                  # 运行时数据文件
│   ├── fish_audio_voices.json  # Fish Audio 音色缓存
│   └── tts_samples/       # TTS 测试音频样本
│
├── scripts/                # 工具脚本
│   ├── test_kokoro_tts.py      # TTS 回退测试
│   ├── fish_audio_voices.py    # Fish Audio 音色管理（list/test）
│   └── ...
│
├── tests/                  # 测试代码
├── deps/                  # 外部依赖
│   └── activitywatch/     # ActivityWatch 行为监控
└── docs/                  # 项目文档
```

## 开发约定

### 后端开发 (Python)
- 使用 FastAPI 框架，通过 `lifespan` 上下文管理器管理启动/停止生命周期
- 数据模型使用 Pydantic schemas
- 共享工具函数集中在 `kuakua_agent/utils/shared.py`，避免跨模块重复
- 数据库访问通过 `Database.get_conn()` 公开方法，禁止访问 `._db` 私有属性
- 延迟导入重量级依赖（如 `langgraph`）放在函数内部，避免阻塞模块加载

### 桌面应用开发 (Electron/Vue)
- 使用 electron-vite 构建
- Vue 3 + Composition API
- TypeScript 严格模式
- 前后端通信使用 axios（REST）+ WebSocket（实时推送）

### TTS 语音播报
- **Fish Audio**（主用）：云端高质量 TTS，需配置 `FISH_AUDIO_API_KEY` 和 `fish_audio_voice_id`
- **Kokoro-82M**（备用）：本地离线 TTS，无需联网
- `FallbackTTS` 根据 `tts_engine` 偏好自动选择：fish_audio 优先 → 失败回退 kokoro
- 音色管理：`data/fish_audio_voices.json` 存本地缓存，脚本拉取 API 更新

### API 调试
- `POST /api/debug/trigger-praise` — 手动触发夸夸 + TTS 测试
- `GET /api/debug/summary-raw` — 查看原始 ActivityWatch 数据

### Git 使用
- 统一在 `main` 分支开发
- `.worktrees/` 目录用于隔离功能分支

## 目录重构规范

**触发口令**: `帮我按项目规范重构目录` / `整理项目结构` / `规范化项目目录`

### 1 强制命名规则

1. 所有文件夹、文件统一使用 **小写蛇形命名** `snake_case`
2. 禁止驼峰、大写、随意简写、语义模糊命名
3. 所有目录必须见名知意，附带一行中文用途说明
4. 抽象难懂命名强制映射：

| 旧命名 | 新命名 | 用途 |
|--------|--------|------|
| `brain` | `ai_engine` | AI 引擎 |
| `memory` | `storage_layer` | 持久化层 |
| `output` | `notification` | 通知与语音 |
| `usage` | `user_behavior` | 用户行为 |
| `tools` | `scripts` | 工具脚本 |

### 2 目录架构强制约束

1. 后端统一根目录固定为 `kuakua_agent`，全局和文档 `backend` 命名对齐
2. `services` 只保留四大业务域：**ai**、**storage**、**monitor**、**notify**，合并过深嵌套、拆分过细文件
3. 层级扁平化：能二级不三级，能三级不四级，禁止无效多层嵌套
4. **不改动任何业务代码逻辑、不删功能**，只做目录迁移、重命名、合并、清理

### 3 必须执行清理项

1. 输出【无用可删除文件/文件夹清单】并附带删除理由
2. 输出【旧混乱目录 → 新规范名称】对照表
3. 合并职责重叠、拆分过细、命名混乱的目录
4. `data` 目录只保留业务 JSON 数据，全部日志文件清理
5. 前端 Vue 严格分层：`components` / `views` / `hooks` / `store` / `utils`，拆分基础组件与业务页面
6. `docs` 归档零散带日期规划文档，只保留核心架构、接口、规范文档
7. `tools` 统一重命名为 `scripts`，整合所有工具/测试/代理脚本
8. 剔除冗余：`egg-info`、`.vscode`、`.claude`、日志、模型权重、二进制文件移出业务仓库

### 4 输出固定格式（必须按顺序输出）

1. **无用文件&文件夹删除清单**（带理由）
2. **旧混乱目录 → 新规范命名对照表**
3. **文件合并 & 目录精简迁移方案**
4. **全新完整规范化目录树**（每一项带中文注释用途）
5. **分步可直接执行的迁移改造操作步骤**

### 5 额外约束

- 全程保持原有业务功能完全不变
- 只做目录结构、命名、合并、冗余清理
- 不新增自定义配色、不改动代码业务逻辑
- 所有目录注释清晰，适合 VSCode 直接对照整改

## 相关链接

- 项目文档: `docs/PROJECT_DOC.md`
- 开发计划: `docs/superpowers/plans/`
- 技术设计: `docs/superpowers/specs/`
