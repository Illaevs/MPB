# Эксперимент: Glass dark panel для основной рабочей области

**Дата:** 2026-05
**Раздел:** `/projects` (Сделки)
**Статус:** откачен в основную ветку, сохранён здесь для будущего рассмотрения

---

## Контекст

Дизайн-референс от пользователя предложил для основной рабочей области:
- Полупрозрачную тёмную «page panel» вместо плоского `--color-bg`
- «Голую» таблицу без card-обёртки внутри панели
- Строки с границей-разделителем и большим вертикальным padding'ом
- Hover-only action кнопки в строках
- Крупный заголовок light-веса
- Status badge'и rounded-full с tonal-bg

Источник — Tailwind-prototype со стилем `bg-[#10131a]/80 backdrop-blur-md` (см. также Linear / Pipedrive / современные SaaS-CRM 2025).

Цель эксперимента — оценить, насколько такая визуальная подача меняет ощущение от центрального раздела CRM по сравнению с текущим solid-light SaaS-стилем.

---

## Что было реализовано

### Финальная версия (variant C — полу-tonal)

Применялась к `<Projects.vue>` через флаг-класс `projects-view--glass` на корневом `<div>`. CSS жил отдельным блоком в конце `<style scoped>` файла. Параллельно в `App.vue` стоял `:has()`-override, убирающий padding `.content-body` чтобы панель упиралась в chrome.

**Ключевые токены:**

| Что | Значение |
|---|---|
| Background панели | `rgba(15, 23, 42, 0.55)` |
| Backdrop-filter | `blur(20px) saturate(150%)` |
| Padding панели | `32px` со всех сторон |
| Title font | `1.875rem`, weight `300`, white |
| Inputs / chips / view-toggle / clear bg | `rgba(15, 23, 42, 0.65)` (плотнее панели для собственной читаемости) |
| Inputs / chips hover bg | `rgba(30, 41, 59, 0.75)` |
| Inputs border | `rgba(255, 255, 255, 0.10)` |
| Table thead | bg transparent, border-bottom `rgba(255, 255, 255, 0.10)`, text `#94a3b8` 11px uppercase tracking 0.06em |
| Table tbody row | bg transparent, border-bottom `rgba(255, 255, 255, 0.08)` |
| Table td padding | `24px` (py-6) |
| Td text | `#cbd5e1` (`#94a3b8` для muted) |
| Hover row bg | `rgba(255, 255, 255, 0.04)` (применять к `td`, не `tr` — иначе глобальный `.table tbody tr:hover td` перебивает) |
| Deal name link | `#ffffff` weight 600, hover `#60a5fa` |
| Status badge | `rgba(16, 185, 129, 0.10)` bg, `#34d399` text, border `rgba(16, 185, 129, 0.25)`, `rounded-full` |
| Health chip (orange) | `rgba(249, 115, 22, 0.10)` bg, border `rgba(249, 115, 22, 0.25)`, text `#fb923c` |
| Create button | solid `#2563eb`, hover `#1d4ed8` |
| Row actions | `opacity: 0` → `1` on row hover |

### Полный CSS

