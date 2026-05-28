<template>
  <div class="ui-field" :class="{ 'ui-field--block': true }">
    <label v-if="label" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>

    <div class="ui-chip-input" :class="wrapClasses" @click="focusInput">
      <template v-for="(item, index) in items" :key="`${item}-${index}`">
        <a
          v-if="linkPrefix"
          class="ui-chip-input__chip"
          :href="`${linkPrefix}${item}`"
          target="_blank"
          rel="noopener noreferrer"
          @click.stop
        >
          <span class="ui-chip-input__chip-text">{{ item }}</span>
          <button
            type="button"
            class="ui-chip-input__chip-remove"
            aria-label="Удалить"
            :disabled="disabled"
            @click.stop.prevent="removeItem(item, index)"
          >
            <i class="fa fa-times" aria-hidden="true"></i>
          </button>
        </a>

        <span v-else class="ui-chip-input__chip">
          <span class="ui-chip-input__chip-text">{{ item }}</span>
          <button
            type="button"
            class="ui-chip-input__chip-remove"
            aria-label="Удалить"
            :disabled="disabled"
            @click.stop.prevent="removeItem(item, index)"
          >
            <i class="fa fa-times" aria-hidden="true"></i>
          </button>
        </span>
      </template>

      <input
        ref="inputEl"
        v-model="draft"
        class="ui-chip-input__control"
        :placeholder="placeholder"
        :disabled="disabled"
        @keydown="onKeyDown"
        @blur="onBlur"
      />
    </div>

    <div v-if="displayError" class="ui-field__error">{{ displayError }}</div>
    <div v-else-if="hint" class="ui-field__hint">{{ hint }}</div>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue'

export default {
  name: 'UiChipInput',
  props: {
    modelValue: { type: Array, default: () => [] },
    label: { type: String, default: null },
    hint: { type: String, default: null },
    error: { type: String, default: null },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    required: { type: Boolean, default: false },
    validator: { type: Function, default: null },
    addOnBlur: { type: Boolean, default: true },
    addKeys: { type: Array, default: () => ['Enter', ','] },
    linkPrefix: { type: String, default: null }
  },
  emits: ['update:modelValue', 'add', 'remove'],
  setup(props, { emit }) {
    const draft = ref('')
    const localError = ref('')
    const inputEl = ref(null)

    const items = computed(() => Array.isArray(props.modelValue) ? props.modelValue : [])
    const displayError = computed(() => localError.value || props.error)

    watch(() => props.modelValue, () => { localError.value = '' })

    const wrapClasses = computed(() => ({
      'ui-chip-input--invalid': !!displayError.value,
      'ui-chip-input--disabled': props.disabled
    }))

    const normalizeValue = (value) => String(value || '').trim()

    const pushValue = () => {
      const value = normalizeValue(draft.value)
      if (!value) return false
      if (props.validator) {
        const validation = props.validator(value)
        if (validation !== true) {
          localError.value = typeof validation === 'string' ? validation : 'Некорректное значение'
          return false
        }
      }
      if (items.value.includes(value)) {
        draft.value = ''
        localError.value = ''
        return false
      }
      const next = [...items.value, value]
      emit('update:modelValue', next)
      emit('add', value)
      draft.value = ''
      localError.value = ''
      return true
    }

    const removeItem = (value, index) => {
      if (props.disabled) return
      const next = items.value.filter((_, itemIndex) => itemIndex !== index)
      emit('update:modelValue', next)
      emit('remove', value, index)
    }

    const onKeyDown = (event) => {
      if (props.addKeys.includes(event.key)) {
        event.preventDefault()
        pushValue()
      } else if (event.key === 'Backspace' && !draft.value && items.value.length) {
        removeItem(items.value[items.value.length - 1], items.value.length - 1)
      }
    }

    const onBlur = () => {
      if (props.addOnBlur) pushValue()
    }

    const focusInput = () => {
      if (!props.disabled) inputEl.value?.focus()
    }

    return {
      draft,
      items,
      inputEl,
      displayError,
      wrapClasses,
      removeItem,
      onKeyDown,
      onBlur,
      focusInput
    }
  }
}
</script>

<style scoped>
.ui-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  width: 100%;
}

.ui-field__label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  letter-spacing: 0.3px;
}

.ui-field__required {
  color: var(--color-danger);
  margin-left: 2px;
}

.ui-chip-input {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  min-height: 36px;
  padding: var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
  cursor: text;
}

.ui-chip-input:hover:not(.ui-chip-input--disabled) {
  border-color: var(--color-text-muted);
}

.ui-chip-input:focus-within {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.ui-chip-input--invalid {
  border-color: var(--color-danger);
}

.ui-chip-input--invalid:focus-within {
  box-shadow: 0 0 0 3px var(--color-danger-soft);
}

.ui-chip-input--disabled {
  background: var(--color-surface-2);
  opacity: 0.75;
}

.ui-chip-input__chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  max-width: 100%;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  text-decoration: none;
}

.ui-chip-input__chip-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
}

.ui-chip-input__chip-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: currentColor;
  cursor: pointer;
  flex-shrink: 0;
}

.ui-chip-input__chip-remove:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
}

.ui-chip-input__control {
  flex: 1 1 140px;
  min-width: 120px;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--text-md);
  padding: var(--space-1) 0;
}

.ui-chip-input__control::placeholder {
  color: var(--color-text-subtle);
}

.ui-chip-input__control:disabled {
  cursor: not-allowed;
}

.ui-field__hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.ui-field__error {
  font-size: var(--text-xs);
  color: var(--color-danger);
}
</style>
