<template>
  <div class="ui-chip-filter" :class="{ 'is-open': open }">
    <button
      ref="btnEl"
      type="button"
      class="ui-chip-filter__btn"
      :class="[selectedOption ? 'is-selected' : 'is-empty']"
      :style="chipStyle"
      :disabled="disabled"
      @click="toggle"
    >
      <span v-if="selectedOption && selectedOption.color" class="ui-chip-filter__dot"></span>
      <i v-else-if="emptyIcon" class="ui-chip-filter__icon" :class="emptyIcon"></i>
      <span class="ui-chip-filter__label">
        {{ selectedOption ? selectedOption.label : placeholder }}
      </span>
      <span v-if="resolvedCount != null" class="ui-chip-filter__count">{{ resolvedCount }}</span>
      <i class="fas fa-caret-down ui-chip-filter__caret"></i>
    </button>
    <transition name="ui-chip-filter-pop">
      <div v-if="open" v-click-outside="closeMenu" class="ui-chip-filter__menu" :class="{ 'align-right': alignRight }">
        <button
          type="button"
          class="ui-chip-filter__item is-empty-option"
          :class="{ 'is-active': isEmptyValue }"
          @click="select(emptyValue)"
        >
          <span class="ui-chip-filter__item-label">{{ placeholder }}</span>
          <span v-if="totalCount != null" class="ui-chip-filter__item-count">{{ totalCount }}</span>
          <i v-if="isEmptyValue" class="fas fa-check ui-chip-filter__check"></i>
        </button>
        <div class="ui-chip-filter__divider"></div>
        <button
          v-for="opt in options"
          :key="String(opt.value)"
          type="button"
          class="ui-chip-filter__item"
          :class="{ 'is-active': isActive(opt) }"
          :style="opt.color ? { '--chip-color': opt.color } : null"
          @click="select(opt.value)"
        >
          <span v-if="opt.color" class="ui-chip-filter__dot"></span>
          <span class="ui-chip-filter__item-label">{{ opt.label }}</span>
          <span v-if="getCount(opt) != null" class="ui-chip-filter__item-count">{{ getCount(opt) }}</span>
          <i v-if="isActive(opt)" class="fas fa-check ui-chip-filter__check"></i>
        </button>
      </div>
    </transition>
  </div>
</template>

<script>
import { computed, ref } from 'vue'

/**
 * Универсальный chip-фильтр (взят за основу из Contracts.vue, обобщён).
 *
 * Использование:
 *   <UiChipFilter
 *     v-model="status"
 *     :options="STATUS_OPTIONS"
 *     placeholder="Все статусы"
 *     empty-icon="fas fa-circle-half-stroke"
 *     :counts="{ active: 12, completed: 3, total: 47 }"
 *   />
 *
 *   STATUS_OPTIONS = [
 *     { value: 'active',    label: 'Активные',    color: '#22c55e' },
 *     { value: 'completed', label: 'Завершённые', color: '#3b82f6' },
 *   ]
 *
 * - Цвет берётся из option.color (любая CSS-цветовая строка).
 * - Подсчёты передаются через counts (объект с ключами option.value и total).
 * - Пустое значение по умолчанию — '', можно переопределить через empty-value.
 */
