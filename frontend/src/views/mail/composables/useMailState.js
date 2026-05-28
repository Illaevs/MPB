import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import DOMPurify from 'dompurify'
import { api } from '../../../services/api'
import { useToast } from '../../../composables/useToast'
import { normalizeEmailBody, looksGibberish, formatPlainTextToHtml, fixMojibake } from '../../../utils/mailHelpers'
import { downloadFromApi } from '../../../utils/download'
import { formatDate as fmtDate, formatTime as fmtTime, formatDateTime as fmtDateTime } from '../../../utils/format'
import { parseServerDate } from '../../../composables/useServerClock'

/**
 * Mail view shared state + actions.
 *
 * Phase 5 decomposition: extracted from views/Mail.vue.
 * - axios.* calls migrated to api.mail.* (services/api/mail.js).
 * - File-download endpoints continue to use utils/download.downloadFromApi
 *   because it handles content-disposition / progress queue uniformly.
 */
export function useMailState() {
  const { add: addToast } = useToast()

  const mailViewRef = ref(null)
  const messageRefs = ref([])

  // ── State ─────────────────────────────────────────────────────────────────
  let messagesRequestSeq = 0
  const mailboxes = ref([])
  const selectedMailboxId = ref(null)
  const selectedFolder = ref('inbox')
  const folderStats = ref([])
  const messages = ref([])
  const messageTotal = ref(0)
  const messageLimit = ref(50)
  const messageOffset = ref(0)
  const hasMoreMessages = ref(false)
  const loadingMailboxes = ref(false)
  const loadingMessages = ref(false)
  const loadingMoreMessages = ref(false)
  const loadingMessageBody = ref(false)
  const movingMessage = ref(false)
  const creating = ref(false)
  const sending = ref(false)
  const deleting = ref(false)
  const showCreate = ref(false)
  const mailboxDropdownOpen = ref(false)
  const actionsOpen = ref(false)
  const appPasswordOpen = ref(false)
  const appPasswordValue = ref('')
  const connectingAppPassword = ref(false)
  const deleteConfirmOpen = ref(false)
  const searchInput = ref('')
  const searchQuery = ref('')
  const searchFocused = ref(false)
  const selectedMessageId = ref(null)
  const mobileView = ref('list')

  // Compose
  const composeMode = ref('new') // 'new' | 'reply' | 'forward'
  const inlineComposeOpen = ref(false)
  const newComposeOpen = ref(false)
  const composeForm = ref({ to: '', subject: '', body: '' })

  // Keyboard
  const focusedMessageIndex = ref(-1)
  const createForm = ref({ name: '', email: '' })

  // ── Computed ──────────────────────────────────────────────────────────────
  const mailFolders = computed(() => {
    const defaults = [
      { id: 'inbox', label: 'Входящие', icon: 'fa-inbox' },
      { id: 'important', label: 'Важные', icon: 'fa-star' },
      { id: 'sent', label: 'Отправленные', icon: 'fa-paper-plane' },
      { id: 'drafts', label: 'Черновики', icon: 'fa-file-alt' },
      { id: 'archive', label: 'Архив', icon: 'fa-archive' },
      { id: 'spam', label: 'Спам', icon: 'fa-exclamation-circle' },
      { id: 'trash', label: 'Корзина', icon: 'fa-trash-alt' }
    ]
    const stats = new Map(folderStats.value.map(item => [item.id, item]))
    return defaults.map(folder => {
      const stat = stats.get(folder.id) || {}
      return {
        ...folder,
        count: Number(stat.count || 0),
        unread_count: Number(stat.unread_count || 0)
      }
    })
  })

  const selectedMailbox = computed(() => mailboxes.value.find(b => b.id === selectedMailboxId.value) || null)

  const connectLabel = computed(() => {
    if (!selectedMailbox.value) return 'Подключить'
    const s = selectedMailbox.value.status
    if (s === 'connected') return 'Переавторизовать'
    if (s === 'error') return 'Переподключить'
    return 'Подключить'
  })

  const filteredMessages = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return messages.value
    return messages.value.filter(m =>
      (m.subject || '').toLowerCase().includes(q) ||
      (m.from_addr || '').toLowerCase().includes(q) ||
      (m.cc_addr || '').toLowerCase().includes(q) ||
      (m.snippet || '').toLowerCase().includes(q)
    )
  })

  const selectedMessage = computed(() => messages.value.find(m => m.id === selectedMessageId.value) || null)
  const selectedMessageIndex = computed(() => filteredMessages.value.findIndex(m => m.id === selectedMessageId.value))
  const unreadCount = computed(() => messages.value.filter(m => !m.is_read).length)

  // ── HTML sanitization helpers ─────────────────────────────────────────────
  const stripHtmlToText = (html) => {
    if (!html) return ''
    const sanitized = DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['p','br','b','i','u','strong','em','a','ul','ol','li','blockquote','span','div','table','tr','td','th','thead','tbody','tfoot','h1','h2','h3','h4','h5','h6','colgroup','col'],
      ALLOWED_ATTR: ['href','alt','class','width','height','cellpadding','cellspacing','align','valign','bgcolor','colspan','rowspan'],
      FORBID_TAGS: ['style', 'img'],
      FORBID_ATTR: ['style', 'src', 'srcset']
    })
    const parsed = new DOMParser().parseFromString(sanitized, 'text/html')
    return (parsed.body.textContent || '').replace(/\s+/g, ' ').trim()
  }

  const sanitizeInlineStyle = (value) => {
    if (!value) return ''
    return String(value)
      .replace(/url\s*\([^)]*\)/gi, '')
      .replace(/expression\s*\([^)]*\)/gi, '')
      .replace(/position\s*:\s*(fixed|sticky)\s*;?/gi, '')
      .replace(/behavior\s*:\s*[^;]+;?/gi, '')
      .replace(/-moz-binding\s*:\s*[^;]+;?/gi, '')
      .replace(/(?:left|right|top|bottom)\s*:\s*-\d+[^;]*;?/gi, '')
  }

  const sanitizeEmailHtml = (html) => {
    const clean = DOMPurify.sanitize(html || '', {
      ALLOWED_TAGS: ['p','br','b','i','u','strong','em','a','ul','ol','li','blockquote','span','div','table','tr','td','th','thead','tbody','tfoot','h1','h2','h3','h4','h5','h6','colgroup','col','center','font','img'],
      ALLOWED_ATTR: ['href','title','alt','class','width','height','cellpadding','cellspacing','align','valign','bgcolor','colspan','rowspan','style','border','role','aria-label','src'],
      FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'textarea', 'select', 'link', 'meta'],
      FORBID_ATTR: ['srcset', 'onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'autofocus']
    })
    const doc = new DOMParser().parseFromString(`<div>${clean}</div>`, 'text/html')
    doc.querySelectorAll('[style]').forEach(el => {
      const safeStyle = sanitizeInlineStyle(el.getAttribute('style'))
      if (safeStyle) el.setAttribute('style', safeStyle)
      else el.removeAttribute('style')
    })
    doc.querySelectorAll('a[href]').forEach(el => {
      const href = (el.getAttribute('href') || '').trim()
      if (/^(javascript|data|vbscript):/i.test(href)) {
        el.removeAttribute('href')
        return
      }
      el.setAttribute('target', '_blank')
      el.setAttribute('rel', 'noopener noreferrer nofollow')
    })
    doc.querySelectorAll('img[src]').forEach(el => {
      const src = (el.getAttribute('src') || '').trim()
      if (!/^(data:image\/|cid:)/i.test(src)) {
        el.removeAttribute('src')
        el.setAttribute('alt', el.getAttribute('alt') || 'Изображение заблокировано')
      }
    })
    return doc.body.firstElementChild?.innerHTML || ''
  }

  const cleanSnippetText = (value) => {
    if (!value) return ''
    let raw = String(value).replace(/\u0000/g, '').trim()
    if (!raw) return ''

    const hasHtmlMarkers = /<!doctype|<\/?(html|body|head|div|p|table|br|span|meta|style)\b/i.test(raw)
    const norm = normalizeEmailBody(raw, hasHtmlMarkers ? 'text/html' : 'text/plain')
    let text = ''
    if (norm.body_html) text = stripHtmlToText(norm.body_html)
    else if (norm.body_text) text = norm.body_text
    else text = raw

    text = text
      .replace(/<!doctype[^>]*>/gi, '')
      .replace(/content-transfer-encoding:\s*base64.*$/gim, '')
      .replace(/content-type:\s*[^;]+.*$/gim, '')
      .replace(/charset\s*=\s*["']?[^"'\s;]+/gim, '')
      .replace(/--=+[^\n\r]*/g, '')
      .replace(/\s+/g, ' ')
      .trim()

    if (!text) return ''
    if (looksGibberish(raw) || looksGibberish(text)) return ''

    const compact = text.replace(/\s+/g, '')
    if (compact.length > 48 && /^[A-Za-z0-9+/=]+$/.test(compact)) return ''
    return text
  }

  const displayBody = computed(() => {
    const msg = selectedMessage.value
    if (!msg) return { body_html: '', body_text: '' }

    if (msg.body_html && msg.body_html.trim()) {
      const norm = normalizeEmailBody(msg.body_html, 'text/html')
      if (norm.body_html || norm.body_text) return norm
    }

    let raw = (msg.body_text || msg.body || '').trim()
    if (raw && !/<[^>]+>/.test(raw)) {
      raw = fixMojibake(raw)
    }
    if (raw) {
      const looksLikeHtml = /<\/?(html|body|head|div|p|table|br|span|meta|style|a|td|tr)\b/i.test(raw) || /<!doctype/i.test(raw)
      if (looksLikeHtml) {
        const norm = normalizeEmailBody(raw, 'text/html')
        if (norm.body_html) return norm
      }
      const norm = normalizeEmailBody(raw, msg.content_type || 'text/plain')
      if (norm.body_html || norm.body_text) return norm
      if (!looksGibberish(raw)) return { body_html: '', body_text: raw }
    }

    const snippet = (msg.snippet || '').trim()
    if (snippet) {
      const cleaned = cleanSnippetText(snippet)
      if (cleaned) return { body_html: '', body_text: cleaned }
      if (!looksGibberish(snippet)) return { body_html: '', body_text: snippet }
    }

    return { body_html: '', body_text: '' }
  })

  const formattedPlainText = computed(() => {
    const text = displayBody.value.body_text
    if (!text) return ''
    const hasQuotes = /^>+\s?/m.test(text)
    const hasSeparators = /^[-_=]{3,}\s*$/m.test(text)
    if (!hasQuotes && !hasSeparators) return ''
    const html = formatPlainTextToHtml(text)
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['br', 'blockquote', 'hr'],
      ALLOWED_ATTR: ['class']
    })
  })

  const sanitizedBody = computed(() => {
    if (!displayBody.value.body_html) return ''
    return sanitizeEmailHtml(displayBody.value.body_html)
  })

  // ── Watchers ──────────────────────────────────────────────────────────────
  let searchTimeout = null
  watch(searchInput, (val) => {
    clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => { searchQuery.value = val }, 300)
  })

  watch(selectedMessageId, async (id) => {
    if (!id) return
    const msg = messages.value.find(m => m.id === id)
    if (msg && !msg.body_loaded) await loadMessageBody(id)
    if (msg && !msg.is_read) msg.is_read = true
    inlineComposeOpen.value = false
  })

  // ── Keyboard ──────────────────────────────────────────────────────────────
  const scrollToMessage = (index) => {
    nextTick(() => { messageRefs.value[index]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) })
  }

  const handleKeydown = (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
    const count = filteredMessages.value.length
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        if (focusedMessageIndex.value < count - 1) {
          focusedMessageIndex.value++
          selectMessage(filteredMessages.value[focusedMessageIndex.value].id)
          scrollToMessage(focusedMessageIndex.value)
        }
        break
      case 'ArrowUp':
        e.preventDefault()
        if (focusedMessageIndex.value > 0) {
          focusedMessageIndex.value--
          selectMessage(filteredMessages.value[focusedMessageIndex.value].id)
          scrollToMessage(focusedMessageIndex.value)
        }
        break
      case 'Enter':
        if (selectedMessage.value) mobileView.value = 'preview'
        break
      case 'Escape':
        if (inlineComposeOpen.value) { closeInlineCompose(); break }
        if (newComposeOpen.value) { newComposeOpen.value = false; break }
        if (appPasswordOpen.value) { closeAppPassword(); break }
        if (deleteConfirmOpen.value) { deleteConfirmOpen.value = false; break }
        break
      case 'n':
        if ((e.ctrlKey || e.metaKey) && selectedMailbox.value) { e.preventDefault(); openNewCompose() }
        break
      case 'r':
        if ((e.ctrlKey || e.metaKey) && selectedMessage.value) { e.preventDefault(); replyToMessage() }
        break
    }
  }

  // ── Attachment helpers ────────────────────────────────────────────────────
  const safeExternalAttachmentUrl = (value) => {
    if (!value || typeof value !== 'string') return ''
    try {
      const url = new URL(value)
      if (url.protocol !== 'https:') return ''
      const host = url.hostname.toLowerCase()
      const allowed = [
        'disk.yandex.ru',
        'yadi.sk',
        'downloader.disk.yandex.ru',
        'cloud.mail.ru',
        'drive.google.com',
        'docs.google.com',
        'dropbox.com',
        'onedrive.live.com',
        'sharepoint.com'
      ]
      return allowed.some(domain => host === domain || host.endsWith(`.${domain}`)) ? url.toString() : ''
    } catch {
      return ''
    }
  }

  const normalizeMailAttachments = (items = [], messageId = '') => {
    const list = Array.isArray(items) ? items : []
    return list.map((item, index) => {
      const id = String(item.id || index + 1)
      const rawName = String(item.name || `Вложение ${index + 1}`)
      const name = rawName.replace(/[<>:"/\\|?*\u0000-\u001F]/g, '_').trim() || `Вложение ${index + 1}`
      const fallbackUrl = messageId ? `/api/v1/mail/messages/${messageId}/attachments/${encodeURIComponent(id)}` : ''
      const downloadUrl = item.download_url || item.url || fallbackUrl
      const safeUrl = typeof downloadUrl === 'string' && downloadUrl.startsWith('/api/v1/mail/') ? downloadUrl : ''
      const externalUrl = safeExternalAttachmentUrl(item.external_url || '')
      return {
        ...item,
        id,
        name,
        size: Number.isFinite(Number(item.size)) ? Number(item.size) : null,
        download_url: safeUrl,
        external_url: externalUrl,
        external: Boolean(externalUrl),
        blocked: Boolean(item.blocked || (!safeUrl && !externalUrl)),
        blocked_reason: item.blocked_reason || (!safeUrl && !externalUrl ? 'Недопустимая ссылка вложения' : '')
      }
    })
  }

  // ── API methods (api.mail.*) ──────────────────────────────────────────────
  const loadMailboxes = async () => {
    loadingMailboxes.value = true
    try {
      const data = await api.mail.list()
      mailboxes.value = data || []
      if (!selectedMailboxId.value && mailboxes.value.length) {
        selectedMailboxId.value = mailboxes.value[0].id
        await loadFolderStats()
        await loadMessages()
        refreshCurrentFolderSilently()
      }
    } catch (e) {
      console.error('Mailboxes load error:', e)
      mailboxes.value = []
    } finally {
      loadingMailboxes.value = false
    }
  }

  const selectMailbox = async (id) => {
    selectedMailboxId.value = id
    selectedFolder.value = 'inbox'
    selectedMessageId.value = null
    focusedMessageIndex.value = -1
    inlineComposeOpen.value = false
    await loadFolderStats()
    await loadMessages()
    refreshCurrentFolderSilently()
  }

  const selectFolder = async (folder) => {
    if (!selectedMailbox.value || selectedFolder.value === folder) return
    selectedFolder.value = folder
    selectedMessageId.value = null
    focusedMessageIndex.value = -1
    inlineComposeOpen.value = false
    messages.value = []
    messageTotal.value = 0
    messageOffset.value = 0
    hasMoreMessages.value = false
    await loadMessages()
    refreshCurrentFolderSilently()
  }

  const selectMessage = (id) => {
    selectedMessageId.value = id
    const idx = filteredMessages.value.findIndex(m => m.id === id)
    if (idx !== -1) focusedMessageIndex.value = idx
  }

  const loadMessageBody = async (id) => {
    loadingMessageBody.value = true
    try {
      const p = (await api.mail.getMessage(id)) || {}
      const attachments = normalizeMailAttachments(p.attachments || [], id)
      const isBackendHtml = String(p.content_type || '').toLowerCase().includes('html')
      const backendHtml = (p.body_html || (isBackendHtml ? p.body : '') || '').replace(/\u0000/g, '').trim()
      let raw = p.body_html || p.body_text || p.body || ''
      if (raw && !isBackendHtml && !/<[^>]+>/.test(raw)) {
        raw = fixMojibake(raw)
      }
      const ct = p.content_type || (p.body_html ? 'text/html' : 'text/plain')
      const norm = backendHtml ? normalizeEmailBody(backendHtml, 'text/html') : normalizeEmailBody(raw, ct)
      const idx = messages.value.findIndex(m => m.id === id)
      if (idx !== -1) {
        const current = messages.value[idx]
        const attachmentPatch = {
          attachments,
          attachments_count: attachments.length || current.attachments_count || 0,
          has_attachments: Boolean(attachments.length || current.has_attachments),
          cc_addr: p.cc_addr ?? current.cc_addr
        }
        if (norm.body_html || norm.body_text) {
          messages.value[idx] = { ...current, ...attachmentPatch, body_html: norm.body_html, body_text: norm.body_text, body_loaded: true }
        } else {
          const cleanedText = looksGibberish(current.body_text || '') ? '' : current.body_text
          messages.value[idx] = { ...current, ...attachmentPatch, body_text: cleanedText, body_loaded: true }
        }
      }
    } catch (e) {
      console.error('Load message body error:', e)
      const idx = messages.value.findIndex(m => m.id === id)
      if (idx !== -1) messages.value[idx] = { ...messages.value[idx], body_loaded: true }
    } finally {
      loadingMessageBody.value = false
    }
  }

  const loadFolderStats = async () => {
    if (!selectedMailbox.value) { folderStats.value = []; return }
    try {
      const data = await api.mail.listFolders(selectedMailbox.value.id)
      folderStats.value = data || []
    } catch (e) {
      console.error('Mail folders error:', e)
      folderStats.value = []
    }
  }

  const mapMessage = (item) => ({
    ...item,
    is_read: item.is_read !== false,
    attachments_count: item.attachments_count || (item.has_attachments ? 1 : 0),
    snippet: cleanSnippetText(item.snippet || '')
  })

  const loadMessages = async (force = false, append = false, options = {}) => {
    if (!selectedMailbox.value) { messages.value = []; return }
    const mailboxId = options.mailboxId || selectedMailbox.value.id
    const folder = options.folder || selectedFolder.value
    const silent = Boolean(options.silent)
    const requestId = ++messagesRequestSeq
    if (!silent) {
      if (append) loadingMoreMessages.value = true
      else loadingMessages.value = true
    }
    try {
      const offset = append ? messages.value.length : 0
      const data = await api.mail.listMessages(mailboxId, {
        limit: messageLimit.value,
        offset,
        folder,
        refresh: force ? 1 : 0
      })
      if (
        requestId !== messagesRequestSeq ||
        !selectedMailbox.value ||
        selectedMailbox.value.id !== mailboxId ||
        selectedFolder.value !== folder
      ) return
      const items = (data?.items || []).map(mapMessage)
      const selectedBeforeApply = selectedMessageId.value
      if (!append && silent && selectedBeforeApply && !items.some(item => item.id === selectedBeforeApply)) {
        await loadFolderStats()
        return
      }
      messages.value = append ? [...messages.value, ...items] : items
      messageTotal.value = Number(data?.total || messages.value.length)
      messageOffset.value = Number(data?.offset || offset)
      hasMoreMessages.value = Boolean(data?.has_more)
      if (!append && messages.value.length) {
        const preservedIndex = selectedBeforeApply
          ? messages.value.findIndex(message => message.id === selectedBeforeApply)
          : -1
        if (preservedIndex !== -1) {
          selectedMessageId.value = selectedBeforeApply
          focusedMessageIndex.value = preservedIndex
        } else if (!silent) {
          selectedMessageId.value = messages.value[0].id
          focusedMessageIndex.value = 0
        }
      } else if (!append) {
        if (!silent) {
          selectedMessageId.value = null
          focusedMessageIndex.value = -1
        }
      }
      if (!append) await loadFolderStats()
    } catch (e) {
      if (
        requestId !== messagesRequestSeq ||
        !selectedMailbox.value ||
        selectedMailbox.value.id !== mailboxId ||
        selectedFolder.value !== folder
      ) return
      console.error('Mail messages error:', e)
      if (!append && !silent) messages.value = []
    } finally {
      if (requestId === messagesRequestSeq) {
        if (!silent) {
          loadingMessages.value = false
          loadingMoreMessages.value = false
        }
      }
    }
  }

  const loadMoreMessages = () => loadMessages(false, true)

  const refreshCurrentFolderSilently = () => {
    if (!selectedMailbox.value || selectedFolder.value === 'important') return
    const mailboxId = selectedMailbox.value.id
    const folder = selectedFolder.value
    setTimeout(() => {
      if (!selectedMailbox.value || selectedMailbox.value.id !== mailboxId || selectedFolder.value !== folder) return
      loadMessages(true, false, { silent: true, mailboxId, folder })
    }, 100)
  }

  const createMailbox = async () => {
    if (!createForm.value.name.trim() || !createForm.value.email.trim()) {
      addToast('warning', 'Заполните название и email'); return
    }
    creating.value = true
    try {
      const created = await api.mail.create({ name: createForm.value.name, email: createForm.value.email })
      mailboxes.value = [...mailboxes.value, created]
      selectedMailboxId.value = created.id
      resetCreate()
      addToast('success', 'Ящик создан')
    } catch (e) {
      console.error('Create mailbox error:', e)
      addToast('error', 'Не удалось создать ящик')
    } finally { creating.value = false }
  }

  const resetCreate = () => { createForm.value = { name: '', email: '' }; showCreate.value = false }

  const connectMailbox = async () => {
    if (!selectedMailbox.value) return
    try {
      const data = await api.mail.connect(selectedMailbox.value.id)
      if (data?.auth_url) {
        const parsed = new URL(data.auth_url, window.location.origin)
        const allowedHosts = new Set([
          window.location.host,
          'oauth.yandex.ru',
          'passport.yandex.ru',
          'id.yandex.ru'
        ])
        if (!['https:', 'http:'].includes(parsed.protocol) || !allowedHosts.has(parsed.host)) {
          throw new Error('Untrusted auth redirect')
        }
        window.location.href = parsed.toString()
      }
    } catch (e) { console.error('Connect error:', e); addToast('error', 'Не удалось открыть OAuth') }
  }

  const connectMailboxAppPassword = async () => {
    if (!selectedMailbox.value) return
    const pw = appPasswordValue.value.trim()
    if (!pw) { addToast('warning', 'Введите пароль приложения'); return }
    connectingAppPassword.value = true
    try {
      await api.mail.connectAppPassword(selectedMailbox.value.id, { app_password: pw })
      addToast('success', 'Ящик подключен')
      appPasswordValue.value = ''; appPasswordOpen.value = false
      await loadMailboxes(); await loadMessages()
    } catch (e) { console.error('App password error:', e); addToast('error', 'Не удалось подключить') }
    finally { connectingAppPassword.value = false }
  }

  const closeAppPassword = () => { appPasswordOpen.value = false; appPasswordValue.value = '' }

  const exportMailbox = async () => {
    if (!selectedMailbox.value) return
    try {
      await downloadFromApi(
        `/api/v1/mail/mailboxes/${selectedMailbox.value.id}/export`,
        { params: { days: 30 } },
        `mail_${selectedMailbox.value.email}_30d.csv`,
        { module: 'mail', entityId: selectedMailbox.value.id }
      )
      addToast('success', 'Экспорт готов')
    } catch (e) { console.error('Export error:', e); addToast('error', 'Не удалось выгрузить') }
  }

  const formatFileSize = (value) => {
    const size = Number(value || 0)
    if (!size) return ''
    if (size < 1024) return `${size} Б`
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} КБ`
    return `${(size / (1024 * 1024)).toFixed(1)} МБ`
  }

  const downloadMailAttachment = async (attachment) => {
    if (!attachment || attachment.blocked) {
      addToast('warning', attachment?.blocked_reason || 'Вложение заблокировано')
      return
    }
    if (attachment.external_url) {
      window.open(attachment.external_url, '_blank', 'noopener,noreferrer')
      return
    }
    if (!attachment.download_url) {
      addToast('error', 'Нет безопасной ссылки для скачивания')
      return
    }
    try {
      await downloadFromApi(
        attachment.download_url,
        {},
        attachment.name || 'attachment',
        { module: 'mail', entityId: selectedMessageId.value }
      )
    } catch (e) {
      console.error('Mail attachment download error:', e)
      addToast('error', 'Не удалось скачать вложение')
    }
  }

  const confirmDelete = () => { actionsOpen.value = false; deleteConfirmOpen.value = true }

  const deleteMailbox = async () => {
    if (!selectedMailbox.value) return
    deleting.value = true
    try {
      await api.mail.remove(selectedMailbox.value.id)
      mailboxes.value = mailboxes.value.filter(b => b.id !== selectedMailbox.value.id)
      selectedMailboxId.value = mailboxes.value[0]?.id || null
      selectedMessageId.value = null; messages.value = []; deleteConfirmOpen.value = false
      addToast('success', 'Ящик удалён')
    } catch (e) { console.error('Delete error:', e); addToast('error', 'Не удалось удалить') }
    finally { deleting.value = false }
  }

  // ── Compose ───────────────────────────────────────────────────────────────
  const openNewCompose = () => {
    composeMode.value = 'new'
    composeForm.value = { to: '', subject: '', body: '' }
    inlineComposeOpen.value = false
    newComposeOpen.value = true
  }

  const replyToMessage = () => {
    if (!selectedMessage.value) return
    composeMode.value = 'reply'
    composeForm.value = {
      to: selectedMessage.value.from_addr || '',
      subject: `Re: ${selectedMessage.value.subject || ''}`,
      body: `\n\n---\n${selectedMessage.value.snippet || ''}`
    }
    newComposeOpen.value = false
    inlineComposeOpen.value = true
  }

  const forwardMessage = () => {
    if (!selectedMessage.value) return
    composeMode.value = 'forward'
    composeForm.value = {
      to: '',
      subject: `Fwd: ${selectedMessage.value.subject || ''}`,
      body: `\n\n--- Пересылаемое сообщение ---\nОт: ${selectedMessage.value.from_addr}\nКому: ${selectedMessage.value.to_addr || ''}\nКопия: ${selectedMessage.value.cc_addr || ''}\nДата: ${formatDateFull(selectedMessage.value.date)}\n\n${selectedMessage.value.snippet || ''}`
    }
    newComposeOpen.value = false
    inlineComposeOpen.value = true
  }

  const closeInlineCompose = () => { inlineComposeOpen.value = false; resetCompose() }
  const resetCompose = () => { composeForm.value = { to: '', subject: '', body: '' }; composeMode.value = 'new' }

  const sendMail = async () => {
    if (!selectedMailbox.value) return
    const toList = composeForm.value.to.split(',').map(v => v.trim()).filter(Boolean)
    if (!toList.length || !composeForm.value.subject.trim()) { addToast('warning', 'Укажите получателя и тему'); return }
    sending.value = true
    try {
      await api.mail.sendMessage(selectedMailbox.value.id, {
        to: toList, subject: composeForm.value.subject, body: composeForm.value.body
      })
      addToast('success', 'Письмо отправлено')
      resetCompose(); inlineComposeOpen.value = false; newComposeOpen.value = false
      await loadMessages()
    } catch (e) {
      console.error('Send error:', e)
      addToast('error', e?.response?.data?.detail || 'Не удалось отправить')
    }
    finally { sending.value = false }
  }

  const moveSelectedMessage = async (target) => {
    if (!selectedMessage.value || movingMessage.value) return
    const currentId = selectedMessage.value.id
    movingMessage.value = true
    try {
      await api.mail.moveMessage(currentId, { target })
      const currentIndex = messages.value.findIndex(m => m.id === currentId)
      messages.value = messages.value.filter(m => m.id !== currentId)
      messageTotal.value = Math.max(0, messageTotal.value - 1)
      const next = messages.value[Math.min(currentIndex, messages.value.length - 1)]
      selectedMessageId.value = next?.id || null
      focusedMessageIndex.value = next ? messages.value.findIndex(m => m.id === next.id) : -1
      await loadFolderStats()
      const labels = { archive: 'Письмо перемещено в архив', spam: 'Письмо перемещено в спам', trash: 'Письмо перемещено в корзину' }
      addToast('success', labels[target] || 'Письмо перемещено')
    } catch (e) {
      console.error('Move message error:', e)
      addToast('error', e?.response?.data?.detail || 'Не удалось переместить письмо')
    } finally {
      movingMessage.value = false
    }
  }

  // ── Display helpers ───────────────────────────────────────────────────────
  const statusLabel = (v) => ({ new: 'Новый', connected: 'Подключен', error: 'Ошибка' })[v] || 'Неизвестно'
  const statusDotClass = (v) => ({ connected: 'dot-success', error: 'dot-danger', new: 'dot-warning' })[v] || 'dot-muted'

  const parseAddress = (value) => {
    const raw = String(value || '').trim()
    if (!raw) return { name: '', email: '' }
    const match = raw.match(/^(.*?)\s*<([^>]+)>$/)
    if (match) {
      const name = match[1].replace(/^"|"$/g, '').trim()
      const email = match[2].trim()
      return { name: name || email, email }
    }
    return { name: raw, email: raw.includes('@') ? raw : '' }
  }

  const getSenderName = (message) => {
    if (!message) return '-'
    return parseAddress(message.from_addr).name || message.from_addr || '-'
  }

  const getSenderEmail = (message) => {
    if (!message) return ''
    return parseAddress(message.from_addr).email || message.from_addr || ''
  }

  const formatDate = (v) => {
    if (!v) return '-'
    const d = parseServerDate(v) || new Date(v), now = new Date()
    if (d.toDateString() === now.toDateString()) return fmtTime(d)
    return fmtDate(d, { day: '2-digit', month: 'short' })
  }

  const formatDateFull = (v) => {
    if (!v) return '-'
    return fmtDateTime(v, { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const getInitials = (value) => {
    if (!value) return '?'
    const cleaned = String(value).replace(/<[^>]+>/g, '').trim()
    const parts = cleaned.split(/\s+/).filter(Boolean)
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
    return cleaned.split('@')[0].substring(0, 2).toUpperCase()
  }

  const avatarColor = (value) => {
    const palette = ['#2563eb', '#7c3aed', '#0891b2', '#059669', '#ea580c', '#dc2626', '#4f46e5', '#0f766e']
    const source = String(value || '')
    let hash = 0
    for (let i = 0; i < source.length; i++) hash = ((hash << 5) - hash) + source.charCodeAt(i)
    return palette[Math.abs(hash) % palette.length]
  }

  const attachmentExtension = (attachment) => {
    const name = String(attachment?.name || '').toLowerCase()
    return name.includes('.') ? name.split('.').pop() : ''
  }

  const attachmentTypeClass = (attachment) => {
    if (attachment?.blocked) return 'type-blocked'
    if (attachment?.external_url) return 'type-link'
    const ext = attachmentExtension(attachment)
    if (['pdf'].includes(ext)) return 'type-pdf'
    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'].includes(ext)) return 'type-image'
    if (['xls', 'xlsx', 'csv'].includes(ext)) return 'type-sheet'
    if (['zip', 'rar', '7z'].includes(ext)) return 'type-archive'
    return 'type-other'
  }

  const attachmentIconClass = (attachment) => {
    const type = attachmentTypeClass(attachment)
    if (type === 'type-link') return 'fas fa-link'
    if (type === 'type-image') return 'fas fa-file-image'
    if (type === 'type-pdf') return 'fas fa-file-pdf'
    if (type === 'type-sheet') return 'fas fa-file-excel'
    if (type === 'type-archive') return 'fas fa-file-archive'
    if (type === 'type-blocked') return 'fas fa-ban'
    return 'fas fa-file-alt'
  }

  onMounted(() => { loadMailboxes(); mailViewRef.value?.focus() })
  onUnmounted(() => { clearTimeout(searchTimeout) })

  return {
    // Refs
    mailViewRef, messageRefs,
    // State
    mailboxes, messages, selectedMailboxId, selectedMailbox, selectedFolder, mailFolders, connectLabel,
    messageTotal, messageLimit, messageOffset, hasMoreMessages,
    selectedMessageId, selectedMessage, selectedMessageIndex, unreadCount,
    filteredMessages, displayBody, formattedPlainText, sanitizedBody,
    searchInput, searchQuery, searchFocused,
    loadingMailboxes, loadingMessages, loadingMoreMessages, loadingMessageBody, movingMessage,
    creating, sending, deleting,
    showCreate, mailboxDropdownOpen, actionsOpen,
    appPasswordOpen, appPasswordValue, connectingAppPassword, deleteConfirmOpen,
    mobileView, focusedMessageIndex,
    composeMode, inlineComposeOpen, newComposeOpen, composeForm, createForm,
    // Actions
    handleKeydown, loadMailboxes, selectMailbox, selectFolder, selectMessage,
    createMailbox, resetCreate, connectMailbox, connectMailboxAppPassword, closeAppPassword,
    loadMessages, loadMoreMessages, exportMailbox, confirmDelete, deleteMailbox,
    openNewCompose, replyToMessage, forwardMessage, closeInlineCompose, resetCompose, sendMail, moveSelectedMessage,
    // Display helpers
    statusLabel, statusDotClass, formatDate, formatDateFull, formatFileSize,
    downloadMailAttachment, getInitials, avatarColor, getSenderName, getSenderEmail,
    attachmentTypeClass, attachmentIconClass
  }
}

// Shared v-click-outside directive used by sidebar dropdown & reader actions.
export const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (e) => {
      if (!el.contains(e.target)) binding.value()
    }
    setTimeout(() => document.addEventListener('click', el._clickOutside), 0)
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutside)
  }
}
