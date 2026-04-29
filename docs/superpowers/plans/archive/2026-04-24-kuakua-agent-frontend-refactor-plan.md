# 夸夸Agent前端架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重建夸夸Agent前端UI框架，解决布局错乱、样式冲突问题，打造稳定可维护的组件库

**Architecture:**
- 采用「可折叠左侧功能区 + 中间主内容区」的经典桌面端布局
- 建立基于CSS变量的主题系统，支持暖奶油风2.0视觉规范
- 组件拆分：基础组件(base/) + 布局组件(layout/) + 业务组件(summary/chat/)

**Tech Stack:** Vue 3 + TypeScript + CSS Variables + electron-vite

---

## 文件结构规划

### 新建文件
```
src/renderer/styles/
├── vars.css           # CSS变量定义（颜色、字体、间距、圆角、阴影）
└── base.css           # 基础样式重置

src/renderer/components/base/
├── KuButton.vue       # 按钮组件
├── KuCard.vue         # 卡片容器
├── KuInput.vue        # 输入框
└── KuSpinner.vue      # 加载动画

src/renderer/components/layout/
├── AppLayout.vue      # 主布局容器
├── Sidebar.vue        # 侧边栏
├── SidebarHeader.vue  # 侧边栏头部
├── SidebarOverview.vue # 今日概览模块
├── SidebarNav.vue     # 导航菜单
└── SidebarConversations.vue  # 历史会话

src/renderer/components/summary/
└── SummaryCard.vue    # 摘要卡片

src/renderer/components/chat/
├── ChatBubble.vue     # 聊天气泡
├── ChatComposer.vue   # 聊天输入框
└── QuickPrompts.vue   # 快捷语
```

### 重写文件
```
src/renderer/App.vue                    # 主布局入口
src/renderer/views/DailySummary.vue     # 每日摘要页
src/renderer/views/ChatCompanion.vue   # 陪伴聊天页
src/renderer/views/Settings.vue        # 偏好设置页
src/renderer/components/TimePieChart.vue
src/renderer/components/GlobalError.vue
```

### 保留文件（不修改）
```
src/renderer/store/chat.ts
src/renderer/store/summary.ts
src/renderer/store/app.ts
src/renderer/api/index.ts
src/renderer/types/api.ts
src/renderer/router/index.ts
src/renderer/constants/index.ts
```

---

## 任务清单

### 阶段一：基础设施（CSS变量 + 基础样式）

#### Task 1: 创建CSS变量文件
**Files:**
- Create: `src/renderer/styles/vars.css`

- [ ] **Step 1: 创建CSS变量文件**

