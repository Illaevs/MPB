<template>
  <div class="accreditations-sub">
    <div class="accreditations-sub__toolbar">
      <div>
        <h2 class="accreditations-sub__title">Аккредитации подрядчика</h2>
        <p class="accreditations-sub__subtitle">Загрузка документов и отправка направлений на проверку</p>
      </div>
      <div class="accreditations-sub__selector">
        <UiSelect
          v-model="selectedCompanyId"
          :options="companyOptions"
          placeholder="Выберите подрядчика"
          @change="loadAll"
        />
      </div>
    </div>

    <UiEmptyState
      v-if="!selectedCompanyId"
      class="accreditations-sub__empty"
      icon="fas fa-building"
      title="Выберите компанию"
      description="Выберите подрядчика сверху, чтобы управлять документами и направлениями аккредитации."
    />

    <div v-else class="accreditations-sub__layout">
      <UiCard class="accreditations-sub__documents" padding="md">
        <template #header>
          <div class="section-header">
            <div>
              <h3 class="section-header__title">Документы</h3>
              <p class="section-header__subtitle">Текущие версии и загрузка новых файлов</p>
            </div>
          </div>
        </template>

        <div class="documents-list">
          <article v-for="group in groupedDocuments" :key="group.type" class="doc-group">
            <header class="doc-group__header">
              <div class="doc-group__title-wrap">
                <span class="doc-group__icon">{{ getDocIcon(group.type) }}</span>
                <div>
                  <div class="doc-group__title">{{ docTypeLabel(group.type, group.items[0]?.doc_value) }}</div>
                  <div class="doc-group__subtitle">
                    {{ group.items.length > 1 ? `Версий: ${group.items.length}` : 'Одна версия' }}
                  </div>
                </div>
              </div>
              <div class="doc-group__header-actions">
                <UiButton
                  v-if="group.items.length > 1"
                  variant="ghost"
                  size="xs"
                  @click="toggleHistory(group.type)"
                >
                  {{ isHistoryOpen(group.type) ? 'Скрыть историю' : `История +${group.items.length - 1}` }}
                </UiButton>
                <UiButton
                  variant="outline"
                  size="xs"
                  icon-left="fas fa-plus"
                  @click="startNewVersion(group)"
                >
                  Версия
                </UiButton>
              </div>
            </header>

            <div class="doc-item">
              <div class="doc-item__body">
                <div class="doc-item__name">{{ group.items[0]?.file_name || 'Файл' }}</div>
                <div class="doc-item__meta">
                  <UiBadge size="sm" :variant="getStatusVariant(group.items[0]?.status)">
                    {{ statusLabel(group.items[0]?.status) }}
                  </UiBadge>
                </div>
                <div v-if="group.items[0]?.comment" class="doc-item__comment">
                  <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                  <span>{{ group.items[0].comment }}</span>
                </div>
              </div>
              <div class="doc-item__actions">
                <UiIconButton
                  icon="fas fa-download"
                  label="Скачать документ"
                  size="sm"
                  :disabled="!group.items[0]?.yandex_path"
                  @click="downloadDocument(group.items[0])"
                />
                <UiIconButton
                  icon="fas fa-trash"
                  label="Удалить документ"
                  variant="danger"
                  size="sm"
                  :disabled="group.items[0]?.status === 'approved'"
                  @click="removeDocument(group.items[0])"
                />
              </div>
            </div>

            <div v-if="isHistoryOpen(group.type)" class="doc-history">
              <div v-for="doc in group.items.slice(1)" :key="doc.id" class="doc-history__item">
                <div class="doc-history__body">
                  <div class="doc-history__name">{{ doc.file_name || 'Файл' }}</div>
                  <UiBadge size="sm" :variant="getStatusVariant(doc.status)">
                    {{ statusLabel(doc.status) }}
                  </UiBadge>
                </div>
                <UiIconButton
                  icon="fas fa-download"
                  label="Скачать документ"
                  size="sm"
                  :disabled="!doc.yandex_path"
                  @click="downloadDocument(doc)"
                />
              </div>
            </div>
          </article>

          <UiEmptyState
            v-if="!groupedDocuments.length"
            class="documents-list__empty"
            icon="fas fa-folder-open"
            title="Документы не загружены"
            description="Добавьте первый документ ниже, чтобы отправить его на аккредитацию."
          />
        </div>

        <div class="upload-section">
          <div class="section-header">
            <div>
              <h4 class="section-header__title section-header__title--sm">Добавить документ</h4>
              <p class="section-header__subtitle">Новая версия автоматически прикрепится к выбранному типу документа</p>
            </div>
          </div>

          <div class="upload-form">
            <UiSelect
              v-model="newDoc.doc_type"
              :options="docTypeOptions"
              placeholder="Выберите тип документа"
            />
            <UiSelect
              v-if="newDoc.doc_type === 'sro'"
              v-model="newDoc.doc_value"
              :options="sroOptions"
              placeholder="Уровень СРО"
            />

            <div
              class="file-upload-zone"
              @click="$refs.fileInput.click()"
              @dragover.prevent
              @drop.prevent="onFileDrop"
            >
              <input ref="fileInput" type="file" class="sr-only" @change="onFileSelect">
              <i class="fas fa-cloud-upload-alt file-upload-zone__icon" aria-hidden="true"></i>
              <div v-if="selectedFile" class="file-upload-zone__name">{{ selectedFile.name }}</div>
              <div v-else class="file-upload-zone__hint">Перетащите файл сюда или нажмите для выбора</div>
            </div>

            <UiButton
              variant="primary"
              block
              :loading="uploading"
              icon-left="fas fa-upload"
              :disabled="!selectedFile || !newDoc.doc_type"
              @click="uploadDocument"
            >
              Загрузить
            </UiButton>
          </div>
        </div>
      </UiCard>

      <UiCard class="accreditations-sub__directions" padding="md">
        <template #header>
          <div class="section-header">
            <div>
              <h3 class="section-header__title">Направления</h3>
              <p class="section-header__subtitle">Отметьте направления и отправьте их на проверку</p>
            </div>
          </div>
        </template>

        <div class="directions-table-wrap">
          <table class="directions-table">
            <thead>
              <tr>
                <th>Направление</th>
                <th>Статус</th>
                <th class="text-center">Выбрать</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dir in directions" :key="dir.id" :class="{ 'directions-table__row--locked': isDirectionLocked(dir.id) }">
                <td class="direction-name">{{ dir.name }}</td>
                <td>
                  <UiBadge size="sm" :variant="getStatusVariant(accreditationMap[dir.id]?.status)">
                    {{ statusLabel(accreditationMap[dir.id]?.status) }}
                  </UiBadge>
                </td>
                <td class="text-center">
                  <input
                    v-model="selectedDirections"
                    type="checkbox"
                    class="direction-checkbox"
                    :value="dir.id"
                    :disabled="isDirectionLocked(dir.id)"
                  >
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <template #footer>
          <div class="submit-section">
            <div class="submit-section__hint">
              <span v-if="selectedDirections.length">Выбрано: {{ selectedDirections.length }}</span>
              <span v-else>Отметьте направления для отправки на проверку</span>
            </div>
            <UiButton
              variant="primary"
              icon-left="fas fa-paper-plane"
              :disabled="!selectedDirections.length"
              @click="requestAccreditations"
            >
              Отправить на проверку
            </UiButton>
          </div>
        </template>
      </UiCard>
    </div>

    <div v-if="toast.show" class="toast-notification" :class="`toast-notification--${toast.type}`">
      <i :class="toast.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'" aria-hidden="true"></i>
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/services/api'
import { downloadFromHref } from '../utils/download'
import { useUploadQueueStore } from '../stores/uploadQueue'
import { useCompaniesStore } from '../stores/companies'
import { useCategoriesStore } from '../stores/categories'
import {
  UiBadge,
  UiButton,
  UiCard,
  UiEmptyState,
  UiIconButton,
  UiSelect
} from '../components/ui'

