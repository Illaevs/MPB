<template>
  <div>
    <!-- Floating bulk-action bar — single panel, no secondary modals -->
    <transition name="bulk-bar">
      <div v-if="selectedTaskIds.size > 0" class="bulk-bar">
        <div class="bulk-bar__info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано: <b>{{ selectedTaskIds.size }}</b></span>
        </div>
        <div class="bulk-bar__actions">
          <select class="form-control form-control-sm" :disabled="bulkBusy" @change="onPick($event, 'status')">
            <option value="" disabled selected>Статус…</option>
            <option value="new">Новая</option>
            <option value="in_progress">В работе</option>
            <option value="pending">Ожидает</option>
            <option value="completed">Завершена</option>
            <option value="cancelled">Отменена</option>
            <option value="deferred">Отложена</option>
          </select>

          <select class="form-control form-control-sm" :disabled="bulkBusy" @change="onPick($event, 'priority')">
            <option value="" disabled selected>Приоритет…</option>
            <option value="low">Низкий</option>
            <option value="normal">Нормальный</option>
            <option value="high">Высокий</option>
            <option value="urgent">Срочный</option>
          </select>

          <input
            type="date"
            class="form-control form-control-sm bulk-bar__date"
            title="Дедлайн"
            :disabled="bulkBusy"
            @change="onDeadline($event)"
          >

          <select class="form-control form-control-sm" :disabled="bulkBusy" @change="onPick($event, 'assignee')">
            <option value="" disabled selected>+ Исполнитель…</option>
            <option v-for="u in users" :key="'a' + u.id" :value="u.id">{{ u.full_name }}</option>
          </select>

          <select class="form-control form-control-sm" :disabled="bulkBusy" @change="onPick($event, 'watcher')">
            <option value="" disabled selected>+ Наблюдатель…</option>
            <option v-for="u in users" :key="'w' + u.id" :value="u.id">{{ u.full_name }}</option>
          </select>

          <select class="form-control form-control-sm" :disabled="bulkBusy" @change="onPick($event, 'project')">
            <option value="" disabled selected>Проект…</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
          </select>

          <button class="btn btn-sm btn-outline-danger" :disabled="bulkBusy" @click="bulkDelete">
            <i class="fas fa-trash mr-1"></i> Удалить
          </button>
          <button class="btn btn-sm btn-outline-secondary" :disabled="bulkBusy" @click="clearTaskSelection">
            Снять выбор
          </button>
        </div>
      </div>
    </transition>

    <!-- Task filters live inside TasksToolbar.vue as a popover now. -->
  </div>
</template>

<script>
export default {
  name: 'TaskModals',
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state
    const onPick = (event, kind) => {
      const value = event.target.value
      event.target.value = ''
      if (!value) return
      if (kind === 'status') s.bulkSetStatus(value)
      else if (kind === 'priority') s.bulkSetPriority(value)
      else if (kind === 'assignee') s.bulkAddAssignee(value)
      else if (kind === 'watcher') s.bulkAddWatcher(value)
      else if (kind === 'project') s.bulkSetProject(value)
    }
    const onDeadline = (event) => {
      const value = event.target.value
      event.target.value = ''
      if (value) s.bulkSetDeadline(value)
    }
    return { ...s, onPick, onDeadline }
  }
}
</script>

<style scoped>
.bulk-bar__date { min-width: 150px; }
</style>