```css
/* 夸夸Agent视觉设计系统 - v1.0 */

:root {
  /* ==================== 颜色系统 ==================== */

  /* 背景色 */
  --color-bg-primary: #faf7f4;
  --color-bg-secondary: #f4ede5;
  --color-bg-card: #fffdfb;
  --color-bg-elevated: #ffffff;
  --color-bg-sidebar: #f0e6db;

  /* 文字色 */
  --color-text-primary: #3d3028;
  --color-text-secondary: #8a7160;
  --color-text-tertiary: #b09a88;
  --color-text-inverse: #ffffff;

  /* 强调色 */
  --color-accent: #c98a69;
  --color-accent-hover: #b87a59;
  --color-accent-soft: rgba(201, 138, 105, 0.12);
  --color-accent-light: rgba(201, 138, 105, 0.08);

  /* 功能色 */
  --color-success: #7a9f6a;
  --color-success-soft: rgba(122, 159, 106, 0.12);
  --color-warning: #d4a84b;
  --color-danger: #c06050;
  --color-danger-soft: rgba(192, 96, 80, 0.12);

  /* 边框色 */
  --color-border: rgba(119, 104, 87, 0.10);
  --color-border-strong: rgba(119, 104, 87, 0.18);

  /* 阴影 */
  --shadow-xs: 0 1px 3px rgba(177, 140, 100, 0.06);
  --shadow-sm: 0 2px 8px rgba(177, 140, 100, 0.08);
  --shadow-md: 0 8px 24px rgba(177, 140, 100, 0.12);
  --shadow-lg: 0 16px 48px rgba(177, 140, 100, 0.16);

  /* ==================== 字体系统 ==================== */

  --font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI',
               'Microsoft YaHei', 'Noto Sans SC', sans-serif;

  --font-size-xs: 11px;
  --font-size-sm: 13px;
  --font-size-base: 15px;
  --font-size-lg: 17px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 30px;
  --font-size-4xl: 38px;

  --line-height-tight: 1.25;
  --line-height-normal: 1.6;
  --line-height-relaxed: 1.8;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* ==================== 间距系统 ==================== */

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* ==================== 圆角系统 ==================== */

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-2xl: 32px;
  --radius-full: 9999px;

  /* ==================== 动画系统 ==================== */

  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* ==================== 布局系统 ==================== */

  --sidebar-width: 280px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 72px;
  --content-max-width: 960px;
}

/* 深色主题（可选） */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-primary: #1a1512;
    --color-bg-secondary: #231e1a;
    --color-bg-card: #2a2420;
    --color-bg-elevated: #332c28;
    --color-bg-sidebar: #1f1a16;

    --color-text-primary: #f0ebe5;
    --color-text-secondary: #b8a898;
    --color-text-tertiary: #8a7a6a;

    --color-border: rgba(255, 240, 230, 0.08);
    --color-border-strong: rgba(255, 240, 230, 0.15);

    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.20);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.28);
    --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.36);
  }
}
```

- [ ] **Step 2: 提交CSS变量文件**

```bash
git add src/renderer/styles/vars.css
git commit -m "feat(frontend): add CSS design system variables"
```

---

#### Task 2: 创建基础样式重置文件
**Files:**
- Create: `src/renderer/styles/base.css`

- [ ] **Step 1: 创建基础样式文件**

```css
/* 夸夸Agent - 基础样式重置 */

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body {
  min-height: 100vh;
  height: 100%;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

#app {
  min-height: 100vh;
}

button,
input,
textarea,
select {
  font: inherit;
  color: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}

ul,
ol {
  list-style: none;
}

img,
svg {
  display: block;
  max-width: 100%;
}

h1, h2, h3, h4, h5, h6 {
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border-strong);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

/* Focus样式 */
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

- [ ] **Step 2: 在main.ts中引入样式文件**

Modify: `src/renderer/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import '@/renderer/styles/vars.css'
import '@/renderer/styles/base.css'
import { useAppStore } from '@/store/app'

// ... rest of file unchanged
```

- [ ] **Step 3: 提交基础样式文件**

```bash
git add src/renderer/styles/base.css src/renderer/main.ts
git commit -m "feat(frontend): add base CSS reset and import style files"
```

---

### 阶段二：基础组件库

#### Task 3: 创建KuButton组件
**Files:**
- Create: `src/renderer/components/base/KuButton.vue`

- [ ] **Step 1: 创建KuButton组件**

```vue
<template>
  <button
    :class="['ku-button', `ku-button--${variant}`, `ku-button--${size}`, { 'ku-button--disabled': disabled }]"
    :disabled="disabled"
    :type="type"
  >
    <span v-if="loading" class="ku-button__spinner"></span>
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  type?: 'button' | 'submit' | 'reset'
}>()

withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  type?: 'button' | 'submit' | 'reset'
}>(), {
  variant: 'secondary',
  size: 'md',
  disabled: false,
  loading: false,
  type: 'button'
})
</script>

<style scoped>
.ku-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-weight: var(--font-weight-medium);
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}

.ku-button--sm {
  min-height: 32px;
  padding: 0 var(--space-3);
  font-size: var(--font-size-sm);
}

.ku-button--md {
  min-height: 44px;
  padding: 0 var(--space-5);
  font-size: var(--font-size-base);
}

.ku-button--lg {
  min-height: 52px;
  padding: 0 var(--space-6);
  font-size: var(--font-size-lg);
}

