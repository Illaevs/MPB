<template>
  <Teleport to="body">
    <transition name="confirm">
      <div v-if="state.visible" class="confirm-overlay" v-modal-close="reject">
        <div class="confirm-card" role="alertdialog" aria-modal="true">
          <h4 class="confirm-title">{{ state.title }}</h4>
          <div v-if="state.message" class="confirm-message">{{ state.message }}</div>
          <div class="confirm-actions">
            <UiButton variant="ghost" size="sm" @click="reject">
              {{ state.cancelText }}
            </UiButton>
            <UiButton
              ref="confirmBtn"
              :variant="confirmVariant"
              size="sm"
              @click="accept"
            >
              {{ state.confirmText }}
            </UiButton>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script>
import { computed, watch, nextTick, ref } from 'vue'
import { useConfirm } from '../../composables/useConfirm'
import UiButton from './UiButton.vue'

export default {
  name: 'ConfirmDialog',
  components: { UiButton },
  setup() {
    const { state, accept, reject } = useConfirm()
    const confirmBtn = ref(null)

    const confirmVariant = computed(() => {
      const v = state.value.variant
      if (v === 'danger') return 'danger'
      if (v === 'warning') return 'warning'
      return 'primary'
    })

    const onKey = (e) => {
      if (!state.value.visible) return
      if (e.key === 'Escape') reject()
      if (e.key === 'Enter') accept()
    }

    watch(() => state.value.visible, (vis) => {
      if (vis) {
        document.addEventListener('keydown', onKey)
        nextTick(() => {
          const btnRef = confirmBtn.value
          const el = btnRef?.$el || btnRef
          el?.focus?.()
        })
      } else {
        document.removeEventListener('keydown', onKey)
      }
    })

    return { state, accept, reject, confirmVariant, confirmBtn }
  }
}
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.48);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  backdrop-filter: blur(2px);
}

.confirm-card {
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  width: 100%;
  max-width: 420px;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
}

.confirm-title {
  margin: 0 0 var(--space-2);
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
}

.confirm-message {
  font-size: var(--text-md);
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  line-height: var(--leading-normal);
  white-space: pre-wrap;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.confirm-enter-active,
.confirm-leave-active {
  transition: opacity var(--dur-fast) var(--ease-out);
}
.confirm-enter-active .confirm-card,
.confirm-leave-active .confirm-card {
  transition: transform var(--dur-fast) var(--ease-out);
}
.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}
.confirm-enter-from .confirm-card,
.confirm-leave-to .confirm-card {
  transform: translateY(8px) scale(0.98);
}
</style>
