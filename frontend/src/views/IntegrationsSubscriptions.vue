<template>
  <div class="event-subs-view p-3">
    <div class="d-flex justify-between align-center mb-3">
      <h2 class="m-0">Подписки event bus</h2>
      <button class="btn btn-primary" @click="openCreate">
        <i class="fas fa-plus mr-1"></i> Добавить подписку
      </button>
    </div>

    <div v-if="loading && !items.length" class="text-muted">Загрузка…</div>
    <div v-else-if="!items.length" class="text-muted text-center py-5">
      Подписок ещё нет. Добавьте первую, чтобы внешние системы получали события через webhook.
    </div>
    <div v-else class="table-container card">
      <table class="table">
        <thead>
          <tr>
            <th>Название</th>
            <th>Pattern</th>
            <th>URL</th>
            <th>Active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sub in items" :key="sub.id">
            <td class="fw-500">{{ sub.name }}</td>
            <td class="font-monospace small">{{ sub.event_type_pattern }}</td>
            <td class="small text-muted" :title="sub.target_url">{{ truncate(sub.target_url, 50) }}</td>
            <td>
              <input type="checkbox" :checked="sub.is_active" @change="toggleActive(sub, $event.target.checked)" />
            </td>
            <td class="text-right">
              <button class="btn btn-sm btn-icon" @click="openEdit(sub)" title="Редактировать">
                <i class="fas fa-pen"></i>
              </button>
              <button class="btn btn-sm btn-icon text-danger" @click="remove(sub)" title="Удалить">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Form modal (create/edit) -->
    <div v-if="formOpen" class="modal-overlay" v-modal-close="closeForm">
      <div class="modal-content modal-glass" @click.stop style="max-width: 640px;">
        <div class="modal-glass-header">
          <h4 class="m-0">{{ editing ? 'Изменить подписку' : 'Новая подписка' }}</h4>
          <button class="btn btn-sm btn-icon btn-ghost" @click="closeForm">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <form class="modal-body" @submit.prevent="save">
          <div class="form-group mb-2">
            <label>Название *</label>
            <input v-model="form.name" type="text" class="form-control" required placeholder="Например: Telegram-канал отдел продаж" />
          </div>
          <div class="form-group mb-2">
            <label>Pattern событий *</label>
            <input v-model="form.event_type_pattern" type="text" class="form-control" required placeholder="deal.*, *.after_create, *" />
            <small class="text-muted">Glob: `*` — любое, `deal.*` — все события сделки, `deal.after_create` — точное.</small>
          </div>
          <div class="form-group mb-2">
            <label>URL приёмника *</label>
            <input v-model="form.target_url" type="text" class="form-control" required placeholder="https://example.com/webhook" />
          </div>
          <div class="form-group mb-2">
            <label>HMAC secret *</label>
            <div class="d-flex gap-2">
              <input v-model="form.hmac_secret" type="text" class="form-control" required />
              <button type="button" class="btn btn-outline-secondary" @click="genSecret">
                <i class="fas fa-random"></i>
              </button>
            </div>
            <small class="text-muted">Воркер подписывает каждый webhook hex-digest от sha256(secret, body) → заголовок <code>X-Event-Signature</code>.</small>
          </div>
          <div class="form-group mb-2">
            <label>Описание</label>
            <textarea v-model="form.description" class="form-control" rows="2"></textarea>
          </div>
          <div class="form-group mb-2">
            <label class="d-flex align-center gap-2">
              <input type="checkbox" v-model="form.is_active" />
              <span>Активна</span>
            </label>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeForm">Отмена</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
              <span>{{ editing ? 'Сохранить' : 'Создать' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

const blankForm = () => ({
  name: '',
  event_type_pattern: '*',
  delivery_method: 'webhook',
  target_url: '',
  hmac_secret: '',
  description: '',
  is_active: true,
})

export default {
  name: 'IntegrationsSubscriptions',
  setup() {
    const toast = useToast()
    const { confirm } = useConfirm()
    const items = ref([])
    const loading = ref(false)
    const formOpen = ref(false)
    const editing = ref(null)   // null = create, id = edit
    const form = ref(blankForm())
    const saving = ref(false)

    const load = async () => {
      loading.value = true
      try { items.value = await api.eventBus.listSubscriptions() || [] }
      catch (e) { toast.error(e?.response?.data?.detail || 'Не удалось загрузить подписки'); items.value = [] }
      finally { loading.value = false }
    }

    const openCreate = () => {
      editing.value = null
      form.value = blankForm()
      genSecret()
      formOpen.value = true
    }
    const openEdit = (sub) => {
      editing.value = sub.id
      form.value = {
        name: sub.name,
        event_type_pattern: sub.event_type_pattern,
        delivery_method: sub.delivery_method || 'webhook',
        target_url: sub.target_url,
        hmac_secret: sub.hmac_secret,
        description: sub.description || '',
        is_active: !!sub.is_active,
      }
      formOpen.value = true
    }
    const closeForm = () => { formOpen.value = false; editing.value = null; form.value = blankForm() }

    const save = async () => {
      saving.value = true
      try {
        if (editing.value) await api.eventBus.updateSubscription(editing.value, form.value)
        else await api.eventBus.createSubscription(form.value)
        toast.success('Сохранено')
        closeForm()
        await load()
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось сохранить')
      } finally { saving.value = false }
    }

    const toggleActive = async (sub, value) => {
      try {
        await api.eventBus.updateSubscription(sub.id, { is_active: value })
        sub.is_active = value
      } catch (e) {
        toast.error('Не удалось переключить статус')
        await load()
      }
    }

    const remove = async (sub) => {
      const ok = await confirm({
        title: 'Удалить подписку?',
        message: `«${sub.name}» больше не будет получать события.`,
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      try {
        await api.eventBus.deleteSubscription(sub.id)
        toast.success('Удалено')
        await load()
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось удалить')
      }
    }

    const genSecret = () => {
      const arr = new Uint8Array(24)
      crypto.getRandomValues(arr)
      form.value.hmac_secret = Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('')
    }
    const truncate = (s, n) => !s ? '' : (s.length > n ? s.slice(0, n) + '…' : s)

    onMounted(load)
    return {
      items, loading, formOpen, editing, form, saving,
      load, openCreate, openEdit, closeForm, save, toggleActive, remove, genSecret, truncate,
    }
  }
}
</script>

<style scoped>
.event-subs-view { height: 100%; overflow: auto; }
.font-monospace { font-family: ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace; }
</style>
