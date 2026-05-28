<template>
  <div class="category-smart-select" :class="rootClasses">
    <input
      :id="inputId"
      v-model="query"
      type="text"
      class="form-control category-smart-select__input"
      :class="inputClass"
      :placeholder="placeholder"
      :disabled="disabled"
      autocomplete="off"
      @focus="open"
      @input="onInput"
      @keydown.down.prevent="moveActive(1)"
      @keydown.up.prevent="moveActive(-1)"
      @keydown.enter.prevent="selectActive"
      @keydown.esc.prevent="close"
      @blur="onBlur"
    />

    <button
      v-if="allowClear && !disabled && normalizedValue"
      type="button"
      class="category-smart-select__clear"
      title="Очистить"
      @mousedown.prevent
      @click="clear"
    >
      <i class="fas fa-times"></i>
    </button>

    <div v-if="isOpen" class="category-smart-select__dropdown">
      <button
        v-for="(item, index) in filteredOptions"
        :key="`${item.value}-${index}`"
        type="button"
        class="category-smart-select__item"
        :class="{ 'category-smart-select__item--active': index === activeIndex }"
        @mousedown.prevent
        @click="select(item)"
      >
        <span class="category-smart-select__title">{{ item.label }}</span>
        <small v-if="item.hint" class="category-smart-select__hint">{{ item.hint }}</small>
      </button>

      <button
        v-if="canUseCustomValue"
        type="button"
        class="category-smart-select__item category-smart-select__item--custom"
        @mousedown.prevent
        @click="useCustomValue"
      >
        <span class="category-smart-select__title">Использовать "{{ trimmedQuery }}"</span>
      </button>

      <div v-if="!filteredOptions.length && !canUseCustomValue" class="category-smart-select__empty">
        Ничего не найдено
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Категория' },
  inputId: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
  allowClear: { type: Boolean, default: true },
  allowCustom: { type: Boolean, default: false },
  size: { type: String, default: '' },
  inputClass: { type: [String, Array, Object], default: '' }
})

const emit = defineEmits(['update:modelValue', 'change'])

const query = ref('')
const isOpen = ref(false)
const activeIndex = ref(0)

const normalizedValue = computed(() => props.modelValue == null ? '' : String(props.modelValue))
const trimmedQuery = computed(() => query.value.trim())

const rootClasses = computed(() => ({
  'category-smart-select--sm': props.size === 'sm' || String(props.inputClass || '').includes('form-control-sm'),
  'category-smart-select--xs': props.size === 'xs' || String(props.inputClass || '').includes('form-select-xs'),
  'category-smart-select--disabled': props.disabled
}))

const normalizeOption = (option) => {
  if (typeof option === 'string' || typeof option === 'number') {
    const value = String(option)
    return { value, label: value, hint: '' }
  }
  const value = option?.value ?? option?.id ?? option?.key ?? option?.label ?? ''
  const label = option?.label ?? option?.name ?? value
  return {
    value: String(value ?? ''),
    label: String(label ?? ''),
    hint: option?.hint || ''
  }
}

const normalizedOptions = computed(() => {
  const seen = new Set()
  return (props.options || [])
    .map(normalizeOption)
    .filter((option) => {
      if (!option.value && !option.label) return false
      const key = option.value.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
})

const selectedOption = computed(() => {
  const value = normalizedValue.value.toLowerCase()
  if (!value) return null
  return normalizedOptions.value.find((option) => option.value.toLowerCase() === value) || null
})

const filteredOptions = computed(() => {
  const q = trimmedQuery.value.toLowerCase()
  if (!q) return normalizedOptions.value
  return normalizedOptions.value.filter((option) => {
    return option.label.toLowerCase().includes(q) ||
      option.value.toLowerCase().includes(q) ||
      String(option.hint || '').toLowerCase().includes(q)
  })
})

const canUseCustomValue = computed(() => {
  if (!props.allowCustom) return false
  const value = trimmedQuery.value
  if (!value) return false
  return !normalizedOptions.value.some((option) => option.value.toLowerCase() === value.toLowerCase())
})

const syncQuery = () => {
  query.value = selectedOption.value?.label || normalizedValue.value || ''
}

const emitValue = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

const open = () => {
  if (props.disabled) return
  isOpen.value = true
  activeIndex.value = 0
}

const close = () => {
  isOpen.value = false
  syncQuery()
}

const onInput = () => {
  if (!isOpen.value) open()
  activeIndex.value = 0
}

const onBlur = () => {
  setTimeout(() => {
    isOpen.value = false
    syncQuery()
  }, 120)
}

const select = (option) => {
  emitValue(option.value)
  query.value = option.label
  isOpen.value = false
}

const clear = () => {
  emitValue('')
  query.value = ''
  isOpen.value = false
}

const useCustomValue = () => {
  const value = trimmedQuery.value
  if (!value) return
  emitValue(value)
  query.value = value
  isOpen.value = false
}

const moveActive = (direction) => {
  if (!isOpen.value) {
    open()
    return
  }
  const count = filteredOptions.value.length
  if (!count) return
  activeIndex.value = (activeIndex.value + direction + count) % count
}

const selectActive = () => {
  if (!isOpen.value) {
    open()
    return
  }
  const option = filteredOptions.value[activeIndex.value]
  if (option) {
    select(option)
    return
  }
  if (canUseCustomValue.value) useCustomValue()
}

watch(() => props.modelValue, syncQuery, { immediate: true })
watch(() => props.options, syncQuery)
</script>

<style scoped>
.category-smart-select {
  position: relative;
  width: 100%;
}

.category-smart-select__input {
  padding-right: 30px;
}

.category-smart-select--xs .category-smart-select__input {
  min-height: 26px;
  padding: 2px 28px 2px 6px;
  font-size: 12px;
  border: 0;
  background: transparent;
}

.category-smart-select--sm .category-smart-select__input {
  min-height: 31px;
  font-size: 13px;
}

.category-smart-select__clear {
  position: absolute;
  top: 50%;
  right: 7px;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 11px;
  line-height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.category-smart-select__clear:hover {
  background: var(--md-sys-color-surface-variant);
}

.category-smart-select__dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 4000;
  max-height: 260px;
  overflow-y: auto;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, #d7dde8);
  border-radius: 10px;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.16);
  padding: 4px;
}

.category-smart-select__item {
  width: 100%;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--md-sys-color-on-surface, #1f2937);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 7px 9px;
  text-align: left;
}

.category-smart-select__item:hover,
.category-smart-select__item--active {
  background: var(--md-sys-color-surface-variant, #eef3f8);
}

.category-smart-select__item--custom {
  color: var(--md-sys-color-primary, #0d6efd);
}

.category-smart-select__title {
  font-size: 13px;
  line-height: 1.25;
}

.category-smart-select__hint,
.category-smart-select__empty {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant, #64748b);
}

.category-smart-select__empty {
  padding: 8px 9px;
}
</style>
