import { defineStore } from 'pinia'

const statusLabelMap = {
  preparing: 'Подготовка',
  downloading: 'Скачивание',
  done: 'Готово',
  error: 'Ошибка'
}

const SUCCESS_AUTO_DISMISS_MS = 5000
const autoDismissTimers = new Map()

export const useDownloadQueueStore = defineStore('downloadQueue', {
  state: () => ({
    items: []
  }),
  getters: {
    hasItems: (state) => state.items.length > 0
  },
  actions: {
    addLocalDownload({ fileName, module, entityId }) {
      const localId = `download-${Date.now()}-${Math.random().toString(16).slice(2)}`
      this.items.unshift({
        id: localId,
        localId,
        file_name: fileName || 'Файл',
        status: 'preparing',
        progress: 0,
        indeterminate: true,
        error_message: null,
        module: module || null,
        entity_id: entityId || null
      })
      this._trim()
      return localId
    },
    updateProgress(localId, progress, options = {}) {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (!item) return
      if (options.fileName) {
        item.file_name = options.fileName
      }
      item.status = options.status || 'downloading'
      item.indeterminate = !!options.indeterminate
      if (typeof progress === 'number' && Number.isFinite(progress)) {
        item.progress = Math.min(100, Math.max(0, Math.round(progress)))
      }
    },
    rename(localId, fileName) {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (item && fileName) {
        item.file_name = fileName
      }
    },
    markDone(localId, fileName = '') {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (!item) return
      if (fileName) item.file_name = fileName
      item.status = 'done'
      item.progress = 100
      item.indeterminate = false
      item.error_message = null
      this._scheduleAutoDismiss(item.id)
    },
    markError(localId, message) {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (!item) return
      this._clearAutoDismiss(item.id)
      item.status = 'error'
      item.indeterminate = false
      item.error_message = message || 'Ошибка скачивания'
    },
    clearFinished() {
      this.items
        .filter((item) => item.status === 'done' || item.status === 'error')
        .forEach((item) => this._clearAutoDismiss(item.id))
      this.items = this.items.filter((item) => item.status !== 'done' && item.status !== 'error')
    },
    removeItem(id) {
      if (!id) return
      this._clearAutoDismiss(id)
      this.items = this.items.filter((item) => item.id !== id && item.localId !== id)
    },
    statusLabel(status) {
      return statusLabelMap[status] || status
    },
    _scheduleAutoDismiss(id) {
      if (!id || autoDismissTimers.has(id)) return
      const timerId = setTimeout(() => {
        autoDismissTimers.delete(id)
        this.removeItem(id)
      }, SUCCESS_AUTO_DISMISS_MS)
      autoDismissTimers.set(id, timerId)
    },
    _clearAutoDismiss(id) {
      const timerId = autoDismissTimers.get(id)
      if (timerId) {
        clearTimeout(timerId)
        autoDismissTimers.delete(id)
      }
    },
    _trim() {
      if (this.items.length > 20) {
        this.items = this.items.slice(0, 20)
      }
    }
  }
})
