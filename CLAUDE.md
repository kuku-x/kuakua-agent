# Kuakua Agent 项目规范

## 项目概述

AI 夸夸 Agent 桌面软件 - 基于 ActivityWatch 的电脑行为监控与 AI 智能分析助手。

## 技术架构

- **后端**: Python FastAPI (`kuakua_agent/`)
- **桌面应用**: Electron + Vue 3 + TypeScript (`desktop/`)
- **外部依赖**: ActivityWatch (`deps/activitywatch/`)
- **语音合成**: Kokoro-82M 本地离线 TTS（`pip install kokoro`）

## 目录结构

```
kuakua-agent/
├── CLAUDE.md              # 本文件
├── pyproject.toml         # Python 项目配置
│
├── kuakua_agent/           # Python FastAPI 后端
│   ├── main.py
│   ├── config.py
│   ├── api/               # API 路由与错误处理
│   ├── core/              # 核心基础设施（logging, tracing, errors）
│   ├── schemas/           # Pydantic 数据模型
│   └── services/          # 业务逻辑服务（四大域：ai_engine, storage_layer, monitor, notification）
│
├── desktop/               # Electron 桌面应用
│   ├── src/
│   │   ├── main/         # Electron 主进程
│   │   ├── preload/      # 预加载脚本
│   │   └── renderer/     # Vue 渲染进程
│   │       ├── api/       # API 调用
│   │       ├── components/# UI 组件（base/, layout/, settings/, business/, widgets/）
│   │       ├── constants/  # 常量配置
│   │       ├── hooks/     # Vue Hooks
│   │       ├── router/    # 路由配置
│   │       ├── store/     # 状态管理
│   │       ├── styles/    # 全局样式
│   │       ├── types/     # TypeScript 类型
│   │       ├── utils/     # 工具函数
│   │       └── views/     # 页面视图
│   └── package.json
│
├── scripts/                # 工具脚本
├── tests/                  # 测试代码
│
├── deps/                  # 外部依赖
│   └── activitywatch/     # ActivityWatch 行为监控
│
└── docs/                  # 项目文档
    ├── PROJECT_DOC.md     # 项目说明
    └── superpowers/       # 开发规划文档
```

## 开发约定

### 后端开发 (Python)
- 使用 FastAPI 框架
- 数据模型使用 Pydantic schemas
- 遵循 `kuakua_agent/` 模块划分

### 桌面应用开发 (Electron/Vue)
- 使用 electron-vite 构建
- Vue 3 + Composition API
- TypeScript 严格模式

### Git 使用
- 统一在 `main` 分支开发
- `.worktrees/` 目录用于隔离功能分支

## 相关链接

- 项目文档: `docs/PROJECT_DOC.md`
- 开发计划: `docs/superpowers/plans/`
- 技术设计: `docs/superpowers/specs/`
