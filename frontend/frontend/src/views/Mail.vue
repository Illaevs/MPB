<template>
  <div class="mail-view mail-design" @keydown="handleKeydown" tabindex="0" ref="mailViewRef">
    <MailSidebar
      :mailboxes="mailboxes"
      :selected-mailbox="selectedMailbox"
      :selected-mailbox-id="selectedMailboxId"
      :mail-folders="mailFolders"
      :selected-folder="selectedFolder"
      :loading-mailboxes="loadingMailboxes"
      :mailbox-dropdown-open="mailboxDropdownOpen"
      :show-create="showCreate"
      :creating="creating"
      :create-form="createForm"
      :status-dot-class="statusDotClass"
      @update:mailbox-dropdown-open="mailboxDropdownOpen = $event"
      @update:show-create="showCreate = $event"
      @update:create-form="createForm = $event"
      @select-mailbox="selectMailbox"
      @select-folder="selectFolder"
      @open-new-compose="openNewCompose"
      @create-mailbox="createMailbox"
      @reset-create="resetCreate"
    />

    <MailList
      :selected-mailbox="selectedMailbox"
      :filtered-messages="filteredMessages"
      :selected-message-id="selectedMessageId"
      :focused-message-index="focusedMessageIndex"
      :loading-messages="loadingMessages"
      :loading-more-messages="loadingMoreMessages"
      :has-more-messages="hasMoreMessages"
      :message-total="messageTotal"
      :search-input="searchInput"
      :search-query="searchQuery"
      :search-focused="searchFocused"
      :avatar-color="avatarColor"
      :get-sender-email="getSenderEmail"
      :get-sender-name="getSenderName"
      :get-initials="getInitials"
      :format-date="formatDate"
      :message-refs-list="messageRefs"
      @update:search-input="searchInput = $event"
      @update:search-focused="searchFocused = $event"
      @update:mobile-view="mobileView = $event"
      @select-message="selectMessage"
      @load-more="loadMoreMessages"
    />

    <MailReader
      :selected-message="selectedMessage"
      :selected-message-index="selectedMessageIndex"
      :filtered-messages="filteredMessages"
      :selected-mailbox="selectedMailbox"
      :moving-message="movingMessage"
      :loading-messages="loadingMessages"
      :loading-message-body="loadingMessageBody"
      :actions-open="actionsOpen"
      :connect-label="connectLabel"
      :display-body="displayBody"
      :sanitized-body="sanitizedBody"
      :formatted-plain-text="formattedPlainText"
      :inline-compose-open="inlineComposeOpen"
      :compose-mode="composeMode"
      :compose-form="composeForm"
      :sending="sending"
      :get-initials="getInitials"
      :get-sender-name="getSenderName"
      :get-sender-email="getSenderEmail"
      :format-date="formatDate"
      :format-date-full="formatDateFull"
      :format-file-size="formatFileSize"
      :attachment-type-class="attachmentTypeClass"
      :attachment-icon-class="attachmentIconClass"
      @update:actions-open="actionsOpen = $event"
      @update:compose-form="composeForm = $event"
      @reply="replyToMessage"
      @forward="forwardMessage"
      @move="moveSelectedMessage"
      @reload="loadMessages(true)"
      @open-app-password="appPasswordOpen = true"
      @connect-mailbox="connectMailbox"
      @export-mailbox="exportMailbox"
      @confirm-delete="confirmDelete"
      @download-attachment="downloadMailAttachment"
      @close-inline-compose="closeInlineCompose"
      @send-mail="sendMail"
      @reset-compose="resetCompose"
    />

    <MailComposer
      :open="newComposeOpen"
      :compose-form="composeForm"
      :sending="sending"
      @update:open="newComposeOpen = $event"
      @update:compose-form="composeForm = $event"
      @send-mail="sendMail"
      @reset-compose="resetCompose"
    />

    <!-- ── App Password Modal ── -->
    <transition name="modal-fade">
      <div v-if="appPasswordOpen" class="modal-backdrop" @click.self="closeAppPassword">
        <div class="modal-card">
          <div class="modal-header">
            <span class="fw-600"><i class="fas fa-key mr-2"></i> Пароль приложения</span>
            <button class="btn-icon" @click="closeAppPassword"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body-inner">
            <p class="small text-muted mb-3">
              Пароль приложения используется для IMAP/SMTP доступа.
              Получите его в настройках безопасности вашей почты.
            </p>
            <div class="mb-3">
              <label class="small text-muted mb-1">Пароль приложения</label>
              <input
                v-model="appPasswordValue"
                class="form-control"
                type="password"
                placeholder="Введите пароль"
                @keyup.enter="connectMailboxAppPassword"
              >
            </div>
          </div>
          <div class="modal-footer-inner">
            <button class="btn btn-outline-secondary" @click="closeAppPassword">Отмена</button>
            <button class="btn btn-primary" :disabled="connectingAppPassword" @click="connectMailboxAppPassword">
              <i v-if="connectingAppPassword" class="fas fa-spinner fa-spin mr-1"></i>
              Подключить
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ── Delete Confirmation ── -->
    <transition name="modal-fade">
      <div v-if="deleteConfirmOpen" class="modal-backdrop" @click.self="deleteConfirmOpen = false">
        <div class="modal-card modal-card-sm">
          <div class="modal-header">
            <span class="fw-600 text-danger"><i class="fas fa-exclamation-triangle mr-2"></i> Удаление ящика</span>
          </div>
          <div class="modal-body-inner">
            <p>Вы уверены, что хотите удалить ящик <strong>{{ selectedMailbox?.email }}</strong>?</p>
            <p class="small text-muted">Это действие нельзя отменить. Все письма будут удалены.</p>
          </div>
          <div class="modal-footer-inner">
            <button class="btn btn-outline-secondary" @click="deleteConfirmOpen = false">Отмена</button>
            <button class="btn btn-danger" :disabled="deleting" @click="deleteMailbox">
              <i v-if="deleting" class="fas fa-spinner fa-spin mr-1"></i>
              Удалить
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import MailSidebar from './mail/parts/MailSidebar.vue'
import MailList from './mail/parts/MailList.vue'
import MailReader from './mail/parts/MailReader.vue'
import MailComposer from './mail/parts/MailComposer.vue'
import { useMailState } from './mail/composables/useMailState'