export default {
  name: 'AccreditationsSubcontractor',
  components: {
    UiBadge,
    UiButton,
    UiCard,
    UiEmptyState,
    UiIconButton,
    UiSelect
  },
  setup() {
    const companiesStore = useCompaniesStore()
    const categoriesStore = useCategoriesStore()
    const subcontractors = ref([])
    const selectedCompanyId = ref('')
    const documents = ref([])
    const directions = ref([])
    const accreditations = ref([])
    const selectedDirections = ref([])
    const newDoc = ref({ doc_type: '', doc_value: '', file_name: '', file_url: '', parent_id: null })
    const selectedFile = ref(null)
    const openHistory = ref([])
    const uploading = ref(false)
    const uploadQueue = useUploadQueueStore()

    const toast = ref({ show: false, message: '', type: 'success' })

    const showToast = (message, type = 'success') => {
      toast.value = { show: true, message, type }
      setTimeout(() => { toast.value.show = false }, 3000)
    }

    const companyOptions = computed(() => subcontractors.value.map((company) => ({
      value: company.id,
      label: company.name
    })))

    const docTypeOptions = [
      { value: 'portfolio', label: '📁 Портфолио' },
      { value: 'diploma', label: '🎓 Диплом' },
      { value: 'license', label: '📜 Лицензия' },
      { value: 'sro', label: '🛡️ СРО' }
    ]

    const sroOptions = [
      { value: 'до 25м', label: 'До 25м' },
      { value: 'до 300м', label: 'До 300м' },
      { value: 'нет', label: 'Нет' }
    ]

    const loadCompanies = async () => {
      await companiesStore.ensureLoaded()
      subcontractors.value = companiesStore.items.filter((company) => company.type === 'subcontractor')
    }

    const loadDocuments = async () => {
      if (!selectedCompanyId.value) return
      const res = await api.accreditations.listCompanyDocuments(selectedCompanyId.value)
      documents.value = res || []
    }

    const loadDirections = async () => {
      await categoriesStore.ensureLoaded()
      directions.value = categoriesStore.items
    }

    const loadAccreditations = async () => {
      if (!selectedCompanyId.value) return
      const res = await api.accreditations.list({ company_id: selectedCompanyId.value })
      accreditations.value = res || []
    }

    const loadAll = async () => {
      selectedDirections.value = []
      await Promise.all([loadDocuments(), loadAccreditations()])
    }

    const onFileSelect = (event) => {
      const file = event.target.files && event.target.files[0]
      selectedFile.value = file || null
    }

    const onFileDrop = (event) => {
      const file = event.dataTransfer.files && event.dataTransfer.files[0]
      selectedFile.value = file || null
    }

    const uploadDocument = async () => {
      if (!selectedCompanyId.value || !newDoc.value.doc_type || !selectedFile.value) return
      uploading.value = true
      const localId = uploadQueue.addLocalUpload({
        fileName: selectedFile.value.name,
        module: 'accreditations',
        entityId: selectedCompanyId.value
      })
      try {
        const form = new FormData()
        form.append('file', selectedFile.value)
        form.append('company_id', selectedCompanyId.value)
        form.append('doc_type', newDoc.value.doc_type)
        if (newDoc.value.doc_value) form.append('doc_value', newDoc.value.doc_value)
        if (newDoc.value.parent_id) form.append('parent_id', newDoc.value.parent_id)
        const response = await api.accreditations.uploadDocument(form, {
          onUploadProgress: (event) => {
            if (!event.total) return
            const progress = (event.loaded / event.total) * 100
            uploadQueue.updateProgress(localId, progress)
          }
        })
        uploadQueue.markQueued(localId, response)
        newDoc.value = { doc_type: '', doc_value: '', file_name: '', file_url: '', parent_id: null }
        selectedFile.value = null
        showToast('Документ отправлен в очередь')
        void loadDocuments()
      } catch (error) {
        console.error(error)
        uploadQueue.markError(localId, error?.response?.data?.detail)
        showToast('Не удалось загрузить документ', 'error')
      } finally {
        uploading.value = false
      }
    }

    const removeDocument = async (doc) => {
      if (!doc?.id) return
      if (!confirm('Удалить документ?')) return
      try {
        await api.accreditations.removeDocument(doc.id)
        showToast('Документ удален')
        void loadDocuments()
      } catch (error) {
        console.error(error)
        showToast('Не удалось удалить документ', 'error')
      }
    }

    const downloadDocument = async (doc) => {
      if (!doc?.id) return
      try {
        const res = await api.accreditations.getDocumentDownloadHref(doc.id)
        if (res?.href) {
          await downloadFromHref(res.href, doc.file_name || 'document')
        }
      } catch (error) {
        console.error(error)
        showToast('Не удалось скачать документ', 'error')
      }
    }

    const requestAccreditations = async () => {
      if (!selectedCompanyId.value || !selectedDirections.value.length) return
      try {
        await api.accreditations.requestAccreditations({
          company_id: selectedCompanyId.value,
          direction_ids: selectedDirections.value
        })
        showToast('Запрос отправлен')
        selectedDirections.value = []
        await loadAccreditations()
      } catch (error) {
        console.error(error)
        showToast('Не удалось отправить запрос', 'error')
      }
    }

    const accreditationMap = computed(() => {
      const map = {}
      for (const item of accreditations.value) {
        map[item.direction_id] = item
      }
      return map
    })

    const getStatusVariant = (status) => {
      if (status === 'pending') return 'warning'
      if (status === 'approved') return 'success'
      if (status === 'rejected') return 'danger'
      return 'neutral'
    }

    const statusLabel = (status) => {
      if (!status) return 'Не отправлялось'
      if (status === 'pending') return 'Ожидает'
      if (status === 'approved') return 'Аккредитовано'
      if (status === 'rejected') return 'Отклонено'
      return status
    }

    const docTypeLabel = (type, value) => {
      if (type === 'portfolio') return 'Портфолио'
      if (type === 'diploma') return 'Диплом'
      if (type === 'license') return 'Лицензия'
      if (type === 'sro') return `СРО (${value || '-'})`
      return type
    }

    const getDocIcon = (type) => {
      const icons = { portfolio: '📁', diploma: '🎓', license: '📜', sro: '🛡️' }
      return icons[type] || '📄'
    }

    const groupedDocuments = computed(() => {
      const groups = {}
      for (const doc of documents.value) {
        if (!groups[doc.doc_type]) groups[doc.doc_type] = []
        groups[doc.doc_type].push(doc)
      }
      return Object.keys(groups).map((type) => ({
        type,
        items: groups[type].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
      }))
    })

    const startNewVersion = (group) => {
      const latest = group.items[0]
      newDoc.value = {
        doc_type: group.type,
        doc_value: latest?.doc_value || '',
        file_name: '',
        file_url: '',
        parent_id: latest?.id || null
      }
    }

    const toggleHistory = (type) => {
      if (openHistory.value.includes(type)) {
        openHistory.value = openHistory.value.filter((item) => item !== type)
      } else {
        openHistory.value = [...openHistory.value, type]
      }
    }

    const isHistoryOpen = (type) => openHistory.value.includes(type)

    const isDirectionLocked = (directionId) => {
      const item = accreditationMap.value[directionId]
      return item && (item.status === 'pending' || item.status === 'approved')
    }

    onMounted(async () => {
      await Promise.all([loadCompanies(), loadDirections()])
    })

    return {
      selectedCompanyId,
      directions,
      selectedDirections,
      newDoc,
      selectedFile,
      groupedDocuments,
      accreditationMap,
      companyOptions,
      docTypeOptions,
      sroOptions,
      uploading,
      toast,
      loadAll,
      uploadDocument,
      onFileSelect,
      onFileDrop,
      removeDocument,
      downloadDocument,
      requestAccreditations,
      statusLabel,
      getStatusVariant,
      docTypeLabel,
      getDocIcon,
      startNewVersion,
      toggleHistory,
      isHistoryOpen,
      isDirectionLocked
    }
  }
}
</script>

