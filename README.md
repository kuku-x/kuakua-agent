# 夸夸 Agent (Kuakua Agent)

基于 ActivityWatch 的电脑行为监控与 AI 智能分析助手，自动生成每日使用总结、专属暖心夸赞与时间管理建议。

## 功能特性

- **电脑行为监控** - 自动记录软件使用时长、窗口活动、网页浏览
- **每日智能总结** - 分析时间分配、专注时长、碎片化时间
- **专属夸夸功能** - 基于真实行为数据的个性化鼓励与正向激励
- **时间管理建议** - 针对久坐、用眼、效率等问题的实用建议
- **情绪陪伴聊天** - 支持倾诉、安慰、暖心鼓励的 AI 陪伴
- **语音播报** - 使用 Kokoro-82M 本地离线 TTS，支持 100+ 中文音色，温暖女声播报夸夸内容

## 技术栈

- **后端**: Python FastAPI
- **桌面应用**: Electron + Vue 3 + TypeScript
- **行为监控**: ActivityWatch
- **语音合成**: Kokoro-82M（本地离线，Apache 2.0）

## 项目结构

```
kuakua-agent/
├── CLAUDE.md              # 项目规范
├── pyproject.toml         # Python 后端配置
│
├── backend/               # Python FastAPI 后端
│   ├── main.py
│   ├── config.py
│   ├── api/               # API 路由
│   ├── schemas/           # 数据模型
│   └── services/          # 业务逻辑
│
├── desktop/               # Electron 桌面应用
│   ├── src/
│   │   ├── main/         # 主进程
│   │   ├── preload/      # 预加载脚本
│   │   └── renderer/     # 渲染进程 (Vue)
│   │       ├── api/
│   │       ├── components/
│   │       ├── hooks/
│   │       ├── router/
│   │       ├── store/
│   │       ├── types/
│   │       ├── utils/
│   │       └── views/
│   └── package.json
│
├── deps/                  # 外部依赖
│   └── activitywatch/     # ActivityWatch 行为监控
│
└── docs/                  # 项目文档
    ├── PROJECT_DOC.md     # 项目说明
    └── superpowers/       # 开发规划
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 pnpm

### 后端启动

```bash
cd kuakua_agent
pip install -e .
uvicorn kuakua_agent.main:app --reload --port 8001
```

### 桌面应用启动

```bash
cd desktop
npm install
npm run dev
```

### 打包构建

```bash
cd desktop
npm run electron:build
```

## 数据隐私

所有数据均存储在本地电脑，不上传云端，保护用户隐私安全。

## License

MIT
