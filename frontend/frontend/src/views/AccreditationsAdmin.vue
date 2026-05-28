<template>
  <div class="accreditations-admin">
    <div class="accreditations-admin__toolbar">
      <div>
        <h2 class="accreditations-admin__title">Аккредитации</h2>
        <p class="accreditations-admin__subtitle">Проверка документов и направлений подрядчиков</p>
      </div>
    </div>

    <div class="accreditations-admin__layout">
      <UiCard class="accreditations-admin__sidebar" title="Подрядчики" :subtitle="`Всего: ${filteredSubcontractors.length}`">
        <div class="accreditations-admin__search">
          <UiInput
            v-model="searchQuery"
            size="sm"
            icon-left="fas fa-search"
            placeholder="Поиск компании"
          />
        </div>

        <div class="company-list">
          <button
            v-for="company in filteredSubcontractors"
            :key="company.id"
            type="button"
            class="company-list__item"
            :class="{ 'company-list__item--active': company.id === selectedCompanyId }"
            @click="selectCompany(company.id)"
          >
            <span class="company-list__name">{{ company.name }}</span>
            <span class="company-list__meta">
              <UiBadge
                v-if="pendingCounts[company.id]"
                variant="warning"
                size="sm"
                pill
              >
                {{ pendingCounts[company.id] }}
              </UiBadge>
              <span class="company-list__status" :class="`company-list__status--${getCompanyStatusClass(company.id)}`"></span>
            </span>
          </button>

          <UiEmptyState
            v-if="!filteredSubcontractors.length"
            class="company-list__empty"
            icon="fas fa-building"
            title="Компании не найдены"
            description="Измените строку поиска или добавьте нового подрядчика"
          />
        </div>
      </UiCard>

      <UiCard class="accreditations-admin__content" padding="md">
        <UiEmptyState
          v-if="!selectedCompanyId"
          class="accreditations-admin__empty"
          icon="fas fa-building"
          title="Выберите компанию"
          description="Слева появится список подрядчиков. Выберите нужную компанию, чтобы посмотреть документы и направления."
        />

        <template v-else>
          <section class="content-section">
            <div class="content-section__header">
              <div>
                <h3 class="content-section__title">Документы</h3>
                <p class="content-section__subtitle">Текущие версии и история проверок</p>
              </div>
            </div>

            <div class="documents-grid">
              <article v-for="group in groupedDocuments" :key="group.type" class="document-group">
                <header class="document-group__header">
                  <div class="document-group__title-wrap">
                    <span class="document-group__icon">{{ getDocIcon(group.type) }}</span>
                    <div>
                      <div class="document-group__title">{{ docTypeLabel(group.type, group.items[0]?.doc_value) }}</div>
                      <div class="document-group__subtitle">
                        {{ group.items.length > 1 ? `Версий: ${group.items.length}` : 'Одна версия' }}
                      </div>
                    </div>
                  </div>
                  <UiButton
                    v-if="group.items.length > 1"
                    variant="ghost"
                    size="xs"
                    @click="toggleHistory(group.type)"
                  >
                    {{ isHistoryOpen(group.type) ? 'Скрыть историю' : `История +${group.items.length - 1}` }}
                  </UiButton>
                </header>

                <div class="document-item">
                  <div class="document-item__body">
                    <div class="document-item__name">{{ group.items[0]?.file_name || 'Файл' }}</div>
                    <div class="document-item__meta">
                      <UiBadge size="sm" :variant="getStatusVariant(group.items[0]?.status)">
                        {{ statusLabel(group.items[0]?.status) }}
                      </UiBadge>
                      <span v-if="group.items[0]?.created_at" class="document-item__date">
                        {{ formatDate(group.items[0].created_at) }}
                      </span>
                    </div>
                    <div v-if="group.items[0]?.comment" class="document-item__comment">
                      <i class="fas fa-comment-alt" aria-hidden="true"></i>
                      <span>{{ group.items[0].comment }}</span>
                    </div>
                  </div>
                  <div class="document-item__actions">
                    <UiIconButton
                      icon="fas fa-download"
                      label="Скачать документ"
                      size="sm"
                      :disabled="!group.items[0]?.yandex_path"
                      @click="downloadDocument(group.items[0])"
                    />
                    <UiButton
                      variant="success"
                      size="xs"
                      icon-left="fas fa-check"
                      title="Аккредитовать документ"
                      @click="approveDocument(group.items[0])"
                    />
                    <UiButton
                      variant="danger"
                      size="xs"
                      icon-left="fas fa-times"
                      title="Отклонить документ"
                      @click="openRejectModal('document', group.items[0])"
                    />
                  </div>
                </div>

                <div v-if="isHistoryOpen(group.type)" class="document-history">
                  <div v-for="doc in group.items.slice(1)" :key="doc.id" class="document-history__item">
                    <div class="document-history__body">
                      <div class="document-history__name">{{ doc.file_name || 'Файл' }}</div>
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
                class="documents-grid__empty"
                icon="fas fa-folder-open"
                title="Документы не загружены"
                description="Подрядчик еще не отправлял документы на аккредитацию."
              />
            </div>
          </section>

          <section class="content-section">
            <div class="content-section__header">
              <div>
                <h3 class="content-section__title">Направления</h3>
                <p class="content-section__subtitle">Решения по аккредитации по каждому направлению</p>
              </div>
            </div>

            <div class="directions-table-wrap">
              <table class="directions-table">
                <thead>
                  <tr>
                    <th>Направление</th>
                    <th>Статус</th>
                    <th class="text-right">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="dir in directions" :key="dir.id">
                    <td>
                      <div class="direction-name">{{ dir.name }}</div>
                      <div v-if="accreditationMap[dir.id]?.comment" class="direction-comment">
                        <i class="fas fa-comment-alt" aria-hidden="true"></i>
                        <span>{{ accreditationMap[dir.id].comment }}</span>
                      </div>
                    </td>
                    <td>
                      <UiBadge size="sm" :variant="getStatusVariant(accreditationMap[dir.id]?.status)">
                        {{ statusLabel(accreditationMap[dir.id]?.status) }}
                      </UiBadge>
                    </td>
                    <td class="text-right">
                      <div class="direction-actions">
                        <UiButton
                          variant="success"
                          size="xs"
                          icon-left="fas fa-check"
                          title="Аккредитовать направление"
                          @click="approveAccreditation(dir.id)"
                        />
                        <UiButton
                          variant="danger"
                          size="xs"
                          icon-left="fas fa-times"
                          title="Отклонить направление"
                          @click="openRejectModal('accreditation', dir.id)"
                        />
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>
      </UiCard>
    </div>

    <UiModal
      v-model="showRejectModal"
      title="Отклонение"
      size="sm"
      @close="closeRejectModal"
    >
      <UiTextarea
        v-model="rejectReason"
        label="Причина отклонения"
        placeholder="Укажите причину отклонения"
        :rows="4"
      />

      <template #footer>
        <UiButton variant="secondary" @click="closeRejectModal">Отмена</UiButton>
        <UiButton variant="danger" :disabled="!rejectReason.trim()" @click="confirmReject">
          Отклонить
        </UiButton>
      </template>
    </UiModal>

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
import { useCompaniesStore } from '../stores/companies'
import { useCategoriesStore } from '../stores/categories'
import {
  UiBadge,
  UiButton,
  UiCard,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiModal,
  UiTextarea
} from '../components/ui'

