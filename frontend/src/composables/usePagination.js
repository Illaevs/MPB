import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * Реактивная пагинация, опционально синхронизируется с query string.
 *
 * const pagination = usePagination({ perPage: 25, syncQuery: true })
 * const fetcher = ({ signal }) => api.deals.list(pagination.params.value, { signal })
 *
 * params.value сразу пригоден для передачи в API как { skip, limit }.
 */
export function usePagination(options = {}) {
  const {
    perPage: defaultPerPage = 25,
    page: defaultPage = 1,
    syncQuery = false,
    pageKey = 'page',
    perPageKey = 'per_page',
  } = options

  const route = syncQuery ? useRoute() : null
  const router = syncQuery ? useRouter() : null

  const page = ref(syncQuery && route?.query?.[pageKey]
    ? Number(route.query[pageKey]) || defaultPage
    : defaultPage)
  const perPage = ref(syncQuery && route?.query?.[perPageKey]
    ? Number(route.query[perPageKey]) || defaultPerPage
    : defaultPerPage)
  const total = ref(0)

  const totalPages = computed(() => {
    if (!total.value || !perPage.value) return 0
    return Math.max(1, Math.ceil(total.value / perPage.value))
  })

  const params = computed(() => ({
    skip: (Math.max(1, page.value) - 1) * perPage.value,
    limit: perPage.value,
  }))

  function setPage(next) {
    const n = Math.max(1, Number(next) || 1)
    if (n === page.value) return
    page.value = n
  }

  function setPerPage(next) {
    const n = Math.max(1, Number(next) || defaultPerPage)
    if (n === perPage.value) return
    perPage.value = n
    page.value = 1
  }

  function reset() {
    page.value = defaultPage
    perPage.value = defaultPerPage
    total.value = 0
  }

  function setTotal(value) {
    total.value = Math.max(0, Number(value) || 0)
  }

  if (syncQuery && router) {
    watch([page, perPage], ([p, pp]) => {
      const query = { ...route.query }
      if (p === defaultPage) delete query[pageKey]
      else query[pageKey] = String(p)
      if (pp === defaultPerPage) delete query[perPageKey]
      else query[perPageKey] = String(pp)
      router.replace({ query }).catch(() => {})
    })
  }

  return {
    page,
    perPage,
    total,
    totalPages,
    params,
    setPage,
    setPerPage,
    setTotal,
    reset,
  }
}
