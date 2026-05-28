<template>
  <div class="ai-assistant">
    <button
      type="button"
      class="ai-assistant__fab"
      :class="{ 'ai-assistant__fab--open': open }"
      :title="enabled ? 'AI-ассистент' : 'AI временно недоступен'"
      @click="toggleOpen"
    >
      <i class="fas fa-wand-magic-sparkles"></i>
      <span v-if="!compact">{{ enabled ? 'AI' : 'AI off' }}</span>
    </button>

    <transition name="fade">
      <div v-if="open" class="ai-assistant__panel">
        <div class="ai-assistant__header">
          <div>
            <div class="ai-assistant__title">Универсальный AI-ассистент</div>
            <div class="ai-assistant__subtitle">
              {{ enabled ? (model ? `Модель: ${model}` : 'Подключен через backend') : statusDetail }}
            </div>
          </div>
          <div class="ai-assistant__header-actions">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="clearConversation">
              <i class="fas fa-eraser mr-1"></i> Очистить
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="open = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div class="ai-assistant__messages">
          <div
            v-for="(message, index) in messages"
            :key="`${message.role}-${index}`"
            class="ai-assistant__message"
            :class="`ai-assistant__message--${message.role}`"
          >
            <div class="ai-assistant__message-role">
              {{ message.role === 'assistant' ? 'Ассистент' : 'Вы' }}
            </div>
            <div class="ai-assistant__message-body">{{ message.content }}</div>
          </div>

          <div v-if="busy" class="ai-assistant__message ai-assistant__message--assistant">
            <div class="ai-assistant__message-role">Ассистент</div>
            <div class="ai-assistant__message-body">
              <i class="fas fa-spinner fa-spin mr-2"></i>Думаю над ответом...
            </div>
          </div>
        </div>

        <div class="ai-assistant__suggestions">
          <button
            v-for="suggestion in suggestions"
            :key="suggestion"
            type="button"
            class="ai-assistant__suggestion"
            @click="prompt = suggestion"
          >
            {{ suggestion }}
          </button>
        </div>

        <div v-if="error" class="ai-assistant__error">
          <i class="fas fa-triangle-exclamation mr-2"></i>{{ error }}
        </div>

        <div class="ai-assistant__composer">
          <textarea
            v-model.trim="prompt"
            class="form-control ai-assistant__textarea"
            :disabled="busy || !enabled"
            rows="3"
            placeholder="Например: Следующий платеж по сделке Новоленская ТЭС. Сколько у нас расходов за этот месяц?"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <button
            type="button"
            class="btn btn-primary ai-assistant__send"
            :disabled="busy || !enabled || !prompt"
            @click="sendMessage"
          >
            <i class="fas fa-paper-plane mr-1"></i> Отправить
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../services/api'

const route = useRoute()

const open = ref(false)
const busy = ref(false)
const enabled = ref(false)
const model = ref('')
const error = ref('')
const prompt = ref('')
const statusDetail = ref('Проверяю подключение...')
const messages = ref([
  {
    role: 'assistant',
    content: 'Могу ответить по сделкам, товарам, этапам, плановым платежам и расходам за месяц. Если вопрос относится к текущей сделке, учту контекст страницы.',
    usedDealIds: [],
    usedSections: []
  }
])

const suggestions = [
  'Следующий платеж по этой сделке',
  'Сколько у нас расходов за этот месяц?',
  'Какие там товары?',
  'Как идет разработка по ганту?'
]

const compact = computed(() => typeof window !== 'undefined' && window.innerWidth < 768)

const pageContext = computed(() => {
  let entityType = null
  let entityId = null
  if (route.name === 'ProjectDetail' && route.params?.id) {
    entityType = 'deal'
    entityId = String(route.params.id)
  } else if (route.name === 'ContractDetail' && route.params?.id) {
    entityType = 'contract'
    entityId = String(route.params.id)
  } else if (route.name === 'LeadDetail' && route.params?.id) {
    entityType = 'lead'
    entityId = String(route.params.id)
  }
  return {
    route_name: route.name ? String(route.name) : null,
    path: route.fullPath || route.path || null,
    section: route.meta?.section ? String(route.meta.section) : null,
    entity_type: entityType,
    entity_id: entityId,
    params: Object.fromEntries(Object.entries(route.params || {}).map(([key, value]) => [key, String(value)])),
    query: Object.fromEntries(Object.entries(route.query || {}).map(([key, value]) => [key, Array.isArray(value) ? value.map(String) : String(value)]))
  }
})

const conversationHistory = computed(() =>
  messages.value
    .filter((item, index) => !(index === 0 && item.role === 'assistant'))
    .map(item => ({
      role: item.role,
      content: item.content,
      used_deal_ids: item.usedDealIds || [],
      used_sections: item.usedSections || []
    }))
)

