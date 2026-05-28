<template>
  <section class="approval-widget">
    <header class="approval-widget__header">
      <div class="approval-widget__header-copy">
        <h5>{{ title }}</h5>
        <p>{{ subtitle }}</p>
      </div>
      <button type="button" class="approval-widget__refresh" :disabled="loading" @click="reload">
        <i class="fas" :class="loading ? 'fa-spinner fa-spin' : 'fa-rotate-right'"></i>
      </button>
    </header>

    <div v-if="!entityId" class="approval-widget__empty">
      {{ emptyText }}
    </div>

    <template v-else>
      <div v-if="visibleInstance" class="approval-widget__status">
        <span class="approval-widget__badge" :class="`is-${visibleInstance.status}`">
          {{ statusLabel(visibleInstance.status) }}
        </span>
        <div class="approval-widget__status-copy">
          <strong>{{ visibleInstance.template_name }}</strong>
          <span>{{ visibleInstance.entity_label || entityLabel || 'Текущий объект' }}</span>
        </div>
      </div>

      <div v-if="currentStep" class="approval-widget__focus-card">
        <div class="approval-widget__focus-top">
          <span class="approval-widget__focus-label">Текущий шаг</span>
          <span class="approval-widget__focus-assignee">{{ currentStep.assignee_label || 'Без исполнителя' }}</span>
        </div>
        <strong>{{ currentStep.title }}</strong>
        <p v-if="currentStep.description">{{ currentStep.description }}</p>
      </div>

      <div v-if="canStart" class="approval-widget__start">
        <label v-if="availableTemplates.length > 1" class="approval-widget__field">
          <span>Шаблон согласования</span>
          <select v-model="selectedTemplateId" class="approval-widget__select">
            <option v-for="template in availableTemplates" :key="template.id" :value="template.id">
              {{ template.name }}
            </option>
          </select>
        </label>
        <button type="button" class="approval-widget__primary" :disabled="acting || !selectedTemplateId" @click="startApproval">
          <i v-if="acting" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-paper-plane"></i>
          <span>Отправить на согласование</span>
        </button>
      </div>

      <div v-if="canAct" class="approval-widget__action-box">
        <label class="approval-widget__field">
          <span>Комментарий</span>
          <textarea
            v-model="actionComment"
            rows="3"
            class="approval-widget__textarea"
            placeholder="Добавьте комментарий для согласования или отклонения"
          ></textarea>
        </label>
        <div class="approval-widget__action-row">
          <button type="button" class="approval-widget__primary" :disabled="acting" @click="approveCurrent">
            <i v-if="acting" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-check"></i>
            <span>Согласовать</span>
          </button>
          <button type="button" class="approval-widget__danger" :disabled="acting" @click="rejectCurrent">
            <i class="fas fa-xmark"></i>
            <span>Отклонить</span>
          </button>
        </div>
      </div>

      <div v-else-if="!visibleInstance && !availableTemplates.length && !loading" class="approval-widget__empty">
        Для этого типа объектов пока нет активных шаблонов согласования.
      </div>

      <div v-if="visibleSteps.length" class="approval-widget__timeline">
        <div class="approval-widget__timeline-head">
          <span>Маршрут согласования</span>
          <small v-if="instances.length > 1">История запусков: {{ instances.length }}</small>
        </div>
        <ol class="approval-widget__steps">
          <li
            v-for="step in visibleSteps"
            :key="step.id"
            class="approval-widget__step"
            :class="{
              'is-pending': step.status === 'pending',
              'is-approved': step.status === 'approved',
              'is-rejected': step.status === 'rejected'
            }"
          >
            <span class="approval-widget__step-dot"></span>
            <div class="approval-widget__step-copy">
              <div class="approval-widget__step-top">
                <strong>{{ step.title }}</strong>
                <span>{{ statusLabel(step.status) }}</span>
              </div>
              <div class="approval-widget__step-meta">
                <span>{{ step.assignee_label || 'Без исполнителя' }}</span>
                <span v-if="step.acted_by_label">Решение: {{ step.acted_by_label }}</span>
              </div>
              <p v-if="step.description">{{ step.description }}</p>
              <p v-if="step.comment" class="approval-widget__step-comment">{{ step.comment }}</p>
            </div>
          </li>
        </ol>
      </div>
    </template>
  </section>
