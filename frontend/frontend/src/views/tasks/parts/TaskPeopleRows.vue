<template>
  <div class="task-people">
    <!-- ПОСТАНОВЩИК ======================================== -->
    <div class="task-people__row">
      <div class="task-people__label">
        <i class="far fa-flag"></i>
        <span>Постановщик</span>
      </div>
      <div class="task-people__avatars">
        <UserAvatarPill
          v-if="reporter"
          :user="reporter"
          @remove="setReporter(null)"
        />
        <UserPickerButton
          :label="reporter ? 'Сменить' : 'Назначить'"
          :users="users"
          :selected-ids="reporter ? [reporter.id] : []"
          mode="single"
          @select="onReporterSelect"
        />
      </div>
    </div>

    <!-- ИСПОЛНИТЕЛИ ======================================== -->
    <div class="task-people__row">
      <div class="task-people__label">
        <i class="fas fa-user-gear"></i>
        <span>Исполнители</span>
      </div>
      <div class="task-people__avatars">
        <UserAvatarPill
          v-for="user in assignees"
          :key="'asg-' + user.id"
          :user="user"
          @remove="removeAssignee(user.id)"
        />
        <UserPickerButton
          :label="assignees.length ? '+ Добавить' : 'Назначить'"
          :users="users"
          :selected-ids="assignees.map((u) => u.id)"
          mode="multi"
          @select="toggleAssignee"
        />
      </div>
    </div>

    <!-- НАБЛЮДАТЕЛИ ======================================== -->
    <div class="task-people__row">
      <div class="task-people__label">
        <i class="far fa-eye"></i>
        <span>Наблюдатели</span>
      </div>
      <div class="task-people__avatars">
        <UserAvatarPill
          v-for="user in watchers"
          :key="'wch-' + user.id"
          :user="user"
          @remove="removeWatcher(user.id)"
        />
        <UserPickerButton
          :label="watchers.length ? '+ Добавить' : 'Добавить'"
          :users="users"
          :selected-ids="watchers.map((u) => u.id)"
          mode="multi"
          @select="toggleWatcher"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import UserAvatarPill from '../../../components/ui/UserAvatarPill.vue'
import UserPickerButton from '../../../components/ui/UserPickerButton.vue'

export default {
  name: 'TaskPeopleRows',
  components: { UserAvatarPill, UserPickerButton },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state
    const tf = s.taskForm
    const usersRef = s.users

    function trigger() {
      if (typeof s.triggerAutoDraftIfNeeded === 'function') s.triggerAutoDraftIfNeeded()
      // Save people changes immediately — they happen as discrete clicks,
      // and stacking debounced saves caused rapid additions to roll back to
      // the previous person on response merge. flushAutoSave + the request
      // counter inside the composable serialize this cleanly.
      if (typeof s.flushAutoSave === 'function') s.flushAutoSave()
    }
    function findUser(id) {
      if (!id) return null
      return (usersRef.value || []).find((u) => String(u.id) === String(id)) || null
    }

    // ---- Reporter (single, wired to created_by_user_id) ------
    const reporter = computed(() => findUser(tf.value.created_by_user_id))
    function setReporter(user) {
      tf.value.created_by_user_id = user ? user.id : null
      trigger()
    }
    function onReporterSelect(user) {
      // single-mode picker: toggle / replace
      if (!user) return setReporter(null)
      if (reporter.value && reporter.value.id === user.id) setReporter(null)
      else setReporter(user)
    }

    // ---- Assignees (multi, M2M via assignee_ids) -------------
    // The backend now persists the full list in `task_assignees`. The legacy
    // `assigned_to_user_id` is derived as `assignee_ids[0]` server-side.
    const assignees = computed(() => {
      const ids = Array.isArray(tf.value.assignee_ids) ? tf.value.assignee_ids : []
      return ids.map(findUser).filter(Boolean)
    })
    function toggleAssignee(user) {
      if (!user) return
      const ids = Array.isArray(tf.value.assignee_ids) ? tf.value.assignee_ids.map(String) : []
      const i = ids.findIndex((id) => id === String(user.id))
      if (i >= 0) ids.splice(i, 1)
      else ids.push(String(user.id))
      tf.value.assignee_ids = ids
      // Keep legacy primary in sync for any UI that still reads it.
      tf.value.assigned_to_user_id = ids.length ? ids[0] : null
      trigger()
    }
    function removeAssignee(userId) {
      const ids = (Array.isArray(tf.value.assignee_ids) ? tf.value.assignee_ids : [])
        .filter((id) => String(id) !== String(userId))
      tf.value.assignee_ids = ids
      tf.value.assigned_to_user_id = ids.length ? ids[0] : null
      trigger()
    }

    // ---- Watchers (multi, M2M via watcher_ids) ---------------
    const watchers = computed(() => {
      const ids = Array.isArray(tf.value.watcher_ids) ? tf.value.watcher_ids : []
      return ids.map(findUser).filter(Boolean)
    })
    function toggleWatcher(user) {
      if (!user) return
      const ids = Array.isArray(tf.value.watcher_ids) ? tf.value.watcher_ids.map(String) : []
      const i = ids.findIndex((id) => id === String(user.id))
      if (i >= 0) ids.splice(i, 1)
      else ids.push(String(user.id))
      tf.value.watcher_ids = ids
      trigger()
    }
    function removeWatcher(userId) {
      tf.value.watcher_ids = (Array.isArray(tf.value.watcher_ids) ? tf.value.watcher_ids : [])
        .filter((id) => String(id) !== String(userId))
      trigger()
    }

    return {
      users: usersRef,
      reporter, assignees, watchers,
      setReporter, onReporterSelect,
      toggleAssignee, removeAssignee,
      toggleWatcher, removeWatcher
    }
  }
}
</script>

<style scoped>
.task-people {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid var(--glass-border-light);
  border-radius: var(--radius-md);
}

/* Dark theme — slate-tinted glass */
:root[data-theme="dark"] .task-people {
  background: rgba(15, 23, 42, 0.4);
  border-color: var(--glass-border-dark);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .task-people {
    background: rgba(15, 23, 42, 0.4);
    border-color: var(--glass-border-dark);
  }
}

.task-people__row {
  display: grid;
  grid-template-columns: 160px 1fr;
  align-items: center;
  gap: var(--space-3);
}

.task-people__label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-muted);
}
.task-people__label i { color: var(--color-text-subtle); }

.task-people__hint {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: 6px;
  padding: 1px 6px;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-warning);
  background: var(--color-warning-soft);
  border-radius: var(--radius-pill);
  cursor: help;
}
.task-people__hint i { font-size: 10px; }

.task-people__avatars {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 32px;
}

@media (max-width: 640px) {
  .task-people__row {
    grid-template-columns: 1fr;
    gap: var(--space-1);
  }
}
</style>
