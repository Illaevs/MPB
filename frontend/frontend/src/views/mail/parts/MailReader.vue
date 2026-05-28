<template>
  <main class="mail-reader-pane">
    <template v-if="selectedMessage">
      <div class="reader-toolbar">
        <div class="reader-actions-left">
          <button class="reader-action" @click="$emit('reply')" title="Ответить">
            <i class="fas fa-reply"></i>
          </button>
          <button class="reader-action" @click="$emit('forward')" title="Переслать">
            <i class="fas fa-share"></i>
          </button>
          <span class="reader-divider"></span>
          <button class="reader-action muted" :disabled="movingMessage" @click="$emit('move', 'archive')" title="Архив">
            <i class="fas fa-archive"></i>
          </button>
          <button class="reader-action muted" :disabled="movingMessage" @click="$emit('move', 'trash')" title="Удалить">
            <i class="fas fa-trash-alt"></i>
          </button>
          <button class="reader-action muted" :disabled="movingMessage" @click="$emit('move', 'spam')" title="Спам">
            <i class="fas fa-exclamation-circle"></i>
          </button>
        </div>

        <div class="reader-actions-right">
          <span class="reader-counter">{{ selectedMessageIndex + 1 }} из {{ filteredMessages.length }}</span>
          <button
            class="reader-action"
            :disabled="!selectedMailbox || loadingMessages"
            @click="$emit('reload')"
            title="Синхронизировать"
          >
            <i class="fas fa-sync" :class="{ 'fa-spin': loadingMessages }"></i>
          </button>
          <div class="dropdown" v-if="selectedMailbox">
            <button class="reader-action" @click="$emit('update:actionsOpen', !actionsOpen)" title="Действия">
              <i class="fas fa-ellipsis-v"></i>
            </button>
            <transition name="dropdown-fade">
              <div v-if="actionsOpen" class="actions-dropdown-menu" v-click-outside="() => $emit('update:actionsOpen', false)">
                <button class="dropdown-item" @click="$emit('connect-mailbox'); $emit('update:actionsOpen', false)">
                  <i class="fas fa-plug"></i> {{ connectLabel }}
                </button>
                <button class="dropdown-item" @click="$emit('open-app-password'); $emit('update:actionsOpen', false)">
                  <i class="fas fa-key"></i> Пароль приложения
                </button>
                <button class="dropdown-item" @click="$emit('export-mailbox'); $emit('update:actionsOpen', false)">
                  <i class="fas fa-file-export"></i> Экспорт 30 дней
                </button>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item text-danger" @click="$emit('confirm-delete')">
                  <i class="fas fa-trash"></i> Удалить ящик
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <div class="reader-scroll">
        <article class="reader-inner">
          <header class="reader-header">
            <div class="reader-title-row">
              <h1>{{ selectedMessage.subject || '(без темы)' }}</h1>
              <div v-if="selectedMessage.attachments?.length" class="reader-labels">
                <span>Вложения</span>
              </div>
            </div>

            <div class="sender-card">
              <div class="avatar-sm">{{ getInitials(getSenderName(selectedMessage)) }}</div>
              <div class="sender-main">
                <div class="sender-line">
                  <strong>{{ getSenderName(selectedMessage) }}</strong>
                  <span>&lt;{{ getSenderEmail(selectedMessage) }}&gt;</span>
                </div>
                <div class="sender-to">
                  Кому: <span>{{ selectedMessage.to_addr || selectedMailbox?.email || '-' }}</span>
                </div>
                <div v-if="selectedMessage.cc_addr" class="sender-to">
                  Копия: <span>{{ selectedMessage.cc_addr }}</span>
                </div>
              </div>
              <div class="sender-date">
                <strong>{{ formatDate(selectedMessage.date) }}</strong>
                <span>{{ formatDateFull(selectedMessage.date) }}</span>
              </div>
            </div>
          </header>

          <section v-if="selectedMessage.attachments?.length" class="attachment-section">
            <div class="attachment-title">
              <i class="fas fa-paperclip"></i>
              <span>Вложения ({{ selectedMessage.attachments.length }})</span>
            </div>
            <div class="attachment-grid">
              <button
                v-for="att in selectedMessage.attachments"
                :key="att.id"
                class="attachment-card"
                :class="{ blocked: att.blocked }"
                :disabled="att.blocked || (!att.download_url && !att.external_url)"
                :title="att.blocked_reason || (att.external_url ? 'Открыть ссылку' : 'Скачать вложение')"
                @click="$emit('download-attachment', att)"
              >
                <span class="attachment-icon" :class="attachmentTypeClass(att)">
                  <i :class="attachmentIconClass(att)"></i>
                </span>
                <span class="attachment-info">
                  <strong>{{ att.name }}</strong>
                  <small>{{ att.blocked_reason || (att.external_url ? 'Внешняя ссылка' : '') || formatFileSize(att.size) || att.content_type || 'Файл' }}</small>
                </span>
              </button>
            </div>
          </section>

          <div class="reader-body">
            <div v-if="loadingMessageBody" class="body-loading">
              <i class="fas fa-spinner fa-spin"></i> Загрузка...
            </div>
            <div v-if="displayBody.body_html" v-html="sanitizedBody" class="message-html"></div>
            <div v-else-if="displayBody.body_text && formattedPlainText" v-html="formattedPlainText" class="message-html message-plain-formatted"></div>
            <div v-else-if="displayBody.body_text" class="message-text">{{ displayBody.body_text }}</div>
            <div v-else class="text-muted">{{ selectedMessage.snippet || 'Нет содержимого' }}</div>
          </div>

          <div class="quick-reply" @click="$emit('reply')">
            <div class="quick-avatar">{{ getInitials(selectedMailbox?.name || 'UN') }}</div>
            <div class="quick-input">Нажмите сюда для быстрого ответа...</div>
          </div>
        </article>
      </div>

      <transition name="slide-up">
        <div v-if="inlineComposeOpen" class="inline-compose">
          <div class="inline-compose-header">
            <span class="fw-600">
              <i class="fas" :class="composeMode === 'reply' ? 'fa-reply' : 'fa-share'"></i>
              {{ composeMode === 'reply' ? 'Ответ' : 'Пересылка' }}
            </span>
            <button class="reader-action" @click="$emit('close-inline-compose')" title="Закрыть">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="inline-compose-fields">
            <div class="inline-field">
              <label>Кому</label>
              <input
                :value="composeForm.to"
                @input="updateField('to', $event.target.value)"
                class="form-control form-control-sm"
                placeholder="email@example.com"
              >
            </div>
            <div class="inline-field">
              <label>Тема</label>
              <input
                :value="composeForm.subject"
                @input="updateField('subject', $event.target.value)"
                class="form-control form-control-sm"
              >
            </div>
            <textarea
              :value="composeForm.body"
              @input="updateField('body', $event.target.value)"
              class="form-control form-control-sm inline-textarea"
              placeholder="Текст сообщения..."
              rows="4"
            ></textarea>
          </div>
          <div class="inline-compose-footer">
            <button class="btn btn-sm btn-primary" :disabled="sending" @click="$emit('send-mail')">
              <i v-if="sending" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
              Отправить
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="$emit('reset-compose')">Очистить</button>
          </div>
        </div>
      </transition>
    </template>

    <div v-else class="reader-empty">
      <div class="reader-empty-icon"><i class="fas fa-envelope-open"></i></div>
      <p>Выберите письмо для чтения</p>
    </div>
  </main>
