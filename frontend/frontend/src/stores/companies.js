import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'

/**
 * Справочник контрагентов.
 *
 * Используется как кеш для селектов и форм, где нужен «полный список».
 * Раньше каждое из 20+ мест дёргало /api/v1/companies/?limit=1000 само;
 * теперь — `await store.ensureLoaded()` за сессию один раз.
 *
 * Для CRUD-операций (Companies.vue) используйте api.companies.* напрямую —
 * после mutation вызывайте store.refresh().
 */
export const useCompaniesStore = defineStore('companies', () => {
  const items = ref([])
  const loaded = ref(false)
  const loading = ref(false)
  let inFlight = null

  const byId = computed(() => {
    const map = new Map()
    for (const item of items.value) {
      if (item?.id) map.set(String(item.id), item)
    }
    return map
  })

  function getById(id) {
    return id ? byId.value.get(String(id)) || null : null
  }

  async function ensureLoaded() {
    if (loaded.value) return items.value
    if (inFlight) return inFlight
    loading.value = true
    inFlight = api.companies.list()
      .then((data) => {
        items.value = Array.isArray(data) ? data : []
        loaded.value = true
        return items.value
      })
      .finally(() => {
        loading.value = false
        inFlight = null
      })
    return inFlight
  }

  async function refresh() {
    loaded.value = false
    inFlight = null
    return ensureLoaded()
  }

  function invalidate() {
    loaded.value = false
    inFlight = null
  }

  function upsert(company) {
    if (!company?.id) return
    const idx = items.value.findIndex((it) => String(it.id) === String(company.id))
    if (idx >= 0) {
      const next = items.value.slice()
      next[idx] = { ...next[idx], ...company }
      items.value = next
    } else {
      items.value = [...items.value, company]
    }
  }

  function removeLocal(id) {
    if (!id) return
    items.value = items.value.filter((it) => String(it.id) !== String(id))
  }

  return {
    items,
    loaded,
    loading,
    byId,
    getById,
    ensureLoaded,
    refresh,
    invalidate,
    upsert,
    removeLocal,
  }
})
