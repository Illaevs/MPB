<template>
  <div class="tk-chat">
    <div class="tk-chat__header">
      <div class="tk-chat__title">
        <i class="far fa-comments"></i>
        <span>Переписка по тикету</span>
      </div>
      <button type="button" class="tk-chat__refresh" :disabled="loading" @click="reload">
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        <span>Обновить</span>
      </button>
    </div>

    <div class="tk-chat__body">
      <div ref="listRef" class="tk-chat__list">
        <div v-if="loading && !messages.length" class="tk-chat__empty">
          <i class="fas fa-spinner fa-spin mr-1"></i> Загрузка…
        </div>
        <div v-else-if="!messages.length" class="tk-chat__empty">
          Сообщений пока нет.
        </div>
        <div v-else class="tk-chat__messages">
          <div
            v-for="m in messages"
            :key="m.id"
            class="tk-chat__row"
            :class="{ 'is-own': isOwn(m), 'is-internal': m.is_internal }"
          >
            <div class="tk-chat__avatar" :style="avatarStyle(m)">{{ initial(m) }}</div>
            <div class="tk-chat__main">
              <div class="tk-chat__meta">
                <span class="tk-chat__author">{{ m.user_name || 'Пользователь' }}</span>
                <span v-if="m.is_internal" class="tk-chat__badge">внутренняя</span>
                <span class="tk-chat__time">{{ fmtTime(m.created_at) }}</span>
                <span v-if="m.edited_at" class="tk-chat__edited">изменено</span>
              </div>
              <div class="tk-chat__bubble" :class="{ 'is-own': isOwn(m), 'is-internal': m.is_internal }">
                <template v-if="m.is_deleted">
                  <span class="tk-chat__deleted">Сообщение удалено</span>
                </template>
                <template v-else>
                  <div v-if="editingId === m.id" class="tk-chat__edit">
                    <textarea v-model="editingBody" rows="3" class="tk-chat__edit-area"></textarea>
                    <div class="tk-chat__edit-actions">
                      <button class="tk-chat__btn tk-chat__btn--primary" @click="saveEdit(m)">Сохранить</button>
                      <button class="tk-chat__btn" @click="cancelEdit">Отмена</button>
                    </div>
                  </div>
                  <template v-else>
                    <div v-if="m.body" class="tk-chat__text">{{ m.body }}</div>
                    <div v-if="m.attachments && m.attachments.length" class="tk-chat__files">
                      <template v-for="(f, i) in m.attachments" :key="i">
                        <button
                          v-if="isImage(f)"
                          type="button"
                          class="tk-chat__img"
                          @click="lightbox = f"
                        >
                          <img :src="f.download_url || f.url" :alt="f.name" loading="lazy" />
                        </button>
                        <button
                          v-else
                          type="button"
                          class="tk-chat__file"
                          @click="download(f)"
                        >
                          <i :class="fileIcon(f)"></i>
                          <span class="tk-chat__file-name">{{ f.name || 'Файл' }}</span>
                          <span v-if="f.size" class="tk-chat__file-size">{{ fmtSize(f.size) }}</span>
                        </button>
                      </template>
                    </div>
                  </template>
                </template>
              </div>
              <div v-if="canModify(m) && editingId !== m.id" class="tk-chat__actions">
                <button v-if="m.body" type="button" class="tk-chat__link" @click="startEdit(m)">Редактировать</button>
                <button type="button" class="tk-chat__link is-danger" @click="remove(m)">Удалить</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="canWrite" class="tk-chat__composer">
        <div v-if="pendingFiles.length" class="tk-chat__pending">
          <div v-for="(f, i) in pendingFiles" :key="i" class="tk-chat__pending-item">
            <i class="fas fa-paperclip"></i>
            <span>{{ f.name }}</span>
            <button type="button" @click="pendingFiles.splice(i, 1)"><i class="fas fa-times"></i></button>
          </div>
        </div>
        <div class="tk-chat__bar">
          <textarea
            v-model="draft"
            class="tk-chat__input"
            rows="1"
            placeholder="Сообщение… (Ctrl+Enter — отправить, можно вставить скрин из буфера)"
            @keydown.ctrl.enter.prevent="send"
            @keydown.meta.enter.prevent="send"
            @paste="onPaste"
          ></textarea>
          <div class="tk-chat__tools">
            <label v-if="isStaff" class="tk-chat__internal" title="Видна только тех. поддержке">
              <input type="checkbox" v-model="sendInternal" />
              <span>внутр.</span>
            </label>
            <button type="button" class="tk-chat__tool" title="Прикрепить файл" @click="$refs.fileInput.click()">
              <i class="fas fa-paperclip"></i>
            </button>
            <button type="button" class="tk-chat__send" :disabled="sending" @click="send">
              <i v-if="sending" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
        <input ref="fileInput" type="file" multiple class="d-none" @change="onPick" />
      </div>
    </div>

    <Teleport to="body">
      <div v-if="lightbox" class="tk-lightbox" @click.self="lightbox = null">
        <button type="button" class="tk-lightbox__close" @click="lightbox = null"><i class="fas fa-times"></i></button>
        <img :src="lightbox.download_url || lightbox.url" :alt="lightbox.name" class="tk-lightbox__img" />
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { api } from '@/services/api'
import { getActiveUser } from '../utils/permissions'
import { useToast } from '../composables/useToast'
import { downloadFromApi } from '../utils/download'
import { formatDateTime } from '../utils/format'