<style scoped>
.accreditations-sub {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
}

.accreditations-sub__toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.accreditations-sub__title {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.accreditations-sub__subtitle {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.accreditations-sub__selector {
  flex: 0 1 320px;
  min-width: 220px;
}

.accreditations-sub__empty {
  min-height: 320px;
}

.accreditations-sub__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 1.2fr);
  gap: var(--space-4);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
}

.section-header__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.section-header__title--sm {
  font-size: var(--text-base);
}

.section-header__subtitle {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.documents-list__empty {
  min-height: 220px;
}

.doc-group {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.doc-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border-subtle);
}

.doc-group__title-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.doc-group__icon {
  font-size: var(--text-lg);
}

.doc-group__title {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.doc-group__subtitle {
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.doc-group__header-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  flex-shrink: 0;
}

.doc-item,
.doc-history__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
}

.doc-history__item {
  background: var(--color-surface-2);
  border-top: 1px dashed var(--color-border);
}

.doc-item__body,
.doc-history__body {
  flex: 1;
  min-width: 0;
}

.doc-item__name,
.doc-history__name {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.doc-item__meta {
  margin-top: var(--space-1);
}

.doc-item__comment {
  display: inline-flex;
  align-items: flex-start;
  gap: var(--space-2);
  margin-top: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--text-sm);
}

