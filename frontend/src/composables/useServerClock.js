import { ref, onMounted, onBeforeUnmount, computed } from 'vue'

/**
 * Серверные часы — фиксируют разницу между локальным `Date.now()` и
 * часами сервера. Используется там, где локальные часы устройства
 * могут спешить/отставать: счётчик рабочего дня, часы в шапке и т.п.
 *
 * Откуда берётся offset: HTTP-заголовок `Date` присутствует на каждом
 * ответе uvicorn/FastAPI (стандартный HTTP/1.1 header). При каждом
 * успешном ответе axios-interceptor зовёт `setFromHttpDate(value)`,
 * который пересчитывает offset.
 *
 * `offsetMs` — глобальное состояние модуля (один на приложение),
 * экспонируется через одиночные computed/ref.
 */

// модульный singleton — не делаем defineStore, тут не нужна Pinia
let offsetMs = 0
const offsetRef = ref(0)        // реактивный «снимок» offsetMs (Vue triggers)
let lastSyncedAt = 0            // когда последний раз обновляли offset (epoch ms client)

// «Тики» каждую секунду для реактивных часов в шапке.
const nowTick = ref(Date.now())
let tickTimer = null

function startTicking() {
  if (tickTimer) return
  tickTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
}
function stopTicking() {
  if (tickTimer) { clearInterval(tickTimer); tickTimer = null }
}

/**
 * Обновить offset из HTTP `Date` заголовка. Терпимо относится к
 * битому/отсутствующему заголовку — просто ничего не делает.
 */
export function setFromHttpDate(headerValue) {
  if (!headerValue) return
  try {
    const serverMs = new Date(headerValue).getTime()
    if (!Number.isFinite(serverMs)) return
    const clientMs = Date.now()
    const newOffset = serverMs - clientMs
    // Анти-дребезг: применяем только если расхождение >1с и обновление
    // не чаще раза в 10с (HTTP Date имеет точность до секунды).
    if (Math.abs(newOffset - offsetMs) < 1000 && (clientMs - lastSyncedAt) < 10_000) return
    offsetMs = newOffset
    offsetRef.value = newOffset
    lastSyncedAt = clientMs
  } catch { /* ignore */ }
}

/** Текущее «серверное» epoch ms — то же что Date.now(), но скорректированное. */
export function serverNow() {
  return Date.now() + offsetMs
}

/** Серверный Date в виде объекта (для форматирования). */
export function serverDate() {
  return new Date(Date.now() + offsetMs)
}

/**
 * Композабл-обёртка для подписки в компонентах. Возвращает:
 * - `offsetMs` (реактивный),
 * - `now` (Date — обновляется каждую секунду),
 * - `nowMs` (epoch ms, серверный),
 * - `formatMsk(date)` — форматирует HH:MM в часовом поясе Europe/Moscow.
 */
export function useServerClock() {
  const now = computed(() => new Date(nowTick.value + offsetRef.value))
  const nowMs = computed(() => nowTick.value + offsetRef.value)

  onMounted(startTicking)
  onBeforeUnmount(() => {
    // не останавливаем глобально — может использоваться в нескольких
    // компонентах одновременно; ничего страшного что таймер висит.
  })

  return {
    offsetMs: offsetRef,
    now,
    nowMs,
    formatMsk,
  }
}

const _mskFormatter = new Intl.DateTimeFormat('ru-RU', {
  timeZone: 'Europe/Moscow',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

/** Форматирует Date в HH:MM по Москве (UTC+3) независимо от
 *  локальной таймзоны устройства. */
export function formatMsk(date) {
  try {
    return _mskFormatter.format(date)
  } catch {
    return ''
  }
}

/**
 * Парсит timestamp, пришедший от сервера. Если строка БЕЗ суффикса
 * таймзоны — трактуем как **UTC** (добавляем 'Z'). Причина: SQLite +
 * SQLAlchemy `func.now()` / `server_default=func.now()` пишут в БД
 * `CURRENT_TIMESTAMP` — это всегда UTC по спецификации SQLite,
 * независимо от TZ-настройки самого сервера. Pydantic сериализует
 * naive datetime без TZ-метки → фронту прилетает «голый» ISO,
 * который без хелпера парсится как LOCAL TIME (ECMAScript spec для
 * date-time-форм без TZ) — отсюда «−3 часа» у MSK-юзеров.
 *
 * Если суффикс есть — парсим как есть.
 *
 * Возвращает Date или null.
 */
export function parseServerDate(value) {
  if (!value) return null
  if (value instanceof Date) return value
  const s = String(value)
  const hasTz = /[Zz]|[+-]\d{2}:?\d{2}$/.test(s)
  const d = hasTz ? new Date(s) : new Date(s + 'Z')
  return Number.isNaN(d.getTime()) ? null : d
}

const _mskDateTimeFormatter = new Intl.DateTimeFormat('ru-RU', {
  timeZone: 'Europe/Moscow',
  day: '2-digit',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

/** Полная дата-время по Москве — для списков уведомлений / журналов. */
export function formatMskDateTime(value) {
  const d = parseServerDate(value)
  if (!d) return ''
  try {
    return _mskDateTimeFormatter.format(d)
  } catch {
    return ''
  }
}

// Запускаем тик-таймер при первом импорте — чтобы часы в шапке тикали
// сразу, не дожидаясь монтирования какого-то конкретного компонента.
startTicking()
