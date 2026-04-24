# 夸夸Agent前端架构重构设计方案

**日期**: 2026/04/24
**版本**: v1.0
**状态**: 已批准

---

## 一、项目概述与目标

### 1.1 重构背景
当前夸夸Agent前端套用了ChatGPT模板，存在以下问题：
- 布局错乱：主内容区被挤压到侧边栏、内容溢出屏幕
- 样式冲突：不同页面风格不一致，CSS变量管理混乱
- 功能适配失败：部分交互不符合夸夸Agent原生业务逻辑

### 1.2 重构目标
- 布局稳定：无溢出、无错位、无排版错乱
- 风格统一：贴合夸夸Agent温柔暖奶油风产品定位
- 功能完整：所有原生业务正常可用
- 代码清晰：组件拆分合理，样式与逻辑分离

### 1.3 技术约束
- **业务逻辑零改动**：Store、API、类型定义、路由配置全部保留
- **不新增无意义依赖**：基于现有 Vue3 + Vite + Electron 技术栈
- **必须通过打包验证**：`npm run dev` 和 `npx electron-vite build` 均需正常运行

---

## 二、布局架构

### 2.1 整体布局结构
```
┌─────────────────────────────────────────────────────────┐
│  ┌───────────┐  ┌─────────────────────────────────────┐│
│  │  侧边栏    │  │           主内容区                   ││
│  │ 可折叠     │  │  ┌───────────────────────────────┐ ││
│  │           │  │  │      页面内容 (router-view)    │ ││
│  │ 顶部控制   │  │  │                               │ ││
│  │ ───────── │  │  └───────────────────────────────┘ ││
│  │ 今日概览   │  │                                     ││
│  │ ───────── │  │                                     ││
│  │ 功能入口   │  │                                     ││
│  │ 摘/聊/设  │  │                                     ││
│  │ ───────── │  │                                     ││
│  │ 历史会话   │  │                                     ││
│  └───────────┘  └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 2.2 布局规格

| 区域 | 宽度 | 最小宽度 | 最大宽度 | 折叠后宽度 |
|------|------|----------|----------|------------|
| 侧边栏 | 280px | 280px | 280px | 72px |
| 主内容区 | flex: 1 | 0 | - | flex: 1 |

### 2.3 侧边栏内部结构

```
侧边栏 (Sidebar)
├── 顶部控制区 (SidebarHeader)
│   ├── 折叠/展开按钮
│   └── 新建对话按钮
├── 今日概览模块 (TodayOverview)
│   ├── 概览标题
│   └── 数据卡片 (专注/放松/总时长)
├── 功能入口区 (Navigation)
│   ├── 每日摘要
│   ├── 陪伴聊天
│   └── 偏好设置
└── 历史会话列表 (ConversationList)
    ├── 会话项 (可点击切换)
    └── 删除按钮
```

---

## 三、组件库架构

### 3.1 目录结构
```
src/components/
├── base/              # 基础原子组件
│   ├── KuButton.vue   # 按钮
│   ├── KuCard.vue     # 卡片容器
│   ├── KuInput.vue    # 输入框
│   ├── KuBadge.vue    # 标签徽章
│   └── KuSpinner.vue  # 加载 spinner
├── layout/            # 布局组件
│   ├── Sidebar.vue    # 侧边栏
│   ├── SidebarHeader.vue
│   ├── SidebarNav.vue
│   ├── SidebarConversations.vue
│   ├── TodayOverview.vue
│   └── PageContainer.vue
├── summary/           # 摘要相关
│   ├── SummaryCard.vue
│   └── TimePieChart.vue
├── chat/              # 聊天相关
│   ├── ChatBubble.vue
│   ├── Composer.vue
│   ├── MessageList.vue
│   └── QuickPrompts.vue
└── common/           # 通用
    └── GlobalError.vue
