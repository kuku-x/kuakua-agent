# 无 API Key 降级体验设计

## 1. 概述

当用户未配置 LLM API Key 时，夸夸 Agent 应提供完整的降级体验：不报错、不卡死、不空白，让用户始终感受到陪伴感。

**目标**：
- 全局拦截：无 Key 时不发起无效网络请求
- 首页引导：明确提示 + 模板夸夸卡片
- 聊天兜底：消息失败时自动回复温柔模板夸夸

## 2. 架构设计

### 2.1 三层防护模型

```
┌─────────────────────────────────────────────┐
│              C 层：全局拦截                  │
│  后端 ModelAdapter.has_api_key()           │
│  前端 useApiKeyCheck() composable           │
│  无 Key → 降级路径，不发请求                │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│              B 层：首页引导                  │
│  FallbackPraiseBanner (黄色弱提示)          │
│  FallbackPraiseCard (模板夸夸卡片)          │
│  位置：DailySummary 顶部                    │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│              A 层：聊天兜底                  │
│  ChatCompanion sendMessage 失败检测         │
│  自动插入模板夸夸作为回复                    │
└─────────────────────────────────────────────┘
```

### 2.2 降级判断逻辑

```
用户操作 → 调用 LLM
    ↓
has_api_key() == true → 正常调用 LLM
    ↓ false
NoApiKeyError → 降级处理
    ↓
前端检测到 NoApiKeyError
    ↓
根据场景选择：
  - 首页 → 显示 Banner + 卡片
  - 聊天 → 插入模板夸夸
```

## 3. 后端变更

### 3.1 新增 NoApiKeyError

```python
# kuakua_agent/core/errors.py

class NoApiKeyError(Exception):
    """API Key 未配置时的特定异常"""
    pass
```

### 3.2 ModelAdapter 新增方法

```python
# kuakua_agent/services/ai_engine/adapter.py

def has_api_key(self) -> bool:
    """检查是否配置了 API Key"""
    return bool(self.api_key)

def _require_api_key(self) -> None:
    """Raise if no API key is configured"""
    if not self.has_api_key():
        raise NoApiKeyError(
            "API key is not configured. "
            "Please set DEEPSEEK_API_KEY / LLM_API_KEY / ARK_API_KEY "
            "in your environment or .env file."
        )
```

## 4. 前端变更

### 4.1 模板夸夸数组

```typescript
// desktop/src/utils/praiseTemplates.ts

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

### 4.2 API Key 检测 Composable

```typescript
// desktop/src/hooks/useApiKeyCheck.ts

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

### 4.3 FallbackPraiseBanner 组件

```vue
<!-- desktop/src/components/business/FallbackPraiseBanner.vue -->
<template>
  <div v-if="visible" class="fallback-banner">
    <span>未配置 API Key，部分功能不可用</span>
    <button @click="$emit('goToSettings')">去设置</button>
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
</style>
```

### 4.4 FallbackPraiseCard 组件

```vue
<!-- desktop/src/components/business/FallbackPraiseCard.vue -->
<template>
  <KuCard class="fallback-card">
    <p class="fallback-card__praise">{{ praise }}</p>
    <p class="fallback-card__hint">— 模板夸夸（配置 API Key 解锁更多）</p>
  </KuCard>
</template>

<script setup lang="ts">
import { getRandomTemplatePraise } from '@/utils/praiseTemplates'

const praise = getRandomTemplatePraise()
</script>
```

### 4.5 DailySummary 集成

在 `DailySummary.vue` 顶部添加 Banner 和卡片：

```vue
<template>
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
  </section>
</template>
```

### 4.6 ChatCompanion 兜底逻辑

修改 `store/chat.ts` 的 `sendMessage`：

```typescript
// 检测到 API Key 缺失时，使用模板夸夸
if (errorMessage.includes('API key') || errorMessage.includes('API_KEY')) {
  session.messages[assistantIndex].content = getRandomTemplatePraise()
  session.messages[assistantIndex].status = 'sent'
} else {
  session.messages[assistantIndex].content = '抱歉，回复失败了。'
  session.messages[assistantIndex].status = 'failed'
}
```

## 5. 文件变更清单

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

## 6. 验收标准

- [ ] 后端 `has_api_key()` 方法正确检测 Key 配置
- [ ] 后端 `NoApiKeyError` 在 Key 缺失时被正确抛出
- [ ] 首页在无 Key 时显示黄色引导 Banner
- [ ] 首页 Banner 下方显示模板夸夸卡片
- [ ] 聊天消息失败时自动插入模板夸夸（非错误提示）
- [ ] 点击 Banner 可跳转设置页
