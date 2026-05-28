import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'

/**
 * Справочник категорий товаров.
 * До 6+ потребителей, теперь — один кеш.
 */
export const useCategoriesStore = defineStore('categories', () => {
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
    // Бэкенд поддерживает skip/limit; для справочника берём «всё» одним батчем.
    inFlight = api.categories.list({ skip: 0, limit: 1000 })
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

  function upsert(category) {
    if (!category?.id) return
    const idx = items.value.findIndex((it) => String(it.id) === String(category.id))
    if (idx >= 0) {
      const next = items.value.slice()
      next[idx] = { ...next[idx], ...category }
      items.value = next
    } else {
      items.value = [...items.value, category]
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
