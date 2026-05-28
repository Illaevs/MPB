/**
 * v-modal-close="closeFn"
 *
 * Безопасная замена `@click.self="closeFn"` на overlay-элементе модалки.
 *
 * ПОЧЕМУ нельзя `@click.self`.
 * Пользователь зажимает mouse внутри модалки (textarea/input — начинает
 * выделение), тащит мышь наружу за пределы модалки на overlay, отпускает
 * там mouseup. Браузер генерирует `click` event с `target === overlay`
 * (он же `currentTarget`) → `.self` модификатор проходит → модалка
 * закрывается, выделенный текст и всё что напечатано теряются. Очень
 * раздражает.
 *
 * РЕШЕНИЕ. Запоминаем target первоначального mousedown. Закрываем
 * модалку ТОЛЬКО если оба события — mousedown и click — произошли
 * непосредственно на overlay-элементе. Если mousedown был внутри
 * (на input/textarea/кнопке) — click игнорируем.
 *
 * Использование:
 *   <div class="modal-overlay" v-modal-close="closeFn">…</div>
 *
 * Можно передавать функцию закрытия напрямую (`closeModal`) или
 * объект-обработчик. Если value не функция — директива no-op.
 */

const STATE = Symbol('modalCloseDirective')

function isElementDescendant(parent, child) {
  let cur = child
  while (cur) {
    if (cur === parent) return true
    cur = cur.parentNode
  }
  return false
}

export default {
  mounted(el, binding) {
    const state = {
      // target первоначального mousedown в области overlay
      downTarget: null,
      // последний binding.value — обновляется в `updated`
      handler: typeof binding.value === 'function' ? binding.value : null,
    }
    el[STATE] = state

    state.onMouseDown = (event) => {
      // Сохраняем target ИМЕННО в момент mousedown — если он === el,
      // значит палец был на пустой области overlay; если internal — на
      // содержимом модалки, тогда блокируем закрытие.
      state.downTarget = event.target
    }
    state.onClick = (event) => {
      const fn = state.handler
      try {
        if (!fn) return
        // Safety-net #1: если в момент клика есть АКТИВНОЕ выделение
        // текста — это закрытие drag-selection. Никогда не закрываем,
        // независимо от target'ов. Это самая частая жалоба
        // («выделил в textarea — отпустил снаружи — модалка закрылась»).
        const sel = window.getSelection && window.getSelection()
        if (sel && String(sel).length > 0) return
        // Safety-net #2: если на overlay нажали мышь (mousedown был
        // на child — input/textarea/кнопка) — игнорируем click даже
        // если он целится в overlay.
        if (state.downTarget !== el) return
        // Strict mode: только если click target — сам overlay.
        if (event.target !== el) return
        fn(event)
      } finally {
        state.downTarget = null
      }
    }
    // Доп. safety: если mouseup был ВНЕ overlay (например, drag завершился
    // вне браузера) — сбрасываем флаг, чтобы не закрывать на следующем
    // обычном click внутри модалки случайно.
    state.onMouseUp = (event) => {
      if (!isElementDescendant(el, event.target)) {
        state.downTarget = null
      }
    }

    el.addEventListener('mousedown', state.onMouseDown)
    el.addEventListener('click', state.onClick)
    window.addEventListener('mouseup', state.onMouseUp, true)
  },

  updated(el, binding) {
    const state = el[STATE]
    if (!state) return
    state.handler = typeof binding.value === 'function' ? binding.value : null
  },

  beforeUnmount(el) {
    const state = el[STATE]
    if (!state) return
    el.removeEventListener('mousedown', state.onMouseDown)
    el.removeEventListener('click', state.onClick)
    window.removeEventListener('mouseup', state.onMouseUp, true)
    delete el[STATE]
  },
}
