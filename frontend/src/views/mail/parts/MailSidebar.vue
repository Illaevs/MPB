<template>
  <aside class="mail-folders-pane">
    <div class="mailbox-dropdown" v-click-outside="() => $emit('update:mailboxDropdownOpen', false)">
      <button class="mailbox-trigger" @click="$emit('update:mailboxDropdownOpen', !mailboxDropdownOpen)">
        <template v-if="selectedMailbox">
          <span class="trigger-dot" :class="statusDotClass(selectedMailbox.status)"></span>
          <div class="trigger-info">
            <span class="trigger-name">{{ selectedMailbox.name }}</span>
            <span class="trigger-email">{{ selectedMailbox.email }}</span>
          </div>
        </template>
        <template v-else>
          <i class="fas fa-inbox"></i>
          <span class="trigger-name">Выберите ящик</span>
        </template>
        <i class="fas fa-chevron-down trigger-chevron" :class="{ rotated: mailboxDropdownOpen }"></i>
      </button>

      <transition name="dropdown-fade">
        <div v-if="mailboxDropdownOpen" class="mailbox-dropdown-menu">
          <div v-if="loadingMailboxes" class="dropdown-empty">
            <i class="fas fa-spinner fa-spin"></i> Загрузка...
          </div>
          <template v-else>
            <button
              v-for="box in mailboxes"
              :key="box.id"
              class="mailbox-option"
              :class="{ active: selectedMailboxId === box.id }"
              @click="onSelectMailbox(box.id)"
            >
              <span class="option-dot" :class="statusDotClass(box.status)"></span>
              <div class="option-info">
                <span class="option-name">{{ box.name }}</span>
                <span class="option-email">{{ box.email }}</span>
              </div>
            </button>

            <div v-if="!mailboxes.length" class="dropdown-empty">Нет почтовых ящиков</div>
            <div class="dropdown-divider"></div>

            <button v-if="!showCreate" class="mailbox-option create-option" @click.stop="$emit('update:showCreate', true)">
              <i class="fas fa-plus"></i>
              <span>Добавить ящик</span>
            </button>
            <div v-else class="dropdown-create" @click.stop>
              <input :value="createForm.name" @input="updateCreateForm('name', $event.target.value)" class="form-control form-control-sm" placeholder="Название">
              <input :value="createForm.email" @input="updateCreateForm('email', $event.target.value)" class="form-control form-control-sm" placeholder="email@company.ru" type="email">
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-primary flex-grow-1" :disabled="creating" @click="$emit('create-mailbox')">
                  <i v-if="creating" class="fas fa-spinner fa-spin"></i>
                  Создать
                </button>
                <button class="btn btn-sm btn-outline-secondary" @click="$emit('reset-create')">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </template>
        </div>
      </transition>
    </div>

    <button class="compose-primary" @click="$emit('open-new-compose')" :disabled="!selectedMailbox">
      <i class="fas fa-plus"></i>
      <span>Написать</span>
    </button>

    <nav class="folder-list">
      <button
        v-for="folder in mailFolders"
        :key="folder.id"
        class="folder-item"
        :class="{ active: selectedFolder === folder.id }"
        @click="$emit('select-folder', folder.id)"
      >
        <span><i class="fas" :class="folder.icon"></i> {{ folder.label }}</span>
        <b v-if="folder.count">{{ folder.count }}</b>
      </button>
    </nav>

    <div class="mail-sidebar-separator"></div>

    <div class="mail-labels">
      <h3>Метки</h3>
      <button><span class="label-dot blue"></span> Работа</button>
      <button><span class="label-dot orange"></span> Финансы</button>
      <button><span class="label-dot violet"></span> Проекты</button>
    </div>
  </aside>
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
  name: 'MailSidebar',
  directives: { 'click-outside': vClickOutside },
  props: {
    mailboxes: { type: Array, required: true },
    selectedMailbox: { type: Object, default: null },
    selectedMailboxId: { type: [String, Number], default: null },
    mailFolders: { type: Array, required: true },
    selectedFolder: { type: String, required: true },
    loadingMailboxes: Boolean,
    mailboxDropdownOpen: Boolean,
    showCreate: Boolean,
    creating: Boolean,
    createForm: { type: Object, required: true },
    statusDotClass: { type: Function, required: true }
  },
  emits: [
    'update:mailboxDropdownOpen',
    'update:showCreate',
    'update:createForm',
    'select-mailbox',
    'select-folder',
    'open-new-compose',
    'create-mailbox',
    'reset-create'
  ],
  setup(props, { emit }) {
    const onSelectMailbox = (id) => {
      emit('select-mailbox', id)
      emit('update:mailboxDropdownOpen', false)
    }
    const updateCreateForm = (key, value) => {
      emit('update:createForm', { ...props.createForm, [key]: value })
    }
    return { onSelectMailbox, updateCreateForm }
  }
}
</script>

