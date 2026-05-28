<template>
  <button
    type="button"
    class="ui-popover-item"
    :class="classes"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <i v-if="icon" :class="icon" class="ui-popover-item__icon" aria-hidden="true"></i>
    <span class="ui-popover-item__label"><slot /></span>
    <span v-if="$slots.trailing" class="ui-popover-item__trailing"><slot name="trailing" /></span>
  </button>
</template>

<script>
import { computed } from 'vue'

const VARIANTS = ['default', 'danger']

export default {
  name: 'UiPopoverItem',
  props: {
    icon: { type: String, default: null },
    variant: { type: String, default: 'default', validator: v => VARIANTS.includes(v) },
    active: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false }
  },
  emits: ['click'],
  setup(props) {
    const classes = computed(() => [
      `ui-popover-item--${props.variant}`,
      {
        'is-active': props.active,
        'is-disabled': props.disabled
      }
    ])
    return { classes }
  }
}
</script>

<style scoped>
.ui-popover-item {
  width: 100%;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  text-align: left;
  cursor: pointer;
  transition:
    background-color var(--dur-fast) ease,
    color var(--dur-fast) ease;
}

.ui-popover-item:hover:not(:disabled) {
  background: var(--color-surface-3);
}

.ui-popover-item:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.ui-popover-item__icon {
  color: var(--color-text-muted);
  width: 14px;
  text-align: center;
  flex-shrink: 0;
}

.ui-popover-item__label {
  min-width: 0;
  flex: 1;
}

.ui-popover-item__trailing {
  margin-left: auto;
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
}

.ui-popover-item.is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.ui-popover-item.is-active .ui-popover-item__icon,
.ui-popover-item.is-active .ui-popover-item__trailing {
  color: var(--color-primary);
}

.ui-popover-item--danger {
  color: var(--color-danger);
}

.ui-popover-item--danger .ui-popover-item__icon,
.ui-popover-item--danger .ui-popover-item__trailing {
  color: var(--color-danger);
}

.ui-popover-item--danger:hover:not(:disabled) {
  background: var(--color-danger-soft);
}

.ui-popover-item.is-disabled,
.ui-popover-item:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
