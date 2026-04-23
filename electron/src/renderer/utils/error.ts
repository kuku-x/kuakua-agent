import { ERROR_MESSAGES } from '@/constants'

export function handleApiError(error: unknown): string {
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
      return ERROR_MESSAGES.ACTIVITYWATCH_NOT_RUNNING
    case 500:
      return data?.error?.message || ERROR_MESSAGES.UNKNOWN_ERROR
    default:
      return data?.error?.message || data?.detail || data?.message || ERROR_MESSAGES.UNKNOWN_ERROR
  }
}

export function showError(message: string): void {
  console.error(message)
}
