<template>
  <aside class="params-panel">
    <header class="params-panel__head">
      <div>
        <span class="params-panel__eyebrow">Параметры</span>
        <h3 class="params-panel__title">Документа</h3>
      </div>
      <span v-if="resolving" class="params-panel__resolving" title="Подгрузка полей">
        <i class="fas fa-spinner fa-spin"></i>
      </span>
    </header>

    <div class="params-panel__body">
      <div v-for="group in fieldGroups" :key="group.id" class="params-panel__group">
        <div v-if="group.label" class="params-panel__group-label">{{ group.label }}</div>

        <div
          v-for="field in group.fields"
          :key="field.key"
          class="params-panel__field"
          :class="{ 'params-panel__field--active': activeFieldKey === field.key }"
          :data-field-key="field.key"
        >
          <label class="params-panel__label">
            {{ field.label }}<span v-if="field.required" class="params-panel__req">*</span>
          </label>

          <!-- ===== ANCHOR controls (drive resolve) ===== -->
          <template v-if="field.role === 'anchor'">
            <!-- recipient company -->
            <CompanySmartSelect
              v-if="field.type === 'company-select'"
              :model-value="anchors.recipientCompanyId.value"
              fetch-url="/api/v1/companies/"
              :fetch-params="{}"
              placeholder="Найти контрагента"
              @update:model-value="$emit('pick-recipient', $event)"
            />

            <!-- our company key (free text — keys are profile-specific) -->
            <input
              v-else-if="field.type === 'our-company-select'"
              type="text"
              class="params-panel__input"
              placeholder="Ключ нашей компании"
              :value="anchors.ourCompanyKey.value"
              @input="anchors.ourCompanyKey.value = $event.target.value"
              @focus="$emit('focus-field', field.key)"
            />

            <!-- deal -->
            <select
              v-else-if="field.type === 'deal-select'"
              class="params-panel__input"
              :value="anchors.dealId.value"
              @change="$emit('pick-deal', $event.target.value)"
            >
              <option value="">— не выбрана —</option>
              <option v-for="d in dealOptions" :key="d.id" :value="d.id">{{ d.title }}</option>
            </select>

            <!-- contract -->
            <select
              v-else-if="field.type === 'contract-select'"
              class="params-panel__input"
              :value="anchors.contractId.value"
              :disabled="!anchors.dealId.value"
              @change="anchors.contractId.value = $event.target.value"
            >
              <option value="">{{ anchors.dealId.value ? '— не выбран —' : 'сначала сделка' }}</option>
              <option v-for="c in contractOptions" :key="c.id" :value="c.id">{{ c.label }}</option>
            </select>

            <!-- recipient bank account -->
            <select
              v-else-if="field.type === 'bank-account-select'"
              class="params-panel__input"
              :value="anchors.bankAccountIndex.value ?? ''"
              @change="anchors.bankAccountIndex.value = $event.target.value === '' ? null : Number($event.target.value)"
            >
              <option value="">— по умолчанию —</option>
              <option v-for="(acc, i) in recipientBankAccounts" :key="i" :value="i">
                {{ bankLabel(acc, i) }}
              </option>
            </select>

            <!-- linked stages -->
            <div v-else-if="field.type === 'stage-multiselect'" class="params-panel__checks">
              <p v-if="!stageOptions.length" class="params-panel__hint">
                {{ anchors.dealId.value ? 'У сделки нет этапов' : 'Выберите сделку' }}
              </p>
              <label v-for="s in stageOptions" :key="s.id" class="params-panel__check">
                <input
                  type="checkbox"
                  :value="s.id"
                  :checked="anchors.linkedStageIds.value.includes(s.id)"
                  @change="toggleStage(s.id)"
                />
                <span>{{ s.name }}</span>
              </label>
            </div>

            <!-- payment rows -->
            <div v-else-if="field.type === 'payment-rows'" class="params-panel__pay">
              <p v-if="!paymentOptions.length" class="params-panel__hint">
                {{ anchors.dealId.value ? 'Нет входящих платежей' : 'Выберите сделку' }}
              </p>
              <label v-for="p in paymentOptions" :key="p.id" class="params-panel__check">
                <input
                  type="checkbox"
                  :checked="isPaymentPicked(p.id)"
                  @change="togglePayment(p)"
                />
                <span>{{ formatMoney(p.amount) }} · {{ p.date || '—' }}</span>
              </label>
            </div>

            <!-- recipient override text fields -->
            <input
              v-else
              type="text"
              class="params-panel__input"
              :placeholder="field.placeholder"
              :value="anchorTextValue(field.key)"
              @input="setAnchorText(field.key, $event.target.value)"
              @focus="$emit('focus-field', field.key)"
            />
          </template>

          <!-- ===== RESOLVED (read-only, filled by /editor/resolve) ===== -->
          <div v-else class="params-panel__resolved">
            <span v-if="resolvedText(field.key)">{{ resolvedText(field.key) }}</span>
            <span v-else class="params-panel__resolved-empty">— подставится автоматически —</span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import CompanySmartSelect from '../../../components/ui/CompanySmartSelect.vue'

const GROUP_LABELS = {
  parties: 'Стороны',
  context: 'Договор / сделка',
  bank: 'Банк',
  lines: 'Строки документа',
  document: 'Документ',
  requisites: 'Реквизиты (авто)',
  totals: 'Суммы (авто)',
}
const GROUP_ORDER = ['parties', 'context', 'bank', 'lines', 'document', 'requisites', 'totals']

