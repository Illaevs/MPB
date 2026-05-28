<template>
  <div class="outgoing-v2-shell">
    <!-- Top toolbar (text-formatting acts on focused editable region) -->
    <header class="outgoing-v2-toolbar">
      <div class="outgoing-v2-toolbar__left">
        <!-- Document kind switcher — segmented pills in the top bar -->
        <div class="kind-switcher" role="tablist" aria-label="Тип документа">
          <button
            v-for="kind in DOC_KINDS"
            :key="kind.value"
            type="button"
            class="kind-pill"
            :class="{ 'kind-pill--active': documentKind === kind.value }"
            :title="kind.label"
            role="tab"
            :aria-selected="documentKind === kind.value"
            @click="setDocumentKind(kind.value)"
          >
            <i :class="kind.icon"></i>
            <span>{{ kind.label }}</span>
          </button>
        </div>
      </div>
      <div class="outgoing-v2-toolbar__right">
        <!-- Скачать DOCX (direct) -->
        <button
          type="button"
          class="tlb-btn tlb-btn--ghost tlb-btn--label"
          title="Скачать DOCX"
          @click="downloadAs('docx')"
        >
          <i class="far fa-file-word"></i>
          <span>Скачать DOCX</span>
        </button>

        <!-- Создать версию (direct) -->
        <button
          type="button"
          class="tlb-btn tlb-btn--ghost tlb-btn--label"
          title="Сохранить как новую версию"
          @click="createVersion"
        >
          <i class="fas fa-code-branch"></i>
          <span>Версия</span>
        </button>

        <!-- Versions popover -->
        <div class="popover-wrap" v-click-outside="() => versionsOpen = false">
          <button
            type="button"
            class="tlb-btn tlb-btn--ghost"
            :class="{ 'tlb-btn--has-badge': versions.length > 0 }"
            title="Версии"
            @click="togglePopover('versions')"
          >
            <i class="fas fa-clock-rotate-left"></i>
            <span v-if="versions.length" class="tlb-btn__badge">{{ versions.length }}</span>
          </button>
          <transition name="pop">
            <div v-if="versionsOpen" class="side-popover">
              <header class="side-popover__head">
                <div>
                  <span class="side-popover__eyebrow">История</span>
                  <h4>Версии документа</h4>
                </div>
                <button type="button" class="tlb-btn" @click="versionsOpen = false">
                  <i class="fas fa-times"></i>
                </button>
              </header>

              <div v-if="!versions.length" class="side-popover__empty">
                Версий ещё нет. Создавайте снимки документа в важные моменты — кнопка <i class="fas fa-code-branch"></i> рядом.
              </div>
              <ol v-else class="version-list">
                <li v-for="(v, idx) in versions" :key="v.id" class="version-list__item">
                  <div class="version-list__num">v{{ versions.length - idx }}</div>
                  <div class="version-list__body">
                    <div class="version-list__meta">
                      <span class="version-list__author">{{ v.author }}</span>
                      <span class="version-list__time">· {{ formatRelative(v.created_at) }}</span>
                    </div>
                    <div v-if="v.comment" class="version-list__comment">{{ v.comment }}</div>
                  </div>
                  <div class="version-list__actions">
                    <button class="ver-dl ver-dl--word" title="Скачать DOCX" @click="downloadVersion(v, 'docx')">
                      <i class="fas fa-file-word"></i>
                    </button>
                    <button class="ver-dl ver-dl--pdf" title="Скачать PDF" @click="downloadVersion(v, 'pdf')">
                      <i class="fas fa-file-pdf"></i>
                    </button>
                  </div>
                </li>
              </ol>
            </div>
          </transition>
        </div>

        <!-- Attachments popover -->
        <div class="popover-wrap" v-click-outside="() => attachmentsOpen = false">
          <button
            type="button"
            class="tlb-btn tlb-btn--ghost"
            :class="{ 'tlb-btn--has-badge': attachments.length > 0 }"
            title="Приложения"
            @click="togglePopover('attachments')"
          >
            <i class="fas fa-paperclip"></i>
            <span v-if="attachments.length" class="tlb-btn__badge">{{ attachments.length }}</span>
          </button>
          <transition name="pop">
            <div v-if="attachmentsOpen" class="side-popover">
              <header class="side-popover__head">
                <div>
                  <span class="side-popover__eyebrow">Файлы</span>
                  <h4>Приложения</h4>
                </div>
                <button type="button" class="tlb-btn" @click="attachmentsOpen = false">
                  <i class="fas fa-times"></i>
                </button>
              </header>

              <div class="attachment-uploader" @drop.prevent="onDropFiles" @dragover.prevent>
                <input
                  ref="fileInputRef"
                  type="file"
                  multiple
                  hidden
                  @change="onPickFiles"
                />
                <button class="tlb-btn tlb-btn--primary" @click="$refs.fileInputRef.click()">
                  <i class="fas fa-plus mr-1"></i> Добавить файлы
                </button>
                <span class="attachment-uploader__hint">или перетащите сюда</span>
              </div>

              <div v-if="!attachments.length" class="side-popover__empty">
                Пока без приложений.
              </div>
              <ul v-else class="attachment-list">
                <li v-for="f in attachments" :key="f.id" class="attachment-list__item">
                  <i :class="fileIcon(f.name)" class="attachment-list__icon"></i>
                  <div class="attachment-list__body">
                    <div class="attachment-list__name" :title="f.name">{{ f.name }}</div>
                    <div class="attachment-list__meta">{{ formatBytes(f.size) }}</div>
                  </div>
                  <button class="tlb-btn" title="Скачать">
                    <i class="fas fa-download"></i>
                  </button>
                  <button class="tlb-btn" title="Удалить" @click="removeAttachment(f.id)">
                    <i class="fas fa-times"></i>
                  </button>
                </li>
              </ul>
            </div>
          </transition>
        </div>

        <div class="tlb-sep"></div>

        <!-- Status pill — visible at all times, click to change -->
        <div class="status-wrap" v-click-outside="() => statusOpen = false">
          <button
            type="button"
            class="status-pill"
            :class="`status-pill--${docStatus.key}`"
            @click="togglePopover('status')"
          >
            <span class="status-pill__dot"></span>
            <span>{{ docStatus.label }}</span>
            <i class="fas fa-caret-down"></i>
          </button>
          <transition name="pop">
            <div v-if="statusOpen" class="status-menu">
              <button
                v-for="opt in DOC_STATUSES"
                :key="opt.key"
                type="button"
                class="status-menu__item"
                :class="`status-menu__item--${opt.key}`"
                @click="setStatus(opt.key)"
              >
                <span class="status-pill__dot"></span>
                <span>{{ opt.label }}</span>
                <i v-if="docStatus.key === opt.key" class="fas fa-check ml-auto"></i>
              </button>
            </div>
          </transition>
        </div>

        <!-- Approval — popover stepper -->
        <div class="approval-wrap" v-click-outside="() => approvalOpen = false">
          <button
            type="button"
            class="tlb-btn approval-btn"
            :class="{ 'approval-btn--active': approvalActive }"
            title="Согласование"
            @click="togglePopover('approval')"
          >
            <i class="fas fa-clipboard-check"></i>
            <span class="hide-sm">Согласование</span>
            <span v-if="approvalActive" class="approval-btn__badge">
              {{ currentApprovalStepNumber }}/{{ approvalSteps.length }}
            </span>
          </button>
          <transition name="pop">
            <div v-if="approvalOpen" class="approval-popover">
              <header class="approval-popover__head">
                <div>
                  <span class="approval-popover__eyebrow">Маршрут</span>
                  <h4>Согласование документа</h4>
                </div>
                <button
                  type="button"
                  class="tlb-btn"
                  title="Закрыть"
                  @click="approvalOpen = false"
                ><i class="fas fa-times"></i></button>
              </header>

              <div v-if="!approvalActive" class="approval-popover__empty">
                <p>Согласование ещё не запущено.</p>
                <button class="tlb-btn tlb-btn--primary" @click="startApproval">
                  <i class="fas fa-play mr-1"></i> Запустить согласование
                </button>
              </div>

              <ol v-else class="approval-stepper">
                <li
                  v-for="(step, idx) in approvalSteps"
                  :key="step.id"
                  class="approval-stepper__item"
                  :class="[
                    `approval-stepper__item--${step.status}`,
                    { 'approval-stepper__item--current': idx === currentApprovalStepIndex }
                  ]"
                >
                  <span class="approval-stepper__index">
                    <i v-if="step.status === 'approved'" class="fas fa-check"></i>
                    <i v-else-if="step.status === 'rejected'" class="fas fa-times"></i>
                    <span v-else>{{ idx + 1 }}</span>
                  </span>
                  <div class="approval-stepper__body">
                    <div class="approval-stepper__name">{{ step.user.full_name }}</div>
                    <div class="approval-stepper__meta">
                      <span class="approval-stepper__role">{{ step.role }}</span>
                      <span v-if="step.acted_at" class="approval-stepper__time">· {{ formatRelative(step.acted_at) }}</span>
                    </div>
                    <p v-if="step.comment" class="approval-stepper__comment">{{ step.comment }}</p>
                  </div>
                </li>
              </ol>

              <footer v-if="approvalActive" class="approval-popover__foot">
                <button class="tlb-btn" @click="resetApproval">
                  <i class="fas fa-rotate-left mr-1"></i> Сбросить
                </button>
              </footer>
            </div>
          </transition>
        </div>

        <button class="tlb-btn tlb-btn--primary" :disabled="saving || !documentId" @click="saveDraft">
          <i class="fas mr-1" :class="saving ? 'fa-spinner fa-spin' : 'fa-check'"></i>
          {{ saving ? 'Сохранение…' : 'Сохранить' }}
        </button>
      </div>
    </header>

    <!-- Three-column workspace -->
    <div class="outgoing-v2-body">
      <!-- LEFT: registry (placeholder list for MVP) -->
      <aside class="outgoing-v2-left">
        <header class="outgoing-v2-left__head">
          <span>Реестр</span>
          <button class="tlb-btn tlb-btn--primary" title="Создать"><i class="fas fa-plus"></i></button>
        </header>
        <label class="outgoing-v2-left__search">
          <i class="fas fa-search"></i>
          <input
            type="search"
            placeholder="Поиск по реестру…"
            v-model.trim="searchQuery"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="outgoing-v2-left__search-clear"
            @click="searchQuery = ''"
            title="Очистить"
          >
            <i class="fas fa-times"></i>
          </button>
        </label>
        <div class="outgoing-v2-left__list">
          <div
            v-for="item in filteredRegistryItems"
            :key="item.id"
            class="reg-item"
            :class="{ 'reg-item--active': item.id === activeDocumentId }"
            @click="openDocument(item.id)"
          >
            <div class="reg-item__no">{{ item.no }}</div>
            <div class="reg-item__title">{{ item.title }}</div>
            <span class="reg-item__status" :class="`reg-item__status--${item.status}`">
              {{ DOC_STATUS_LABEL[item.status] || item.status }}
            </span>
          </div>
          <div v-if="registryLoading" class="outgoing-v2-left__empty">
            Загрузка реестра…
          </div>
          <div v-else-if="!filteredRegistryItems.length" class="outgoing-v2-left__empty">
            {{ searchQuery ? 'Ничего не нашлось' : 'Реестр пуст' }}
          </div>
        </div>
      </aside>

      <!-- CENTER: document -->
      <main class="outgoing-v2-center">
        <!-- Formatting toolbar — sits above the page, acts on focused body -->
        <div class="format-bar" role="toolbar" aria-label="Форматирование">
          <button
            class="tlb-btn"
            :disabled="!editorAvailable"
            title="Отменить (Ctrl+Z)"
            @mousedown.prevent
            @click="execCmd('undo')"
          ><i class="fas fa-undo"></i></button>
          <button
            class="tlb-btn"
            :disabled="!editorAvailable"
            title="Повторить (Ctrl+Y)"
            @mousedown.prevent
            @click="execCmd('redo')"
          ><i class="fas fa-redo"></i></button>

          <div class="tlb-sep"></div>

          <select
            class="tlb-select"
            :disabled="!editorAvailable"
            :value="paragraphBlock"
            @mousedown="captureSelection"
            @change="onBlockChange($event.target.value)"
          >
            <option value="p">Текст</option>
            <option value="h2">Заголовок</option>
            <option value="h3">Подзаголовок</option>
            <option value="blockquote">Цитата</option>
            <option value="pre">Код</option>
          </select>

          <div class="tlb-sep"></div>

          <button
            v-for="btn in inlineButtons"
            :key="btn.cmd"
            class="tlb-btn"
            :class="{ 'tlb-btn--active': cmdState[btn.cmd] }"
            :disabled="!editorAvailable"
            :title="btn.title"
            @mousedown.prevent
            @click="execCmd(btn.cmd)"
          ><i :class="btn.icon"></i></button>

          <div class="tlb-sep"></div>

          <button
            v-for="btn in alignButtons"
            :key="btn.cmd"
            class="tlb-btn"
            :class="{ 'tlb-btn--active': cmdState[btn.cmd] }"
            :disabled="!editorAvailable"
            :title="btn.title"
            @mousedown.prevent
            @click="execCmd(btn.cmd)"
          ><i :class="btn.icon"></i></button>

          <div class="tlb-sep"></div>

          <button
            v-for="btn in listButtons"
            :key="btn.cmd"
            class="tlb-btn"
            :class="{ 'tlb-btn--active': cmdState[btn.cmd] }"
            :disabled="!editorAvailable"
            :title="btn.title"
            @mousedown.prevent
            @click="execCmd(btn.cmd)"
          ><i :class="btn.icon"></i></button>

          <button
            class="tlb-btn"
            :disabled="!editorAvailable"
            title="Вставить изображение"
            @mousedown.prevent
            @click="onInsertImage"
          ><i class="fas fa-image"></i></button>
        </div>

        <div v-if="loading" class="outgoing-v2-center__loading">
          <i class="fas fa-spinner fa-spin"></i> Загрузка шаблона…
        </div>
        <div v-else-if="loadError" class="outgoing-v2-center__error">
          {{ loadError }}
        </div>
        <OutgoingTemplateRenderer
          v-else-if="template"
          :layout-html="template.layout_html"
          :placeholder-fields="template.placeholder_fields"
          :field-values="fieldValues"
          :resolved-context="resolvedContext"
          v-model:editable-content="editableContent"
          :active-field-key="activeFieldKey"
          @select-field="onChipSelect"
          @editable-focus="onEditableFocus"
          @editable-blur="onEditableBlur"
        />
      </main>

      <!-- RIGHT: parameters -->
      <OutgoingParametersPanel
        v-if="template"
        :placeholder-fields="template.placeholder_fields"
        v-model:field-values="fieldValues"
        :active-field-key="activeFieldKey"
        :anchors="anchors"
        :deal-options="dealOptions"
        :contract-options="contractOptions"
        :stage-options="stageOptions"
        :payment-options="paymentOptions"
        :recipient-company="recipientCompany"
        :resolving="resolving"
        @focus-field="(k) => activeFieldKey = k"
        @pick-recipient="onRecipientPicked"
        @pick-deal="onDealPicked"
      />
    </div>

    <!-- Version comment modal (replaces native prompt) -->
    <transition name="pop">
      <div
        v-if="versionModalOpen"
        class="ovm-overlay"
        @click.self="cancelVersion"
        @keydown.esc="cancelVersion"
      >
        <div class="ovm" role="dialog" aria-modal="true" aria-labelledby="ovm-title">
          <header class="ovm__head">
            <h3 id="ovm-title" class="ovm__title">Новая версия</h3>
            <button type="button" class="tlb-btn" title="Закрыть" @click="cancelVersion">
              <i class="fas fa-times"></i>
            </button>
          </header>
          <div class="ovm__body">
            <label for="ovm-comment" class="ovm__label">Комментарий к версии</label>
            <textarea
              id="ovm-comment"
              ref="versionCommentInput"
              v-model="versionComment"
              class="ovm__textarea"
              rows="3"
              placeholder="Например: правки от юристов (необязательно)"
              @keydown.ctrl.enter="confirmVersion"
              @keydown.meta.enter="confirmVersion"
            ></textarea>
            <p class="ovm__hint">Ctrl+Enter — сохранить</p>
          </div>
          <footer class="ovm__foot">
            <button type="button" class="tlb-btn tlb-btn--label" @click="cancelVersion">Отмена</button>
            <button type="button" class="tlb-btn tlb-btn--label tlb-btn--primary" @click="confirmVersion">
              <i class="fas fa-code-branch mr-1"></i> Создать версию
            </button>
          </footer>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { computed, onBeforeUnmount, onMounted, reactive, ref, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import OutgoingTemplateRenderer from './outgoing/templateV2/OutgoingTemplateRenderer.vue'
import OutgoingParametersPanel from './outgoing/templateV2/OutgoingParametersPanel.vue'
import { useOutgoingV2Resolve } from './outgoing/templateV2/useOutgoingV2Resolve'
import { get as apiGet } from '../services/api/_client'
import {
  listTemplatesV2,
  getTemplateV2,
  list as apiListDocs,
  getById as apiGetDoc,
  update as apiUpdateDoc,
  createVersion as apiCreateVersion,
  uploadAttachments as apiUploadAttachments,
  editorPreview as apiEditorPreview,
  downloadVersionFile as apiDownloadVersionFile,
} from '../services/api/outgoing'

const V2_SCHEMA_VERSION = 2

const INLINE_BUTTONS = [
  { cmd: 'bold', title: 'Жирный (Ctrl+B)', icon: 'fas fa-bold' },
  { cmd: 'italic', title: 'Курсив (Ctrl+I)', icon: 'fas fa-italic' },
  { cmd: 'underline', title: 'Подчёркнутый (Ctrl+U)', icon: 'fas fa-underline' },
]
const ALIGN_BUTTONS = [
  { cmd: 'justifyLeft', title: 'По левому краю', icon: 'fas fa-align-left' },
  { cmd: 'justifyCenter', title: 'По центру', icon: 'fas fa-align-center' },
  { cmd: 'justifyRight', title: 'По правому краю', icon: 'fas fa-align-right' },
  { cmd: 'justifyFull', title: 'По ширине', icon: 'fas fa-align-justify' },
]
const LIST_BUTTONS = [
  { cmd: 'insertUnorderedList', title: 'Маркированный список', icon: 'fas fa-list-ul' },
  { cmd: 'insertOrderedList', title: 'Нумерованный список', icon: 'fas fa-list-ol' },
]
const STATE_COMMANDS = [
  'bold', 'italic', 'underline',
  'justifyLeft', 'justifyCenter', 'justifyRight', 'justifyFull',
  'insertUnorderedList', 'insertOrderedList',
]
const BLOCK_TAGS = new Set(['p', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre', 'div'])

// Document kinds — match backend `document_kind` enum.
const DOC_KINDS = [
  { value: 'letter',      label: 'Письмо',        icon: 'fas fa-envelope' },
  { value: 'act',         label: 'Акт',           icon: 'fas fa-file-lines' },
  { value: 'upd',         label: 'УПД',           icon: 'fas fa-file-signature' },
  { value: 'invoice',     label: 'Счёт',          icon: 'fas fa-file-invoice' },
  { value: 'vat_invoice', label: 'Счёт-фактура',  icon: 'fas fa-file-invoice-dollar' },
]

// Document statuses — same palette across pill, dropdown, list badge.
const DOC_STATUSES = [
  { key: 'draft',     label: 'Черновик' },
  { key: 'review',    label: 'На согласовании' },
  { key: 'sent',      label: 'Отправлен' },
  { key: 'signed',    label: 'Подписан' },
  { key: 'rejected',  label: 'Отклонён' },
]
const DOC_STATUS_LABEL = Object.fromEntries(DOC_STATUSES.map((s) => [s.key, s.label]))

// Approval pipeline stub — to be replaced with `ApprovalWidget` data once
// the route is hooked into the real document.
const APPROVAL_STUB = [
  { id: 's1', user: { id: 'u1', full_name: 'Анна Кузнецова'  }, role: 'Юрист',          status: 'approved', acted_at: '2026-05-13T14:32:00Z', comment: '' },
  { id: 's2', user: { id: 'u2', full_name: 'Илья Романов'    }, role: 'Финансы',        status: 'approved', acted_at: '2026-05-14T09:12:00Z', comment: '' },
  { id: 's3', user: { id: 'u3', full_name: 'Сергей Петров'   }, role: 'Технический',    status: 'pending',  acted_at: null, comment: '' },
  { id: 's4', user: { id: 'u4', full_name: 'Мария Смирнова'  }, role: 'Финальный',      status: 'pending',  acted_at: null, comment: '' },
]

const formatRelative = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 Б'
  const units = ['Б', 'КБ', 'МБ', 'ГБ']
  let i = 0
  let n = bytes
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++ }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${units[i]}`
}

const fileIcon = (name) => {
  const ext = (name || '').toLowerCase().split('.').pop()
  if (['pdf'].includes(ext)) return 'far fa-file-pdf'
  if (['doc', 'docx'].includes(ext)) return 'far fa-file-word'
  if (['xls', 'xlsx', 'csv'].includes(ext)) return 'far fa-file-excel'
  if (['ppt', 'pptx'].includes(ext)) return 'far fa-file-powerpoint'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'far fa-file-image'
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'far fa-file-zipper'
  return 'far fa-file'
}

// Lightweight click-outside directive (mirrors the one in Calendar/Tasks).
const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

export default {
  name: 'OutgoingRegistryV2',
  components: { OutgoingTemplateRenderer, OutgoingParametersPanel },
  directives: { 'click-outside': clickOutside },
  setup() {
    const route = useRoute()
    const template = ref(null)
    const loading = ref(true)
    const loadError = ref('')
    const fieldValues = ref({})
    const editableContent = ref({})
    const activeFieldKey = ref('')
    const editableFocused = ref(false)

    // -------- Document persistence --------
    // documentId === null  → unsaved scratch (template skeleton, no persistence)
    // documentId === <uuid> → an existing backend document is loaded
    const documentId = ref(route.query.id || null)
    const saving = ref(false)

    // -------- Document kind switcher --------
    const documentKind = ref(route.query.kind || 'letter')

    const kindLabel = (value) => {
      const def = DOC_KINDS.find((k) => k.value === value)
      return def ? def.label : value
    }

    // Load the template_v2 layout for the current kind (optionally a specific
    // template id, e.g. the one stored in a saved draft).
    const loadTemplate = async (templateId = null) => {
      loading.value = true
      loadError.value = ''
      try {
        if (templateId) {
          try {
            template.value = await getTemplateV2(templateId)
            return
          } catch { /* fall through to kind lookup */ }
        }
        const templates = (await listTemplatesV2({ document_kind: documentKind.value })) || []
        if (!templates.length) {
          template.value = null
          loadError.value = `Для типа «${kindLabel(documentKind.value)}» шаблон ещё не настроен.`
          return
        }
        const queryId = route.query.template_id
        const match = queryId ? templates.find((t) => t.id === queryId) : null
        template.value = await getTemplateV2((match || templates[0]).id)
      } catch (e) {
        loadError.value = e?.response?.data?.detail || e.message || 'Не удалось загрузить шаблон'
      } finally {
        loading.value = false
      }
    }

    const setDocumentKind = async (value) => {
      if (documentKind.value === value) return
      documentKind.value = value
      // Switching kind starts a fresh scratch document of that kind.
      documentId.value = null
      fieldValues.value = {}
      editableContent.value = {}
      activeFieldKey.value = ''
      await loadTemplate()
    }

    // ---- Build / parse the v2 editor_draft payload ----
    // `editor_mode` column is enum-locked to {classic,structured} server-side,
    // so the real mode lives INSIDE the draft. We detect v2 by schema_version.
    const buildV2Draft = () => ({
      schema_version: V2_SCHEMA_VERSION,
      mode: 'template_v2',
      template_id: template.value?.id || null,
      document_kind: documentKind.value,
      field_values: { ...fieldValues.value },
      editable_regions: { ...editableContent.value },
    })

    const applyV2Draft = (draft) => {
      documentKind.value = draft.document_kind || documentKind.value
      fieldValues.value = draft.field_values || {}
      editableContent.value = draft.editable_regions || {}
    }

    // -------- Anchors (shared with classic editor via doc columns) --------
    const anchors = {
      recipientCompanyId: ref(''),
      ourCompanyKey: ref(''),
      dealId: ref(''),
      contractId: ref(''),
      bankAccountIndex: ref(null),
      linkedStageIds: ref([]),
      linkedPaymentItems: ref([]),
      recipientEio: ref(''),
      recipientToName: ref(''),
      recipientGenitiveName: ref(''),
      recipientShortName: ref(''),
      recipientAppeal: ref(''),
      recipientSalutation: ref(''),
    }

    // Candidate lists for the anchor pickers (loaded per selected deal).
    const dealOptions = ref([])
    const contractOptions = ref([])
    const stageOptions = ref([])
    const paymentOptions = ref([])
    const recipientCompany = ref(null) // full company for bank_accounts[]

    const loadDeals = async () => {
      try {
        const rows = await apiGet('/api/v1/deals/', { limit: 200 })
        dealOptions.value = (Array.isArray(rows) ? rows : rows?.items || [])
          .map((d) => ({ id: d.id, title: d.title || d.name || d.id }))
      } catch { dealOptions.value = [] }
    }
    const loadDealContext = async (dealId) => {
      contractOptions.value = []
      stageOptions.value = []
      paymentOptions.value = []
      if (!dealId) return
      try {
        const [contracts, stages, payments] = await Promise.all([
          apiGet(`/api/v1/contracts/deal/${dealId}`).catch(() => []),
          apiGet(`/api/v1/stages/deal/${dealId}`).catch(() => []),
          apiGet('/api/v1/income-expense/', { deal_id: dealId, direction: 'income' }).catch(() => []),
        ])
        contractOptions.value = (Array.isArray(contracts) ? contracts : [])
          .map((c) => ({ id: c.id, label: `${c.number || c.contract_number || '—'} от ${c.date || c.contract_date || ''}` }))
        stageOptions.value = (Array.isArray(stages) ? stages : [])
          .filter((s) => s.stage_type !== 'payment')
          .map((s) => ({ id: s.id, name: s.name || s.title || s.id, amount: s.planned_cost ?? s.amount ?? null }))
        const pays = Array.isArray(payments) ? payments : payments?.items || []
        paymentOptions.value = pays.map((p) => ({ id: p.id, amount: p.amount, date: p.date }))
      } catch { /* ignore — anchors still usable */ }
    }
    const loadRecipientCompany = async (companyId) => {
      recipientCompany.value = null
      if (!companyId) return
      try {
        recipientCompany.value = await apiGet(`/api/v1/companies/${companyId}`)
      } catch { /* ignore */ }
    }

    const { resolving, resolvedContext, runResolve } = useOutgoingV2Resolve({
      documentKind, documentId, anchors, fieldValues, editableContent,
    })

    // React to anchor selections that need candidate reloads.
    const onDealPicked = async (id) => {
      anchors.dealId.value = id
      anchors.contractId.value = ''
      anchors.linkedStageIds.value = []
      anchors.linkedPaymentItems.value = []
      await loadDealContext(id)
    }
    const onRecipientPicked = async (id) => {
      anchors.recipientCompanyId.value = id
      anchors.bankAccountIndex.value = null
      await loadRecipientCompany(id)
    }

    const buildAnchorsPayload = () => ({
      recipient_company_id: anchors.recipientCompanyId.value || null,
      our_company_key: anchors.ourCompanyKey.value || null,
      deal_id: anchors.dealId.value || null,
      contract_id: anchors.contractId.value || null,
      bank_account_index: anchors.bankAccountIndex.value,
      linked_stage_ids: anchors.linkedStageIds.value,
      linked_payment_items: anchors.linkedPaymentItems.value,
      recipient_eio: anchors.recipientEio.value || '',
      recipient_to_name: anchors.recipientToName.value || '',
      recipient_genitive_name: anchors.recipientGenitiveName.value || '',
      recipient_short_name: anchors.recipientShortName.value || '',
      recipient_appeal: anchors.recipientAppeal.value || '',
      recipient_salutation: anchors.recipientSalutation.value || '',
    })

    const applyAnchorsFromDoc = (d) => {
      anchors.recipientCompanyId.value = d.recipient_company_id || ''
      anchors.ourCompanyKey.value = d.our_company_key || ''
      anchors.dealId.value = d.deal_id || ''
      anchors.contractId.value = d.contract_id || ''
      anchors.bankAccountIndex.value = d.bank_account_index ?? null
      anchors.linkedStageIds.value = Array.isArray(d.linked_stage_ids) ? d.linked_stage_ids : []
      anchors.linkedPaymentItems.value = Array.isArray(d.linked_payment_items) ? d.linked_payment_items : []
      anchors.recipientEio.value = d.recipient_eio || ''
      anchors.recipientToName.value = d.recipient_to_name || ''
      anchors.recipientGenitiveName.value = d.recipient_genitive_name || ''
      anchors.recipientShortName.value = d.recipient_short_name || ''
      anchors.recipientAppeal.value = d.recipient_appeal || ''
      anchors.recipientSalutation.value = d.recipient_salutation || ''
    }

    const onChipSelect = (fieldKey) => {
      activeFieldKey.value = fieldKey
      nextTick(() => {
        const node = document.querySelector(
          `.params-panel [data-field-key="${CSS.escape(fieldKey)}"] input, ` +
          `.params-panel [data-field-key="${CSS.escape(fieldKey)}"] textarea`
        )
        if (node) node.focus()
      })
    }

    // -------- Toolbar wiring --------
    // We use `document.execCommand` — deprecated but still implemented in
    // every browser we ship to, and the simplest way to drive a contenteditable
    // surface without pulling Tiptap in this MVP. Step 5 of the plan replaces
    // this with Tiptap proper.
    const cmdState = reactive({})
    const paragraphBlock = ref('p')

    // Tracks the most-recently-focused editable DOM node and the last
    // selection range INSIDE it. The toolbar uses these to restore selection
    // before running a command — necessary when the user clicks the
    // <select> dropdown (which natively steals focus from the editor).
    let lastEditableEl = null
    let lastRange = null
    // Reactive flag — true once the user has focused an editable region
    // at least once. Used to enable controls that need selection restore
    // (e.g. the block-format <select>, which loses editor focus natively).
    const editorAvailable = ref(false)

    const isInsideEditable = () => {
      if (!lastEditableEl) return false
      const sel = window.getSelection()
      if (!sel || sel.rangeCount === 0) return lastRange !== null
      return lastEditableEl.contains(sel.anchorNode)
    }

    const refreshCmdState = () => {
      if (!isInsideEditable()) return
      for (const cmd of STATE_COMMANDS) {
        try { cmdState[cmd] = document.queryCommandState(cmd) }
        catch { cmdState[cmd] = false }
      }
      const sel = window.getSelection()
      if (sel && sel.rangeCount) {
        let node = sel.anchorNode
        while (node && node.nodeType === 3) node = node.parentNode
        while (node && !BLOCK_TAGS.has((node.tagName || '').toLowerCase())) {
          node = node.parentNode
          if (!node || node === lastEditableEl) break
        }
        const tag = (node?.tagName || 'p').toLowerCase()
        paragraphBlock.value = BLOCK_TAGS.has(tag) ? tag : 'p'
      }
    }

    const onEditableFocus = (info) => {
      editableFocused.value = true
      lastEditableEl = info?.el || null
      editorAvailable.value = !!lastEditableEl
    }
    const onEditableBlur = () => {
      // Don't clear lastEditableEl on blur — toolbar interactions need it to
      // restore focus + selection.
      editableFocused.value = false
    }

    const restoreFocus = () => {
      if (!lastEditableEl) return false
      lastEditableEl.focus()
      editableFocused.value = true
      if (lastRange) {
        const sel = window.getSelection()
        try {
          sel.removeAllRanges()
          sel.addRange(lastRange)
        } catch {
          // range may be detached — fall back to placing caret at end
          const range = document.createRange()
          range.selectNodeContents(lastEditableEl)
          range.collapse(false)
          sel.removeAllRanges()
          sel.addRange(range)
        }
      }
      return true
    }

    const execCmd = (cmd, value = null) => {
      if (!lastEditableEl) return
      if (!isInsideEditable() || !editableFocused.value) {
        if (!restoreFocus()) return
      }
      try {
        document.execCommand(cmd, false, value)
      } catch (e) {
        // eslint-disable-next-line no-console
        console.warn(`execCommand failed for ${cmd}`, e)
      }
      refreshCmdState()
    }

    const captureSelection = () => {
      // No-op: mousedown handler on <select> kept for symmetry; the actual
      // selection has already been captured by the selectionchange listener.
      refreshCmdState()
    }

    const onBlockChange = (tag) => {
      execCmd('formatBlock', `<${tag}>`)
      paragraphBlock.value = tag
    }

    const onInsertImage = () => {
      const url = window.prompt('URL изображения')
      if (!url) return
      execCmd('insertImage', url)
    }

    // Keep command state + last range in sync as the caret moves.
    const onSelectionChange = () => {
      if (!lastEditableEl) return
      const sel = window.getSelection()
      if (!sel || sel.rangeCount === 0) return
      // Save only if selection is inside the editable region.
      if (lastEditableEl.contains(sel.anchorNode)) {
        try { lastRange = sel.getRangeAt(0).cloneRange() } catch { /* ignore */ }
        refreshCmdState()
      }
    }
    onMounted(() => {
      document.addEventListener('selectionchange', onSelectionChange)
    })
    onBeforeUnmount(() => {
      document.removeEventListener('selectionchange', onSelectionChange)
    })

    const toast = (msg, isErr = false) => {
      // Minimal feedback channel for MVP — replace with the app toast bus later.
      // eslint-disable-next-line no-console
      console[isErr ? 'error' : 'log']('[outgoing-v2]', msg)
    }

    const saveDocument = async () => {
      if (!documentId.value) {
        toast('Документ ещё не создан — сохранение доступно после открытия записи из реестра.', true)
        return
      }
      saving.value = true
      try {
        await apiUpdateDoc(documentId.value, {
          editor_mode: 'classic', // backend enum-locks; real mode in draft
          editor_schema_version: 1,
          editor_draft: buildV2Draft(),
          document_kind: documentKind.value,
          status: documentStatus.value,
          // Anchors → top-level columns: this is what keeps classic ↔ v2 in sync.
          ...buildAnchorsPayload(),
        })
        await loadRegistry()
        toast('Сохранено')
      } catch (e) {
        toast(e?.response?.data?.detail || e.message || 'Не удалось сохранить', true)
      } finally {
        saving.value = false
      }
    }
    // Keep the old name referenced by the template button.
    const saveDraft = saveDocument

    // -------- Download + versions + attachments --------
    const downloadOpen = ref(false)
    const versionsOpen = ref(false)
    const attachmentsOpen = ref(false)
    const versions = ref([])
    const attachments = ref([])

    const triggerBlobDownload = (blob, filename) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    }

    const downloadAs = async (format) => {
      downloadOpen.value = false
      try {
        // Server still renders via the legacy/block pipeline; the v2 layout
        // render path is a separate backend task. We send the resolve payload
        // it expects and stream whatever it returns.
        const payload = {
          document_id: documentId.value || undefined,
          document_kind: documentKind.value,
          editor_mode: 'classic',
          editor_schema_version: 1,
          editor_draft: buildV2Draft(),
        }
        const resp = await apiEditorPreview(format, payload)
        const blob = resp?.data ?? resp
        triggerBlobDownload(blob, `document.${format}`)
      } catch (e) {
        toast(e?.response?.data?.detail || e.message || `Не удалось сформировать ${format.toUpperCase()}`, true)
      }
    }

    const downloadVersion = async (v, format) => {
      if (!documentId.value) return
      try {
        const resp = await apiDownloadVersionFile(documentId.value, v.id, format)
        const blob = resp?.data ?? resp
        const num = v.version_number || ''
        triggerBlobDownload(blob, `version-${num || v.id}.${format}`)
      } catch (e) {
        const detail = e?.response?.data?.detail
        toast(detail || e.message || `Не удалось скачать версию (${format})`, true)
      }
    }

    // Version comment is collected via a custom modal (no native prompt).
    const versionModalOpen = ref(false)
    const versionComment = ref('')
    const versionCommentInput = ref(null)

    const createVersion = () => {
      versionComment.value = ''
      versionModalOpen.value = true
      nextTick(() => { versionCommentInput.value?.focus() })
    }
    const confirmVersion = async () => {
      versionModalOpen.value = false
      if (!documentId.value) {
        toast('Сначала откройте сохранённый документ из реестра.', true)
        return
      }
      try {
        // Persist current draft, then snapshot a version server-side.
        // (Backend re-renders canonical; comment field is a follow-up tweak.)
        await saveDocument()
        await apiCreateVersion(documentId.value)
        await refreshDetail()
        versionsOpen.value = true
        toast('Версия создана')
      } catch (e) {
        toast(e?.response?.data?.detail || e.message || 'Не удалось создать версию', true)
      }
    }
    const cancelVersion = () => {
      versionModalOpen.value = false
    }

    const fileInputRef = ref(null)
    const addFiles = async (files) => {
      const list = Array.from(files || [])
      if (!list.length) return
      if (!documentId.value) {
        toast('Прикрепление файлов доступно после открытия документа из реестра.', true)
        return
      }
      try {
        const fd = new FormData()
        list.forEach((f) => fd.append('files', f))
        await apiUploadAttachments(documentId.value, fd)
        await refreshDetail()
        toast('Файлы загружены')
      } catch (e) {
        toast(e?.response?.data?.detail || e.message || 'Не удалось загрузить файлы', true)
      }
    }
    const onPickFiles = (e) => {
      addFiles(e.target.files || [])
      e.target.value = ''
    }
    const onDropFiles = (e) => {
      addFiles(e.dataTransfer?.files || [])
    }
    const removeAttachment = (id) => {
      attachments.value = attachments.value.filter((f) => f.id !== id)
    }

    // -------- Left panel: registry list (backend) --------
    const searchQuery = ref('')
    const activeDocumentId = ref(documentId.value)
    const registryItems = ref([])
    const registryLoading = ref(false)

    const mapRegistryItem = (d) => ({
      id: d.id,
      no: d.outgoing_number_display || d.outgoing_number || '—',
      title: d.subject || kindLabel(d.document_kind),
      date: d.letter_date || d.created_at,
      status: d.status || 'draft',
    })

    const loadRegistry = async () => {
      registryLoading.value = true
      try {
        const rows = (await apiListDocs({ limit: 100 })) || []
        registryItems.value = (Array.isArray(rows) ? rows : []).map(mapRegistryItem)
      } catch (e) {
        toast(e?.response?.data?.detail || e.message || 'Не удалось загрузить реестр', true)
      } finally {
        registryLoading.value = false
      }
    }

    const filteredRegistryItems = computed(() => {
      const q = searchQuery.value.toLowerCase()
      if (!q) return registryItems.value
      return registryItems.value.filter((item) =>
        String(item.no).toLowerCase().includes(q) ||
        String(item.title).toLowerCase().includes(q)
      )
    })

    const mapVersions = (rows) => (rows || []).map((v) => ({
      id: v.id,
      author: v.created_by || 'Система',
      created_at: v.created_at,
      comment: v.comment || '',
      version_number: v.version_number,
      pdf_public_url: v.pdf_public_url || null,
    }))
    const mapFiles = (rows) => (rows || [])
      .filter((f) => (f.file_type || 'attachment') === 'attachment')
      .map((f) => ({
        id: f.id,
        name: f.file_name || 'файл',
        size: f.file_size || 0,
        public_url: f.public_url || null,
      }))

    const applyDetail = (d) => {
      documentId.value = d.id
      activeDocumentId.value = d.id
      documentStatus.value = d.status || 'draft'
      versions.value = mapVersions(d.versions)
      attachments.value = mapFiles(d.files)
      // Anchors come from doc columns (shared with classic editor).
      applyAnchorsFromDoc(d)
      const draft = d.editor_draft
      if (draft && Number(draft.schema_version) === V2_SCHEMA_VERSION) {
        applyV2Draft(draft)
        return draft.template_id || null
      }
      // Legacy doc opened in the v2 editor — start a clean v2 body for its kind.
      documentKind.value = d.document_kind || documentKind.value
      fieldValues.value = {}
      editableContent.value = {}
      return null
    }

    const refreshDetail = async () => {
      if (!documentId.value) return
      try {
        const d = await apiGetDoc(documentId.value)
        versions.value = mapVersions(d.versions)
        attachments.value = mapFiles(d.files)
        documentStatus.value = d.status || documentStatus.value
      } catch (e) {
        toast(e?.response?.data?.detail || e.message || 'Не удалось обновить документ', true)
      }
    }

    const openDocument = async (id) => {
      loading.value = true
      loadError.value = ''
      try {
        const d = await apiGetDoc(id)
        const tplId = applyDetail(d)
        await loadTemplate(tplId)
        // Hydrate candidate lists + recipient bank, then resolve placeholders.
        await Promise.all([
          loadDealContext(anchors.dealId.value),
          loadRecipientCompany(anchors.recipientCompanyId.value),
        ])
        await runResolve()
      } catch (e) {
        loadError.value = e?.response?.data?.detail || e.message || 'Не удалось открыть документ'
      } finally {
        loading.value = false
      }
    }

    // -------- Document status pill --------
    const statusOpen = ref(false)
    const documentStatus = ref('draft')
    const docStatus = computed(() => DOC_STATUSES.find((s) => s.key === documentStatus.value) || DOC_STATUSES[0])
    const setStatus = (key) => {
      documentStatus.value = key
      statusOpen.value = false
    }

    // -------- Approval popover --------
    const approvalOpen = ref(false)
    const approvalSteps = ref([...APPROVAL_STUB])
    const approvalActive = computed(() => approvalSteps.value.some((s) => s.status !== 'idle'))
    const currentApprovalStepIndex = computed(() => {
      const idx = approvalSteps.value.findIndex((s) => s.status === 'pending')
      return idx >= 0 ? idx : approvalSteps.value.length - 1
    })
    const currentApprovalStepNumber = computed(() => currentApprovalStepIndex.value + 1)
    const startApproval = () => {
      approvalSteps.value = approvalSteps.value.map((s, i) => ({
        ...s,
        status: i === 0 ? 'pending' : 'pending',
        acted_at: null,
        comment: '',
      }))
      documentStatus.value = 'review'
    }
    const resetApproval = () => {
      approvalSteps.value = approvalSteps.value.map((s) => ({
        ...s, status: 'idle', acted_at: null, comment: ''
      }))
      documentStatus.value = 'draft'
    }

    // -------- Single-popover coordinator --------
    // Toggling one popover deterministically closes every other one, so
    // opening B always dismisses A regardless of click-outside timing.
    const POPOVERS = {
      download: downloadOpen,
      versions: versionsOpen,
      attachments: attachmentsOpen,
      status: statusOpen,
      approval: approvalOpen,
    }
    const togglePopover = (name) => {
      const willOpen = !POPOVERS[name].value
      Object.values(POPOVERS).forEach((r) => { r.value = false })
      POPOVERS[name].value = willOpen
    }

    onMounted(async () => {
      await Promise.all([loadRegistry(), loadDeals()])
      if (documentId.value) {
        await openDocument(documentId.value)
      } else {
        await loadTemplate()
      }
    })

    return {
      template,
      loading,
      loadError,
      saving,
      documentId,
      openDocument,
      registryLoading,
      fieldValues,
      editableContent,
      activeFieldKey,
      editableFocused,
      onChipSelect,
      saveDraft,
      // toolbar
      cmdState,
      paragraphBlock,
      editorAvailable,
      inlineButtons: INLINE_BUTTONS,
      alignButtons: ALIGN_BUTTONS,
      listButtons: LIST_BUTTONS,
      execCmd,
      captureSelection,
      onBlockChange,
      onInsertImage,
      onEditableFocus,
      onEditableBlur,
      // left panel
      searchQuery,
      activeDocumentId,
      filteredRegistryItems,
      DOC_STATUS_LABEL,
      // status
      statusOpen,
      docStatus,
      setStatus,
      DOC_STATUSES,
      // approval
      approvalOpen,
      approvalSteps,
      approvalActive,
      currentApprovalStepIndex,
      currentApprovalStepNumber,
      startApproval,
      resetApproval,
      formatRelative,
      // kind switcher
      DOC_KINDS,
      documentKind,
      setDocumentKind,
      // anchors + resolve
      anchors,
      dealOptions,
      contractOptions,
      stageOptions,
      paymentOptions,
      recipientCompany,
      resolvedContext,
      resolving,
      onRecipientPicked,
      onDealPicked,
      // download / versions / attachments
      downloadOpen,
      versionsOpen,
      attachmentsOpen,
      versions,
      attachments,
      downloadAs,
      downloadVersion,
      createVersion,
      fileInputRef,
      onPickFiles,
      onDropFiles,
      removeAttachment,
      formatBytes,
      fileIcon,
      togglePopover,
      // version comment modal
      versionModalOpen,
      versionComment,
      versionCommentInput,
      confirmVersion,
      cancelVersion,
    }
  }
}
</script>

<style scoped>
.outgoing-v2-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Toolbar */
.outgoing-v2-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  height: 48px;
  padding: 0 14px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface);
  flex-shrink: 0;
}
.outgoing-v2-toolbar__left,
.outgoing-v2-toolbar__right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.outgoing-v2-toolbar__right { gap: 8px; }

.tlb-btn {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: var(--text-sm);
}
.tlb-btn:hover:not(:disabled) { background: var(--color-surface-2); color: var(--color-text); }
.tlb-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.tlb-btn--active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

/* Ghost variant for right-side toolbar icons (download/versions/attachments) */
.tlb-btn--ghost {
  position: relative;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-muted);
}
.tlb-btn--ghost:hover:not(:disabled) {
  background: var(--color-surface-2);
  color: var(--color-text);
}
/* Labelled variant — icon + text, auto width */
.tlb-btn--label {
  width: auto;
  gap: 6px;
  padding: 0 12px;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
}
.tlb-btn__badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 15px;
  height: 15px;
  padding: 0 4px;
  background: var(--color-primary);
  color: #fff;
  font-size: 10px;
  font-weight: var(--fw-bold);
  border-radius: var(--radius-pill);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* ---- Download menu ---- */
.download-wrap { position: relative; }
.download-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 600;
  min-width: 200px;
  padding: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}
.download-menu__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
}
.download-menu__item:hover { background: var(--color-surface-2); }
.download-menu__item i { width: 14px; color: var(--color-text-muted); }

/* ---- Side popover (versions + attachments) ---- */
.popover-wrap { position: relative; }
.side-popover {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 600;
  width: 360px;
  max-height: 480px;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}
.side-popover__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.side-popover__head h4 { margin: 2px 0 0; font-size: var(--text-base); font-weight: var(--fw-semibold); color: var(--color-text); }
.side-popover__eyebrow {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-subtle);
}
.side-popover__empty {
  padding: 20px 16px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.45;
}
.side-popover__empty i { color: var(--color-text-subtle); margin: 0 2px; }

/* Versions list */
.version-list {
  list-style: none;
  margin: 0;
  padding: 6px 8px;
  overflow-y: auto;
}
.version-list__item {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}
.version-list__item:hover { background: var(--color-surface-2); }
.version-list__num {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
}
.version-list__meta { font-size: var(--text-sm); color: var(--color-text); }
.version-list__author { font-weight: var(--fw-semibold); }
.version-list__time { color: var(--color-text-muted); }
.version-list__comment {
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.version-list__actions { display: inline-flex; gap: 6px; }
.ver-dl {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 1.15rem;
  line-height: 1;
  transition: background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.ver-dl:hover { transform: translateY(-1px); }
.ver-dl--pdf { color: #e53935; }
.ver-dl--pdf:hover { background: rgba(229, 57, 53, 0.12); }
.ver-dl--word { color: #2b6cb0; }
.ver-dl--word:hover { background: rgba(43, 108, 176, 0.12); }

/* Attachments list + uploader */
.attachment-uploader {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-2);
}
.attachment-uploader__hint { font-size: var(--text-xs); color: var(--color-text-muted); }
.attachment-list {
  list-style: none;
  margin: 0;
  padding: 6px 8px;
  overflow-y: auto;
}
.attachment-list__item {
  display: grid;
  grid-template-columns: 28px 1fr auto auto;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}
.attachment-list__item:hover { background: var(--color-surface-2); }
.attachment-list__icon { color: var(--color-text-muted); font-size: 1rem; }
.attachment-list__name {
  font-size: var(--text-sm);
  color: var(--color-text);
  font-weight: var(--fw-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.attachment-list__meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.tlb-btn--primary {
  width: auto;
  padding: 0 14px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-weight: var(--fw-medium);
  font-size: var(--text-sm);
}
.tlb-btn--primary:hover:not(:disabled) { background: var(--color-primary-hover, #2f6fe0); }

.tlb-sep {
  width: 1px;
  height: 22px;
  background: var(--color-border-subtle);
  margin: 0 6px;
}

.tlb-select {
  height: 30px;
  padding: 0 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: var(--text-sm);
  color: var(--color-text);
}
.tlb-select:disabled { opacity: 0.45; }

/* Body — three columns */
.outgoing-v2-body {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 320px;
}

/* Left panel */
.outgoing-v2-left {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border-subtle);
}
.outgoing-v2-left__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.outgoing-v2-left__search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 16px;
  padding: 0 10px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-text);
}
.outgoing-v2-left__search:focus-within {
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: var(--shadow-focus);
}
.outgoing-v2-left__search > i { color: var(--color-text-subtle); font-size: var(--text-sm); }
.outgoing-v2-left__search input {
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: var(--text-sm);
  color: var(--color-text);
  padding: 0;
  min-width: 0;
}
.outgoing-v2-left__search input::placeholder { color: var(--color-text-subtle); }
.outgoing-v2-left__search-clear {
  border: 0;
  background: transparent;
  padding: 4px;
  border-radius: var(--radius-sm);
  color: var(--color-text-subtle);
  cursor: pointer;
}
.outgoing-v2-left__search-clear:hover { color: var(--color-text); background: var(--color-surface-3); }

.outgoing-v2-left__list { flex: 1 1 auto; overflow-y: auto; padding: 4px 8px 12px; }
.outgoing-v2-left__empty {
  padding: 24px 12px;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.reg-item {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.reg-item:hover { background: var(--color-surface-2); }
.reg-item--active { background: var(--color-primary-soft); }
.reg-item__no { font-size: var(--text-sm); font-weight: var(--fw-semibold); color: var(--color-primary); }
.reg-item__title { font-size: var(--text-sm); color: var(--color-text); }
.reg-item__status {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: lowercase;
}
.reg-item__status::before { content: '\25cf'; color: var(--color-text-subtle); margin-right: 4px; }
.reg-item__status--draft::before    { color: var(--color-warning); }
.reg-item__status--review::before   { color: var(--color-primary); }
.reg-item__status--sent::before     { color: var(--color-info, var(--color-primary)); }
.reg-item__status--signed::before   { color: var(--color-success); }
.reg-item__status--rejected::before { color: var(--color-danger); }

/* ---- Status pill in toolbar right ---- */
.status-wrap { position: relative; }
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
  color: var(--color-text);
  white-space: nowrap;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.status-pill:hover { background: var(--color-surface-2); }
.status-pill__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-text-subtle);
  flex-shrink: 0;
}
.status-pill--draft .status-pill__dot,
.status-menu__item--draft .status-pill__dot { background: var(--color-warning); }
.status-pill--review .status-pill__dot,
.status-menu__item--review .status-pill__dot { background: var(--color-primary); }
.status-pill--sent .status-pill__dot,
.status-menu__item--sent .status-pill__dot { background: var(--color-info, var(--color-primary)); }
.status-pill--signed .status-pill__dot,
.status-menu__item--signed .status-pill__dot { background: var(--color-success); }
.status-pill--rejected .status-pill__dot,
.status-menu__item--rejected .status-pill__dot { background: var(--color-danger); }

.status-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 600;
  min-width: 220px;
  padding: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}
.status-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
}
.status-menu__item:hover { background: var(--color-surface-2); }
.ml-auto { margin-left: auto; color: var(--color-primary); }

/* ---- Approval popover ---- */
.approval-wrap { position: relative; }
.approval-btn {
  width: auto;
  height: 32px;
  padding: 0 10px;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}
.approval-btn:hover:not(:disabled) { background: var(--color-surface-2); color: var(--color-text); }
.approval-btn--active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-soft);
}
.approval-btn__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 18px;
  padding: 0 6px;
  background: var(--color-primary);
  color: #fff;
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  border-radius: var(--radius-pill);
}

.approval-popover {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 600;
  width: 360px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}
.approval-popover__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.approval-popover__head h4 { margin: 2px 0 0; font-size: var(--text-base); font-weight: var(--fw-semibold); color: var(--color-text); }
.approval-popover__eyebrow {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-subtle);
}
.approval-popover__empty {
  padding: 20px 16px 24px;
  text-align: center;
}
.approval-popover__empty p {
  margin: 0 0 12px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
.approval-popover__foot {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border-subtle);
  display: flex;
  justify-content: flex-end;
}

.approval-stepper {
  list-style: none;
  margin: 0;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.approval-stepper__item {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 10px;
  align-items: flex-start;
  position: relative;
}
.approval-stepper__item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 14px;
  top: 32px;
  bottom: -14px;
  width: 1px;
  background: var(--color-border-subtle);
}
.approval-stepper__index {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  flex-shrink: 0;
}
.approval-stepper__item--approved .approval-stepper__index {
  background: var(--color-success-soft);
  color: var(--color-success);
}
.approval-stepper__item--rejected .approval-stepper__index {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}
.approval-stepper__item--current .approval-stepper__index {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 0 0 4px var(--color-primary-soft);
}
.approval-stepper__body { min-width: 0; }
.approval-stepper__name { font-size: var(--text-sm); font-weight: var(--fw-semibold); color: var(--color-text); }
.approval-stepper__meta { display: flex; gap: 6px; align-items: center; font-size: var(--text-xs); color: var(--color-text-muted); margin-top: 2px; }
.approval-stepper__role { font-weight: var(--fw-medium); }
.approval-stepper__comment {
  margin: 6px 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  padding: 6px 10px;
  background: var(--color-surface-2);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--color-border);
}

.hide-sm { display: inline; }
@media (max-width: 900px) {
  .hide-sm { display: none; }
}

.pop-enter-active, .pop-leave-active { transition: opacity var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out); }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }

/* ---- Version comment modal ---- */
.ovm-overlay {
  position: fixed;
  inset: 0;
  z-index: 9200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.42);
}
.ovm {
  width: min(440px, 100%);
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
  overflow: hidden;
}
.ovm__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.ovm__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: var(--fw-bold);
  color: var(--color-text);
}
.ovm__body {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ovm__label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-weight: 600;
  color: var(--color-text-muted);
}
.ovm__textarea {
  width: 100%;
  min-height: 76px;
  resize: vertical;
  padding: 8px 10px;
  font-size: var(--text-sm);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.ovm__textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.ovm__hint {
  margin: 2px 0 0;
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}
.ovm__foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid var(--color-border-subtle);
}
.ovm__foot .tlb-btn--primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.ovm__foot .tlb-btn--primary:hover { background: var(--color-primary-hover, #2f6fe0); }

/* Center */
.outgoing-v2-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 24px 24px;
  overflow-y: auto;
  background: var(--color-surface-2);
  gap: 16px;
}
.outgoing-v2-center__loading,
.outgoing-v2-center__error {
  margin: auto;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
.outgoing-v2-center__error { color: var(--color-danger); }

/* Kind switcher — compact segmented pills in the top toolbar (left) */
.kind-switcher {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-pill);
}
.kind-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px;
  border: 0;
  background: transparent;
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  white-space: nowrap;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.kind-pill:hover { background: var(--color-surface); color: var(--color-text); }
.kind-pill--active {
  background: var(--color-surface);
  color: var(--color-primary);
  font-weight: var(--fw-semibold);
  box-shadow: var(--shadow-xs, 0 1px 2px rgba(15, 23, 42, 0.06));
}
.kind-pill i { font-size: 0.9em; }

/* Formatting bar — capsule above the A4 page (mirrors the doc width) */
.format-bar {
  width: min(820px, 100%);
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  padding: 6px 10px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
.format-bar .tlb-sep {
  height: 22px;
  margin: 0 6px;
}
</style>
