import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'

/**
 * Каталог товаров.
 *
 * Используется как кеш для ProductSmartSelect и форм
 * (лиды/сделки/задачи/договоры). Раньше каждая форма дёргала /api/v1/products/
 * самостоятельно — теперь один раз за сессию.
 *
 * Для CRUD-операций (Catalog.vue) — `api.products.*` напрямую с последующим
 * `refresh()` / `upsert()` / `removeLocal()`.
 */
export const useProductsStore = defineStore('products', () => {
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
    inFlight = api.products.list({ limit: 1000 })
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

  function upsert(product) {
    if (!product?.id) return
    const idx = items.value.findIndex((it) => String(it.id) === String(product.id))
    if (idx >= 0) {
      const next = items.value.slice()
      next[idx] = { ...next[idx], ...product }
      items.value = next
    } else {
      items.value = [...items.value, product]
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
