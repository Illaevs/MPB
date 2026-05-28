<template>
  <div class="ui-pager" :class="`ui-pager--${size}`">
    <UiIconButton
      icon="fas fa-chevron-left"
      label="Назад"
      :size="iconSize"
      :disabled="loading || currentPage <= 1"
      @click="setPage(currentPage - 1)"
    />

    <span class="ui-pager__label">{{ currentPage }}<span class="ui-pager__total">/{{ totalPages }}</span></span>

    <UiIconButton
      icon="fas fa-chevron-right"
      label="Вперёд"
      :size="iconSize"
      :disabled="loading || currentPage >= totalPages"
      @click="setPage(currentPage + 1)"
    />

    <UiSelect
      class="ui-pager__size"
      :model-value="pageSize"
      :options="sizeOptions"
      :disabled="loading"
      :size="size"
      :block="false"
      @update:modelValue="setPageSize"
    />
  </div>
</template>

<script>
import { computed } from 'vue'
import UiIconButton from './UiIconButton.vue'
import UiSelect from './UiSelect.vue'

const SIZES = ['sm', 'md']

export default {
  name: 'UiPager',
  components: { UiIconButton, UiSelect },
  props: {
    modelValue: { type: Number, default: 1 },
    total: { type: Number, default: 0 },
    pageSize: { type: Number, default: 20 },
    pageSizes: { type: Array, default: () => [10, 20, 50, 100, 200] },
    loading: { type: Boolean, default: false },
    size: { type: String, default: 'sm', validator: v => SIZES.includes(v) }
  },
  emits: ['update:modelValue', 'update:pageSize', 'change'],
  setup(props, { emit }) {
    const totalPages = computed(() => Math.max(1, Math.ceil((Number(props.total) || 0) / Math.max(1, Number(props.pageSize) || 1))))
    const currentPage = computed(() => {
      const page = Number(props.modelValue) || 1
      return Math.min(Math.max(1, page), totalPages.value)
    })
    const sizeOptions = computed(() => props.pageSizes.map(value => ({ value, label: String(value) })))
    const iconSize = computed(() => (props.size === 'sm' ? 'sm' : 'md'))

    const setPage = (page) => {
      const next = Math.min(Math.max(1, page), totalPages.value)
      if (next === currentPage.value) return
      emit('update:modelValue', next)
      emit('change', next)
    }

    const setPageSize = (value) => {
      const nextSize = Number(value) || props.pageSize
      if (nextSize !== props.pageSize) emit('update:pageSize', nextSize)
      const nextPage = Math.min(currentPage.value, Math.max(1, Math.ceil((Number(props.total) || 0) / Math.max(1, nextSize))))
      if (nextPage !== props.modelValue) emit('update:modelValue', nextPage)
      emit('change', nextPage)
    }

    return { currentPage, totalPages, sizeOptions, iconSize, setPage, setPageSize }
  }
}
</script>

<style scoped>
.ui-pager {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.ui-pager__label {
  display: inline-flex;
  align-items: baseline;
  gap: 1px;
  min-width: 44px;
  justify-content: center;
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.ui-pager__total {
  color: var(--color-text-muted);
}

.ui-pager__size {
  min-width: 74px;
}

.ui-pager--sm .ui-pager__label {
  font-size: var(--text-sm);
}

.ui-pager--md .ui-pager__label {
  font-size: var(--text-base);
  min-width: 56px;
}

.ui-pager--md {
  gap: var(--space-3);
}
</style>
