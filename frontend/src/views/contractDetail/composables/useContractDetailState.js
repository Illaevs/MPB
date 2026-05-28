import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { api } from '@/services/api'
import { expenseCategories } from '@/utils/categories'
import { downloadFromApi } from '@/utils/download'
import { useUploadQueueStore } from '@/stores/uploadQueue'
import { useCompaniesStore } from '@/stores/companies'
import { useToast } from '@/composables/useToast'

export const CD_STATUS_OPTIONS = [
  { value: 'approval',    label: 'На согласовании' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'completed',   label: 'Подписан' },
]

export const cdClickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

export function useContractDetailState() {
  const route = useRoute()
  const router = useRouter()
  const toast = useToast()
  const contractId = route.params.id
  const uploadQueue = useUploadQueueStore()
  const companiesStore = useCompaniesStore()

  const loading = ref(false)
  const uploading = ref(false)
  const contract = ref(null)
  const dealTitle = ref('')
  const subcontractorTitle = ref('')
  const documents = ref([])
  const dealProducts = ref([])
  const expandedDocs = ref([])
  const payments = ref([])
  const paymentSummary = ref({ total_amount: 0, paid_amount: 0, pending_amount: 0 })
  const stages = ref([])
  const showUploadModal = ref(false)
  const activeTab = ref('data')
  const statusMenuOpen = ref(false)
  const statusBusy = ref(false)
  const cdStatusOptions = CD_STATUS_OPTIONS

  const companies = ref([])
  const expenseEntries = ref([])
  const expenseSummary = ref({ total_amount: 0, paid_amount: 0, pending_amount: 0 })
  const loadingExpenses = ref(false)
  const showExpenseModal = ref(false)
  const showBulkExpenseModal = ref(false)
  const showInvoiceProductsModal = ref(false)
  const invoiceProductsDoc = ref(null)
  const invoiceProductIds = ref([])
  const savingInvoiceProducts = ref(false)
  const focusedDocumentAmountId = ref(null)
  const documentAmountDrafts = ref({})
  const uploadAmountFocused = ref(false)
  const uploadAmountDraft = ref('')
  const editingExpense = ref(null)
  const expenseForm = ref({
    amount: '',
    plan_date: '',
    actual_date: '',
    category_code: ''
  })
  const bulkForm = ref({
    category_code: '',
    amount: '',
    start_date: '',
    frequency: 'month',
    periods: 1
  })

  const docTypes = [
    { key: 'contract', label: 'Договор' },
    { key: 'addendum', label: 'Доп. соглашения' },
    { key: 'act', label: 'Акты' },
    { key: 'invoice', label: 'Накладные' }
  ]
  const docTypeRows = [
    [docTypes[0], docTypes[1]],
    [docTypes[2], docTypes[3]]
  ]

  const paymentFilters = ref({ direction: '', status: '', search: '' })
  const documentFilters = ref({ status: '', search: '', docType: '' })

  const setActiveTab = (tab) => {
    activeTab.value = tab
    const q = { ...(route.query || {}) }
    q.tab = tab
    router.replace({ query: q }).catch(() => {})
  }

  const onChangeStatus = async (newStatus) => {
    statusMenuOpen.value = false
    if (!contract.value || newStatus === contract.value.status) return
    const previous = contract.value.status
    contract.value = { ...contract.value, status: newStatus }
    statusBusy.value = true
    try {
      const c = contract.value
      await api.contracts.update(contractId, {
        contract_number: c.contract_number,
        contract_date: c.contract_date,
        status: newStatus,
        amount: c.amount,
        contract_type: c.contract_type,
        customer_id: c.customer_id || null,
        executor_id: c.executor_id || null,
        deal_id: c.deal_id || null,
      })
      toast.success(`Статус: ${(CD_STATUS_OPTIONS.find(o => o.value === newStatus) || {}).label || newStatus}`)
    } catch (e) {
      contract.value = { ...contract.value, status: previous }
      toast.error(e?.response?.data?.detail || 'Не удалось изменить статус')
    } finally {
      statusBusy.value = false
    }
  }

  const toggleDocumentExpanded = (docId) => {
    const key = String(docId)
    const next = expandedDocs.value.includes(key)
      ? expandedDocs.value.filter(id => id !== key)
      : [...expandedDocs.value, key]
    expandedDocs.value = next
  }

  const isDocumentExpanded = (docId) => expandedDocs.value.includes(String(docId))

  const getDocumentFiles = (doc) => {
    const files = []
    if (doc.pdf_storage_path) {
      files.push({
        key: `${doc.id}-pdf`,
        kind: 'pdf',
        name: doc.pdf_file_name || 'PDF'
      })
    }
    if (doc.edit_storage_path) {
      files.push({
        key: `${doc.id}-edit`,
        kind: 'edit',
        name: doc.edit_file_name || 'Ред. формат'
      })
    }
    return files
  }

  const uploadForm = ref({
    docType: 'contract',
    fileKind: 'pdf',
    status: 'draft',
    amount: '',
    productIds: [],
    file: null,
    documentId: null
  })
  const uploadFileInput = ref(null)
  const isDropActive = ref(false)

  const docGroups = computed(() => {
    const groups = { contract: [], addendum: [], act: [], invoice: [] }
    documents.value.forEach((doc) => {
      if (groups[doc.doc_type]) {
        groups[doc.doc_type].push(doc)
      }
    })
    return groups
  })

  const filteredDocGroups = computed(() => {
    const groups = { contract: [], addendum: [], act: [], invoice: [] }
    const search = documentFilters.value.search.trim().toLowerCase()
    documents.value.forEach((doc) => {
      if (!groups[doc.doc_type]) return
      if (documentFilters.value.docType && doc.doc_type !== documentFilters.value.docType) return
      if (documentFilters.value.status && doc.status !== documentFilters.value.status) return
      if (search) {
        const hay = `${doc.pdf_file_name || ''} ${doc.edit_file_name || ''} ${doc.number_in_contract || ''}`.toLowerCase()
        if (!hay.includes(search)) return
      }
      groups[doc.doc_type].push(doc)
    })
    return groups
  })

  const filteredDocumentsList = computed(() => {
    const search = documentFilters.value.search.trim().toLowerCase()
    const docTypeOrder = { contract: 0, addendum: 1, act: 2, invoice: 3 }
    return documents.value.filter((doc) => {
      if (documentFilters.value.docType && doc.doc_type !== documentFilters.value.docType) return false
      if (documentFilters.value.status && doc.status !== documentFilters.value.status) return false
      if (search) {
        const hay = `${documentTypeLabel(doc.doc_type)} ${doc.number_in_contract || ''} ${doc.pdf_file_name || ''} ${doc.edit_file_name || ''}`.toLowerCase()
        if (!hay.includes(search)) return false
      }
      return true
    }).slice().sort((left, right) => {
      const typeOrder = (docTypeOrder[left.doc_type] ?? 99) - (docTypeOrder[right.doc_type] ?? 99)
      if (typeOrder !== 0) return typeOrder
      const leftNumber = Number(left.number_in_contract || 0)
      const rightNumber = Number(right.number_in_contract || 0)
      if (leftNumber !== rightNumber) return leftNumber - rightNumber
      return String(left.id || '').localeCompare(String(right.id || ''))
    })
  })

  const filteredPayments = computed(() => {
    const search = paymentFilters.value.search.trim().toLowerCase()
    return payments.value.filter((entry) => {
      if (paymentFilters.value.direction && entry.direction !== paymentFilters.value.direction) return false
      if (paymentFilters.value.status && entry.payment_status !== paymentFilters.value.status) return false
      if (search) {
        const hay = `${entry.payer_name || ''} ${entry.payee_name || ''} ${entry.deal_title || ''}`.toLowerCase()
        if (!hay.includes(search)) return false
      }
      return true
    })
  })

  const filteredStages = computed(() => {
    return stages.value.filter(stage => stage.stage_type === 'stage')
  })

  const isServiceContract = computed(() => contract.value?.contract_type === 'services')

  const normalizeId = (value) => {
    if (!value) return ''
    return String(value).replace(/-/g, '').toLowerCase()
  }

  const getCompanyNameById = (id) => {
    if (!id) return ''
    const normalizedId = normalizeId(id)
    const match = companies.value.find(company => normalizeId(company.id) === normalizedId)
    return match ? match.name : ''
  }

  const expensePayerName = computed(() => {
    const name = getCompanyNameById(contract.value?.customer_id)
    if (name) return name
    const fallback = expenseEntries.value.find(entry => entry.payer_name)?.payer_name
    return fallback || ''
  })

  const expensePayeeName = computed(() => {
    const name = getCompanyNameById(contract.value?.executor_id)
    if (name) return name
    const fallback = expenseEntries.value.find(entry => entry.payee_name)?.payee_name
    return fallback || ''
  })

  const customerName = computed(() => {
    const name = getCompanyNameById(contract.value?.customer_id)
    if (name) return name
    const fallback = payments.value.find(entry => entry.payee_name)?.payee_name
    return fallback || ''
  })

  const executorName = computed(() => {
    const name = getCompanyNameById(contract.value?.executor_id)
    if (name) return name
    const fallback = payments.value.find(entry => entry.payer_name)?.payer_name
    return fallback || ''
  })

  const paymentCompletionPercent = computed(() => {
    const total = Number(paymentSummary.value.total_amount || 0)
    const paid = Number(paymentSummary.value.paid_amount || 0)
    if (!total || total <= 0) return 0
    return Math.max(0, Math.min(100, Math.round((paid / total) * 100)))
  })

  const paidPercent = computed(() => paymentCompletionPercent.value)
  const pendingPercent = computed(() => {
    const total = Number(paymentSummary.value.total_amount || 0)
    const pending = Number(paymentSummary.value.pending_amount || 0)
    if (!total || total <= 0) return 0
    return Math.max(0, Math.min(100 - paidPercent.value, Math.round((pending / total) * 100)))
  })
  const unpaidPercent = computed(() => Math.max(0, 100 - paidPercent.value - pendingPercent.value))

  const signedDocumentsCount = computed(() => {
    return documents.value.filter(doc => doc.status === 'signed').length
  })

  const showUploadAmountField = computed(() => (
    !uploadForm.value.documentId &&
    ['contract', 'addendum', 'act'].includes(uploadForm.value.docType)
  ))

  const documentAmountHelpText = 'Договор: цена договора. Доп. соглашение: новая цена договора (если меняется). Акт: стоимость выполненных работ.'

  const uploadAmountHelpText = computed(() => {
    const hints = {
      contract: 'Цена договора',
      addendum: 'Новая цена договора, если доп. соглашение меняет стоимость',
      act: 'Стоимость выполненных работ'
    }
    return hints[uploadForm.value.docType] || documentAmountHelpText
  })

  const showUploadInvoiceProducts = computed(() => (
    !uploadForm.value.documentId &&
    uploadForm.value.docType === 'invoice'
  ))

  const sortedDealProducts = computed(() => (
    [...dealProducts.value].sort((left, right) => {
      const leftName = String(dealProductName(left) || '').toLowerCase()
      const rightName = String(dealProductName(right) || '').toLowerCase()
      return leftName.localeCompare(rightName, 'ru')
    })
  ))

  const closedStagesCount = computed(() => {
    return filteredStages.value.filter(stage => stage.is_closed === true || stage.status === 'completed').length
  })

  const stagesPlannedAmount = computed(() => {
    return filteredStages.value.reduce((sum, stage) => sum + Number(stage.planned_cost || 0), 0)
  })

  const contractHighlights = computed(() => {
    return [
      {
        label: 'Заказчик',
        value: customerName.value || 'Не указан',
        meta: contractTypeLabel(contract.value?.contract_type),
        icon: 'fas fa-building'
      },
      {
        label: 'Исполнитель',
        value: executorName.value || 'Не указан',
        meta: subcontractorTitle.value || 'Контрагент по договору',
        icon: 'fas fa-user-tie'
      },
      {
        label: 'Сделка',
        value: dealTitle.value || 'Без сделки',
        meta: contract.value?.contract_date ? `Дата договора ${formatDate(contract.value.contract_date)}` : '',
        icon: 'fas fa-briefcase'
      },
      {
        label: 'Сумма договора',
        value: formatAmount(contract.value?.amount || 0),
        meta: contractStatusLabel(contract.value?.status),
        icon: 'fas fa-wallet'
      },
      {
        label: 'Документы',
        value: `${documents.value.length}`,
        meta: signedDocumentsCount.value ? `Подписано ${signedDocumentsCount.value}` : 'Подписанных пока нет',
        icon: 'fas fa-file-signature'
      },
      {
        label: 'Этапы',
        value: `${filteredStages.value.length}`,
        meta: filteredStages.value.length
          ? `Закрыто ${closedStagesCount.value} • План ${formatAmount(stagesPlannedAmount.value)}`
          : 'Этапы еще не добавлены',
        icon: 'fas fa-tasks'
      }
    ]
  })

  const loadCompanies = async () => {
    try {
      await companiesStore.ensureLoaded()
      companies.value = companiesStore.items
    } catch (error) {
      console.error('Error loading companies:', error)
      companies.value = []
    }
  }

  const loadCard = async () => {
    loading.value = true
    try {
      const data = await api.contracts.getCard(contractId)
      contract.value = data.contract
      dealTitle.value = data.deal_title || ''
      subcontractorTitle.value = data.subcontractor_title || ''
      documents.value = data.documents || []
      payments.value = data.payments || []
      paymentSummary.value = data.payment_summary || { total_amount: 0, paid_amount: 0, pending_amount: 0 }
      stages.value = data.stages || []
      if (contract.value?.deal_id) {
        await loadDealProducts()
      } else {
        dealProducts.value = []
      }
      if (contract.value?.contract_type === 'services') {
        await loadExpenses()
      } else {
        expenseEntries.value = []
        expenseSummary.value = { total_amount: 0, paid_amount: 0, pending_amount: 0 }
      }
    } catch (error) {
      console.error('Error loading contract card:', error)
    } finally {
      loading.value = false
    }
  }

  const loadDealProducts = async () => {
    const dealId = contract.value?.deal_id
    if (!dealId) {
      dealProducts.value = []
      return
    }
    try {
      const response = await axios.get(`/api/v1/products/deal/${dealId}`)
      dealProducts.value = response.data || []
    } catch (error) {
      console.error('Error loading deal products:', error)
      dealProducts.value = []
    }
  }

  const loadExpenses = async () => {
    loadingExpenses.value = true
    try {
      const data = await api.contracts.listExpenses(contractId)
      expenseEntries.value = data.items || []
      expenseSummary.value = data.summary || { total_amount: 0, paid_amount: 0, pending_amount: 0 }
    } catch (error) {
      console.error('Error loading expenses:', error)
      expenseEntries.value = []
      expenseSummary.value = { total_amount: 0, paid_amount: 0, pending_amount: 0 }
    } finally {
      loadingExpenses.value = false
    }
  }

  const formatAmount = (value) => {
    const amount = Number(value || 0)
    return amount.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  const parseAmountInput = (value) => {
    const raw = String(value ?? '').replace(/\s+/g, '').replace(',', '.').replace(/[^\d.]/g, '')
    if (!raw) return null
    const [integerPart, ...fractionParts] = raw.split('.')
    const normalized = `${integerPart || '0'}${fractionParts.length ? `.${fractionParts.join('')}` : ''}`
    const amount = Number(normalized)
    return Number.isFinite(amount) ? amount : null
  }

  const amountToEditValue = (value) => {
    if (value === '' || value == null) return ''
    const amount = Number(value)
    if (!Number.isFinite(amount)) return ''
    return amount.toString().replace('.', ',')
  }

  const formatAmountInput = (value) => {
    if (value === '' || value == null) return ''
    const amount = Number(value)
    if (!Number.isFinite(amount)) return ''
    return amount.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  const documentAmountInputValue = (doc) => {
    if (!doc?.id) return ''
    if (focusedDocumentAmountId.value === doc.id) {
      return documentAmountDrafts.value[doc.id] ?? amountToEditValue(doc.amount)
    }
    return formatAmountInput(doc.amount)
  }

  const onDocumentAmountFocus = (doc, event) => {
    focusedDocumentAmountId.value = doc.id
    documentAmountDrafts.value = {
      ...documentAmountDrafts.value,
      [doc.id]: amountToEditValue(doc.amount)
    }
    event.target.value = documentAmountDrafts.value[doc.id]
  }

  const onDocumentAmountInput = (doc, event) => {
    documentAmountDrafts.value = {
      ...documentAmountDrafts.value,
      [doc.id]: event.target.value
    }
  }

  const onDocumentAmountBlur = async (doc) => {
    const amount = parseAmountInput(documentAmountDrafts.value[doc.id])
    const { [doc.id]: removed, ...rest } = documentAmountDrafts.value
    documentAmountDrafts.value = rest
    focusedDocumentAmountId.value = null
    doc.amount = amount
    await updateDocumentAmount(doc)
  }

  const uploadAmountInputValue = computed(() => (
    uploadAmountFocused.value ? uploadAmountDraft.value : formatAmountInput(uploadForm.value.amount)
  ))

  const onUploadAmountFocus = (event) => {
    uploadAmountFocused.value = true
    uploadAmountDraft.value = amountToEditValue(uploadForm.value.amount)
    event.target.value = uploadAmountDraft.value
  }

  const onUploadAmountInput = (event) => {
    uploadAmountDraft.value = event.target.value
  }

  const onUploadAmountBlur = () => {
    uploadForm.value.amount = parseAmountInput(uploadAmountDraft.value) ?? ''
    uploadAmountFocused.value = false
    uploadAmountDraft.value = ''
  }

  const formatDate = (value) => {
    if (!value) return '-'
    return new Date(value).toLocaleDateString('ru-RU')
  }

  const paymentStatusLabel = (status) => {
    const labels = { unpaid: 'Не оплачено', partial: 'Частично', paid: 'Оплачено' }
    return labels[status] || status
  }

  const paymentStatusClass = (status) => {
    const classes = { unpaid: 'badge-secondary', partial: 'badge-warning', paid: 'badge-success' }
    return classes[status] || 'badge-secondary'
  }

  const contractTypeLabel = (type) => {
    const labels = { general_contractor: 'Генподрядный', subcontractor: 'Субподряд', services: 'Оказание услуг', labor: 'Трудовой' }
    return labels[type] || type || '-'
  }

  const contractStatusLabel = (status) => {
    const labels = { approval: 'На согласовании', in_progress: 'В работе', completed: 'Подписан' }
    return labels[status] || status || '-'
  }

  const stageTypeLabel = (type) => {
    const labels = { stage: 'Этап', payment: 'Платеж', other: 'Другое' }
    return labels[type] || type || '-'
  }

  const stageStatusLabel = (status) => {
    const labels = { planned: 'Запланирован', in_progress: 'В работе', completed: 'Завершен', delayed: 'Задержан' }
    return labels[status] || status || '-'
  }

  const stageStatusClass = (status) => {
    const classes = { planned: 'badge-secondary', in_progress: 'badge-primary', completed: 'badge-success', delayed: 'badge-danger' }
    return classes[status] || 'badge-secondary'
  }

  const docStatusClass = (status) => {
    const classes = {
      draft: 'status-draft',
      signing: 'status-signing',
      signed: 'status-signed',
      canceled: 'status-canceled'
    }
    return classes[status] || 'status-draft'
  }

  const getFileExtension = (fileName = '', fallbackKind = '') => {
    const normalized = String(fileName || '').trim().toLowerCase()
    if (normalized.includes('.')) {
      return normalized.split('.').pop() || ''
    }
    if (fallbackKind === 'pdf') return 'pdf'
    return normalized
  }

  const fileNameParts = (fileName = '') => {
    const normalized = String(fileName || '').trim()
    const dotIndex = normalized.lastIndexOf('.')
    if (dotIndex <= 0) {
      return {
        base: normalized || 'Файл',
        ext: ''
      }
    }
    return {
      base: normalized.slice(0, dotIndex),
      ext: normalized.slice(dotIndex)
    }
  }

  const fileActionClass = (fileName = '', fallbackKind = '') => {
    const ext = getFileExtension(fileName, fallbackKind)
    if (ext === 'pdf') return 'file-action file-action--pdf'
    if (['doc', 'docx', 'rtf', 'odt'].includes(ext)) return 'file-action file-action--word'
    if (['xls', 'xlsx', 'csv', 'ods'].includes(ext)) return 'file-action file-action--excel'
    return 'file-action file-action--other'
  }

  const fileIconClass = (fileName = '', fallbackKind = '') => {
    const ext = getFileExtension(fileName, fallbackKind)
    if (ext === 'pdf') return 'fa-file-pdf'
    if (['doc', 'docx', 'rtf', 'odt'].includes(ext)) return 'fa-file-word'
    if (['xls', 'xlsx', 'csv', 'ods'].includes(ext)) return 'fa-file-excel'
    return 'fa-file'
  }

  const documentTypeLabel = (type) => {
    return docTypes.find(item => item.key === type)?.label || type || '-'
  }

  const documentTypeBadgeClass = (type) => {
    const classes = {
      contract: 'contract-type-pill--violet',
      addendum: 'contract-type-pill--blue',
      act: 'contract-type-pill--sky',
      invoice: 'contract-type-pill--orange'
    }
    return classes[type] || 'contract-type-pill--gray'
  }

  const documentAmountAllowed = (docType) => ['contract', 'addendum', 'act'].includes(docType)

  const dealProductName = (item) => item?.custom_name || item?.product?.name || item?.product_name || 'Товар'

  const shortProductName = (name) => {
    const value = String(name || 'Товар').trim()
    return value.length > 24 ? `${value.slice(0, 24)}…` : value
  }

  const resetPaymentFilters = () => {
    paymentFilters.value = { direction: '', status: '', search: '' }
  }

  const resetDocumentFilters = () => {
    documentFilters.value = { status: '', search: '', docType: '' }
  }

  const openUploadModal = (docType, doc = null, fileKind = 'pdf') => {
    uploadForm.value = {
      docType,
      fileKind,
      status: doc?.status || 'draft',
      amount: '',
      productIds: [],
      file: null,
      documentId: doc ? doc.id : null
    }
    uploadAmountFocused.value = false
    uploadAmountDraft.value = ''
    showUploadModal.value = true
  }

  const closeUploadModal = () => {
    showUploadModal.value = false
    uploadForm.value.file = null
    uploadForm.value.documentId = null
    uploadForm.value.amount = ''
    uploadForm.value.productIds = []
    uploadAmountFocused.value = false
    uploadAmountDraft.value = ''
  }

  const onUploadFileChange = (event) => {
    const file = event.target.files[0]
    uploadForm.value.file = file || null
    isDropActive.value = false
  }

  const triggerUploadFile = () => {
    if (uploadFileInput.value) {
      uploadFileInput.value.click()
    }
  }

  const handleDropOver = (event) => {
    if (event?.dataTransfer) {
      event.dataTransfer.dropEffect = 'copy'
    }
    isDropActive.value = true
  }

  const handleDropLeave = () => {
    isDropActive.value = false
  }

  const handleDropFile = (event) => {
    isDropActive.value = false
    const file = event?.dataTransfer?.files?.[0]
    if (file) {
      uploadForm.value.file = file
      if (uploadFileInput.value) {
        const dataTransfer = new DataTransfer()
        dataTransfer.items.add(file)
        uploadFileInput.value.files = dataTransfer.files
      }
    }
  }

  const submitUpload = async () => {
    if (uploading.value) return
    if (!uploadForm.value.file) {
      alert('Выберите файл для загрузки')
      return
    }
    if (uploadAmountFocused.value) {
      uploadForm.value.amount = parseAmountInput(uploadAmountDraft.value) ?? ''
      uploadAmountFocused.value = false
      uploadAmountDraft.value = ''
    }
    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('file_kind', uploadForm.value.fileKind)
      formData.append('file', uploadForm.value.file)
      formData.append('contract_id', contractId)
      if (uploadForm.value.documentId) {
        formData.append('document_id', uploadForm.value.documentId)
      } else {
        formData.append('doc_type', uploadForm.value.docType)
        formData.append('status', uploadForm.value.status)
        if (documentAmountAllowed(uploadForm.value.docType) && uploadForm.value.amount !== '') {
          formData.append('amount', uploadForm.value.amount)
        }
        if (uploadForm.value.docType === 'invoice' && uploadForm.value.productIds.length) {
          formData.append('product_ids', JSON.stringify(uploadForm.value.productIds))
        }
      }
      const localId = uploadQueue.addLocalUpload({
        fileName: uploadForm.value.file?.name || 'Файл',
        module: 'contracts',
        entityId: contractId
      })
      const data = await api.contracts.uploadDocument(formData, {
        onUploadProgress: (event) => {
          if (!event.total) return
          const progress = (event.loaded / event.total) * 100
          uploadQueue.updateProgress(localId, progress)
        }
      })
      uploadQueue.markQueued(localId, data)
      void loadCard()
      closeUploadModal()
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Ошибка загрузки файла')
    } finally {
      uploading.value = false
    }
  }

  const downloadDocument = async (doc, fileKind, fallbackName = '') => {
    try {
      const defaultName = fileKind === 'pdf' ? 'document.pdf' : 'document.docx'
      const fileName = fileKind === 'pdf'
        ? (doc.pdf_file_name || fallbackName || defaultName)
        : (doc.edit_file_name || fallbackName || defaultName)
      await downloadFromApi(
        `/api/v1/contracts/documents/${doc.id}/download`,
        { params: { file_kind: fileKind } },
        fileName,
        { module: 'contracts', entityId: contractId }
      )
    } catch (error) {
      console.error('Download failed:', error)
      alert('Ошибка скачивания файла')
    }
  }

  const updateDocumentStatus = async (doc) => {
    try {
      await api.contracts.updateDocument(doc.id, { status: doc.status })
    } catch (error) {
      console.error('Status update failed:', error)
      alert('Ошибка обновления статуса')
    }
  }

  const updateDocumentAmount = async (doc) => {
    if (!documentAmountAllowed(doc.doc_type)) return
    try {
      const amount = doc.amount === '' || doc.amount == null ? null : Number(doc.amount)
      await api.contracts.updateDocument(doc.id, { amount })
    } catch (error) {
      console.error('Amount update failed:', error)
      alert('Ошибка обновления суммы')
      void loadCard()
    }
  }

  const openInvoiceProductsModal = (doc) => {
    invoiceProductsDoc.value = doc
    invoiceProductIds.value = (doc.linked_products || []).map(item => item.deal_product_id)
    showInvoiceProductsModal.value = true
  }

  const closeInvoiceProductsModal = () => {
    showInvoiceProductsModal.value = false
    invoiceProductsDoc.value = null
    invoiceProductIds.value = []
    savingInvoiceProducts.value = false
  }

  const saveInvoiceProducts = async () => {
    if (!invoiceProductsDoc.value) return
    savingInvoiceProducts.value = true
    try {
      const updated = await api.contracts.updateDocumentProducts(
        invoiceProductsDoc.value.id,
        { deal_product_ids: invoiceProductIds.value }
      )
      documents.value = documents.value.map(doc => doc.id === updated.id ? updated : doc)
      closeInvoiceProductsModal()
    } catch (error) {
      console.error('Invoice products update failed:', error)
      alert('Ошибка сохранения связей с товарами')
    } finally {
      savingInvoiceProducts.value = false
    }
  }

  const deleteDocument = async (doc) => {
    if (!confirm('Удалить документ?')) return
    try {
      await api.contracts.removeDocument(doc.id)
      void loadCard()
    } catch (error) {
      console.error('Delete failed:', error)
      alert('Ошибка удаления')
    }
  }

  const deleteDocumentFile = async (doc, fileKind, fileName = '') => {
    const kindLabel = fileKind === 'pdf' ? 'PDF' : 'редактируемый файл'
    const targetLabel = fileName || kindLabel
    if (!confirm(`Удалить файл "${targetLabel}"?`)) return
    try {
      await api.contracts.removeDocumentFile(doc.id, fileKind)
      void loadCard()
    } catch (error) {
      console.error('Delete file failed:', error)
      alert('Ошибка удаления файла')
    }
  }

  const resetExpenseForm = () => {
    expenseForm.value = {
      amount: '',
      plan_date: '',
      actual_date: '',
      category_code: ''
    }
    editingExpense.value = null
  }

  const openExpenseModal = (entry = null) => {
    if (entry) {
      editingExpense.value = entry
      expenseForm.value = {
        amount: entry.amount ?? '',
        plan_date: entry.plan_date ? String(entry.plan_date).slice(0, 10) : '',
        actual_date: entry.actual_date ? String(entry.actual_date).slice(0, 10) : '',
        category_code: entry.category_code || ''
      }
    } else {
      resetExpenseForm()
    }
    showExpenseModal.value = true
  }

  const closeExpenseModal = () => {
    showExpenseModal.value = false
    resetExpenseForm()
  }

  const saveExpense = async () => {
    if (!expenseForm.value.amount || !expenseForm.value.plan_date) {
      alert('Укажите сумму и дату планового платежа')
      return
    }
    const payload = {
      amount: Number(expenseForm.value.amount),
      plan_date: expenseForm.value.plan_date,
      actual_date: expenseForm.value.actual_date || null,
      category_code: expenseForm.value.category_code || null
    }
    try {
      if (editingExpense.value?.id) {
        await api.contracts.updateExpense(contractId, editingExpense.value.id, payload)
      } else {
        await api.contracts.createExpense(contractId, payload)
      }
      await loadExpenses()
      closeExpenseModal()
    } catch (error) {
      console.error('Error saving expense:', error)
      alert('Ошибка сохранения расхода')
    }
  }

  const deleteExpense = async (entry) => {
    if (!confirm('Удалить расход?')) return
    try {
      await api.contracts.removeExpense(contractId, entry.id)
      await loadExpenses()
    } catch (error) {
      console.error('Error deleting expense:', error)
      alert('Ошибка удаления расхода')
    }
  }

  const openBulkExpenseModal = () => {
    bulkForm.value = {
      category_code: '',
      amount: '',
      start_date: '',
      frequency: 'month',
      periods: 1
    }
    showBulkExpenseModal.value = true
  }

  const closeBulkExpenseModal = () => {
    showBulkExpenseModal.value = false
  }

  const createBulkExpenses = async () => {
    if (!bulkForm.value.amount || !bulkForm.value.start_date || !bulkForm.value.periods) {
      alert('Заполните сумму, дату начала и количество периодов')
      return
    }
    const payload = {
      category_code: bulkForm.value.category_code || null,
      amount: Number(bulkForm.value.amount),
      start_date: bulkForm.value.start_date,
      frequency: bulkForm.value.frequency,
      periods: Number(bulkForm.value.periods)
    }
    try {
      await api.contracts.createBulkExpenses(contractId, payload)
      await loadExpenses()
      closeBulkExpenseModal()
    } catch (error) {
      console.error('Error creating bulk expenses:', error)
      alert('Ошибка массового создания')
    }
  }

  const contractStatusClass = (status) => {
    const classes = { approval: 'badge-warning', in_progress: 'badge-info', completed: 'badge-success' }
    return classes[status] || 'badge-secondary'
  }

  onMounted(async () => {
    const requestedTab = String(route.query?.tab || '')
    if (['data', 'expenses', 'documents'].includes(requestedTab)) {
      activeTab.value = requestedTab
    }
    await Promise.all([loadCompanies(), loadCard()])
  })

  return {
    // state
    contractId,
    loading,
    uploading,
    contract,
    dealTitle,
    subcontractorTitle,
    documents,
    dealProducts,
    payments,
    paymentSummary,
    stages,
    showUploadModal,
    activeTab,
    statusMenuOpen,
    statusBusy,
    cdStatusOptions,
    companies,
    expenseEntries,
    expenseSummary,
    loadingExpenses,
    showExpenseModal,
    showBulkExpenseModal,
    showInvoiceProductsModal,
    invoiceProductsDoc,
    invoiceProductIds,
    savingInvoiceProducts,
    editingExpense,
    expenseForm,
    bulkForm,
    expenseCategories,
    uploadForm,
    uploadFileInput,
    isDropActive,
    paymentFilters,
    documentFilters,
    docTypes,
    docTypeRows,
    // computeds
    docGroups,
    filteredDocGroups,
    filteredDocumentsList,
    filteredPayments,
    filteredStages,
    isServiceContract,
    expensePayerName,
    expensePayeeName,
    customerName,
    executorName,
    paymentCompletionPercent,
    paidPercent, pendingPercent, unpaidPercent,
    contractHighlights,
    closedStagesCount,
    stagesPlannedAmount,
    sortedDealProducts,
    showUploadAmountField,
    showUploadInvoiceProducts,
    documentAmountHelpText,
    uploadAmountHelpText,
    uploadAmountInputValue,
    // methods
    setActiveTab,
    onChangeStatus,
    contractStatusClass,
    formatAmount,
    formatDate,
    paymentStatusLabel,
    paymentStatusClass,
    contractTypeLabel,
    contractStatusLabel,
    stageTypeLabel,
    stageStatusLabel,
    stageStatusClass,
    docStatusClass,
    fileNameParts,
    fileActionClass,
    fileIconClass,
    documentTypeLabel,
    documentTypeBadgeClass,
    documentAmountAllowed,
    documentAmountInputValue,
    onDocumentAmountFocus,
    onDocumentAmountInput,
    onDocumentAmountBlur,
    onUploadAmountFocus,
    onUploadAmountInput,
    onUploadAmountBlur,
    dealProductName,
    shortProductName,
    resetPaymentFilters,
    resetDocumentFilters,
    openExpenseModal,
    closeExpenseModal,
    saveExpense,
    deleteExpense,
    openBulkExpenseModal,
    closeBulkExpenseModal,
    createBulkExpenses,
    openUploadModal,
    closeUploadModal,
    onUploadFileChange,
    triggerUploadFile,
    handleDropOver,
    handleDropLeave,
    handleDropFile,
    submitUpload,
    toggleDocumentExpanded,
    isDocumentExpanded,
    getDocumentFiles,
    downloadDocument,
    deleteDocumentFile,
    updateDocumentStatus,
    updateDocumentAmount,
    openInvoiceProductsModal,
    closeInvoiceProductsModal,
    saveInvoiceProducts,
    deleteDocument,
  }
}
