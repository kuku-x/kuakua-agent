# ActivityWatch 状态指示器设计

## 1. 概述

在侧边栏顶部添加 ActivityWatch 连接状态指示器，实时展示 AW 连接状态，提供一键排查和配置入口。

**目标**：
- 用户能在 30 秒内从"看不到数据"到"知道 AW 状态"
- 断连时提供明确的操作路径（重连/日志/配置）

## 2. 视觉设计

### 2.1 状态指示器外观

```
┌─────────────────────────────────┐
│  [●] 已连接           [↻] [⋮]  │
└─────────────────────────────────┘
```

| 状态 | 颜色 | 文案 | 动画 |
|------|------|------|------|
| 已连接 | 绿色 `#22c55e` | "已连接" | 静止 |
| 同步中 | 黄色 `#eab308` | "同步中" | 呼吸动画 |
| 已断开 | 红色 `#ef4444` | "已断开" | 静止 |

### 2.2 状态按钮组
- **[↻] 重连按钮** — 手动触发重连
- **[⋮] 更多按钮** — 展开操作菜单

### 2.3 弹窗设计

```
┌────────────────────────────────────┐
│ ActivityWatch 状态               [×]│
├────────────────────────────────────┤
│ ● 已连接                          │
│   上次同步: 2 分钟前              │
├────────────────────────────────────┤
│ [↻] 立即重连                      │
│ [📋] 查看日志                      │
│ [⚙] 跳转配置                      │
└────────────────────────────────────┘
```

## 3. 组件清单

### 3.1 `AwStatusIndicator.vue`
侧边栏顶部状态指示器组件

**Props:**
- `status: 'connected' | 'syncing' | 'disconnected'`
- `lastSyncTime: Date | null`

**Events:**
- `retry` — 点击重连
- `openLogs` — 点击查看日志
- `openSettings` — 点击跳转配置

**样式：** 紧凑行高，适配侧边栏宽度

### 3.2 `AwStatusPopover.vue`
点击指示器弹出的操作面板

## 4. 后端 API

### `GET /api/activitywatch/status`
返回 AW 连接状态

**Response:**
```json
{
  "status": "connected" | "disconnected",
  "last_sync": "2026-04-30T10:00:00Z" | null,
  "error": null | "连接超时" | "服务未运行"
}
```

## 5. 交互逻辑

### 5.1 启动流程
1. App 启动时立即调用 `/api/activitywatch/status`
2. 根据返回值设置初始状态
3. 若断连，后端自动重试 3 次（间隔 5s），失败后返回 `disconnected`

### 5.2 定时轮询
- 前端每 30 秒轮询一次状态
- 用户可手动点击 [↻] 立即刷新

### 5.3 重连逻辑
- 手动重连：前端调用 `/api/activitywatch/status`，后端尝试连接
- 后端内部断连重试：最多 3 次，间隔 5 秒

### 5.4 弹窗操作
| 操作 | 行为 |
|------|------|
| 立即重连 | 调用 API 重试，更新状态 |
| 查看日志 | 调用 `/api/debug/summary-raw` 或打开日志文件 |
| 跳转配置 | 路由跳转到 `/settings#activitywatch` |

## 6. 文件变更

### 新增文件
- `desktop/src/renderer/components/layout/AwStatusIndicator.vue`
- `desktop/src/renderer/components/layout/AwStatusPopover.vue`

### 修改文件
- `desktop/src/renderer/components/layout/Sidebar.vue` — 顶部添加指示器
- `kuakua_agent/api/activitywatch_proxy_routes.py` — 新增 `/status` 端点
- `desktop/src/renderer/api/index.ts` — 新增 `getAwStatus` 调用

## 7. 验收标准

- [ ] 侧边栏顶部显示 AW 状态指示器
- [ ] 三种状态（绿/黄/红）正确显示
- [ ] 点击指示器弹出操作面板
- [ ] 重连、查看日志、跳转配置三个按钮可用
- [ ] 启动时自动检测状态
- [ ] 30 秒轮询更新状态
- [ ] 断连时显示红色并提示用户