export default {
  name: 'AccreditationsAdmin',
  components: {
    UiBadge,
    UiButton,
    UiCard,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiModal,
    UiTextarea
  },
  setup() {
    const companiesStore = useCompaniesStore()
    const categoriesStore = useCategoriesStore()
    const subcontractors = ref([])
    const selectedCompanyId = ref('')
    const documents = ref([])
    const directions = ref([])
    const accreditations = ref([])
    const openHistory = ref([])
    const searchQuery = ref('')
    const pendingCounts = ref({})

    const showRejectModal = ref(false)
    const rejectType = ref('')
    const rejectTarget = ref(null)
    const rejectReason = ref('')

    const toast = ref({ show: false, message: '', type: 'success' })

    const showToast = (message, type = 'success') => {
      toast.value = { show: true, message, type }
      setTimeout(() => { toast.value.show = false }, 3000)
    }

    const filteredSubcontractors = computed(() => {
      if (!searchQuery.value.trim()) return subcontractors.value
      const q = searchQuery.value.toLowerCase()
      return subcontractors.value.filter((company) => company.name?.toLowerCase().includes(q))
    })

    const loadCompanies = async () => {
      await companiesStore.ensureLoaded()
      subcontractors.value = companiesStore.items.filter((company) => company.type === 'subcontractor')
      const counts = {}
      for (const company of subcontractors.value) {
        try {
          const docsRes = await api.accreditations.listCompanyDocuments(company.id)
          const pending = (docsRes || []).filter((doc) => doc.status === 'pending').length
          if (pending > 0) counts[company.id] = pending
        } catch (error) {
          console.error(error)
        }
      }
      pendingCounts.value = counts
    }

    const loadDirections = async () => {
      await categoriesStore.ensureLoaded()
      directions.value = categoriesStore.items
    }

    const loadDocuments = async () => {
      if (!selectedCompanyId.value) return
      const res = await api.accreditations.listCompanyDocuments(selectedCompanyId.value)
      documents.value = res || []
    }

    const loadAccreditations = async () => {
      if (!selectedCompanyId.value) return
      const res = await api.accreditations.list({ company_id: selectedCompanyId.value })
      accreditations.value = res || []
    }

    const selectCompany = async (companyId) => {
      selectedCompanyId.value = companyId
      await Promise.all([loadDocuments(), loadAccreditations()])
    }

    const approveDocument = async (doc) => {
      await api.accreditations.updateDocument(doc.id, {
        status: 'approved',
        comment: null
      })
      showToast('Документ аккредитован')
      await loadDocuments()
      await loadCompanies()
    }

    const openRejectModal = (type, target) => {
      rejectType.value = type
      rejectTarget.value = target
      rejectReason.value = ''
      showRejectModal.value = true
    }

    const closeRejectModal = () => {
      showRejectModal.value = false
      rejectTarget.value = null
      rejectReason.value = ''
    }

    const confirmReject = async () => {
      if (!rejectReason.value.trim()) return

      if (rejectType.value === 'document') {
        await api.accreditations.updateDocument(rejectTarget.value.id, {
          status: 'rejected',
          comment: rejectReason.value
        })
        showToast('Документ отклонен', 'error')
        await loadDocuments()
      } else {
        const acc = accreditationMap.value[rejectTarget.value]
        if (!acc) {
          await api.accreditations.create({
            company_id: selectedCompanyId.value,
            direction_id: rejectTarget.value,
            status: 'rejected',
            comment: rejectReason.value
          })
        } else {
          await api.accreditations.update(acc.id, {
            status: 'rejected',
            comment: rejectReason.value
          })
        }
        showToast('Направление отклонено', 'error')
        await loadAccreditations()
      }

      closeRejectModal()
      await loadCompanies()
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

    const approveAccreditation = async (directionId) => {
      const acc = accreditationMap.value[directionId]
      if (!acc) {
        await api.accreditations.create({
          company_id: selectedCompanyId.value,
          direction_id: directionId,
          status: 'approved'
        })
      } else {
        await api.accreditations.update(acc.id, {
          status: 'approved',
          comment: null
        })
      }
      showToast('Направление аккредитовано')
      await loadAccreditations()
    }

    const accreditationMap = computed(() => {
      const map = {}
      for (const item of accreditations.value) {
        map[item.direction_id] = item
      }
      return map
    })

    const getCompanyStatusClass = (companyId) => {
      if (pendingCounts.value[companyId]) return 'pending'
      return 'neutral'
    }

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

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleDateString('ru-RU')
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

    const toggleHistory = (type) => {
      if (openHistory.value.includes(type)) {
        openHistory.value = openHistory.value.filter((item) => item !== type)
      } else {
        openHistory.value = [...openHistory.value, type]
      }
    }

    const isHistoryOpen = (type) => openHistory.value.includes(type)

    onMounted(async () => {
      await Promise.all([loadCompanies(), loadDirections()])
    })

    return {
      subcontractors,
      filteredSubcontractors,
      selectedCompanyId,
      directions,
      searchQuery,
      pendingCounts,
      groupedDocuments,
      accreditationMap,
      toast,
      showRejectModal,
      rejectReason,
      selectCompany,
      approveDocument,
      openRejectModal,
      closeRejectModal,
      confirmReject,
      downloadDocument,
      approveAccreditation,
      getCompanyStatusClass,
      getStatusVariant,
      statusLabel,
      docTypeLabel,
      getDocIcon,
      formatDate,
      toggleHistory,
      isHistoryOpen
    }
  }
}
</script>

<style scoped>
.accreditations-admin {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
}

.accreditations-admin__toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.accreditations-admin__title {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.accreditations-admin__subtitle {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.accreditations-admin__layout {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
  gap: var(--space-4);
  min-height: 0;
}

.accreditations-admin__sidebar,
.accreditations-admin__content {
  min-height: 0;
}

.accreditations-admin__search {
  margin-bottom: var(--space-3);
}

.company-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 0;
}

.company-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
  transition:
    border-color var(--dur-fast) ease,
    background-color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease;
}

.company-list__item:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface-2);
}