</template>

<script>
import { computed, defineComponent, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../services/api'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'

export default defineComponent({
  name: 'ApprovalWidget',
  props: {
    entityType: {
      type: String,
      required: true,
    },
    entityId: {
      type: [String, Number],
      default: null,
    },
    entityLabel: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: 'Согласование',
    },
    emptyText: {
      type: String,
      default: 'Сохраните объект, чтобы запустить согласование.',
    },
    allowRestartAfterApproved: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['updated', 'state-changed'],
  setup(props, { emit }) {
    const route = useRoute()
    const authStore = useAuthStore()
    const { success: toastSuccess, error: toastError } = useToast()

    const loading = ref(false)
    const acting = ref(false)
    const templates = ref([])
    const instances = ref([])
    const selectedTemplateId = ref('')
    const actionComment = ref('')

    const highlightInstanceId = computed(() => String(route.query.approvalInstance || ''))
    const availableTemplates = computed(() => templates.value.filter((item) => item.is_active))
    const activeInstance = computed(() => instances.value.find((item) => item.status === 'pending') || null)
    const latestInstance = computed(() => instances.value[0] || null)
    const highlightedInstance = computed(() => {
      if (!highlightInstanceId.value) return null
      return instances.value.find((item) => String(item.id) === highlightInstanceId.value) || null
    })
    const visibleInstance = computed(() => highlightedInstance.value || activeInstance.value || latestInstance.value)
    const visibleSteps = computed(() => visibleInstance.value?.steps || [])
    const currentStep = computed(() => visibleSteps.value.find((item) => item.status === 'pending') || null)
    const currentUserId = computed(() => String(authStore.user?.id || ''))
    const currentRoleId = computed(() => String(authStore.user?.role_id || ''))

    const canAct = computed(() => {
      if (!currentStep.value) return false
      if (currentStep.value.assignee_type === 'user') {
        return String(currentStep.value.assignee_user_id || '') === currentUserId.value
      }
      if (currentStep.value.assignee_type === 'role') {
        return String(currentStep.value.assignee_role_id || '') === currentRoleId.value
      }
      return false
    })

    const canStart = computed(() => (
      !!props.entityId &&
      !activeInstance.value &&
      availableTemplates.value.length > 0 &&
      (props.allowRestartAfterApproved || latestInstance.value?.status !== 'approved')
    ))

    const subtitle = computed(() => {
      if (!props.entityId) return 'Сначала сохраните объект, затем запустите маршрут согласования.'
      if (activeInstance.value) return 'Согласование уже идет. Здесь виден текущий шаг и действия согласующего.'
      if (latestInstance.value?.status === 'approved') {
        return props.allowRestartAfterApproved
          ? 'Последний маршрут завершен успешно. При необходимости можно запустить новый.'
          : 'Последний маршрут завершен успешно.'
      }
      if (latestInstance.value?.status === 'rejected') {
        return 'Последний маршрут отклонен. После правок можно запустить новый.'
      }
      return 'Запустите маршрут вручную и отслеживайте статус прямо внутри сущности.'
    })

    const emitState = () => {
      emit('state-changed', {
        loading: loading.value,
        templateCount: availableTemplates.value.length,
        instances: instances.value,
        activeInstance: activeInstance.value,
        latestInstance: latestInstance.value,
        visibleInstance: visibleInstance.value,
        latestStatus: latestInstance.value?.status || null,
      })
    }

    const statusLabel = (status) => {
      switch (status) {
        case 'pending':
          return 'На согласовании'
        case 'approved':
          return 'Согласовано'
        case 'rejected':
          return 'Отклонено'
        case 'waiting':
          return 'Ожидает'
        default:
          return status || 'Неизвестно'
      }
    }

    const loadTemplates = async () => {
      if (!props.entityType) return
      const data = await api.approvals.listRuntimeTemplates({
        entity_type: props.entityType,
        active: true,
      })
      templates.value = Array.isArray(data) ? data : []
      if (!selectedTemplateId.value || !availableTemplates.value.some((item) => item.id === selectedTemplateId.value)) {
        selectedTemplateId.value = availableTemplates.value[0]?.id || ''
      }
    }

    const loadInstances = async () => {
      if (!props.entityId) {
        instances.value = []
        return
      }
      const data = await api.approvals.listInstances({
        entity_type: props.entityType,
        entity_id: props.entityId,
      })
      instances.value = Array.isArray(data) ? data : []
    }

    const reload = async () => {
      loading.value = true
      try {
        await Promise.all([loadTemplates(), loadInstances()])
      } catch (error) {
        console.error('Approval widget load error:', error)
        toastError(error?.response?.data?.detail || 'Не удалось загрузить данные согласования')
      } finally {
        loading.value = false
        emitState()
      }
    }

    const startApproval = async () => {
      if (!props.entityId || !selectedTemplateId.value) return
      acting.value = true
      try {
        await api.approvals.createInstance({
          template_id: selectedTemplateId.value,
          entity_type: props.entityType,
          entity_id: String(props.entityId),
          entity_label: props.entityLabel || null,
        })
        actionComment.value = ''
        await reload()
        toastSuccess('Согласование запущено')
        emit('updated')
      } catch (error) {
        console.error('Approval start error:', error)
        toastError(error?.response?.data?.detail || 'Не удалось запустить согласование')
      } finally {
        acting.value = false
      }
    }

    const approveCurrent = async () => {
      if (!activeInstance.value) return
      acting.value = true
      try {
        await api.approvals.approveInstance(activeInstance.value.id, {
          comment: actionComment.value || null,
        })
        actionComment.value = ''
        await reload()
        toastSuccess('Шаг согласован')
        emit('updated')
      } catch (error) {
        console.error('Approval approve error:', error)
        toastError(error?.response?.data?.detail || 'Не удалось согласовать шаг')
      } finally {
        acting.value = false
      }
    }

    const rejectCurrent = async () => {
      if (!activeInstance.value) return
      if (!actionComment.value.trim()) {
        toastError('Добавьте комментарий к отклонению')
        return
      }
      acting.value = true
      try {
        await api.approvals.rejectInstance(activeInstance.value.id, {
          comment: actionComment.value,
        })
        actionComment.value = ''
        await reload()
        toastSuccess('Согласование отклонено')
        emit('updated')
      } catch (error) {
        console.error('Approval reject error:', error)
        toastError(error?.response?.data?.detail || 'Не удалось отклонить согласование')
      } finally {
        acting.value = false
      }
    }

    watch(() => props.entityId, () => {
      reload()
    }, { immediate: false })

    watch([availableTemplates, visibleInstance], () => {
      emitState()
    })

    onMounted(reload)

    return {
      loading,
      acting,
      instances,
      selectedTemplateId,
      actionComment,
      availableTemplates,
      activeInstance,
      latestInstance,
      visibleInstance,
      visibleSteps,
      currentStep,
      canAct,
      canStart,
      subtitle,
      statusLabel,
      reload,
      startApproval,
      approveCurrent,
      rejectCurrent,
    }
  },
})
</script>

<style scoped>
.approval-widget {
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.08);
}

