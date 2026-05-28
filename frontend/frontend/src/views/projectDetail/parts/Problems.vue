<template>
    <div
      v-if="activeTab === 'problems'"
      id="panel-problems"
      class="card h-100 d-flex flex-column overflow-hidden"
      role="tabpanel"
      aria-labelledby="tab-problems"
    >
      <div class="card-header border-bottom p-3 d-flex justify-between align-center">
        <div class="d-flex align-center gap-2">
          <h3 class="card-title m-0">Проблемы по сделке</h3>
          <span v-if="dealHealthActiveCount" class="badge badge-danger badge-sm">{{ dealHealthActiveCount }}</span>
        </div>
        <button class="btn btn-sm btn-outline-primary" @click="loadDealHealthIssues(true)">
          <i class="fas fa-sync-alt mr-1" :class="{ 'fa-spin': dealHealthLoading }"></i> Перепроверить
        </button>
      </div>
      <div class="project-activity-toolbar border-bottom p-3 d-flex justify-between align-center gap-3 flex-wrap">
        <div class="text-muted small">
          Контроль связей, сроков и полноты данных по этой сделке.
        </div>
        <div class="project-activity-filter">
          <label class="text-muted small mb-1 d-block">Статус</label>
          <select v-model="dealHealthStatusFilter" class="form-control form-control-sm" @change="loadDealHealthIssues(false)">
            <option value="active">Активные</option>
            <option value="open">Открытые</option>
            <option value="ignored">Игнор</option>
            <option value="resolved">Решенные</option>
          </select>
        </div>
      </div>
      <div class="flex-grow-1 overflow-auto p-3">
        <div v-if="dealHealthLoading" class="d-flex flex-column gap-2">
          <SkeletonLoader height="72px" v-for="i in 6" :key="`health-skel-${i}`" />
        </div>
        <div v-else-if="!dealHealthIssues.length" class="text-center text-muted small py-5">
          Активных проблем по этой сделке не найдено
        </div>
        <div v-else class="project-activity-list">
          <div
            v-for="issue in dealHealthIssues"
            :key="issue.id"
            class="project-health-row"
          >
            <button
              type="button"
              class="project-health-row__main"
              @click="openDealHealthIssue(issue)"
            >
              <div class="project-activity-row__head">
                <span class="badge badge-sm" :class="issue.severity === 'error' ? 'badge-danger' : 'badge-warning'">
                  {{ issue.severity === 'error' ? 'Ошибка' : 'Предупреждение' }}
                </span>
                <span class="badge badge-sm badge-secondary">{{ getDealHealthModuleLabel(issue.module) }}</span>
                <span class="project-activity-row__time">{{ formatDateTime(issue.last_detected_at || issue.first_detected_at) }}</span>
              </div>
              <div class="project-activity-row__title">{{ issue.title }}</div>
              <div class="project-activity-row__summary">{{ issue.description }}</div>
              <div class="project-activity-row__meta">
                <span v-if="issue.payload?.stage_name">Этап: {{ issue.payload.stage_name }}</span>
                <span v-if="issue.payload?.product_name">· Товар: {{ issue.payload.product_name }}</span>
                <span v-if="issue.payload?.contract_number">· Договор: {{ issue.payload.contract_number }}</span>
                <span v-if="issue.payload?.outgoing_number">· Письмо: {{ issue.payload.outgoing_number }}</span>
              </div>
            </button>
            <div class="project-health-row__actions">
              <button
                type="button"
                class="btn btn-sm btn-primary"
                @click.stop.prevent="openDealHealthIssue(issue)"
              >
                Исправить
              </button>
              <button
                v-if="issue.status !== 'ignored'"
                type="button"
                class="btn btn-sm btn-outline-secondary"
                @click.stop.prevent="openDealHealthIgnoreModal(issue)"
              >
                Игнор
              </button>
              <button
                v-else
                type="button"
                class="btn btn-sm btn-outline-primary"
                @click.stop.prevent="setDealHealthIssueStatus(issue, 'open')"
              >
                Вернуть
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="dealHealthIgnoreModal.visible" class="modal-overlay" @click="closeDealHealthIgnoreModal">
      <div class="modal-glass" style="max-width: 560px;" @click.stop>
        <div class="modal-glass-header">
          <h3>Игнорировать проблему</h3>
          <button type="button" class="btn btn-sm btn-secondary" @click="closeDealHealthIgnoreModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-glass-body">
          <div class="form-group">
            <label>Проблема</label>
            <div class="bg-light rounded px-3 py-2 fw-600">{{ dealHealthIgnoreModal.issue?.title }}</div>
          </div>
          <div class="form-group">
            <label for="deal-health-ignore-reason">Причина</label>
            <textarea
              id="deal-health-ignore-reason"
              v-model.trim="dealHealthIgnoreModal.reason"
              class="form-control"
              rows="4"
              placeholder="Почему проблему можно временно не учитывать"
            ></textarea>
          </div>
          <div class="form-group">
            <label for="deal-health-ignore-until">Игнорировать до</label>
            <input
              id="deal-health-ignore-until"
              v-model="dealHealthIgnoreModal.until"
              type="datetime-local"
              class="form-control"
            >
            <small class="text-muted">Если срок не указан, проблема останется в игноре до ручного возврата.</small>
          </div>
        </div>
        <div class="modal-glass-footer">
          <button type="button" class="btn btn-secondary" @click="closeDealHealthIgnoreModal">Отмена</button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="dealHealthIgnoreModal.saving"
            @click="confirmDealHealthIgnore"
          >
            <i v-if="dealHealthIgnoreModal.saving" class="fas fa-spinner fa-spin"></i>
            <span v-else>Игнорировать</span>
          </button>
        </div>
      </div>
    </div>
</template>

<script>
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
export default {
  name: 'Problems',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
