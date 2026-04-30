# 无 API Key 降级体验实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 当用户未配置 API Key 时，提供完整的降级体验：全局拦截不报错 + 首页引导 + 聊天兜底模板夸夸。

**Architecture:** 后端新增 `NoApiKeyError` 和 `has_api_key()` 方法；前端新增检测 composable 和两个降级组件（Banner + 卡片），聊天失败时自动插入模板夸夸。

**Tech Stack:** Vue 3 + TypeScript (前端), FastAPI (后端)

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `kuakua_agent/core/errors.py` | 修改 | 新增 `NoApiKeyError` |
| `kuakua_agent/services/ai_engine/adapter.py` | 修改 | 新增 `has_api_key()` 方法 |
| `desktop/src/utils/praiseTemplates.ts` | 创建 | 模板夸夸数组 + 随机获取函数 |
| `desktop/src/hooks/useApiKeyCheck.ts` | 创建 | API Key 检测 composable |
| `desktop/src/components/business/FallbackPraiseBanner.vue` | 创建 | 首页引导 Banner |
| `desktop/src/components/business/FallbackPraiseCard.vue` | 创建 | 模板夸夸卡片 |
| `desktop/src/views/DailySummary.vue` | 修改 | 集成 Banner 和卡片 |
| `desktop/src/store/chat.ts` | 修改 | 聊天兜底逻辑 |

---

## Task 1: 后端 - 新增 NoApiKeyError

**Files:**
- Modify: `kuakua_agent/core/errors.py`

- [ ] **Step 1: 在 `errors.py` 新增 `NoApiKeyError`**

找到合适位置添加：

```python
class NoApiKeyError(Exception):
    """API Key 未配置时的特定异常"""
    pass
```

- [ ] **Step 2: 提交**

```bash
git add kuakua_agent/core/errors.py
git commit -m "feat: add NoApiKeyError exception"
```

---

## Task 2: 后端 - ModelAdapter 新增 has_api_key()

**Files:**
- Modify: `kuakua_agent/services/ai_engine/adapter.py`

- [ ] **Step 1: 确认 `NoApiKeyError` 已导入**

在文件顶部找到 `from kuakua_agent.core.errors import` 行，确认包含 `NoApiKeyError`。

- [ ] **Step 2: 新增 `has_api_key()` 方法**

在 `ModelAdapter` 类中找到 `__init__` 方法之后，添加：

```python
def has_api_key(self) -> bool:
    """检查是否配置了 API Key"""
    return bool(self.api_key)
```

- [ ] **Step 3: 修改 `_require_api_key()` 使用 `NoApiKeyError`**

找到现有的 `_require_api_key` 方法，将 `raise ValueError(...)` 改为：

```python
def _require_api_key(self) -> None:
    """Raise if no API key is configured"""
    if not self.has_api_key():
        raise NoApiKeyError(
            "API key is not configured. "
            "Please set DEEPSEEK_API_KEY / LLM_API_KEY / ARK_API_KEY "
            "in your environment or .env file."
        )
```

- [ ] **Step 4: 提交**

```bash
git add kuakua_agent/services/ai_engine/adapter.py
git commit -m "feat: add has_api_key method and use NoApiKeyError"
```

---

## Task 3: 前端 - 模板夸夸数组

**Files:**
- Create: `desktop/src/utils/praiseTemplates.ts`

- [ ] **Step 1: 创建 `praiseTemplates.ts`**

```typescript
export const TEMPLATE_PRAISES = [
  "今天也在努力呢，休息一下也没关系哦~",
  "你已经走了很远，给自己点个赞吧",
  "每一天的小进步，都值得被看见",
  "累了就休息，夸夸一直陪着你",
  "相信你已经在最好的路上",
  "不必和别人比较，今天的你比昨天更棒",
  "努力本身就已经很了不起",
  "给自己一首歌的时间放松一下吧",
  "你已经坚持了很久，这本身就很伟大",
  "相信直觉，你做的选择不会错",
  "今天有什么小成就吗？我想听听",
  "记得喝水，记得休息，记得对自己好",
  "你今天也辛苦了",
  "有时候停下脚步，也是前进的一部分",
  "我看见你的努力了，真棒",
]

export function getRandomTemplatePraise(): string {
  return TEMPLATE_PRAISES[Math.floor(Math.random() * TEMPLATE_PRAISES.length)]
}
```

- [ ] **Step 2: 提交**

```bash
git add desktop/src/utils/praiseTemplates.ts
git commit -m "feat: add template praises array and random getter"
```

---

## Task 4: 前端 - API Key 检测 Composable

**Files:**
- Create: `desktop/src/hooks/useApiKeyCheck.ts`

- [ ] **Step 1: 创建 `useApiKeyCheck.ts`**

```typescript
import { ref } from 'vue'
import { getSettings } from '@/api'

export function useApiKeyCheck() {
  const hasApiKey = ref(true)
  const checking = ref(false)

  async function checkApiKey() {
    checking.value = true
    try {
      const res = await getSettings()
      hasApiKey.value = res.data.data?.doubao_api_key_set ?? false
    } catch {
      hasApiKey.value = false
    } finally {
      checking.value = false
    }
  }

  return { hasApiKey, checking, checkApiKey }
}
```

- [ ] **Step 2: 提交**

```bash
git add desktop/src/hooks/useApiKeyCheck.ts
git commit -m "feat: add useApiKeyCheck composable"
```

