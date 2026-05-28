<template>
  <span class="ui-badge" :class="classes">
    <i v-if="icon" :class="icon" class="ui-badge__icon" aria-hidden="true"></i>
    <span v-if="dot" class="ui-badge__dot" aria-hidden="true"></span>
    <span class="ui-badge__label"><slot>{{ label }}</slot></span>
    <button
      v-if="closable"
      type="button"
      class="ui-badge__close"
      aria-label="Удалить"
      @click.stop="$emit('close', $event)"
    >
      <i class="fa fa-times" aria-hidden="true"></i>
    </button>
  </span>
</template>

<script>
import { computed } from 'vue'

const VARIANTS = ['neutral', 'primary', 'success', 'warning', 'danger', 'info']
const SIZES = ['sm', 'md']

export default {
  name: 'UiBadge',
  props: {
    label: { type: [String, Number], default: '' },
    variant: { type: String, default: 'neutral', validator: v => VARIANTS.includes(v) },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    icon: { type: String, default: null },
    pill: { type: Boolean, default: false },
    outline: { type: Boolean, default: false },
    dot: { type: Boolean, default: false },
    closable: { type: Boolean, default: false }
  },
  emits: ['close'],
  setup(props) {
    const classes = computed(() => [
      `ui-badge--${props.variant}`,
      `ui-badge--${props.size}`,
      {
        'ui-badge--pill': props.pill,
        'ui-badge--outline': props.outline
      }
    ])
    return { classes }
  }
}
</script>

<style scoped>
.ui-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-weight: var(--fw-semibold);
  line-height: 1.4;
  white-space: nowrap;
  border: 1px solid transparent;
}

.ui-badge--sm { padding: 1px var(--space-2); font-size: var(--text-xs); border-radius: var(--radius-xs); }
.ui-badge--md { padding: 2px var(--space-2); font-size: var(--text-sm); border-radius: var(--radius-xs); }
.ui-badge--pill { border-radius: var(--radius-pill); padding-left: var(--space-3); padding-right: var(--space-3); }

.ui-badge__icon { font-size: 0.85em; }
.ui-badge__label { min-width: 0; }
.ui-badge__dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
}

.ui-badge__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: currentColor;
  cursor: pointer;
  padding: 0;
}

.ui-badge__close:hover {
  background: rgba(255, 255, 255, 0.32);
}

.ui-badge__close:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

/* filled */
.ui-badge--neutral { background: var(--color-surface-3); color: var(--color-text-muted); }
.ui-badge--primary { background: var(--color-primary-soft); color: var(--color-primary); }
.ui-badge--success { background: var(--color-success-soft); color: var(--color-success); }
.ui-badge--warning { background: var(--color-warning-soft); color: var(--color-warning); }
.ui-badge--danger { background: var(--color-danger-soft); color: var(--color-danger); }
.ui-badge--info { background: var(--color-info-soft); color: var(--color-info); }

/* outline */
.ui-badge--outline { background: transparent; border-color: currentColor; }
.ui-badge--outline.ui-badge--neutral { color: var(--color-text-muted); }
</style>
