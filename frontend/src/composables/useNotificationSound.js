import { useUiPreferences } from './useUiPreferences'

/**
 * Звуковые уведомления — общий синтез + два независимых тумблера.
 *
 * Дизайн:
 *  - Звук — программный (Web Audio API), без mp3-файлов: меньше
 *    деплоя, корректнее iOS Safari (требует user-interaction перед
 *    AudioContext.resume() — мы вызываем play только после того, как
 *    юзер уже что-то нажал в приложении, так что allow).
 *  - Два независимых тумблера:
 *      prefs.notifications.soundEnabled          — для общего bell-ринга
 *      prefs.notifications.messengerSoundEnabled — для новых сообщений
 *    Юзер может оставить один из них.
 *  - Singleton AudioContext на вкладку — один объект на всё
 *    приложение, не плодим. SSR-safe.
 */

let _audioCtx = null
let _lastPlayedAt = 0
const MIN_GAP_MS = 250 // защита от спама (если N пушей пришли за тик)

function getAudioCtx() {
  if (typeof window === 'undefined') return null
  if (_audioCtx) return _audioCtx
  const Ctor = window.AudioContext || window.webkitAudioContext
  if (!Ctor) return null
  try {
    _audioCtx = new Ctor()
  } catch (e) {
    _audioCtx = null
  }
  return _audioCtx
}

/**
 * Двутоновый «ding»: 880 Hz (A5) → 1320 Hz (E6, чистая квинта).
 * Длительность ~250мс, плавный fade, громкость средняя (-20 dB).
 *
 * `tone` — 'high' (notification) / 'low' (messenger). Для разнообразия
 * между source'ами; обе фокусированно-короткие, чтобы не раздражать.
 */
function playDing(tone = 'high') {
  const ctx = getAudioCtx()
  if (!ctx) return
  try {
    // iOS / Chrome могут оставить ctx в 'suspended' до user gesture.
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {})
    }
    const now = ctx.currentTime
    const f1 = tone === 'low' ? 660 : 880  // E5 vs A5
    const f2 = tone === 'low' ? 990 : 1320 // B5 vs E6 (квинта)

    const osc1 = ctx.createOscillator()
    const gain1 = ctx.createGain()
    osc1.type = 'sine'
    osc1.frequency.setValueAtTime(f1, now)
    gain1.gain.setValueAtTime(0, now)
    gain1.gain.linearRampToValueAtTime(0.1, now + 0.01)
    gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.16)
    osc1.connect(gain1).connect(ctx.destination)
    osc1.start(now)
    osc1.stop(now + 0.17)

    const osc2 = ctx.createOscillator()
    const gain2 = ctx.createGain()
    osc2.type = 'sine'
    osc2.frequency.setValueAtTime(f2, now + 0.08)
    gain2.gain.setValueAtTime(0, now + 0.08)
    gain2.gain.linearRampToValueAtTime(0.08, now + 0.09)
    gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.25)
    osc2.connect(gain2).connect(ctx.destination)
    osc2.start(now + 0.08)
    osc2.stop(now + 0.26)
  } catch (e) {
    // глушим — звук не критичен, лучше тихо чем сломать UI.
  }
}

export function useNotificationSound() {
  const { prefs } = useUiPreferences()

  const _throttled = (fn) => {
    const t = Date.now()
    if (t - _lastPlayedAt < MIN_GAP_MS) return
    _lastPlayedAt = t
    fn()
  }

  /** Общие уведомления (bell в шапке, NotificationCenter). */
  const playNotificationDing = () => {
    if (!prefs.notifications?.soundEnabled) return
    _throttled(() => playDing('high'))
  }

  /** Новое сообщение в мессенджере (DM / group). */
  const playMessengerDing = () => {
    if (!prefs.notifications?.messengerSoundEnabled) return
    _throttled(() => playDing('low'))
  }

  return {
    playNotificationDing,
    playMessengerDing,
  }
}
