import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'
import { serverNow } from '../composables/useServerClock'

/**
 * Состояние «рабочего дня» — учёт времени для текущего пользователя.
 *
 * Модель проста:
 *  - `session` — активная сессия (или null, если не начат).
 *  - `trackWorkTime` — выключатель фичи для роли (если false — модал
 *    и счётчик не показываются вовсе).
 *  - `idleTimeoutMinutes` — через сколько минут бездействия фронт
 *    автоматически закроет сессию (с `ended_at = lastActivityAt`).
 *  - `lastActivityAt` — обновляется композаблом useIdleTracker'ом
 *    на каждое движение/клик/keydown/scroll/visibilitychange.
 *
 * Поведение модала:
 *  - При первом GET /workday/active после логина: если track + нет сессии
 *    → showStartModal = true (App.vue монтирует блокирующий слой).
 *  - После авто-закрытия по idle → снова нет активной → снова модал
 *    при следующем взаимодействии (юзер так попросил).
 */
const HEARTBEAT_MS = 60_000        // 60 секунд между heartbeat
const IDLE_CHECK_MS = 15_000       // 15 секунд между проверками idle (локальный таймер)
const RECENT_ACTIVITY_WINDOW_MS = 30_000  // heartbeat только если была активность в последние 30 сек

export const useWorkdayStore = defineStore('workday', () => {
  const session = ref(null)
  const trackWorkTime = ref(false)
  const idleTimeoutMinutes = ref(30)
  const loading = ref(false)
  const initialized = ref(false)

  // Сумма ЗАКРЫТЫХ сегодняшних сессий по московской дате (от бэкенда).
  // К ней фронт прибавляет live-elapsed активной сессии — чтобы цифра
  // в чипе не «прыгала» от поллинга, а росла секунда в секунду.
  // После «Закончить день» бэк её увеличит на следующем GET /active.
  const workedTodaySeconds = ref(0)

  // Активность пользователя — обновляется глобальным трекером.
  // Дата в мс СЕРВЕРНОГО времени (serverNow = Date.now() + offset), чтобы
  // не зависеть от спешащих/отстающих часов устройства.
  const lastActivityAt = ref(serverNow())

  // Тикающий таймер для счётчика на топбаре — увеличивается каждую секунду
  // пока сессия активна, чтобы шапка перерисовывалась. Тоже серверное время.
  const nowTick = ref(serverNow())

  let pollTimer = null
  let heartbeatTimer = null
  let idleCheckTimer = null
  let tickTimer = null

  const isActive = computed(() => !!session.value)
  const showStartModal = computed(() =>
    initialized.value && trackWorkTime.value && !session.value
  )

  // Длительность активной сессии — для отображения «04:22:18» в шапке.
  // ISO-строки от бэка могут прийти как tz-aware (`...+00:00`) — это
  // штатный случай, — так и как naive (`...875762` без TZ) для старых
  // записей в SQLite. `new Date('naive_iso')` интерпретирует naive
  // как local, из-за чего счётчик стартует со смещения таймзоны
  // (например, +03:00 в МСК). Помечаем naive строки как UTC явно.
  function parseBackendDate(value) {
    if (!value) return null
    const s = String(value)
    const hasTZ = /[+\-]\d{2}:?\d{2}$|Z$/i.test(s)
    return new Date(hasTZ ? s : s + 'Z')
  }

  // Live-вклад АКТИВНОЙ сессии: секунды от started_at до nowTick.
  // Не учитывает закрытые — их даёт бэк через workedTodaySeconds.
  const activeSessionElapsedSeconds = computed(() => {
    if (!session.value?.started_at) return 0
    const started = parseBackendDate(session.value.started_at)?.getTime()
    if (!Number.isFinite(started)) return 0
    // Якорь конца счётчика — обычно «сейчас». Но если серверный
    // last_activity_at протух (вкладка/сеть умерли, heartbeat не идёт) —
    // сервер засчитает время только до него, поэтому и чип замораживаем
    // там же, а не накручиваем «мёртвые» часы простоя.
    let endMs = nowTick.value
    const lastAct = parseBackendDate(session.value.last_activity_at)?.getTime()
    if (Number.isFinite(lastAct)) {
      const idleMs = (idleTimeoutMinutes.value || 30) * 60_000
      if (nowTick.value - lastAct > idleMs) endMs = lastAct
    }
    return Math.max(0, Math.floor((endMs - started) / 1000))
  })

  // ИТОГ ЗА ДЕНЬ — то что видит юзер в чипе.
  // closed (с бэка, обновляется при поллинге /active раз в 60с)
  // + live активная (тикает каждую секунду на фронте).
  // Это снимает «страх отдельных коротких отрезков» — счётчик растёт
  // через весь день, включая обед и перерывы с авто-стопом по idle.
  const elapsedSeconds = computed(() => {
    const base = workedTodaySeconds.value || 0
    return base + activeSessionElapsedSeconds.value
  })

  const formattedElapsed = computed(() => {
    const s = elapsedSeconds.value
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const ss = s % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
  })

  function reset() {
    session.value = null
    trackWorkTime.value = false
    idleTimeoutMinutes.value = 30
    workedTodaySeconds.value = 0
    initialized.value = false
    stopTimers()
  }

  function markActivity() {
    lastActivityAt.value = serverNow()
  }

  async function fetchActive({ silent = false } = {}) {
    if (!silent) loading.value = true
    try {
      const data = await api.workday.getActive()
      session.value = data?.session || null
      trackWorkTime.value = !!data?.track_work_time
      idleTimeoutMinutes.value = Number(data?.idle_timeout_minutes) || 30
      // worked_today_seconds — закрытые сегодняшние (МСК). К нему
      // computed elapsedSeconds сам добавит live активную.
      workedTodaySeconds.value = Number(data?.worked_today_seconds) || 0
      initialized.value = true
      if (session.value) {
        // только что увидели активную — считаем это активностью
        markActivity()
      }
      return data
    } catch (e) {
      // 401 → пользователь не залогинен; молча игнорируем
      session.value = null
      initialized.value = true
      return null
    } finally {
      loading.value = false
    }
  }

  async function startDay({ note_start } = {}) {
    if (!trackWorkTime.value) return null
    const data = await api.workday.start({ note_start: note_start || null })
    session.value = data || null
    markActivity()
    return data
  }

  async function endDay({ reason = 'manual', note_end } = {}) {
    if (!session.value) return null
    const payload = { reason, note_end: note_end || null }
    if (reason === 'idle') {
      // lastActivityAt — уже серверное время в epoch ms; toISOString
      // выдаст UTC, что и нужно бэку.
      payload.ended_at = new Date(lastActivityAt.value).toISOString()
    }
    try {
      const data = await api.workday.end(payload)
      session.value = null
      // Подтянем свежий worked_today_seconds сразу — иначе следующий
      // старт дня покажет старую (заниженную) сумму до 60-секундного поллинга.
      fetchActive({ silent: true })
      return data
    } catch (e) {
      // Если уже закрыли с другой вкладки — синхронизируемся.
      await fetchActive({ silent: true })
      return null
    }
  }

  async function sendHeartbeat() {
    if (!session.value) return
    try {
      const data = await api.workday.heartbeat()
      // Если бэк сообщил что сессии нет (он сам закрыл по idle) — синк.
      if (!data?.session_id) {
        session.value = null
      }
    } catch (e) { /* noop — следующий тик попробует */ }
  }

  function stopTimers() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
    if (idleCheckTimer) { clearInterval(idleCheckTimer); idleCheckTimer = null }
    if (tickTimer) { clearInterval(tickTimer); tickTimer = null }
  }

  function startTimers() {
    stopTimers()
    // 1) Каждую секунду — обновляем nowTick (серверное время), чтобы счётчик тикал.
    tickTimer = setInterval(() => { nowTick.value = serverNow() }, 1000)

    // 2) Heartbeat каждую минуту, но только если была активность последние 30с.
    //    Всё сравнение в серверных мс — независимо от локальных часов.
    heartbeatTimer = setInterval(() => {
      if (!session.value) return
      if (document.hidden) return
      if (serverNow() - lastActivityAt.value > RECENT_ACTIVITY_WINDOW_MS) return
      sendHeartbeat()
    }, HEARTBEAT_MS)

    // 3) Проверка idle: если давно не было активности → авто-закрытие.
    idleCheckTimer = setInterval(async () => {
      if (!session.value) return
      const idleMs = idleTimeoutMinutes.value * 60_000
      if (serverNow() - lastActivityAt.value < idleMs) return
      // Закрываем — сервер пишет ended_at = lastActivityAt
      await endDay({ reason: 'idle' })
    }, IDLE_CHECK_MS)

    // 4) Периодически перетягиваем /active — на случай если сессию
    //    закрыли с другой вкладки/устройства или по серверной idle-страховке.
    pollTimer = setInterval(() => { fetchActive({ silent: true }) }, 60_000)
  }

  return {
    // state
    session,
    trackWorkTime,
    idleTimeoutMinutes,
    loading,
    initialized,
    lastActivityAt,
    nowTick,
    workedTodaySeconds,
    // computed
    isActive,
    showStartModal,
    elapsedSeconds,
    activeSessionElapsedSeconds,
    formattedElapsed,
    // actions
    reset,
    markActivity,
    fetchActive,
    startDay,
    endDay,
    sendHeartbeat,
    startTimers,
    stopTimers,
  }
})
