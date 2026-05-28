import { ref, onMounted, nextTick, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PizZip from 'pizzip'
import Docxtemplater from 'docxtemplater'
import { renderAsync as renderDocxAsync } from 'docx-preview'
import axios from 'axios'
import DOMPurify from 'dompurify'
import * as outgoingApi from '../../../services/api/outgoing'
import { downloadFromApi, downloadFromPath, downloadFromHref } from '../../../utils/download'
import { useUploadQueueStore } from '../../../stores/uploadQueue'
import { useAuthStore } from '../../../stores/auth'
import { useCompaniesStore } from '../../../stores/companies'
import { useToast } from '../../../composables/useToast'
import { staticOurCompanies, previewCompanyProfiles } from '../../../config/appVariant'

/**
 * Composable for OutgoingRegistry view.
 *
 * Holds all reactive state, API calls (api.outgoing.* + a small number of
 * cross-domain axios calls flagged below), and helper functions.
 *
 * Cross-domain axios calls kept intentionally:
 *  - GET  /api/v1/ai/status                (ai module — separate domain)
 *  - POST /api/v1/ai/outgoing/assist       (ai module)
 *  - GET  /api/v1/deals/                   (deals module)
 *  - GET  /api/v1/contracts/deal/{id}      (contracts module)
 *  - GET  /api/v1/stages/deal/{id}         (stages module)
 *  - GET  /api/v1/income-expense/          (incomeExpense module)
 *  - GET  /templates/*.docx                (static asset)
 *
 * Attachments upload uses raw axios to keep onUploadProgress (api/_client
 * does not forward it).
 */
export function useOutgoingRegistryState() {
  const route = useRoute()
  const router = useRouter()
  const companiesStore = useCompaniesStore()
  const documents = ref([])
  const page = ref(1)
  const pageSize = 20
  const hasNext = computed(() => documents.value.length === pageSize)
  const companies = ref([])
  const deals = ref([])
  const activeDocument = ref({})
  const activeDocumentId = ref(null)
  const outgoingApprovalState = ref({
    activeInstance: null,
    latestInstance: null,
    latestStatus: null,
    templateCount: 0,
  })
  const versions = ref([])
  const files = ref([])
  const pendingFiles = ref([])
  const loading = ref(false)
  const saving = ref(false)
  const isEditing = ref(false)
  const deleteModalOpen = ref(false)
  const uploadQueue = useUploadQueueStore()
  const authStore = useAuthStore()
  const { success: toastSuccess, error: toastError } = useToast()
  const canEditSequences = computed(() => {
    if (authStore.isSuperuser) return true
    const perms = authStore.permissions || {}
    const registryPerms = perms.outgoing_registry || {}
    return !!(registryPerms.read_all || registryPerms.read_assigned)
  })
  const documentKinds = [
    { value: 'letter', label: 'Письма', singular: 'Письмо', subtitle: 'Реестр писем', icon: 'fa-envelope' },
    { value: 'invoice', label: 'Счета', singular: 'Счет', subtitle: 'Реестр счетов', icon: 'fa-file-invoice-dollar' },
    { value: 'upd', label: 'УПД', singular: 'УПД', subtitle: 'Реестр УПД', icon: 'fa-file-contract' },
    { value: 'act', label: 'Акты', singular: 'Акт', subtitle: 'Реестр актов', icon: 'fa-clipboard-check' },
    { value: 'vat_invoice', label: 'Счет-фактуры', singular: 'Счет-фактура', subtitle: 'Реестр счет-фактур', icon: 'fa-file-invoice' }
  ]
  const normalizeDocumentKind = (value) => {
    const allowed = documentKinds.map((item) => item.value)
    return allowed.includes(value) ? value : 'letter'
  }
  const activeKind = ref(normalizeDocumentKind(route.query.kind))
  const activeKindMeta = computed(() => documentKinds.find((item) => item.value === activeKind.value) || documentKinds[0])
  const documentKindMeta = (doc) => (
    documentKinds.find((item) => item.value === (doc?.document_kind || activeKind.value)) || documentKinds[0]
  )
  const isLetterKind = computed(() => activeKind.value === 'letter')
  const isActKind = computed(() => activeKind.value === 'act')
  const hasEditableNumberSuffix = computed(() => isLetterKind.value)
  const requiresStageLinks = computed(() => ['act', 'upd', 'vat_invoice'].includes(activeKind.value))
  const requiresPaymentLinks = computed(() => ['act', 'invoice'].includes(activeKind.value))
  const isLetterDocument = (doc) => (doc?.document_kind || activeKind.value) === 'letter'

  const ourCompanies = ref(
    staticOurCompanies.map((company) => ({
      label: company.label,
      value: company.key
    }))
  )
  const ourCompanyLocked = computed(() => !!(activeDocumentId.value && activeDocument.value?.our_company_key))

  const filters = ref({
    search: '',
    status: '',
    our_company_key: '',
    recipient_company_id: '',
    date_from: '',
    date_to: ''
  })
  const currentParams = ref({})
  const filtersReady = ref(false)
  const filtersDebounce = ref(null)
  const dealContracts = ref([])
  const dealStages = ref([])
  const dealPayments = ref([])
  const dealPaymentUsage = ref({})
  const editorBlockCatalog = ref([])
  const editorFields = ref([])
  const editorTemplateBlocks = ref([])
  const editorResolvedFields = ref({})
  const editorResolvedContext = ref({})
  const editorSchemaVersion = ref(1)
  const editorSchemaDraft = ref(null)
  const editorSchemaLoading = ref(false)
  const aiEnabled = ref(false)
  const aiReachable = ref(false)
  const aiModel = ref('')

  const previewMode = ref('fit-page')
  const previewScale = ref(1)
  const previewPdfBaseUrl = ref('')
  const previewFrameSrc = computed(() => {
    if (!previewPdfBaseUrl.value) return ''
    const zoom = previewMode.value === 'fit-page'
      ? 'page-fit'
      : previewMode.value === 'fit-width'
        ? 'page-width'
        : '100'
    return `${previewPdfBaseUrl.value}#toolbar=0&navpanes=0&scrollbar=1&zoom=${zoom}`
  })
  const previewReady = ref(false)
  const previewLoading = ref(false)
  const previewScaleLabel = computed(() => {
    if (previewMode.value === 'actual') return 100
    if (previewMode.value === 'fit-width') return 100
    return 90
  })
  const liveStructuredPreviewMode = ref('pdf')
  const liveStructuredPreviewLoading = ref(false)
  const liveStructuredPreviewError = ref('')
  const liveStructuredPreviewPdfUrl = ref('')
  const liveStructuredPreviewDocxRef = ref(null)
  const liveStructuredPreviewPdfSrc = computed(() => (
    liveStructuredPreviewPdfUrl.value
      ? `${liveStructuredPreviewPdfUrl.value}#toolbar=0&navpanes=0&scrollbar=1&zoom=page-fit`
      : ''
  ))
  const canRenderStructuredPreview = computed(() => (
    isEditing.value &&
    form.value.editor_mode === 'structured' &&
    !!form.value.recipient_company_id
  ))

  const sequencesModalOpen = ref(false)
  const sequenceLoading = ref(false)
  const sequenceSaving = ref(false)
  const sequences = ref([])
  const sequenceForm = ref({})

  const editorRef = ref(null)
  const attachmentsEditorRef = ref(null)
  const docListRef = ref(null)
  const editorSelectionRange = ref(null)
  const showFormattingMarks = ref(false)
  const editorInList = ref(false)
  const attachmentsInList = ref(false)
  const tableModalOpen = ref(false)
  const tableForm = ref({
    rows: 2,
    cols: 3,
    includeHeader: true
  })
  const tableControls = ref({
    visible: false,
    left: 0,
    top: 0,
    rowIndex: -1,
    colIndex: -1,
    canDeleteRow: false,
    canDeleteCol: false
  })
  let hoveredTableCell = null
  let tableControlsHover = false
  let tableControlsHideTimer = null
  const introParagraphBusy = ref(false)

  const DEFAULT_RECIPIENT_EIO = 'Генеральному директору'
  const OUTGOING_DRAFT_STORAGE_PREFIX = 'crm_outgoing_draft'
  const OUTGOING_DRAFT_NOTICE_PREFIX = 'crm_outgoing_draft_notice'
  const OUTGOING_DRAFT_AUTOSAVE_DELAY = 1000

  const buildDefaultForm = () => ({
    document_kind: activeKind.value,
    editor_mode: activeKind.value === 'letter' ? 'classic' : 'structured',
    editor_schema_version: 1,
    editor_draft: null,
    editor_validation: { errors: [], warnings: [] },
    editor_render_context: { snapshot_mode: 'live' },
    recipient_company_id: '',
    our_company_key: ourCompanies.value[0]?.value || 'normbud',
    deal_id: '',
    contract_id: '',
    letter_date: new Date().toISOString().split('T')[0],
    subject: '',
    body: '',
    attachments_list: '',
    bank_account_index: null,
    linked_stage_ids: [],
    linked_payment_items: [],
    recipient_short_name: '',
    recipient_to_name: '',
    recipient_appeal: '',
    recipient_eio: DEFAULT_RECIPIENT_EIO,
    recipient_genitive_name: '',
    recipient_salutation: '',
    outgoing_number_suffix: ''
  })
  const form = ref(buildDefaultForm())
  const draftRestoreModalOpen = ref(false)
  const draftRestoreCandidate = ref(null)
  const draftRestoreReason = ref('')
  const restoredPendingFileNames = ref([])
  const draftSyncSuspended = ref(false)
  let draftAutosaveTimer = null
  let editorResolveTimer = null
  let editorResolveRequestSeq = 0
  let liveStructuredPreviewTimer = null
  let liveStructuredPreviewRequestSeq = 0

  const cloneDeep = (value) => JSON.parse(JSON.stringify(value))

  const computeLocalEditorValidation = (draft, documentKind = activeKind.value) => {
    const blocks = Array.isArray(draft?.content) ? draft.content : []
    const errors = []
    const warnings = []
    const blockTypes = blocks.map((block) => String(block?.type || ''))
    if (!blocks.length) errors.push('Конструктор документа не содержит блоков.')
    if (!blockTypes.includes('document_meta')) warnings.push('Отсутствует блок шапки документа.')
    if (documentKind !== 'letter' && !blockTypes.includes('signature_stamp')) {
      warnings.push('Отсутствует блок подписей.')
    }
    if (documentKind === 'invoice' && !blockTypes.includes('invoice_items_table')) {
      warnings.push('Для счета обычно нужна табличная часть.')
    }
    if (['act', 'upd', 'vat_invoice'].includes(documentKind) && !blockTypes.includes('stage_lines_block')) {
      warnings.push('Для выбранного типа документа нет блока строк по этапам.')
    }
    if (documentKind === 'act' && !blockTypes.includes('payment_allocation_block')) {
      warnings.push('Для акта не добавлен блок зачетов платежей.')
    }
    return { errors, warnings }
  }

  const syncDraftWithCurrentForm = (draft) => {
    const nextDraft = cloneDeep(draft || { schema_version: 1, document_kind: form.value.document_kind || activeKind.value, content: [] })
    const blocks = Array.isArray(nextDraft.content) ? nextDraft.content : []
    const richTextBlock = blocks.find((block) => block?.type === 'rich_text_block')
    const introBlock = blocks.find((block) => block?.type === 'intro_paragraph')
    const basisBlock = blocks.find((block) => block?.type === 'basis_block')
    if (richTextBlock && !richTextBlock.attrs?.html && form.value.body) {
      richTextBlock.attrs = { ...(richTextBlock.attrs || {}), html: form.value.body }
    }
    if (introBlock && !introBlock.attrs?.text && form.value.recipient_appeal) {
      introBlock.attrs = { ...(introBlock.attrs || {}), text: '' }
    }
    if (basisBlock && !basisBlock.attrs?.text_pattern && form.value.subject) {
      basisBlock.attrs = { ...(basisBlock.attrs || {}), text_pattern: form.value.subject }
    }
    return nextDraft
  }

  const syncStructuredDraftIntoForm = () => {
    if (form.value.editor_mode !== 'structured') return
    const blocks = Array.isArray(form.value.editor_draft?.content) ? form.value.editor_draft.content : []
    const richTextBlock = blocks.find((block) => block?.type === 'rich_text_block')
    const basisBlock = blocks.find((block) => block?.type === 'basis_block')
    if (isLetterKind.value && richTextBlock?.attrs?.html) {
      form.value.body = richTextBlock.attrs.html
    }
    if (!isLetterKind.value && basisBlock?.attrs?.text_pattern && !form.value.subject) {
      form.value.subject = basisBlock.attrs.text_pattern
    }
  }

  const ensureEditorDraft = ({ forceDefault = false } = {}) => {
    const draft = form.value.editor_draft
    if (!forceDefault && draft && Array.isArray(draft.content) && draft.content.length) {
      form.value.editor_draft = syncDraftWithCurrentForm(draft)
      form.value.editor_schema_version = Number(draft.schema_version || editorSchemaVersion.value || 1)
      form.value.editor_validation = computeLocalEditorValidation(form.value.editor_draft, form.value.document_kind || activeKind.value)
      return
    }
    const defaultDraft = cloneDeep(editorSchemaLoading.value || !editorBlockCatalog.value.length
      ? { schema_version: 1, document_kind: form.value.document_kind || activeKind.value, content: [] }
      : {
          schema_version: editorSchemaVersion.value,
          document_kind: form.value.document_kind || activeKind.value,
          content: []
        })
    if (editorSchemaDraft.value && Array.isArray(editorSchemaDraft.value.content)) {
      form.value.editor_draft = cloneDeep(editorSchemaDraft.value)
    } else {
      form.value.editor_draft = defaultDraft
    }
    form.value.editor_draft = syncDraftWithCurrentForm(form.value.editor_draft)
    form.value.editor_schema_version = Number(form.value.editor_draft?.schema_version || editorSchemaVersion.value || 1)
    form.value.editor_validation = computeLocalEditorValidation(form.value.editor_draft, form.value.document_kind || activeKind.value)
  }

  const buildParams = () => {
    const params = {}
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.our_company_key) params.our_company_key = filters.value.our_company_key
    if (filters.value.recipient_company_id) params.recipient_company_id = filters.value.recipient_company_id
    if (filters.value.date_from) params.date_from = filters.value.date_from
    if (filters.value.date_to) params.date_to = filters.value.date_to
    params.document_kind = activeKind.value
    params.skip = (page.value - 1) * pageSize
    params.limit = pageSize
    return params
  }

  const loadEditorSchema = async (documentKind = activeKind.value) => {
    editorSchemaLoading.value = true
    try {
      const result = await outgoingApi.getEditorSchema({ document_kind: documentKind })
      editorBlockCatalog.value = result?.block_catalog || []
      editorFields.value = result?.fields || []
      editorTemplateBlocks.value = result?.template_blocks || []
      editorSchemaVersion.value = Number(result?.schema_version || 1)
      editorSchemaDraft.value = result?.default_draft || null
    } catch (error) {
      console.error('Error loading editor schema:', error)
      editorBlockCatalog.value = []
      editorFields.value = []
      editorTemplateBlocks.value = []
      editorSchemaVersion.value = 1
      editorSchemaDraft.value = null
    } finally {
      editorSchemaLoading.value = false
    }
  }

  const loadAiStatus = async () => {
    try {
      // cross-domain endpoint; not in outgoing.js
      const response = await axios.get('/api/v1/ai/status')
      aiReachable.value = !!response.data?.reachable
      aiEnabled.value = !!response.data?.enabled && aiReachable.value
      aiModel.value = response.data?.model || ''
    } catch (error) {
      console.error('Error loading AI status:', error)
      aiEnabled.value = false
      aiReachable.value = false
      aiModel.value = ''
    }
  }

  const loadEditorContext = async (documentId) => {
    if (!documentId) {
      editorResolvedFields.value = {}
      editorResolvedContext.value = {}
      return
    }
    try {
      const result = await outgoingApi.getEditorContext(documentId)
      editorBlockCatalog.value = result?.block_catalog || editorBlockCatalog.value
      editorFields.value = result?.fields || editorFields.value
      editorTemplateBlocks.value = result?.template_blocks || editorTemplateBlocks.value
      editorResolvedFields.value = result?.resolved_fields || {}
      editorResolvedContext.value = result?.resolved_context || {}
      editorSchemaVersion.value = Number(result?.schema_version || editorSchemaVersion.value || 1)
      if (result?.validation) {
        form.value.editor_validation = result.validation
      }
    } catch (error) {
      console.error('Error loading editor context:', error)
      editorResolvedFields.value = {}
      editorResolvedContext.value = {}
    }
  }

  const clearEditorResolveTimer = () => {
    if (!editorResolveTimer) return
    clearTimeout(editorResolveTimer)
    editorResolveTimer = null
  }

  const buildEditorResolvePayload = () => ({
    document_id: activeDocumentId.value || null,
    document_kind: form.value.document_kind || activeKind.value,
    editor_mode: form.value.editor_mode || (activeKind.value === 'letter' ? 'classic' : 'structured'),
    editor_schema_version: Number(form.value.editor_schema_version || editorSchemaVersion.value || 1),
    editor_draft: form.value.editor_draft ? cloneDeep(form.value.editor_draft) : null,
    editor_render_context: form.value.editor_render_context ? cloneDeep(form.value.editor_render_context) : { snapshot_mode: 'live' },
    recipient_company_id: form.value.recipient_company_id || null,
    our_company_key: form.value.our_company_key || null,
    deal_id: form.value.deal_id || null,
    contract_id: form.value.contract_id || null,
    letter_date: form.value.letter_date || null,
    subject: form.value.subject || '',
    body: form.value.body || '',
    attachments_list: form.value.attachments_list || '',
    bank_account_index: form.value.bank_account_index,
    linked_stage_ids: Array.isArray(form.value.linked_stage_ids) ? [...form.value.linked_stage_ids] : [],
    linked_payment_items: Array.isArray(form.value.linked_payment_items)
      ? form.value.linked_payment_items.map((item) => ({ ...item }))
      : [],
    recipient_short_name: form.value.recipient_short_name || '',
    recipient_to_name: form.value.recipient_to_name || '',
    recipient_appeal: form.value.recipient_appeal || '',
    recipient_eio: form.value.recipient_eio || '',
    recipient_genitive_name: form.value.recipient_genitive_name || '',
    recipient_salutation: form.value.recipient_salutation || '',
    status: 'draft'
  })

  const editorResolveSignature = computed(() => JSON.stringify(buildEditorResolvePayload()))

  const resolveStructuredEditorContext = async () => {
    if (!isEditing.value || draftSyncSuspended.value || form.value.editor_mode !== 'structured') return
    if (!form.value.recipient_company_id) {
      editorResolvedFields.value = {}
      editorResolvedContext.value = {}
      form.value.editor_validation = computeLocalEditorValidation(form.value.editor_draft, form.value.document_kind || activeKind.value)
      return
    }
    const requestSeq = ++editorResolveRequestSeq
    try {
      const result = await outgoingApi.resolveEditor(buildEditorResolvePayload())
      if (requestSeq !== editorResolveRequestSeq) return
      editorBlockCatalog.value = result?.block_catalog || editorBlockCatalog.value
      editorFields.value = result?.fields || editorFields.value
      editorTemplateBlocks.value = result?.template_blocks || editorTemplateBlocks.value
      editorResolvedFields.value = result?.resolved_fields || {}
      editorResolvedContext.value = result?.resolved_context || {}
      if (result?.validation) {
        form.value.editor_validation = result.validation
      }
    } catch (error) {
      if (requestSeq !== editorResolveRequestSeq) return
      console.error('Error resolving structured editor context:', error)
      editorResolvedContext.value = {}
    }
  }

  const scheduleStructuredEditorResolve = (delay = 250) => {
    clearEditorResolveTimer()
    editorResolveTimer = setTimeout(() => {
      resolveStructuredEditorContext()
    }, delay)
  }

  const requestOutgoingAiAssist = async ({ action, prompt, currentHtml, selectionText, selectionPresent }) => {
    if (!aiEnabled.value || !aiReachable.value) {
      throw new Error('AI-контур сейчас недоступен.')
    }
    // cross-domain ai endpoint, not in outgoing.js
    const response = await axios.post('/api/v1/ai/outgoing/assist', {
      action,
      prompt: prompt || '',
      current_html: currentHtml || '',
      selection_text: selectionText || '',
      selection_present: !!selectionPresent,
      document_payload: buildEditorResolvePayload(),
    })
    return response.data
  }

  const applyFilters = async () => {
    page.value = 1
    currentParams.value = buildParams()
    await loadDocuments(currentParams.value)
  }

  const resetFilters = async () => {
    filters.value = {
      search: '',
      status: '',
      our_company_key: '',
      recipient_company_id: '',
      date_from: '',
      date_to: ''
    }
    page.value = 1
    currentParams.value = buildParams()
    await loadDocuments(currentParams.value)
  }

  const switchDocumentKind = async (kind) => {
    const nextKind = normalizeDocumentKind(kind)
    if (nextKind === activeKind.value) return
    persistDraftNow()
    activeKind.value = nextKind
    page.value = 1
    activeDocumentId.value = null
    activeDocument.value = {}
    versions.value = []
    files.value = []
    pendingFiles.value = []
    clearPreviewContainer()
    previewReady.value = false
    clearStructuredLivePreviewTimer()
    clearStructuredLivePreview()
    isEditing.value = false
    form.value = buildDefaultForm()
    editorResolvedFields.value = {}
    syncDocumentQuery(null)
    router.replace({ query: { ...route.query, kind: nextKind } }).catch(() => {})
    await loadEditorSchema(nextKind)
    ensureEditorDraft({ forceDefault: true })
    currentParams.value = buildParams()
    await loadDocuments(currentParams.value)
    await openDocumentFromQueryOrDefault()
  }

  watch(filters, () => {
    if (!filtersReady.value) return
    if (filtersDebounce.value) clearTimeout(filtersDebounce.value)
    filtersDebounce.value = setTimeout(() => applyFilters(), 300)
  }, { deep: true })

  watch(
    () => form.value.editor_draft,
    (draft) => {
      form.value.editor_validation = computeLocalEditorValidation(draft, form.value.document_kind || activeKind.value)
      scheduleDraftPersist()
    },
    { deep: true }
  )

  watch(
    () => form.value.editor_mode,
    (mode) => {
      if (mode === 'structured') {
        ensureEditorDraft()
        scheduleStructuredEditorResolve(0)
        scheduleStructuredLivePreview(0)
      } else {
        clearEditorResolveTimer()
        clearStructuredLivePreviewTimer()
        clearStructuredLivePreview()
      }
      scheduleDraftPersist()
    }
  )

  watch(editorResolveSignature, () => {
    if (!isEditing.value || draftSyncSuspended.value || form.value.editor_mode !== 'structured') return
    scheduleStructuredEditorResolve()
    scheduleStructuredLivePreview()
  })

  watch(liveStructuredPreviewMode, () => {
    if (!isEditing.value || form.value.editor_mode !== 'structured') return
    scheduleStructuredLivePreview(0)
  })

  const clearDraftAutosaveTimer = () => {
    if (!draftAutosaveTimer) return
    clearTimeout(draftAutosaveTimer)
    draftAutosaveTimer = null
  }

  const getDraftScope = () => (
    String(authStore.user?.id || authStore.user?.email || 'anonymous')
  )

  const getDraftContextKind = (kind = activeKind.value) => normalizeDocumentKind(kind || activeKind.value)

  const getDraftContextId = (documentId = activeDocumentId.value, kind = activeKind.value) => {
    const normalizedKind = getDraftContextKind(kind)
    return documentId ? `${normalizedKind}:${documentId}` : `${normalizedKind}:new`
  }

  const buildDraftStorageKey = (documentId = activeDocumentId.value, kind = activeKind.value) => (
    `${OUTGOING_DRAFT_STORAGE_PREFIX}:${getDraftScope()}:${getDraftContextId(documentId, kind)}`
  )

  const buildDraftNoticeKey = (documentId = activeDocumentId.value, kind = activeKind.value) => (
    `${OUTGOING_DRAFT_NOTICE_PREFIX}:${getDraftScope()}:${getDraftContextId(documentId, kind)}`
  )

  const buildLegacyDraftStorageKey = (documentId = activeDocumentId.value) => (
    `${OUTGOING_DRAFT_STORAGE_PREFIX}:${getDraftScope()}:${documentId ? String(documentId) : 'new'}`
  )

  const buildLegacyDraftNoticeKey = (documentId = activeDocumentId.value) => (
    `${OUTGOING_DRAFT_NOTICE_PREFIX}:${getDraftScope()}:${documentId ? String(documentId) : 'new'}`
  )

  const readStorageJson = (key) => {
    if (!key) return null
    try {
      const raw = sessionStorage.getItem(key)
      return raw ? JSON.parse(raw) : null
    } catch (error) {
      console.error('Error reading outgoing draft from storage:', error)
      return null
    }
  }

  const writeStorageJson = (key, value) => {
    if (!key) return
    try {
      sessionStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Error writing outgoing draft to storage:', error)
    }
  }

  const removeStorageKey = (key) => {
    if (!key) return
    try {
      sessionStorage.removeItem(key)
    } catch (error) {
      console.error('Error removing outgoing draft from storage:', error)
    }
  }

  const buildComparableDraftForm = (source = {}) => ({
    document_kind: source.document_kind || activeKind.value,
    editor_mode: source.editor_mode || (activeKind.value === 'letter' ? 'classic' : 'structured'),
    editor_schema_version: Number(source.editor_schema_version || editorSchemaVersion.value || 1),
    editor_draft: source.editor_draft ? cloneDeep(source.editor_draft) : null,
    editor_validation: source.editor_validation ? cloneDeep(source.editor_validation) : { errors: [], warnings: [] },
    editor_render_context: source.editor_render_context ? cloneDeep(source.editor_render_context) : { snapshot_mode: 'live' },
    recipient_company_id: source.recipient_company_id || '',
    our_company_key: source.our_company_key || ourCompanies.value[0]?.value || 'normbud',
    deal_id: source.deal_id || '',
    contract_id: source.contract_id || '',
    letter_date: source.letter_date || '',
    subject: source.subject || '',
    body: source.body || '',
    attachments_list: source.attachments_list || '',
    bank_account_index: source.bank_account_index ?? null,
    linked_stage_ids: Array.isArray(source.linked_stage_ids) ? [...source.linked_stage_ids] : [],
    linked_payment_items: Array.isArray(source.linked_payment_items) ? source.linked_payment_items.map((item) => ({ ...item })) : [],
    recipient_short_name: source.recipient_short_name || '',
    recipient_to_name: source.recipient_to_name || '',
    recipient_appeal: source.recipient_appeal || '',
    recipient_eio: source.recipient_eio || DEFAULT_RECIPIENT_EIO,
    recipient_genitive_name: source.recipient_genitive_name || '',
    recipient_salutation: source.recipient_salutation || '',
    outgoing_number_suffix: source.outgoing_number_suffix || ''
  })

  const normalizeDraftText = (value) => (
    String(value || '')
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/<\/?(p|div|li|ul|ol|span|strong|em|b|i|u|table|tr|td|th|tbody|thead)[^>]*>/gi, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  )

  const buildDraftComparisonSignature = (source = {}, pendingFileNames = []) => {
    const comparable = buildComparableDraftForm(source)
    return JSON.stringify({
      ...comparable,
      body: normalizeDraftText(comparable.body),
      attachments_list: normalizeDraftText(comparable.attachments_list),
      editor_draft: comparable.editor_draft || null,
      pending_file_names: [...(pendingFileNames || [])].filter(Boolean)
    })
  }

  const hasMeaningfulDraftContent = (draftPayload) => {
    if (!draftPayload) return false
    const comparable = buildComparableDraftForm(draftPayload.form || {})
    const meaningfulFields = [
      comparable.recipient_company_id,
      comparable.deal_id,
      comparable.subject,
      normalizeDraftText(comparable.body),
      normalizeDraftText(comparable.attachments_list),
      comparable.recipient_short_name,
      comparable.recipient_to_name,
      comparable.recipient_appeal,
      comparable.recipient_eio !== DEFAULT_RECIPIENT_EIO ? comparable.recipient_eio : '',
      comparable.recipient_genitive_name,
      comparable.recipient_salutation,
      JSON.stringify(comparable.editor_draft || null)
    ]
    return meaningfulFields.some(Boolean) || (draftPayload.pending_file_names || []).length > 0
  }

  const buildDraftPayload = () => ({
    version: 1,
    document_id: activeDocumentId.value || null,
    saved_at: new Date().toISOString(),
    form: buildComparableDraftForm(form.value),
    pending_file_names: pendingFiles.value.map((file) => file?.name).filter(Boolean)
  })

  const clearDraftNotice = (documentId = activeDocumentId.value) => {
    removeStorageKey(buildDraftNoticeKey(documentId))
    removeStorageKey(buildLegacyDraftNoticeKey(documentId))
  }

  const clearDraftForDocument = (documentId = activeDocumentId.value) => {
    removeStorageKey(buildDraftStorageKey(documentId))
    removeStorageKey(buildLegacyDraftStorageKey(documentId))
    clearDraftNotice(documentId)
    if (!documentId) {
      restoredPendingFileNames.value = []
    }
  }

  const persistDraftNow = () => {
    clearDraftAutosaveTimer()
    if (!isEditing.value || draftSyncSuspended.value) return
    const payload = buildDraftPayload()
    const key = buildDraftStorageKey(payload.document_id)
    if (!hasMeaningfulDraftContent(payload)) {
      clearDraftForDocument(payload.document_id)
      return
    }
    writeStorageJson(key, payload)
  }

  const scheduleDraftPersist = () => {
    if (!isEditing.value || draftSyncSuspended.value) return
    clearDraftAutosaveTimer()
    draftAutosaveTimer = setTimeout(() => {
      persistDraftNow()
    }, OUTGOING_DRAFT_AUTOSAVE_DELAY)
  }

  const maybePromptDraftRestore = (documentId, baseForm) => {
    let draftKey = buildDraftStorageKey(documentId)
    let draft = readStorageJson(draftKey)
    if (!hasMeaningfulDraftContent(draft)) {
      const legacyKey = buildLegacyDraftStorageKey(documentId)
      const legacyDraft = readStorageJson(legacyKey)
      const legacyKind = normalizeDocumentKind(legacyDraft?.form?.document_kind || 'letter')
      if (hasMeaningfulDraftContent(legacyDraft) && legacyKind === activeKind.value) {
        draftKey = legacyKey
        draft = legacyDraft
      }
    }
    if (!hasMeaningfulDraftContent(draft)) {
      removeStorageKey(draftKey)
      clearDraftNotice(documentId)
      return false
    }
    const baseSignature = buildDraftComparisonSignature(baseForm, [])
    const draftSignature = buildDraftComparisonSignature(draft.form, draft.pending_file_names)
    if (baseSignature === draftSignature) {
      clearDraftForDocument(documentId)
      return false
    }
    draftRestoreCandidate.value = draft
    draftRestoreReason.value = (
      readStorageJson(buildDraftNoticeKey(documentId))?.reason ||
      readStorageJson(buildLegacyDraftNoticeKey(documentId))?.reason ||
      ''
    )
    draftRestoreModalOpen.value = true
    return true
  }

  const displayOutgoingNumber = (doc) => {
    if (!doc) return ''
    return doc.outgoing_number_display || doc.outgoing_number || ''
  }

  const upsertDocumentInList = (document) => {
    if (!document?.id) return
    const index = documents.value.findIndex((item) => String(item.id) === String(document.id))
    if (index === -1) {
      documents.value = [document, ...documents.value]
      return
    }
    documents.value.splice(index, 1, { ...documents.value[index], ...document })
  }

  const syncDocumentQuery = (documentId = null) => {
    const nextQuery = { ...route.query }
    if (documentId) nextQuery.document_id = String(documentId)
    else delete nextQuery.document_id
    router.replace({ query: nextQuery }).catch(() => {})
  }

  const loadDocuments = async (params = null) => {
    const requestParams = params || buildParams()
    currentParams.value = requestParams
    loading.value = true
    try {
      const result = await outgoingApi.list(requestParams)
      documents.value = result || []
    } catch (error) {
      console.error('Error loading registry:', error)
      documents.value = []
    } finally {
      loading.value = false
    }
  }

  const nextPage = async () => {
    if (!hasNext.value) return
    page.value += 1
    currentParams.value = buildParams()
    await loadDocuments(currentParams.value)
  }

  const prevPage = async () => {
    if (page.value <= 1) return
    page.value -= 1
    currentParams.value = buildParams()
    await loadDocuments(currentParams.value)
  }

  const loadCompanies = async () => {
    try {
      await companiesStore.ensureLoaded()
      companies.value = companiesStore.items
    } catch (error) {
      console.error('Error loading companies:', error)
    }
  }

  const loadDeals = async () => {
    try {
      // cross-domain endpoint
      const response = await axios.get('/api/v1/deals/')
      deals.value = response.data || []
    } catch (error) {
      console.error('Error loading deals:', error)
    }
  }

  const loadDealContext = async (dealId) => {
    dealContracts.value = []
    dealStages.value = []
    dealPayments.value = []
    dealPaymentUsage.value = {}
    if (!dealId) return
    try {
      const closingParams = activeDocumentId.value ? { exclude_document_id: activeDocumentId.value } : {}
      const [contractsRes, stagesRes, paymentsRes, closingRes] = await Promise.all([
        // cross-domain: contracts, stages, income-expense
        axios.get(`/api/v1/contracts/deal/${dealId}`),
        axios.get(`/api/v1/stages/deal/${dealId}`),
        axios.get('/api/v1/income-expense/', { params: { deal_id: dealId, direction: 'income' } }),
        outgoingApi.getClosingDocuments(dealId, closingParams)
      ])
      dealContracts.value = contractsRes.data || []
      dealStages.value = (stagesRes.data || []).filter((stage) => stage.stage_type !== 'payment')
      dealPayments.value = paymentsRes.data || []
      dealPaymentUsage.value = closingRes?.payment_usage || {}
    } catch (error) {
      console.error('Error loading deal context:', error)
    }
  }

  const selectedRecipient = computed(() => (
    companies.value.find((item) => String(item.id) === String(form.value.recipient_company_id)) || null
  ))

  const recipientBankAccounts = computed(() => {
    const raw = selectedRecipient.value?.bank_accounts || []
    return Array.isArray(raw) ? raw.filter((item) => item && typeof item === 'object') : []
  })

  const bankAccountLabel = (account, index = null) => {
    if (!account) return 'Нет реквизитов'
    const prefix = index !== null ? `${index + 1}. ` : ''
    const bank = account.bank_name || account.bank || 'Банк'
    const rs = account.account_rs || account.rs || account.account || ''
    const bik = account.bik ? `БИК ${account.bik}` : ''
    return [prefix + bank, rs, bik].filter(Boolean).join(' · ')
  }

  const formatMoney = (value) => {
    const amount = Number(value || 0)
    return amount.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₽'
  }

  const getCurrentPaymentLinkAmount = (entryId, currentIndex = -1) => (
    (form.value.linked_payment_items || []).reduce((sum, item, index) => {
      if (index === currentIndex) return sum
      if (String(item.entry_id || '') !== String(entryId || '')) return sum
      return sum + Number(item.amount || 0)
    }, 0)
  )

  const getPaymentAvailableAmount = (payment, currentIndex = -1) => {
    const entryId = String(payment?.id || '')
    const total = Number(payment?.amount || 0)
    const used = Number(dealPaymentUsage.value?.[entryId]?.used_amount || 0)
    const currentFormUsage = getCurrentPaymentLinkAmount(entryId, currentIndex)
    return Math.max(total - used - currentFormUsage, 0)
  }

  const paymentOptionLabel = (payment, currentIndex = -1) => {
    const base = `${formatDate(payment.plan_date)} · ${formatMoney(payment.amount)} · ${payment.category_code || 'без категории'}`
    const available = getPaymentAvailableAmount(payment, currentIndex)
    const used = Number(dealPaymentUsage.value?.[String(payment.id)]?.used_amount || 0)
    return used > 0
      ? `${base} · доступно ${formatMoney(available)}`
      : base
  }

  const addPaymentLink = () => {
    form.value.linked_payment_items.push({ entry_id: '', amount: null, note: '' })
  }

  const removePaymentLink = (index) => {
    form.value.linked_payment_items.splice(index, 1)
  }

  const normalizePersonValue = (value) => {
    if (!value) return ''
    return value.replace(/[.,;]/g, ' ').replace(/\s+/g, ' ').trim()
  }

  const parsePerson = (value) => {
    const cleaned = normalizePersonValue(value)
    if (!cleaned) return { surname: '', name: '', patronymic: '' }
    const parts = cleaned.split(' ')
    return {
      surname: parts[0] || '',
      name: parts[1] || '',
      patronymic: parts[2] || ''
    }
  }

  const buildInitials = (name, patronymic) => {
    const initials = []
    if (name) initials.push(`${name[0].toUpperCase()}.`)
    if (patronymic) initials.push(`${patronymic[0].toUpperCase()}.`)
    return initials.join('')
  }

  const toDativeSurname = (surname) => {
    if (!surname) return ''
    const lower = surname.toLowerCase()
    if (lower.endsWith('ко') || lower.endsWith('их') || lower.endsWith('ых')) return surname
    if (lower.endsWith('ова') || lower.endsWith('ева') || lower.endsWith('ина')) return `${surname.slice(0, -1)}ой`
    if (lower.endsWith('ая')) return `${surname.slice(0, -2)}ой`
    if (lower.endsWith('я')) return `${surname.slice(0, -1)}е`
    if (lower.endsWith('ий')) return `${surname.slice(0, -2)}ию`
    if (lower.endsWith('й')) return `${surname.slice(0, -1)}ю`
    if (lower.endsWith('ь')) return `${surname.slice(0, -1)}ю`
    if (lower.endsWith('а')) return `${surname.slice(0, -1)}е`
    return `${surname}у`
  }

  const toGenitiveSurname = (surname) => {
    if (!surname) return ''
    const lower = surname.toLowerCase()
    if (lower.endsWith('ко') || lower.endsWith('их') || lower.endsWith('ых')) return surname
    if (lower.endsWith('ова') || lower.endsWith('ева') || lower.endsWith('ина')) return `${surname.slice(0, -1)}ой`
    if (lower.endsWith('ая')) return `${surname.slice(0, -2)}ой`
    if (lower.endsWith('ия')) return `${surname.slice(0, -1)}и`
    if (lower.endsWith('я')) return `${surname.slice(0, -1)}и`
    if (lower.endsWith('ий')) return `${surname.slice(0, -2)}ого`
    if (lower.endsWith('й')) return `${surname.slice(0, -1)}я`
    if (lower.endsWith('ь')) return `${surname.slice(0, -1)}я`
    if (lower.endsWith('а')) return `${surname.slice(0, -1)}ы`
    return `${surname}а`
  }

  const buildToName = (person) => {
    if (!person?.surname) return ''
    const initials = buildInitials(person.name, person.patronymic)
    const dativeSurname = toDativeSurname(person.surname)
    return initials ? `${dativeSurname} ${initials}`.trim() : dativeSurname
  }

  const buildGenitiveName = (person) => {
    if (!person?.surname) return ''
    const initials = buildInitials(person.name, person.patronymic)
    const genitiveSurname = toGenitiveSurname(person.surname)
    return initials ? `${genitiveSurname} ${initials}`.trim() : genitiveSurname
  }

  const buildAppeal = (person) => {
    const parts = []
    if (person?.name) parts.push(person.name)
    if (person?.patronymic) parts.push(person.patronymic)
    return parts.join(' ')
  }

  const extractOutgoingSuffix = (value) => {
    if (!value) return ''
    const raw = value.includes(':') ? value.split(':')[1] : value
    const match = raw.match(/^(\d+)[/\\](\d{4}-\d{2})$/)
    return match ? match[2] : ''
  }

  const suffixFromDate = (value) => {
    if (!value) return ''
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return ''
    const month = String(parsed.getMonth() + 1).padStart(2, '0')
    return `${parsed.getFullYear()}-${month}`
  }

  const guessSalutation = (person) => {
    const patronymic = (person?.patronymic || '').toLowerCase()
    const surname = (person?.surname || '').toLowerCase()
    const isFemale = patronymic.endsWith('на') || surname.endsWith('а') || surname.endsWith('я')
    return isFemale ? 'Уважаемая' : 'Уважаемый'
  }

  const fillRecipientFromCompany = () => {
    const company = companies.value.find((item) => item.id === form.value.recipient_company_id)
    if (!company) return
    const shortName = company.short_name || company.shortName || company.name || ''
    const person = parsePerson(company.contact_person || company.contactPerson || '')
    form.value.recipient_short_name = shortName
    if (isLetterKind.value) {
      form.value.recipient_to_name = buildToName(person)
      form.value.recipient_appeal = buildAppeal(person)
      form.value.recipient_salutation = guessSalutation(person)
    } else {
      form.value.recipient_genitive_name = buildGenitiveName(person) || shortName
      form.value.recipient_to_name = ''
      form.value.recipient_appeal = ''
      form.value.recipient_salutation = ''
    }
    if (!form.value.recipient_eio) {
      form.value.recipient_eio = DEFAULT_RECIPIENT_EIO
    }
  }

  const applyDraftRestore = async () => {
    if (!draftRestoreCandidate.value) {
      draftRestoreModalOpen.value = false
      return
    }
    draftSyncSuspended.value = true
    form.value = buildComparableDraftForm(draftRestoreCandidate.value.form || {})
    pendingFiles.value = []
    restoredPendingFileNames.value = [...(draftRestoreCandidate.value.pending_file_names || [])]
    await nextTick()
    setEditableContent(editorRef.value, form.value.body, bodySanitizeConfig)
    setEditableContent(
      attachmentsEditorRef.value,
      attachmentsTextToHtml(form.value.attachments_list || ''),
      attachmentsSanitizeConfig
    )
    refreshToolbarStates()
    draftSyncSuspended.value = false
    draftRestoreModalOpen.value = false
    draftRestoreCandidate.value = null
    draftRestoreReason.value = ''
    scheduleStructuredEditorResolve(0)
    scheduleStructuredLivePreview(0)
    scheduleDraftPersist()
    toastSuccess('Локальный черновик восстановлен')
  }

  const discardDraftRestore = () => {
    clearDraftForDocument(activeDocumentId.value)
    draftRestoreModalOpen.value = false
    draftRestoreCandidate.value = null
    draftRestoreReason.value = ''
    restoredPendingFileNames.value = []
  }

  const selectDocument = async (documentId, options = {}) => {
    const { syncQuery = true, preloaded = null } = options
    persistDraftNow()
    activeDocumentId.value = documentId
    isEditing.value = false
    try {
      const documentData = preloaded || (await outgoingApi.getById(documentId))
      upsertDocumentInList(documentData)
      activeDocument.value = documentData
      versions.value = documentData.versions || []
      files.value = documentData.files || []
      activeKind.value = normalizeDocumentKind(documentData.document_kind || activeKind.value)
      await loadEditorSchema(activeKind.value)
      form.value = buildComparableDraftForm({
        document_kind: documentData.document_kind || activeKind.value,
        editor_mode: documentData.editor_mode || (activeKind.value === 'letter' ? 'classic' : 'structured'),
        editor_schema_version: documentData.editor_schema_version || editorSchemaVersion.value || 1,
        editor_draft: documentData.editor_draft || null,
        editor_validation: documentData.editor_validation || { errors: [], warnings: [] },
        editor_render_context: documentData.editor_render_context || { snapshot_mode: 'live' },
        recipient_company_id: documentData.recipient_company_id || '',
        our_company_key: documentData.our_company_key || form.value.our_company_key || 'normbud',
        deal_id: documentData.deal_id || '',
        contract_id: documentData.contract_id || '',
        letter_date: documentData.letter_date || new Date().toISOString().split('T')[0],
        subject: documentData.subject || '',
        body: documentData.body || '',
        attachments_list: documentData.attachments_list || '',
        bank_account_index: documentData.bank_account_index ?? null,
        linked_stage_ids: documentData.linked_stage_ids || [],
        linked_payment_items: documentData.linked_payment_items || [],
        recipient_short_name: documentData.recipient_short_name || '',
        recipient_to_name: documentData.recipient_to_name || '',
        recipient_appeal: documentData.recipient_appeal || '',
        recipient_eio: documentData.recipient_eio || DEFAULT_RECIPIENT_EIO,
        recipient_genitive_name: documentData.recipient_genitive_name || '',
        recipient_salutation: documentData.recipient_salutation || '',
        outgoing_number_suffix: normalizeDocumentKind(documentData.document_kind) === 'letter'
          ? (extractOutgoingSuffix(documentData.outgoing_number_display || documentData.outgoing_number) || suffixFromDate(documentData.letter_date))
          : ''
      })
      ensureEditorDraft()
      await loadDealContext(form.value.deal_id)
      await loadEditorContext(documentData.id)
      pendingFiles.value = []
      restoredPendingFileNames.value = []
      draftRestoreModalOpen.value = false
      draftRestoreCandidate.value = null
      draftRestoreReason.value = ''
      clearStructuredLivePreview()
      await nextTick()
      await renderPreview(documentData)
      if (syncQuery) syncDocumentQuery(documentId)
    } catch (error) {
      console.error('Error loading document:', error)
    }
  }

  const startNewDocument = () => {
    persistDraftNow()
    draftSyncSuspended.value = true
    activeDocumentId.value = null
    activeDocument.value = {}
    versions.value = []
    files.value = []
    pendingFiles.value = []
    clearPreviewContainer()
    previewReady.value = false
    clearStructuredLivePreview()
    restoredPendingFileNames.value = []
    form.value = {
      ...buildDefaultForm(),
      document_kind: activeKind.value,
      outgoing_number_suffix: activeKind.value === 'letter' ? suffixFromDate(new Date().toISOString().split('T')[0]) : ''
    }
    editorResolvedFields.value = {}
    isEditing.value = true
    syncDocumentQuery(null)
    nextTick(async () => {
      await loadEditorSchema(activeKind.value)
      ensureEditorDraft({ forceDefault: true })
      setEditableContent(editorRef.value, '', bodySanitizeConfig)
      setEditableContent(attachmentsEditorRef.value, '', attachmentsSanitizeConfig)
      draftSyncSuspended.value = false
      scheduleStructuredEditorResolve(0)
      scheduleStructuredLivePreview(0)
      maybePromptDraftRestore(null, form.value)
    })
  }

  const enableEditMode = () => {
    draftSyncSuspended.value = true
    isEditing.value = true
    restoredPendingFileNames.value = []
    nextTick(() => {
      setEditableContent(editorRef.value, form.value.body, bodySanitizeConfig)
      setEditableContent(attachmentsEditorRef.value, attachmentsTextToHtml(form.value.attachments_list || ''), attachmentsSanitizeConfig)
      refreshToolbarStates()
      draftSyncSuspended.value = false
      scheduleStructuredEditorResolve(0)
      scheduleStructuredLivePreview(0)
      maybePromptDraftRestore(activeDocumentId.value, form.value)
    })
  }

  const cancelEdit = async () => {
    clearDraftForDocument(activeDocumentId.value)
    restoredPendingFileNames.value = []
    if (!activeDocumentId.value) {
      if (documents.value.length) selectDocument(documents.value[0].id)
      else isEditing.value = false
    } else {
      isEditing.value = false
      clearStructuredLivePreview()
      form.value.body = activeDocument.value.body || ''
      form.value.attachments_list = activeDocument.value.attachments_list || ''
      await nextTick()
      await renderPreview(activeDocument.value)
    }
  }

  const openDocumentFromQueryOrDefault = async () => {
    const requestedId = route.query.document_id
    if (requestedId) {
      let documentData = documents.value.find((item) => String(item.id) === String(requestedId)) || null
      if (!documentData) {
        try {
          documentData = await outgoingApi.getById(requestedId)
          upsertDocumentInList(documentData)
        } catch (error) {
          console.error('Error loading document from query:', error)
        }
      }
      if (documentData?.id) {
        await selectDocument(documentData.id, { syncQuery: false, preloaded: documentData })
        return
      }
    }
    if (!activeDocumentId.value && documents.value.length) {
      await selectDocument(documents.value[0].id, { syncQuery: false })
    }
  }

  const handleFileChange = (event) => {
    pendingFiles.value = Array.from(event.target.files || [])
    restoredPendingFileNames.value = []
  }

  /**
   * Multipart upload — kept on raw axios to retain onUploadProgress
   * (api/_client.request() does not forward the progress callback).
   */
  const queueAttachments = async (documentId, uploadFiles) => {
    let hasSuccess = false
    for (const file of uploadFiles) {
      const localId = uploadQueue.addLocalUpload({
        fileName: file.name,
        module: 'outgoing_registry',
        entityId: documentId
      })
      try {
        const fd = new FormData()
        fd.append('attachments_files', file)
        const response = await axios.post(`/api/v1/outgoing-registry/${documentId}/attachments`, fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (eventProgress) => {
            if (!eventProgress.total) return
            const progress = (eventProgress.loaded / eventProgress.total) * 100
            uploadQueue.updateProgress(localId, progress)
          }
        })
        uploadQueue.markQueued(localId, response.data)
        hasSuccess = true
      } catch (error) {
        console.error('Error uploading attachment:', error)
        uploadQueue.markError(localId, error?.response?.data?.detail)
      }
    }
    return hasSuccess
  }

  const onListKeydown = (e) => {
    if (!documents.value.length) return
    const currentIdx = documents.value.findIndex(d => d.id === activeDocumentId.value)
    if (e.key === 'ArrowDown' || e.key === 'j') {
      e.preventDefault()
      const nextIdx = Math.min(currentIdx + 1, documents.value.length - 1)
      selectDocument(documents.value[nextIdx].id)
    } else if (e.key === 'ArrowUp' || e.key === 'k') {
      e.preventDefault()
      const prevIdx = Math.max(currentIdx - 1, 0)
      selectDocument(documents.value[prevIdx].id)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (activeDocumentId.value) enableEditMode()
    } else if (e.key === 'Escape') {
      if (isEditing.value) cancelEdit()
    }
  }

  // --- DOCX ENGINE ---
  const stripHtml = (html) => {
    if (!html) return ''
    const tmp = document.createElement('DIV')
    tmp.innerHTML = DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['p', 'div', 'br', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span', 'b', 'i', 'u', 'strong', 'em'],
      ALLOWED_ATTR: ['style', 'colspan', 'rowspan']
    })
      .replace(/<\/p>/gi, '</p>[[NL]]')
      .replace(/<\/div>/gi, '</div>[[NL]]')
      .replace(/<br\s*\/?>/gi, '<br>[[NL]]')
      .replace(/<\/li>/gi, '</li>[[NL]]')
    let text = tmp.innerText || tmp.textContent || ''
    return text.replace(/\[\[NL\]\]/g, '\n')
  }

  const flattenObject = (value, prefix = '', target = {}) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return target
    Object.entries(value).forEach(([key, entry]) => {
      const nextKey = prefix ? `${prefix}.${key}` : key
      if (entry && typeof entry === 'object' && !Array.isArray(entry)) {
        flattenObject(entry, nextKey, target)
        return
      }
      target[nextKey] = entry ?? ''
    })
    return target
  }

  const companyLabel = (key) => {
    const entry = ourCompanies.value.find((item) => item.value === key)
    return entry?.label || 'Письмо'
  }

  const getPreviewTemplateProfile = (key) => previewCompanyProfiles[key] || {
    key: 'default',
    logo: '',
    signature: '',
    infoLines: [companyLabel(key)],
    footerLines: [],
    signerTitle: 'Руководитель',
    signerName: ''
  }

  const resolveTemplateUrl = (docData) => {
    const key = docData?.our_company_key || form.value.our_company_key
    const templateMap = {
      normbud: '/templates/outgoing_normbud.docx',
      bayer: '/templates/outgoing_bayer.docx',
      morozov: '/templates/outgoing_morozov.docx'
    }
    return templateMap[key] || '/templates/template.docx'
  }

  const formatOutgoingNumberForFile = (value) => {
    if (!value) return 'draft'
    const match = value.match(/^(\d+)[/\\](\d{4})-(\d{2})$/)
    if (match) return `${match[1]}_${match[3]}-${match[2]}`
    return value.replace(/[/\\]/g, '_')
  }

  const buildOutgoingFileName = (docData) => {
    const company = companyLabel(docData?.our_company_key || form.value.our_company_key).replace(/\s+/g, '_')
    const numberRaw = docData?.outgoing_number_display || docData?.outgoing_number
    const number = formatOutgoingNumberForFile(numberRaw)
    const kind = documentKindMeta(docData).singular || 'Документ'
    return `${company}_${kind}_${number}`
  }

  const DOCX_BODY_PLACEHOLDER = '__DOCX_BODY_PLACEHOLDER__'

  const xmlEscape = (value = '') => String(value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;')

  const htmlEscape = (value = '') => String(value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  const buildRunPropsXml = (baseRunPropsInner = '', formats = {}) => {
    const extras = []
    if (formats.bold) extras.push('<w:b/>')
    if (formats.italic) extras.push('<w:i/>')
    if (formats.underline) extras.push('<w:u w:val="single"/>')
    return `<w:rPr>${extras.join('')}${baseRunPropsInner}</w:rPr>`
  }

  const DEFAULT_BODY_FIRST_LINE_TWIPS = 709

  const parseCssLengthToTwips = (value) => {
    if (value === null || value === undefined) return null
    const normalized = String(value).trim().toLowerCase().replace(',', '.')
    const match = normalized.match(/^(-?\d+(?:\.\d+)?)(cm|mm|pt|px)?$/)
    if (!match) return null
    const amount = Number(match[1])
    if (!Number.isFinite(amount)) return null
    const unit = match[2] || 'px'
    if (unit === 'cm') return Math.round(amount * 567)
    if (unit === 'mm') return Math.round(amount * 56.7)
    if (unit === 'pt') return Math.round(amount * 20)
    return Math.round(amount * 15)
  }

  const mergeParagraphPropsXml = (baseParagraphPropsXml = '', paragraphOptions = {}) => {
    const hasOverrides = (
      paragraphOptions.firstLineTwips !== undefined ||
      paragraphOptions.leftTwips !== undefined ||
      paragraphOptions.hangingTwips !== undefined ||
      paragraphOptions.justification
    )
    if (!hasOverrides) return baseParagraphPropsXml

    let xml = baseParagraphPropsXml || '<w:pPr></w:pPr>'
    if (paragraphOptions.firstLineTwips !== undefined || paragraphOptions.leftTwips !== undefined || paragraphOptions.hangingTwips !== undefined) {
      xml = xml.replace(/<w:ind\b[^>]*\/>/g, '')
      const attrs = []
      if (paragraphOptions.leftTwips !== undefined && paragraphOptions.leftTwips !== null) attrs.push(`w:left="${paragraphOptions.leftTwips}"`)
      if (paragraphOptions.firstLineTwips !== undefined && paragraphOptions.firstLineTwips !== null) attrs.push(`w:firstLine="${paragraphOptions.firstLineTwips}"`)
      if (paragraphOptions.hangingTwips !== undefined && paragraphOptions.hangingTwips !== null) attrs.push(`w:hanging="${paragraphOptions.hangingTwips}"`)
      if (attrs.length) {
        xml = xml.replace('</w:pPr>', `<w:ind ${attrs.join(' ')}/></w:pPr>`)
      }
    }
    if (paragraphOptions.justification) {
      xml = xml.replace(/<w:jc\b[^>]*\/>/g, '')
      xml = xml.replace('</w:pPr>', `<w:jc w:val="${paragraphOptions.justification}"/></w:pPr>`)
    }
    return xml
  }

  const paragraphOptionsFromNode = (node, fallback = {}) => {
    const options = { ...fallback }
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return options
    const textIndent = parseCssLengthToTwips(node.style?.textIndent)
    if (textIndent !== null) options.firstLineTwips = textIndent
    const textAlign = (node.style?.textAlign || '').trim().toLowerCase()
    if (textAlign === 'justify') options.justification = 'both'
    else if (textAlign === 'center') options.justification = 'center'
    else if (textAlign === 'right' || textAlign === 'end') options.justification = 'right'
    else if (textAlign === 'left' || textAlign === 'start') options.justification = 'left'
    return options
  }

  const trimTrailingParagraphNodes = (nodes) => {
    const clones = Array.from(nodes || []).map((node) => node.cloneNode(true))
    const trimNodeList = (list) => {
      for (let index = list.length - 1; index >= 0; index -= 1) {
        const node = list[index]
        if (!node) continue
        if (node.nodeType === Node.TEXT_NODE) {
          const nextText = (node.textContent || '').replace(/[\s ]+$/g, '')
          node.textContent = nextText
          if (!nextText.length) { node.remove(); continue }
          break
        }
        if (node.nodeType !== Node.ELEMENT_NODE) { node.remove(); continue }
        const tag = node.tagName.toLowerCase()
        if (tag === 'br') { node.remove(); continue }
        trimNodeList(Array.from(node.childNodes || []))
        const remainingText = (node.textContent || '').replace(/[\s ]+/g, '')
        const hasBreak = !!node.querySelector?.('br')
        if (!remainingText.length && !hasBreak) { node.remove(); continue }
        break
      }
    }
    trimNodeList(clones)
    return clones
  }

  const buildTextRunsXml = (text = '', baseRunPropsInner = '', formats = {}) => {
    const normalized = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    const segments = normalized.split('\n')
    return segments.map((segment, index) => {
      const parts = segment.split('\t')
      const runParts = []
      if (parts.length === 1 && parts[0] === '') {
        runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:t xml:space="preserve"></w:t></w:r>`)
      } else {
        parts.forEach((part, partIndex) => {
          if (part.length > 0) {
            const preserve = /^\s|\s$| {2,}/.test(part)
            runParts.push(
              `<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:t${preserve ? ' xml:space="preserve"' : ''}>${xmlEscape(part)}</w:t></w:r>`
            )
          }
          if (partIndex < parts.length - 1) {
            runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:tab/></w:r>`)
          }
        })
      }
      if (index < segments.length - 1) {
        runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:br/></w:r>`)
      }
      return runParts.join('')
    }).join('')
  }

  const buildRunsFromDomNode = (node, baseRunPropsInner = '', formats = {}) => {
    if (!node) return ''
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent || ''
      return text ? buildTextRunsXml(text, baseRunPropsInner, formats) : ''
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return ''
    const tag = node.tagName.toLowerCase()
    if (tag === 'br') {
      return `<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:br/></w:r>`
    }
    const nextFormats = { ...formats }
    if (tag === 'b' || tag === 'strong' || Number(node.style?.fontWeight || 400) >= 600) nextFormats.bold = true
    if (tag === 'i' || tag === 'em' || node.style?.fontStyle === 'italic') nextFormats.italic = true
    if (tag === 'u' || (node.style?.textDecoration || '').includes('underline')) nextFormats.underline = true
    return Array.from(node.childNodes || []).map((child) => buildRunsFromDomNode(child, baseRunPropsInner, nextFormats)).join('')
  }

  const buildParagraphXml = (runsXml, baseParagraphPropsXml = '', baseRunPropsInner = '', paragraphOptions = {}) => {
    const safeRuns = runsXml && runsXml.trim()
      ? runsXml
      : `<w:r>${buildRunPropsXml(baseRunPropsInner)}<w:t xml:space="preserve"></w:t></w:r>`
    return `<w:p>${mergeParagraphPropsXml(baseParagraphPropsXml, paragraphOptions)}${safeRuns}</w:p>`
  }

  const buildParagraphFromNodes = (nodes, baseParagraphPropsXml = '', baseRunPropsInner = '', prefix = '', paragraphOptions = {}) => {
    const sanitizedNodes = trimTrailingParagraphNodes(nodes)
    const bodyRuns = sanitizedNodes.map((node) => buildRunsFromDomNode(node, baseRunPropsInner)).join('')
    const prefixRuns = prefix ? buildTextRunsXml(prefix, baseRunPropsInner) : ''
    return buildParagraphXml(`${prefixRuns}${bodyRuns}`.trim(), baseParagraphPropsXml, baseRunPropsInner, paragraphOptions)
  }

  const buildCellParagraphsXml = (cell, baseParagraphPropsXml = '', baseRunPropsInner = '') => {
    const tableParagraphOptions = { firstLineTwips: 0 }
    const directBlocks = Array.from(cell.childNodes || []).filter((node) => (
      node.nodeType === Node.ELEMENT_NODE && ['p', 'div', 'ul', 'ol', 'table'].includes(node.tagName.toLowerCase())
    ))
    if (!directBlocks.length) {
      return buildParagraphFromNodes(cell.childNodes, baseParagraphPropsXml, baseRunPropsInner, '', tableParagraphOptions)
    }
    const fragments = []
    directBlocks.forEach((node) => {
      const tag = node.tagName.toLowerCase()
      if (tag === 'p' || tag === 'div') {
        fragments.push(buildParagraphFromNodes(node.childNodes, baseParagraphPropsXml, baseRunPropsInner, '', tableParagraphOptions))
        return
      }
      if (tag === 'ul' || tag === 'ol') {
        Array.from(node.children || []).forEach((child, index) => {
          const prefix = tag === 'ol' ? `${index + 1}. ` : '• '
          fragments.push(buildParagraphFromNodes(child.childNodes, baseParagraphPropsXml, baseRunPropsInner, prefix, tableParagraphOptions))
        })
      }
    })
    return fragments.join('') || buildParagraphXml('', baseParagraphPropsXml, baseRunPropsInner, tableParagraphOptions)
  }

  const buildTableXml = (table, baseParagraphPropsXml = '', baseRunPropsInner = '') => {
    const rows = Array.from(table.rows || [])
    if (!rows.length) return ''
    const columnCount = Math.max(
      ...rows.map((row) => Array.from(row.cells || []).reduce((sum, cell) => sum + Math.max(1, Number(cell.colSpan || 1)), 0)),
      1
    )
    const usableWidth = 9000
    const cellWidth = Math.floor(usableWidth / columnCount)
    const gridColsXml = Array.from({ length: columnCount }, () => `<w:gridCol w:w="${cellWidth}"/>`).join('')
    const rowsXml = rows.map((row) => {
      const rowCellsXml = Array.from(row.cells || []).map((cell) => {
        const tag = cell.tagName.toLowerCase()
        const colspan = Math.max(1, Number(cell.colSpan || 1))
        const width = cellWidth * colspan
        const cellBlocks = buildCellParagraphsXml(cell, baseParagraphPropsXml, baseRunPropsInner)
        const shd = tag === 'th' ? '<w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/>' : ''
        const gridSpan = colspan > 1 ? `<w:gridSpan w:val="${colspan}"/>` : ''
        return `
          <w:tc>
            <w:tcPr>
              <w:tcW w:w="${width}" w:type="dxa"/>
              ${gridSpan}
              <w:vAlign w:val="top"/>
              ${shd}
            </w:tcPr>
            ${cellBlocks}
          </w:tc>
        `
      }).join('')
      return `<w:tr>${rowCellsXml}</w:tr>`
    }).join('')

    return `
      <w:tbl>
        <w:tblPr>
          <w:tblW w:w="0" w:type="auto"/>
          <w:tblLayout w:type="fixed"/>
          <w:tblBorders>
            <w:top w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/>
            <w:left w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/>
            <w:bottom w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/>
            <w:right w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/>
            <w:insideH w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/>
            <w:insideV w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/>
          </w:tblBorders>
        </w:tblPr>
        <w:tblGrid>${gridColsXml}</w:tblGrid>
        ${rowsXml}
      </w:tbl>
    `.replace(/\n\s+/g, '')
  }

  const buildWordBodyXml = (html, baseParagraphPropsXml = '', baseRunPropsInner = '') => {
    const wrapper = document.createElement('div')
    wrapper.innerHTML = DOMPurify.sanitize(html || '', bodySanitizeConfig)
    const blocks = []
    const blockTags = ['p', 'div', 'ul', 'ol', 'table']
    const defaultParagraphOptions = { firstLineTwips: DEFAULT_BODY_FIRST_LINE_TWIPS, justification: 'both' }

    const pushParagraphFromNode = (node, prefix = '', paragraphOptions = defaultParagraphOptions) => {
      blocks.push(buildParagraphFromNodes(node.childNodes || [], baseParagraphPropsXml, baseRunPropsInner, prefix, paragraphOptions))
    }

    const appendBlockNode = (node) => {
      if (!node) return
      if (node.nodeType === Node.TEXT_NODE) {
        if ((node.textContent || '').trim()) {
          blocks.push(buildParagraphXml(buildTextRunsXml(node.textContent || '', baseRunPropsInner), baseParagraphPropsXml, baseRunPropsInner, defaultParagraphOptions))
        }
        return
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return
      const tag = node.tagName.toLowerCase()
      if (tag === 'table') { blocks.push(buildTableXml(node, baseParagraphPropsXml, baseRunPropsInner)); return }
      if (tag === 'ul' || tag === 'ol') {
        Array.from(node.children || []).forEach((child, index) => {
          const prefix = tag === 'ol' ? `${index + 1}. ` : '• '
          pushParagraphFromNode(child, prefix, { firstLineTwips: 0 })
        })
        return
      }
      if (tag === 'p') { pushParagraphFromNode(node, '', paragraphOptionsFromNode(node, defaultParagraphOptions)); return }
      if (tag === 'div') {
        const hasBlockChildren = Array.from(node.childNodes || []).some((child) => (
          child.nodeType === Node.ELEMENT_NODE && blockTags.includes(child.tagName.toLowerCase())
        ))
        if (!hasBlockChildren) {
          pushParagraphFromNode(node, '', paragraphOptionsFromNode(node, defaultParagraphOptions))
          return
        }
        Array.from(node.childNodes || []).forEach((child) => {
          if (child.nodeType === Node.TEXT_NODE && (child.textContent || '').trim()) {
            blocks.push(buildParagraphXml(buildTextRunsXml(child.textContent || '', baseRunPropsInner), baseParagraphPropsXml, baseRunPropsInner, defaultParagraphOptions))
            return
          }
          appendBlockNode(child)
        })
        return
      }
      blocks.push(buildParagraphFromNodes([node], baseParagraphPropsXml, baseRunPropsInner, '', defaultParagraphOptions))
    }

    Array.from(wrapper.childNodes || []).forEach((node) => appendBlockNode(node))

    if (!blocks.length) {
      blocks.push(buildParagraphXml('', baseParagraphPropsXml, baseRunPropsInner, defaultParagraphOptions))
    }
    return blocks.join('')
  }

  const injectRichBodyIntoDocxZip = (zip, html) => {
    const xmlPath = 'word/document.xml'
    const xml = zip.file(xmlPath)?.asText()
    if (!xml) return
    const placeholderIndex = xml.indexOf(DOCX_BODY_PLACEHOLDER)
    if (placeholderIndex === -1) return
    const paragraphStartWithAttrs = xml.lastIndexOf('<w:p ', placeholderIndex)
    const paragraphStartBare = xml.lastIndexOf('<w:p>', placeholderIndex)
    const paragraphStart = Math.max(paragraphStartWithAttrs, paragraphStartBare)
    const paragraphEndMarker = xml.indexOf('</w:p>', placeholderIndex)
    if (paragraphStart === -1 || paragraphEndMarker === -1) return
    const paragraphEnd = paragraphEndMarker + '</w:p>'.length
    const placeholderParagraphXml = xml.slice(paragraphStart, paragraphEnd)
    const pPrMatch = placeholderParagraphXml.match(/<w:pPr>[\s\S]*?<\/w:pPr>/)
    const rPrMatch = placeholderParagraphXml.match(/<w:rPr>([\s\S]*?)<\/w:rPr>/)
    const richBodyXml = buildWordBodyXml(html, pPrMatch ? pPrMatch[0] : '', rPrMatch ? rPrMatch[1] : '')
    zip.file(xmlPath, `${xml.slice(0, paragraphStart)}${richBodyXml}${xml.slice(paragraphEnd)}`)
  }

  const validateDocxDocumentXml = (zip) => {
    const xml = zip.file('word/document.xml')?.asText()
    if (!xml) return false
    try {
      const parsed = new DOMParser().parseFromString(xml, 'application/xml')
      return !parsed.querySelector('parsererror')
    } catch (error) {
      console.error('DOCX XML Validation Error:', error)
      return false
    }
  }

  const normalizeFloatingPictureLayers = (zip) => {
    const xmlPath = 'word/document.xml'
    const xml = zip.file(xmlPath)?.asText()
    if (!xml) return
    const nextXml = xml.replace(/<wp:anchor\b[\s\S]*?<\/wp:anchor>/g, (anchorXml) => {
      if (!anchorXml.includes('drawingml/2006/picture')) return anchorXml
      return anchorXml
        .replace(/\sbehindDoc="1"/, ' behindDoc="0"')
        .replace(/\srelativeHeight="\d+"/, ' relativeHeight="251659264"')
    })
    if (nextXml !== xml) zip.file(xmlPath, nextXml)
  }

  const normalizeInlineHtmlForDocx = (nodes, formats = {}) => {
    return Array.from(nodes || []).map((node) => {
      if (!node) return ''
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent || ''
        return htmlEscape(text)
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return ''
      const tag = node.tagName.toLowerCase()
      if (tag === 'br') return '<br>'
      const nextFormats = { ...formats }
      if (tag === 'b' || tag === 'strong' || Number(node.style?.fontWeight || 400) >= 600) nextFormats.bold = true
      if (tag === 'i' || tag === 'em' || node.style?.fontStyle === 'italic') nextFormats.italic = true
      if (tag === 'u' || (node.style?.textDecoration || '').includes('underline')) nextFormats.underline = true
      let inner = normalizeInlineHtmlForDocx(node.childNodes || [], nextFormats)
      if (!inner) return ''
      if (nextFormats.underline && !formats.underline) inner = `<u>${inner}</u>`
      if (nextFormats.italic && !formats.italic) inner = `<em>${inner}</em>`
      if (nextFormats.bold && !formats.bold) inner = `<strong>${inner}</strong>`
      return inner
    }).join('')
  }

  const normalizeTableHtmlForDocx = (table) => {
    const rows = Array.from(table.rows || [])
    if (!rows.length) return ''
    const rowsHtml = rows.map((row) => {
      const cellsHtml = Array.from(row.cells || []).map((cell) => {
        const tag = cell.tagName.toLowerCase() === 'th' ? 'th' : 'td'
        const attrs = []
        if (cell.colSpan && Number(cell.colSpan) > 1) attrs.push(`colspan="${Number(cell.colSpan)}"`)
        if (cell.rowSpan && Number(cell.rowSpan) > 1) attrs.push(`rowspan="${Number(cell.rowSpan)}"`)
        const content = normalizeInlineHtmlForDocx(cell.childNodes || []) || '&nbsp;'
        return `<${tag}${attrs.length ? ` ${attrs.join(' ')}` : ''}>${content}</${tag}>`
      }).join('')
      return `<tr>${cellsHtml}</tr>`
    }).join('')
    return `<table>${rowsHtml}</table>`
  }

  const normalizeHtmlForDocx = (html) => {
    const wrapper = document.createElement('div')
    wrapper.innerHTML = DOMPurify.sanitize(html || '', bodySanitizeConfig)
    const blockTags = ['p', 'div', 'ul', 'ol', 'table']
    const blocks = []
    const pushParagraph = (nodes) => {
      const inline = normalizeInlineHtmlForDocx(nodes || [])
      if (inline.trim()) blocks.push(`<p>${inline}</p>`)
    }
    Array.from(wrapper.childNodes || []).forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        if ((node.textContent || '').trim()) pushParagraph([node])
        return
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return
      const tag = node.tagName.toLowerCase()
      if (tag === 'table') { blocks.push(normalizeTableHtmlForDocx(node)); return }
      if (tag === 'ul' || tag === 'ol') {
        const items = Array.from(node.children || []).map((child) => `<li>${normalizeInlineHtmlForDocx(child.childNodes || []) || '&nbsp;'}</li>`).join('')
        if (items) blocks.push(`<${tag}>${items}</${tag}>`)
        return
      }
      if (tag === 'p') { pushParagraph(node.childNodes || []); return }
      if (tag === 'div') {
        const hasBlockChildren = Array.from(node.childNodes || []).some((child) => (
          child.nodeType === Node.ELEMENT_NODE && blockTags.includes(child.tagName.toLowerCase())
        ))
        if (hasBlockChildren) {
          Array.from(node.childNodes || []).forEach((child) => {
            if (child.nodeType === Node.TEXT_NODE && (child.textContent || '').trim()) {
              pushParagraph([child])
            } else if (child.nodeType === Node.ELEMENT_NODE) {
              const childTag = child.tagName.toLowerCase()
              if (childTag === 'table') blocks.push(normalizeTableHtmlForDocx(child))
              else if (childTag === 'ul' || childTag === 'ol') {
                const items = Array.from(child.children || []).map((item) => `<li>${normalizeInlineHtmlForDocx(item.childNodes || []) || '&nbsp;'}</li>`).join('')
                if (items) blocks.push(`<${childTag}>${items}</${childTag}>`)
              } else {
                pushParagraph(child.childNodes || [])
              }
            }
          })
        } else {
          pushParagraph(node.childNodes || [])
        }
        return
      }
      pushParagraph([node])
    })
    return blocks.join('') || `<p>${htmlEscape(stripHtml(html || ''))}</p>`
  }

  const plainTextHtmlForDocx = (html) => {
    const text = stripHtml(html || '')
    const paragraphs = text.split(/\n{2,}/).map((item) => item.trim()).filter(Boolean)
    if (!paragraphs.length) return '<p></p>'
    return paragraphs.map((item) => `<p>${htmlEscape(item).replace(/\n/g, '<br>')}</p>`).join('')
  }

  const generateDocxBlob = async (docData) => {
    try {
      // static template asset — direct fetch
      const response = await axios.get(resolveTemplateUrl(docData), { responseType: 'arraybuffer' })
      const bodyText = stripHtml(docData.body || '')
      const bodyLines = [{ text: DOCX_BODY_PLACEHOLDER }]
      const attachmentsText = (docData.attachments_list || '').toString()
      const attachmentsLines = attachmentsText.split('\n').map(line => line.trim()).filter(line => line.length > 0).map(line => ({ text: line }))
      const recipientShortName = docData.recipient_short_name || ''
      const recipientToName = docData.recipient_to_name || ''
      const recipientAppeal = docData.recipient_appeal || ''
      const recipientEio = docData.recipient_eio || ''
      const recipientSalutation = docData.recipient_salutation || ''
      const recipientSalutationFull = `${recipientSalutation} ${recipientAppeal}`.trim()
      const renderTemplateZip = () => {
        const zip = new PizZip(response.data)
        const doc = new Docxtemplater(zip, {
          paragraphLoop: true,
          linebreaks: true,
          nullGetter: () => '',
        })
        doc.render({
          ...flattenObject(docData),
          ...docData,
          outgoing_number: docData.outgoing_number || '',
          letter_date: formatDateLong(docData.letter_date),
          subject: docData.subject || '',
          body: bodyText,
          body_lines: bodyLines,
          recipient_company_name: docData.recipient_company_name || '',
          recipient_short_name: recipientShortName,
          recipient_to_name: recipientToName,
          recipient_appeal: recipientAppeal,
          recipient_eio: recipientEio,
          recipient_salutation: recipientSalutation,
          recipient_salutation_full: recipientSalutationFull,
          attachments_list: attachmentsText,
          attachments_lines: attachmentsLines
        })
        return doc.getZip()
      }
      const bodyCandidates = [
        normalizeHtmlForDocx(docData.body || ''),
        plainTextHtmlForDocx(docData.body || '')
      ].filter((value, index, list) => value && list.indexOf(value) === index)

      for (let index = 0; index < bodyCandidates.length; index += 1) {
        const renderedZip = renderTemplateZip()
        injectRichBodyIntoDocxZip(renderedZip, bodyCandidates[index])
        normalizeFloatingPictureLayers(renderedZip)
        if (!validateDocxDocumentXml(renderedZip)) {
          if (index < bodyCandidates.length - 1) {
            console.warn('DOCX body fallback retry', { attempt: index + 1 })
            continue
          }
          console.error('DOCX Generation Error: invalid XML after all fallbacks')
          return null
        }
        return renderedZip.generate({
          type: 'blob',
          mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        })
      }
      return null
    } catch (error) {
      console.error('DOCX Generation Error:', error)
      return null
    }
  }

  const revokePreviewPdfUrl = () => {
    if (!previewPdfBaseUrl.value) return
    URL.revokeObjectURL(previewPdfBaseUrl.value)
    previewPdfBaseUrl.value = ''
  }

  const clearPreviewContainer = () => { revokePreviewPdfUrl() }

  const revokeStructuredPreviewPdfUrl = () => {
    if (!liveStructuredPreviewPdfUrl.value) return
    URL.revokeObjectURL(liveStructuredPreviewPdfUrl.value)
    liveStructuredPreviewPdfUrl.value = ''
  }

  const clearStructuredPreviewDocx = () => {
    if (liveStructuredPreviewDocxRef.value) {
      liveStructuredPreviewDocxRef.value.innerHTML = ''
    }
  }

  const clearStructuredLivePreview = () => {
    revokeStructuredPreviewPdfUrl()
    clearStructuredPreviewDocx()
    liveStructuredPreviewError.value = ''
  }

  const clearStructuredLivePreviewTimer = () => {
    if (!liveStructuredPreviewTimer) return
    clearTimeout(liveStructuredPreviewTimer)
    liveStructuredPreviewTimer = null
  }

  const renderStructuredPreviewDocx = async (blob) => {
    if (!liveStructuredPreviewDocxRef.value) return
    clearStructuredPreviewDocx()
    await renderDocxAsync(blob, liveStructuredPreviewDocxRef.value, liveStructuredPreviewDocxRef.value, {
      className: 'docx', inWrapper: true, ignoreWidth: false, ignoreHeight: false, breakPages: true,
    })
  }

  const readBlobErrorMessage = async (error, fallback = 'Не удалось сформировать live preview') => {
    const responseData = error?.response?.data
    if (!responseData) return fallback
    if (typeof responseData === 'string') return responseData || fallback
    if (responseData instanceof Blob) {
      try {
        const text = await responseData.text()
        if (!text) return fallback
        try {
          const parsed = JSON.parse(text)
          return parsed?.detail || parsed?.message || text || fallback
        } catch {
          return text || fallback
        }
      } catch {
        return fallback
      }
    }
    return responseData?.detail || responseData?.message || fallback
  }

  const requestStructuredLivePreview = async (format = liveStructuredPreviewMode.value) => {
    if (!canRenderStructuredPreview.value) {
      clearStructuredLivePreview()
      return
    }
    const requestSeq = ++liveStructuredPreviewRequestSeq
    liveStructuredPreviewLoading.value = true
    liveStructuredPreviewError.value = ''
    try {
      const response = await outgoingApi.editorPreview(format, buildEditorResolvePayload())
      if (requestSeq !== liveStructuredPreviewRequestSeq) return
      if (format === 'pdf') {
        clearStructuredPreviewDocx()
        revokeStructuredPreviewPdfUrl()
        liveStructuredPreviewPdfUrl.value = URL.createObjectURL(response.data)
      } else {
        revokeStructuredPreviewPdfUrl()
        await nextTick()
        await renderStructuredPreviewDocx(response.data)
      }
    } catch (error) {
      if (requestSeq !== liveStructuredPreviewRequestSeq) return
      clearStructuredLivePreview()
      liveStructuredPreviewError.value = await readBlobErrorMessage(error)
    } finally {
      if (requestSeq === liveStructuredPreviewRequestSeq) {
        liveStructuredPreviewLoading.value = false
      }
    }
  }

  const refreshStructuredLivePreview = async () => {
    await requestStructuredLivePreview(liveStructuredPreviewMode.value)
  }

  const scheduleStructuredLivePreview = (delay = 700) => {
    clearStructuredLivePreviewTimer()
    if (!canRenderStructuredPreview.value) {
      clearStructuredLivePreview()
      return
    }
    liveStructuredPreviewTimer = setTimeout(() => {
      requestStructuredLivePreview(liveStructuredPreviewMode.value)
    }, delay)
  }

  const setStructuredPreviewMode = (mode) => {
    if (liveStructuredPreviewMode.value === mode) return
    liveStructuredPreviewMode.value = mode
  }

  const hasCurrentRender = (docData) => {
    const fileList = Array.isArray(docData?.files) ? docData.files : []
    return (
      fileList.some((item) => !item.version_id && item.file_type === 'render_docx') &&
      fileList.some((item) => !item.version_id && item.file_type === 'render_pdf')
    )
  }

  const buildRenderSignature = (docData) => JSON.stringify({
    document_kind: docData?.document_kind || 'letter',
    outgoing_number: docData?.outgoing_number || docData?.outgoing_number_display || '',
    letter_date: docData?.letter_date || '',
    subject: docData?.subject || '',
    body: docData?.body || '',
    attachments_list: docData?.attachments_list || '',
    recipient_company_id: docData?.recipient_company_id || '',
    recipient_short_name: docData?.recipient_short_name || '',
    recipient_to_name: docData?.recipient_to_name || '',
    recipient_appeal: docData?.recipient_appeal || '',
    recipient_eio: docData?.recipient_eio || '',
    recipient_genitive_name: docData?.recipient_genitive_name || '',
    recipient_salutation: docData?.recipient_salutation || '',
    our_company_key: docData?.our_company_key || 'normbud',
    deal_id: docData?.deal_id || '',
    contract_id: docData?.contract_id || '',
    bank_account_index: docData?.bank_account_index ?? null,
    linked_stage_ids: docData?.linked_stage_ids || [],
    linked_payment_items: docData?.linked_payment_items || []
  })

  const shouldRegenerateRender = (beforeDoc, afterDoc) => (
    buildRenderSignature(beforeDoc) !== buildRenderSignature(afterDoc)
  )

  const syncCurrentRender = async (docData, options = {}) => {
    const { silent = false } = options
    if (!docData?.id) return docData
    try {
      const updated = await outgoingApi.generateRenderCache(docData.id)
      upsertDocumentInList(updated)
      if (String(activeDocumentId.value) === String(updated.id)) {
        activeDocument.value = updated
        versions.value = updated.versions || []
        files.value = updated.files || []
      }
      return updated
    } catch (serverError) {
      console.warn('Server render cache generation failed, falling back to client DOCX render', serverError)
    }
    const docxBlob = await generateDocxBlob(docData)
    if (!docxBlob) {
      if (!silent) toastError('Не удалось сформировать Word-файл')
      return null
    }
    const payload = new FormData()
    payload.append(
      'file',
      new File(
        [docxBlob],
        `${buildOutgoingFileName(docData)}.docx`,
        { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
      )
    )
    const updated = await outgoingApi.uploadRenderCache(docData.id, payload)
    upsertDocumentInList(updated)
    if (String(activeDocumentId.value) === String(updated.id)) {
      activeDocument.value = updated
      versions.value = updated.versions || []
      files.value = updated.files || []
    }
    return updated
  }

  const renderPreview = async (docData) => {
    clearPreviewContainer()
    previewReady.value = false
    previewScale.value = previewMode.value === 'fit-page' ? 0.9 : 1
    if (!docData) {
      previewLoading.value = false
      return
    }
    previewLoading.value = true
    try {
      const response = await outgoingApi.previewPdf(docData.id)
      previewPdfBaseUrl.value = URL.createObjectURL(response.data)
      previewReady.value = true
    } catch (err) {
      console.error('DOCX Preview Error:', err)
      toastError('Не удалось сформировать предпросмотр из шаблона Word')
    } finally {
      previewLoading.value = false
    }
  }

  const refreshPreview = async () => {
    const docData = activeDocument.value
    if (!docData?.id) return
    previewLoading.value = true
    try {
      const syncedDocument = await syncCurrentRender(docData, { silent: false })
      const effectiveDocument = syncedDocument || docData
      if (syncedDocument) {
        activeDocument.value = effectiveDocument
        versions.value = effectiveDocument.versions || []
        files.value = effectiveDocument.files || []
      }
      await renderPreview(effectiveDocument)
    } finally {
      previewLoading.value = false
    }
  }

  const applyPreviewScale = () => {
    previewScale.value = previewMode.value === 'fit-page' ? 0.9 : 1
  }

  const setPreviewMode = (mode) => { previewMode.value = mode }

  const downloadDocx = async () => {
    if (!activeDocumentId.value) return
    try {
      await downloadFromApi(
        outgoingApi.renderDocxUrl(activeDocumentId.value),
        {},
        `${buildOutgoingFileName(activeDocument.value)}.docx`,
        { module: 'outgoing_registry', entityId: activeDocumentId.value }
      )
    } catch (error) {
      console.error('DOCX Generation Error:', error)
      toastError('Не удалось сформировать Word-файл')
    }
  }

  const downloadOutgoingVersion = async (version) => {
    if (!version) return
    const fallbackName = version.outgoing_number ? `Letter_${version.outgoing_number}.pdf` : 'document.pdf'
    if (version.pdf_path) {
      try {
        await downloadFromPath(version.pdf_path, fallbackName)
        return
      } catch (e) { console.error(e) }
    }
    if (version.pdf_public_url) {
      await downloadFromHref(version.pdf_public_url, fallbackName)
    }
  }

  const getVersionFile = (versionId, type) => {
    if (!versionId) return null
    return (files.value || []).find((item) => item.version_id === versionId && item.file_type === type) || null
  }

  const downloadOutgoingVersionFile = async (version, type) => {
    if (!version) return
    const file = getVersionFile(version.id, type)
    if (file) {
      await downloadOutgoingFile(file)
      return
    }
    if (type === 'pdf') {
      await downloadOutgoingVersion(version)
    }
  }

  const downloadOutgoingFile = async (item) => {
    if (!item) return
    const fallbackName = item.file_name || item.file_type || 'file'
    if (item.file_path) {
      try {
        await downloadFromPath(item.file_path, fallbackName)
        return
      } catch (e) { console.error(e) }
    }
    if (item.public_url) {
      await downloadFromHref(item.public_url, fallbackName)
    }
  }

  // --- Rich Text Editor ---
  const bodySanitizeConfig = {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li', 'div', 'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td'],
    ALLOWED_ATTR: ['style', 'colspan', 'rowspan']
  }
  const attachmentsSanitizeConfig = {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li', 'div', 'span'],
    ALLOWED_ATTR: ['style']
  }
  const editableBlockTags = new Set(['P', 'DIV', 'UL', 'OL', 'TABLE'])

  const normalizeEditableHtmlForDisplay = (html, sanitizeConfig) => {
    const source = document.createElement('div')
    source.innerHTML = DOMPurify.sanitize(html || '', sanitizeConfig)
    const result = document.createElement('div')
    let pendingInlineNodes = []
    const hasNestedBlockChildren = (node) => Array.from(node.childNodes || []).some(
      (child) => child.nodeType === Node.ELEMENT_NODE && editableBlockTags.has(child.tagName.toUpperCase())
    )
    const flushInlineNodes = () => {
      if (!pendingInlineNodes.length) return
      const paragraph = document.createElement('p')
      pendingInlineNodes.forEach((node) => paragraph.appendChild(node))
      if (!paragraph.childNodes.length) paragraph.innerHTML = '<br>'
      result.appendChild(paragraph)
      pendingInlineNodes = []
    }
    const consumeNode = (node) => {
      if (!node) return
      if (node.nodeType === Node.TEXT_NODE) {
        if ((node.textContent || '').trim()) pendingInlineNodes.push(node.cloneNode(true))
        return
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return
      const tagName = node.tagName.toUpperCase()
      if (tagName === 'BR') { pendingInlineNodes.push(node.cloneNode(true)); return }
      if (tagName === 'P') { flushInlineNodes(); result.appendChild(node.cloneNode(true)); return }
      if (tagName === 'DIV') {
        flushInlineNodes()
        if (hasNestedBlockChildren(node)) {
          Array.from(node.childNodes || []).forEach((child) => consumeNode(child))
        } else {
          const paragraph = document.createElement('p')
          if (node.hasAttribute('style')) paragraph.setAttribute('style', node.getAttribute('style'))
          paragraph.innerHTML = node.innerHTML || '<br>'
          result.appendChild(paragraph)
        }
        return
      }
      if (tagName === 'UL' || tagName === 'OL' || tagName === 'TABLE') {
        flushInlineNodes()
        result.appendChild(node.cloneNode(true))
        return
      }
      pendingInlineNodes.push(node.cloneNode(true))
    }
    Array.from(source.childNodes || []).forEach((node) => consumeNode(node))
    flushInlineNodes()
    return result.innerHTML || '<p><br></p>'
  }

  const setEditableContent = (target, html, sanitizeConfig) => {
    if (!target) return
    target.innerHTML = normalizeEditableHtmlForDisplay(html, sanitizeConfig)
  }

  const normalizeEditableDom = (target, sanitizeConfig) => {
    if (!target) return
    const normalized = normalizeEditableHtmlForDisplay(target.innerHTML, sanitizeConfig)
    if (target.innerHTML !== normalized) target.innerHTML = normalized
  }

  const INTRO_PARAGRAPH_REGEX = /^между .+ и .+ заключен договор .+ на выполнение работ по объекту /i

  const normalizeIntroText = (value) => (
    String(value || '').toLowerCase().replace(/[«»"""""]/g, ' ').replace(/\s+/g, ' ').trim()
  )

  const isGeneratedIntroParagraph = (node) => {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return false
    if (!editableBlockTags.has(node.tagName?.toUpperCase?.())) return false
    return INTRO_PARAGRAPH_REGEX.test(normalizeIntroText(node.textContent || ''))
  }

  const buildIntroParagraphNode = (text) => {
    const paragraph = document.createElement('p')
    paragraph.textContent = text
    paragraph.style.textIndent = '1.25cm'
    paragraph.style.marginTop = '0'
    paragraph.style.marginBottom = '0'
    return paragraph
  }

  const upsertIntroParagraphIntoEditor = (text) => {
    if (!editorRef.value || !text) return
    const editor = editorRef.value
    Array.from(editor.childNodes || [])
      .filter((node) => isGeneratedIntroParagraph(node))
      .forEach((node) => node.remove())
    const introParagraph = buildIntroParagraphNode(text)
    const insertBeforeNode = Array.from(editor.childNodes || []).find((node) => {
      if (node.nodeType === Node.TEXT_NODE) return Boolean((node.textContent || '').trim())
      return node.nodeType === Node.ELEMENT_NODE
    })
    editor.insertBefore(introParagraph, insertBeforeNode || null)
    syncBodyFromEditor()
    captureEditorSelection()
    refreshToolbarStates()
  }

  const insertIntroParagraph = async () => {
    if (!form.value.deal_id) {
      toastError('Выберите сделку для вводного абзаца')
      return
    }
    if (!form.value.recipient_company_id && !form.value.recipient_short_name) {
      toastError('Заполните получателя или его краткое наименование')
      return
    }
    introParagraphBusy.value = true
    try {
      const result = await outgoingApi.getDealIntro(form.value.deal_id, {
        our_company_key: form.value.our_company_key,
        recipient_short_name: form.value.recipient_short_name || '',
        recipient_company_id: form.value.recipient_company_id || ''
      })
      const paragraphText = String(result?.paragraph_text || '').trim()
      if (!paragraphText) throw new Error('Empty intro paragraph payload')
      upsertIntroParagraphIntoEditor(paragraphText)
      toastSuccess('Вводный абзац добавлен')
    } catch (error) {
      console.error('Error building outgoing intro paragraph:', error)
      toastError(error?.response?.data?.detail || 'Не удалось сформировать вводный абзац')
    } finally {
      introParagraphBusy.value = false
    }
  }

  const getSelectionNodeWithin = (container) => {
    if (!container) return null
    const selection = window.getSelection?.()
    if (!selection || selection.rangeCount === 0) return null
    let node = selection.anchorNode
    if (!node) return null
    if (node.nodeType === Node.TEXT_NODE) node = node.parentNode
    if (!node || !container.contains(node)) return null
    return node
  }

  const isNodeInsideList = (node) => !!node?.closest?.('ul, ol')

  const refreshToolbarStates = () => {
    editorInList.value = isNodeInsideList(getSelectionNodeWithin(editorRef.value))
    attachmentsInList.value = isNodeInsideList(getSelectionNodeWithin(attachmentsEditorRef.value))
  }

  const toggleFormattingMarks = () => {
    showFormattingMarks.value = !showFormattingMarks.value
    if (showFormattingMarks.value) {
      normalizeEditableDom(editorRef.value, bodySanitizeConfig)
      normalizeEditableDom(attachmentsEditorRef.value, attachmentsSanitizeConfig)
      syncBodyFromEditor()
      syncAttachmentsFromEditor()
    }
    refreshToolbarStates()
  }

  const captureEditorSelection = () => {
    if (!editorRef.value) return
    const selection = window.getSelection?.()
    if (!selection || selection.rangeCount === 0) return
    const range = selection.getRangeAt(0)
    const commonNode = range.commonAncestorContainer
    if (!editorRef.value.contains(commonNode)) return
    editorSelectionRange.value = range.cloneRange()
    refreshToolbarStates()
  }

  const restoreEditorSelection = () => {
    if (!editorRef.value) return false
    editorRef.value.focus()
    const selection = window.getSelection?.()
    if (!selection) return false
    selection.removeAllRanges()
    if (editorSelectionRange.value) {
      selection.addRange(editorSelectionRange.value)
      return true
    }
    const range = document.createRange()
    range.selectNodeContents(editorRef.value)
    range.collapse(false)
    selection.addRange(range)
    return true
  }

  const syncBodyFromEditor = () => {
    if (!editorRef.value) return
    form.value.body = DOMPurify.sanitize(editorRef.value.innerHTML, bodySanitizeConfig)
  }

  const clearTableControlsHideTimer = () => {
    if (tableControlsHideTimer) {
      clearTimeout(tableControlsHideTimer)
      tableControlsHideTimer = null
    }
  }

  const hideTableControls = () => {
    clearTableControlsHideTimer()
    hoveredTableCell = null
    tableControls.value.visible = false
  }

  const updateTableControlsForCell = (cell) => {
    if (!cell || !editorRef.value) { hideTableControls(); return }
    const row = cell.parentElement
    const table = cell.closest('table')
    if (!row || !table) { hideTableControls(); return }
    const rowSection = row.parentElement
    const bodyRows = Array.from(table.querySelectorAll('tr'))
    const rowCells = Array.from(row.children).filter((item) => ['TD', 'TH'].includes(item.tagName))
    const colIndex = rowCells.indexOf(cell)
    const rowIndex = bodyRows.indexOf(row)
    if (rowIndex === -1 || colIndex === -1) { hideTableControls(); return }
    const rect = cell.getBoundingClientRect()
    hoveredTableCell = cell
    tableControls.value = {
      visible: true,
      left: rect.right - 188,
      top: rect.top - 42,
      rowIndex, colIndex,
      canDeleteRow: bodyRows.length > 1,
      canDeleteCol: rowCells.length > 1,
      rowSectionTag: rowSection?.tagName || 'TBODY'
    }
  }

  const updateTableControlsPosition = () => {
    if (!hoveredTableCell) return
    updateTableControlsForCell(hoveredTableCell)
  }

  const onEditorMouseMove = (event) => {
    const cell = event.target?.closest?.('td, th')
    if (!cell || !editorRef.value?.contains(cell)) {
      if (!tableControlsHover) hideTableControls()
      return
    }
    clearTableControlsHideTimer()
    updateTableControlsForCell(cell)
  }

  const onEditorMouseLeave = () => {
    clearTableControlsHideTimer()
    tableControlsHideTimer = setTimeout(() => {
      if (!tableControlsHover) hideTableControls()
    }, 120)
  }

  const onTableControlsEnter = () => { tableControlsHover = true; clearTableControlsHideTimer() }
  const onTableControlsLeave = () => { tableControlsHover = false; hideTableControls() }

  const getTableContext = () => {
    const cell = hoveredTableCell
    const row = cell?.parentElement
    const table = cell?.closest?.('table')
    if (!cell || !row || !table) return null
    return { cell, row, table }
  }

  const cloneCellPresentation = (sourceCell, nextCell, fallbackText) => {
    if (!sourceCell || !nextCell) return
    if (sourceCell.hasAttribute('style')) nextCell.setAttribute('style', sourceCell.getAttribute('style'))
    if (sourceCell.hasAttribute('colspan')) nextCell.setAttribute('colspan', sourceCell.getAttribute('colspan'))
    if (sourceCell.hasAttribute('rowspan')) nextCell.setAttribute('rowspan', sourceCell.getAttribute('rowspan'))
    nextCell.textContent = fallbackText
  }

  const insertCellAt = (row, index) => {
    const cells = Array.from(row.children).filter((item) => ['TD', 'TH'].includes(item.tagName))
    const sourceCell = cells[index] || cells[cells.length - 1] || null
    const tagName = sourceCell?.tagName?.toLowerCase() || (row.parentElement?.tagName === 'THEAD' ? 'th' : 'td')
    const nextCell = row.children[index + 1] || null
    const newCell = document.createElement(tagName)
    const defaultText = tagName === 'th' ? `Заголовок ${cells.length + 1}` : `Ячейка ${tableControls.value.rowIndex + 1}.${cells.length + 1}`
    cloneCellPresentation(sourceCell, newCell, defaultText)
    row.insertBefore(newCell, nextCell)
    return newCell
  }

  const addTableRow = () => {
    const context = getTableContext()
    if (!context) return
    const { row } = context
    const sourceCells = Array.from(row.children).filter((item) => ['TD', 'TH'].includes(item.tagName))
    const newRow = document.createElement('tr')
    sourceCells.forEach((sourceCell, index) => {
      const tagName = sourceCell.tagName.toLowerCase()
      const newCell = document.createElement(tagName)
      const defaultText = tagName === 'th' ? `Заголовок ${index + 1}` : `Ячейка ${tableControls.value.rowIndex + 2}.${index + 1}`
      cloneCellPresentation(sourceCell, newCell, defaultText)
      newRow.appendChild(newCell)
    })
    row.parentNode.insertBefore(newRow, row.nextSibling)
    syncBodyFromEditor()
    updateTableControlsForCell(newRow.children[Math.max(0, tableControls.value.colIndex)] || newRow.children[0])
  }

  const addTableColumn = () => {
    const context = getTableContext()
    if (!context) return
    const { table } = context
    Array.from(table.querySelectorAll('tr')).forEach((row) => {
      insertCellAt(row, tableControls.value.colIndex)
    })
    syncBodyFromEditor()
    updateTableControlsPosition()
  }

  const removeTableRow = () => {
    const context = getTableContext()
    if (!context || !tableControls.value.canDeleteRow) return
    const { row, table } = context
    const rows = Array.from(table.querySelectorAll('tr'))
    const nextRow = rows[tableControls.value.rowIndex + 1] || rows[tableControls.value.rowIndex - 1] || null
    row.remove()
    syncBodyFromEditor()
    if (nextRow?.children?.length) {
      updateTableControlsForCell(nextRow.children[Math.max(0, Math.min(tableControls.value.colIndex, nextRow.children.length - 1))])
    } else {
      hideTableControls()
    }
  }

  const removeTableColumn = () => {
    const context = getTableContext()
    if (!context || !tableControls.value.canDeleteCol) return
    const { table } = context
    Array.from(table.querySelectorAll('tr')).forEach((row) => {
      const cells = Array.from(row.children).filter((item) => ['TD', 'TH'].includes(item.tagName))
      const cell = cells[tableControls.value.colIndex]
      if (cell) cell.remove()
    })
    syncBodyFromEditor()
    const firstRemainingRow = table.querySelector('tr')
    if (firstRemainingRow?.children?.length) {
      const nextIndex = Math.max(0, Math.min(tableControls.value.colIndex - 1, firstRemainingRow.children.length - 1))
      updateTableControlsForCell(firstRemainingRow.children[nextIndex])
    } else {
      hideTableControls()
    }
  }

  const onEditorInput = (e) => {
    form.value.body = DOMPurify.sanitize(e.target.innerHTML, bodySanitizeConfig)
    captureEditorSelection()
    refreshToolbarStates()
  }

  const onEditorPaste = (e) => {
    e.preventDefault()
    const text = (e.clipboardData || window.clipboardData).getData('text/plain')
    document.execCommand('insertText', false, text)
    captureEditorSelection()
    refreshToolbarStates()
  }

  const escapeHtml = (value) => (
    value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  )

  const attachmentsTextToHtml = (text) => {
    if (!text) return ''
    const lines = text.replace(/\r\n/g, '\n').split('\n').map(line => line.trim()).filter(Boolean)
    if (!lines.length) return ''
    const isBullet = (line) => line.startsWith('• ') || line.startsWith('- ')
    if (lines.every(isBullet)) {
      const items = lines.map(line => line.replace(/^[-•]\s?/, '')).map(item => `<li>${escapeHtml(item)}</li>`).join('')
      return `<ul>${items}</ul>`
    }
    return lines.map(line => `<div>${escapeHtml(line)}</div>`).join('')
  }

  const attachmentsHtmlToText = (html) => {
    if (!html) return ''
    const container = document.createElement('div')
    container.innerHTML = DOMPurify.sanitize(html, attachmentsSanitizeConfig)
    const lines = []
    const pushLine = (value) => {
      const text = value.replace(/\s+/g, ' ').trim()
      if (text) lines.push(text)
    }
    const walk = (node) => {
      if (node.nodeType === Node.TEXT_NODE) { pushLine(node.textContent || ''); return }
      if (node.nodeType !== Node.ELEMENT_NODE) return
      const tag = node.tagName.toUpperCase()
      if (tag === 'BR') { lines.push(''); return }
      if (tag === 'UL' || tag === 'OL') { Array.from(node.children).forEach(child => walk(child)); return }
      if (tag === 'LI') {
        const text = node.textContent || ''
        if (text.trim()) lines.push(`• ${text.trim()}`)
        return
      }
      if (tag === 'P' || tag === 'DIV') { pushLine(node.textContent || ''); return }
      pushLine(node.textContent || '')
    }
    Array.from(container.childNodes).forEach(child => walk(child))
    return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim()
  }

  const syncAttachmentsFromEditor = () => {
    if (!attachmentsEditorRef.value) return
    const rawHtml = attachmentsEditorRef.value.innerHTML
    const html = DOMPurify.sanitize(rawHtml, attachmentsSanitizeConfig)
    form.value.attachments_list = attachmentsHtmlToText(html)
  }

  const onAttachmentsInput = () => {
    syncAttachmentsFromEditor()
    refreshToolbarStates()
  }

  const onAttachmentsPaste = (e) => {
    e.preventDefault()
    const text = (e.clipboardData || window.clipboardData).getData('text/plain')
    document.execCommand('insertText', false, text)
    syncAttachmentsFromEditor()
    refreshToolbarStates()
  }

  const formatAttachmentsIndent = () => {
    if (attachmentsEditorRef.value) attachmentsEditorRef.value.focus()
    document.execCommand('formatBlock', false, 'p')
    const selection = window.getSelection()
    if (selection.rangeCount > 0) {
      const node = selection.anchorNode?.parentNode
      if (node && node.nodeName === 'P') {
        node.style.textIndent = '1.25cm'
        node.style.marginTop = '0'
        node.style.marginBottom = '0'
      }
    }
    syncAttachmentsFromEditor()
    refreshToolbarStates()
  }

  const formatAttachmentsList = () => {
    if (attachmentsEditorRef.value) attachmentsEditorRef.value.focus()
    document.execCommand('insertUnorderedList')
    syncAttachmentsFromEditor()
    refreshToolbarStates()
  }

  const formatIndent = () => {
    restoreEditorSelection()
    document.execCommand('formatBlock', false, 'p')
    const selection = window.getSelection()
    if (selection.rangeCount > 0) {
      const node = selection.anchorNode.parentNode
      if (node.nodeName === 'P') {
        node.style.textIndent = '1.25cm'
        node.style.marginTop = '0'
        node.style.marginBottom = '0'
      }
    }
    syncBodyFromEditor()
    captureEditorSelection()
    refreshToolbarStates()
  }

  const formatList = () => {
    restoreEditorSelection()
    document.execCommand('insertUnorderedList')
    syncBodyFromEditor()
    captureEditorSelection()
    refreshToolbarStates()
  }

  const openTableModal = () => { captureEditorSelection(); tableModalOpen.value = true }
  const closeTableModal = () => { tableModalOpen.value = false }

  const buildTableHtml = ({ rows, cols, includeHeader }) => {
    const safeRows = Math.min(20, Math.max(1, Number(rows || 1)))
    const safeCols = Math.min(10, Math.max(1, Number(cols || 1)))
    const headerRow = includeHeader
      ? `<thead><tr>${Array.from({ length: safeCols }, (_, index) => `<th style="border:1px solid #cbd5e1;padding:8px 10px;background:#f8fafc;">Заголовок ${index + 1}</th>`).join('')}</tr></thead>`
      : ''
    const bodyRowsCount = includeHeader ? Math.max(1, safeRows - 1) : safeRows
    const bodyRows = Array.from({ length: bodyRowsCount }, (_, rowIndex) => (
      `<tr>${Array.from({ length: safeCols }, (_, colIndex) => `<td style="border:1px solid #cbd5e1;padding:8px 10px;">Ячейка ${rowIndex + 1}.${colIndex + 1}</td>`).join('')}</tr>`
    )).join('')
    return `<table style="width:100%;border-collapse:collapse;margin:12px 0;">${headerRow}<tbody>${bodyRows}</tbody></table><p><br></p>`
  }

  const insertTable = () => {
    if (!editorRef.value) return
    restoreEditorSelection()
    const html = buildTableHtml(tableForm.value)
    document.execCommand('insertHTML', false, html)
    syncBodyFromEditor()
    captureEditorSelection()
    closeTableModal()
  }

  const saveDocument = async () => {
    if (saving.value) return
    if (!form.value.recipient_company_id) {
      toastError('Выберите получателя')
      return
    }
    if (isLetterKind.value && !form.value.subject) {
      toastError('Заполните тему письма')
      return
    }
    if (requiresPaymentLinks.value) {
      const invalidPayment = (form.value.linked_payment_items || []).some((item, index) => {
        if (!item.entry_id) return false
        const payment = dealPayments.value.find((entry) => String(entry.id) === String(item.entry_id))
        if (!payment) return false
        return Number(item.amount || 0) > getPaymentAvailableAmount(payment, index) + 0.005
      })
      if (invalidPayment) {
        toastError('Сумма зачета превышает доступный остаток платежа')
        return
      }
    }
    syncStructuredDraftIntoForm()
    if (isLetterKind.value) syncAttachmentsFromEditor()
    form.value.editor_validation = computeLocalEditorValidation(form.value.editor_draft, form.value.document_kind || activeKind.value)
    persistDraftNow()
    saving.value = true
    try {
      const wasNewDocument = !activeDocumentId.value
      const previousDocument = activeDocumentId.value ? { ...activeDocument.value } : null
      const draftKeyBeforeSave = buildDraftStorageKey(activeDocumentId.value)
      let documentData = null
      if (activeDocumentId.value) {
        const payload = {
          document_kind: form.value.document_kind || activeKind.value,
          editor_mode: form.value.editor_mode || (activeKind.value === 'letter' ? 'classic' : 'structured'),
          editor_schema_version: Number(form.value.editor_schema_version || editorSchemaVersion.value || 1),
          editor_draft: form.value.editor_draft || null,
          editor_validation: form.value.editor_validation || { errors: [], warnings: [] },
          editor_render_context: form.value.editor_render_context || { snapshot_mode: 'live' },
          recipient_company_id: form.value.recipient_company_id,
          our_company_key: form.value.our_company_key,
          subject: form.value.subject || activeKindMeta.value.singular,
          body: form.value.body || '',
          attachments_list: form.value.attachments_list || '',
          contract_id: form.value.contract_id || null,
          bank_account_index: form.value.bank_account_index,
          linked_stage_ids: form.value.linked_stage_ids || [],
          linked_payment_items: form.value.linked_payment_items || [],
          recipient_short_name: form.value.recipient_short_name || '',
          recipient_to_name: form.value.recipient_to_name || '',
          recipient_appeal: form.value.recipient_appeal || '',
          recipient_eio: form.value.recipient_eio || '',
          recipient_genitive_name: form.value.recipient_genitive_name || '',
          recipient_salutation: form.value.recipient_salutation || ''
        }
        if ((form.value.document_kind || activeKind.value) === 'letter' && form.value.outgoing_number_suffix) {
          payload.outgoing_number_suffix = form.value.outgoing_number_suffix.trim()
        }
        if (form.value.deal_id) payload.deal_id = form.value.deal_id
        if (form.value.letter_date) payload.letter_date = form.value.letter_date
        documentData = await outgoingApi.update(activeDocumentId.value, payload)
        if (pendingFiles.value.length) {
          await queueAttachments(activeDocumentId.value, pendingFiles.value)
          pendingFiles.value = []
          documentData = await outgoingApi.getById(activeDocumentId.value)
        }
      } else {
        const payload = new FormData()
        payload.append('document_kind', form.value.document_kind || activeKind.value)
        payload.append('editor_mode', form.value.editor_mode || (activeKind.value === 'letter' ? 'classic' : 'structured'))
        payload.append('editor_schema_version', String(form.value.editor_schema_version || editorSchemaVersion.value || 1))
        payload.append('editor_draft', JSON.stringify(form.value.editor_draft || null))
        payload.append('editor_validation', JSON.stringify(form.value.editor_validation || { errors: [], warnings: [] }))
        payload.append('editor_render_context', JSON.stringify(form.value.editor_render_context || { snapshot_mode: 'live' }))
        payload.append('recipient_company_id', form.value.recipient_company_id)
        if (form.value.deal_id) payload.append('deal_id', form.value.deal_id)
        if (form.value.contract_id) payload.append('contract_id', form.value.contract_id)
        if (form.value.letter_date) payload.append('letter_date', form.value.letter_date)
        payload.append('our_company_key', form.value.our_company_key)
        payload.append('subject', form.value.subject || activeKindMeta.value.singular)
        payload.append('body', form.value.body || '')
        payload.append('attachments_list', form.value.attachments_list || '')
        if (form.value.bank_account_index !== null && form.value.bank_account_index !== undefined) {
          payload.append('bank_account_index', String(form.value.bank_account_index))
        }
        payload.append('linked_stage_ids', JSON.stringify(form.value.linked_stage_ids || []))
        payload.append('linked_payment_items', JSON.stringify(form.value.linked_payment_items || []))
        payload.append('recipient_short_name', form.value.recipient_short_name || '')
        payload.append('recipient_to_name', form.value.recipient_to_name || '')
        payload.append('recipient_appeal', form.value.recipient_appeal || '')
        payload.append('recipient_eio', form.value.recipient_eio || '')
        payload.append('recipient_genitive_name', form.value.recipient_genitive_name || '')
        payload.append('recipient_salutation', form.value.recipient_salutation || '')
        documentData = await outgoingApi.create(payload)
        activeDocument.value = documentData
        activeDocumentId.value = documentData.id
        if (pendingFiles.value.length) {
          await queueAttachments(activeDocumentId.value, pendingFiles.value)
          pendingFiles.value = []
          documentData = await outgoingApi.getById(activeDocumentId.value)
        }
      }
      const updatedDocument = documentData || activeDocument.value
      const needsRenderSync = (
        wasNewDocument ||
        shouldRegenerateRender(previousDocument, updatedDocument) ||
        (
          !hasCurrentRender(updatedDocument) &&
          !(Array.isArray(updatedDocument?.versions) && updatedDocument.versions.length)
        )
      )
      const syncedDocument = needsRenderSync
        ? await syncCurrentRender(updatedDocument, { silent: false })
        : null
      const effectiveDocument = syncedDocument || updatedDocument
      if (!hasCurrentRender(effectiveDocument)) {
        toastError('Документ сохранен, но шаблон Word не удалось пересобрать')
      }
      await loadDocuments(buildParams())
      await selectDocument(effectiveDocument.id, { preloaded: effectiveDocument })
      removeStorageKey(draftKeyBeforeSave)
      clearDraftForDocument(effectiveDocument.id)
      restoredPendingFileNames.value = []
      isEditing.value = false
      toastSuccess('Документ успешно сохранен')
    } catch (error) {
      console.error('Error saving document:', error)
      if (error.response) console.error('Error details:', error.response.data)
      if (error?.response?.status === 401) {
        writeStorageJson(buildDraftNoticeKey(activeDocumentId.value), {
          reason: 'session_expired',
          at: new Date().toISOString()
        })
        toastError('Сеанс истек. Черновик сохранен локально. Войдите повторно.')
      } else {
        toastError('Ошибка сохранения документа')
      }
    } finally {
      saving.value = false
    }
  }

  const createVersion = async () => {
    if (!activeDocumentId.value) return
    if (outgoingApprovalState.value?.activeInstance || outgoingApprovalState.value?.latestStatus === 'rejected') {
      toastError('Нельзя выпустить версию, пока согласование не завершено успешно.')
      return
    }
    loading.value = true
    try {
      await outgoingApi.createVersion(activeDocumentId.value)
      const versionsData = await outgoingApi.getById(activeDocumentId.value)
      activeDocument.value = versionsData
      versions.value = versionsData.versions || []
      files.value = versionsData.files || []
      await renderPreview(versionsData)
      toastSuccess('Версия успешно создана')
    } catch (error) {
      console.error('Error creating version:', error)
      toastError('Ошибка создания версии')
    } finally {
      loading.value = false
    }
  }

  const confirmDelete = () => { deleteModalOpen.value = true }

  const deleteDocument = async () => {
    if (!activeDocumentId.value) return
    deleteModalOpen.value = false
    try {
      const deletedDocumentId = activeDocumentId.value
      await outgoingApi.remove(activeDocumentId.value)
      activeDocumentId.value = null
      activeDocument.value = {}
      versions.value = []
      files.value = []
      pendingFiles.value = []
      restoredPendingFileNames.value = []
      clearPreviewContainer()
      previewReady.value = false
      clearStructuredLivePreviewTimer()
      clearStructuredLivePreview()
      isEditing.value = false
      form.value = buildDefaultForm()
      clearDraftForDocument(deletedDocumentId)
      syncDocumentQuery(null)
      await loadDocuments()
      await openDocumentFromQueryOrDefault()
      toastSuccess('Документ удален')
    } catch (error) {
      console.error('Error deleting document:', error)
      toastError('Ошибка удаления документа')
    }
  }

  const handleOutgoingApprovalState = (state) => {
    outgoingApprovalState.value = state || {
      activeInstance: null, latestInstance: null, latestStatus: null, templateCount: 0,
    }
  }

  const refreshOutgoingAfterApproval = async () => {
    if (!activeDocumentId.value) { await loadDocuments(buildParams()); return }
    try {
      const data = await outgoingApi.getById(activeDocumentId.value)
      activeDocument.value = data || {}
      versions.value = activeDocument.value.versions || []
      files.value = activeDocument.value.files || []
      upsertDocumentInList(activeDocument.value)
      await loadDocuments(buildParams())
    } catch (error) {
      console.error(error)
    }
  }

  const formatDate = (value) => {
    if (!value) return '-'
    return new Date(value).toLocaleDateString('ru-RU')
  }

  const formatDateLong = (value) => {
    if (!value) return ''
    const formatted = new Date(value).toLocaleDateString('ru-RU', {
      day: '2-digit', month: 'long', year: 'numeric'
    })
    return formatted.replace(/\s?г\.?$/, '')
  }

  const formatDateTime = (value) => {
    if (!value) return '-'
    return new Date(value).toLocaleString('ru-RU')
  }

  const openSequences = async () => {
    if (!canEditSequences.value) return
    sequencesModalOpen.value = true
    await loadSequences()
  }

  const closeSequences = () => { sequencesModalOpen.value = false }

  const loadSequences = async () => {
    sequenceLoading.value = true
    try {
      const result = await outgoingApi.listSequences({
        document_kind: activeKind.value,
        sequence_date: form.value.letter_date || activeDocument.value?.letter_date || new Date().toISOString().split('T')[0]
      })
      sequences.value = result || []
      const values = {}
      sequences.value.forEach((row) => { values[row.our_company_key] = row.next_seq })
      sequenceForm.value = values
    } catch (error) {
      console.error('Error loading sequences:', error)
      toastError('Ошибка загрузки нумерации')
    } finally {
      sequenceLoading.value = false
    }
  }

  const saveSequences = async () => {
    if (sequenceSaving.value) return
    sequenceSaving.value = true
    try {
      const updates = sequences.value
        .map((row) => {
          const nextSeq = Number(sequenceForm.value[row.our_company_key])
          if (!Number.isFinite(nextSeq) || nextSeq < 1) return null
          if (nextSeq === row.next_seq) return null
          return outgoingApi.updateSequence(row.our_company_key, {
            next_seq: nextSeq,
            document_kind: row.document_kind || activeKind.value,
            sequence_date: row.sequence_date || form.value.letter_date || activeDocument.value?.letter_date || null
          })
        })
        .filter(Boolean)
      if (updates.length) await Promise.all(updates)
      await loadSequences()
      toastSuccess('Номера обновлены')
    } catch (error) {
      console.error('Error saving sequences:', error)
      toastError('Ошибка сохранения нумерации')
    } finally {
      sequenceSaving.value = false
    }
  }

  const handlePageHide = () => { persistDraftNow() }

  const handleVisibilityChange = () => {
    if (document.visibilityState === 'hidden') persistDraftNow()
  }

  watch(form, () => {
    if (!isEditing.value || draftSyncSuspended.value) return
    scheduleDraftPersist()
  }, { deep: true })

  watch(() => form.value.deal_id, async (dealId, oldDealId) => {
    await loadDealContext(dealId)
    if (isEditing.value && dealId !== oldDealId) {
      form.value.contract_id = ''
      form.value.linked_stage_ids = []
      form.value.linked_payment_items = []
    }
  })

  watch(() => form.value.recipient_company_id, () => {
    if (!recipientBankAccounts.value.length) {
      form.value.bank_account_index = null
      if (!form.value.recipient_company_id) clearStructuredLivePreview()
      return
    }
    if (
      form.value.bank_account_index === null ||
      form.value.bank_account_index === undefined ||
      form.value.bank_account_index >= recipientBankAccounts.value.length
    ) {
      form.value.bank_account_index = 0
    }
    if (!form.value.recipient_company_id) clearStructuredLivePreview()
  })

  watch(pendingFiles, () => {
    if (!isEditing.value || draftSyncSuspended.value) return
    scheduleDraftPersist()
  }, { deep: true })

  onMounted(async () => {
    window.addEventListener('beforeunload', handlePageHide)
    window.addEventListener('pagehide', handlePageHide)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    await Promise.all([loadCompanies(), loadDeals(), loadEditorSchema(activeKind.value), loadDocuments(), loadAiStatus()])
    await openDocumentFromQueryOrDefault()
    filtersReady.value = true
  })

  watch(() => route.query.document_id, async (value, oldValue) => {
    if (value === oldValue) return
    if (!value) return
    if (String(activeDocumentId.value) === String(value)) return
    let documentData = documents.value.find((item) => String(item.id) === String(value)) || null
    if (!documentData) {
      try {
        documentData = await outgoingApi.getById(value)
        upsertDocumentInList(documentData)
      } catch (error) {
        console.error('Error syncing document from query:', error)
        return
      }
    }
    await selectDocument(documentData.id, { syncQuery: false, preloaded: documentData })
  })

  watch(previewMode, async () => {
    await nextTick()
    applyPreviewScale()
  })

  onBeforeUnmount(() => {
    persistDraftNow()
    if (filtersDebounce.value) clearTimeout(filtersDebounce.value)
    clearDraftAutosaveTimer()
    clearEditorResolveTimer()
    clearStructuredLivePreviewTimer()
    clearStructuredLivePreview()
    clearPreviewContainer()
    clearTableControlsHideTimer()
    window.removeEventListener('beforeunload', handlePageHide)
    window.removeEventListener('pagehide', handlePageHide)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })

  return {
    // refs
    documents, companies, deals, activeDocument, activeDocumentId,
    versions, files, pendingFiles, loading, saving, form, isEditing,
    documentKinds, activeKind, activeKindMeta, documentKindMeta, switchDocumentKind,
    isLetterKind, hasEditableNumberSuffix, isActKind, requiresStageLinks, requiresPaymentLinks, isLetterDocument,
    dealContracts, dealStages, dealPayments, recipientBankAccounts, bankAccountLabel, formatMoney,
    getPaymentAvailableAmount, paymentOptionLabel, addPaymentLink, removePaymentLink,
    editorRef, attachmentsEditorRef, docListRef, previewReady,
    selectDocument, startNewDocument, handleFileChange, saveDocument,
    fillRecipientFromCompany, insertIntroParagraph, introParagraphBusy,
    createVersion, formatDate, formatDateTime, renderPreview, refreshPreview,
    enableEditMode, cancelEdit, onEditorInput, onEditorPaste, formatIndent, formatList,
    showFormattingMarks, toggleFormattingMarks, editorInList, attachmentsInList, refreshToolbarStates,
    tableModalOpen, tableForm, openTableModal, closeTableModal, insertTable, captureEditorSelection,
    tableControls, onEditorMouseMove, onEditorMouseLeave, updateTableControlsPosition,
    onTableControlsEnter, onTableControlsLeave, addTableRow, addTableColumn, removeTableRow, removeTableColumn,
    onAttachmentsInput, onAttachmentsPaste, formatAttachmentsIndent, formatAttachmentsList,
    downloadDocx, downloadOutgoingVersion, downloadOutgoingVersionFile, downloadOutgoingFile, getVersionFile,
    deleteModalOpen, confirmDelete, deleteDocument, handleOutgoingApprovalState, refreshOutgoingAfterApproval,
    filters, applyFilters, resetFilters, displayOutgoingNumber, ourCompanies, ourCompanyLocked, companyLabel,
    page, hasNext, nextPage, prevPage,
    previewMode, previewScale, setPreviewMode, previewFrameSrc,
    previewScaleLabel, previewLoading, onListKeydown,
    editorBlockCatalog, editorFields, editorTemplateBlocks, editorResolvedFields, editorSchemaLoading, ensureEditorDraft,
    aiEnabled, aiModel, requestOutgoingAiAssist,
    canRenderStructuredPreview, liveStructuredPreviewMode, liveStructuredPreviewLoading,
    liveStructuredPreviewError, liveStructuredPreviewPdfSrc, liveStructuredPreviewDocxRef,
    setStructuredPreviewMode, refreshStructuredLivePreview,
    canEditSequences, sequencesModalOpen, sequences, sequenceForm, sequenceLoading, sequenceSaving,
    openSequences, closeSequences, saveSequences,
    draftRestoreModalOpen, draftRestoreCandidate, draftRestoreReason,
    restoredPendingFileNames, applyDraftRestore, discardDraftRestore,
  }
}
