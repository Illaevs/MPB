<template>
  <div class="ui-field" :class="{ 'ui-field--block': block }">
    <label v-if="label" :for="inputId" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>

    <div class="ui-field__wrap" :class="wrapClasses">
      <i v-if="iconLeft" :class="iconLeft" class="ui-field__icon ui-field__icon--left" aria-hidden="true"></i>

      <input
        :id="inputId"
        ref="inputEl"
        class="ui-field__input"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :autocomplete="autocomplete"
        :min="min"
        :max="max"
        :step="step"
        :maxlength="maxlength"
        @input="onInput"
        @change="$emit('change', $event.target.value)"
        @blur="$emit('blur', $event)"
        @focus="$emit('focus', $event)"
        @keydown="$emit('keydown', $event)"
      />

      <i v-if="iconRight && !clearable" :class="iconRight" class="ui-field__icon ui-field__icon--right" aria-hidden="true"></i>
      <button
        v-else-if="clearable && hasValue && !disabled && !readonly"
        type="button"
        class="ui-field__clear"
        aria-label="Очистить"
        @click="clear"
      >
        <i class="fa fa-times-circle" aria-hidden="true"></i>
      </button>
    </div>

    <div v-if="error" class="ui-field__error">{{ error }}</div>
    <div v-else-if="hint" class="ui-field__hint">{{ hint }}</div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'

let uid = 0

const SIZES = ['sm', 'md', 'lg']

export default {
  name: 'UiInput',
  props: {
    modelValue: { type: [String, Number], default: '' },
    label: { type: String, default: null },
    placeholder: { type: String, default: null },
    type: { type: String, default: 'text' },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    hint: { type: String, default: null },
    error: { type: String, default: null },
    disabled: { type: Boolean, default: false },
    readonly: { type: Boolean, default: false },
    required: { type: Boolean, default: false },
    block: { type: Boolean, default: true },
    clearable: { type: Boolean, default: false },
    iconLeft: { type: String, default: null },
    iconRight: { type: String, default: null },
    autocomplete: { type: String, default: null },
    min: { type: [String, Number], default: null },
    max: { type: [String, Number], default: null },
    step: { type: [String, Number], default: null },
    maxlength: { type: [String, Number], default: null }
  },
  emits: ['update:modelValue', 'change', 'blur', 'focus', 'keydown', 'clear'],
  setup(props, { emit }) {
    const inputEl = ref(null)
    const inputId = `ui-input-${++uid}`

    const hasValue = computed(() => props.modelValue !== '' && props.modelValue != null)

    const wrapClasses = computed(() => [
      `ui-field__wrap--${props.size}`,
      {
        'ui-field__wrap--invalid': !!props.error,
        'ui-field__wrap--disabled': props.disabled,
        'has-icon-left': !!props.iconLeft,
        'has-icon-right': !!props.iconRight || (props.clearable && hasValue.value)
      }
    ])

    const onInput = (e) => {
      let v = e.target.value
      if (props.type === 'number' && v !== '') v = Number(v)
      emit('update:modelValue', v)
    }

    const clear = () => {
      emit('update:modelValue', '')
      emit('clear')
      inputEl.value?.focus()
    }

    return { inputId, inputEl, wrapClasses, hasValue, onInput, clear }
  }
}
</script>

<style scoped>
.ui-field {
  display: inline-flex;
  flex-direction: column;
  gap: var(--space-1);
}
.ui-field--block { display: flex; width: 100%; }

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

.ui-field__wrap {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
}

.ui-field__wrap:hover:not(.ui-field__wrap--disabled) {
  border-color: var(--color-text-muted);
}

.ui-field__wrap:focus-within {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.ui-field__wrap--invalid {
  border-color: var(--color-danger);
}
.ui-field__wrap--invalid:focus-within {
  box-shadow: 0 0 0 3px var(--color-danger-soft);
}

.ui-field__wrap--disabled {
  background: var(--color-surface-2);
  opacity: 0.7;
}

.ui-field__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--text-md);
}
.ui-field__input::placeholder { color: var(--color-text-subtle); }
.ui-field__input:disabled { cursor: not-allowed; }

/* sizes */
.ui-field__wrap--sm { min-height: 28px; }
.ui-field__wrap--sm .ui-field__input { padding: var(--space-1) var(--space-2); font-size: var(--text-sm); }
.ui-field__wrap--md { min-height: 36px; }
.ui-field__wrap--md .ui-field__input { padding: var(--space-2) var(--space-3); }
.ui-field__wrap--lg { min-height: 44px; }
.ui-field__wrap--lg .ui-field__input { padding: var(--space-3) var(--space-4); font-size: var(--text-lg); }

/* icons */
.ui-field__icon {
  color: var(--color-text-subtle);
  font-size: var(--text-md);
  flex-shrink: 0;
}
.ui-field__icon--left { padding-left: var(--space-3); }
.ui-field__icon--right { padding-right: var(--space-3); }
.has-icon-left .ui-field__input { padding-left: var(--space-2); }
.has-icon-right .ui-field__input { padding-right: var(--space-2); }

.ui-field__clear {
  background: transparent;
  border: none;
  padding: 0 var(--space-3);
  color: var(--color-text-subtle);
  cursor: pointer;
  display: flex;
  align-items: center;
}
.ui-field__clear:hover { color: var(--color-text-muted); }

.ui-field__hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.ui-field__error {
  font-size: var(--text-xs);
  color: var(--color-danger);
}
</style>