.approval-widget__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.approval-widget__header-copy {
  min-width: 0;
}

.approval-widget__header h5 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.approval-widget__header p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.approval-widget__refresh,
.approval-widget__primary,
.approval-widget__danger,
.approval-widget__select,
.approval-widget__textarea {
  font: inherit;
}

.approval-widget__refresh {
  width: 34px;
  height: 34px;
  border: 1px solid #d9e3f0;
  border-radius: 10px;
  background: #fff;
  color: #64748b;
  cursor: pointer;
}

.approval-widget__refresh:disabled,
.approval-widget__primary:disabled,
.approval-widget__danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.approval-widget__status,
.approval-widget__focus-card,
.approval-widget__action-box,
.approval-widget__timeline {
  border: 1px solid #e8edf4;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
}

.approval-widget__status {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
}

.approval-widget__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.approval-widget__badge.is-pending {
  background: rgba(245, 158, 11, 0.16);
  color: #b45309;
}

.approval-widget__badge.is-approved {
  background: rgba(16, 185, 129, 0.16);
  color: #047857;
}

.approval-widget__badge.is-rejected {
  background: rgba(239, 68, 68, 0.15);
  color: #b91c1c;
}

.approval-widget__status-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.approval-widget__status-copy strong,
.approval-widget__focus-card strong,
.approval-widget__step-top strong {
  color: #0f172a;
}

