import { ERROR_MESSAGES } from '@/constants'

export interface ApiErrorContext {
  /** 区分错误来源，用于更精准的提示文案 */
  source?: 'activitywatch' | 'chat' | 'summary' | 'settings' | 'general'
}

export function handleApiError(error: unknown, context: ApiErrorContext = {}): string {
  if (!error || typeof error !== 'object') {
    return ERROR_MESSAGES.UNKNOWN_ERROR
  }

  const err = error as {
    response?: {
      status?: number
      data?: { detail?: string; message?: string; error?: { message?: string } }
    }
    message?: string
  }

  if (!err.response) {
    return err.message || ERROR_MESSAGES.NETWORK_ERROR
  }

  const status = err.response.status
  const data = err.response.data

  switch (status) {
    case 400:
    case 422:
      return data?.error?.message || data?.detail || data?.message || '请求参数错误'
    case 401:
      return ERROR_MESSAGES.API_KEY_NOT_SET
    case 404:
      // 根据 context 给出更精准的提示
      if (context.source === 'activitywatch') {
        return ERROR_MESSAGES.ACTIVITYWATCH_NOT_RUNNING
      }
      return data?.error?.message || data?.detail || data?.message || '请求的资源不存在'
    case 500:
    case 502:
    case 503:
      return data?.error?.message || ERROR_MESSAGES.UNKNOWN_ERROR
    default:
      return data?.error?.message || data?.detail || data?.message || ERROR_MESSAGES.UNKNOWN_ERROR
  }
}

/**
 * 上报全局错误 — 同时 console 日志 + 写入全局 error store（如果可用）。
 * 用于那些没有局部 error UI 的调用场景（如 AppLayout 后台轮询）。
 */
export function reportGlobalError(message: string): void {
  console.error('[GlobalError]', message)
  // 延迟 import 避免循环依赖，且仅在客户端环境调用
  try {
    // 使用动态 import 打破循环引用
    import('@/store/app').then(({ useAppStore }) => {
      useAppStore().setGlobalError(message)
    }).catch(() => {
      // Pinia 未就绪时静默失败
    })
  } catch {
    // 模块加载失败时静默
  }
}
