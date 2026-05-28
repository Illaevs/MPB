import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'

/**
 * Справочник пользователей.
 * Раньше /api/v1/users/ дёргался из 12+ мест. Теперь — один раз за сессию.
 */
export const useUsersStore = defineStore('users', () => {
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

  const active = computed(() => items.value.filter((u) => u?.is_active !== false))

  async function ensureLoaded() {
    if (loaded.value) return items.value
    if (inFlight) return inFlight
    loading.value = true
    inFlight = api.users.list()
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

  function upsert(user) {
    if (!user?.id) return
    const idx = items.value.findIndex((it) => String(it.id) === String(user.id))
    if (idx >= 0) {
      const next = items.value.slice()
      next[idx] = { ...next[idx], ...user }
      items.value = next
    } else {
      items.value = [...items.value, user]
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
    active,
    getById,
    ensureLoaded,
    refresh,
    invalidate,
    upsert,
    removeLocal,
  }
})
