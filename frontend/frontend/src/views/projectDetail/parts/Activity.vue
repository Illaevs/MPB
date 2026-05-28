<template>
    <div
      v-if="activeTab === 'activity'"
      id="panel-activity"
      class="card h-100 d-flex flex-column overflow-hidden"
      role="tabpanel"
      aria-labelledby="tab-activity"
    >
      <div class="card-header border-bottom p-3 d-flex justify-between align-center">
        <h3 class="card-title m-0">Активность по сделке</h3>
        <button class="btn btn-sm btn-outline-primary" @click="loadDealActivity({ reset: true })">
          <i class="fas fa-sync-alt mr-1" :class="{ 'fa-spin': dealActivityLoading }"></i> Обновить
        </button>
      </div>
      <div class="project-activity-toolbar border-bottom p-3 d-flex justify-between align-center gap-3 flex-wrap">
        <div class="text-muted small">
          Единая лента изменений по сделке: этапы, задачи, договоры, документы и письма.
        </div>
        <div class="project-activity-filter">
          <label class="text-muted small mb-1 d-block">Фильтр</label>
          <select v-model="dealActivityCategory" class="form-control form-control-sm">
            <option v-for="option in dealActivityCategoryOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>
      <div class="flex-grow-1 overflow-auto p-3">
        <div v-if="dealActivityLoading" class="d-flex flex-column gap-2">
          <SkeletonLoader height="72px" v-for="i in 6" :key="`activity-skel-${i}`" />
        </div>
        <div v-else-if="!dealActivity.length" class="text-center text-muted small py-5">
          События по этой сделке пока не найдены
        </div>
        <div v-else class="project-activity-list">
          <button
            v-for="item in dealActivity"
            :key="item.id"
            type="button"
            class="project-activity-row"
            @click="openDealActivityItem(item)"
          >
            <div class="project-activity-row__icon">
              <i class="fas" :class="getDealActivityMeta(item).icon"></i>
            </div>
            <div class="project-activity-row__main">
              <div class="project-activity-row__head">
                <span class="badge badge-sm" :class="getDealActivityMeta(item).className">
                  {{ getDealActivityMeta(item).label }}
                </span>
                <span class="project-activity-row__time">{{ formatDateTime(item.happened_at) }}</span>
              </div>
              <div class="project-activity-row__title">{{ item.title }}</div>
              <div v-if="item.summary" class="project-activity-row__summary">{{ item.summary }}</div>
              <div class="project-activity-row__meta">
                <span>Инициатор: {{ item.actor_name || 'Система' }}</span>
                <span v-if="item.action_label || item.action">· {{ item.action_label || item.action }}</span>
              </div>
            </div>
            <div class="project-activity-row__arrow">
              <i class="fas fa-chevron-right"></i>
            </div>
          </button>
          <div v-if="dealActivityHasMore" class="pt-2 text-center">
            <button class="btn btn-sm btn-outline-primary" :disabled="dealActivityLoadingMore" @click="loadMoreDealActivity">
              <i v-if="dealActivityLoadingMore" class="fas fa-spinner fa-spin mr-1"></i>
              <span>Показать еще</span>
            </button>
          </div>
        </div>
      </div>
    </div>
</template>

<script>
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
export default {
  name: 'Activity',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
