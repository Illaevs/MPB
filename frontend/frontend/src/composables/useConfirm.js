import { ref } from 'vue'

const state = ref({
  visible: false,
  title: '',
  message: '',
  confirmText: 'Подтвердить',
  cancelText: 'Отмена',
  variant: 'primary',
  resolve: null
})

export function useConfirm() {
  const confirm = (options = {}) => {
    return new Promise((resolve) => {
      state.value = {
        visible: true,
        title: options.title || 'Подтверждение',
        message: options.message || '',
        confirmText: options.confirmText || 'Подтвердить',
        cancelText: options.cancelText || 'Отмена',
        variant: options.variant || 'primary',
        resolve
      }
    })
  }

  const accept = () => {
    if (state.value.resolve) state.value.resolve(true)
    state.value.visible = false
    state.value.resolve = null
  }

  const reject = () => {
    if (state.value.resolve) state.value.resolve(false)
    state.value.visible = false
    state.value.resolve = null
  }

  return { state, confirm, accept, reject }
}