.doc-item__actions {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.upload-section {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.file-upload-zone {
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface-2);
  text-align: center;
  cursor: pointer;
  transition:
    border-color var(--dur-fast) ease,
    background-color var(--dur-fast) ease;
}

.file-upload-zone:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.file-upload-zone__icon {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--text-2xl);
  color: var(--color-primary);
}

.file-upload-zone__name {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.file-upload-zone__hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.directions-table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.directions-table {
  width: 100%;
  border-collapse: collapse;
}

.directions-table th,
.directions-table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
  text-align: left;
  vertical-align: middle;
}

.directions-table thead th {
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.directions-table tbody tr:last-child td {
  border-bottom: none;
}

.directions-table tbody tr:hover {
  background: var(--color-surface-2);
}

.directions-table__row--locked {
  opacity: 0.64;
}

.direction-name {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.direction-checkbox {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.direction-checkbox:disabled {
  cursor: not-allowed;
}

.submit-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
}

.submit-section__hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.text-center {
  text-align: center;
}

.toast-notification {
  position: fixed;
  right: var(--space-4);
  bottom: var(--space-4);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  color: #fff;
  box-shadow: var(--shadow-lg);
  z-index: 1200;
}

.toast-notification--success {
  background: var(--color-success);
}

.toast-notification--error {
  background: var(--color-danger);
}

@media (max-width: 1100px) {
  .accreditations-sub__layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .accreditations-sub {
    padding: var(--space-3);
  }

  .accreditations-sub__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .accreditations-sub__selector {
    min-width: 0;
  }

  .doc-group__header,
  .doc-item,
  .doc-history__item,
  .submit-section {
    flex-direction: column;
    align-items: stretch;
  }

  .directions-table {
    min-width: 640px;
  }

  .toast-notification {
    left: var(--space-3);
    right: var(--space-3);
    bottom: var(--space-3);
  }
}
</style>
