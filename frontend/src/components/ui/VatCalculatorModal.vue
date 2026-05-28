<template>
  <UiModal
    :model-value="modelValue"
    title="Калькулятор НДС"
    size="lg"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="vat-calculator-grid">
      <div class="form-group">
        <label>Сумма с НДС</label>
        <input
          v-model="amountInput"
          type="text"
          inputmode="decimal"
          class="form-control"
          placeholder="0,00"
        >
      </div>
      <div class="form-group">
        <label>Ставка, %</label>
        <input
          v-model="rateInput"
          type="text"
          inputmode="decimal"
          class="form-control"
          placeholder="22"
        >
      </div>
    </div>

    <div class="vat-calculator-note">
      Выделение НДС из суммы с НДС: НДС = Сумма × Ставка / (100 + Ставка)
    </div>

    <div class="vat-calculator-results">
      <div class="vat-calculator-card">
        <span class="vat-calculator-card__label">Сумма с НДС</span>
        <strong class="vat-calculator-card__value">{{ formatMoney(calculation.gross) }} ₽</strong>
      </div>
      <div class="vat-calculator-card vat-calculator-card--accent">
        <span class="vat-calculator-card__label">Сумма НДС</span>
        <strong class="vat-calculator-card__value">{{ formatMoney(calculation.vat) }} ₽</strong>
      </div>
      <div class="vat-calculator-card">
        <span class="vat-calculator-card__label">Сумма без НДС</span>
        <strong class="vat-calculator-card__value">{{ formatMoney(calculation.net) }} ₽</strong>
      </div>
    </div>

    <div class="vat-calculator-words">
      <div v-for="item in wordRows" :key="item.key" class="vat-calculator-word-card">
        <div class="vat-calculator-word-card__header">
          <strong>{{ item.label }}</strong>
          <span>{{ formatMoney(item.value) }} ₽</span>
        </div>

        <div class="vat-calculator-copy-row">
          <div class="vat-calculator-copy-row__text">{{ item.plain }}</div>
          <UiButton variant="outline" size="sm" icon-left="far fa-copy" @click="copyVatText(item.plain, item.label)">
            Копировать
          </UiButton>
        </div>

        <div class="vat-calculator-copy-row">
          <div class="vat-calculator-copy-row__text">{{ item.parenthesized }}</div>
          <UiButton variant="outline" size="sm" icon-left="far fa-copy" @click="copyVatText(item.parenthesized, `${item.label} в скобках`)">
            Копировать
          </UiButton>
        </div>
      </div>
    </div>

    <template #footer>
      <UiButton variant="ghost" @click="close">Закрыть</UiButton>
    </template>
  </UiModal>
</template>

<script>
import { computed, ref } from 'vue'
import UiModal from './UiModal.vue'
import UiButton from './UiButton.vue'
import { useToast } from '../../composables/useToast'
import { formatRussianMoneyWords } from '../../utils/russianMoneyWords'

const parseDecimalInput = (value) => {
  const normalized = String(value ?? '').replace(/\s+/g, '').replace(',', '.')
  if (!normalized) return 0
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : 0
}

const roundMoney = (value) => Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100

const formatMoney = (value) => new Intl.NumberFormat('ru-RU', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(Number(value || 0))

const copyText = async (value) => {
  if (navigator?.clipboard?.writeText) {
    await navigator.clipboard.writeText(value)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.setAttribute('readonly', 'readonly')
  textarea.style.position = 'absolute'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  document.body.removeChild(textarea)
}

export default {
  name: 'VatCalculatorModal',
  components: { UiModal, UiButton },
  props: {
    modelValue: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const amountInput = ref('')
    const rateInput = ref('22')

    const { success: toastSuccess, error: toastError } = useToast()

    const calculation = computed(() => {
      const gross = Math.max(0, roundMoney(parseDecimalInput(amountInput.value)))
      const rate = Math.max(0, roundMoney(parseDecimalInput(rateInput.value)))
      const vat = gross > 0 && rate > 0 ? roundMoney((gross * rate) / (100 + rate)) : 0
      const net = roundMoney(gross - vat)
      return { gross, rate, vat, net }
    })

    const wordRows = computed(() => [
      {
        key: 'gross',
        label: 'Сумма с НДС',
        value: calculation.value.gross,
        plain: formatRussianMoneyWords(calculation.value.gross),
        parenthesized: formatRussianMoneyWords(calculation.value.gross, { parenthesized: true }),
      },
      {
        key: 'net',
        label: 'Сумма без НДС',
        value: calculation.value.net,
        plain: formatRussianMoneyWords(calculation.value.net),
        parenthesized: formatRussianMoneyWords(calculation.value.net, { parenthesized: true }),
      },
      {
        key: 'vat',
        label: 'Сумма НДС',
        value: calculation.value.vat,
        plain: formatRussianMoneyWords(calculation.value.vat),
        parenthesized: formatRussianMoneyWords(calculation.value.vat, { parenthesized: true }),
      },
    ])

    const copyVatText = async (text, label) => {
      try {
        await copyText(text)
        toastSuccess(`${label} скопировано`)
      } catch (error) {
        console.error('Error copying VAT text:', error)
        toastError('Не удалось скопировать текст')
      }
    }

    const close = () => emit('update:modelValue', false)

    return {
      amountInput,
      rateInput,
      calculation,
      wordRows,
      formatMoney,
      copyVatText,
      close,
    }
  },
}
</script>

<style scoped>
.vat-calculator-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(220px, 0.6fr);
  gap: var(--space-4);
}

.vat-calculator-note {
  margin-top: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-text-muted);
  font-size: var(--text-md);
}

.vat-calculator-results {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.vat-calculator-card {
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.vat-calculator-card--accent {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-soft-strong);
}

.vat-calculator-card__label {
  display: block;
  margin-bottom: var(--space-1);
  font-size: var(--text-md);
  color: var(--color-text-muted);
}

.vat-calculator-card__value {
  display: block;
  font-size: var(--text-xl);
  line-height: 1.2;
  color: var(--color-text);
}

.vat-calculator-words {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-5);
}

.vat-calculator-word-card {
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.vat-calculator-word-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.vat-calculator-word-card__header strong {
  color: var(--color-text);
}

.vat-calculator-word-card__header span {
  color: var(--color-text-muted);
  white-space: nowrap;
}

.vat-calculator-copy-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-3);
  align-items: center;
}

.vat-calculator-copy-row + .vat-calculator-copy-row {
  margin-top: var(--space-2);
}

.vat-calculator-copy-row__text {
  min-height: 42px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  line-height: var(--leading-normal);
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (max-width: 900px) {
  .vat-calculator-grid,
  .vat-calculator-results {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .vat-calculator-word-card__header,
  .vat-calculator-copy-row {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