.company-list__item--active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: var(--shadow-focus);
}

.company-list__name {
  min-width: 0;
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
}

.company-list__meta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.company-list__status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border-strong);
}

.company-list__status--pending {
  background: var(--color-warning);
}

.company-list__empty,
.accreditations-admin__empty,
.documents-grid__empty {
  min-height: 220px;
}

.content-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.content-section + .content-section {
  margin-top: var(--space-5);
}

.content-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.content-section__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.content-section__subtitle {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.documents-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.document-group {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
}

.document-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border-subtle);
}

.document-group__title-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.document-group__icon {
  font-size: var(--text-lg);
}

.document-group__title {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.document-group__subtitle {
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.document-item,
.document-history__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
}

.document-history__item {
  border-top: 1px dashed var(--color-border);
  background: var(--color-surface-2);
}

.document-item__body,
.document-history__body {
  flex: 1;
  min-width: 0;
}

.document-item__name,
.document-history__name {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.document-item__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-1);
}

.document-item__date {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.document-item__comment,
.direction-comment {
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

.document-item__actions,
.direction-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  flex-shrink: 0;
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
  vertical-align: top;
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

.direction-name {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.text-right {
  text-align: right;
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
  .accreditations-admin__layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .accreditations-admin {
    padding: var(--space-3);
  }

  .document-group__header,
  .document-item,
  .document-history__item {
    flex-direction: column;
    align-items: stretch;
  }

  .document-item__actions,
  .direction-actions {
    justify-content: flex-start;
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