</template>

<script>
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

export default {
  name: 'MailReader',
  directives: { 'click-outside': vClickOutside },
  props: {
    selectedMessage: { type: Object, default: null },
    selectedMessageIndex: { type: Number, default: -1 },
    filteredMessages: { type: Array, default: () => [] },
    selectedMailbox: { type: Object, default: null },
    movingMessage: Boolean,
    loadingMessages: Boolean,
    loadingMessageBody: Boolean,
    actionsOpen: Boolean,
    connectLabel: { type: String, default: '' },
    displayBody: { type: Object, default: () => ({ body_html: '', body_text: '' }) },
    sanitizedBody: { type: String, default: '' },
    formattedPlainText: { type: String, default: '' },
    inlineComposeOpen: Boolean,
    composeMode: { type: String, default: 'new' },
    composeForm: { type: Object, required: true },
    sending: Boolean,
    // helper functions
    getInitials: { type: Function, required: true },
    getSenderName: { type: Function, required: true },
    getSenderEmail: { type: Function, required: true },
    formatDate: { type: Function, required: true },
    formatDateFull: { type: Function, required: true },
    formatFileSize: { type: Function, required: true },
    attachmentTypeClass: { type: Function, required: true },
    attachmentIconClass: { type: Function, required: true }
  },
  emits: [
    'update:actionsOpen', 'update:composeForm',
    'reply', 'forward', 'move', 'reload', 'open-app-password',
    'connect-mailbox', 'export-mailbox', 'confirm-delete',
    'download-attachment', 'close-inline-compose', 'send-mail', 'reset-compose'
  ],
  setup(props, { emit }) {
    const updateField = (key, value) => {
      emit('update:composeForm', { ...props.composeForm, [key]: value })
    }
    return { updateField }
  }
}
</script>

