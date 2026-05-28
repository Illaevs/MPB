import { ref } from 'vue'

const toasts = ref([])

export function useToast() {
  const add = (type, message, duration = 3000) => {
    const id = Date.now() + Math.random()
    toasts.value.push({ id, type, message })
    
    setTimeout(() => {
      remove(id)
    }, duration)
  }

  const remove = (id) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (msg, duration) => add('success', msg, duration)
  const error = (msg, duration) => add('error', msg, duration)
  const info = (msg, duration) => add('info', msg, duration)
  const warning = (msg, duration) => add('warning', msg, duration)

  return {
    toasts,
    add,
    remove,
    success,
    error,
    info,
    warning
  }
}
