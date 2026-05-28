import { rawRequest } from '../services/api/_client'
import { useDownloadQueueStore } from '../stores/downloadQueue'

const extractFilename = (disposition, fallback = 'file') => {
  if (!disposition) return fallback
  const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i)
  if (match?.[1]) {
    try {
      return decodeURIComponent(match[1])
    } catch (e) {
      return match[1]
    }
  }
  if (match?.[2]) return match[2]
  return fallback
}

const triggerBlobDownload = (blob, fileName) => {
  const blobUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => window.URL.revokeObjectURL(blobUrl), 100)
}

const isSameOriginHref = (href) => {
  try {
    const resolved = new URL(href, window.location.origin)
    return resolved.origin === window.location.origin
  } catch (error) {
    return false
  }
}

export const openTrustedExternalUrl = (href, allowedHosts = []) => {
  if (!href || typeof window === 'undefined') return false
  try {
    const resolved = new URL(href, window.location.origin)
    const isHttp = resolved.protocol === 'http:' || resolved.protocol === 'https:'
    if (!isHttp) return false
    const isSameOrigin = resolved.origin === window.location.origin
    const isAllowedHost = allowedHosts.includes(resolved.hostname)
    if (!isSameOrigin && !isAllowedHost) return false
    const win = window.open(resolved.toString(), '_blank', 'noopener,noreferrer')
    if (win) win.opener = null
    return true
  } catch (error) {
    return false
  }
}

const extractErrorMessage = async (error, fallback = 'Не удалось скачать файл') => {
  const detail = error?.response?.data
  if (detail instanceof Blob && typeof detail.text === 'function') {
    try {
      const text = await detail.text()
      if (!text) return fallback
      try {
        const parsed = JSON.parse(text)
        return parsed?.detail || text || fallback
      } catch (parseError) {
        return text || fallback
      }
    } catch (blobError) {
      return fallback
    }
  }
  return error?.response?.data?.detail || error?.message || fallback
}

export const downloadFromApi = async (url, config = {}, fallbackName = 'file', meta = {}) => {
  if (!url) return
  const queue = useDownloadQueueStore()
  const localId = queue.addLocalDownload({
    fileName: fallbackName,
    module: meta.module,
    entityId: meta.entityId
  })
  try {
    const response = await rawRequest({
      method: 'get',
      url,
      responseType: 'blob',
      ...config,
      onDownloadProgress: (event) => {
        if (typeof config.onDownloadProgress === 'function') {
          config.onDownloadProgress(event)
        }
        if (!event?.total) {
          queue.updateProgress(localId, null, { status: 'downloading', indeterminate: true })
          return
        }
        const progress = (event.loaded / event.total) * 100
        queue.updateProgress(localId, progress, { status: 'downloading', indeterminate: false })
      }
    })
    const disposition = response.headers?.['content-disposition'] || ''
    const filename = extractFilename(disposition, fallbackName)
    queue.rename(localId, filename)
    triggerBlobDownload(response.data, filename)
    queue.markDone(localId, filename)
    return response
  } catch (error) {
    const message = await extractErrorMessage(error)
    queue.markError(localId, message)
    throw error
  }
}

export const downloadFromHref = async (href, fallbackName = 'file', meta = {}) => {
  if (!href) return
  if (!isSameOriginHref(href)) {
    if (openTrustedExternalUrl(href)) return
    throw new Error('Недопустимая ссылка для скачивания')
  }
  await downloadFromApi(href, {}, fallbackName, meta)
}

export const downloadFromPath = async (path, fallbackName = 'file', meta = {}) => {
  if (!path) return
  const href = `/api/v1/storage/download?path=${encodeURIComponent(path)}`
  await downloadFromHref(href, fallbackName, meta)
}

export { extractFilename }
