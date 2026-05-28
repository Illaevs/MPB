<template>
  <teleport to="body">
    <transition name="ui-drawer">
      <div
        v-if="modelValue"
        class="ui-drawer__overlay"
        v-modal-close="onOverlayClick"
      >
        <aside
          class="ui-drawer"
          :class="[`ui-drawer--${side}`, `ui-drawer--${size}`]"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : null"
        >
          <header v-if="$slots.header || title || closable" class="ui-drawer__header">
            <slot name="header">
              <h3 v-if="title" :id="titleId" class="ui-drawer__title">{{ title }}</h3>
            </slot>
            <button
              v-if="closable"
              type="button"
              class="ui-drawer__close"
              aria-label="Закрыть"
              @click="close"
            >
              <i class="fa fa-times" aria-hidden="true"></i>
            </button>
          </header>

          <div class="ui-drawer__body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="ui-drawer__footer">
            <slot name="footer" />
          </footer>
        </aside>
      </div>
    </transition>
  </teleport>
</template>

<script>
import { onBeforeUnmount, watch } from 'vue'

let uid = 0

const SIDES = ['right', 'left']
const SIZES = ['sm', 'md', 'lg', 'xl']

export default {
  name: 'UiDrawer',
  props: {
    modelValue: { type: Boolean, default: false },
    side: { type: String, default: 'right', validator: v => SIDES.includes(v) },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    title: { type: String, default: null },
    closable: { type: Boolean, default: true },
    closeOnOverlay: { type: Boolean, default: true },
    closeOnEsc: { type: Boolean, default: true }
  },
  emits: ['update:modelValue', 'close'],
  setup(props, { emit }) {
    const titleId = `ui-drawer-title-${++uid}`

    const close = () => {
      emit('update:modelValue', false)
      emit('close')
    }

    const onOverlayClick = () => {
      if (props.closeOnOverlay) close()
    }

    const onKeyDown = (event) => {
      if (event.key === 'Escape' && props.closeOnEsc) close()
    }

    const lockScroll = (lock) => {
      if (typeof document === 'undefined') return
      document.body.style.overflow = lock ? 'hidden' : ''
    }

    watch(() => props.modelValue, (value) => {
      lockScroll(value)
      if (typeof window === 'undefined') return
      const method = value ? 'addEventListener' : 'removeEventListener'
      window[method]('keydown', onKeyDown)
    }, { immediate: true })

    onBeforeUnmount(() => {
      lockScroll(false)
      if (typeof window !== 'undefined') window.removeEventListener('keydown', onKeyDown)
    })

    return { titleId, close, onOverlayClick }
  }
}
</script>

<style scoped>
.ui-drawer__overlay {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 1000;
}

.ui-drawer {
  height: 100dvh;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
  box-shadow: var(--shadow-xl);
}

.ui-drawer--left {
  margin-right: auto;
  border-left: none;
}

.ui-drawer--right {
  margin-left: auto;
  border-right: none;
}

.ui-drawer--sm { width: 360px; }
.ui-drawer--md { width: 480px; }
.ui-drawer--lg { width: 640px; }
.ui-drawer--xl { width: 840px; }

.ui-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.ui-drawer__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.ui-drawer__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--dur-fast) ease, color var(--dur-fast) ease;
}

.ui-drawer__close:hover {
  background: var(--color-surface-3);
  color: var(--color-text);
}

.ui-drawer__close:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.ui-drawer__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-5);
}

.ui-drawer__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface-2);
  flex-shrink: 0;
}

.ui-drawer-enter-active,
.ui-drawer-leave-active {
  transition: opacity var(--dur-slow) ease;
}

.ui-drawer-enter-active .ui-drawer,
.ui-drawer-leave-active .ui-drawer {
  transition: transform var(--dur-slow) var(--ease-out);
}

.ui-drawer-enter-from,
.ui-drawer-leave-to {
  opacity: 0;
}

.ui-drawer-enter-from .ui-drawer--right,
.ui-drawer-leave-to .ui-drawer--right {
  transform: translateX(100%);
}

.ui-drawer-enter-from .ui-drawer--left,
.ui-drawer-leave-to .ui-drawer--left {
  transform: translateX(-100%);
}
</style>