const THEMES = [
  { background: 'linear-gradient(135deg,#d7e7ff,#b4d0ff)', color: '#2563eb' },
  { background: 'linear-gradient(135deg,#ffe4d3,#ffc79c)', color: '#b45309' },
  { background: 'linear-gradient(135deg,#e8ddff,#c8b4ff)', color: '#7c3aed' },
  { background: 'linear-gradient(135deg,#d9f7ec,#a9e7cb)', color: '#0f8f5d' },
  { background: 'linear-gradient(135deg,#ffe7ef,#ffc3d3)', color: '#be185d' },
]
const IMG_RE = /\.(png|jpe?g|gif|webp|bmp|svg|avif)$/i

export default {
  name: 'TicketChat',
  props: {
    ticketId: { type: [String, Number], default: '' },
    canWrite: { type: Boolean, default: true },
    isStaff: { type: Boolean, default: false },
  },
  emits: ['updated'],
  setup(props, { emit }) {
    const { error: toastError } = useToast()
    const messages = ref([])
    const loading = ref(false)
    const sending = ref(false)
    const draft = ref('')
    const sendInternal = ref(false)
    const pendingFiles = ref([])
    const editingId = ref(null)
    const editingBody = ref('')
    const lightbox = ref(null)
    const listRef = ref(null)
    const fileInput = ref(null)
    let timer = null

    const me = () => getActiveUser()
    const isOwn = (m) => String(m.user_id) === String(me()?.id)
    const canModify = (m) =>
      !m.is_deleted && (isOwn(m) || props.isStaff || me()?.is_superuser)

    const initial = (m) => String(m.user_name || 'П').trim().charAt(0).toUpperCase() || 'П'
    const avatarStyle = (m) => {
      const key = String(m.user_id || '') + String(m.user_name || '')
      const idx = key.split('').reduce((s, c) => s + c.charCodeAt(0), 0) % THEMES.length
      return THEMES[idx]
    }
    const fmtTime = (v) => {
      if (!v) return ''
      try { return formatDateTime(v, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) }
      catch { return v }
    }
    const fmtSize = (b) => {
      const u = ['Б', 'КБ', 'МБ', 'ГБ']; let i = 0; let v = Number(b) || 0
      while (v >= 1024 && i < u.length - 1) { v /= 1024; i += 1 }
      return `${v.toFixed(i === 0 ? 0 : 1)} ${u[i]}`
    }
    const isImage = (f) =>
      (f?.content_type && String(f.content_type).startsWith('image/')) || IMG_RE.test(String(f?.name || ''))
    const fileIcon = (f) => {
      const n = String(f?.name || '').toLowerCase()
      if (/\.pdf$/.test(n)) return 'far fa-file-pdf'
      if (/\.(docx?)$/.test(n)) return 'far fa-file-word'
      if (/\.(xlsx?|csv)$/.test(n)) return 'far fa-file-excel'
      return 'far fa-file'
    }

    const scrollBottom = async () => {
      await nextTick()
      if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
    }

    const load = async ({ silent = false } = {}) => {
      if (!props.ticketId) return
      if (!silent) loading.value = true
      try {
        const data = await api.support.getTicket(props.ticketId)
        const next = (data && data.messages) || []
        const grew = next.length > messages.value.length
        messages.value = next
        emit('updated', data)
        if (grew) await scrollBottom()
      } catch (e) {
        if (!silent) toastError('Не удалось загрузить переписку')
      } finally {
        if (!silent) loading.value = false
      }
    }
    const reload = () => { if (!loading.value) load() }

    const onPick = (e) => {
      const files = Array.from(e.target.files || [])
      if (files.length) pendingFiles.value.push(...files)
      e.target.value = ''
    }
    const onPaste = (e) => {
      const items = e.clipboardData && e.clipboardData.items
      if (!items) return
      for (const it of items) {
        if (it.kind === 'file' && it.type.startsWith('image/')) {
          const blob = it.getAsFile()
          if (blob) {
            const ext = (it.type.split('/')[1] || 'png').split('+')[0]
            const file = new File([blob], `screenshot-${Date.now()}.${ext}`, { type: it.type })
            pendingFiles.value.push(file)
          }
        }
      }
    }

    const send = async () => {
      if (sending.value) return
      const text = draft.value.trim()
      if (!text && !pendingFiles.value.length) return
      sending.value = true
      try {
        const form = new FormData()
        if (text) form.append('body', text)
        if (props.isStaff && sendInternal.value) form.append('is_internal', 'true')
        pendingFiles.value.forEach((f) => form.append('files', f, f.name))
        const res = await api.support.addMessage(props.ticketId, form)
        if (res) messages.value = [...messages.value, res]
        draft.value = ''
        pendingFiles.value = []
        saveDraft('')
        await scrollBottom()
        emit('updated')
      } catch (e) {
        toastError('Не удалось отправить сообщение')
      } finally {
        sending.value = false
      }
    }

    const startEdit = (m) => { editingId.value = m.id; editingBody.value = m.body || '' }
    const cancelEdit = () => { editingId.value = null; editingBody.value = '' }
    const saveEdit = async (m) => {
      const b = editingBody.value.trim()
      if (!b) return
      try {
        const res = await api.support.updateMessage(m.id, { body: b })
        messages.value = messages.value.map((x) => (x.id === m.id ? res : x))
        cancelEdit()
      } catch (e) { toastError('Не удалось изменить сообщение') }
    }
    const remove = async (m) => {
      try {
        await api.support.deleteMessage(m.id)
        messages.value = messages.value.map((x) =>
          x.id === m.id ? { ...x, is_deleted: true, body: null } : x)
      } catch (e) { toastError('Не удалось удалить сообщение') }
    }
    const download = async (f) => {
      try {
        if (f?.download_url) await downloadFromApi(f.download_url, {}, f.name || 'file', { module: 'support' })
      } catch (e) { toastError('Не удалось скачать файл') }
    }

    const draftKey = () => `ticketChat.draft.${props.ticketId}`
    const saveDraft = (v) => { try { v ? localStorage.setItem(draftKey(), v) : localStorage.removeItem(draftKey()) } catch (_e) { /* noop */ } }
    watch(draft, (v) => saveDraft(v))

    const start = () => {
      stop()
      if (props.ticketId) timer = setInterval(() => load({ silent: true }), 12000)
    }
    const stop = () => { if (timer) { clearInterval(timer); timer = null } }

    watch(() => props.ticketId, async (id) => {
      messages.value = []
      cancelEdit()
      try { draft.value = localStorage.getItem(draftKey()) || '' } catch (_e) { draft.value = '' }
      if (id) { await load(); start() }
    })

    onMounted(async () => {
      try { draft.value = localStorage.getItem(draftKey()) || '' } catch (_e) { draft.value = '' }
      if (props.ticketId) { await load(); start() }
    })
    onBeforeUnmount(stop)

    return {
      messages, loading, sending, draft, sendInternal, pendingFiles,
      editingId, editingBody, lightbox, listRef, fileInput,
      isOwn, canModify, initial, avatarStyle, fmtTime, fmtSize,
      isImage, fileIcon, reload, onPick, onPaste, send,
      startEdit, cancelEdit, saveEdit, remove, download,
    }
  },
}
</script>