```

### 3.2 基础组件规范

#### KuButton
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| variant | 'primary' \| 'secondary' \| 'ghost' | 'secondary' | 按钮变体 |
| size | 'sm' \| 'md' \| 'lg' | 'md' | 尺寸 |
| disabled | boolean | false | 禁用状态 |

#### KuCard
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| padding | 'sm' \| 'md' \| 'lg' | 'md' | 内边距 |
| hoverable | boolean | false | 可悬浮效果 |

#### KuInput
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | 'text' \| 'password' | 'text' | 输入框类型 |
| placeholder | string | '' | 占位文本 |

---

## 四、视觉设计规范

### 4.1 颜色系统

```css
/* 亮色主题 */
:root {
  /* 背景色 */
  --color-bg-primary: #faf7f4;      /* 主背景 - 温暖米白 */
  --color-bg-secondary: #f4ede5;    /* 次背景 - 侧边栏 */
  --color-bg-card: #fffdfb;        /* 卡片背景 */
  --color-bg-elevated: #ffffff;     /* 悬浮层背景 */

  /* 文字色 */
  --color-text-primary: #3d3028;    /* 主要文字 - 深暖棕 */
  --color-text-secondary: #8a7160; /* 次要文字 */
  --color-text-tertiary: #b09a88;  /* 辅助文字 */
  --color-text-inverse: #ffffff;   /* 反色文字 */

  /* 强调色 */
  --color-accent: #c98a69;         /* 主强调色 - 暖橙 */
  --color-accent-hover: #b87a59;   /* 强调色悬浮 */
  --color-accent-soft: rgba(201, 138, 105, 0.12);

  /* 状态色 */
  --color-success: #7a9f6a;        /* 成功 - 柔和绿 */
  --color-warning: #d4a84b;        /* 警告 - 柔和黄 */
  --color-danger: #c06050;         /* 危险 - 柔和红 */

  /* 边框色 */
  --color-border: rgba(119, 104, 87, 0.12);
  --color-border-strong: rgba(119, 104, 87, 0.20);

  /* 阴影 */
  --shadow-sm: 0 2px 8px rgba(177, 140, 100, 0.08);
  --shadow-md: 0 8px 24px rgba(177, 140, 100, 0.12);
  --shadow-lg: 0 16px 48px rgba(177, 140, 100, 0.16);
}
```

### 4.2 字体系统

```css
/* 字体栈 */
--font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI',
               'Microsoft YaHei', 'Noto Sans SC', sans-serif;

/* 字号 */
--font-size-xs: 12px;
--font-size-sm: 13px;
--font-size-base: 15px;
--font-size-lg: 17px;
--font-size-xl: 20px;
--font-size-2xl: 24px;
--font-size-3xl: 30px;
--font-size-4xl: 38px;

/* 行高 */
--line-height-tight: 1.25;
--line-height-normal: 1.6;
--line-height-relaxed: 1.8;

/* 字重 */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### 4.3 间距系统

```css
/* 基础间距单位: 4px */
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
```

### 4.4 圆角系统

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 24px;
--radius-2xl: 32px;
--radius-full: 9999px;
```

### 4.5 动画规范

```css
/* 过渡时长 */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 400ms;

/* 缓动函数 */
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
```

---

## 五、页面设计

### 5.1 每日摘要页 (DailySummary)

#### 布局结构
```
┌─────────────────────────────────────────┐
│  页面标题区                              │
│  "看看你今天的节奏、专注与放松。"          │
│  [刷新摘要按钮]                          │
├─────────────────────────────────────────┤
│  操作按钮区                              │
│  [带着摘要去聊天] [让夸夸鼓励我一下]       │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐  │
│  │  SummaryCard │  │  TimePieChart   │  │
│  │  今日夸夸    │  │  时间分布       │  │
│  │  + 数据统计  │  │                 │  │
│  └─────────────┘  └─────────────────┘  │
├─────────────────────────────────────────┤
│  应用使用列表                            │
│  ┌─────────────────────────────────────┐│
│  │ App1  │ 偏工作 │ 2.5h │ 工作      ││
│  │ App2  │ 偏娱乐 │ 1.5h │ 娱乐      ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

#### 视觉规格
- 页面最大宽度: 960px，居中显示
- 卡片间距: 20px
- 标题字号: 32px (h2)，28px (h3)
- 正文字号: 15px
- 卡片圆角: 24px

