/**
 * Локализованное форматирование даты/времени/чисел.
 *
 * Источник настроек — useUiPreferences().prefs.locale:
 *   - dateFormat    — BCP-47 локаль для дат (например 'ru-RU', 'en-US'); null = системная
 *   - numberFormat  — BCP-47 локаль для чисел; null = системная
 *   - timezone      — IANA-таймзона (например 'Europe/Moscow'); null = системная
 *
 * Утилита читает настройки лениво через геттер, чтобы не создавать
 * циклических импортов и реагировать на изменения настроек.
 */
import { useUiPreferences } from '../composables/useUiPreferences'

function locale() {
  const { prefs } = useUiPreferences()
  return prefs.locale || {}
}

function dateLocale() {
  return locale().dateFormat || undefined
}

function numberLocale() {
  return locale().numberFormat || undefined
}

function timeZone() {
  return locale().timezone || undefined
}

export function formatDate(value, options) {
  if (value == null || value === '') return ''
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return new Intl.DateTimeFormat(dateLocale(), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: timeZone(),
    ...(options || {}),
  }).format(d)
}

export function formatDateTime(value, options) {
  if (value == null || value === '') return ''
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return new Intl.DateTimeFormat(dateLocale(), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: timeZone(),
    ...(options || {}),
  }).format(d)
}

export function formatTime(value, options) {
  if (value == null || value === '') return ''
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return new Intl.DateTimeFormat(dateLocale(), {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: timeZone(),
    ...(options || {}),
  }).format(d)
}

export function formatNumber(value, options) {
  const n = Number(value)
  if (!Number.isFinite(n)) return ''
  return new Intl.NumberFormat(numberLocale(), options || {}).format(n)
}
