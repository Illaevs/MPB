<template>
  <div class="gantt-view" :class="{ 'gantt-view--embedded': embedded }">
    <div v-if="!embedded" class="gantt-page-header">
      <div class="gantt-page-header__title">
        <h2>План-график</h2>
        <span v-if="visibleEntryCount" class="badge badge-counter">{{ visibleEntryCount }} {{ counterLabel }}</span>
      </div>

      <div class="gantt-page-header__actions">
        <select
          v-if="!isDealLocked"
          v-model="selectedDealId"
          @change="loadStages"
          class="form-control"
          style="width: 250px;"
        >
          <option value="">{{ selectPlaceholder }}</option>
          <option v-for="deal in deals" :key="deal.id" :value="deal.id">
            {{ deal.title }}
          </option>
        </select>

        <button class="btn btn-primary" @click="showCreateModal = true" :disabled="!selectedDealId">
          <i class="fas fa-plus mr-1"></i>
          Новый этап
        </button>
      </div>
    </div>

    <div v-if="selectedDealId && !embedded" class="gantt-mode-toolbar">
      <div class="project-gantt-switch">
        <button
          class="project-gantt-switch-btn"
          :class="{ active: ganttMode === 'stages' }"
          @click="setGanttMode('stages')"
        >
          Этапы
        </button>
        <button
          v-if="canShowExecutionMode"
          class="project-gantt-switch-btn"
          :class="{ active: ganttMode === 'execution' }"
          @click="setGanttMode('execution')"
        >
          Контрактация
        </button>
      </div>
    </div>

    <div v-if="selectedDealId" class="gantt-surface">
      <div v-if="currentLoading" class="gantt-loading">
        <div class="spinner"></div>
      </div>

      <ExecutionGantt
        v-else-if="ganttMode === 'stages'"
        :groups="stageGroups"
        search-placeholder="Поиск по этапам..."
        empty-title="Нет этапов"
        empty-hint="Создайте первый этап, чтобы увидеть график."
        group-count-label="этапов"
        name-column-label="ЭТАП"
        status-column-label="СТАТУС"
        export-filename="plan-grafik-etapy.csv"
      />

      <ExecutionGantt
        v-else
        :groups="executionGroups"
        search-placeholder="Поиск по товарам и подзадачам..."
        empty-title="Нет связей по исполнению"
        empty-hint="Назначьте товары и подзадачи в исполнении, чтобы построить график."
        group-count-label="поз\."
        name-column-label="НАИМЕНОВАНИЕ"
        status-column-label="СТАТУС"
        export-filename="plan-grafik-kontraktaciya.csv"
      />
    </div>

    <div v-else-if="!embedded" class="gantt-empty-state card">
      <div class="empty-state">
        <i class="fas fa-project-diagram"></i>
        <p>Выберите объект</p>
        <small class="text-muted">Для просмотра плана-графика выберите сделку или субподрядчика.</small>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" v-modal-close="closeModal">
      <div class="modal-content" style="max-width: 700px;" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditing ? 'Редактировать этап' : 'Новый этап' }}</h3>
          <button class="btn btn-sm btn-secondary" @click="closeModal">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <form class="modal-body" @submit.prevent="saveStage">
          <div class="form-group mb-3">
            <label>Название этапа *</label>
            <input v-model="stageForm.name" type="text" class="form-control" required />
          </div>

          <div class="form-group mb-3">
            <label>Описание</label>
            <textarea v-model="stageForm.description" class="form-control" rows="3"></textarea>
          </div>

          <div class="d-flex gap-3 mb-3">
            <div class="form-group w-50">
              <label>Дата начала *</label>
              <input v-model="stageForm.date_start" type="date" class="form-control" required />
            </div>
            <div class="form-group w-50">
              <label>Длительность (дни) *</label>
              <input v-model.number="stageForm.duration" type="number" class="form-control" min="1" required />
            </div>
          </div>

          <div class="d-flex gap-3 mb-3">
            <div class="form-group w-50">
              <label>Тип этапа</label>
              <select v-model="stageForm.stage_type" class="form-control" :disabled="isEditing">
                <option value="stage">Этап</option>
                <option value="payment">Оплата</option>
                <option value="other">Другое</option>
              </select>
              <small v-if="isEditing" class="text-muted">Тип этапа нельзя менять после создания</small>
            </div>

            <div class="form-group w-50">
              <label>Тип срока</label>
              <select v-model="stageForm.term_type" class="form-control">
                <option value="work_days">Рабочие дни</option>
                <option value="calendar_days">Календарные дни</option>
              </select>
            </div>
          </div>

          <div class="d-flex gap-3 mb-3">
            <div class="form-group w-50">
              <label>Статус</label>
              <select v-model="stageForm.status" class="form-control">
                <option value="planned">Запланирован</option>
                <option value="in_progress">В работе</option>
                <option value="completed">Завершен</option>
                <option value="delayed">Задержан</option>
              </select>
            </div>

            <div class="form-group w-50">
              <label>Подрядчик</label>
              <select v-model="stageForm.subcontractor_id" class="form-control">
                <option value="">Не выбран</option>
                <option v-for="c in subcontractors" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>

          <div class="d-flex gap-3 mb-3">
            <div :class="isEditing ? 'form-group w-50' : 'form-group w-100'">
              <label>Плановый бюджет</label>
              <input v-model.number="stageForm.planned_cost" type="number" class="form-control" step="0.01" />
            </div>

            <div v-if="isEditing" class="form-group w-50">
              <label>Фактический бюджет</label>
              <input v-model.number="stageForm.actual_cost" type="number" class="form-control" step="0.01" />
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
              {{ isEditing ? 'Сохранить' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import ExecutionGantt from '../components/ExecutionGantt.vue'
import { useCompaniesStore } from '../stores/companies'

const STAGE_TYPE_META = [
  { key: 'stage', name: 'Основные этапы' },
  { key: 'payment', name: 'Платежные этапы' },
  { key: 'other', name: 'Прочие этапы' }
]

export default {
  name: 'Gantt',
  components: { ExecutionGantt },
  props: {
    dealId: {
      type: [String, Number],
      default: ''
    },
    subcontractorId: {
      type: [String, Number],
      default: ''
    },
    embedded: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const route = useRoute()
    const companiesStore = useCompaniesStore()
    const deals = ref([])
    const entityType = ref(props.subcontractorId ? 'subcontractor' : 'deal')
    const stages = ref([])
    const subcontractors = ref([])
    const loading = ref(false)
    const executionLoading = ref(false)
    const saving = ref(false)
    const showCreateModal = ref(false)
    const isEditing = ref(false)
    const ganttMode = ref('stages')
    const selectedDealId = ref(String(props.subcontractorId || props.dealId || ''))
    const executionData = ref({ stages: [] })

    const stageForm = ref({
      name: '',
      description: '',
      date_start: '',
      duration: 1,
      stage_type: 'stage',
      term_type: 'work_days',
      status: 'planned',
      subcontractor_id: '',
      planned_cost: 0,
      actual_cost: 0,
      deal_id: '',
      subcontractor_card_id: '',
      parent_id: null
    })

    const selectPlaceholder = computed(() => (
      entityType.value === 'subcontractor' ? 'Выберите субподрядчика' : 'Выберите сделку'
    ))

    const isDealLocked = computed(() => props.embedded && !!selectedDealId.value)
    const canShowExecutionMode = computed(() => entityType.value === 'deal' && !!selectedDealId.value)
    const currentLoading = computed(() => ganttMode.value === 'execution' ? executionLoading.value : loading.value)

    const visibleEntryCount = computed(() => {
      if (ganttMode.value === 'execution') {
        return executionGroups.value.reduce((sum, group) => sum + (group.items?.length || 0), 0)
      }
      return stages.value.length
    })

    const counterLabel = computed(() => {
      if (ganttMode.value === 'execution') return 'товаров'
      const count = stages.value.length
      if (count % 10 === 1 && count % 100 !== 11) return 'этап'
      if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'этапа'
      return 'этапов'
    })

    const statusToProgress = (status, explicitProgress) => {
      if (Number.isFinite(Number(explicitProgress))) {
        return Math.max(0, Math.min(100, Number(explicitProgress)))
      }
      if (status === 'completed') return 100
      if (status === 'in_progress') return 45
      if (status === 'delayed' || status === 'overdue') return 25
      return 0
    }

    const normalizeExecutionStatus = (value) => {
      if (value === 'overdue' || value === 'delayed') return 'delayed'
      if (value === 'completed') return 'completed'
      if (value === 'in_progress') return 'in_progress'
      if (value === 'not_started') return 'not_started'
      return 'planned'
    }

    const aggregateExecutionStatus = (items = []) => {
      const statuses = items.map((item) => normalizeExecutionStatus(item.status)).filter(Boolean)
      if (!statuses.length) return 'planned'
      if (statuses.every((status) => status === 'completed')) return 'completed'
      if (statuses.some((status) => status === 'delayed')) return 'delayed'
      if (statuses.some((status) => status === 'in_progress')) return 'in_progress'
      if (statuses.some((status) => status === 'not_started')) return 'not_started'
      return 'planned'
    }

    const aggregateExecutionProgress = (items = []) => {
      if (!items.length) return 0
      return Math.round(items.reduce((sum, item) => sum + Number(item.progress || 0), 0) / items.length)
    }

    const todayIso = () => new Date().toISOString().slice(0, 10)

    const shiftIsoDate = (value, days = 0) => {
      if (!value) return ''
      const date = new Date(`${String(value).slice(0, 10)}T00:00:00`)
      if (Number.isNaN(date.getTime())) return ''
      date.setDate(date.getDate() + days)
      return date.toISOString().slice(0, 10)
    }

    const maxIsoDate = (values = []) => {
      const filtered = values.filter(Boolean).map((value) => String(value).slice(0, 10))
      if (!filtered.length) return ''
      return filtered.sort().at(-1) || ''
    }

    const minIsoDate = (values = []) => {
      const filtered = values.filter(Boolean).map((value) => String(value).slice(0, 10))
      if (!filtered.length) return ''
      return filtered.sort()[0] || ''
    }

    const dateProgressPercent = (startDateValue, dueDateValue, status) => {
      if (status === 'completed') return 100
      const start = startDateValue ? new Date(`${String(startDateValue).slice(0, 10)}T00:00:00`) : null
      const due = dueDateValue ? new Date(`${String(dueDateValue).slice(0, 10)}T00:00:00`) : null
      if (!start || !due || Number.isNaN(start.getTime()) || Number.isNaN(due.getTime())) {
        return statusToProgress(status)
      }
      const totalDays = Math.round((due.getTime() - start.getTime()) / 86400000)
      if (totalDays <= 0) {
        return new Date() >= due ? 100 : 0
      }
      const today = new Date()
      const elapsedDays = Math.round((today.getTime() - start.getTime()) / 86400000)
      const ratio = (elapsedDays / totalDays) * 100
      return Math.max(0, Math.min(100, Math.round(ratio)))
    }

    const deriveStageEndDate = (stage) => {
      if (stage.date_end) return stage.date_end
      if (!stage.date_start) return ''
      const date = new Date(`${String(stage.date_start).slice(0, 10)}T00:00:00`)
      if (Number.isNaN(date.getTime())) return ''
      date.setDate(date.getDate() + Math.max(Number(stage.duration || 1) - 1, 0))
      return date.toISOString().slice(0, 10)
    }

    const stageGroups = computed(() => {
      return STAGE_TYPE_META.map((groupMeta) => {
        const items = stages.value
          .filter((stage) => String(stage.stage_type || 'stage') === groupMeta.key)
          .map((stage) => ({
            id: `stage-${stage.id}`,
            name: stage.name,
            status: normalizeExecutionStatus(stage.status),
            progress: statusToProgress(stage.status, stage.progress),
            startDate: stage.date_start || deriveStageEndDate(stage) || todayIso(),
            endDate: deriveStageEndDate(stage) || stage.date_start || todayIso(),
            children: []
          }))

        if (!items.length) return null

        return {
          id: `group-${groupMeta.key}`,
          name: groupMeta.name,
          status: aggregateExecutionStatus(items),
          progress: aggregateExecutionProgress(items),
          startDate: items.map((item) => item.startDate).filter(Boolean).sort()[0] || '',
          endDate: maxIsoDate(items.map((item) => item.endDate)),
          items
        }
      }).filter(Boolean)
    })

    const buildExecutionSubtaskRows = (product, stageStart) => {
      const rows = []
      const multipleAssignments = (product.assignments || []).length > 1
      ;(product.assignments || []).forEach((assignment) => {
        ;(assignment.subtasks || []).forEach((subtask, index) => {
          const baseTitle = subtask.title || `Подзадача ${index + 1}`
          rows.push({
            id: subtask.id || `${assignment.id}-${index}`,
            name: multipleAssignments ? `${baseTitle} · ${assignment.subcontractor_name || 'Исполнитель'}` : baseTitle,
            status: normalizeExecutionStatus(subtask.status),
            progress: statusToProgress(subtask.status),
            startDate: shiftIsoDate(subtask.due_date || assignment.due_date || stageStart, -7),
            endDate: subtask.due_date || assignment.due_date || stageStart,
            children: []
          })
        })
      })
      return rows.sort((a, b) => String(a.endDate || '').localeCompare(String(b.endDate || '')))
    }

    const executionGroups = computed(() => {
      return (executionData.value.stages || []).map((stage) => {
        const stageStart = stage.date_start || stage.date_end || todayIso()
        const productRows = (stage.products || []).map((product) => {
          const assignments = product.assignments || []
          const subtasks = buildExecutionSubtaskRows(product, stageStart)
          const workingStartDate = minIsoDate(assignments.map((assignment) => assignment.start_date)) || stageStart
          const workingDueDate = maxIsoDate(assignments.map((assignment) => assignment.due_date))
          const contractDueDate = maxIsoDate(assignments.map((assignment) => assignment.contract_due_date))
          return {
            id: `product-${product.deal_product_id || product.product_id || product.name}`,
            name: product.name,
            status: aggregateExecutionStatus(assignments),
            progress: dateProgressPercent(workingStartDate, workingDueDate || contractDueDate || stage.date_end || stageStart, aggregateExecutionStatus(assignments)),
            startDate: workingStartDate,
            endDate: workingDueDate || contractDueDate || stage.date_end || stageStart,
            contractDueDate: contractDueDate || '',
            children: subtasks
          }
        })
        return {
          id: `execution-stage-${stage.id}`,
          name: stage.name,
          status: aggregateExecutionStatus(productRows),
          progress: aggregateExecutionProgress(productRows),
          startDate: stage.date_start || stageStart,
          endDate: stage.date_end || maxIsoDate(productRows.map((row) => row.endDate)) || stageStart,
          items: productRows
        }
      })
    })

    const loadDeals = async () => {
      try {
        const data = entityType.value === 'subcontractor'
          ? await api.gantt.listSubcontractors()
          : await api.gantt.listDeals()
        deals.value = data
      } catch (error) {
        console.error('Error loading deals:', error)
      }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        subcontractors.value = companiesStore.items.filter((company) => company.type === 'subcontractor')
      } catch (error) {
        console.error('Error loading companies:', error)
      }
    }

    const loadExecutionData = async () => {
      if (!canShowExecutionMode.value) {
        executionData.value = { stages: [] }
        return
      }
      executionLoading.value = true
      try {
        const data = await api.gantt.dealDefacto(selectedDealId.value)
        executionData.value = data || { stages: [] }
      } catch (error) {
        console.error('Error loading execution gantt:', error)
        executionData.value = { stages: [] }
      } finally {
        executionLoading.value = false
      }
    }

    const loadStages = async () => {
      if (!selectedDealId.value) {
        stages.value = []
        executionData.value = { stages: [] }
        return
      }
      loading.value = true
      try {
        const data = entityType.value === 'subcontractor'
          ? await api.gantt.listSubcontractorStages(selectedDealId.value)
          : await api.gantt.listDealStages(selectedDealId.value)
        stages.value = Array.isArray(data) ? data : []
        if (ganttMode.value === 'execution') {
          await loadExecutionData()
        }
      } catch (error) {
        console.error('Error loading stages:', error)
        stages.value = []
      } finally {
        loading.value = false
      }
    }

    const setGanttMode = async (mode) => {
      ganttMode.value = mode
      if (mode === 'execution' && canShowExecutionMode.value && !executionData.value.stages.length) {
        await loadExecutionData()
      }
    }

    const saveStage = async () => {
      if (saving.value) return
      if (!stageForm.value.name?.trim() || !stageForm.value.date_start) {
        alert('Название и дата начала обязательны')
        return
      }

      saving.value = true
      if (entityType.value === 'subcontractor') {
        stageForm.value.subcontractor_card_id = selectedDealId.value
        stageForm.value.deal_id = null
      } else {
        stageForm.value.deal_id = selectedDealId.value
        stageForm.value.subcontractor_card_id = null
      }

      try {
        const isSub = entityType.value === 'subcontractor'
        if (isEditing.value) {
          if (isSub) await api.gantt.updateSubcontractorStage(stageForm.value.id, stageForm.value)
          else await api.gantt.updateDealStage(stageForm.value.id, stageForm.value)
        } else {
          if (isSub) await api.gantt.createSubcontractorStage(stageForm.value)
          else await api.gantt.createDealStage(stageForm.value)
        }
        await loadStages()
        closeModal()
      } catch (error) {
        console.error('Error saving stage:', error)
        alert('Ошибка сохранения этапа')
      } finally {
        saving.value = false
      }
    }

    const closeModal = () => {
      showCreateModal.value = false
      isEditing.value = false
      stageForm.value = {
        name: '',
        description: '',
        date_start: '',
        duration: 1,
        stage_type: 'stage',
        term_type: 'work_days',
        status: 'planned',
        subcontractor_id: '',
        planned_cost: 0,
        actual_cost: 0,
        deal_id: '',
        subcontractor_card_id: '',
        parent_id: null
      }
    }

    const editStage = (stage) => {
      stageForm.value = { ...stage }
      isEditing.value = true
      showCreateModal.value = true
    }

    const deleteStage = async (stage) => {
      if (!confirm(`Удалить этап "${stage.name}"?`)) return
      try {
        if (entityType.value === 'subcontractor') {
          await api.gantt.removeSubcontractorStage(stage.id)
        } else {
          await api.gantt.removeDealStage(stage.id)
        }
        await loadStages()
      } catch (error) {
        console.error('Error deleting stage:', error)
        alert('Ошибка удаления этапа')
      }
    }

    watch(
      () => [props.dealId, props.subcontractorId],
      async ([dealIdValue, subcontractorIdValue]) => {
        entityType.value = subcontractorIdValue ? 'subcontractor' : 'deal'
        const nextId = subcontractorIdValue || dealIdValue || ''
        if (String(nextId || '') === String(selectedDealId.value || '')) return
        selectedDealId.value = String(nextId || '')
        if (entityType.value !== 'deal' && ganttMode.value === 'execution') {
          ganttMode.value = 'stages'
        }
        await loadStages()
      }
    )

    watch(ganttMode, async (mode) => {
      if (mode === 'execution' && canShowExecutionMode.value && !executionData.value.stages.length) {
        await loadExecutionData()
      }
    })

    onMounted(async () => {
      const routeSubcontractorId = route.query.subcontractor
      const routeDealId = route.query.deal
      const routeEditId = route.query.edit
      const routeCreateFlag = route.query.create

      const initialSubcontractor = props.subcontractorId || routeSubcontractorId
      const initialDeal = props.dealId || routeDealId
      const initialEntityId = initialSubcontractor || initialDeal

      if (initialSubcontractor) entityType.value = 'subcontractor'

      if (!props.embedded || !initialEntityId) {
        await loadDeals()
      }

      await loadCompanies()

      if (initialEntityId) {
        selectedDealId.value = String(initialEntityId)
        await loadStages()

        if (routeEditId && stages.value.length > 0) {
          const stageToEdit = stages.value.find((stage) => String(stage.id) === String(routeEditId))
          if (stageToEdit) editStage(stageToEdit)
        }

        if (routeCreateFlag && !props.embedded) {
          isEditing.value = false
          showCreateModal.value = true
        }
      }
    })

    return {
      embedded: props.embedded,
      deals,
      subcontractors,
      stages,
      loading,
      executionLoading,
      saving,
      showCreateModal,
      isEditing,
      selectedDealId,
      isDealLocked,
      selectPlaceholder,
      stageForm,
      ganttMode,
      canShowExecutionMode,
      currentLoading,
      visibleEntryCount,
      counterLabel,
      stageGroups,
      executionGroups,
      loadStages,
      setGanttMode,
      saveStage,
      closeModal
    }
  }
}
</script>

<style scoped>
.gantt-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

.gantt-view--embedded {
  gap: 0;
  min-height: 100%;
}

.gantt-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.gantt-page-header__title,
.gantt-page-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.gantt-page-header__title h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.badge-counter {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.gantt-mode-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.project-gantt-switch {
  display: inline-flex;
  align-items: center;
  padding: 4px;
  border-radius: 14px;
  background: rgba(var(--md-sys-color-outline-rgb), 0.08);
  gap: 4px;
}

.project-gantt-switch-btn {
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 10px;
}

.project-gantt-switch-btn.active {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
}

.gantt-surface {
  flex: 1 1 auto;
  min-height: 0;
}

.gantt-loading {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gantt-empty-state {
  min-height: 320px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 1rem;
  text-align: center;
}

.empty-state i {
  font-size: 3rem;
  color: var(--md-sys-color-outline-variant);
  margin-bottom: 1rem;
}

.empty-state p {
  font-size: 1rem;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 0.5rem;
}
</style>

