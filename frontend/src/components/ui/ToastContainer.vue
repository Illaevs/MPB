<template>
  <Teleport to="body">
    <div class="toast-container">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-card"
          :class="`toast-${toast.type}`"
          @click="remove(toast.id)"
        >
          <div class="toast-icon">
            <i v-if="toast.type === 'success'" class="fas fa-check-circle"></i>
            <i v-if="toast.type === 'error'" class="fas fa-exclamation-circle"></i>
            <i v-if="toast.type === 'info'" class="fas fa-info-circle"></i>
            <i v-if="toast.type === 'warning'" class="fas fa-exclamation-triangle"></i>
          </div>
          <div class="toast-message">{{ toast.message }}</div>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script>
import { useToast } from '../../composables/useToast'

export default {
  name: 'ToastContainer',
  setup() {
    const { toasts, remove } = useToast()
    return { toasts, remove }
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none; /* Let clicks pass through container */
}

.toast-card {
  pointer-events: auto;
  min-width: 300px;
  max-width: 400px;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--md-sys-color-surface-thick);
  border: 1px solid var(--md-sys-color-outline);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
  backdrop-filter: blur(20px) saturate(180%);
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.toast-message {
  font-size: 13px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

/* Types */
.toast-success .toast-icon { color: var(--color-success); }
.toast-error .toast-icon { color: var(--color-danger); }
.toast-warning .toast-icon { color: var(--color-warning); }
.toast-info .toast-icon { color: var(--color-info); }

/* Animation */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(30px) scale(0.9);
}
</style>
