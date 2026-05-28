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

        <div class="acc-filters">
          <select v-model="companyStatusFilter" class="acc-filters__select">
            <option value="all">Все компании</option>
            <option value="pending">С ожидающими проверками</option>
          </select>

          <div class="acc-dirfilter" v-click-outside="() => dirFilterOpen = false">
            <button
              ref="dirFilterBtn"
              type="button"
              class="acc-dirfilter__btn"
              :class="{ 'is-active': dirFilterIds.length }"
              @click="toggleDirPop"
            >
              <i class="fas fa-filter"></i>
              <span>{{ dirFilterIds.length ? `Направления: ${dirFilterIds.length}` : 'Фильтр по направлениям' }}</span>
              <i class="fas fa-chevron-down"></i>
            </button>
            <transition name="acc-pop">
              <div v-if="dirFilterOpen" class="acc-dirfilter__pop" :style="dirPopStyle">
                <div class="acc-dirfilter__head">
                  <span>Аккредитованы по всем выбранным</span>
                  <button v-if="dirFilterIds.length" type="button" class="acc-dirfilter__clear" @click="clearDirFilter">Сбросить</button>
                </div>
                <label
                  v-for="dir in directions"
                  :key="`f-${dir.id}`"
                  class="acc-dirfilter__item"
                >
                  <input
                    type="checkbox"
                    :checked="dirFilterIds.includes(dir.id)"
                    @change="toggleDirFilter(dir.id)"
                  >
                  <span>{{ dir.name }}</span>
                </label>
              </div>
            </transition>
          </div>
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
                    <th class="acc-cb-col">
                      <input
                        type="checkbox"
                        class="acc-cb"
                        :checked="allDirsSelected"
                        :indeterminate.prop="someDirsSelected && !allDirsSelected"
                        @change="toggleAllDirs"
                      >
                    </th>
                    <th>Направление</th>
                    <th>Статус</th>
                    <th class="text-right">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="dir in directions" :key="dir.id" :class="{ 'is-selected': selectedDirIds.includes(dir.id) }">
                    <td class="acc-cb-col">
                      <input
                        type="checkbox"
                        class="acc-cb"
                        :checked="selectedDirIds.includes(dir.id)"
                        @change="toggleDirSelected(dir.id)"
                      >
                    </td>
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

    <transition name="acc-bulk">
      <div v-if="selectedDirIds.length && selectedCompanyId" class="acc-bulkbar">
        <div class="acc-bulkbar__info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано направлений: <b>{{ selectedDirIds.length }}</b></span>
        </div>
        <div class="acc-bulkbar__actions">
          <UiButton variant="success" size="sm" icon-left="fas fa-check" :loading="bulkBusy" @click="bulkApprove">
            Аккредитовать
          </UiButton>
          <UiButton variant="danger" size="sm" icon-left="fas fa-times" :disabled="bulkBusy" @click="openBulkReject">
            Отклонить
          </UiButton>
          <UiButton variant="secondary" size="sm" @click="clearDirSelection">Снять выбор</UiButton>
        </div>
      </div>
    </transition>

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
import { ref, onMounted, computed, watch } from 'vue'
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

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

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
  directives: { 'click-outside': clickOutside },
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

    // Basic + directions filters
    const companyStatusFilter = ref('all')
    const dirFilterOpen = ref(false)
    const dirFilterIds = ref([])
    const accreditedSet = ref(new Set())
    // Popup рендерится position:fixed по координатам кнопки, чтобы не
    // обрезаться overflow карточки сайдбара и не уходить под правый блок.
    const dirFilterBtn = ref(null)
    const dirPopStyle = ref({})

    const positionDirPop = () => {
      const el = dirFilterBtn.value
      if (!el) return
      const r = el.getBoundingClientRect()
      const width = Math.min(380, window.innerWidth - 24)
      const left = Math.max(12, Math.min(r.left, window.innerWidth - width - 12))
      dirPopStyle.value = {
        position: 'fixed',
        top: `${Math.round(r.bottom + 4)}px`,
        left: `${Math.round(left)}px`,
        width: `${width}px`,
      }
    }
    const closeDirPop = () => { dirFilterOpen.value = false }
    const toggleDirPop = () => {
      if (dirFilterOpen.value) { dirFilterOpen.value = false; return }
      positionDirPop()
      dirFilterOpen.value = true
    }
    watch(dirFilterOpen, (open) => {
      if (open) {
        window.addEventListener('resize', closeDirPop)
        window.addEventListener('scroll', closeDirPop, true)
      } else {
        window.removeEventListener('resize', closeDirPop)
        window.removeEventListener('scroll', closeDirPop, true)
      }
    })

    // Bulk editor (directions of the selected company)
    const selectedDirIds = ref([])
    const bulkBusy = ref(false)

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
      let list = subcontractors.value
      const q = searchQuery.value.trim().toLowerCase()
      if (q) list = list.filter((c) => c.name?.toLowerCase().includes(q))
      if (companyStatusFilter.value === 'pending') {
        list = list.filter((c) => pendingCounts.value[c.id])
      }
      if (dirFilterIds.value.length) {
        list = list.filter((c) => accreditedSet.value.has(String(c.id)))
      }
      return list
    })

    const toggleDirFilter = (id) => {
      const i = dirFilterIds.value.indexOf(id)
      if (i >= 0) dirFilterIds.value.splice(i, 1)
      else dirFilterIds.value.push(id)
    }
    const clearDirFilter = () => { dirFilterIds.value = [] }

    watch(dirFilterIds, async (ids) => {
      if (!ids.length) { accreditedSet.value = new Set(); return }
      try {
        const res = await api.accreditations.accreditedCompanyIds(ids, 'approved')
        accreditedSet.value = new Set((res || []).map(String))
      } catch (error) {
        console.error(error)
        accreditedSet.value = new Set()
      }
    }, { deep: true })

    // ---- Bulk directions selection ----
    const allDirsSelected = computed(() =>
      directions.value.length > 0 && selectedDirIds.value.length === directions.value.length
    )
    const someDirsSelected = computed(() => selectedDirIds.value.length > 0)
    const toggleDirSelected = (id) => {
      const i = selectedDirIds.value.indexOf(id)
      if (i >= 0) selectedDirIds.value.splice(i, 1)
      else selectedDirIds.value.push(id)
    }
    const toggleAllDirs = () => {
      selectedDirIds.value = allDirsSelected.value ? [] : directions.value.map((d) => d.id)
    }
    const clearDirSelection = () => { selectedDirIds.value = [] }

    const bulkApprove = async () => {
      if (!selectedCompanyId.value || !selectedDirIds.value.length) return
      bulkBusy.value = true
      try {
        await api.accreditations.bulkSetDirections(
          selectedCompanyId.value, [...selectedDirIds.value], 'approved'
        )
        showToast(`Аккредитовано направлений: ${selectedDirIds.value.length}`)
        clearDirSelection()
        await Promise.all([loadAccreditations(), loadCompanies()])
      } catch (error) {
        console.error(error)
        showToast('Не удалось аккредитовать', 'error')
      } finally {
        bulkBusy.value = false
      }
    }

    const openBulkReject = () => {
      rejectType.value = 'bulk'
      rejectTarget.value = null
      rejectReason.value = ''
      showRejectModal.value = true
    }

    const loadCompanies = async () => {
      await companiesStore.ensureLoaded()
      subcontractors.value = companiesStore.items.filter((company) => company.type === 'subcontractor')
      const counts = {}
      for (const company of subcontractors.value) {
        try {
          // Счётчик = ожидающие документы + ожидающие направления
          // (каждое направление на аккредитацию или документ идёт в счётчик).
          const [docsRes, accRes] = await Promise.all([
            api.accreditations.listCompanyDocuments(company.id),
            api.accreditations.list({ company_id: company.id, status: 'pending' }),
          ])
          const pendingDocs = (docsRes || []).filter((doc) => doc.status === 'pending').length
          const pendingDirs = (accRes || []).length
          const total = pendingDocs + pendingDirs
          if (total > 0) counts[company.id] = total
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
      selectedDirIds.value = []
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

      if (rejectType.value === 'bulk') {
        bulkBusy.value = true
        try {
          await api.accreditations.bulkSetDirections(
            selectedCompanyId.value, [...selectedDirIds.value], 'rejected', rejectReason.value
          )
          showToast(`Отклонено направлений: ${selectedDirIds.value.length}`, 'error')
          clearDirSelection()
          await Promise.all([loadAccreditations(), loadCompanies()])
        } catch (error) {
          console.error(error)
          showToast('Не удалось отклонить', 'error')
        } finally {
          bulkBusy.value = false
          closeRejectModal()
        }
        return
      }

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
      companyStatusFilter,
      dirFilterOpen,
      dirFilterIds,
      dirFilterBtn,
      dirPopStyle,
      toggleDirPop,
      toggleDirFilter,
      clearDirFilter,
      selectedDirIds,
      allDirsSelected,
      someDirsSelected,
      toggleDirSelected,
      toggleAllDirs,
      clearDirSelection,
      bulkBusy,
      bulkApprove,
      openBulkReject,
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
  min-height: calc(100vh - 84px);
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
  flex: 1;
  min-height: 0;
}

/* Карточки тянутся на всю высоту строки грида; внутренний скролл —
   таблица аккредитаций доходит до низа экрана (как в Задачах). */
.accreditations-admin__sidebar,
.accreditations-admin__content {
  min-height: 0;
  max-height: 100%;
  overflow: auto;
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

/* ---- Filters (basic + directions multi-select) ---- */
.acc-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.acc-filters__select {
  width: 100%;
  height: 32px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
}

.acc-dirfilter { position: relative; }

.acc-dirfilter__btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  height: 32px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  cursor: pointer;
}
.acc-dirfilter__btn .fa-chevron-down { margin-left: auto; font-size: 0.7em; }
.acc-dirfilter__btn.is-active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.acc-dirfilter__pop {
  /* position/top/left/width задаются инлайном (fixed по кнопке),
     чтобы не обрезаться overflow карточки и не уходить под правый блок */
  position: fixed;
  z-index: 1600;
  max-height: 340px;
  overflow-y: auto;
  padding: var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  /* Базово список направлений в 2 столбца. */
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px var(--space-1);
  align-content: start;
}

.acc-dirfilter__head {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: 0 var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
}
.acc-dirfilter__clear {
  border: none;
  background: none;
  color: var(--color-primary);
  font-size: var(--text-xs);
  cursor: pointer;
}
.acc-dirfilter__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  padding: 6px var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  cursor: pointer;
}
.acc-dirfilter__item input { flex-shrink: 0; }
.acc-dirfilter__item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.acc-dirfilter__item:hover { background: var(--color-surface-2); }

.acc-pop-enter-active, .acc-pop-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.acc-pop-enter-from, .acc-pop-leave-to { opacity: 0; transform: translateY(-6px); }

/* ---- Bulk selection ---- */
.acc-cb-col { width: 40px; text-align: center; }
.acc-cb { width: 16px; height: 16px; cursor: pointer; accent-color: var(--color-primary); }
.directions-table tbody tr.is-selected { background: var(--color-primary-soft); }

.acc-bulkbar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1500;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 10px 16px;
  border-radius: 14px;
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 12px 32px rgba(13, 71, 161, 0.35);
  flex-wrap: wrap;
  max-width: calc(100vw - 32px);
}
.acc-bulkbar__info { display: flex; align-items: center; gap: var(--space-2); white-space: nowrap; }
.acc-bulkbar__actions { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }

.acc-bulk-enter-active, .acc-bulk-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.acc-bulk-enter-from, .acc-bulk-leave-to { opacity: 0; transform: translateX(-50%) translateY(20px); }

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