```css
/* В <style scoped> Projects.vue, в самом конце */

.projects-view--glass {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 32px;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  color: #cbd5e1;
}

.projects-view--glass .list-card {
  background: transparent;
  border: none;
  box-shadow: none;
  border-radius: 0;
  overflow: visible;
  margin: 0;
}

.projects-view--glass .list-card__toolbar {
  background: transparent;
  border-bottom: none;
  padding: 0;
  margin-bottom: 24px;
}

.projects-view--glass .list-card__body {
  padding: 0;
}

.projects-view--glass .projects-toolbar-compact__title h1 {
  font-size: 1.875rem;
  font-weight: 300;
  letter-spacing: -0.02em;
  color: #ffffff;
}

.projects-view--glass .projects-toolbar-compact__count {
  background: rgba(59, 130, 246, 0.20);
  color: #60a5fa;
  border: none;
  padding: 4px 10px;
  border-radius: 9999px;
}

.projects-view--glass .projects-toolbar-compact__search,
.projects-view--glass .projects-toolbar-compact__field {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 6px;
  height: 36px;
  color: #cbd5e1;
}

.projects-view--glass .projects-toolbar-compact__search input,
.projects-view--glass .projects-toolbar-compact__field .form-control {
  color: #e2e8f0;
}

.projects-view--glass .projects-toolbar-compact__search input::placeholder,
.projects-view--glass .projects-toolbar-compact__field .form-control::placeholder {
  color: #94a3b8;
}

.projects-view--glass .projects-toolbar-compact__search i {
  color: #94a3b8;
}

.projects-view--glass .projects-toolbar-compact__field span {
  color: #94a3b8;
  font-weight: 400;
  font-size: 13px;
}

.projects-view--glass .projects-toolbar-compact__view {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 6px;
  padding: 4px;
  height: 36px;
}

.projects-view--glass .projects-toolbar-compact__view-btn {
  height: 28px;
  padding: 0 14px;
  color: #94a3b8;
  background: transparent;
  border-radius: 4px;
}

.projects-view--glass .projects-toolbar-compact__view-btn--active {
  background: rgba(255, 255, 255, 0.10);
  color: #ffffff;
}

.projects-view--glass .projects-toolbar-compact__clear {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.10);
  color: #cbd5e1;
  height: 36px;
  border-radius: 6px;
  padding: 0 14px;
}

.projects-view--glass .projects-toolbar-compact__clear:hover {
  background: rgba(30, 41, 59, 0.75);
}

.projects-view--glass .projects-toolbar-compact__create {
  background: #2563eb;
  color: #ffffff;
  border-radius: 6px;
  height: 36px;
  padding: 0 16px;
  border: none;
  font-weight: 500;
}

.projects-view--glass .projects-toolbar-compact__create:hover {
  background: #1d4ed8;
}

.projects-view--glass .ui-chip-filter__btn {
  background: rgba(15, 23, 42, 0.65);
  border-color: rgba(255, 255, 255, 0.10);
  color: #cbd5e1;
  height: 36px;
  border-radius: 6px;
}

.projects-view--glass .ui-chip-filter__btn:hover:not(:disabled) {
  background: rgba(30, 41, 59, 0.75);
}

.projects-view--glass .ui-chip-filter__btn.is-empty .ui-chip-filter__icon {
  color: #94a3b8;
}

.projects-view--glass .table-container.card {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.projects-view--glass .table {
  width: 100%;
  border-collapse: collapse;
}

.projects-view--glass .table thead th {
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
  color: #94a3b8;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 16px 24px;
  text-align: left;
}

.projects-view--glass .table tbody tr {
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.projects-view--glass .table tbody td {
  border: none;
  padding: 24px;
  color: #cbd5e1;
  vertical-align: middle;
  font-size: 14px;
  background-color: transparent;
  transition: background-color var(--dur-fast) ease;
}

/* Override глобального `.table tbody tr:hover td { background: var(--color-surface-2) }`
   на td, не на tr. */
.projects-view--glass .table tbody tr:hover td {
  background-color: rgba(255, 255, 255, 0.04);
}

.projects-view--glass .table tbody td.text-muted {
  color: #94a3b8;
}

.projects-view--glass .table tbody tr a[href^="/projects/"] {
  color: #ffffff !important;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
}

.projects-view--glass .table tbody tr a[href^="/projects/"]:hover {
  color: #60a5fa !important;
}

.projects-view--glass .project-health-count {
  background: rgba(249, 115, 22, 0.10);
  border-color: rgba(249, 115, 22, 0.25);
  color: #fb923c;
  border-radius: 4px;
}

.projects-view--glass .project-health-count--error {
  background: rgba(239, 68, 68, 0.10);
  border-color: rgba(239, 68, 68, 0.25);
  color: #f87171;
}

.projects-view--glass .table tbody .badge {
  background: rgba(16, 185, 129, 0.10);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 9999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  box-shadow: none;
}

.projects-view--glass .table tbody td[style*="monospace"] {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: #e2e8f0;
  font-weight: 500;
}

.projects-view--glass .table tbody td:last-child > .d-flex {
  opacity: 0;
  transition: opacity var(--dur-fast) ease;
}

.projects-view--glass .table tbody tr:hover td:last-child > .d-flex {
  opacity: 1;
}

.projects-view--glass .table tbody .btn.btn-sm {
  background: transparent !important;
  border: none !important;
  color: #94a3b8 !important;
  padding: 4px 6px;
  font-size: 14px;
}

.projects-view--glass .table tbody .btn.btn-outline-primary:hover {
  color: #60a5fa !important;
}

.projects-view--glass .table tbody .btn.btn-danger:hover {
  color: #f87171 !important;
}

.projects-view--glass .table-container > .d-flex.border-top {
  border-top-color: rgba(255, 255, 255, 0.08) !important;
  color: #94a3b8;
}

.projects-view--glass .table-container .btn.btn-outline-secondary {
  background: rgba(15, 23, 42, 0.65);
  border-color: rgba(255, 255, 255, 0.10);
  color: #cbd5e1;
}
```

### Override в App.vue (`<style scoped>` рядом с `.content-body`)

```css
/* Чтобы glass-панель прижалась к chrome без полоски wallpaper по краям. */
.content-body:has(.projects-view--glass) {
  padding: 0;
}
```

### Template-флаг в Projects.vue

```html
<div class="projects-view projects-view--glass">
  ...
</div>
```

---

## Чтобы re-enable

1. На корневом `<div>` в `frontend/src/views/Projects.vue` добавить класс `projects-view--glass`.
2. Вставить CSS-блок выше в конец `<style scoped>` секции `Projects.vue`.
3. Вставить `:has()` правило в `<style scoped>` `App.vue` рядом с `.content-body`.

---

## Наблюдения / открытые вопросы

**Плюсы:**
- Wallpaper-фон становится частью продукта, а не декорацией под chrome.
- Контраст title + light bg делает информацию более читаемой при беглом скане.
- Hover-only кнопки строк дают чистый scan-mode (как в Linear).
- 24px row padding + 1.875rem title — air'у в интерфейсе, ощущение «продуктового» SaaS, не «1С».

**Минусы / вопросы:**
- На wallpaper'ах с высоким контрастом (снег + огни) текст местами плывёт — даже с `blur(20px)`.
- Decision-point: применять ли ко всем list-view или только к флагманскому экрану (сделки/задачи).
- Theme-toggle (light/dark) в этой системе теряет смысл для рабочей зоны — она всегда тёмная. Нужно либо сделать light-вариант панели, либо явно объяснить дизайн-решение «workspace всегда dark, chrome переключается».
- Filter chips (`UiChipFilter`) пришлось перекрашивать локально — общий компонент рассчитан на light surface. Если стиль войдёт в продакшен — переделать `UiChipFilter` под токены, а не hardcode-цвета.
- Mobile (375-768px) не прорабатывался — на узких экранах padding 32px съест половину viewport.

**Что подумать дальше:**
- Расширить ли на ProjectDetail / Tasks / Contracts? (центральные разделы CRM)
- Какой visual язык для модалок и форм поверх такой панели?
- Кастомизация под пользователя — пусть выберет «классический» / «glass» / «density» в settings?