---

## Task 5: 前端 - FallbackPraiseBanner 组件

**Files:**
- Create: `desktop/src/components/business/FallbackPraiseBanner.vue`

- [ ] **Step 1: 创建 `FallbackPraiseBanner.vue`**

```vue
<template>
  <div v-if="visible" class="fallback-banner">
    <span>未配置 API Key，部分功能不可用</span>
    <button type="button" @click="$emit('goToSettings')">去设置</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean }>()
defineEmits<{ goToSettings: [] }>()
</script>

<style scoped>
.fallback-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: 8px;
  font-size: 13px;
  color: #92400e;
}

.fallback-banner button {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid rgba(234, 179, 8, 0.5);
  border-radius: 4px;
  color: #92400e;
  font-size: 12px;
  cursor: pointer;
}

.fallback-banner button:hover {
  background: rgba(234, 179, 8, 0.1);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add desktop/src/components/business/FallbackPraiseBanner.vue
git commit -m "feat: add FallbackPraiseBanner component"
```

---

## Task 6: 前端 - FallbackPraiseCard 组件

**Files:**
- Create: `desktop/src/components/business/FallbackPraiseCard.vue`

- [ ] **Step 1: 创建 `FallbackPraiseCard.vue`**

```vue
<template>
  <KuCard class="fallback-card">
    <p class="fallback-card__praise">{{ praise }}</p>
    <p class="fallback-card__hint">— 模板夸夸（配置 API Key 解锁更多）</p>
  </KuCard>
</template>

<script setup lang="ts">
import KuCard from '@/components/base/KuCard.vue'
import { getRandomTemplatePraise } from '@/utils/praiseTemplates'

const praise = getRandomTemplatePraise()
</script>

<style scoped>
.fallback-card {
  padding: var(--space-5);
  text-align: center;
}

.fallback-card__praise {
  font-size: 1.1rem;
  color: var(--color-text-primary);
  line-height: 1.6;
  margin-bottom: var(--space-3);
}

.fallback-card__hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add desktop/src/components/business/FallbackPraiseCard.vue
git commit -m "feat: add FallbackPraiseCard component"
```

---

## Task 7: 前端 - DailySummary 集成

**Files:**
- Modify: `desktop/src/views/DailySummary.vue`

- [ ] **Step 1: 添加导入**

找到 `<script setup>` 部分，添加：

```typescript
import FallbackPraiseBanner from '@/components/business/FallbackPraiseBanner.vue'
import FallbackPraiseCard from '@/components/business/FallbackPraiseCard.vue'
import { useApiKeyCheck } from '@/hooks/useApiKeyCheck'

const { hasApiKey, checkApiKey } = useApiKeyCheck()
```

- [ ] **Step 2: 在 `onMounted` 中调用检测**

找到 `onMounted` 钩子，添加：

```typescript
onMounted(() => {
  checkApiKey()
  // ...existing code
})
```

- [ ] **Step 3: 在模板顶部添加 Banner 和卡片**

找到 `<section class="summary-page">` 紧接其下添加：

```vue
<section class="summary-page">
  <!-- Fallback Banner -->
  <FallbackPraiseBanner
    v-if="!hasApiKey"
    :visible="!hasApiKey"
    @go-to-settings="router.push('/settings')"
  />

  <!-- Fallback Praise Card -->
  <FallbackPraiseCard v-if="!hasApiKey" />

  <!-- 现有内容... -->
```

- [ ] **Step 4: 提交**

```bash
git add desktop/src/views/DailySummary.vue
git commit -m "feat: integrate FallbackPraiseBanner and FallbackPraiseCard into DailySummary"
```

---

## Task 8: 前端 - ChatCompanion 聊天兜底逻辑

**Files:**
- Modify: `desktop/src/store/chat.ts`

- [ ] **Step 1: 添加导入**

找到导入部分，添加：

```typescript
import { getRandomTemplatePraise } from '@/utils/praiseTemplates'
import { handleApiError } from '@/utils/error'
```

- [ ] **Step 2: 修改 `sendMessage` 中的错误处理**

找到 catch 块中设置 `session.messages[assistantIndex].content = '抱歉，回复失败了。'` 的位置，替换为：

```typescript
} catch (e: unknown) {
  const errorMessage = handleApiError(e)
  // 检测是否是 API Key 相关错误
  const isApiKeyError = errorMessage.includes('API key') ||
                         errorMessage.includes('API_KEY') ||
                         errorMessage.includes('API密钥')

  if (isApiKeyError) {
    session.messages[assistantIndex].content = getRandomTemplatePraise()
    session.messages[assistantIndex].status = 'sent'
    error.value = null  // 不显示错误提示
  } else {
    error.value = errorMessage
    session.messages[assistantIndex].status = 'failed'
    session.messages[assistantIndex].content = '抱歉，回复失败了。'
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add desktop/src/store/chat.ts
git commit -m "feat: add fallback template praise for chat when API key missing"
```

---

## 验收标准

- [ ] 后端 `has_api_key()` 方法正确检测 Key 配置
- [ ] 后端 `NoApiKeyError` 在 Key 缺失时被正确抛出
- [ ] 首页在无 Key 时显示黄色引导 Banner
- [ ] 首页 Banner 下方显示模板夸夸卡片
- [ ] 聊天消息失败时自动插入模板夸夸（非错误提示）
- [ ] 点击 Banner 可跳转设置页
