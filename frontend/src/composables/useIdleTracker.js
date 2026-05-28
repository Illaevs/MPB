import { onMounted, onBeforeUnmount } from 'vue'

/**
 * useIdleTracker — глобальный детектор активности пользователя.
 *
 * Слушает мышь, клавиатуру, скролл и visibilitychange. На каждом событии
 * вызывает переданный callback (с throttle, чтобы не дёргать его на
 * каждом мс). Используется workday store'ом для обновления
 * `lastActivityAt`, по которому решается «idle / не idle».
 *
 * События, которые не считаем активностью: фокус скрытой вкладки.
 *
 * Минимум зависимостей — самостоятельная функция, можно поставить
 * один раз в App.vue setup() и забыть.
 */
const THROTTLE_MS = 1000  // не чаще раза в секунду

export function useIdleTracker(onActivity) {
  let lastFired = 0

  function tick() {
    if (document.hidden) return
    const now = Date.now()
    if (now - lastFired < THROTTLE_MS) return
    lastFired = now
    try { onActivity?.() } catch (e) { /* noop */ }
  }

  function onVisibilityChange() {
    if (!document.hidden) {
      // Возвращение из фона — это сама по себе активность.
      lastFired = 0
      tick()
    }
  }

  const events = ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll']

  onMounted(() => {
    events.forEach((evt) => window.addEventListener(evt, tick, { passive: true, capture: true }))
    document.addEventListener('visibilitychange', onVisibilityChange)
    // первый «пинок» — пользователь только что открыл / залогинился
    tick()
  })

  onBeforeUnmount(() => {
    events.forEach((evt) => window.removeEventListener(evt, tick, { capture: true }))
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })
}
