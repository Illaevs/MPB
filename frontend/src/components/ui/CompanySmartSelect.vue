<template>
  <div class="smart-select">
    <input
      :id="inputId"
      v-model="query"
      type="text"
      class="form-control"
      :placeholder="placeholder"
      :disabled="disabled"
      @focus="open"
      @input="onInput"
      @blur="onBlur"
      autocomplete="off"
    />
    <div
      v-if="showDropdown"
      class="smart-select__dropdown"
      @mousedown.prevent
    >
      <button
        v-for="item in filtered"
        :key="item.id"
        type="button"
        class="smart-select__item"
        @click="select(item)"
      >
        <div class="smart-select__title">{{ item.name }}</div>
        <div class="smart-select__subtitle">ИНН: {{ item.inn || '—' }}</div>
      </button>
      <div v-if="!filtered.length" class="smart-select__empty">Ничего не найдено</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Найти контрагента' },
  inputId: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
  fetchUrl: { type: String, default: '' },
  fetchParams: { type: Object, default: () => ({}) },
  fetchLimit: { type: Number, default: 50 },
  minQueryLength: { type: Number, default: 1 },
  maxResults: { type: Number, default: 10 }
})

const emit = defineEmits(['update:modelValue'])

const query = ref('')
const isOpen = ref(false)
const remoteOptions = ref([])
const selectedOption = ref(null)
const fetchTimer = ref(null)
const fetchToken = ref(0)

const normalizeId = (value) => {
  if (!value) return ''
  return String(value).replace(/-/g, '').toLowerCase()
}

const matchOption = (value) => {
  if (!value) return null
  const normalized = normalizeId(value)
  const localMatch = props.options.find(item => normalizeId(item.id) === normalized)
  if (localMatch) return localMatch
  const remoteMatch = remoteOptions.value.find(item => normalizeId(item.id) === normalized)
  if (remoteMatch) return remoteMatch
  if (selectedOption.value && normalizeId(selectedOption.value.id) === normalized) {
    return selectedOption.value
  }
  return null
}

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  const source = props.fetchUrl ? remoteOptions.value : props.options
  const matches = source
    .filter(item =>
      (item.name && item.name.toLowerCase().includes(q)) ||
      (item.short_name && item.short_name.toLowerCase().includes(q)) ||
      (item.full_name && item.full_name.toLowerCase().includes(q)) ||
      (item.inn && String(item.inn).toLowerCase().includes(q))
    )
  if (!props.maxResults || props.maxResults <= 0) {
    return matches
  }
  return matches.slice(0, props.maxResults)
})

const showDropdown = computed(() => isOpen.value && filtered.value.length)

const normalizeFetchUrl = () => {
  if (!props.fetchUrl) return ''
  return props.fetchUrl.endsWith('/') ? props.fetchUrl.slice(0, -1) : props.fetchUrl
}

const fetchById = async (value) => {
  const base = normalizeFetchUrl()
  if (!base || !value) return null
  try {
    const res = await axios.get(`${base}/${value}`)
    return res.data || null
  } catch (error) {
    return null
  }
}

const syncQuery = async () => {
  const matched = matchOption(props.modelValue)
  if (matched) {
    query.value = matched.name || ''
    selectedOption.value = matched
    return
  }
  if (!props.modelValue || !props.fetchUrl) {
    query.value = ''
    return
  }
  const fetched = await fetchById(props.modelValue)
  if (fetched) {
    selectedOption.value = fetched
    query.value = fetched.name || ''
  } else {
    query.value = ''
  }
}

const fetchRemoteOptions = async (term) => {
  const raw = props.fetchUrl
  if (!raw) return
  // Принудительно сохраняем trailing slash — иначе FastAPI отвечает
  // 307 Redirect на абсолютный URL и CSP режет cross-origin фолловап.
  const url = raw.endsWith('/') ? raw : `${raw}/`
  const token = ++fetchToken.value
  try {
    const res = await axios.get(url, {
      params: { ...props.fetchParams, search: term, limit: props.fetchLimit }
    })
    if (token !== fetchToken.value) return
    remoteOptions.value = Array.isArray(res.data) ? res.data : []
  } catch (error) {
    if (token !== fetchToken.value) return
    remoteOptions.value = []
  }
}

const open = () => {
  if (props.disabled) return
  isOpen.value = true
}

const onInput = () => {
  if (!isOpen.value) isOpen.value = true
  if (!query.value.trim()) {
    selectedOption.value = null
    remoteOptions.value = []
    emit('update:modelValue', '')
  }
}

const onBlur = () => {
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}

const select = (item) => {
  emit('update:modelValue', item.id)
  query.value = item.name
  selectedOption.value = item
  isOpen.value = false
}

watch(() => props.modelValue, () => { void syncQuery() }, { immediate: true })
watch(() => props.options, () => {
  if (props.modelValue) {
    void syncQuery()
  }
})

watch(query, (value) => {
  if (!props.fetchUrl) return
  const term = value.trim()
  if (term.length < props.minQueryLength) {
    remoteOptions.value = []
    return
  }
  if (fetchTimer.value) {
    clearTimeout(fetchTimer.value)
  }
  fetchTimer.value = setTimeout(() => {
    fetchRemoteOptions(term)
  }, 250)
})
</script>

<style scoped>
.smart-select {
  position: relative;
}

.smart-select__dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  /* 3000 — внутри модалки (z-index ~1000-2000) и при backdrop-filter
     этого хватает, чтоб dropdown не перекрывался соседями. */
  z-index: 3000;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  max-height: 240px;
  overflow: auto;
}

.smart-select__item {
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border: none;
  background: transparent;
}

.smart-select__item:hover {
  background: var(--md-sys-color-surface-variant);
}

.smart-select__title {
  font-weight: 600;
  font-size: 14px;
}

.smart-select__subtitle {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.smart-select__empty {
  padding: 10px 12px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}
</style>
