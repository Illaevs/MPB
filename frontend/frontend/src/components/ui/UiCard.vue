<template>
  <section class="ui-card" :class="classes">
    <header v-if="$slots.header || title" class="ui-card__header">
      <slot name="header">
        <div class="ui-card__titles">
          <h3 v-if="title" class="ui-card__title">{{ title }}</h3>
          <p v-if="subtitle" class="ui-card__subtitle">{{ subtitle }}</p>
        </div>
      </slot>
      <div v-if="$slots.actions" class="ui-card__actions">
        <slot name="actions" />
      </div>
    </header>

    <div class="ui-card__body" :class="{ 'ui-card__body--flush': flushBody }">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="ui-card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script>
import { computed } from 'vue'

const PADDING = ['none', 'sm', 'md', 'lg']

export default {
  name: 'UiCard',
  props: {
    title: { type: String, default: null },
    subtitle: { type: String, default: null },
    padding: { type: String, default: 'md', validator: v => PADDING.includes(v) },
    flushBody: { type: Boolean, default: false },
    interactive: { type: Boolean, default: false }
  },
  setup(props) {
    const classes = computed(() => [
      `ui-card--pad-${props.padding}`,
      { 'ui-card--interactive': props.interactive }
    ])
    return { classes }
  }
}
</script>

<style scoped>
.ui-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow var(--dur-base) ease, border-color var(--dur-base) ease, transform var(--dur-base) var(--ease-out);
}

.ui-card--interactive {
  cursor: pointer;
}

.ui-card--interactive:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-strong);
}

.ui-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.ui-card__titles {
  min-width: 0;
}

.ui-card__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  line-height: var(--leading-tight);
}

.ui-card__subtitle {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.ui-card__actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.ui-card__body { padding: var(--space-4); }
.ui-card__body--flush { padding: 0; }

.ui-card__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface-2);
}

/* padding modifiers */
.ui-card--pad-none .ui-card__body { padding: 0; }
.ui-card--pad-sm .ui-card__body { padding: var(--space-3); }
.ui-card--pad-md .ui-card__body { padding: var(--space-4); }
.ui-card--pad-lg .ui-card__body { padding: var(--space-6); }
</style>
