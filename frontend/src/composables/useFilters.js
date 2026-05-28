import { reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * Реактивный набор фильтров с опциональной синхронизацией в query string.
 *
 *   const filters = useFilters({
 *     search: '',
 *     status: null,
 *     responsibleId: null,
 *   }, { syncQuery: true })
 *
 *   const params = computed(() => buildParams(filters.state))
 *
 * Пустые/null/undefined/'' значения не попадают в query.
 */
export function useFilters(initial = {}, options = {}) {
  const { syncQuery = false, queryKeyMap = {} } = options

  const route = syncQuery ? useRoute() : null
  const router = syncQuery ? useRouter() : null

  const state = reactive({ ...initial })

  if (syncQuery && route) {
    for (const key of Object.keys(initial)) {
      const qKey = queryKeyMap[key] || key
      const raw = route.query?.[qKey]
      if (raw === undefined) continue
      if (typeof initial[key] === 'number') {
        const num = Number(raw)
        state[key] = Number.isFinite(num) ? num : initial[key]
      } else if (typeof initial[key] === 'boolean') {
        state[key] = raw === 'true' || raw === '1'
      } else {
        state[key] = String(raw)
      }
    }
  }

  function reset() {
    for (const key of Object.keys(initial)) {
      state[key] = initial[key]
    }
  }

  function set(patch) {
    Object.assign(state, patch)
  }

  function isEmpty(value) {
    return value === null || value === undefined || value === '' ||
      (Array.isArray(value) && value.length === 0)
  }

  if (syncQuery && router) {
    watch(state, () => {
      const query = { ...route.query }
      for (const key of Object.keys(initial)) {
        const qKey = queryKeyMap[key] || key
        const value = state[key]
        if (isEmpty(value) || value === initial[key]) {
          delete query[qKey]
        } else {
          query[qKey] = String(value)
        }
      }
      router.replace({ query }).catch(() => {})
    }, { deep: true })
  }

  return { state, set, reset, isEmpty }
}
