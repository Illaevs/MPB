<template>
  <teleport to="body">
    <transition name="ui-modal">
      <div
        v-if="modelValue"
        class="ui-modal__overlay"
        v-modal-close="onOverlayClick"
        @keydown.esc="onEsc"
        tabindex="-1"
      >
        <div
          class="ui-modal"
          :class="[`ui-modal--${size}`, { 'ui-modal--scroll-body': scrollBody }]"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : null"
        >
          <header v-if="$slots.header || title" class="ui-modal__header">
            <slot name="header">
              <h3 :id="titleId" class="ui-modal__title">{{ title }}</h3>
            </slot>
            <button
              v-if="closable"
              type="button"
              class="ui-modal__close"
              aria-label="Закрыть"
              @click="close"
            >
              <i class="fa fa-times" aria-hidden="true"></i>
            </button>
          </header>

          <div class="ui-modal__body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="ui-modal__footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script>
import { computed, watch, onBeforeUnmount } from 'vue'

let uid = 0
const SIZES = ['sm', 'md', 'lg', 'xl', 'full']

export default {
  name: 'UiModal',
  props: {
    modelValue: { type: Boolean, default: false },
    title: { type: String, default: null },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    closable: { type: Boolean, default: true },
    closeOnOverlay: { type: Boolean, default: true },
    closeOnEsc: { type: Boolean, default: true },
    scrollBody: { type: Boolean, default: true }
  },
  emits: ['update:modelValue', 'close'],
  setup(props, { emit }) {
    const titleId = `ui-modal-title-${++uid}`

    const close = () => {
      emit('update:modelValue', false)
      emit('close')
    }

    const onOverlayClick = () => { if (props.closeOnOverlay) close() }
    const onEsc = () => { if (props.closeOnEsc) close() }

    const lockScroll = (lock) => {
      if (typeof document === 'undefined') return
      document.body.style.overflow = lock ? 'hidden' : ''
    }

    watch(() => props.modelValue, (v) => lockScroll(v), { immediate: true })
    onBeforeUnmount(() => lockScroll(false))

    return { titleId, close, onOverlayClick, onEsc }
  }
}
</script>

<style scoped>
.ui-modal__overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  z-index: 1000;
}

.ui-modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-height: calc(100dvh - 2 * var(--space-4));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ui-modal--sm { max-width: 420px; }
.ui-modal--md { max-width: 640px; }
.ui-modal--lg { max-width: 880px; }
.ui-modal--xl { max-width: 1200px; }
.ui-modal--full {
  max-width: none;
  width: calc(100vw - 2 * var(--space-4));
  height: calc(100dvh - 2 * var(--space-4));
}

.ui-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.ui-modal__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.ui-modal__close {
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
.ui-modal__close:hover { background: var(--color-surface-3); color: var(--color-text); }
.ui-modal__close:focus-visible { outline: none; box-shadow: var(--shadow-focus); }

.ui-modal__body {
  padding: var(--space-5);
  flex: 1;
  min-height: 0;
}
.ui-modal--scroll-body .ui-modal__body { overflow-y: auto; }

.ui-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface-2);
  flex-shrink: 0;
}

.ui-modal-enter-active,
.ui-modal-leave-active { transition: opacity var(--dur-base) ease; }
.ui-modal-enter-active .ui-modal,
.ui-modal-leave-active .ui-modal { transition: transform var(--dur-base) var(--ease-out); }
.ui-modal-enter-from,
.ui-modal-leave-to { opacity: 0; }
.ui-modal-enter-from .ui-modal,
.ui-modal-leave-to .ui-modal { transform: translateY(8px) scale(0.98); }
</style>