// recipient override text fields → anchor ref name
const TEXT_ANCHOR_BY_KEY = {
  'recipient.eio': 'recipientEio',
  'recipient.to_name': 'recipientToName',
  'recipient.genitive_name': 'recipientGenitiveName',
  'recipient.short_name': 'recipientShortName',
}

export default {
  name: 'OutgoingParametersPanel',
  components: { CompanySmartSelect },
  props: {
    placeholderFields: { type: Array, default: () => [] },
    fieldValues: { type: Object, default: () => ({}) },
    activeFieldKey: { type: String, default: '' },
    anchors: { type: Object, required: true },
    dealOptions: { type: Array, default: () => [] },
    contractOptions: { type: Array, default: () => [] },
    stageOptions: { type: Array, default: () => [] },
    paymentOptions: { type: Array, default: () => [] },
    recipientCompany: { type: Object, default: null },
    resolving: { type: Boolean, default: false },
  },
  emits: ['update:fieldValues', 'focus-field', 'pick-recipient', 'pick-deal'],
  setup(props) {
    const fieldGroups = computed(() => {
      const buckets = new Map()
      for (const f of props.placeholderFields) {
        const g = f.group || '_default'
        if (!buckets.has(g)) buckets.set(g, { id: g, label: GROUP_LABELS[g] || '', fields: [] })
        buckets.get(g).fields.push(f)
      }
      const ordered = GROUP_ORDER.filter((g) => buckets.has(g)).map((g) => buckets.get(g))
      for (const [g, b] of buckets) if (!GROUP_ORDER.includes(g)) ordered.push(b)
      return ordered
    })

    const resolvedText = (key) => {
      const v = props.fieldValues[key]
      return v === undefined || v === null ? '' : String(v)
    }

    const recipientBankAccounts = computed(() => {
      const raw = props.recipientCompany?.bank_accounts || []
      return Array.isArray(raw) ? raw : []
    })
    const bankLabel = (acc, i) => {
      const bank = acc.bank_name || acc.name || `Счёт ${i + 1}`
      const rs = acc.account_rs || acc.rs || acc.account || ''
      return rs ? `${bank} · ${rs}` : bank
    }

    const anchorTextValue = (key) => {
      const refName = TEXT_ANCHOR_BY_KEY[key]
      return refName ? (props.anchors[refName]?.value || '') : ''
    }
    const setAnchorText = (key, val) => {
      const refName = TEXT_ANCHOR_BY_KEY[key]
      if (refName && props.anchors[refName]) props.anchors[refName].value = val
    }

    const toggleStage = (id) => {
      const arr = props.anchors.linkedStageIds.value.slice()
      const i = arr.indexOf(id)
      if (i >= 0) arr.splice(i, 1)
      else arr.push(id)
      props.anchors.linkedStageIds.value = arr
    }

    const isPaymentPicked = (id) =>
      props.anchors.linkedPaymentItems.value.some((p) => p.entry_id === id || p.id === id)
    const togglePayment = (p) => {
      const arr = props.anchors.linkedPaymentItems.value.slice()
      const idx = arr.findIndex((x) => x.entry_id === p.id || x.id === p.id)
      if (idx >= 0) arr.splice(idx, 1)
      else arr.push({ entry_id: p.id, amount: p.amount, note: '' })
      props.anchors.linkedPaymentItems.value = arr
    }

    const formatMoney = (n) => {
      const num = Number(n)
      if (!Number.isFinite(num)) return String(n ?? '—')
      return num.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₽'
    }

    return {
      fieldGroups, resolvedText, recipientBankAccounts, bankLabel,
      anchorTextValue, setAnchorText, toggleStage,
      isPaymentPicked, togglePayment, formatMoney,
    }
  }
}
</script>

<style scoped>
.params-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border-subtle);
}
.params-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.params-panel__eyebrow {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-subtle);
  display: block;
}
.params-panel__title {
  margin: 0;
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}
.params-panel__resolving { color: var(--color-primary); font-size: var(--text-sm); }

.params-panel__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.params-panel__group { display: flex; flex-direction: column; gap: 12px; }
.params-panel__group-label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.params-panel__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-radius: var(--radius-md);
}
.params-panel__field--active {
  background: var(--color-primary-soft);
  padding: 8px 10px;
  margin: -8px -10px;
}
.params-panel__label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.3px;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.params-panel__req { color: var(--color-danger); margin-left: 2px; }

.params-panel__input {
  width: 100%;
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
}
.params-panel__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.params-panel__input:disabled { opacity: 0.55; cursor: not-allowed; }

.params-panel__resolved {
  min-height: 36px;
  padding: 8px 10px;
  border: 1px dashed var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-text);
  font-size: var(--text-sm);
  word-break: break-word;
}
.params-panel__resolved-empty { color: var(--color-text-subtle); font-style: italic; }

.params-panel__checks,
.params-panel__pay { display: flex; flex-direction: column; gap: 6px; }
.params-panel__check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
}
.params-panel__check input { accent-color: var(--color-primary); }
.params-panel__hint { margin: 0; font-size: var(--text-xs); color: var(--color-text-subtle); }
</style>
