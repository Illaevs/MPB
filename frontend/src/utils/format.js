/**
 * Локализованное форматирование даты/времени/чисел.
 *
 * Источник настроек — useUiPreferences().prefs.locale:
 *   - dateFormat    — BCP-47 локаль для дат (например 'ru-RU', 'en-US'); null = системная
 *   - numberFormat  — BCP-47 локаль для чисел; null = системная
 *   - timezone      — IANA-таймзона (например 'Europe/Moscow'); null = по умолчанию
 *
 * Зона по умолчанию — **Europe/Moscow**, потому что бэкенд CRM работает
 * на МСК-сервере и пишет `datetime.now()` без TZ-метки. Если фронт
 * откроют в браузере с другой таймзоной (UTC, Europe/Kaliningrad,
 * etc.), всё равно покажется серверное время — это «source of truth»
 * для бизнес-данных (created_at сообщений, дедлайны и т.д.).
 *
 * Парсинг naive ISO-строк делается через `parseServerDate()` —
 * добавляет +03:00, если суффикса нет. Это решает «−3 часа» баг у
 * юзеров вне МСК.
 *
 * Утилита читает настройки лениво через геттер, чтобы не создавать
 * циклических импортов и реагировать на изменения настроек.
 */
import { useUiPreferences } from '../composables/useUiPreferences'
import { parseServerDate } from '../composables/useServerClock'

// Дефолт — Europe/Moscow. Пользователь может переопределить через
// настройки локали (prefs.locale.timezone).
const DEFAULT_TZ = 'Europe/Moscow'

function locale() {
  const { prefs } = useUiPreferences()
  return prefs.locale || {}
}

function dateLocale() {
  return locale().dateFormat || 'ru-RU'
}

function numberLocale() {
  return locale().numberFormat || 'ru-RU'
}

function timeZone() {
  return locale().timezone || DEFAULT_TZ
}

// Хелпер: вернуть Date из любого входа (Date | ISO-строка | epoch ms).
// Если на входе naive ISO-строка с сервера — трактуем как Europe/Moscow.
function toDate(value) {
  if (value == null || value === '') return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value === 'number') {
    const d = new Date(value)
    return Number.isNaN(d.getTime()) ? null : d
  }
  return parseServerDate(value)
}

export function formatDate(value, options) {
  const d = toDate(value)
  if (!d) return ''
  return new Intl.DateTimeFormat(dateLocale(), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: timeZone(),
    ...(options || {}),
  }).format(d)
}

export function formatDateTime(value, options) {
  const d = toDate(value)
  if (!d) return ''
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
  const d = toDate(value)
  if (!d) return ''
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
