/**
 * Единая работа с ошибками axios/api.
 *
 * Бэкенд (FastAPI) возвращает структуру:
 *   { detail: "..." } | { detail: [{loc, msg, type}, ...] } | { detail: { code, message } }
 *
 * Цель — превратить любую ошибку axios или сетевой/абортовый сбой в
 * стабильную форму, удобную для UI:
 *   { status, code, detail, message, isCancel, isNetwork, raw }
 */

export function extractApiError(error) {
  if (!error) {
    return {
      status: 0,
      code: null,
      detail: null,
      message: 'Неизвестная ошибка',
      isCancel: false,
      isNetwork: false,
      raw: null,
    }
  }

  // axios cancel / native AbortError
  const isCancel = Boolean(
    error.code === 'ERR_CANCELED' ||
    error.name === 'CanceledError' ||
    error.name === 'AbortError' ||
    error.__CANCEL__ === true
  )

  const response = error.response
  const status = response?.status ?? 0
  const data = response?.data

  let code = null
  let detail = null
  let message = null

  if (data && typeof data === 'object') {
    if (typeof data.detail === 'string') {
      detail = data.detail
      message = data.detail
    } else if (Array.isArray(data.detail)) {
      // Pydantic validation errors
      detail = data.detail
      const first = data.detail[0]
      if (first?.msg) {
        const loc = Array.isArray(first.loc) ? first.loc.filter((p) => p !== 'body').join('.') : ''
        message = loc ? `${loc}: ${first.msg}` : first.msg
      } else {
        message = 'Ошибка валидации'
      }
    } else if (data.detail && typeof data.detail === 'object') {
      detail = data.detail
      code = data.detail.code ?? null
      message = data.detail.message ?? data.detail.detail ?? null
    } else if (typeof data.message === 'string') {
      message = data.message
    }
    code = code ?? data.code ?? null
  } else if (typeof data === 'string' && data.trim()) {
    detail = data
    message = data
  }

  const isNetwork = !response && !isCancel

  if (!message) {
    if (isCancel) message = 'Запрос отменён'
    else if (isNetwork) message = 'Нет связи с сервером'
    else if (status === 401) message = 'Требуется авторизация'
    else if (status === 403) message = 'Недостаточно прав'
    else if (status === 404) message = 'Не найдено'
    else if (status === 409) message = 'Конфликт состояния'
    else if (status === 422) message = 'Ошибка валидации'
    else if (status >= 500) message = 'Ошибка сервера'
    else message = error.message || 'Неизвестная ошибка'
  }

  return {
    status,
    code,
    detail,
    message,
    isCancel,
    isNetwork,
    raw: error,
  }
}

export function toUserMessage(error, fallback = 'Произошла ошибка') {
  const info = extractApiError(error)
  if (info.isCancel) return null
  return info.message || fallback
}

export function isCancel(error) {
  return extractApiError(error).isCancel
}

export function isNetworkError(error) {
  return extractApiError(error).isNetwork
}
