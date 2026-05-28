<template>
  <div
    class="star-rating"
    :class="{ 'is-readonly': readonly }"
    @mouseleave="hover = 0"
  >
    <button
      v-for="i in 5"
      :key="i"
      type="button"
      class="star-rating__star"
      :disabled="readonly"
      :title="`${display.toFixed(1)} из 5`"
      @mousemove="onMove($event, i)"
      @click="onClick($event, i)"
    >
      <i class="far fa-star star-rating__bg"></i>
      <span class="star-rating__fill" :style="{ width: fillPct(i) + '%' }">
        <i class="fas fa-star"></i>
      </span>
    </button>
    <button
      v-if="!readonly && Number(modelValue) > 0"
      type="button"
      class="star-rating__clear"
      title="Сбросить"
      @click.stop="emitValue(0)"
    >
      <i class="fas fa-xmark"></i>
    </button>
    <span v-if="showValue" class="star-rating__num">{{ display.toFixed(1) }}</span>
  </div>
</template>

<script>
import { computed, ref } from 'vue'

export default {
  name: 'StarRating',
  props: {
    modelValue: { type: [Number, String], default: 0 },
    readonly: { type: Boolean, default: false },
    showValue: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const hover = ref(0)

    const current = computed(() => {
      const h = hover.value
      if (h > 0) return h
      const v = Number(props.modelValue) || 0
      return Math.min(5, Math.max(0, Math.round(v * 2) / 2))
    })

    const display = computed(() => current.value)

    const fillPct = (i) => {
      const c = current.value
      if (c >= i) return 100
      if (c >= i - 0.5) return 50
      return 0
    }

    const valueAt = (event, i) => {
      const rect = event.currentTarget.getBoundingClientRect()
      const isLeftHalf = event.clientX - rect.left < rect.width / 2
      return i - (isLeftHalf ? 0.5 : 0)
    }

    const onMove = (event, i) => {
      if (props.readonly) return
      hover.value = valueAt(event, i)
    }

    const emitValue = (v) => {
      hover.value = 0
      emit('update:modelValue', Math.min(5, Math.max(0, Math.round(v * 2) / 2)))
    }

    const onClick = (event, i) => {
      if (props.readonly) return
      emitValue(valueAt(event, i))
    }

    return { hover, display, fillPct, onMove, onClick, emitValue }
  },
}
</script>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  line-height: 1;
}

.star-rating__star {
  position: relative;
  width: 18px;
  height: 18px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #f59e0b;
  font-size: 15px;
}

.star-rating.is-readonly .star-rating__star {
  cursor: default;
}

.star-rating__bg {
  color: var(--color-border-strong, #cbd5e1);
}

.star-rating__fill {
  position: absolute;
  inset: 0;
  overflow: hidden;
  white-space: nowrap;
  color: #f59e0b;
}

.star-rating__fill i {
  font-size: 15px;
}

.star-rating__clear {
  margin-left: 4px;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-subtle, #94a3b8);
  cursor: pointer;
  font-size: 11px;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease;
}

.star-rating:hover .star-rating__clear {
  opacity: 1;
}

.star-rating__clear:hover {
  color: var(--color-danger, #dc2626);
}

.star-rating__num {
  margin-left: 5px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-muted, #64748b);
}
</style>