export default {
  name: 'UiChipFilter',
  directives: {
    'click-outside': {
      beforeMount(el, binding) {
        el._co = (e) => {
          if (!(el === e.target || el.contains(e.target))) binding.value(e)
        }
        setTimeout(() => document.addEventListener('click', el._co), 0)
      },
      unmounted(el) {
        document.removeEventListener('click', el._co)
      },
    },
  },
  props: {
    modelValue: { type: [String, Number, null], default: '' },
    options: { type: Array, required: true },
    placeholder: { type: String, default: 'Все' },
    emptyIcon: { type: String, default: '' },
    counts: { type: Object, default: () => ({}) },
    /**
     * Значение, считающееся "пустым" (выбрано пункт "все").
     * По умолчанию пустая строка.
     */
    emptyValue: { type: [String, Number, null], default: '' },
    /** Показать total count в чипе, когда фильтр не выбран. */
    showTotalInChip: { type: Boolean, default: true },
    /** Выравнивание выпадашки по правому краю кнопки. */
    alignRight: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const open = ref(false)
    const btnEl = ref(null)

    const isEmptyValue = computed(() => {
      const v = props.modelValue
      const empty = props.emptyValue
      if (v == null && empty == null) return true
      if (v === '' && empty === '') return true
      return String(v ?? '') === String(empty ?? '')
    })

    const selectedOption = computed(() => {
      if (isEmptyValue.value) return null
      return props.options.find((o) => String(o.value) === String(props.modelValue)) || null
    })

    const totalCount = computed(() =>
      props.counts && props.counts.total != null ? props.counts.total : null
    )

    const getCount = (opt) => {
      if (!props.counts) return null
      const c = props.counts[opt.value]
      return c == null ? null : c
    }

    const resolvedCount = computed(() => {
      if (selectedOption.value) {
        const c = getCount(selectedOption.value)
        return c != null ? c : null
      }
      return props.showTotalInChip ? totalCount.value : null
    })

    const chipStyle = computed(() => {
      if (selectedOption.value?.color) {
        return { '--chip-color': selectedOption.value.color }
      }
      return null
    })

    const isActive = (opt) => String(props.modelValue) === String(opt.value)

    const toggle = () => {
      if (props.disabled) return
      open.value = !open.value
    }

    const closeMenu = () => {
      open.value = false
    }

    const select = (value) => {
      emit('update:modelValue', value)
      open.value = false
    }

    return {
      open,
      btnEl,
      isEmptyValue,
      selectedOption,
      totalCount,
      resolvedCount,
      chipStyle,
      isActive,
      getCount,
      toggle,
      closeMenu,
      select,
    }
  },
}
</script>

<style scoped>
.ui-chip-filter {
  position: relative;
  display: inline-flex;
}

.ui-chip-filter__btn {
  --chip-color: var(--color-text);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition: background var(--dur-fast) ease, border-color var(--dur-fast) ease, color var(--dur-fast) ease;
  white-space: nowrap;
}

.ui-chip-filter__btn:hover:not(:disabled) {
  background: var(--color-surface-3);
}

.ui-chip-filter__btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ui-chip-filter__btn.is-selected {
  color: var(--chip-color);
  border-color: color-mix(in srgb, var(--chip-color) 45%, transparent);
  background: color-mix(in srgb, var(--chip-color) 8%, var(--color-surface));
}

.ui-chip-filter__btn.is-selected:hover:not(:disabled) {
  background: color-mix(in srgb, var(--chip-color) 12%, var(--color-surface));
}

.ui-chip-filter__icon {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.ui-chip-filter__label {
  font-weight: var(--fw-semibold);
}

.ui-chip-filter__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 18px;
  padding: 0 6px;
  border-radius: 9px;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: 0.72rem;
  font-weight: var(--fw-semibold);
  line-height: 1;
}

.is-selected .ui-chip-filter__count {
  background: color-mix(in srgb, var(--chip-color) 16%, transparent);
  color: var(--chip-color);
}

.ui-chip-filter__caret {
  font-size: 0.7rem;
  opacity: 0.65;
}

.ui-chip-filter__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--chip-color);
  flex-shrink: 0;
}

.ui-chip-filter__menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 50;
  min-width: 200px;
  max-width: 320px;
  padding: 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.ui-chip-filter__menu.align-right {
  left: auto;
  right: 0;
}

.ui-chip-filter__item {
  --chip-color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: 6px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  font-size: var(--text-sm);
  cursor: pointer;
  text-align: left;
  transition: background var(--dur-fast) ease, color var(--dur-fast) ease;
}

.ui-chip-filter__item:hover {
  background: var(--color-surface-3);
}

.ui-chip-filter__item.is-active {
  font-weight: var(--fw-semibold);
}

.ui-chip-filter__item:not(.is-empty-option) {
  color: var(--chip-color);
}

.ui-chip-filter__item:not(.is-empty-option):hover {
  background: color-mix(in srgb, var(--chip-color) 10%, transparent);
}

.ui-chip-filter__item-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ui-chip-filter__item-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 18px;
  padding: 0 6px;
  border-radius: 9px;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: 0.7rem;
  font-weight: var(--fw-semibold);
  line-height: 1;
}

.ui-chip-filter__check {
  font-size: 0.7rem;
  opacity: 0.85;
}

.ui-chip-filter__divider {
  height: 1px;
  margin: 4px 2px;
  background: var(--color-border-subtle);
}

.ui-chip-filter-pop-enter-active,
.ui-chip-filter-pop-leave-active {
  transition: opacity var(--dur-fast) ease, transform var(--dur-fast) ease;
}

.ui-chip-filter-pop-enter-from,
.ui-chip-filter-pop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
