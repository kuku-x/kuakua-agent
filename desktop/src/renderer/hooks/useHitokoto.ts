import { ref, watch } from 'vue'

export interface HitokotoQuote {
  id: number
  hitokoto: string
  type: string
  from: string
  from_who: string | null
  creator: string
  created_at: string
}

export interface HitokotoCategory {
  label: string
  code: string
}

export const HITOKOTO_CATEGORIES: HitokotoCategory[] = [
  { label: '文学', code: 'd' },
  { label: '影视', code: 'h' },
  { label: '诗词', code: 'i' },
  { label: '网易云', code: 'j' },
  { label: '哲学', code: 'k' },
  { label: '原创', code: 'e' },
  { label: '情话', code: 'l' },
]

const HITOKOTO_TYPE_KEY = 'kuakua_hitokoto_type'
const HITOKOTO_CACHE_DATE_KEY = 'kuakua_hitokoto_date'
const HITOKOTO_CACHE_KEY = 'kuakua_hitokoto_cache'

const FALLBACK_QUOTES: HitokotoQuote[] = [
  { id: 1, hitokoto: '今天已经很棒了，记得给自己一个微笑。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 2, hitokoto: '休息是为了走更远的路，你值得片刻安静。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 3, hitokoto: '每一个小小的进步，都是成长路上的闪光。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 4, hitokoto: '今天的你，比昨天又进步了一点点。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 5, hitokoto: '别忘了，你也在闪闪发光呀。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 6, hitokoto: '慢一点也没关系，每朵花都有自己的花期。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 7, hitokoto: '今天辛苦了，给自己泡杯热茶吧。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 8, hitokoto: '你已经做得很好了，真的。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 9, hitokoto: '偶尔停下来，也是一种前进。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
  { id: 10, hitokoto: '今天也辛苦啦，明天继续一起加油。', type: 'f', from: '内心', from_who: null, creator: 'system', created_at: '0' },
]

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function getTodayString(): string {
  return new Date().toISOString().split('T')[0]
}

export function getSavedCategory(): string {
  return localStorage.getItem(HITOKOTO_TYPE_KEY) || 'd'
}

export function saveCategory(code: string): void {
  localStorage.setItem(HITOKOTO_TYPE_KEY, code)
}

export function useHitokoto() {
  const quote = ref<HitokotoQuote | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentCategory = ref(getSavedCategory())

  function getCachedDate(): string | null {
    return localStorage.getItem(HITOKOTO_CACHE_DATE_KEY)
  }

  function setCache(nextQuote: HitokotoQuote): void {
    localStorage.setItem(HITOKOTO_CACHE_KEY, JSON.stringify(nextQuote))
    localStorage.setItem(HITOKOTO_CACHE_DATE_KEY, getTodayString())
  }

  function getCache(): HitokotoQuote | null {
    if (getCachedDate() !== getTodayString()) {
      return null
    }

    const cached = localStorage.getItem(HITOKOTO_CACHE_KEY)
    if (!cached) {
      return null
    }

    try {
      return JSON.parse(cached)
    } catch {
      return null
    }
  }

  function getRandomFallback(): HitokotoQuote {
    return FALLBACK_QUOTES[Math.floor(Math.random() * FALLBACK_QUOTES.length)]
  }

  async function fetchQuote(forceRefresh = false): Promise<void> {
    if (!forceRefresh) {
      const cached = getCache()
      if (cached) {
        quote.value = cached
        return
      }
    }

    loading.value = true
    error.value = null

    try {
      const url = `https://v1.hitokoto.cn?c=${currentCategory.value}&encode=json`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      // XSS 防护：对所有外部来源的文本进行 HTML 转义
      quote.value = {
        id: data.id || 0,
        hitokoto: escapeHtml(data.hitokoto || ''),
        type: data.type || 'f',
        from: escapeHtml(data.from || '未知'),
        from_who: data.from_who ? escapeHtml(data.from_who) : null,
        creator: data.creator || 'unknown',
        created_at: data.created_at || '0',
      }

      setCache(quote.value)
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : '获取失败'
      quote.value = getRandomFallback()
    } finally {
      loading.value = false
    }
  }

  async function refreshQuote(): Promise<void> {
    await fetchQuote(true)
  }

  function setCategory(code: string): void {
    currentCategory.value = code
    saveCategory(code)
    void fetchQuote(true)
  }

  watch(currentCategory, (newCode) => {
    saveCategory(newCode)
  })

  return {
    quote,
    loading,
    error,
    currentCategory,
    fetchQuote,
    refreshQuote,
    setCategory,
  }
}