.approval-widget__status-copy span,
.approval-widget__focus-assignee,
.approval-widget__focus-card p,
.approval-widget__step-copy p,
.approval-widget__step-meta,
.approval-widget__timeline-head small,
.approval-widget__empty {
  color: #64748b;
}

.approval-widget__focus-card,
.approval-widget__action-box,
.approval-widget__timeline {
  padding: 14px;
}

.approval-widget__focus-top,
.approval-widget__timeline-head,
.approval-widget__step-top,
.approval-widget__step-meta,
.approval-widget__action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.approval-widget__focus-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.approval-widget__focus-label,
.approval-widget__field span:first-child,
.approval-widget__timeline-head span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #94a3b8;
}

.approval-widget__start,
.approval-widget__action-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-widget__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.approval-widget__select,
.approval-widget__textarea {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border: 1px solid #dbe4ef;
  border-radius: 12px;
  background: #fff;
  color: #0f172a;
}

.approval-widget__select {
  min-height: 42px;
  padding: 0 12px;
}

.approval-widget__textarea {
  padding: 10px 12px;
  resize: vertical;
}

.approval-widget__primary,
.approval-widget__danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 14px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
}

.approval-widget__primary {
  background: #2563eb;
  color: #fff;
}

.approval-widget__danger {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.approval-widget__empty {
  padding: 12px 14px;
  border: 1px dashed #d6e0ec;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.86);
  font-size: 13px;
  line-height: 1.5;
}

.approval-widget__steps {
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-widget__step {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 12px;
  align-items: flex-start;
}

.approval-widget__step-dot {
  width: 14px;
  height: 14px;
  margin-top: 6px;
  border-radius: 999px;
  background: #cbd5e1;
  box-shadow: 0 0 0 5px rgba(203, 213, 225, 0.22);
}

.approval-widget__step.is-pending .approval-widget__step-dot {
  background: #f59e0b;
  box-shadow: 0 0 0 5px rgba(245, 158, 11, 0.16);
}

.approval-widget__step.is-approved .approval-widget__step-dot {
  background: #10b981;
  box-shadow: 0 0 0 5px rgba(16, 185, 129, 0.14);
}

.approval-widget__step.is-rejected .approval-widget__step-dot {
  background: #ef4444;
  box-shadow: 0 0 0 5px rgba(239, 68, 68, 0.14);
}

.approval-widget__step-copy {
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid #e8edf4;
  border-radius: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.approval-widget__step-top span {
  font-size: 12px;
  color: #64748b;
}

.approval-widget__step-meta {
  flex-wrap: wrap;
  justify-content: flex-start;
  font-size: 12px;
}

.approval-widget__step-comment {
  margin: 0;
  color: #334155;
  font-style: italic;
}

@media (max-width: 640px) {
  .approval-widget {
    padding: 14px;
  }

  .approval-widget__header,
  .approval-widget__timeline-head,
  .approval-widget__step-top,
  .approval-widget__action-row {
    flex-direction: column;
    align-items: stretch;
  }

  .approval-widget__status {
    flex-direction: column;
  }

  .approval-widget__step {
    grid-template-columns: 1fr;
  }

  .approval-widget__step-dot {
    display: none;
  }
}
</style>
