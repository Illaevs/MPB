import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as messengerApi from '../services/api/messenger'
import { getActiveUser, hasSectionAccess } from '../utils/permissions'
import { useToast } from './useToast'
import { useUsersStore } from '../stores/users'
import { downloadFromApi } from '../utils/download'
import { formatDateTime as fmtDateTime, formatTime as fmtTime } from '../utils/format'

const LAST_SEEN_KEY_PREFIX = 'messenger_last_seen_'
const MAX_FILE_BYTES = 1024 * 1024 * 1024
const LINK_RE = /https?:\/\/[^\s<>"']+/gi
const SAFE_PREVIEW_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif'])

const fileLooksLikeImage = (file = {}) => {
  const contentType = String(file.content_type || '').toLowerCase()
  const name = String(file.name || '').toLowerCase()
  if (contentType.startsWith('image/')) return true
  return ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].some((ext) => name.endsWith(ext))
}

const canPreviewImage = (file = {}) => SAFE_PREVIEW_IMAGE_TYPES.has(String(file.type || file.content_type || '').toLowerCase())

const createPendingFileEntry = (file) => {
  const previewUrl = canPreviewImage(file) ? URL.createObjectURL(file) : ''
  return {
    id: `${Date.now()}_${Math.random().toString(36).slice(2)}`,
    file,
    name: file.name || 'Файл',
    size: file.size || 0,
    type: String(file.type || '').toLowerCase(),
    previewUrl,
    isImagePreview: !!previewUrl
  }
}

