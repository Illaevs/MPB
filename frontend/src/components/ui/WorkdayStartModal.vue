<template>
  <Teleport to="body">
    <transition name="workday-modal">
      <div v-if="visible" class="workday-modal-overlay" role="dialog" aria-modal="true">
        <div class="workday-modal-card">
          <div class="workday-modal-greeting">
            <i class="fas fa-sun"></i>
            <span>{{ greeting }}</span>
          </div>
          <h2 class="workday-modal-title">Начнём рабочий день?</h2>
          <p class="workday-modal-hint">
            Пока вы не начнёте рабочий день, остальная часть системы заблокирована.
            Учёт времени автоматически приостановится через
            <strong>{{ idleTimeoutMinutes }} мин</strong> бездействия.
          </p>

          <label class="workday-modal-field">
            <span class="workday-modal-field-label">Что планируете на сегодня? <em>(необязательно)</em></span>
            <textarea
              v-model="noteStart"
              class="workday-modal-textarea"
              rows="3"
              placeholder="Например: разобрать почту, закрыть КП по объекту…"
              :disabled="submitting"
            />
          </label>

          <div class="workday-modal-actions">
            <UiButton
              variant="primary"
              size="md"
              icon-left="fas fa-play"
              :loading="submitting"
              @click="onStart"
            >
              Начать рабочий день
            </UiButton>
          </div>

          <div v-if="errorMsg" class="workday-modal-error">{{ errorMsg }}</div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script>
import { computed, ref, toRefs } from 'vue'
import { useWorkdayStore } from '../../stores/workday'
import { UiButton } from './'

export default {
  name: 'WorkdayStartModal',
  components: { UiButton },
  setup() {
    const store = useWorkdayStore()
    const { showStartModal, idleTimeoutMinutes } = toRefs(store)
    const submitting = ref(false)
    const noteStart = ref('')
    const errorMsg = ref('')

    const visible = computed(() => showStartModal.value)

    const greeting = computed(() => {
      const h = new Date().getHours()
      if (h < 5) return 'Доброй ночи'
      if (h < 12) return 'Доброе утро'
      if (h < 17) return 'Добрый день'
      return 'Добрый вечер'
    })

    const onStart = async () => {
      if (submitting.value) return
      submitting.value = true
      errorMsg.value = ''
      try {
        await store.startDay({ note_start: noteStart.value.trim() || null })
        noteStart.value = ''
      } catch (e) {
        errorMsg.value = e?.response?.data?.detail || 'Не удалось начать рабочий день'
      } finally {
        submitting.value = false
      }
    }

    return {
      visible,
      idleTimeoutMinutes,
      submitting,
      noteStart,
      errorMsg,
      greeting,
      onStart,
    }
  },
}
</script>

<style scoped>
.workday-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.62);
  backdrop-filter: blur(8px) saturate(140%);
  z-index: 11000;  /* выше toast (9999) и confirm (10000) */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.workday-modal-card {
  background: var(--color-surface, #fff);
  color: var(--color-text, #0f172a);
  border-radius: 20px;
  padding: 32px 36px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 32px 64px rgba(15, 23, 42, 0.32), 0 4px 16px rgba(15, 23, 42, 0.12);
  border: 1px solid var(--color-border, rgba(0,0,0,0.06));
}

.workday-modal-greeting {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--color-primary-soft, rgba(99,102,241,0.12));
  color: var(--color-primary, #6366f1);
  font-size: 0.82rem;
  font-weight: 600;
}
.workday-modal-greeting i { font-size: 0.85rem; }

.workday-modal-title {
  margin: 14px 0 6px;
  font-size: 1.55rem;
  line-height: 1.2;
  font-weight: 700;
}

.workday-modal-hint {
  margin: 0 0 20px;
  color: var(--color-text-muted, #64748b);
  font-size: 0.92rem;
  line-height: 1.45;
}
.workday-modal-hint strong {
  color: var(--color-text, #0f172a);
  font-weight: 600;
}

.workday-modal-field {
  display: block;
  margin-bottom: 20px;
}
.workday-modal-field-label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text, #0f172a);
}
.workday-modal-field-label em {
  font-style: normal;
  font-weight: 400;
  color: var(--color-text-muted, #64748b);
}
.workday-modal-textarea {
  width: 100%;
  resize: vertical;
  padding: 10px 12px;
  font-size: 0.92rem;
  font-family: inherit;
  color: var(--color-text, #0f172a);
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, rgba(0,0,0,0.1));
  border-radius: 10px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.workday-modal-textarea:focus {
  border-color: var(--color-primary, #6366f1);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18);
}

.workday-modal-actions {
  display: flex;
  justify-content: flex-end;
}

.workday-modal-error {
  margin-top: 12px;
  font-size: 0.86rem;
  color: var(--color-danger, #dc2626);
}

.workday-modal-enter-active,
.workday-modal-leave-active { transition: opacity 0.2s ease; }
.workday-modal-enter-from,
.workday-modal-leave-to { opacity: 0; }
.workday-modal-enter-active .workday-modal-card,
.workday-modal-leave-active .workday-modal-card { transition: transform 0.2s ease; }
.workday-modal-enter-from .workday-modal-card,
.workday-modal-leave-to .workday-modal-card { transform: translateY(12px) scale(0.96); }
</style>