<style scoped>
.mail-folders-pane {
  width: 256px;
  flex: 0 0 256px;
  min-width: 0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  border-right: 1px solid var(--mail-slate-200, #e2e8f0);
  background: rgba(255, 255, 255, 0.52);
}

.mailbox-dropdown { position: relative; }

.mailbox-trigger {
  width: 100%;
  min-width: 0;
  height: 42px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--mail-slate-700, #334155);
  box-shadow: none;
  cursor: pointer;
  transition: background .14s ease;
}
.mailbox-trigger:hover { background: rgba(255, 255, 255, 0.78); }

.trigger-dot,
.option-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.trigger-info,
.option-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.15;
}

.trigger-name,
.option-name {
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
  color: var(--mail-slate-700, #334155);
}

.trigger-email,
.option-email {
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 10.5px;
  color: var(--mail-slate-400, #94a3b8);
}

.trigger-chevron {
  margin-left: auto;
  font-size: 11px;
  color: var(--mail-slate-400, #94a3b8);
  transition: transform 0.16s ease;
}
.trigger-chevron.rotated { transform: rotate(180deg); }

.mailbox-dropdown-menu {
  position: absolute;
  z-index: 60;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  padding: 8px;
  border: 1px solid var(--mail-slate-200, #e2e8f0);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(14px);
}

.mailbox-option {
  width: 100%;
  min-height: 40px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--mail-slate-700, #334155);
  text-align: left;
  cursor: pointer;
  transition: background .1s ease;
}
.mailbox-option:hover,
.mailbox-option.active {
  background: var(--mail-slate-100, #f1f5f9);
}

.create-option {
  color: var(--mail-blue, #2563eb);
  font-weight: 500;
}
.create-option i { width: 16px; text-align: center; }

.dropdown-create {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 2px 2px;
}

.dropdown-empty {
  padding: 10px;
  font-size: 12px;
  text-align: center;
  color: var(--mail-slate-500, #64748b);
}

.dropdown-divider {
  height: 1px;
  margin: 6px 0;
  background: var(--mail-slate-200, #e2e8f0);
}

.compose-primary {
  width: 100%;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 9px;
  padding: 0 14px;
  border: none;
  border-radius: 10px;
  background: var(--mail-blue, #2563eb);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
  transition: transform 0.14s ease, background 0.14s ease, box-shadow 0.14s ease;
}
.compose-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  background: var(--mail-blue-hover, #1d4ed8);
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.26);
}
.compose-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.folder-item {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--mail-slate-500, #64748b);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease, border-color 0.14s ease;
}
.folder-item span:first-child {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.folder-item i {
  width: 18px;
  text-align: center;
  color: var(--mail-slate-400, #94a3b8);
}
.folder-item b {
  min-width: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--mail-slate-200, #e2e8f0);
  color: var(--mail-slate-600, #475569);
  font-size: 10px;
  line-height: 1.25;
  text-align: center;
}
.folder-item:hover {
  background: rgba(255, 255, 255, 0.62);
  color: var(--mail-slate-900, #0f172a);
}
.folder-item.active {
  border-color: rgba(226, 232, 240, 0.75);
  background: rgba(255, 255, 255, 0.92);
  color: var(--mail-blue, #2563eb);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}
.folder-item.active i { color: var(--mail-blue, #2563eb); }
.folder-item.active b {
  background: var(--mail-blue, #2563eb);
  color: #fff;
}

.mail-sidebar-separator {
  height: 1px;
  margin: 6px 2px 0;
  background: var(--mail-slate-200, #e2e8f0);
}

.mail-labels { padding: 0 8px; }
.mail-labels h3 {
  margin: 0 0 10px;
  color: var(--mail-slate-400, #94a3b8);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.mail-labels button {
  width: 100%;
  height: 28px;
  display: flex;
  align-items: center;
  gap: 11px;
  border: none;
  background: transparent;
  color: var(--mail-slate-500, #64748b);
  font-size: 12px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.label-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}
.label-dot.blue { background: #60a5fa; }
.label-dot.orange { background: #fb923c; }
.label-dot.violet { background: #a78bfa; }

/* dropdown transition */
.dropdown-fade-enter-active, .dropdown-fade-leave-active { transition: all .15s ease; }
.dropdown-fade-enter-from, .dropdown-fade-leave-to { opacity: 0; transform: translateY(-6px) scale(.97); }

/* status dots */
.dot-success { background: var(--color-success, #16a34a); }
.dot-warning { background: var(--color-warning, #f59e0b); }
.dot-danger { background: var(--color-danger, #dc2626); }
.dot-muted { background: var(--mail-slate-400, #94a3b8); }

@media (max-width: 980px) {
  .mail-folders-pane {
    width: 100%;
    flex: 0 0 auto;
    flex-direction: row;
    align-items: center;
    overflow-x: auto;
    border-right: none;
    border-bottom: 1px solid var(--mail-slate-200, #e2e8f0);
  }
  .mail-sidebar-separator,
  .mail-labels { display: none; }
  .folder-list {
    flex: 1;
    flex-direction: row;
    overflow-x: auto;
  }
  .folder-item {
    width: auto;
    flex: 0 0 auto;
  }
  .mailbox-trigger { min-width: 190px; }
  .compose-primary {
    width: auto;
    flex: 0 0 auto;
  }
}

@media (max-width: 640px) {
  .mail-folders-pane { padding: 10px; }
}
</style>