const loadStatus = async () => {
  try {
    const data = await api.ai.status()
    enabled.value = !!data?.enabled && !!data?.reachable
    model.value = data?.model || ''
    statusDetail.value = data?.detail || (enabled.value ? 'Подключен' : 'AI недоступен')
  } catch (err) {
    enabled.value = false
    model.value = ''
    statusDetail.value = err?.response?.data?.detail || err?.message || 'Не удалось проверить статус AI'
  }
}

const toggleOpen = async () => {
  open.value = !open.value
  if (open.value && !enabled.value) {
    await loadStatus()
  }
}

const clearConversation = () => {
  messages.value = [
    {
      role: 'assistant',
      content: 'Диалог очищен. Можешь снова спросить по сделкам, товарам, этапам, платежам и расходам.',
      usedDealIds: [],
      usedSections: []
    }
  ]
  error.value = ''
}

const sendMessage = async () => {
  if (!enabled.value || !prompt.value || busy.value) return
  const message = prompt.value.trim()
  if (!message) return

  error.value = ''
  messages.value.push({ role: 'user', content: message, usedDealIds: [], usedSections: [] })
  prompt.value = ''
  busy.value = true

  try {
    const data = await api.ai.assistantChat({
      message,
      history: conversationHistory.value.slice(-10),
      page_context: pageContext.value
    })
    messages.value.push({
      role: 'assistant',
      content: data?.answer || 'AI не вернул ответ.',
      usedDealIds: data?.used_deal_ids || [],
      usedSections: data?.used_sections || []
    })
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || 'Не удалось получить ответ от AI.'
    messages.value.push({
      role: 'assistant',
      content: 'Не удалось обработать запрос. Попробуй сформулировать его короче или уточнить сделку.',
      usedDealIds: [],
      usedSections: []
    })
  } finally {
    busy.value = false
  }
}

watch(
  () => route.fullPath,
  () => {
    error.value = ''
  }
)

onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1200;
}

.ai-assistant__fab {
  min-width: 60px;
  height: 60px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 800;
  box-shadow: 0 14px 32px rgba(37, 99, 235, 0.35);
}

.ai-assistant__fab--open {
  box-shadow: 0 12px 30px rgba(79, 70, 229, 0.45);
}

.ai-assistant__panel {
  width: min(520px, calc(100vw - 32px));
  max-height: min(72vh, 760px);
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.22);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-assistant__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.ai-assistant__title {
  font-size: 1rem;
  font-weight: 800;
  color: #0f172a;
}

.ai-assistant__subtitle {
  margin-top: 4px;
  font-size: 0.8rem;
  color: #64748b;
}

.ai-assistant__header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.ai-assistant__messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px 8px;
  overflow: auto;
  min-height: 180px;
  max-height: 42vh;
}

.ai-assistant__message {
  max-width: 92%;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 0.94rem;
  line-height: 1.5;
}

.ai-assistant__message--assistant {
  align-self: flex-start;
  background: rgba(241, 245, 249, 0.95);
  color: #0f172a;
}

.ai-assistant__message--user {
  align-self: flex-end;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #fff;
}

.ai-assistant__message-role {
  margin-bottom: 4px;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.72;
}

.ai-assistant__message-body {
  white-space: pre-wrap;
}

.ai-assistant__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 20px 12px;
}

.ai-assistant__suggestion {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(59, 130, 246, 0.16);
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.92);
  color: #1d4ed8;
  font-size: 0.82rem;
  font-weight: 700;
}

.ai-assistant__error {
  margin: 0 20px 12px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(254, 226, 226, 0.95);
  color: #b91c1c;
  font-size: 0.85rem;
}

.ai-assistant__composer {
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-assistant__textarea {
  min-height: 94px;
  resize: vertical;
  border-radius: 16px;
}

.ai-assistant__send {
  align-self: flex-end;
  min-height: 42px;
  min-width: 132px;
  border-radius: 12px;
}

:root[data-theme='dark'] .ai-assistant__panel {
  background: rgba(15, 23, 42, 0.94);
  border-color: rgba(148, 163, 184, 0.18);
}

:root[data-theme='dark'] .ai-assistant__title,
:root[data-theme='dark'] .ai-assistant__message--assistant {
  color: #f8fafc;
}

:root[data-theme='dark'] .ai-assistant__subtitle {
  color: rgba(226, 232, 240, 0.72);
}

:root[data-theme='dark'] .ai-assistant__message--assistant {
  background: rgba(30, 41, 59, 0.94);
}

:root[data-theme='dark'] .ai-assistant__suggestion {
  background: rgba(30, 41, 59, 0.94);
  color: #bfdbfe;
  border-color: rgba(96, 165, 250, 0.25);
}

@media (max-width: 768px) {
  .ai-assistant {
    right: 12px;
    left: 12px;
    bottom: 12px;
  }

  .ai-assistant__panel {
    width: 100%;
    max-height: 78vh;
  }

  .ai-assistant__fab {
    width: 60px;
    min-width: 60px;
    padding: 0;
    margin-left: auto;
  }
}
</style>
