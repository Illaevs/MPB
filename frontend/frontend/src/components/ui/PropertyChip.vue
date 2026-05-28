<template>
  <div
    class="property-chip"
    :class="{
      'property-chip--open': open,
      'property-chip--empty': isEmpty,
      'property-chip--disabled': disabled
    }"
    ref="root"
  >
    <button
      type="button"
      class="property-chip__btn"
      :disabled="disabled"
      :aria-expanded="open"
      :aria-haspopup="true"
      :title="label ? label + (isEmpty ? '' : ': ' + (textValue || '')) : null"
      @click="toggle"
    >
      <span v-if="dotColor" class="property-chip__dot" :style="{ background: dotColor }"></span>
      <i
        v-else-if="icon"
        class="property-chip__icon"
        :class="icon"
        :style="iconColor ? { color: iconColor } : null"
      ></i>
      <span class="property-chip__text" :class="{ 'property-chip__text--muted': isEmpty }">
        <slot name="value">
          {{ isEmpty ? (placeholder || '+ Добавить') : textValue }}
        </slot>
      </span>
      <i class="fas fa-caret-down property-chip__caret" aria-hidden="true"></i>
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        ref="popover"
        class="property-chip__popover"
        role="dialog"
        :style="popoverStyle"
        @click.stop
      >
        <slot name="popover" :close="close" />
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, onBeforeUnmount, watch, nextTick } from 'vue'

export default {
  name: 'PropertyChip',
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number, null], default: null },
    icon: { type: String, default: '' },
    iconColor: { type: String, default: '' },
    dotColor: { type: String, default: '' },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    align: { type: String, default: 'start' } // 'start' | 'end'
  },
  emits: ['open', 'close'],
  setup(props, { emit }) {
    const open = ref(false)
    const root = ref(null)
    const popover = ref(null)
    const popoverStyle = ref({})

    const textValue = computed(() => {
      if (props.value === null || props.value === undefined) return ''
      return String(props.value)
    })
    const isEmpty = computed(() => textValue.value.trim() === '')

    function recomputePopoverPosition() {
      if (!root.value) return
      const btn = root.value.querySelector('.property-chip__btn')
      if (!btn) return
      const r = btn.getBoundingClientRect()
      const align = props.align === 'end'
      popoverStyle.value = {
        position: 'fixed',
        top: `${r.bottom + 6}px`,
        zIndex: 2200,
        ...(align
          ? { right: `${Math.max(8, window.innerWidth - r.right)}px` }
          : { left: `${Math.max(8, r.left)}px` })
      }
    }

    function close() {
      if (!open.value) return
      open.value = false
      emit('close')
    }
    function toggle() {
      if (props.disabled) return
      if (open.value) close()
      else {
        open.value = true
        emit('open')
        nextTick(() => {
          recomputePopoverPosition()
          attachOutside()
        })
      }
    }

    function onOutsideMousedown(ev) {
      if (!root.value) return
      // popover is teleported to <body>, so contains() on root won't see it.
      if (root.value.contains(ev.target)) return
      if (popover.value && popover.value.contains(ev.target)) return
      close()
    }
    function onWindowResize() {
      if (open.value) recomputePopoverPosition()
    }
    function onEscape(ev) {
      if (ev.key === 'Escape' && open.value) {
        ev.stopPropagation()
        close()
      }
    }
    function attachOutside() {
      document.addEventListener('mousedown', onOutsideMousedown)
      document.addEventListener('keydown', onEscape, true)
      window.addEventListener('resize', onWindowResize)
      window.addEventListener('scroll', onWindowResize, true)
    }
    function detachOutside() {
      document.removeEventListener('mousedown', onOutsideMousedown)
      document.removeEventListener('keydown', onEscape, true)
      window.removeEventListener('resize', onWindowResize)
      window.removeEventListener('scroll', onWindowResize, true)
    }

    watch(open, (v) => {
      if (!v) detachOutside()
    })
    onBeforeUnmount(detachOutside)

    return { open, root, popover, isEmpty, textValue, popoverStyle, toggle, close }
  }
}
</script>

<style>
/* not scoped — popover teleports to <body> and needs reachable selectors */
.property-chip {
  position: relative;
  display: inline-flex;
}

.property-chip__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 var(--space-3);
  height: 32px;
  background: var(--color-surface-2);
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
  max-width: 100%;
}
.property-chip__btn:hover {
  background: var(--color-surface-3);
}
.property-chip__btn:focus-visible {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.property-chip__btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.property-chip--open .property-chip__btn {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.property-chip__dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-text-subtle);
}

.property-chip__icon {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.property-chip__text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}
.property-chip__text--muted {
  color: var(--color-text-subtle);
  font-weight: var(--fw-regular);
}

.property-chip__caret {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}

.property-chip__popover {
  position: absolute;
  top: calc(100% + 6px);
  min-width: 220px;
  max-width: 360px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2);
  z-index: 50;
  animation: property-chip-pop var(--dur-fast) var(--ease-out);
}

@keyframes property-chip-pop {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
