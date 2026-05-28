import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import * as documentRegistryApi from '../../../services/api/documentRegistry'
import { downloadFromHref } from '../../../utils/download'
import { useUploadQueueStore } from '../../../stores/uploadQueue'
import { useCompaniesStore } from '../../../stores/companies'
import { staticOurCompanies } from '../../../config/appVariant'

/**
 * Composable for DocumentRegistry view state & API logic.
 *
 * Extracted from the original monolithic DocumentRegistry.vue during the
 * structural split. All API calls go through api.documentRegistry.*
 * (see services/api/documentRegistry.js). No business logic changes.
 */
export function useDocumentRegistryState() {
  const uploadQueue = useUploadQueueStore()
  const companiesStore = useCompaniesStore()
  const documents = ref([])
  const companies = ref([])
  const deals = ref([])
  const documentOptions = ref([])
  const relations = ref([])
  const loading = ref(false)
  const saving = ref(false)
  const showModal = ref(false)
  const isEditing = ref(false)
  const activeTab = ref('documents')
  const search = ref('')
  const selectedStatus = ref('all')
  const selectedType = ref('all')
  const dateFrom = ref('')
  const dateTo = ref('')
  const page = ref(1)
  const pageSize = 25
  const hasNext = ref(false)
  let searchTimeout

  // Split-view state
  const selectedDoc = ref(null)
  const selectedDocChannels = ref({})
  const expandedChannel = ref(null)
  const pendingChannelFiles = ref({})

  const packages = ref([])
  const loadingPackages = ref(false)
  const savingPackage = ref(false)
  const showPackageModal = ref(false)
  const isPackageEditing = ref(false)
  const packageSearch = ref('')
  const packageStatus = ref('all')
  let packageSearchTimeout

  // Drag & drop state
  const docPoolSearch = ref('')
  const availableDocs = ref([])
  const dropTarget = ref(null)
  const draggedDoc = ref(null)
  const isDropTarget = ref(false)
  const selectedDocRelations = ref([])

  const documentForm = ref({
    doc_type: 'outgoing_letter',
    title: '',
    number: '',
    document_date: '',
    status: 'draft',
    project_id: '',
    counterparty_id: '',
    our_company_id: ''
  })

  const packageForm = ref({
    title: '',
    package_date: '',
    status: 'draft',
    project_id: '',
    counterparty_id: '',
    our_company_id: ''
  })

  const packageItems = ref([])
  const selectedPackageDocumentId = ref('')

  const channelKeys = ['post', 'courier', 'email', 'edo']
  const channelLabels = {
    post: 'Почта РФ',
    courier: 'Курьер',
    email: 'Эл. почта',
    edo: 'ЭДО'
  }
  const parentChannelFiles = computed(() => {
    return channelKeys
      .map((key) => ({
        key,
        label: channelLabels[key],
        count: selectedDocChannels.value[key]?.uploaded?.length || 0
      }))
      .filter((item) => item.count > 0)
  })
  const channels = ref({
    post: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null },
    courier: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null },
    email: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null },
    edo: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null }
  })
  const dispatchId = ref('')
  const relationForm = ref({
    related_document_id: '',
    relation_type: 'link'
  })

  const resetChannels = () => {
    channels.value = {
      post: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null },
      courier: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null },
      email: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null },
      edo: { enabled: false, date: '', track: '', files: [], uploaded: [], path: '', id: null }
    }
    dispatchId.value = ''
  }

  const ourCompanies = ref(
    staticOurCompanies.map((company) => ({
      id: company.key,
      name: company.name
    }))
  )

  const loadDocuments = async () => {
    loading.value = true
    try {
      const params = {
        skip: (page.value - 1) * pageSize,
        limit: pageSize
      }
      if (search.value.trim()) params.search = search.value.trim()
      if (selectedStatus.value !== 'all') params.status = selectedStatus.value
      if (selectedType.value !== 'all') params.doc_type = selectedType.value
      if (dateFrom.value) params.date_from = dateFrom.value
      if (dateTo.value) params.date_to = dateTo.value
      const result = await documentRegistryApi.list(params)
      documents.value = result || []
      hasNext.value = documents.value.length === pageSize
    } catch (error) {
      console.error('Error loading documents:', error)
    } finally {
      loading.value = false
    }
  }

  const loadCompanies = async () => {
    await companiesStore.ensureLoaded()
    companies.value = companiesStore.items
  }

  const loadDeals = async () => {
    const response = await axios.get('/api/v1/deals/')
    deals.value = response.data || []
  }

  const loadDocumentOptions = async () => {
    try {
      const result = await documentRegistryApi.list({ skip: 0, limit: 500 })
      documentOptions.value = result || []
    } catch (error) {
      console.error('Error loading document options:', error)
      documentOptions.value = []
    }
  }

  const loadRelations = async (docId) => {
    if (!docId) return
    try {
      const result = await documentRegistryApi.listRelations(docId)
      relations.value = result || []
    } catch (error) {
      console.error('Error loading relations:', error)
      relations.value = []
    }
  }

  const addRelation = async () => {
    if (!documentForm.value.id || !relationForm.value.related_document_id) return
    await documentRegistryApi.addRelation(documentForm.value.id, relationForm.value)
    relationForm.value = { related_document_id: '', relation_type: 'link' }
    await loadRelations(documentForm.value.id)
  }

  const removeRelation = async (relation) => {
    await documentRegistryApi.removeRelation(relation.id)
    await loadRelations(documentForm.value.id)
  }

  const triggerSearch = () => {
    clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
      page.value = 1
      loadDocuments()
    }, 300)
  }

  const changeFilters = () => {
    page.value = 1
    loadDocuments()
  }

  const clearFilters = () => {
    search.value = ''
    selectedStatus.value = 'all'
    selectedType.value = 'all'
    dateFrom.value = ''
    dateTo.value = ''
    page.value = 1
    loadDocuments()
  }

  const nextPage = () => {
    if (hasNext.value) {
      page.value += 1
      loadDocuments()
    }
  }

  const prevPage = () => {
    if (page.value > 1) {
      page.value -= 1
      loadDocuments()
    }
  }

  const loadPackages = async () => {
    loadingPackages.value = true
    try {
      const params = { skip: 0, limit: 200 }
      if (packageSearch.value.trim()) params.search = packageSearch.value.trim()
      if (packageStatus.value !== 'all') params.status = packageStatus.value
      const result = await documentRegistryApi.listPackages(params)
      packages.value = result || []
    } catch (error) {
      console.error('Error loading packages:', error)
    } finally {
      loadingPackages.value = false
    }
  }

  const triggerPackageSearch = () => {
    clearTimeout(packageSearchTimeout)
    packageSearchTimeout = setTimeout(loadPackages, 300)
  }

  const loadPackageItems = async (packageId) => {
    if (!packageId) return
    const result = await documentRegistryApi.listPackageItems(packageId)
    packageItems.value = result || []
  }

  const openPackageCreate = () => {
    isPackageEditing.value = false
    showPackageModal.value = true
    packageForm.value = {
      title: '',
      package_date: '',
      status: 'draft',
      project_id: '',
      counterparty_id: '',
      our_company_id: ''
    }
    selectedPackageDocumentId.value = ''
    packageItems.value = []
    loadDocumentOptions()
  }

  const openPackageEdit = async (pkg) => {
    isPackageEditing.value = true
    showPackageModal.value = true
    packageForm.value = { ...pkg }
    selectedPackageDocumentId.value = ''
    await loadDocumentOptions()
    await loadPackageItems(pkg.id)
  }

  const savePackage = async () => {
    if (!packageForm.value.title.trim()) {
      alert('Название обязательно')
      return
    }
    savingPackage.value = true
    try {
      if (isPackageEditing.value) {
        await documentRegistryApi.updatePackage(packageForm.value.id, packageForm.value)
      } else {
        const res = await documentRegistryApi.createPackage(packageForm.value)
        packageForm.value.id = res.id
      }
      await loadPackages()
      closePackageModal()
    } catch (error) {
      console.error('Error saving package:', error)
      alert('Ошибка сохранения пачки')
    } finally {
      savingPackage.value = false
    }
  }

  const deletePackage = async (pkg) => {
    if (!confirm(`Удалить пачку "${pkg.title}"?`)) return
    await documentRegistryApi.removePackage(pkg.id)
    await loadPackages()
  }

  const addPackageItem = async () => {
    if (!packageForm.value.id || !selectedPackageDocumentId.value) return
    await documentRegistryApi.addPackageItem(packageForm.value.id, {
      document_id: selectedPackageDocumentId.value
    })
    selectedPackageDocumentId.value = ''
    await loadPackageItems(packageForm.value.id)
  }

  const removePackageItem = async (item) => {
    await documentRegistryApi.removePackageItem(item.id)
    await loadPackageItems(packageForm.value.id)
  }

  const closePackageModal = () => {
    showPackageModal.value = false
    isPackageEditing.value = false
  }

  const openCreate = () => {
    isEditing.value = false
    showModal.value = true
    documentForm.value = {
      doc_type: 'outgoing_letter',
      title: '',
      number: '',
      document_date: '',
      status: 'draft',
      project_id: '',
      counterparty_id: '',
      our_company_id: ''
    }
    relations.value = []
    relationForm.value = { related_document_id: '', relation_type: 'link' }
    loadDocumentOptions()
    resetChannels()
  }

  const loadDispatch = async (docId) => {
    resetChannels()
    const dispatches = await documentRegistryApi.listDispatches({ document_id: docId })
    const dispatch = (dispatches || [])[0]
    if (!dispatch) return
    dispatchId.value = dispatch.id
    const channelList = (await documentRegistryApi.listDispatchChannels(dispatch.id)) || []
    channelList.forEach((ch) => {
      if (!channels.value[ch.channel]) return
      channels.value[ch.channel].enabled = true
      channels.value[ch.channel].date = ch.channel_date
      channels.value[ch.channel].track = ch.track_number || ''
      channels.value[ch.channel].path = ch.confirmation_file || ''
      channels.value[ch.channel].files = []
      channels.value[ch.channel].uploaded = []
      channels.value[ch.channel].id = ch.id
    })
    await Promise.all(channelKeys.map((key) => loadChannelFiles(key)))
  }

  const editDocument = async (doc) => {
    isEditing.value = true
    showModal.value = true
    documentForm.value = { ...doc }
    relationForm.value = { related_document_id: '', relation_type: 'link' }
    await loadDocumentOptions()
    await loadRelations(doc.id)
    await loadDispatch(doc.id)
  }

  const loadChannelFiles = async (channelKey) => {
    const channelState = channels.value[channelKey]
    if (!channelState?.id || !channelState.path || !dispatchId.value) {
      if (channelState) channelState.uploaded = []
      return
    }
    try {
      const result = await documentRegistryApi.listChannelFiles(dispatchId.value, channelState.id)
      const items = result || []
      channelState.uploaded = items.filter(item => item.type === 'file')
    } catch (error) {
      console.error('Error loading channel files:', error)
      channelState.uploaded = []
    }
  }

  const handleChannelFilesChange = (channelKey, event) => {
    const files = Array.from(event.target.files || [])
    channels.value[channelKey].files = files
  }

  const removeChannelFile = (channelKey, index) => {
    const files = channels.value[channelKey].files || []
    channels.value[channelKey].files = files.filter((_, idx) => idx !== index)
  }

  const downloadChannelFile = async (channelKey, file) => {
    const channelState = channels.value[channelKey]
    if (!channelState?.id || !dispatchId.value) return
    try {
      const result = await documentRegistryApi.downloadChannelFile(
        dispatchId.value,
        channelState.id,
        { file_path: file.path }
      )
      if (result?.href) {
        await downloadFromHref(
          result.href,
          file.name || 'file',
          { module: 'document_registry', entityId: dispatchId.value }
        )
      }
    } catch (error) {
      console.error('Error downloading file:', error)
    }
  }

  const deleteUploadedChannelFile = async (channelKey, file) => {
    const channelState = channels.value[channelKey]
    if (!channelState?.id || !dispatchId.value) return
    if (!confirm('Delete file?')) return
    try {
      await documentRegistryApi.removeChannelFile(
        dispatchId.value,
        channelState.id,
        { file_path: file.path }
      )
      await loadChannelFiles(channelKey)
    } catch (error) {
      console.error('Error deleting file:', error)
    }
  }

  const queueChannelFiles = async (dispatchId, channelId, files) => {
    if (!files || !files.length) return
    for (const file of files) {
      const localId = uploadQueue.addLocalUpload({
        fileName: file.name,
        module: 'document_registry',
        entityId: dispatchId
      })
      const form = new FormData()
      form.append('file', file)
      try {
        const result = await documentRegistryApi.uploadChannelFile(
          dispatchId,
          channelId,
          form,
          {
            onUploadProgress: (event) => {
              if (!event.total) return
              const progress = (event.loaded / event.total) * 100
              uploadQueue.updateProgress(localId, progress)
            }
          }
        )
        uploadQueue.markQueued(localId, result)
      } catch (error) {
        const detail = error?.response?.data?.detail || 'Ошибка загрузки'
        uploadQueue.markError(localId, detail)
        console.error('Error queueing file:', error)
      }
    }
  }

  const saveDispatchChannels = async (docId) => {
    const enabled = channelKeys.filter((key) => channels.value[key].enabled)
    if (enabled.length === 0) {
      if (dispatchId.value) {
        await documentRegistryApi.removeDispatch(dispatchId.value)
      }
      return
    }
    if (!dispatchId.value) {
      const dispatch = await documentRegistryApi.createDispatch({ document_id: docId })
      dispatchId.value = dispatch.id
    }
    for (const key of channelKeys) {
      const channelState = channels.value[key]
      if (!channelState.enabled) {
        if (channelState.id) {
          await documentRegistryApi.removeDispatchChannel(dispatchId.value, channelState.id)
          channelState.id = null
          channelState.path = ''
          channelState.uploaded = []
          channelState.files = []
        }
        continue
      }
      if (!channelState.date) {
        throw new Error(`Дата обязательна для канала "${channelLabels[key]}"`)
      }
      const payload = {
        channel: key,
        channel_date: channelState.date,
        track_number: key === 'post' ? channelState.track || null : null
      }
      if (channelState.id) {
        await documentRegistryApi.updateDispatchChannel(dispatchId.value, channelState.id, payload)
      } else {
        const res = await documentRegistryApi.createDispatchChannel(dispatchId.value, payload)
        channelState.id = res.id
      }
      if (channelState.files && channelState.files.length > 0) {
        await queueChannelFiles(dispatchId.value, channelState.id, channelState.files)
        channelState.files = []
      }
    }
  }

  const buildDocumentPayload = (source) => ({
    doc_type: source.doc_type,
    title: source.title,
    number: source.number || null,
    document_date: source.document_date || null,
    status: source.status || 'draft',
    project_id: source.project_id || null,
    counterparty_id: source.counterparty_id || null,
    our_company_id: source.our_company_id || null,
    source_type: source.source_type || null,
    source_id: source.source_id || null
  })

  const saveDocument = async () => {
    if (!documentForm.value.title.trim()) {
      alert('Название обязательно')
      return
    }
    const missingChannel = channelKeys.find(
      (key) => channels.value[key].enabled && !channels.value[key].date
    )
    if (missingChannel) {
      alert(`Дата обязательна для канала "${channelLabels[missingChannel]}"`)
      return
    }
    if (!isEditing.value && !documentForm.value.document_date) {
      alert('Document date is required')
      return
    }
    saving.value = true
    try {
      let response
      if (isEditing.value) {
        response = await documentRegistryApi.update(
          documentForm.value.id,
          buildDocumentPayload(documentForm.value)
        )
      } else {
        response = await documentRegistryApi.create(
          buildDocumentPayload(documentForm.value)
        )
        documentForm.value.id = response.id
      }
      await saveDispatchChannels(documentForm.value.id)
      await loadDocuments()
      closeModal()
    } catch (error) {
      console.error('Error saving document:', error)
      alert(error.message || 'Ошибка сохранения документа')
    } finally {
      saving.value = false
    }
  }

  const deleteDocument = async (doc) => {
    if (!confirm(`Удалить документ "${doc.title}"?`)) return
    await documentRegistryApi.remove(doc.id)
    await loadDocuments()
  }

  const closeModal = () => {
    showModal.value = false
    isEditing.value = false
  }

  const formatDate = (value) => {
    if (!value) return '-'
    return new Date(value).toLocaleDateString('ru-RU')
  }

  const getCompanyName = (id) => {
    if (!id) return '-'
    const our = ourCompanies.value.find(c => c.id === id)
    if (our) return our.name
    const company = companies.value.find(c => c.id === id)
    return company ? company.name : '-'
  }

  const getDealTitle = (id) => {
    if (!id) return '-'
    const deal = deals.value.find(d => d.id === id)
    return deal ? deal.title : '-'
  }

  const getDocumentTitle = (id) => {
    if (!id) return '-'
    const doc = documentOptions.value.find(d => d.id === id) || documents.value.find(d => d.id === id)
    return doc ? doc.title : id
  }

  const getStatusClass = (status) => {
    const classes = {
      draft: 'badge-warning-subtle',
      sent: 'badge-info-subtle',
      received: 'badge-success-subtle',
      archived: 'badge-secondary'
    }
    return classes[status] || 'badge-secondary'
  }

  const getStatusText = (status) => {
    const texts = {
      draft: 'Проект',
      sent: 'Направлен',
      received: 'Получен',
      archived: 'Архив'
    }
    return texts[status] || status
  }

  const getTypeText = (type) => {
    const texts = {
      outgoing_letter: 'Исходящее письмо',
      contract: 'Договор',
      addendum: 'Доп. соглашение',
      act: 'Акт',
      waybill: 'Накладная',
      result: 'Результат работ',
      other: 'Прочее'
    }
    return texts[type] || type
  }

  const getTypeIcon = (type) => {
    const icons = { outgoing_letter: '✉️', contract: '📄', addendum: '📝', act: '📋', waybill: '📦', result: '✅', other: '📁' }
    return icons[type] || '📄'
  }

  const getChannelIcon = (ch) => {
    const icons = { post: '📮', courier: '📦', email: '📧', edo: '📑' }
    return icons[ch] || '📤'
  }

  const selectDocument = async (doc) => {
    selectedDoc.value = doc
    selectedDocChannels.value = { post: {}, courier: {}, email: {}, edo: {} }
    selectedDocRelations.value = []

    try {
      // Load dispatch info for this document
      let dispatches = await documentRegistryApi.listDispatches({ document_id: doc.id })
      let dispatch = (dispatches || [])[0]

      // If no dispatch, try to inherit from parent document
      if (!dispatch) {
        const parentRels = await documentRegistryApi.listParentRelations(doc.id)
        const parentRelation = (parentRels || [])[0]
        if (parentRelation) {
          dispatches = await documentRegistryApi.listDispatches({ document_id: parentRelation.document_id })
          dispatch = (dispatches || [])[0]
        }
      }

      if (dispatch) {
        const channelList = (await documentRegistryApi.listDispatchChannels(dispatch.id)) || []
        channelList.forEach((c) => {
          selectedDocChannels.value[c.channel] = {
            enabled: true,
            date: c.channel_date,
            track: c.track_number || '',
            uploaded: []
          }
        })
        // Load files in background (do not await)
        Promise.all(channelList.map(async (c) => {
          try {
            const filesRes = await documentRegistryApi.listChannelFiles(dispatch.id, c.id)
            if (selectedDocChannels.value[c.channel]) {
              selectedDocChannels.value[c.channel].uploaded = (filesRes || []).filter(f => f.type === 'file')
            }
          } catch (e) {
            console.error(`Error loading files for channel ${c.channel}:`, e)
          }
        }))
      }

      // Load related documents
      await loadRelatedDocuments(doc.id)
    } catch (e) {
      console.error('Error loading document details:', e)
    }
  }

  const loadRelatedDocuments = async (docId) => {
    try {
      selectedDocRelations.value = []

      // Load child relations (documents this doc links TO) - now eagerly loaded
      const childRes = await documentRegistryApi.listRelations(docId)
      const children = (childRes || []).map(rel => {
        if (rel.related_document) {
          return {
            ...rel.related_document,
            relationId: rel.id,
            relationType: 'child'
          }
        }
        return null
      }).filter(d => d)
      selectedDocRelations.value.push(...children)

      // Load parent relations (documents that link TO this doc) - now eagerly loaded
      const parentRes = await documentRegistryApi.listParentRelations(docId)
      const parents = (parentRes || []).map(rel => {
        if (rel.document) {
          return {
            ...rel.document,
            relationId: rel.id,
            relationType: 'parent'
          }
        }
        return null
      }).filter(d => d)
      selectedDocRelations.value.push(...parents)
    } catch (e) {
      console.error('Error loading relations:', e)
      selectedDocRelations.value = []
    }
  }

  const onDropRelatedDoc = async (event) => {
    event.preventDefault()
    isDropTarget.value = false
    if (!draggedDoc.value || !selectedDoc.value) return
    if (draggedDoc.value.id === selectedDoc.value.id) {
      alert('Нельзя связать документ с самим собой')
      return
    }

    try {
      await documentRegistryApi.addRelation(selectedDoc.value.id, {
        related_document_id: draggedDoc.value.id,
        relation_type: 'child'
      })
      await loadRelatedDocuments(selectedDoc.value.id)
      draggedDoc.value = null
    } catch (e) {
      if (e.response?.status === 400) {
        alert('Этот документ уже связан!')
      } else {
        console.error('Error adding relation:', e)
        alert('Ошибка при создании связи')
      }
    }
  }

  const removeRelatedDoc = async (relationId) => {
    if (!selectedDoc.value || !relationId) return
    try {
      await documentRegistryApi.removeRelation(relationId)
      await loadRelatedDocuments(selectedDoc.value.id)
    } catch (e) {
      console.error('Error removing relation:', e)
    }
  }

  const toggleChannel = (ch) => {
    expandedChannel.value = expandedChannel.value === ch ? null : ch
    if (!selectedDocChannels.value[ch]) {
      selectedDocChannels.value[ch] = { enabled: false, date: '', track: '', uploaded: [] }
    }
  }

  const dragOverChannel = ref(null)

  const handleDetailChannelUpload = (ch, event) => {
    pendingChannelFiles.value[ch] = Array.from(event.target.files || [])
  }

  const handleChannelFileDrop = (ch, event) => {
    dragOverChannel.value = null
    const files = Array.from(event.dataTransfer.files || [])
    if (files.length) {
      pendingChannelFiles.value[ch] = files
    }
  }

  const removePendingChannelFile = (ch, index) => {
    const files = pendingChannelFiles.value[ch] || []
    pendingChannelFiles.value[ch] = files.filter((_, idx) => idx !== index)
  }

  const downloadDetailChannelFile = async (ch, file) => {
    if (!selectedDoc.value) return
    try {
      // Find dispatch (own or inherited)
      let dispatches = await documentRegistryApi.listDispatches({ document_id: selectedDoc.value.id })
      let dispatch = (dispatches || [])[0]

      if (!dispatch) {
        const parentRels = await documentRegistryApi.listParentRelations(selectedDoc.value.id)
        const parentRelation = (parentRels || [])[0]
        if (parentRelation) {
          dispatches = await documentRegistryApi.listDispatches({ document_id: parentRelation.document_id })
          dispatch = (dispatches || [])[0]
        }
      }

      if (!dispatch) return
      const channelRes = await documentRegistryApi.listDispatchChannels(dispatch.id)
      const chData = (channelRes || []).find(c => c.channel === ch)
      if (!chData) return
      const dl = await documentRegistryApi.downloadChannelFile(dispatch.id, chData.id, { file_path: file.path })
      if (dl?.href) {
        await downloadFromHref(
          dl.href,
          file.name || 'file',
          { module: 'document_registry', entityId: dispatch.id }
        )
      }
    } catch (e) {
      console.error('Error downloading:', e)
    }
  }

  const deleteDetailChannelFile = async (ch, file) => {
    if (!selectedDoc.value) return
    if (!confirm('Delete file?')) return
    try {
      let dispatches = await documentRegistryApi.listDispatches({ document_id: selectedDoc.value.id })
      let dispatch = (dispatches || [])[0]

      if (!dispatch) {
        const parentRels = await documentRegistryApi.listParentRelations(selectedDoc.value.id)
        const parentRelation = (parentRels || [])[0]
        if (parentRelation) {
          dispatches = await documentRegistryApi.listDispatches({ document_id: parentRelation.document_id })
          dispatch = (dispatches || [])[0]
        }
      }

      if (!dispatch) return
      const channelRes = await documentRegistryApi.listDispatchChannels(dispatch.id)
      const chData = (channelRes || []).find(c => c.channel === ch)
      if (!chData) return
      await documentRegistryApi.removeChannelFile(dispatch.id, chData.id, { file_path: file.path })
      const filesRes = await documentRegistryApi.listChannelFiles(dispatch.id, chData.id)
      if (selectedDocChannels.value[ch]) {
        selectedDocChannels.value[ch].uploaded = (filesRes || []).filter(f => f.type === 'file')
      }
    } catch (e) {
      console.error('Error deleting:', e)
    }
  }

  const getChannelPosition = (ch) => {
    // Calculate position % based on date relative to mix/max dates
    const dates = Object.values(selectedDocChannels.value)
      .filter(c => c.enabled && c.date)
      .map(c => new Date(c.date).getTime())

    if (!dates.length) return 50 // Default center

    const min = Math.min(...dates)
    const max = Math.max(...dates)
    const range = max - min

    // If single date or no range, center
    if (range === 0) return 50

    const current = new Date(selectedDocChannels.value[ch].date).getTime()
    // Add padding (10% each side)
    const percent = ((current - min) / range) * 80 + 10
    return Math.round(percent)
  }

  const saveChannelChanges = async (ch) => {
    if (!selectedDoc.value) return
    const chState = selectedDocChannels.value[ch]
    if (!chState.enabled) return
    if (!chState.date) {
      alert(`Дата обязательна для канала "${channelLabels[ch]}"`)
      return
    }

    try {
      // Get or create dispatch
      let dispatches = await documentRegistryApi.listDispatches({ document_id: selectedDoc.value.id })
      let dispatch = (dispatches || [])[0]
      if (!dispatch) {
        dispatch = await documentRegistryApi.createDispatch({ document_id: selectedDoc.value.id })
      }

      // Get existing channel or create
      const channelRes = await documentRegistryApi.listDispatchChannels(dispatch.id)
      let chData = (channelRes || []).find(c => c.channel === ch)

      const payload = { channel: ch, channel_date: chState.date, track_number: ch === 'post' ? chState.track : null }
      if (chData) {
        await documentRegistryApi.updateDispatchChannel(dispatch.id, chData.id, payload)
      } else {
        chData = await documentRegistryApi.createDispatchChannel(dispatch.id, payload)
      }

      // Upload pending files
      if (pendingChannelFiles.value[ch]?.length) {
        await queueChannelFiles(dispatch.id, chData.id, pendingChannelFiles.value[ch])
        pendingChannelFiles.value[ch] = []
      }

      // Reload
      await selectDocument(selectedDoc.value)
      expandedChannel.value = null
    } catch (e) {
      console.error('Error saving channel:', e)
      alert('Ошибка сохранения')
    }
  }

  // Drag & drop functions
  const loadAvailableDocs = async () => {
    try {
      const params = { skip: 0, limit: 100 }
      if (docPoolSearch.value.trim()) params.search = docPoolSearch.value.trim()
      const result = await documentRegistryApi.list(params)
      availableDocs.value = result || []
    } catch (e) {
      console.error('Error loading docs:', e)
    }
  }

  const onDragStart = (event, doc) => {
    draggedDoc.value = doc
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData('text/plain', doc.id)
  }

  const onDropToPackage = async (event, pkg) => {
    event.preventDefault()
    dropTarget.value = null
    if (!draggedDoc.value || !pkg.id) return

    try {
      await documentRegistryApi.addPackageItem(pkg.id, {
        document_id: draggedDoc.value.id
      })
      // Update doc count
      await loadPackagesWithCounts()
      draggedDoc.value = null
    } catch (e) {
      console.error('Error adding to package:', e)
    }
  }

  const loadPackagesWithCounts = async () => {
    await loadPackages()
    // Load doc counts for each package
    for (const pkg of packages.value) {
      try {
        const res = await documentRegistryApi.listPackageItems(pkg.id)
        pkg.docCount = (res || []).length
      } catch (e) {
        pkg.docCount = 0
      }
    }
  }

  onMounted(() => {
    loadDocuments()
    loadCompanies()
    loadDeals()
  })

  return {
    documents,
    companies,
    deals,
    documentOptions,
    relations,
    relationForm,
    loading,
    saving,
    showModal,
    isEditing,
    activeTab,
    ourCompanies,
    search,
    selectedStatus,
    selectedType,
    dateFrom,
    dateTo,
    page,
    hasNext,
    documentForm,
    channelKeys,
    channelLabels,
    channels,
    packages,
    loadingPackages,
    showPackageModal,
    isPackageEditing,
    savingPackage,
    packageForm,
    packageItems,
    selectedPackageDocumentId,
    packageSearch,
    packageStatus,
    openCreate,
    loadDocuments,
    triggerSearch,
    changeFilters,
    clearFilters,
    nextPage,
    prevPage,
    editDocument,
    saveDocument,
    deleteDocument,
    openPackageCreate,
    openPackageEdit,
    savePackage,
    deletePackage,
    loadPackages,
    triggerPackageSearch,
    closePackageModal,
    addPackageItem,
    removePackageItem,
    closeModal,
    addRelation,
    removeRelation,
    handleChannelFilesChange,
    removeChannelFile,
    downloadChannelFile,
    deleteUploadedChannelFile,
    formatDate,
    getCompanyName,
    getDealTitle,
    getDocumentTitle,
    getStatusClass,
    getStatusText,
    getTypeText,
    getTypeIcon,
    getChannelIcon,
    selectedDoc,
    selectedDocChannels,
    selectDocument,
    expandedChannel,
    toggleChannel,
    handleDetailChannelUpload,
    downloadDetailChannelFile,
    deleteDetailChannelFile,
    saveChannelChanges,
    // Drag & drop
    docPoolSearch,
    availableDocs,
    dropTarget,
    onDragStart,
    onDropToPackage,
    loadAvailableDocs,
    // Related docs
    isDropTarget,
    selectedDocRelations,
    onDropRelatedDoc,
    removeRelatedDoc,
    // File Drag Drop
    dragOverChannel,
    handleChannelFileDrop,
    pendingChannelFiles,
    parentChannelFiles,
    removePendingChannelFile,
    getChannelPosition
  }
}
