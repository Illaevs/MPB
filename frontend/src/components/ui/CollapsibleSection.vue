<template>
  <section class="collapsible-section" :class="{ 'is-open': open }">
    <button
      type="button"
      class="collapsible-section__header"
      :aria-expanded="open"
      @click="toggle"
    >
      <i v-if="icon" class="collapsible-section__icon" :class="icon"></i>
      <span class="collapsible-section__title">{{ title }}</span>
      <span v-if="badge !== null && badge !== undefined && badge !== ''" class="collapsible-section__badge" :class="badgeClass">
        {{ badge }}
      </span>
      <span v-if="hint" class="collapsible-section__hint">{{ hint }}</span>
      <i class="fas fa-chevron-down collapsible-section__caret" aria-hidden="true"></i>
    </button>
    <div v-show="open" class="collapsible-section__body">
      <slot />
    </div>
  </section>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'CollapsibleSection',
  props: {
    title: { type: String, required: true },
    icon: { type: String, default: '' },
    badge: { type: [String, Number, null], default: null },
    badgeClass: { type: String, default: '' },
    hint: { type: String, default: '' },
    defaultOpen: { type: Boolean, default: false }
  },
  emits: ['update:open'],
  setup(props, { emit }) {
    const open = ref(props.defaultOpen)
    function toggle() {
      open.value = !open.value
      emit('update:open', open.value)
    }
    return { open, toggle }
  }
}
</script>

<style scoped>
.collapsible-section {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--space-3) 0;
}

.collapsible-section__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  background: transparent;
  border: 0;
  padding: var(--space-2) 0;
  cursor: pointer;
  text-align: left;
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
  border-radius: var(--radius-sm);
  transition: color var(--dur-fast) var(--ease-out);
}
.collapsible-section__header:hover { color: var(--color-primary); }
.collapsible-section__header:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.collapsible-section__icon {
  color: var(--color-text-muted);
  font-size: var(--text-md);
}

.collapsible-section__title { flex: 0 1 auto; }

.collapsible-section__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  border-radius: var(--radius-pill);
}
.collapsible-section__badge--warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}
.collapsible-section__badge--danger {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}
.collapsible-section__badge--success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.collapsible-section__hint {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  font-weight: var(--fw-regular);
}

.collapsible-section__caret {
  margin-left: auto;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  transition: transform var(--dur-base) var(--ease-out);
}
.collapsible-section.is-open .collapsible-section__caret {
  transform: rotate(180deg);
}

.collapsible-section__body {
  padding: var(--space-2) 0 var(--space-3);
  animation: collapsible-section-fade var(--dur-base) var(--ease-out);
}

@keyframes collapsible-section-fade {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
