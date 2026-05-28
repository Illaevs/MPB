<template>
  <button
    type="button"
    class="ui-icon-btn"
    :class="classes"
    :disabled="disabled"
    :aria-label="label"
    :title="title || label"
    @click="$emit('click', $event)"
  >
    <i :class="icon" aria-hidden="true"></i>
  </button>
</template>

<script>
import { computed } from 'vue'

const VARIANTS = ['default', 'primary', 'danger', 'ghost']
const SIZES = ['xs', 'sm', 'md', 'lg']

export default {
  name: 'UiIconButton',
  props: {
    icon: { type: String, required: true },
    label: { type: String, required: true },
    title: { type: String, default: null },
    variant: { type: String, default: 'default', validator: v => VARIANTS.includes(v) },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    disabled: { type: Boolean, default: false }
  },
  emits: ['click'],
  setup(props) {
    const classes = computed(() => [
      `ui-icon-btn--${props.variant}`,
      `ui-icon-btn--${props.size}`
    ])
    return { classes }
  }
}
</script>

<style scoped>
.ui-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition:
    background-color var(--dur-fast) ease,
    color var(--dur-fast) ease,
    border-color var(--dur-fast) ease;
}

.ui-icon-btn:hover:not([disabled]) {
  background: var(--color-surface-3);
  color: var(--color-text);
}

.ui-icon-btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.ui-icon-btn[disabled] {
  opacity: 0.4;
  cursor: not-allowed;
}

/* sizes */
.ui-icon-btn--xs { width: 22px; height: 22px; font-size: var(--text-xs); border-radius: var(--radius-xs); }
.ui-icon-btn--sm { width: 28px; height: 28px; font-size: var(--text-sm); border-radius: var(--radius-xs); }
.ui-icon-btn--md { width: 34px; height: 34px; font-size: var(--text-md); }
.ui-icon-btn--lg { width: 40px; height: 40px; font-size: var(--text-lg); }

/* variants */
.ui-icon-btn--primary { color: var(--color-primary); }
.ui-icon-btn--primary:hover:not([disabled]) {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.ui-icon-btn--danger { color: var(--color-danger); }
.ui-icon-btn--danger:hover:not([disabled]) {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.ui-icon-btn--ghost { color: var(--color-text-subtle); }
.ui-icon-btn--ghost:hover:not([disabled]) {
  background: transparent;
  color: var(--color-text);
}
</style>
