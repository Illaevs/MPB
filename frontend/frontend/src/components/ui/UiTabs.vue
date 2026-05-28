<template>
  <div class="ui-tabs" :class="[`ui-tabs--${variant}`, `ui-tabs--${size}`]" role="tablist">
    <button
      v-for="tab in normalizedTabs"
      :key="tab.value"
      type="button"
      role="tab"
      :aria-selected="tab.value === modelValue"
      class="ui-tabs__tab"
      :class="{ 'is-active': tab.value === modelValue, 'is-disabled': tab.disabled }"
      :disabled="tab.disabled"
      @click="select(tab)"
    >
      <i v-if="tab.icon" :class="tab.icon" class="ui-tabs__icon" aria-hidden="true"></i>
      <span>{{ tab.label }}</span>
      <span v-if="tab.count != null" class="ui-tabs__count">{{ tab.count }}</span>
    </button>
  </div>
</template>

<script>
import { computed } from 'vue'

const VARIANTS = ['segment', 'underline']
const SIZES = ['sm', 'md']

export default {
  name: 'UiTabs',
  props: {
    modelValue: { type: [String, Number, Boolean, null], required: true },
    tabs: { type: Array, required: true },
    variant: { type: String, default: 'segment', validator: v => VARIANTS.includes(v) },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) }
  },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit }) {
    const normalizedTabs = computed(() => props.tabs.map(t => {
      if (typeof t === 'string') return { value: t, label: t }
      return t
    }))

    const select = (tab) => {
      if (tab.disabled || tab.value === props.modelValue) return
      emit('update:modelValue', tab.value)
      emit('change', tab.value)
    }

    return { normalizedTabs, select }
  }
}
</script>

<style scoped>
.ui-tabs {
  display: inline-flex;
  gap: var(--space-1);
}

.ui-tabs__tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-weight: var(--fw-semibold);
  cursor: pointer;
  white-space: nowrap;
  transition:
    background-color var(--dur-fast) ease,
    color var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease;
}

.ui-tabs__tab:focus-visible { outline: none; box-shadow: var(--shadow-focus); }
.ui-tabs__tab:hover:not(.is-disabled):not(.is-active) { color: var(--color-text); }
.ui-tabs__tab.is-disabled { opacity: 0.5; cursor: not-allowed; }

.ui-tabs__count {
  padding: 0 var(--space-2);
  border-radius: var(--radius-pill);
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
}

.ui-tabs__tab.is-active .ui-tabs__count {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

/* --- Variant: segment (pill group on neutral surface) --- */
.ui-tabs--segment {
  background: var(--color-surface-3);
  padding: var(--space-1);
  border-radius: var(--radius-sm);
}
.ui-tabs--segment .ui-tabs__tab {
  border-radius: var(--radius-xs);
}
.ui-tabs--segment .ui-tabs__tab.is-active {
  background: var(--color-surface);
  color: var(--color-primary);
  box-shadow: var(--shadow-xs);
}

/* --- Variant: underline --- */
.ui-tabs--underline {
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}
.ui-tabs--underline .ui-tabs__tab {
  border-radius: 0;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding-left: 0;
  padding-right: 0;
}
.ui-tabs--underline .ui-tabs__tab.is-active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* --- Sizes --- */
.ui-tabs--sm .ui-tabs__tab { padding: var(--space-1) var(--space-3); font-size: var(--text-sm); min-height: 28px; }
.ui-tabs--md .ui-tabs__tab { padding: var(--space-2) var(--space-4); font-size: var(--text-base); min-height: 32px; }
</style>
