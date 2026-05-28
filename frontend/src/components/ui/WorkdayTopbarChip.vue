<template>
  <div v-if="visible" class="workday-chip-wrapper">
    <button
      v-if="isActive"
      type="button"
      class="workday-chip"
      :class="{ 'is-paused': isHidden }"
      :title="`Рабочий день идёт. Авто-стоп через ${idleTimeoutMinutes} мин бездействия.`"
      @click="openEnd"
    >
      <span class="workday-chip-dot"></span>
      <span class="workday-chip-time">{{ formattedElapsed }}</span>
      <i class="fas fa-stop workday-chip-icon"></i>
    </button>

    <Teleport to="body">
      <transition name="workday-end">
        <div v-if="endOpen" class="workday-end-overlay" v-modal-close="closeEnd">
          <div class="workday-end-card">
            <h4 class="workday-end-title">Закончить рабочий день?</h4>
            <div class="workday-end-summary">
              <div><span>Сегодня в системе:</span><strong>{{ formattedElapsed }}</strong></div>
            </div>

            <label class="workday-end-field">
              <span>Краткий итог дня <em>(необязательно)</em></span>
              <textarea
                v-model="noteEnd"
                rows="3"
                :disabled="submitting"
                placeholder="Например: закрыт КП по объекту X, согласован график…"
              />
            </label>

            <div class="workday-end-actions">
              <UiButton variant="ghost" size="sm" :disabled="submitting" @click="closeEnd">
                Отмена
              </UiButton>
              <UiButton
                variant="primary"
                size="sm"
                icon-left="fas fa-check"
                :loading="submitting"
                @click="onEnd"
              >
                Закончить
              </UiButton>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script>
import { computed, ref, toRefs } from 'vue'
import { useWorkdayStore } from '../../stores/workday'
import { UiButton } from './'

export default {
  name: 'WorkdayTopbarChip',
  components: { UiButton },
  setup() {
    const store = useWorkdayStore()
    const { isActive, formattedElapsed, trackWorkTime, idleTimeoutMinutes } = toRefs(store)

    const endOpen = ref(false)
    const noteEnd = ref('')
    const submitting = ref(false)
    const isHidden = ref(false)

    // FE-only флаг, что вкладка в фоне (используется только для визуального стиля).
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        isHidden.value = document.hidden
      })
    }

    const visible = computed(() => trackWorkTime.value)

    const openEnd = () => { endOpen.value = true }
    const closeEnd = () => {
      if (submitting.value) return
      endOpen.value = false
      noteEnd.value = ''
    }

    const onEnd = async () => {
      if (submitting.value) return
      submitting.value = true
      try {
        await store.endDay({ reason: 'manual', note_end: noteEnd.value.trim() || null })
        endOpen.value = false
        noteEnd.value = ''
      } finally {
        submitting.value = false
      }
    }

    return {
      visible,
      isActive,
      formattedElapsed,
      idleTimeoutMinutes,
      isHidden,
      endOpen,
      noteEnd,
      submitting,
      openEnd,
      closeEnd,
      onEnd,
    }
  },
}
</script>

<style scoped>
.workday-chip-wrapper {
  display: inline-flex;
  align-items: center;
}

.workday-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--color-success-soft, rgba(34, 197, 94, 0.12));
  color: var(--color-success, #16a34a);
  border: 1px solid var(--color-success, #16a34a);
  font-size: 0.85rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: background 0.15s, transform 0.05s;
}
.workday-chip:hover { background: var(--color-success-soft-strong, rgba(34, 197, 94, 0.22)); }
.workday-chip:active { transform: scale(0.98); }
.workday-chip.is-paused {
  background: var(--color-surface-2, #f1f5f9);
  color: var(--color-text-muted, #64748b);
  border-color: var(--color-border, rgba(0,0,0,0.1));
}

.workday-chip-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--color-success, #16a34a);
  box-shadow: 0 0 0 0 rgba(34,197,94,0.6);
  animation: wd-pulse 1.6s ease-out infinite;
}
.workday-chip.is-paused .workday-chip-dot {
  background: var(--color-text-subtle, #94a3b8);
  animation: none;
}
@keyframes wd-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(34,197,94,0.55); }
  70%  { box-shadow: 0 0 0 8px rgba(34,197,94,0); }
  100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}

.workday-chip-icon {
  font-size: 0.66rem;
  opacity: 0.65;
}

/* End dialog (small confirm). */
.workday-end-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  z-index: 10500;
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.workday-end-card {
  background: var(--color-surface, #fff);
  color: var(--color-text, #0f172a);
  border-radius: 16px;
  padding: 22px 24px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.24);
  border: 1px solid var(--color-border, rgba(0,0,0,0.06));
}
.workday-end-title {
  margin: 0 0 12px;
  font-size: 1.1rem;
  font-weight: 700;
}
.workday-end-summary {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--color-surface-2, #f8fafc);
  font-size: 0.88rem;
}
.workday-end-summary div { display: flex; justify-content: space-between; gap: 12px; }
.workday-end-summary span { color: var(--color-text-muted, #64748b); }
.workday-end-summary strong { font-variant-numeric: tabular-nums; }

.workday-end-field { display: block; margin-bottom: 16px; }
.workday-end-field > span {
  display: block;
  margin-bottom: 6px;
  font-size: 0.82rem;
  font-weight: 600;
}
.workday-end-field em { font-style: normal; font-weight: 400; color: var(--color-text-muted, #64748b); }
.workday-end-field textarea {
  width: 100%;
  resize: vertical;
  padding: 8px 10px;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, rgba(0,0,0,0.1));
  border-radius: 8px;
  outline: none;
}
.workday-end-field textarea:focus {
  border-color: var(--color-primary, #6366f1);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18);
}

.workday-end-actions {
  display: flex; justify-content: flex-end; gap: 8px;
}

.workday-end-enter-active, .workday-end-leave-active { transition: opacity 0.18s ease; }
.workday-end-enter-from, .workday-end-leave-to { opacity: 0; }
</style>
