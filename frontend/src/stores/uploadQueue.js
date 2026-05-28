import { defineStore } from 'pinia'
import axios from 'axios'

const statusLabelMap = {
  uploading: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430',
  queued: '\u0412 \u043e\u0447\u0435\u0440\u0435\u0434\u0438',
  processing: '\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
  done: '\u0413\u043e\u0442\u043e\u0432\u043e',
  error: '\u041e\u0448\u0438\u0431\u043a\u0430'
}

const DISMISSED_KEY = 'crm_upload_queue_dismissed'
const HISTORY_TTL_MS = 2 * 60 * 60 * 1000
const SUCCESS_AUTO_DISMISS_MS = 5000
const autoDismissTimers = new Map()

const loadDismissed = () => {
  try {
    const raw = localStorage.getItem(DISMISSED_KEY)
    return raw ? JSON.parse(raw) : []
  } catch (e) {
    return []
  }
}

const saveDismissed = (ids) => {
  try {
    localStorage.setItem(DISMISSED_KEY, JSON.stringify(ids))
  } catch (e) {
    // ignore
  }
}

export const useUploadQueueStore = defineStore('uploadQueue', {
  state: () => ({
    items: [],
    pollingId: null,
    dismissedIds: loadDismissed(),
    lastStatusById: {}
  }),
  getters: {
    hasItems: (state) => state.items.length > 0
  },
  actions: {
    addLocalUpload({ fileName, module, entityId }) {
      this.startPolling()
      const localId = `local-${Date.now()}-${Math.random().toString(16).slice(2)}`
      this.items.unshift({
        id: localId,
        localId,
        file_name: fileName,
        status: 'uploading',
        progress: 0,
        module,
        entity_id: entityId
      })
      return localId
    },
    updateProgress(localId, progress) {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (item) {
        item.progress = Math.min(100, Math.max(0, Math.round(progress)))
      }
    },
    markQueued(localId, job) {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (item) {
        item.id = job.id
        item.status = job.status || 'queued'
        item.file_name = job.file_name || item.file_name
        item.progress = 100
        item.error_message = job.error_message || null
        item.created_at = job.created_at
        item.updated_at = job.updated_at
      } else {
        this.items.unshift({
          id: job.id,
          file_name: job.file_name,
          status: job.status || 'queued',
          progress: 100,
          error_message: job.error_message || null,
          created_at: job.created_at,
          updated_at: job.updated_at,
          module: job.module,
          entity_id: job.entity_id
        })
      }
      this.fetchRemote()
      this._scheduleRefresh()
      this._trim()
    },
    markError(localId, message) {
      const item = this.items.find((entry) => entry.localId === localId || entry.id === localId)
      if (item) {
        item.status = 'error'
        item.error_message = message || '\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438'
      }
      this._scheduleRefresh()
    },
    async fetchRemote() {
      try {
        const response = await axios.get('/api/v1/uploads/', {
          params: { limit: 50, _t: Date.now() },
          headers: { 'Cache-Control': 'no-store', Pragma: 'no-cache' }
        })
        this.mergeRemote(response.data || [])
      } catch (error) {
        // ignore polling errors
      }
    },
    mergeRemote(remoteJobs) {
      this.emitStatusEvents(remoteJobs)
      const now = Date.now()
      const dismissed = new Set(this.dismissedIds)
      remoteJobs.forEach((job) => {
        if (!job?.id) return
        if (job.status === 'done') {
          this._scheduleAutoDismiss(job.id)
        } else {
          this._clearAutoDismiss(job.id)
        }
        if (job.status !== 'done' && job.status !== 'error') return
        if (!job.updated_at) return
        const updatedAt = Date.parse(job.updated_at)
        if (!Number.isNaN(updatedAt) && now - updatedAt > HISTORY_TTL_MS) {
          dismissed.add(job.id)
        }
      })
      if (dismissed.size !== this.dismissedIds.length) {
        this.dismissedIds = Array.from(dismissed).slice(-200)
        saveDismissed(this.dismissedIds)
      }
      const filteredJobs = remoteJobs.filter((job) => job && !dismissed.has(job.id))
      const localUploads = this.items.filter((item) => item.localId && item.status === 'uploading')
      const remoteItems = filteredJobs.map((job) => ({
        id: job.id,
        file_name: job.file_name,
        status: job.status || 'queued',
        progress: job.status === 'done' ? 100 : job.status === 'processing' ? 60 : 0,
        error_message: job.error_message || null,
        created_at: job.created_at,
        updated_at: job.updated_at,
        module: job.module,
        entity_id: job.entity_id
      }))
      this.items = [...localUploads, ...remoteItems]
      this._trim()
    },

    emitStatusEvents(remoteJobs) {
      if (typeof window === 'undefined') return
      const previous = this.lastStatusById || {}
      const next = {}
      remoteJobs.forEach((job) => {
        if (!job || !job.id) return
        next[job.id] = job.status
        if (job.status === 'done' && previous[job.id] !== 'done') {
          window.dispatchEvent(new CustomEvent('upload-job-done', { detail: job }))
        }
        if (job.status === 'error' && previous[job.id] !== 'error') {
          window.dispatchEvent(new CustomEvent('upload-job-error', { detail: job }))
        }
      })
      this.lastStatusById = next
    },
    startPolling() {
      if (this.pollingId) return
      this.fetchRemote()
      this.pollingId = setInterval(() => {
        this.fetchRemote()
      }, 3000)
    },
    stopPolling() {
      if (this.pollingId) {
        clearInterval(this.pollingId)
        this.pollingId = null
      }
    },
    clearFinished() {
      const toDismiss = this.items
        .filter((item) => item.status === 'done' || item.status === 'error')
        .map((item) => item.id)
        .filter((id) => id && !id.startsWith('local-'))
      toDismiss.forEach((id) => this._clearAutoDismiss(id))
      if (toDismiss.length) {
        const merged = new Set(this.dismissedIds)
        toDismiss.forEach((id) => merged.add(id))
        this.dismissedIds = Array.from(merged).slice(-200)
        saveDismissed(this.dismissedIds)
      }
      this.items = this.items.filter((item) => item.status !== 'done' && item.status !== 'error')
    },
    removeItem(id, options = {}) {
      if (!id) return
      const { dismiss = false } = options
      this._clearAutoDismiss(id)
      this.items = this.items.filter((item) => item.id !== id && item.localId !== id)
      if (dismiss && !String(id).startsWith('local-')) {
        const merged = new Set(this.dismissedIds)
        merged.add(id)
        this.dismissedIds = Array.from(merged).slice(-200)
        saveDismissed(this.dismissedIds)
      }
    },
    statusLabel(status) {
      return statusLabelMap[status] || status
    },
    _scheduleRefresh() {
      setTimeout(() => this.fetchRemote(), 1500)
      setTimeout(() => this.fetchRemote(), 4000)
    },
    _scheduleAutoDismiss(id) {
      if (!id || String(id).startsWith('local-') || autoDismissTimers.has(id)) return
      const timerId = setTimeout(() => {
        autoDismissTimers.delete(id)
        this.removeItem(id, { dismiss: true })
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
