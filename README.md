# 夸夸 Agent (Kuakua Agent)

基于 ActivityWatch 的电脑行为监控与 AI 智能分析桌面助手。自动追踪每日电脑使用数据，结合大模型生成个性化暖心夸赞、时间管理建议和晚间总结，支持 AI 陪伴聊天。

## 功能

### 行为监控
- 自动采集电脑软件使用时长、窗口切换记录
- 智能区分工作 / 娱乐 / 其他应用类别
- 支持手机使用数据同步（通过 Android 端采集上传）
- ActivityWatch 连接状态实时可视

### AI 智能分析
- **每日摘要** — 自动生成当日专注分、时间分配、高频应用排行
- **专属夸夸** — 基于真实使用数据生成个性化鼓励，不空洞不油腻
- **时间线** — 按小时展示全天应用使用分布，可视化今天是怎么展开的
- **每周复盘** — 7 天数据汇总 + 每日分布条形图 + AI 生成周报文本
- **晚间总结** — 每晚定时生成当天完整总结，桌面通知提醒

### AI 陪伴聊天
- 流式对话，逐字输出回复
- 自动带入每日摘要上下文，让 AI 了解你今天做了什么
- 快捷启动语：结合摘要聊、获取鼓励、整理行动
- 多会话管理，新建 / 切换对话

### 语音播报 (TTS)
- **Fish Audio**（主用）— 云端高质量语音合成，音质接近真人
- **Kokoro-82M**（备用）— 本地离线 TTS，无需联网，支持 42 种中文音色
- 自动故障转移：Fish 不可用时无缝切换 Kokoro
- 设置页支持一键试听，实时切换音色和语速

### 隐私保护
- 所有行为数据本地存储（SQLite），不上传云端
- 数据脱敏开关 — 隐藏敏感应用名称
- 一键清除全部本地数据

## 技术架构

| 层 | 技术 |
|----|------|
| 桌面应用 | Electron + Vue 3 + TypeScript + Pinia |
| 后端 API | Python FastAPI + Pydantic v2 |
| 行为采集 | ActivityWatch（本地服务） |
| AI 引擎 | DeepSeek / 豆包等大模型，支持 LangGraph 工作流 |
| 数据存储 | SQLite（aiosqlite） |
| 语音合成 | Fish Audio API + Kokoro-82M 本地推理 |
| 实时推送 | WebSocket（夸夸推送、流式聊天） |
| 构建工具 | electron-vite + Vite |

## 项目结构

```
kuakua-agent/
├── kuakua_agent/                  # Python FastAPI 后端
│   ├── main.py                    # 应用入口
│   ├── config.py                  # 配置管理（环境变量 + .env）
│   ├── api/                       # API 路由、异常处理、CORS
│   ├── core/                      # 日志、追踪、错误码
│   ├── schemas/                   # Pydantic 数据模型
│   └── services/                  # 业务逻辑
│       ├── ai_engine/             # AI 引擎（模型适配、聊天、摘要、周报、LangGraph）
│       ├── storage_layer/         # 持久化（SQLite、偏好设置、里程碑）
│       ├── monitor/               # 行为监控（ActivityWatch 调度、异常检测、总结）
│       ├── notification/          # 通知与语音（系统通知、FishTTS、KokoroTTS）
│       ├── mcp/                   # MCP 工具协议
│       ├── integrations/          # 集成健康检查
│       └── user_behavior/         # 用户行为持久化
│
├── desktop/                       # Electron 桌面应用
│   ├── src/
│   │   ├── main/                  # Electron 主进程
│   │   ├── preload/               # 预加载脚本
│   │   └── renderer/              # Vue 3 渲染进程
│   │       ├── api/               # API 调用层（axios + fetch SSE）
│   │       ├── components/        # UI 组件（base / layout / business / widgets / settings）
│   │       ├── hooks/             # Vue Hooks（useChat / useSummary / useWebSocket / useWeatherWidget）
│   │       ├── router/            # 路由配置
│   │       ├── store/             # 状态管理（Pinia）
│   │       ├── styles/            # 全局样式
│   │       ├── types/             # TypeScript 类型
│   │       ├── utils/             # 工具函数（格式化 / 错误处理 / 数据校验）
│   │       └── views/             # 页面视图
│   └── package.json
│
├── data/                          # 运行时数据（音色缓存、TTS 样本）
├── scripts/                       # 工具脚本（TTS 测试、音色管理）
├── tests/                         # 测试代码
├── docs/                          # 项目文档
├── deps/activitywatch/            # ActivityWatch 本地服务
├── pyproject.toml                 # Python 项目配置
├── CLAUDE.md                      # 工程规范
└── README.md
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- ActivityWatch（本地运行在 `localhost:5600`）

### 1. 启动 ActivityWatch

```bash
cd deps/activitywatch
python aw-server/aw-server/main.py
```

或下载 [ActivityWatch 官方版本](https://activitywatch.net/downloads/) 并启动。

### 2. 配置环境变量

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx
LLM_MODEL_ID=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
FISH_AUDIO_API_KEY=    # 可选，使用 Fish Audio TTS 时需要
```

### 3. 启动后端

```bash
pip install -e .
uvicorn kuakua_agent.main:app --reload --port 8001
```

API 文档自动生成在 `http://localhost:8001/docs`。

### 4. 启动桌面应用

```bash
cd desktop
npm install
npm run dev
```

桌面应用运行在 `http://localhost:5175`，同时打开 Electron 窗口。

### 打包构建

```bash
cd desktop
npm run electron:build
```

输出在 `desktop/release/` 目录。

## 开发

### API 调试

| 端点 | 说明 |
|------|------|
| `POST /api/debug/trigger-praise` | 手动触发夸夸 + TTS 测试 |
| `POST /api/debug/test-tts` | TTS 语音试听 |
| `GET /api/debug/summary-raw` | 查看原始 ActivityWatch 数据 |
| `GET /api/summary/timeline` | 今日行为时间线 |

### 代码规范

详见 `CLAUDE.md`。关键约定：

- 统一使用 `snake_case` 命名
- 后端延迟导入重量级依赖（如 `langgraph`）
- 数据库访问通过 `Database.get_conn()` 公开方法
- 前端 Vue 3 Composition API + TypeScript 严格模式
- 所有 API 响应使用 `ApiResponse<T>` 标准包装

## License

MIT
