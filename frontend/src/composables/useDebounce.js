import { customRef, onScopeDispose } from 'vue'

/**
 * Debounce ref-значения: запись применяется не сразу, а через delay миллисекунд.
 *
 *   const query = useDebounce('', 300)
 *   watch(query, () => refresh())
 *   // в template: <input v-model="query" />
 */
export function useDebounce(value, delay = 300) {
  let timer = null
  let current = value

  const ref = customRef((track, trigger) => ({
    get() {
      track()
      return current
    },
    set(next) {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        current = next
        timer = null
        trigger()
      }, delay)
    },
  }))

  onScopeDispose(() => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  })

  return ref
}

/**
 * Debounce произвольной функции.
 *   const debouncedSave = useDebouncedFn(save, 400)
 */
export function useDebouncedFn(fn, delay = 300) {
  let timer = null

  function debounced(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      fn(...args)
    }, delay)
  }

  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  onScopeDispose(() => debounced.cancel())

  return debounced
}
