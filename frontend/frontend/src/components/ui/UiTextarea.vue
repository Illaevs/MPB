<template>
  <div class="ui-field" :class="{ 'ui-field--block': block }">
    <label v-if="label" :for="inputId" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>

    <div class="ui-field__wrap" :class="wrapClasses">
      <textarea
        :id="inputId"
        ref="el"
        class="ui-field__textarea"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :rows="rows"
        :maxlength="maxlength"
        @input="onInput"
        @change="$emit('change', $event.target.value)"
        @blur="$emit('blur', $event)"
        @focus="$emit('focus', $event)"
      ></textarea>
    </div>

    <div v-if="error" class="ui-field__error">{{ error }}</div>
    <div v-else-if="hint || showCount" class="ui-field__hint">
      <span v-if="hint">{{ hint }}</span>
      <span v-if="showCount" class="ui-field__count">{{ length }}{{ maxlength ? ` / ${maxlength}` : '' }}</span>
    </div>
  </div>
</template>

<script>
import { computed, ref, nextTick, watch, onMounted } from 'vue'

let uid = 0

export default {
  name: 'UiTextarea',
  props: {
    modelValue: { type: String, default: '' },
    label: { type: String, default: null },
    placeholder: { type: String, default: null },
    hint: { type: String, default: null },
    error: { type: String, default: null },
    disabled: { type: Boolean, default: false },
    readonly: { type: Boolean, default: false },
    required: { type: Boolean, default: false },
    block: { type: Boolean, default: true },
    rows: { type: [String, Number], default: 3 },
    maxlength: { type: [String, Number], default: null },
    showCount: { type: Boolean, default: false },
    autosize: { type: Boolean, default: false },
    maxHeight: { type: Number, default: 240 }
  },
  emits: ['update:modelValue', 'change', 'blur', 'focus'],
  setup(props, { emit }) {
    const el = ref(null)
    const inputId = `ui-textarea-${++uid}`

    const wrapClasses = computed(() => ({
      'ui-field__wrap--invalid': !!props.error,
      'ui-field__wrap--disabled': props.disabled
    }))

    const length = computed(() => (props.modelValue || '').length)

    const resize = () => {
      if (!props.autosize || !el.value) return
      el.value.style.height = 'auto'
      el.value.style.height = Math.min(el.value.scrollHeight, props.maxHeight) + 'px'
    }

    const onInput = (e) => {
      emit('update:modelValue', e.target.value)
      if (props.autosize) nextTick(resize)
    }

    watch(() => props.modelValue, () => { if (props.autosize) nextTick(resize) })
    onMounted(() => { if (props.autosize) resize() })

    return { inputId, el, wrapClasses, length, onInput }
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

.ui-field__required { color: var(--color-danger); margin-left: 2px; }

.ui-field__wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
}

.ui-field__wrap:hover:not(.ui-field__wrap--disabled) { border-color: var(--color-text-muted); }
.ui-field__wrap:focus-within { border-color: var(--color-primary); box-shadow: var(--shadow-focus); }
.ui-field__wrap--invalid { border-color: var(--color-danger); }
.ui-field__wrap--invalid:focus-within { box-shadow: 0 0 0 3px var(--color-danger-soft); }
.ui-field__wrap--disabled { background: var(--color-surface-2); opacity: 0.7; }

.ui-field__textarea {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--text-md);
  padding: var(--space-2) var(--space-3);
  resize: vertical;
  line-height: var(--leading-normal);
}
.ui-field__textarea::placeholder { color: var(--color-text-subtle); }

.ui-field__hint {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.ui-field__count { color: var(--color-text-subtle); }
.ui-field__error { font-size: var(--text-xs); color: var(--color-danger); }
</style>
