<template>
          <div
             v-if="activeTab === 'gantt'"
             id="panel-gantt"
             class="card h-100 overflow-hidden"
             role="tabpanel"
             aria-labelledby="tab-gantt"
          >
             <div class="project-gantt-shell h-100 overflow-hidden">
                <div class="project-gantt-toolbar">
                   <div class="project-gantt-switch">
                      <button
                         class="project-gantt-switch-btn"
                         :class="{ active: ganttViewMode === 'stages' }"
                         @click="setGanttViewMode('stages')"
                      >
                         Этапы
                      </button>
                      <button
                         class="project-gantt-switch-btn"
                         :class="{ active: ganttViewMode === 'execution' }"
                         @click="setGanttViewMode('execution')"
                      >
                         Контрактация
                      </button>
                   </div>
                </div>
                <div class="project-gantt-content h-100 overflow-auto p-3">
                   <Gantt
                      v-if="ganttViewMode === 'stages'"
                      :embedded="true"
                      :deal-id="project.id"
                   />
                   <div v-else-if="defactoLoading" class="project-gantt-loading">
                      <div class="spinner"></div>
                   </div>
                   <ExecutionGantt
                      v-else
                      :groups="executionGanttGroups"
                      search-placeholder="Поиск по товарам и подзадачам..."
                      empty-title="Нет связей по исполнению"
                      empty-hint="Назначьте товары и подзадачи в исполнении, чтобы построить график."
                      group-count-label="поз."
                      name-column-label="НАИМЕНОВАНИЕ"
                      status-column-label="СТАТУС"
                      export-filename="gant-kontraktacii.csv"
                   />
                </div>
             </div>
          </div>
</template>

<script>
import Gantt from '../../Gantt.vue'
import ExecutionGantt from '../../../components/ExecutionGantt.vue'
export default {
  name: 'GanttPanel',
  components: { Gantt,ExecutionGantt },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
