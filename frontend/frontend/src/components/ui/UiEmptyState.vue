<template>
  <div class="ui-empty" :class="[`ui-empty--${size}`]">
    <div v-if="icon || $slots.icon" class="ui-empty__icon">
      <slot name="icon">
        <i :class="icon" aria-hidden="true"></i>
      </slot>
    </div>
    <h4 v-if="title" class="ui-empty__title">{{ title }}</h4>
    <p v-if="description" class="ui-empty__desc">{{ description }}</p>
    <div v-if="$slots.actions" class="ui-empty__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script>
const SIZES = ['sm', 'md', 'lg']

export default {
  name: 'UiEmptyState',
  props: {
    icon: { type: String, default: null },
    title: { type: String, default: null },
    description: { type: String, default: null },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) }
  }
}
</script>

<style scoped>
.ui-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--color-text-muted);
}

.ui-empty--sm { padding: var(--space-5) var(--space-4); gap: var(--space-2); }
.ui-empty--md { padding: var(--space-8) var(--space-5); gap: var(--space-3); }
.ui-empty--lg { padding: var(--space-12) var(--space-6); gap: var(--space-4); }

.ui-empty__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-xl);
}

.ui-empty--sm .ui-empty__icon { width: 40px; height: 40px; font-size: var(--text-lg); border-radius: var(--radius-md); }
.ui-empty--lg .ui-empty__icon { width: 72px; height: 72px; font-size: var(--text-2xl); }

.ui-empty__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  line-height: var(--leading-tight);
}

.ui-empty__desc {
  margin: 0;
  max-width: 360px;
  font-size: var(--text-base);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

.ui-empty__actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
</style>