.ku-button--primary {
  color: var(--color-text-inverse);
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.ku-button--primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.ku-button--secondary {
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  border-color: var(--color-border);
}

.ku-button--secondary:hover:not(:disabled) {
  background: var(--color-bg-elevated);
  border-color: var(--color-border-strong);
}

.ku-button--ghost {
  color: var(--color-text-secondary);
  background: transparent;
  border-color: transparent;
}

.ku-button--ghost:hover:not(:disabled) {
  color: var(--color-text-primary);
  background: var(--color-accent-soft);
}

.ku-button--danger {
  color: var(--color-text-inverse);
  background: var(--color-danger);
  border-color: var(--color-danger);
}

.ku-button--disabled,
.ku-button--disabled:hover {
  opacity: 0.5;
  cursor: not-allowed;
}

.ku-button__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
```

- [ ] **Step 2: 提交KuButton组件**

```bash
git add src/renderer/components/base/KuButton.vue
git commit -m "feat(frontend): add KuButton base component"
```

---

#### Task 4: 创建KuCard组件
**Files:**
- Create: `src/renderer/components/base/KuCard.vue`

- [ ] **Step 1: 创建KuCard组件**

```vue
<template>
  <div :class="['ku-card', `ku-card--${padding}`, { 'ku-card--hoverable': hoverable }]">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  padding?: 'sm' | 'md' | 'lg'
  hoverable?: boolean
}>(), {
  padding: 'md',
  hoverable: false
})
</script>

<style scoped>
.ku-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-fast) var(--ease-out);
}

.ku-card--sm {
  padding: var(--space-4);
}

.ku-card--md {
  padding: var(--space-6);
}

.ku-card--lg {
  padding: var(--space-8);
}

.ku-card--hoverable:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-strong);
}
</style>
```

- [ ] **Step 2: 提交KuCard组件**

```bash
git add src/renderer/components/base/KuCard.vue
git commit -m "feat(frontend): add KuCard base component"
```

---

#### Task 5: 创建KuInput组件
**Files:**
- Create: `src/renderer/components/base/KuInput.vue`

- [ ] **Step 1: 创建KuInput组件**

```vue
<template>
  <div class="ku-input-wrapper">
    <label v-if="label" class="ku-input__label">{{ label }}</label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="ku-input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <span v-if="hint" class="ku-input__hint">{{ hint }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue?: string
  type?: 'text' | 'password' | 'email'
  placeholder?: string
  label?: string
  hint?: string
  disabled?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()

withDefaults(defineProps<{
  modelValue?: string
  type?: 'text' | 'password' | 'email'
  placeholder?: string
  label?: string
  hint?: string
  disabled?: boolean
}>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  label: '',
  hint: '',
  disabled: false
})
</script>

<style scoped>
.ku-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.ku-input__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.ku-input {
  width: 100%;
  min-height: 48px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.ku-input:focus {
  border-color: var(--color-accent);
  outline: none;
}

.ku-input::placeholder {
  color: var(--color-text-tertiary);
}

.ku-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ku-input__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
```

- [ ] **Step 2: 提交KuInput组件**

```bash
git add src/renderer/components/base/KuInput.vue
git commit -m "feat(frontend): add KuInput base component"
```

---

#### Task 6: 创建KuSpinner组件
**Files:**
- Create: `src/renderer/components/base/KuSpinner.vue`

- [ ] **Step 1: 创建KuSpinner组件**

```vue
<template>
  <div :class="['ku-spinner', `ku-spinner--${size}`]" role="status">
    <span class="ku-spinner__circle"></span>
    <span class="ku-spinner__text" v-if="text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  size?: 'sm' | 'md' | 'lg'
  text?: string
}>(), {
  size: 'md',
  text: ''
})
</script>

<style scoped>
.ku-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
}

.ku-spinner--sm .ku-spinner__circle {
  width: 16px;
  height: 16px;
}

.ku-spinner--md .ku-spinner__circle {
  width: 24px;
  height: 24px;
}

.ku-spinner--lg .ku-spinner__circle {
  width: 40px;
  height: 40px;
}

