<template>
  <div class="ui-field" :class="{ 'ui-field--block': block }">
    <label v-if="label" :for="inputId" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>

    <div class="ui-field__wrap" :class="wrapClasses">
      <select
        :id="inputId"
        class="ui-field__select"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        @change="onChange"
        @blur="$emit('blur', $event)"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="opt in normalizedOptions"
          :key="opt.value"
          :value="opt.value"
          :disabled="opt.disabled"
        >{{ opt.label }}</option>
      </select>
      <i class="fa fa-chevron-down ui-field__chevron" aria-hidden="true"></i>
    </div>

    <div v-if="error" class="ui-field__error">{{ error }}</div>
    <div v-else-if="hint" class="ui-field__hint">{{ hint }}</div>
  </div>
</template>

<script>
import { computed } from 'vue'

let uid = 0

const SIZES = ['sm', 'md', 'lg']

export default {
  name: 'UiSelect',
  props: {
    modelValue: { type: [String, Number, Boolean, null], default: '' },
    options: { type: Array, required: true },
    label: { type: String, default: null },
    placeholder: { type: String, default: null },
    hint: { type: String, default: null },
    error: { type: String, default: null },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    disabled: { type: Boolean, default: false },
    required: { type: Boolean, default: false },
    block: { type: Boolean, default: true },
    labelKey: { type: String, default: 'label' },
    valueKey: { type: String, default: 'value' }
  },
  emits: ['update:modelValue', 'change', 'blur'],
  setup(props, { emit }) {
    const inputId = `ui-select-${++uid}`

    const normalizedOptions = computed(() =>
      props.options.map(o => {
        if (o == null) return { value: '', label: '' }
        if (typeof o === 'string' || typeof o === 'number') return { value: o, label: String(o) }
        return {
          value: o[props.valueKey],
          label: o[props.labelKey],
          disabled: !!o.disabled
        }
      })
    )

    const wrapClasses = computed(() => [
      `ui-field__wrap--${props.size}`,
      {
        'ui-field__wrap--invalid': !!props.error,
        'ui-field__wrap--disabled': props.disabled
      }
    ])

    const onChange = (e) => {
      const raw = e.target.value
      const match = normalizedOptions.value.find(o => String(o.value) === raw)
      const v = match ? match.value : raw
      emit('update:modelValue', v)
      emit('change', v)
    }

    return { inputId, normalizedOptions, wrapClasses, onChange }
  }
}
</script>

<style scoped>
.ui-field { display: inline-flex; flex-direction: column; gap: var(--space-1); }
.ui-field--block { display: flex; width: 100%; }

.ui-field__label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  letter-spacing: 0.3px;
}
.ui-field__required { color: var(--color-danger); margin-left: 2px; }

.ui-field__wrap {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
}
.ui-field__wrap:hover:not(.ui-field__wrap--disabled) { border-color: var(--color-text-muted); }
.ui-field__wrap:focus-within { border-color: var(--color-primary); box-shadow: var(--shadow-focus); }
.ui-field__wrap--invalid { border-color: var(--color-danger); }
.ui-field__wrap--disabled { background: var(--color-surface-2); opacity: 0.7; }

.ui-field__select {
  flex: 1;
  appearance: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--text-md);
  cursor: pointer;
  padding-right: var(--space-8);
}
.ui-field__select:disabled { cursor: not-allowed; }

.ui-field__wrap--sm { min-height: 28px; }
.ui-field__wrap--sm .ui-field__select { padding: var(--space-1) var(--space-8) var(--space-1) var(--space-2); font-size: var(--text-sm); }
.ui-field__wrap--md { min-height: 36px; }
.ui-field__wrap--md .ui-field__select { padding: var(--space-2) var(--space-8) var(--space-2) var(--space-3); }
.ui-field__wrap--lg { min-height: 44px; }
.ui-field__wrap--lg .ui-field__select { padding: var(--space-3) var(--space-10) var(--space-3) var(--space-4); font-size: var(--text-lg); }

.ui-field__chevron {
  position: absolute;
  right: var(--space-3);
  pointer-events: none;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}

.ui-field__hint { font-size: var(--text-xs); color: var(--color-text-muted); }
.ui-field__error { font-size: var(--text-xs); color: var(--color-danger); }
</style>
