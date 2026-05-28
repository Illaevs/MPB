<template>
  <div>
    <!-- Floating bulk-action bar -->
    <transition name="bulk-bar">
      <div v-if="selectedTaskIds.size > 0" class="bulk-bar">
        <div class="bulk-bar__info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано: <b>{{ selectedTaskIds.size }}</b></span>
        </div>
        <div class="bulk-bar__actions">
          <select class="form-control form-control-sm" @change="onBulkStatusChange($event)" :disabled="bulkBusy">
            <option value="" disabled selected>Сменить статус...</option>
            <option value="new">Новая</option>
            <option value="in_progress">В работе</option>
            <option value="pending">Ожидает</option>
            <option value="completed">Завершена</option>
            <option value="cancelled">Отменена</option>
            <option value="deferred">Отложена</option>
          </select>
          <button class="btn btn-sm btn-outline-secondary" :disabled="bulkBusy" @click="openBulkAssign">
            <i class="fas fa-user-pen mr-1"></i> Назначить
          </button>
          <button class="btn btn-sm btn-outline-danger" :disabled="bulkBusy" @click="bulkDelete">
            <i class="fas fa-trash mr-1"></i> Удалить
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="clearTaskSelection">Снять выбор</button>
        </div>
      </div>
    </transition>

    <!-- Bulk assign modal -->
    <div v-if="bulkAssignOpen" class="modal-overlay" @click.self="closeBulkAssign">
      <div class="modal-content" @click.stop style="max-width: 420px;">
        <div class="modal-header">
          <h4>Назначить исполнителя на {{ selectedTaskIds.size }} задач</h4>
          <button class="btn-close" @click="closeBulkAssign"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Исполнитель</label>
            <select v-model="bulkAssignUserId" class="form-control">
              <option value="">Снять назначение</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeBulkAssign">Отмена</button>
          <button class="btn btn-primary" :disabled="bulkBusy" @click="bulkAssign">
            <i v-if="bulkBusy" class="fas fa-spinner fa-spin mr-1"></i>
            Применить
          </button>
        </div>
      </div>
    </div>

    <!-- Task filters live inside TasksToolbar.vue as a popover now. -->
  </div>
</template>

<script>
export default {
  name: 'TaskModals',
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state
    const onBulkStatusChange = (event) => {
      const value = event.target.value
      s.bulkSetStatus(value)
      event.target.value = ''
    }
    return { ...s, onBulkStatusChange }
  }
}
</script>