.ku-spinner__circle {
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: ku-spin 0.8s linear infinite;
}

.ku-spinner__text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

@keyframes ku-spin {
  to { transform: rotate(360deg); }
}
</style>
```

- [ ] **Step 2: 提交KuSpinner组件**

```bash
git add src/renderer/components/base/KuSpinner.vue
git commit -m "feat(frontend): add KuSpinner base component"
```

---

### 阶段三：布局组件

#### Task 7: 创建主布局组件AppLayout
**Files:**
- Create: `src/renderer/components/layout/AppLayout.vue`

- [ ] **Step 1: 创建AppLayout组件**

```vue
<template>
  <div class="app-layout" :class="{ 'app-layout--sidebar-collapsed': sidebarCollapsed }">
    <!-- 移动端遮罩 -->
    <div
      v-if="mobileSidebarOpen"
      class="app-layout__overlay"
      @click="mobileSidebarOpen = false"
    ></div>

    <!-- 侧边栏 -->
    <Sidebar
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileSidebarOpen"
      @toggle="handleSidebarToggle"
    />

    <!-- 主内容区 -->
    <main class="app-layout__main">
      <!-- 顶部栏 -->
      <header class="app-layout__topbar">
        <button
          class="app-layout__menu-btn mobile-only"
          @click="mobileSidebarOpen = true"
          aria-label="打开菜单"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <div class="app-layout__heading">
          <h1>{{ currentHeading }}</h1>
          <p v-if="currentDescription" class="app-layout__desc">{{ currentDescription }}</p>
        </div>
        <div class="app-layout__status">
          <span class="app-layout__status-pill">{{ currentStatus }}</span>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="app-layout__content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

const route = useRoute()
const chatStore = useChatStore()
const summaryStore = useSummaryStore()

const sidebarCollapsed = ref(false)
const mobileSidebarOpen = ref(false)

const currentHeading = computed(() => {
  if (route.path === '/chat') return chatStore.activeSession?.title || '新建对话'
  if (route.path === '/settings') return '偏好设置'
  return '每日摘要'
})

const currentDescription = computed(() => {
  if (route.path === '/chat') return '继续你的陪伴对话，或带着今天的上下文开始新的聊天。'
  if (route.path === '/settings') return '管理豆包 API、ActivityWatch 地址与本地隐私选项。'
  return '查看今天的专注、放松与应用使用情况，快速进入对话陪伴。'
})

const currentStatus = computed(() => {
  if (route.path === '/chat') {
    return chatStore.messages.length === 0
      ? '等待你的第一条消息'
      : `当前共有 ${chatStore.messages.length} 条消息`
  }
  if (route.path === '/settings') return '本地配置页'
  if (summaryStore.summary) return `今日累计 ${summaryStore.summary.total_hours} 小时`
  if (summaryStore.loading) return '正在刷新摘要'
  return '等待摘要数据'
})

watch(() => route.fullPath, () => {
  mobileSidebarOpen.value = false
})

function handleSidebarToggle() {
  if (window.matchMedia('(max-width: 960px)').matches) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
    return
  }
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns var(--duration-normal) var(--ease-out);
}

.app-layout--sidebar-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) 1fr;
}

.app-layout__overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(0, 0, 0, 0.3);
}

.app-layout__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
  overflow: hidden;
}

