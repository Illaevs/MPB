import { ref, shallowRef, onScopeDispose } from 'vue'
import { extractApiError, toUserMessage } from '../services/errors'
import { useToast } from './useToast'

/**
 * Универсальная обёртка для одного запроса.
 *
 * const { data, error, loading, refresh, abort } = useApiFetch(
 *   ({ signal }) => api.deals.list({ status: 'open' }, { signal }),
 *   { immediate: true, errorMessage: 'Не удалось загрузить сделки' }
 * )
 *
 * Контракт fetcher: ({ signal }) => Promise<T>.
 * AbortController создаётся внутри; повторный refresh() отменяет предыдущий запрос.
 *
 * Опции:
 *   immediate    — выполнить сразу (по умолчанию true)
 *   initialData  — стартовое значение data
 *   showToast    — показать toast при ошибке (по умолчанию true; false если ошибку обрабатывает потребитель)
 *   errorMessage — fallback-сообщение для toast'а
 *   onError      — кастомный обработчик: (errorInfo) => void
 *   onSuccess    — колбэк после удачного запроса: (result) => void
 */
export function useApiFetch(fetcher, options = {}) {
  const {
    immediate = true,
    initialData = null,
    showToast = true,
    errorMessage = 'Не удалось загрузить данные',
    onError,
    onSuccess,
  } = options

  const toast = useToast()

  const data = shallowRef(initialData)
  const error = ref(null)
  const loading = ref(false)
  let controller = null

  function abort() {
    if (controller) {
      controller.abort()
      controller = null
    }
  }

  async function refresh() {
    abort()
    controller = typeof AbortController !== 'undefined' ? new AbortController() : null
    const signal = controller?.signal
    loading.value = true
    error.value = null
    try {
      const result = await fetcher({ signal })
      data.value = result
      onSuccess?.(result)
      return result
    } catch (e) {
      const info = extractApiError(e)
      if (info.isCancel) return undefined
      error.value = info
      if (onError) {
        onError(info)
      } else if (showToast) {
        const msg = toUserMessage(e, errorMessage)
        if (msg) toast.error(msg)
      }
      throw e
    } finally {
      loading.value = false
      controller = null
    }
  }

  onScopeDispose(() => {
    abort()
  })

  if (immediate) {
    // Не ждём — потребитель сам решит, нужно ли await.
    refresh().catch(() => { /* ошибки уже обработаны выше */ })
  }

  return { data, error, loading, refresh, abort }
}
