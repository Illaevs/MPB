import axios from 'axios'
import { setActivePinia } from 'pinia'
import router from '../router'
import { useAuthStore } from '../stores/auth'
import { setFromHttpDate } from '../composables/useServerClock'

function getCookie(name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : ''
}

export function setupHttpInterceptors(pinia) {
  if (pinia) {
    setActivePinia(pinia)
  }

  const auth = useAuthStore()
  auth.loadFromStorage()
  axios.defaults.withCredentials = true

  axios.interceptors.request.use(
    (config) => {
      config.withCredentials = true
      const method = String(config.method || 'get').toUpperCase()
      if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
        const csrfToken = getCookie('crm_csrf_token')
        if (csrfToken) {
          config.headers = config.headers || {}
          config.headers['X-CSRF-Token'] = csrfToken
        }
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  let isRefreshing = false
  let pending = []

  const onRefreshed = () => {
    pending.forEach((cb) => cb())
    pending = []
  }

  axios.interceptors.response.use(
    (response) => {
      // Каждый успешный ответ несёт стандартный HTTP-заголовок Date —
      // используем его, чтобы выставить смещение серверных часов от
      // локальных. Так счётчик рабочего дня и часы в шапке устойчивы
      // к спешащим/отстающим часам устройства.
      try { setFromHttpDate(response.headers?.date) } catch { /* noop */ }
      return response
    },
    async (error) => {
      // На неуспешном ответе Date тоже есть — обновляем смещение.
      try { setFromHttpDate(error?.response?.headers?.date) } catch { /* noop */ }
      const { config, response } = error
      const isAuthRequest =
        config?.url?.includes('/api/v1/auth/refresh') ||
        config?.url?.includes('/api/v1/auth/login') ||
        config?.url?.includes('/api/v1/auth/verify-2fa') ||
        config?.url?.includes('/api/v1/auth/logout') ||
        config?.url?.includes('/api/v1/auth/session')

      if (
        response?.status === 403 &&
        response?.data?.detail === 'Требуется обязательная настройка двухфакторной аутентификации.'
      ) {
        if (router.currentRoute.value.path !== '/login') {
          router.replace('/login')
        }
        return Promise.reject(error)
      }

      if (!response || response.status !== 401) {
        return Promise.reject(error)
      }

        if (!auth.accessToken) {
          return Promise.reject(error)
        }

      if (config?.__isRetry || isAuthRequest) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pending.push(() => {
            config.__isRetry = true
            resolve(axios(config))
          })
        })
      }

      isRefreshing = true
      try {
        await auth.refresh()
        onRefreshed()
        config.__isRetry = true
        return axios(config)
      } catch (refreshError) {
        await auth.logout()
        if (router.currentRoute.value.path !== '/login') {
          router.replace('/login')
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
  )
}