.app-layout__topbar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  background: linear-gradient(
    to bottom,
    var(--color-bg-primary),
    rgba(250, 247, 244, 0.8),
    transparent
  );
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-layout__menu-btn {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 44px;
  height: 44px;
  padding: 10px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.app-layout__menu-btn span {
  display: block;
  width: 100%;
  height: 2px;
  background: var(--color-text-secondary);
  border-radius: 1px;
}

.app-layout__heading {
  flex: 1;
  min-width: 0;
}

.app-layout__heading h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.app-layout__desc {
  margin-top: var(--space-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.app-layout__status-pill {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  white-space: nowrap;
}

.app-layout__content {
  flex: 1;
  padding: var(--space-6);
  overflow-x: hidden;
}

.mobile-only {
  display: none;
}

@media (max-width: 960px) {
  .app-layout {
    grid-template-columns: 1fr;
  }

  .app-layout__overlay {
    display: block;
  }

  .app-layout__menu-btn {
    display: flex;
  }

  .app-layout__content {
    padding: var(--space-4);
  }

  .mobile-only {
    display: flex;
  }
}
</style>
```

- [ ] **Step 2: 提交AppLayout组件**

```bash
git add src/renderer/components/layout/AppLayout.vue
git commit -m "feat(frontend): add AppLayout main container component"
```

---

#### Task 8: 创建Sidebar侧边栏组件
**Files:**
- Create: `src/renderer/components/layout/Sidebar.vue`

- [ ] **Step 1: 创建Sidebar组件**

```vue
<template>
  <aside
    :class="[
      'sidebar',
      { 'sidebar--collapsed': collapsed },
      { 'sidebar--mobile-open': mobileOpen }
    ]"
  >
    <!-- 侧边栏头部 -->
    <div class="sidebar__header">
      <button
        class="sidebar__toggle"
        @click="$emit('toggle')"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <span class="sidebar__toggle-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="!collapsed" d="M15 18l-6-6 6-6" />
            <path v-else d="M9 18l6-6-6-6" />
          </svg>
        </span>
      </button>
      <button
        v-if="!collapsed"
        class="sidebar__new-chat"
        @click="startNewChat"
      >
        <span class="sidebar__new-chat-plus">+</span>
        <span>新建对话</span>
      </button>
    </div>

    <!-- 今日概览 -->
    <div v-if="!collapsed" class="sidebar__section sidebar__overview">
      <p class="sidebar__section-title">今日概览</p>
      <div class="sidebar__overview-card">
        <template v-if="summaryStore.summary">
          <strong class="sidebar__overview-praise">{{ summaryStore.summary.praise_text }}</strong>
          <div class="sidebar__overview-stats">
            <div class="sidebar__stat">
              <span>专注</span>
              <b>{{ summaryStore.summary.work_hours }}h</b>
            </div>
            <div class="sidebar__stat">
              <span>放松</span>
              <b>{{ summaryStore.summary.entertainment_hours }}h</b>
            </div>
            <div class="sidebar__stat">
              <span>总时长</span>
              <b>{{ summaryStore.summary.total_hours }}h</b>
            </div>
          </div>
        </template>
        <template v-else-if="summaryStore.loading">
          <strong class="sidebar__overview-praise">正在整理今天的行为数据...</strong>
        </template>
        <template v-else>
          <strong class="sidebar__overview-praise">今天的摘要还没有准备好</strong>
        </template>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar__nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sidebar__nav-item"
        :title="collapsed ? item.label : undefined"
      >
        <span class="sidebar__nav-icon">{{ item.icon }}</span>
        <span v-if="!collapsed" class="sidebar__nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 历史会话 -->
    <div class="sidebar__section sidebar__conversations">
      <p v-if="!collapsed" class="sidebar__section-title">
        历史对话
        <span class="sidebar__session-count">{{ chatStore.sessions.length }}</span>
      </p>
      <div class="sidebar__session-list">
        <button
          v-for="session in chatStore.sessions"
          :key="session.id"
          class="sidebar__session-item"
          :class="{ 'sidebar__session-item--active': session.id === chatStore.activeChatId && route.path === '/chat' }"
          @click="openConversation(session.id)"
          :title="collapsed ? session.title : undefined"
        >
          <span class="sidebar__session-icon">聊</span>
          <span v-if="!collapsed" class="sidebar__session-info">
            <strong>{{ session.title }}</strong>
            <small>{{ formatTime(session.updatedAt) }}</small>
          </span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

defineProps<{
  collapsed: boolean
  mobileOpen: boolean
}>()

defineEmits<{
  toggle: []
}>()

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const summaryStore = useSummaryStore()

const navItems = [
  { to: '/', label: '每日摘要', icon: '摘' },
  { to: '/chat', label: '陪伴聊天', icon: '聊' },
  { to: '/settings', label: '偏好设置', icon: '设' },
]

function startNewChat() {
  chatStore.resetChat()
  router.push('/chat')
}

function openConversation(sessionId: string) {
  chatStore.selectChat(sessionId)
  router.push('/chat')
}

function formatTime(date: Date): string {
  const h = `${date.getHours()}`.padStart(2, '0')
  const m = `${date.getMinutes()}`.padStart(2, '0')
  return `${h}:${m}`
}
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  max-width: var(--sidebar-width);
  height: 100vh;
  padding: var(--space-4);
  background: var(--color-bg-sidebar);
  border-right: 1px solid var(--color-border);
  overflow: hidden;
  transition: all var(--duration-normal) var(--ease-out);
}

.sidebar--collapsed {
  width: var(--sidebar-width-collapsed);
  min-width: var(--sidebar-width-collapsed);
  max-width: var(--sidebar-width-collapsed);
}

.sidebar__header {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__toggle:hover {
  background: var(--color-accent-soft);
  color: var(--color-text-primary);
}

.sidebar__toggle-icon {
  display: flex;
  width: 20px;
  height: 20px;
}

.sidebar__toggle-icon svg {
  width: 100%;
  height: 100%;
}

.sidebar__new-chat {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  min-height: 44px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__new-chat:hover {
  background: var(--color-bg-elevated);
  border-color: var(--color-border-strong);
}

.sidebar__new-chat-plus {
  font-size: 18px;
  line-height: 1;
}

.sidebar__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar__section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0 var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.sidebar__session-count {
  font-weight: var(--font-weight-normal);
  color: var(--color-text-tertiary);
}

.sidebar__overview-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.sidebar__overview-praise {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
}

.sidebar__overview-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.sidebar__stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-2);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
}

.sidebar__stat span {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.sidebar__stat b {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  color: var(--color-text-secondary);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__nav-item:hover {
  background: var(--color-accent-soft);
  color: var(--color-text-primary);
}

.sidebar__nav-item.router-link-active {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

.sidebar__nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.sidebar__nav-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.sidebar__conversations {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.sidebar__session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__session-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__session-item:hover {
  background: var(--color-accent-soft);
}

.sidebar__session-item--active {
  background: var(--color-bg-card);
  box-shadow: var(--shadow-sm);
}

.sidebar__session-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-secondary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.sidebar__session-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.sidebar__session-info strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar__session-info small {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 50;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform var(--duration-normal) var(--ease-out);
  }

  .sidebar--mobile-open {
    transform: translateX(0);
  }

  .sidebar--collapsed {
    width: var(--sidebar-width);
    min-width: var(--sidebar-width);
    max-width: var(--sidebar-width);
  }
}
</style>
```

- [ ] **Step 2: 提交Sidebar组件**

```bash
git add src/renderer/components/layout/Sidebar.vue
git commit -m "feat(frontend): add Sidebar layout component"
```

---

### 阶段四：重写App.vue入口

#### Task 9: 重写App.vue
**Files:**
- Modify: `src/renderer/App.vue`

- [ ] **Step 1: 重写App.vue**

```vue
<template>
  <AppLayout />
</template>

<script setup lang="ts">
import AppLayout from '@/renderer/components/layout/AppLayout.vue'
</script>
```

- [ ] **Step 2: 清理App.vue原有样式**

- [ ] **Step 3: 提交App.vue**

```bash
git add src/renderer/App.vue
git commit -m "refactor(frontend): simplify App.vue to use AppLayout"
```

---

### 阶段五：重写视图页面

#### Task 10: 重写DailySummary视图
**Files:**
- Modify: `src/renderer/views/DailySummary.vue`

- [ ] **Step 1: 重写DailySummary页面内容**

页面应包含：
- Hero区域：标题 + 刷新按钮
- 操作按钮：带着摘要去聊天 / 让夸夸鼓励我
- 主内容网格：SummaryCard + TimePieChart
- 应用列表：top_apps 展示

参考设计文档Section 5.1的布局结构

- [ ] **Step 2: 确保布局规范**
- 最大宽度: 960px，居中
- 卡片间距: 20px
- 使用KuCard组件
- 使用KuButton组件

- [ ] **Step 3: 提交DailySummary**

```bash
git add src/renderer/views/DailySummary.vue
git commit -m "refactor(frontend): rewrite DailySummary view with new design system"
```

---

#### Task 11: 重写ChatCompanion视图
**Files:**
- Modify: `src/renderer/views/ChatCompanion.vue`

- [ ] **Step 1: 重写ChatCompanion页面**

页面应包含：
- 空状态：欢迎面板 + 今日摘要卡片 + 快捷对话
- 消息流：ChatBubble 组件展示消息
- 固定底部：ChatComposer 输入框

参考设计文档Section 5.2的布局结构

- [ ] **Step 2: 使用KuButton组件**

- [ ] **Step 3: 提交ChatCompanion**

```bash
git add src/renderer/views/ChatCompanion.vue
git commit -m "refactor(frontend): rewrite ChatCompanion view with new design system"
```

---

#### Task 12: 重写Settings视图
**Files:**
- Modify: `src/renderer/views/Settings.vue`

- [ ] **Step 1: 重写Settings页面**

页面应包含：
- Hero区域：设置页标题
- 两栏布局：设置表单 + 侧边提示
- 表单使用KuInput组件
- 危险操作区：删除数据

参考设计文档Section 5.3的布局结构

- [ ] **Step 2: 提交Settings**

```bash
git add src/renderer/views/Settings.vue
git commit -m "refactor(frontend): rewrite Settings view with new design system"
```

---

### 阶段六：优化组件

#### Task 13: 更新TimePieChart组件
**Files:**
- Modify: `src/renderer/components/TimePieChart.vue`

- [ ] **Step 1: 更新样式使用CSS变量**

将硬编码的颜色替换为CSS变量

- [ ] **Step 2: 提交TimePieChart**

```bash
git add src/renderer/components/TimePieChart.vue
git commit -m "refactor(frontend): update TimePieChart to use CSS variables"
```

---

#### Task 14: 更新GlobalError组件
**Files:**
- Modify: `src/renderer/components/GlobalError.vue`

- [ ] **Step 1: 更新样式使用CSS变量**

- [ ] **Step 2: 提交GlobalError**

```bash
git add src/renderer/components/GlobalError.vue
git commit -m "refactor(frontend): update GlobalError to use CSS variables"
```

---

### 阶段七：验证与测试

#### Task 15: 运行开发服务器验证
**Files:**
- N/A

- [ ] **Step 1: 运行 npm run dev**

```bash
cd desktop
npm run dev
```

- [ ] **Step 2: 验证功能**
- [ ] 侧边栏正常显示
- [ ] 三个路由可正常切换
- [ ] 无控制台错误

---

#### Task 16: 运行打包验证
**Files:**
- N/A

- [ ] **Step 1: 运行打包命令**

```bash
cd desktop
npx electron-vite build
```

- [ ] **Step 2: 验证打包成功**

- [ ] **Step 3: 提交所有更改**

```bash
git add -A
git commit -m "feat(frontend): complete frontend architecture refactor

- Add CSS design system with variables
- Create base component library (KuButton, KuCard, KuInput, KuSpinner)
- Build layout components (AppLayout, Sidebar)
- Rewrite all views with new design system
- All business logic preserved (stores, API unchanged)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## 验收清单

### 功能验收
- [ ] 侧边栏可正常折叠/展开
- [ ] 三个路由页面均可正常访问
- [ ] 每日摘要数据正确显示
- [ ] 聊天消息可正常发送/接收
- [ ] 设置可正常保存

### 视觉验收
- [ ] 无内容溢出屏幕
- [ ] 无元素重叠错位
- [ ] 文字水平排列正常换行
- [ ] 主题色统一为暖奶油风
- [ ] 窗口缩放时布局稳定

### 技术验收
- [ ] `npm run dev` 正常运行
- [ ] `npx electron-vite build` 打包成功
- [ ] TypeScript 类型检查通过
