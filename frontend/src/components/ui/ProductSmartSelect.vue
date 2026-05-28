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
    <div v-if="showDropdown" class="smart-select__dropdown">
      <button
        v-for="item in filtered"
        :key="item.id"
        type="button"
        class="smart-select__item"
        @click="select(item)"
      >
        <div class="smart-select__title">{{ item.name }}</div>
        <div class="smart-select__subtitle">
          Категория: {{ item.category?.name || item.category_name || '-' }}
        </div>
      </button>
      <div v-if="!filtered.length" class="smart-select__empty">Ничего не найдено</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Найти товар' },
  inputId: { type: String, default: undefined },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const query = ref('')
const isOpen = ref(false)

const normalizeId = (value) => {
  if (!value) return ''
  return String(value).replace(/-/g, '').toLowerCase()
}

const matchOption = (value) => {
  if (!value) return null
  const normalized = normalizeId(value)
  return props.options.find(item => normalizeId(item.id) === normalized) || null
}

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return props.options
    .filter(item => {
      const name = item.name ? item.name.toLowerCase() : ''
      const category = item.category?.name ? item.category.name.toLowerCase() : ''
      const categoryName = item.category_name ? item.category_name.toLowerCase() : ''
      return name.includes(q) || category.includes(q) || categoryName.includes(q)
    })
    .slice(0, 10)
})

const showDropdown = computed(() => isOpen.value && filtered.value.length)

const syncQuery = () => {
  const matched = matchOption(props.modelValue)
  query.value = matched ? matched.name : ''
}

const open = () => {
  if (props.disabled) return
  isOpen.value = true
}

const onInput = () => {
  if (!isOpen.value) isOpen.value = true
}

const onBlur = () => {
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}

const select = (item) => {
  emit('update:modelValue', item.id)
  query.value = item.name
  isOpen.value = false
}

watch(() => props.modelValue, syncQuery, { immediate: true })
watch(() => props.options, () => {
  if (props.modelValue) {
    syncQuery()
  }
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
  z-index: 3000;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  max-height: 320px;
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