export function useMessenger() {
  const { error: toastError, success: toastSuccess } = useToast()
  const usersStore = useUsersStore()

  const permissionsVersion = ref(0)
  const loadingConversations = ref(false)
  const loadingMessages = ref(false)
  const sending = ref(false)
  const savingConversation = ref(false)
  const conversations = ref([])
  const activeConversationId = ref('')
  const messages = ref([])
  const users = ref([])
  const draft = ref('')
  const pendingFiles = ref([])
  const mentionPickerOpen = ref(false)
  const mentionQuery = ref('')
  const selectedMentions = ref([])
  const editingId = ref(null)
  const editingBody = ref('')
  const replyTarget = ref(null)
  const pollingTimer = ref(null)

  const touchPermissions = () => {
    permissionsVersion.value += 1
  }

  const activeUser = computed(() => {
    permissionsVersion.value
    return getActiveUser()
  })

  const enabled = computed(() => {
    permissionsVersion.value
    return !!getActiveUser() && hasSectionAccess('global_chat')
  })

  const activeConversation = computed(
    () => conversations.value.find((item) => String(item.id) === String(activeConversationId.value)) || null
  )
  const members = computed(() => activeConversation.value?.members || [])
  const canManageMembers = computed(() => !!activeConversation.value?.can_manage_members)
  const isEditMode = computed(() => !!editingId.value)
  const loading = computed(() => loadingConversations.value || loadingMessages.value)

  const mentionOptions = computed(() => {
    const query = (mentionQuery.value || '').trim().toLowerCase()
    const selectedIds = new Set(selectedMentions.value.map((item) => String(item.id)))
    const memberIds = new Set(members.value.map((item) => String(item.user_id)))
    const source = users.value.filter((user) => {
      if (!user?.id) return false
      if (memberIds.size && !memberIds.has(String(user.id))) return false
      return true
    })
    return source.filter((user) => {
      if (selectedIds.has(String(user.id))) return false
      if (!query) return true
      const haystack = `${user.full_name || ''} ${user.email || ''}`.toLowerCase()
      return haystack.includes(query)
    })
  })

  const files = computed(() =>
    messages.value.flatMap((message) =>
      (message.attachments || []).map((file) => ({
        ...file,
        key: `${message.id}:${file.path || file.name}`,
        message_id: message.id,
        message_user_name: message.user_name || 'Пользователь',
        created_at: message.created_at,
        is_image: fileLooksLikeImage(file)
      }))
    )
  )

  const links = computed(() => {
    const seen = new Set()
    const result = []
    messages.value.forEach((message) => {
      const matches = String(message?.body || '').match(LINK_RE) || []
      matches.forEach((url) => {
        const key = `${message.id}:${url}`
        if (seen.has(key)) return
        seen.add(key)
        result.push({
          url,
          text: url,
          message_id: message.id,
          message_user_name: message.user_name || 'Пользователь',
          created_at: message.created_at
        })
      })
    })
    return result
  })

  const revokePendingPreview = (entry) => {
    if (entry?.previewUrl) {
      URL.revokeObjectURL(entry.previewUrl)
    }
  }

  const resetComposer = () => {
    draft.value = ''
    pendingFiles.value.forEach(revokePendingPreview)
    pendingFiles.value = []
    mentionPickerOpen.value = false
    mentionQuery.value = ''
    selectedMentions.value = []
    editingId.value = null
    editingBody.value = ''
    replyTarget.value = null
  }

  const getLastSeenKey = (conversationId) => `${LAST_SEEN_KEY_PREFIX}${conversationId}`

  const getLastSeenAt = (conversationId) => {
    if (!conversationId) return 0
    try {
      return Number(localStorage.getItem(getLastSeenKey(conversationId)) || 0)
    } catch (error) {
      return 0
    }
  }

  const markConversationSeen = (conversationId = activeConversationId.value, items = messages.value) => {
    const latest = [...items].reverse().find((item) => item?.created_at)
    const ts = latest?.created_at ? new Date(latest.created_at).getTime() : Date.now()
    try {
      localStorage.setItem(getLastSeenKey(conversationId), String(ts))
    } catch (error) {
      // ignore storage failures
    }
  }

  const isConversationUnread = (conversation) => {
    if (!conversation?.last_message?.created_at) return false
    if (String(conversation.last_message.user_id || '') === String(activeUser.value?.id || '')) return false
    const lastSeenAt = getLastSeenAt(conversation.id)
    return new Date(conversation.last_message.created_at).getTime() > lastSeenAt
  }

  const isOwn = (message) => String(message?.user_id || '') === String(activeUser.value?.id || '')

  const canEdit = (message) => {
    if (!message || message.is_deleted) return false
    if (activeUser.value?.is_superuser) return true
    return isOwn(message)
  }

  const formatDateTime = (value) => {
    if (!value) return ''
    try {
      return fmtDateTime(value, {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: 'short'
      })
    } catch (error) {
      return value
    }
  }

  const formatMessageTime = (value) => {
    if (!value) return ''
    try {
      return fmtTime(value)
    } catch (error) {
      return value
    }
  }

  const formatSize = (bytes) => {
    if (!bytes && bytes !== 0) return ''
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ']
    let index = 0
    let value = Number(bytes)
    while (value >= 1024 && index < sizes.length - 1) {
      value /= 1024
      index += 1
    }
    return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${sizes[index]}`
  }

  const loadUsers = async () => {
    if (!enabled.value) return
    try {
      await usersStore.ensureLoaded()
      users.value = usersStore.items
    } catch (error) {
      users.value = []
    }
  }

  const loadConversations = async ({ silent = false, preferredId = null } = {}) => {
    if (!enabled.value) return []
    if (!silent) loadingConversations.value = true
    try {
      const result = await messengerApi.list()
      conversations.value = result || []
      const targetId = String(preferredId || activeConversationId.value || '')
      const exists = conversations.value.find((item) => String(item.id) === targetId)
      if (exists) {
        activeConversationId.value = String(exists.id)
      } else {
        activeConversationId.value = String(conversations.value[0]?.id || '')
      }
      return conversations.value
    } catch (error) {
      conversations.value = []
      activeConversationId.value = ''
      if (!silent) toastError('Не удалось загрузить чаты')
      return []
    } finally {
      if (!silent) loadingConversations.value = false
    }
  }

  const loadMessages = async (conversationId = activeConversationId.value, { silent = false } = {}) => {
    if (!enabled.value || !conversationId) {
      messages.value = []
      return []
    }
    if (!silent) loadingMessages.value = true
    try {
      const result = await messengerApi.listMessages(conversationId)
      messages.value = result || []
      return messages.value
    } catch (error) {
      messages.value = []
      if (!silent) toastError('Не удалось загрузить сообщения')
      return []
    } finally {
      if (!silent) loadingMessages.value = false
    }
  }

  const selectConversation = async (conversationId, { silent = false } = {}) => {
    const targetId = String(conversationId || '')
    if (!targetId) return
    activeConversationId.value = targetId
    resetComposer()
    await loadMessages(targetId, { silent })
  }

  const startPolling = () => {
    if (pollingTimer.value || !enabled.value) return
    pollingTimer.value = setInterval(async () => {
      const preferredId = activeConversationId.value
      await loadConversations({ silent: true, preferredId })
      if (activeConversationId.value) {
        await loadMessages(activeConversationId.value, { silent: true })
      }
    }, 8000)
  }

  const stopPolling = () => {
    if (!pollingTimer.value) return
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }

  const openFilePicker = (fileInputEl) => {
    if (!fileInputEl) return
    fileInputEl.click()
  }

  const appendPendingFiles = (filesList, { clipboardOnlyImages = false } = {}) => {
    if (!filesList.length) return
    const oversized = filesList.find((file) => file.size > MAX_FILE_BYTES)
    if (oversized) {
      toastError('Файл превышает лимит 1 ГБ')
      return { added: 0, skipped: filesList.length }
    }
    const acceptedFiles = clipboardOnlyImages
      ? filesList.filter((file) => SAFE_PREVIEW_IMAGE_TYPES.has(String(file.type || '').toLowerCase()))
      : filesList

    const entries = acceptedFiles.map(createPendingFileEntry)
    pendingFiles.value = [...pendingFiles.value, ...entries]
    return { added: entries.length, skipped: filesList.length - entries.length }
  }

  const onFilesPicked = (event) => {
    const filesList = Array.from(event?.target?.files || [])
    if (!filesList.length) return
    appendPendingFiles(filesList)
    if (event?.target) event.target.value = ''
  }

  const removeFile = (index) => {
    const [removed] = pendingFiles.value.splice(index, 1)
    revokePendingPreview(removed)
  }

  const toggleMentions = () => {
    mentionPickerOpen.value = !mentionPickerOpen.value
    mentionQuery.value = ''
  }

  const addMention = (user) => {
    if (!user) return
    selectedMentions.value.push({
      id: user.id,
      name: user.full_name || user.email || user.id
    })
    const mentionText = `@${user.full_name || user.email || ''}`.trim()
    if (editingId.value) {
      editingBody.value = `${editingBody.value.trim()} ${mentionText}`.trim() + ' '
    } else {
      draft.value = `${draft.value.trim()} ${mentionText}`.trim() + ' '
    }
    mentionPickerOpen.value = false
    mentionQuery.value = ''
  }

  const removeMention = (userId) => {
    selectedMentions.value = selectedMentions.value.filter((item) => String(item.id) !== String(userId))
  }

  const createDirectConversation = async (userId) => {
    if (!userId) return null
    savingConversation.value = true
    try {
      const result = await messengerApi.createDirect(userId)
      await loadConversations({ silent: true, preferredId: result?.id })
      await selectConversation(result?.id, { silent: true })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось открыть личный чат')
      return null
    } finally {
      savingConversation.value = false
    }
  }

  const createConversation = async (payload) => {
    savingConversation.value = true
    try {
      const result = await messengerApi.create(payload)
      await loadConversations({ silent: true, preferredId: result?.id })
      await selectConversation(result?.id, { silent: true })
      toastSuccess('Чат создан')
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось создать чат')
      return null
    } finally {
      savingConversation.value = false
    }
  }

  const updateConversation = async (payload) => {
    if (!activeConversationId.value) return null
    savingConversation.value = true
    try {
      const result = await messengerApi.update(activeConversationId.value, payload)
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось обновить чат')
      return null
    } finally {
      savingConversation.value = false
    }
  }

  const addConversationMembers = async (userIds) => {
    if (!activeConversationId.value || !userIds?.length) return null
    savingConversation.value = true
    try {
      const result = await messengerApi.addMembers(activeConversationId.value, userIds)
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось добавить участников')
      return null
    } finally {
      savingConversation.value = false
    }
  }

  const removeConversationMember = async (userId) => {
    if (!activeConversationId.value || !userId) return null
    savingConversation.value = true
    try {
      const result = await messengerApi.removeMember(activeConversationId.value, userId)
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось удалить участника')
      return null
    } finally {
      savingConversation.value = false
    }
  }

  const sendMessage = async () => {
    if (sending.value || !activeConversationId.value) return null
    const text = (draft.value || '').trim()
    if (!text && !pendingFiles.value.length && !replyTarget.value) return null

    sending.value = true
    try {
      const form = new FormData()
      if (text) form.append('body', text)
      if (selectedMentions.value.length) {
        form.append('mentions', JSON.stringify(selectedMentions.value.map((item) => item.id)))
      }
      if (replyTarget.value?.id) {
        form.append('reply_to_message_id', replyTarget.value.id)
      }
      pendingFiles.value.forEach((entry) => form.append('files', entry.file, entry.name))

      const result = await messengerApi.sendMessage(activeConversationId.value, form)
      if (result) {
        messages.value = [...messages.value, result]
      }
      draft.value = ''
      pendingFiles.value.forEach(revokePendingPreview)
      pendingFiles.value = []
      selectedMentions.value = []
      replyTarget.value = null
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      markConversationSeen(activeConversationId.value, messages.value)
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось отправить сообщение')
      return null
    } finally {
      sending.value = false
    }
  }

  const forwardMessage = async (message, targetConversationId) => {
    if (!message?.id || !targetConversationId) return null
    sending.value = true
    try {
      const form = new FormData()
      form.append('forwarded_from_message_id', message.id)
      const result = await messengerApi.sendMessage(targetConversationId, form)
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      if (String(targetConversationId) === String(activeConversationId.value)) {
        messages.value = [...messages.value, result]
        markConversationSeen(activeConversationId.value, messages.value)
      }
      toastSuccess('Сообщение переслано')
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось переслать сообщение')
      return null
    } finally {
      sending.value = false
    }
  }

  const startReply = (message) => {
    replyTarget.value = message || null
  }

  const cancelReply = () => {
    replyTarget.value = null
  }

  const startEdit = (message) => {
    if (!message || message.is_deleted) return
    editingId.value = message.id
    editingBody.value = message.body || ''
  }

  const cancelEdit = () => {
    editingId.value = null
    editingBody.value = ''
  }

  const saveEdit = async (message) => {
    if (!message?.id || !editingBody.value.trim()) return null
    sending.value = true
    try {
      const result = await messengerApi.updateMessage(message.id, {
        body: editingBody.value.trim()
      })
      messages.value = messages.value.map((item) => (item.id === message.id ? result : item))
      cancelEdit()
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось сохранить сообщение')
      return null
    } finally {
      sending.value = false
    }
  }

  const deleteMessage = async (message) => {
    if (!message?.id) return false
    try {
      await messengerApi.deleteMessage(message.id)
      messages.value = messages.value.map((item) =>
        item.id === message.id
          ? { ...item, is_deleted: true, body: null, attachments: [], is_pinned: false }
          : item
      )
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return true
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось удалить сообщение')
      return false
    }
  }

  const pinMessage = async (message) => {
    if (!message?.id) return null
    try {
      const result = await messengerApi.pinMessage(message.id)
      messages.value = messages.value.map((item) => ({
        ...item,
        is_pinned: item.id === message.id
      }))
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось закрепить сообщение')
      return null
    }
  }

  const unpinMessage = async (message) => {
    if (!message?.id) return null
    try {
      const result = await messengerApi.unpinMessage(message.id)
      messages.value = messages.value.map((item) =>
        item.id === message.id ? { ...item, is_pinned: false } : item
      )
      await loadConversations({ silent: true, preferredId: activeConversationId.value })
      return result || null
    } catch (error) {
      toastError(error.response?.data?.detail || 'Не удалось снять закреп')
      return null
    }
  }

  const downloadAttachment = async (file) => {
    try {
      if (!file?.download_url) return
      await downloadFromApi(
        file.download_url,
        {},
        file.name || 'файл',
        { module: 'messenger', entityId: activeConversationId.value }
      )
    } catch (error) {
      toastError('Не удалось скачать файл')
    }
  }

  const initialize = async () => {
    if (!enabled.value) return
    await Promise.all([loadUsers(), loadConversations()])
    if (activeConversationId.value) {
      await loadMessages(activeConversationId.value)
    }
    startPolling()
  }

  watch(enabled, async (value) => {
    if (!value) {
      stopPolling()
      conversations.value = []
      messages.value = []
      activeConversationId.value = ''
      resetComposer()
      return
    }
    await initialize()
  })

  onMounted(() => {
    window.addEventListener('permissions-updated', touchPermissions)
    window.addEventListener('storage', touchPermissions)
    initialize()
  })

  onBeforeUnmount(() => {
    window.removeEventListener('permissions-updated', touchPermissions)
    window.removeEventListener('storage', touchPermissions)
    pendingFiles.value.forEach(revokePendingPreview)
    stopPolling()
  })

  return {
    activeUser,
    enabled,
    loading,
    loadingConversations,
    loadingMessages,
    savingConversation,
    sending,
    conversations,
    activeConversationId,
    activeConversation,
    users,
    messages,
    members,
    files,
    links,
    draft,
    pendingFiles,
    mentionPickerOpen,
    mentionQuery,
    mentionOptions,
    selectedMentions,
    editingId,
    editingBody,
    replyTarget,
    isEditMode,
    canManageMembers,
    isConversationUnread,
    isOwn,
    canEdit,
    formatDateTime,
    formatMessageTime,
    formatSize,
    markConversationSeen,
    loadConversations,
    loadMessages,
    selectConversation,
    openFilePicker,
    appendPendingFiles,
    onFilesPicked,
    removeFile,
    toggleMentions,
    addMention,
    removeMention,
    createDirectConversation,
    createConversation,
    updateConversation,
    addConversationMembers,
    removeConversationMember,
    sendMessage,
    forwardMessage,
    startReply,
    cancelReply,
    startEdit,
    cancelEdit,
    saveEdit,
    deleteMessage,
    pinMessage,
    unpinMessage,
    downloadAttachment,
    resetComposer
  }
}
