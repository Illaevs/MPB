<template>
  <div v-if="modelValue" class="modal-overlay" v-modal-close="cancel">
    <div class="modal-content lead-form-modal" @click.stop>
      <div class="modal-header">
        <h3 class="m-0">{{ isEditing ? 'Редактировать лид' : 'Новый лид' }}</h3>
        <button class="icon-btn" @click="cancel"><i class="fas fa-times"></i></button>
      </div>

      <form class="modal-body" @submit.prevent="onSubmit">
        <div class="form-row">
          <div class="form-group form-group--wide">
            <label>Название <span class="req">*</span></label>
            <input
              v-model="form.title"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': errors.title }"
              required
            />
            <small v-if="errors.title" class="text-danger">{{ errors.title }}</small>
          </div>
          <div class="form-group">
            <label>Статус</label>
            <select v-model="form.status" class="form-control">
              <option v-for="s in statuses" :key="s.key" :value="s.key">{{ s.label }}</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group form-group--wide">
            <label>Наименование объекта</label>
            <input v-model="form.obj_name" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label>Тип объекта</label>
            <select v-model="form.object_type" class="form-control">
              <option value="">Не выбран</option>
              <option v-for="o in objectTypeOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Адрес объекта</label>
          <input v-model="form.address" type="text" class="form-control" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Заказчик</label>
            <CompanySmartSelect v-model="form.customer_id" :options="companies" placeholder="Найти заказчика" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Ответственный</label>
            <select v-model="form.responsible_user_id" class="form-control">
              <option value="">Не назначен</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name || u.email || u.id }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Площадь (м²)</label>
            <input v-model.number="form.object_area" type="number" class="form-control" min="0" step="0.01" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Аванс, %</label>
            <input
              v-model.number="form.advance_percent"
              type="number"
              class="form-control"
              min="0"
              max="100"
              step="1"
              @blur="clampAdvance"
            />
          </div>
          <!-- НДС больше не выбирается на уровне лида — он определяется
               автоматически по составу товаров (per-line tax_rate). Это
               держит лид и КП консистентными. vat_rate в form-data
               остаётся со значением по умолчанию (22), бэк его получит,
               но пользователь не видит и не меняет. -->
          <div class="form-group"></div>
        </div>
      </form>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="cancel">Отмена</button>
        <button type="button" class="btn btn-primary" :disabled="saving" @click="onSubmit">
          <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
          <i v-else class="fas fa-check mr-1"></i>
          {{ isEditing ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import CompanySmartSelect from '../ui/CompanySmartSelect.vue'

const OBJECT_TYPES = [
  'Линейные - метрополитен',
  'Линейные - дороги, эстакады',
  'Линейные - инженерные сети',
  'Образовательные учреждения',
  'Объекты здравоохранения',
  'Спортивные сооружения',
  'Административные здания',
  'Жилые комплексы',
  'Торговые центры',
  'Паркинги',
  'Аэропорты',
  'Промышленные объекты',
  'Складские/архивные здания',
]

const blank = () => ({
  id: null,
  title: '',
  obj_name: '',
  address: '',
  object_type: '',
  object_area: null,
  customer_id: '',
  responsible_user_id: '',
  advance_percent: 0,
  // НДС больше не выбирается в UI — лид имеет дефолт 22% для бэка,
  // фактическая ставка считается по составу товаров (per-line tax_rate).
  vat_rate: 22,
  status: 'incoming',
})

export default {
  name: 'LeadFormModal',
  components: { CompanySmartSelect },
  props: {
    modelValue: { type: Boolean, default: false },
    lead: { type: Object, default: null },
    companies: { type: Array, default: () => [] },
    users: { type: Array, default: () => [] },
    statuses: { type: Array, default: () => [] },
    saving: { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'submit', 'cancel'],
  setup(props, { emit }) {
    const form = ref(blank())
    const errors = ref({})

    const isEditing = computed(() => !!props.lead?.id)

    const normalizeId = (v) => v ? String(v).replace(/-/g, '').toLowerCase() : ''
    const matchCompanyId = (val) => {
      if (!val) return ''
      const target = normalizeId(val)
      const match = props.companies.find(c => normalizeId(c.id) === target)
      return match ? match.id : ''
    }
    const matchUserId = (val) => {
      if (!val) return ''
      const target = normalizeId(val)
      const match = props.users.find(u => normalizeId(u.id) === target)
      return match ? match.id : ''
    }

    const initForm = () => {
      if (props.lead) {
        form.value = {
          ...blank(),
          ...props.lead,
          customer_id: matchCompanyId(props.lead.customer_id),
          responsible_user_id: matchUserId(props.lead.responsible_user_id),
        }
      } else {
        form.value = blank()
      }
      errors.value = {}
    }

    watch(() => props.modelValue, (open) => { if (open) initForm() })
    watch(() => props.lead, () => { if (props.modelValue) initForm() })

    const clampAdvance = () => {
      const v = Number(form.value.advance_percent)
      if (Number.isNaN(v)) form.value.advance_percent = 0
      else form.value.advance_percent = Math.min(100, Math.max(0, v))
    }

    const validate = () => {
      const e = {}
      if (!String(form.value.title || '').trim()) e.title = 'Введите название'
      errors.value = e
      return Object.keys(e).length === 0
    }

    const onSubmit = () => {
      if (!validate()) return
      clampAdvance()
      const payload = { ...form.value }
      // Drop empties/null for safe PUT/POST
      const cleaned = {}
      Object.keys(payload).forEach((k) => {
        if (payload[k] === '' || payload[k] === null || payload[k] === undefined) return
        cleaned[k] = payload[k]
      })
      // Always send title
      cleaned.title = (form.value.title || '').trim()
      emit('submit', { isEditing: isEditing.value, payload: cleaned, full: form.value })
    }

    const cancel = () => {
      emit('cancel')
      emit('update:modelValue', false)
    }

    return {
      form, errors, isEditing, objectTypeOptions: OBJECT_TYPES,
      clampAdvance, onSubmit, cancel,
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.42);
  z-index: 9100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.lead-form-modal {
  width: min(680px, 100%);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface, #fff);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.22);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}
.modal-header h3 { font-size: 1.05rem; }
.modal-body {
  padding: 14px 18px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}
.icon-btn {
  width: 30px; height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
}
.icon-btn:hover { background: rgba(0,0,0,0.05); }
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.form-group { margin: 0; display: flex; flex-direction: column; }
.form-group label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 600;
  margin-bottom: 4px;
}
.form-group--wide { grid-column: span 1; }
.req { color: #c62828; }
.is-invalid { border-color: #c62828 !important; }
@media (max-width: 720px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