<style scoped>
.mail-reader-pane {
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

.reader-toolbar {
  height: 64px;
  flex: 0 0 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--mail-slate-100, #f1f5f9);
  background: #fff;
}
.reader-actions-left,
.reader-actions-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.reader-divider {
  width: 1px;
  height: 24px;
  margin: 0 8px;
  background: var(--mail-slate-200, #e2e8f0);
}
.reader-counter {
  margin-right: 10px;
  color: var(--mail-slate-400, #94a3b8);
  font-size: 12px;
  font-weight: 700;
}

.reader-action {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--mail-slate-400, #94a3b8);
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}
.reader-action:hover:not(:disabled) {
  background: var(--mail-slate-100, #f1f5f9);
  color: var(--mail-slate-700, #334155);
}
.reader-action:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.dropdown { position: relative; }
.actions-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 80;
  min-width: 210px;
  padding: 7px;
  border: 1px solid var(--mail-slate-200, #e2e8f0);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 45px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(14px);
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: none;
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
  color: var(--mail-slate-700, #334155);
  transition: background .1s ease;
  font-size: 14px;
}
.dropdown-item:hover { background: var(--mail-slate-100, #f1f5f9); }
.dropdown-item.text-danger { color: var(--color-danger, #dc2626); }
.dropdown-item.text-danger:hover { background: rgba(255,59,48,.1); }
.dropdown-divider {
  height: 1px;
  background: var(--mail-slate-200, #e2e8f0);
  margin: 4px 0;
}

.reader-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
}

.reader-inner {
  width: min(100%, 960px);
  margin: 0 auto;
  padding: 32px 40px 36px;
}

.reader-header { margin-bottom: 32px; }
.reader-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}
.reader-title-row h1 {
  margin: 0;
  color: var(--mail-slate-900, #0f172a);
  font-size: clamp(20px, 2vw, 28px);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.reader-labels {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.reader-labels span {
  padding: 4px 9px;
  border-radius: 999px;
  background: var(--mail-slate-100, #f1f5f9);
  color: var(--mail-slate-600, #475569);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.sender-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.avatar-sm,
.quick-avatar {
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--mail-slate-100, #f1f5f9);
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 0 0 2px #fff;
}

.sender-main {
  min-width: 0;
  flex: 1;
}
.sender-line {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 7px;
}
.sender-line strong {
  min-width: 0;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--mail-slate-900, #0f172a);
  font-size: 14px;
}
.sender-line span,
.sender-to,
.sender-date span {
  color: var(--mail-slate-500, #64748b);
  font-size: 12px;
}
.sender-line span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sender-to { margin-top: 3px; }
.sender-to span { color: var(--mail-slate-600, #475569); }
.sender-date {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  text-align: right;
}
.sender-date strong {
  color: var(--mail-slate-900, #0f172a);
  font-size: 13px;
}

.attachment-section {
  margin-bottom: 34px;
  padding: 16px;
  border: 1px solid var(--mail-slate-100, #f1f5f9);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.58);
}
.attachment-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  padding: 0 4px;
  color: var(--mail-slate-400, #94a3b8);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.attachment-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.attachment-card {
  max-width: 280px;
  min-width: 210px;
  height: 66px;
  padding: 10px 14px 10px 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--mail-slate-200, #e2e8f0);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.14s ease, box-shadow 0.14s ease, transform 0.14s ease;
}
.attachment-card:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}
.attachment-card:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.attachment-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  background: var(--mail-slate-100, #f1f5f9);
  color: var(--mail-slate-500, #64748b);
  font-size: 18px;
}
.attachment-icon.type-pdf { background: #fef2f2; color: #ef4444; }
.attachment-icon.type-image { background: #eff6ff; color: #3b82f6; }
.attachment-icon.type-sheet { background: #ecfdf5; color: #10b981; }
.attachment-icon.type-archive { background: #fff7ed; color: #f97316; }
.attachment-icon.type-link { background: #eef2ff; color: #4f46e5; }
.attachment-icon.type-blocked { background: #f1f5f9; color: #64748b; }

.attachment-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.attachment-info strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--mail-slate-900, #0f172a);
  font-size: 12px;
  font-weight: 800;
}
.attachment-info small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--mail-slate-400, #94a3b8);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.reader-body {
  color: var(--mail-slate-700, #334155);
  font-size: 15px;
  line-height: 1.65;
}
.body-loading {
  font-size: 12px;
  color: var(--mail-slate-500, #64748b);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.text-muted { color: var(--mail-slate-500, #64748b) !important; }

.message-html,
.message-text {
  max-width: 100%;
  color: var(--mail-slate-700, #334155);
  font-size: 15px;
  line-height: 1.65;
  overflow-wrap: normal;
  word-break: normal;
}
.message-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.message-html :deep(img) { max-width: 100%; height: auto; border-radius: 6px; }
.message-html :deep(*) { max-width: 100%; }
.message-html :deep(p) { margin: 0 0 0.75em 0; }
.message-html :deep(a) {
  color: var(--mail-blue, #2563eb);
  text-decoration: underline;
  text-decoration-style: dotted;
  text-underline-offset: 2px;
}
.message-html :deep(a:hover) { text-decoration-style: solid; }
.message-html :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 12px;
  border-left: 3px solid var(--mail-slate-200, #e2e8f0);
  color: var(--mail-slate-500, #64748b);
  background: var(--mail-slate-100, #f1f5f9);
  border-radius: 0 8px 8px 0;
  font-size: 13px;
}
.message-html :deep(blockquote blockquote) {
  border-left-color: var(--mail-blue, #2563eb);
  opacity: 0.85;
}
.message-html :deep(hr) {
  border: none;
  border-top: 1px solid var(--mail-slate-200, #e2e8f0);
  margin: 16px 0;
}
.message-html :deep(table) {
  border-collapse: initial;
  max-width: 100%;
  display: table;
}
.message-html :deep(td),
.message-html :deep(th) {
  padding: initial;
  border: none;
  vertical-align: top;
}
.message-html :deep(th) {
  background: initial;
  font-weight: 600;
}
.message-html :deep(ul),
.message-html :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}
.message-html :deep(li) { margin-bottom: 4px; }
.message-html :deep(h1),
.message-html :deep(h2),
.message-html :deep(h3),
.message-html :deep(h4) {
  margin: 16px 0 8px 0;
  line-height: 1.3;
  color: var(--mail-slate-900, #0f172a);
}
.message-html :deep(pre) {
  background: var(--mail-slate-100, #f1f5f9);
  padding: 10px 12px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
}

.message-plain-formatted { font-size: 14px; line-height: 1.6; }
.message-plain-formatted :deep(.quoted-text) {
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 3px solid var(--mail-blue, #2563eb);
  color: var(--mail-slate-500, #64748b);
  background: var(--mail-slate-100, #f1f5f9);
  border-radius: 0 8px 8px 0;
  font-size: 13px;
}
.message-plain-formatted :deep(hr) {
  border: none;
  border-top: 1px solid var(--mail-slate-200, #e2e8f0);
  margin: 12px 0;
}

.quick-reply {
  margin-top: 48px;
  padding-top: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-top: 1px solid var(--mail-slate-100, #f1f5f9);
  cursor: text;
}
.quick-avatar {
  width: 32px;
  height: 32px;
  flex-basis: 32px;
  opacity: 0.62;
  font-size: 10px;
}
.quick-input {
  flex: 1;
  min-height: 38px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border: 1px solid var(--mail-slate-100, #f1f5f9);
  border-radius: 999px;
  background: var(--mail-slate-50, #f8fafc);
  color: var(--mail-slate-400, #94a3b8);
  font-size: 13px;
  transition: background 0.14s ease;
}
.quick-reply:hover .quick-input { background: var(--mail-slate-100, #f1f5f9); }

.reader-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: var(--mail-slate-300, #cbd5e1);
}
.reader-empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--mail-slate-50, #f8fafc);
  font-size: 34px;
}
.reader-empty p {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
}

.inline-compose {
  flex: 0 0 auto;
  padding: 14px 24px 16px;
  border-top: 1px solid var(--mail-slate-100, #f1f5f9);
  background: rgba(255, 255, 255, 0.96);
}
.inline-compose-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--mail-slate-700, #334155);
}
.inline-compose-fields {
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.inline-field {
  display: flex;
  align-items: center;
  gap: 8px;
}
.inline-field label {
  font-size: 12px;
  font-weight: 500;
  color: var(--mail-slate-500, #64748b);
  width: 40px;
  flex-shrink: 0;
}
.inline-field input { flex: 1; }
.inline-textarea { resize: none; }
.inline-compose-footer {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.fw-600 { font-weight: 600; }

.dropdown-fade-enter-active, .dropdown-fade-leave-active { transition: all .15s ease; }
.dropdown-fade-enter-from, .dropdown-fade-leave-to { opacity: 0; transform: translateY(-6px) scale(.97); }

.slide-up-enter-active, .slide-up-leave-active { transition: all .2s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(12px); }

@media (max-width: 1280px) {
  .reader-inner { padding-inline: 28px; }
}

@media (max-width: 640px) {
  .reader-toolbar { padding-inline: 12px; }
  .reader-actions-left .muted,
  .reader-divider,
  .reader-counter { display: none; }
  .reader-inner { padding: 22px 16px 28px; }
  .reader-title-row,
  .sender-card {
    flex-direction: column;
    align-items: flex-start;
  }
  .sender-date {
    align-items: flex-start;
    text-align: left;
  }
  .attachment-card {
    max-width: none;
    width: 100%;
  }
}
</style>
