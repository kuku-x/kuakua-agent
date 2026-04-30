# P1 功能代码审查报告

> 日期：2026-04-30 | 审查维度：状态管理、定时轮询、组件生命周期、初始化时机、异常兜底、UI状态同步、重复请求、内存泄漏

## 问题总览

| 严重度 | 数量 | 关键词 |
|--------|------|--------|
| 🔴🔴 致命 | 4 | anomalies 字段丢失、GlobalError 永不渲染、WebSocket 重连死循环、多连接泄漏 |
| 🔴 严重 | 6 | 异步竞态无 AbortController、监听器泄漏、重复请求、请求堆积 |
| 🟡 一般 | 12 | 死代码、类型不规范、响应格式不一致、组件过大 |

---

## 🔴🔴 致命问题

### 1. `normalizeSummary` 丢弃 `anomalies` 字段（影响功能 1、4）

**文件**: `utils/validation.ts:99-128`
**影响**: 异常日提醒功能完全失效，`SummaryCard.vue` 的 anomalies 区块永不渲染

```typescript
// 当前代码缺少 anomalies 映射
return {
  date: ...,
  total_hours: ...,
  // ❌ 没有 anomalies: asStringArray(item.anomalies)
}
```

### 2. `GlobalError` 组件是僵尸代码（影响功能 5）

**文件**: `store/app.ts`, `utils/error.ts`
**影响**: 全局错误 UI 永远空白。`appStore.setGlobalError()` 在整个代码库中零调用。

### 3. WebSocket 重连死循环（影响功能 3）

**文件**: `hooks/useWebSocket.ts:40-43`
**影响**: `disconnect()` 调用 `ws.close()` → 触发 `onclose` → 重新调度 `connect()`，断开形同虚设。

### 4. WebSocket 多实例泄漏（影响功能 3）

**文件**: `hooks/useWebSocket.ts:81-82`
**影响**: 每次调用 `useWebSocket()` 都创建独立连接，无单例保护。

---

## 🔴 严重问题

### 5. WeeklyReview 无 AbortController
### 6. AppLayout praise_push 监听器未清理
### 7. AppLayout 和 ChatCompanion 重复 fetchTodaySummary
### 8. AppLayout setInterval 请求堆积风险
### 9. TTS 测试无竞态控制
### 10. `handleApiError` 404 映射误判

---

## 🟡 一般问题

- `useChat.ts`、`useSummary.ts` 是死代码
- `api/praise.ts` 纯转发无价值
- WeeklyReview 类型定义在组件内部
- SettingsPanelContent 1250 行过大
- messages 数组无限增长
- `summaryStore` 无请求去重
- TTS 响应格式与全局规范不一致

---

## 修复文件清单

1. `utils/validation.ts` — 补充 anomalies 字段
2. `hooks/useWebSocket.ts` — 单例 + 断开标志位 + 内存安全
3. `store/app.ts` + `utils/error.ts` — 打通全局错误链路
4. `views/WeeklyReview.vue` — AbortController + 保留旧数据 + 类型规范化
5. `components/layout/AppLayout.vue` — 去重请求 + 递归轮询 + 清理监听器
6. `components/settings/SettingsPanelContent.vue` — TTS 竞态控制 + 响应格式统一
