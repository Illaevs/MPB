<template>
  <span
    class="ui-spinner"
    :class="[`ui-spinner--${size}`, { 'ui-spinner--inline': inline }]"
    role="status"
    :aria-label="label"
  ></span>
</template>

<script>
const SIZES = ['xs', 'sm', 'md', 'lg']

export default {
  name: 'UiSpinner',
  props: {
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    label: { type: String, default: 'Загрузка' },
    inline: { type: Boolean, default: false }
  }
}
</script>

<style scoped>
.ui-spinner {
  display: inline-block;
  border-radius: 50%;
  border-style: solid;
  border-color: var(--color-primary-soft-strong);
  border-top-color: var(--color-primary);
  animation: ui-spinner-rotate 0.7s linear infinite;
  flex-shrink: 0;
}

.ui-spinner--inline { vertical-align: -2px; }

.ui-spinner--xs { width: 12px; height: 12px; border-width: 2px; }
.ui-spinner--sm { width: 16px; height: 16px; border-width: 2px; }
.ui-spinner--md { width: 24px; height: 24px; border-width: 3px; }
.ui-spinner--lg { width: 40px; height: 40px; border-width: 4px; }

@keyframes ui-spinner-rotate {
  to { transform: rotate(360deg); }
}
</style>