### 5.2 陪伴聊天页 (ChatCompanion)

#### 布局结构
```
┌─────────────────────────────────────────┐
│  空状态: 欢迎面板                         │
│  ┌─────────────────────────────────────┐│
│  │ "从今天的状态开始，和夸夸慢慢聊一会儿"  ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ 今日数据摘要 (如果有)                 ││
│  │  总时长 │ 专注 │ 放松 │ 专注度        ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ 快捷对话入口 x3                      ││
│  │ [结合今日摘要聊聊] [想要一点鼓励] ...   ││
│  └─────────────────────────────────────┘│
├─────────────────────────────────────────┤
│  消息流区域 (scrollable)                 │
│  ┌─────────────────────────────────────┐│
│  │ [Avatar] 用户消息                    ││
│  │        [Avatar] 夸夸回复             ││
│  └─────────────────────────────────────┘│
├─────────────────────────────────────────┤
│  输入框区 (固定底部)                      │
│  ┌─────────────────────────────────┐    │
│  │ [textarea 输入框]        [发送]  │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

#### 视觉规格
- 消息气泡: 左侧用户消息，右侧 AI 消息
- 消息间距: 2px (同一对话), 16px (不同对话组)
- 输入框最大高度: 200px
- 发送按钮: 主色调，圆角 14px

### 5.3 偏好设置页 (Settings)

#### 布局结构
```
┌─────────────────────────────────────────┐
│  页面标题区                              │
│  "让夸夸Agent更贴近你的本地使用方式。"     │
├─────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────┐ │
│  │ 设置表单         │  │ 侧边提示卡   │ │
│  │                  │  │              │ │
│  │ [API Key 输入]   │  │ "这里不会    │ │
│  │ [AW地址 输入]    │  │ 改动你的     │ │
│  │ [数据脱敏 开关]  │  │ 业务逻辑"    │ │
│  │                  │  │              │ │
│  │ [保存设置 按钮]  │  │              │ │
│  └─────────────────┘  │ ┌──────────┐ │ │
│                        │ │危险操作区 │ │ │
│                        │ │[删除数据] │ │ │
│                        │ └──────────┘ │ │
│                        └──────────────┘ │
└─────────────────────────────────────────┘
```

---

## 六、实现计划

### 阶段一：基础设施重构
1. 重写 `App.vue` 主布局
2. 建立 CSS 变量体系 (vars.css)
3. 创建基础组件 (KuButton, KuCard, KuInput)

### 阶段二：布局组件
4. 实现 Sidebar 侧边栏组件
5. 实现 TodayOverview 今日概览模块
6. 实现 SidebarNav 导航组件
7. 实现 SidebarConversations 会话列表

### 阶段三：页面重构
8. 重写 DailySummary 每日摘要页
9. 重写 ChatCompanion 陪伴聊天页
10. 重写 Settings 偏好设置页

### 阶段四：优化与验证
11. 统一全局样式
12. 响应式适配
13. 打包验证

---

## 七、文件变更清单

### 新建文件
```
src/renderer/styles/vars.css        # CSS 变量定义
src/renderer/styles/base.css        # 基础样式重置
src/renderer/components/base/       # 基础组件目录
src/renderer/components/layout/     # 布局组件目录
```

### 重写文件
```
src/renderer/App.vue                # 主布局
src/renderer/views/DailySummary.vue # 每日摘要页
src/renderer/views/ChatCompanion.vue# 陪伴聊天页
src/renderer/views/Settings.vue     # 偏好设置页
src/renderer/components/SummaryCard.vue
src/renderer/components/TimePieChart.vue
src/renderer/components/ChatBubble.vue
src/renderer/components/GlobalError.vue
```

### 保留文件 (不修改)
```
src/renderer/store/*.ts             # 所有 Store
src/renderer/api/index.ts           # API 调用
src/renderer/types/api.ts           # 类型定义
src/renderer/router/index.ts       # 路由配置
src/renderer/constants/index.ts     # 常量配置
```

---

## 八、验收标准

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
- [ ] Electron 桌面端正常启动
- [ ] TypeScript 类型检查通过
