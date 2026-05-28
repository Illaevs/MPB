<template>
  <component
    :is="tag"
    :type="tag === 'button' ? type : undefined"
    :href="tag === 'a' ? href : undefined"
    :disabled="isDisabled"
    :aria-busy="loading || undefined"
    class="ui-btn"
    :class="classes"
    @click="onClick"
  >
    <span v-if="loading" class="ui-btn__spinner" aria-hidden="true"></span>
    <i v-else-if="iconLeft" :class="iconLeft" class="ui-btn__icon" aria-hidden="true"></i>
    <span v-if="$slots.default" class="ui-btn__label"><slot /></span>
    <i v-if="iconRight && !loading" :class="iconRight" class="ui-btn__icon" aria-hidden="true"></i>
  </component>
</template>

<script>
import { computed } from 'vue'

const VARIANTS = ['primary', 'secondary', 'outline', 'ghost', 'danger', 'success', 'warning']
const SIZES = ['xs', 'sm', 'md', 'lg']

export default {
  name: 'UiButton',
  props: {
    variant: { type: String, default: 'primary', validator: v => VARIANTS.includes(v) },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    type: { type: String, default: 'button' },
    tag: { type: String, default: 'button' },
    href: { type: String, default: null },
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    block: { type: Boolean, default: false },
    iconLeft: { type: String, default: null },
    iconRight: { type: String, default: null }
  },
  emits: ['click'],
  setup(props, { emit, slots }) {
    const isDisabled = computed(() => props.disabled || props.loading)

    const classes = computed(() => [
      `ui-btn--${props.variant}`,
      `ui-btn--${props.size}`,
      {
        'ui-btn--block': props.block,
        'ui-btn--loading': props.loading,
        'ui-btn--icon-only': !slots.default && (props.iconLeft || props.iconRight)
      }
    ])

    const onClick = (e) => {
      if (isDisabled.value) {
        e.preventDefault()
        return
      }
      emit('click', e)
    }

    return { classes, isDisabled, onClick }
  }
}
</script>

<style scoped>
.ui-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-weight: var(--fw-semibold);
  line-height: var(--leading-tight);
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  text-decoration: none;
  transition:
    background-color var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease,
    transform var(--dur-fast) var(--ease-out);
}

.ui-btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.ui-btn:active:not([disabled]) {
  transform: translateY(1px);
}

.ui-btn[disabled],
.ui-btn--loading {
  opacity: 0.55;
  cursor: not-allowed;
}

.ui-btn--block {
  width: 100%;
}

.ui-btn__icon {
  font-size: 0.95em;
  line-height: 1;
}

.ui-btn__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ui-btn-spin 0.7s linear infinite;
  opacity: 0.8;
}

@keyframes ui-btn-spin {
  to { transform: rotate(360deg); }
}

/* --- Sizes --- */
.ui-btn--xs {
  min-height: 24px;
  padding: 2px var(--space-2);
  font-size: var(--text-xs);
  border-radius: var(--radius-xs);
  gap: var(--space-1);
}

.ui-btn--sm {
  min-height: 28px;
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
  border-radius: var(--radius-xs);
}

.ui-btn--md {
  min-height: 36px;
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-base);
}

.ui-btn--lg {
  min-height: 44px;
  padding: var(--space-3) var(--space-5);
  font-size: var(--text-md);
  border-radius: var(--radius-md);
}

/* --- Variants --- */
.ui-btn--primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
}
.ui-btn--primary:hover:not([disabled]) {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.ui-btn--secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border-strong);
}
.ui-btn--secondary:hover:not([disabled]) {
  background: var(--color-surface-2);
  border-color: var(--color-text-muted);
}

.ui-btn--outline {
  background: transparent;
  color: var(--color-primary);
  border-color: var(--color-primary);
}
.ui-btn--outline:hover:not([disabled]) {
  background: var(--color-primary-soft);
}

.ui-btn--ghost {
  background: transparent;
  color: var(--color-text);
  border-color: transparent;
}
.ui-btn--ghost:hover:not([disabled]) {
  background: var(--color-surface-3);
}

.ui-btn--danger {
  background: var(--color-danger);
  color: var(--color-text-inverse);
  border-color: var(--color-danger);
}
.ui-btn--danger:hover:not([disabled]) {
  background: var(--color-danger-hover);
  border-color: var(--color-danger-hover);
}

.ui-btn--success {
  background: var(--color-success);
  color: var(--color-text-inverse);
  border-color: var(--color-success);
}
.ui-btn--success:hover:not([disabled]) {
  background: var(--color-success-hover);
  border-color: var(--color-success-hover);
}

.ui-btn--warning {
  background: var(--color-warning);
  color: var(--color-text-inverse);
  border-color: var(--color-warning);
}
.ui-btn--warning:hover:not([disabled]) {
  background: var(--color-warning-hover);
  border-color: var(--color-warning-hover);
}
</style>