/**
 * Mail view (Phase 5 — thin shell).
 *
 * Все состояние и API-вызовы перенесены в композабл useMailState.
 * Этот файл оставляет роутером импортируемый компонент по прежнему пути
 * (frontend/src/views/Mail.vue), но превращает его в композицию из
 * MailSidebar / MailList / MailReader / MailComposer.
 *
 * axios.* миграция: все обращения теперь идут через api.mail.* (см. композабл).
 */
export default {
  name: 'Mail',
  components: { MailSidebar, MailList, MailReader, MailComposer },
  setup() {
    return useMailState()
  }
}
</script>

<style scoped>
.mail-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  outline: none;
  padding: 8px;
  gap: 8px;
}

.mail-view.mail-design {
  --mail-blue: #2563eb;
  --mail-blue-hover: #1d4ed8;
  --mail-blue-soft: #eff6ff;
  --mail-slate-25: #fbfdff;
  --mail-slate-50: #f8fafc;
  --mail-slate-100: #f1f5f9;
  --mail-slate-200: #e2e8f0;
  --mail-slate-300: #cbd5e1;
  --mail-slate-400: #94a3b8;
  --mail-slate-500: #64748b;
  --mail-slate-600: #475569;
  --mail-slate-700: #334155;
  --mail-slate-900: #0f172a;
  width: 100%;
  height: 100%;
  min-height: 0;
  padding: 0;
  gap: 0;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  border-radius: 24px;
  background: var(--mail-slate-50);
  color: var(--mail-slate-900);
  font-family: Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  box-shadow: var(--shadow-glass);
}

/* ── Modals shared (app password + delete confirm) ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.25);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
}
.modal-card {
  width: 440px;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--mail-slate-200);
  border-radius: 20px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
  overflow: hidden;
}
.modal-card-sm { width: 380px; }
.modal-header {
  padding: 16px;
  border-bottom: 1px solid var(--mail-slate-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.modal-body-inner { padding: 16px; }
.modal-footer-inner {
  padding: 12px 16px;
  border-top: 1px solid var(--mail-slate-200);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--mail-slate-200);
  background: transparent;
  cursor: pointer;
  color: var(--mail-slate-500);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .12s ease;
  font-size: 12px;
}
.btn-icon:hover {
  background: var(--mail-slate-100);
  color: var(--mail-slate-700);
}

.btn-danger {
  background: var(--color-danger, #dc2626);
  border-color: var(--color-danger, #dc2626);
  color: #fff;
}
.btn-danger:hover { filter: brightness(.9); }

.fw-600 { font-weight: 600; }
.text-danger { color: var(--color-danger, #dc2626); }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all .2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .modal-card,
.modal-fade-leave-to .modal-card { transform: scale(.95); }

button:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 2px solid var(--mail-blue);
  outline-offset: 2px;
}

@media (max-width: 980px) {
  .mail-view.mail-design {
    flex-direction: column;
  }
}
</style>