<style scoped>
.tk-chat { display: flex; flex-direction: column; min-height: 0; height: 100%; background: var(--color-surface); color: var(--color-text); }
.tk-chat__header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--color-border-subtle); }
.tk-chat__title { display: inline-flex; align-items: center; gap: var(--space-2); font-weight: var(--fw-semibold); }
.tk-chat__title i { color: var(--color-text-muted); }
.tk-chat__refresh { display: inline-flex; align-items: center; gap: 6px; border: 0; background: transparent; color: var(--color-text-muted); font-weight: var(--fw-medium); cursor: pointer; padding: 4px 8px; border-radius: var(--radius-sm); }
.tk-chat__refresh:hover { background: var(--color-surface-2); color: var(--color-text); }
.tk-chat__body { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
.tk-chat__list { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: var(--space-4); }
.tk-chat__empty { text-align: center; color: var(--color-text-subtle); padding: var(--space-10) var(--space-4); }
.tk-chat__messages { display: flex; flex-direction: column; gap: var(--space-4); }
.tk-chat__row { display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: var(--space-3); align-items: start; }
.tk-chat__row.is-own { grid-template-columns: minmax(0, 1fr) 34px; }
.tk-chat__row.is-own .tk-chat__avatar { order: 2; }
.tk-chat__row.is-own .tk-chat__main { order: 1; align-items: flex-end; }
.tk-chat__avatar { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: var(--fw-bold); font-size: var(--text-base); }
.tk-chat__main { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.tk-chat__meta { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--color-text-subtle); }
.tk-chat__author { color: var(--color-text); font-weight: var(--fw-semibold); }
.tk-chat__badge { padding: 1px 7px; border-radius: var(--radius-pill); background: var(--color-warning-soft); color: var(--color-warning); font-size: var(--text-xs); font-weight: var(--fw-bold); text-transform: uppercase; letter-spacing: 0.03em; }
.tk-chat__edited { font-style: italic; }
.tk-chat__bubble { max-width: min(560px, 80%); padding: 9px 13px; border-radius: 14px; background: var(--color-surface); border: 1px solid var(--color-border); box-shadow: var(--shadow-xs); }
.tk-chat__bubble.is-own { background: var(--color-primary); border-color: var(--color-primary); color: var(--color-on-primary); }
.tk-chat__bubble.is-internal { background: var(--color-warning-soft); border-color: color-mix(in srgb, var(--color-warning) 40%, transparent); color: var(--color-text); }
.tk-chat__text { white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; font-size: var(--text-md); line-height: var(--leading-normal); }
.tk-chat__deleted { color: var(--color-text-subtle); font-style: italic; }
.tk-chat__files { display: flex; flex-direction: column; gap: 6px; margin-top: 6px; }
.tk-chat__img { padding: 0; border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; background: var(--color-surface-2); cursor: zoom-in; width: fit-content; }
.tk-chat__img img { display: block; max-width: 240px; max-height: 180px; }
.tk-chat__file { display: inline-flex; align-items: center; gap: 8px; padding: 7px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); cursor: pointer; text-align: left; }
.tk-chat__file:hover { background: var(--color-surface-3); }
.tk-chat__file-name { font-weight: var(--fw-semibold); font-size: var(--text-sm); }
.tk-chat__file-size { color: var(--color-text-subtle); font-size: var(--text-xs); }
.tk-chat__actions { display: inline-flex; gap: var(--space-3); padding: 0 2px; }
.tk-chat__row.is-own .tk-chat__actions { justify-content: flex-end; }
.tk-chat__link { border: 0; background: transparent; color: var(--color-text-muted); font-size: var(--text-sm); font-weight: var(--fw-semibold); cursor: pointer; padding: 0; }
.tk-chat__link:hover { color: var(--color-primary); }
.tk-chat__link.is-danger { color: var(--color-danger); }
.tk-chat__edit { display: flex; flex-direction: column; gap: 6px; }
.tk-chat__edit-area { width: 100%; border: 1px solid var(--color-border-strong); border-radius: 8px; padding: 6px 8px; font: inherit; resize: vertical; }
.tk-chat__edit-actions { display: flex; justify-content: flex-end; gap: 6px; }
.tk-chat__btn { border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 7px; padding: 4px 10px; font-size: var(--text-sm); font-weight: var(--fw-semibold); cursor: pointer; }
.tk-chat__btn--primary { background: var(--color-primary); border-color: var(--color-primary); color: var(--color-on-primary); }
.tk-chat__composer { border-top: 1px solid var(--color-border-subtle); padding: var(--space-3) var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); }
.tk-chat__pending { display: flex; flex-direction: column; gap: 4px; }
.tk-chat__pending-item { display: inline-flex; align-items: center; gap: 8px; padding: 6px 10px; background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: var(--text-sm); }
.tk-chat__pending-item button { border: 0; background: transparent; color: var(--color-danger); cursor: pointer; margin-left: auto; }
.tk-chat__bar { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2); align-items: end; padding: 8px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.tk-chat__bar:focus-within { border-color: var(--color-primary); box-shadow: var(--shadow-focus); }
.tk-chat__input { min-height: 24px; max-height: 180px; resize: none; border: 0; outline: none; background: transparent; color: var(--color-text); font: inherit; font-size: var(--text-md); padding: 4px 0; }
.tk-chat__tools { display: inline-flex; align-items: center; gap: 6px; }
.tk-chat__internal { display: inline-flex; align-items: center; gap: 4px; font-size: var(--text-xs); font-weight: var(--fw-semibold); color: var(--color-warning); cursor: pointer; }
.tk-chat__tool, .tk-chat__send { width: 34px; height: 34px; border: 0; border-radius: var(--radius-md); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.tk-chat__tool { background: var(--color-surface-2); color: var(--color-text-muted); }
.tk-chat__tool:hover { background: var(--color-surface-3); }
.tk-chat__send { background: var(--color-primary); color: var(--color-on-primary); }
.tk-chat__send:disabled { opacity: 0.55; cursor: default; }
.d-none { display: none; }
.tk-lightbox { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.84); display: flex; align-items: center; justify-content: center; z-index: 2200; cursor: zoom-out; }
.tk-lightbox__img { max-width: 92vw; max-height: 86vh; border-radius: var(--radius-md); box-shadow: var(--shadow-xl); }
.tk-lightbox__close { position: absolute; top: 16px; right: 16px; width: 40px; height: 40px; border-radius: 50%; border: 0; background: rgba(255,255,255,0.14); color: #fff; cursor: pointer; }
</style>
