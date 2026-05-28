<template>
  <span
    class="placeholder-chip"
    :class="{
      'placeholder-chip--empty': isEmpty,
      'placeholder-chip--active': active,
    }"
    :data-field-key="fieldKey"
    role="button"
    tabindex="0"
    @click.stop="$emit('select', fieldKey)"
    @keydown.enter.prevent="$emit('select', fieldKey)"
    @keydown.space.prevent="$emit('select', fieldKey)"
  >
    <span v-if="!isEmpty" class="placeholder-chip__value">{{ displayValue }}</span>
    <span v-else class="placeholder-chip__empty">
      <i class="fas fa-circle-plus"></i>{{ fallbackLabel }}
    </span>
  </span>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'PlaceholderChip',
  props: {
    fieldKey: { type: String, required: true },
    value: { type: [String, Number, null, undefined], default: null },
    label: { type: String, default: '' },
    active: { type: Boolean, default: false },
  },
  emits: ['select'],
  setup(props) {
    const isEmpty = computed(() => props.value === null || props.value === undefined || String(props.value).trim() === '')
    const displayValue = computed(() => (isEmpty.value ? '' : String(props.value)))
    const fallbackLabel = computed(() => props.label || props.fieldKey)
    return { isEmpty, displayValue, fallbackLabel }
  }
}
</script>

<style scoped>
.placeholder-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
  user-select: none;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  line-height: 1.4;
  /* lift slightly so chip baseline aligns with surrounding text */
  vertical-align: baseline;
}
.placeholder-chip:hover {
  background: color-mix(in srgb, var(--color-primary) 18%, transparent);
}
.placeholder-chip:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
.placeholder-chip--active {
  background: var(--color-primary);
  color: #fff;
}

.placeholder-chip--empty {
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border);
  padding: 0 8px;
}
.placeholder-chip--empty:hover {
  background: var(--color-surface-3);
  color: var(--color-text);
  border-style: solid;
}
.placeholder-chip__empty i { font-size: 0.7em; }
</style>
