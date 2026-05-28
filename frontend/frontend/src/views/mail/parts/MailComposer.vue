<template>
  <transition name="modal-fade">
    <div v-if="open" class="modal-backdrop" @click.self="$emit('update:open', false)">
      <div class="compose-modal">
        <div class="compose-modal-header">
          <span class="fw-600"><i class="fas fa-pen mr-2"></i> Новое письмо</span>
          <button class="btn-icon" @click="$emit('update:open', false)"><i class="fas fa-times"></i></button>
        </div>
        <div class="compose-modal-body">
          <div class="compose-field">
            <label>Кому</label>
            <input
              :value="composeForm.to"
              @input="updateField('to', $event.target.value)"
              class="form-control form-control-sm"
              placeholder="user@example.com, user2@example.com"
            >
          </div>
          <div class="compose-field">
            <label>Тема</label>
            <input
              :value="composeForm.subject"
              @input="updateField('subject', $event.target.value)"
              class="form-control form-control-sm"
              placeholder="Тема письма"
            >
          </div>
          <div class="compose-field flex-grow-1">
            <label>Сообщение</label>
            <textarea
              :value="composeForm.body"
              @input="updateField('body', $event.target.value)"
              class="form-control form-control-sm compose-textarea"
              placeholder="Текст письма..."
            ></textarea>
          </div>
        </div>
        <div class="compose-modal-footer">
          <button class="btn btn-primary" :disabled="sending" @click="$emit('send-mail')">
            <i v-if="sending" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-paper-plane mr-1"></i>
            Отправить
          </button>
          <button class="btn btn-outline-secondary" @click="$emit('reset-compose')">Очистить</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'MailComposer',
  props: {
    open: Boolean,
    composeForm: { type: Object, required: true },
    sending: Boolean
  },
  emits: ['update:open', 'update:composeForm', 'send-mail', 'reset-compose'],
  setup(props, { emit }) {
    const updateField = (key, value) => {
      emit('update:composeForm', { ...props.composeForm, [key]: value })
    }
    return { updateField }
  }
}
</script>

<style scoped>
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

.compose-modal {
  width: 520px;
  max-width: 95vw;
  max-height: 80vh;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--mail-slate-200, #e2e8f0);
  border-radius: 20px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.compose-modal-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--mail-slate-200, #e2e8f0);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compose-modal-body {
  padding: 16px;
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.compose-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.compose-field label {
  font-size: 12px;
  font-weight: 500;
  color: var(--mail-slate-500, #64748b);
}
.compose-textarea {
  resize: none;
  min-height: 160px;
  flex: 1;
}

.compose-modal-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--mail-slate-200, #e2e8f0);
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--mail-slate-200, #e2e8f0);
  background: transparent;
  cursor: pointer;
  color: var(--mail-slate-500, #64748b);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .12s ease;
  font-size: 12px;
}
.btn-icon:hover {
  background: var(--mail-slate-100, #f1f5f9);
  color: var(--mail-slate-700, #334155);
}

.fw-600 { font-weight: 600; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all .2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .compose-modal,
.modal-fade-leave-to .compose-modal { transform: scale(.95); }
</style>
