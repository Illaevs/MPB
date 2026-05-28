<template>
  <div class="tasks-view h-100 d-flex flex-column p-3">
    <TasksToolbar :state="state" />

    <TaskBoards :state="state" />

    <TaskDrawer :state="state" />
    <TaskModals :state="state" />
  </div>
</template>

<script>
/**
 * Tasks view (decomposed shell).
 *
 * Previously a monolithic ~8636 LOC file containing toolbar, list/kanban/matrix,
 * auctions, penalty rules, editor and a dozen modals. Now a thin composition shell.
 *
 * Shared state and all API calls live in
 * `views/tasks/composables/useTasksState.js`.
 * Every former direct `axios.*` call has been migrated to `api.tasks.*`
 * (services/api/tasks.js). The only remaining `axios`-style direct call is the
 * generic deals listing (`/api/v1/deals/`) handled via `_client.get`, because
 * the deals endpoint does not belong to the tasks domain.
 *
 * Styling: previously had a single huge `<style scoped>` block. Vue scoped CSS
 * does NOT cascade into child components, so the block has been switched to
 * non-scoped (mirroring the existing dark-theme style block which was already
 * non-scoped). Class names are domain-prefixed (`.task-*`, `.task-sheet__*`,
 * `.task-kanban-*`, `.task-matrix-*`, `.rules-*`, `.auction-*`, `.bulk-bar`)
 * so collisions are unlikely.
 */
import TasksToolbar from './tasks/parts/TasksToolbar.vue'
import TaskBoards from './tasks/parts/TaskBoards.vue'
import TaskDrawer from './tasks/parts/TaskDrawer.vue'
import TaskModals from './tasks/parts/TaskModals.vue'
import { useTasksState } from './tasks/composables/useTasksState'

export default {
  name: 'Tasks',
  components: {
    TasksToolbar, TaskBoards,
    TaskDrawer, TaskModals
  },
  setup() {
    const state = useTasksState()
    return { state }
  }
}
</script>
<style>
.fw-500 { font-weight: 500; }
.fw-600 { font-weight: 600; }
.sticky-header th { position: sticky; top: 0; background-color: var(--md-sys-color-surface); z-index: 1; }

.task-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  font-weight: 700;
  flex-shrink: 0;
}

.task-avatar--sm {
  width: 36px;
  height: 36px;
  font-size: 0.92rem;
}

.task-avatar--md {
  width: 34px;
  height: 34px;
  font-size: 0.88rem;
}

.task-avatar--xl {
  width: 72px;
  height: 72px;
  font-size: 1.45rem;
}

.task-avatar--image {
  background: #e5edf8;
}

.task-avatar__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.task-avatar__fallback {
  line-height: 1;
}

.task-avatar__status {
  position: absolute;
  right: 4px;
  bottom: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
}

.task-avatar__status.is-active {
  background: #30c873;
}

.task-avatar__status.is-inactive {
  background: #eb5757;
}

.task-person {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.task-person__body {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.task-person__body > span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tasks-view {
  gap: 12px;
}

.task-module-topbar,
.task-module-main {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(216, 224, 240, 0.92);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
}

.task-module-topbar {
  padding: 18px 20px;
  border-radius: 24px;
}

.task-module-topbar__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}

.task-module-topbar__title-group {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.task-module-topbar__title-group h1 {
  margin: 0;
  color: #0a1629;
  font-size: 1.7rem;
  line-height: 1.1;
}

.task-module-topbar__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.task-segmented {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 16px;
  background: #f3f5f8;
  border: 1px solid rgba(228, 228, 228, 0.95);
}

.task-segmented__button {
  min-height: 42px;
  padding: 0 14px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #5f6b7c;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.task-segmented__button--active {
  background: #fff;
  color: #0a1629;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.task-toolbar-btn {
  position: relative;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid rgba(10, 22, 41, 0.12);
  border-radius: 14px;
  background: #fff;
  color: #0a1629;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-weight: 700;
}

.task-toolbar-btn__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: #0a1629;
  color: #fff;
  font-size: 0.72rem;
}

.task-toolbar-icon-btn {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(10, 22, 41, 0.08);
  border-radius: 12px;
  background: #fff;
  color: #5f6b7c;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.task-sort-box,
.task-page-size-box {
  min-height: 42px;
  border: 1px solid rgba(10, 22, 41, 0.1);
  border-radius: 14px;
  background: #fff;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
}

.task-sort-box {
  min-width: 230px;
}

.task-sort-box__select,
.task-page-size-box__select {
  border: none;
  background: transparent;
  color: #0a1629;
  font-weight: 700;
  outline: none;
}

.task-sort-box__select {
  min-width: 0;
  flex: 1 1 auto;
}

.task-sort-box__dir {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 10px;
  background: #f3f5f8;
  color: #5f6b7c;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.task-module-topbar__create-btn {
  min-height: 44px;
  padding: 0 18px;
  border-radius: 14px;
  box-shadow: 0 12px 28px rgba(63, 140, 255, 0.22);
}

.task-module-topbar__meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.06));
}
.task-module-topbar__meta .task-module-topbar__filters { margin-right: auto; }

.task-module-topbar__filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.task-module-topbar__meta-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.task-module-topbar__pagination {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #5f6b7c;
  font-weight: 700;
}

.task-module-topbar__count,
.task-module-topbar__hint,
.task-page-size-box span {
  color: #7d8592;
  font-size: 0.84rem;
  font-weight: 700;
}

.task-filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f6f8fb;
  border: 1px solid rgba(216, 224, 240, 0.92);
  color: #445065;
  font-size: 0.82rem;
  font-weight: 700;
}

.task-filter-pill--clear {
  background: #fff;
  color: #0a1629;
  border-color: rgba(10, 22, 41, 0.12);
}

.task-module-main {
  /* Only round the bottom — the top is butted against the toolbar
     (which has `border-radius: var(--radius-lg) var(--radius-lg) 0 0`).
     Rounding the top would crop the column-header tint at the corners. */
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  border-top: 0;
  /* Override global .card { padding: var(--space-4); margin-bottom: ... }
     so the column-header band sits flush to the card edges. */
  padding: 0;
  margin: 0;
}

.task-module-main__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 22px 16px;
  border-bottom: 1px solid rgba(228, 228, 228, 0.95);
}

.task-module-main__headline h2 {
  margin: 0;
  color: #0a1629;
  font-size: 1.25rem;
  font-weight: 700;
}

.task-module-main__headline p {
  margin: 6px 0 0;
  color: #7d8592;
  line-height: 1.55;
}

.task-module-main__summary {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  color: #7d8592;
  font-size: 0.84rem;
  font-weight: 700;
  text-align: right;
}

.task-module-main__summary span:first-child {
  color: #0a1629;
  font-size: 1rem;
}

.task-filters-modal {
  width: min(560px, calc(100vw - 24px));
  border-radius: 24px;
  background: #f8fbff;
  border: 1px solid rgba(216, 224, 240, 0.92);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}

.task-filters-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 22px 22px 14px;
  border-bottom: 1px solid rgba(228, 228, 228, 0.95);
}

.task-filters-modal__eyebrow {
  display: inline-flex;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(63, 140, 255, 0.1);
  color: #3f8cff;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.task-filters-modal__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 22px 12px;
}

.task-filters-modal__footer {
  padding: 0 22px 22px;
  border-top: none;
}

.task-modal-overlay {
  padding: 18px;
}

.task-modal {
  width: min(1240px, calc(100vw - 36px));
  max-height: min(92vh, 980px);
  background:
    radial-gradient(circle at top left, rgba(63, 140, 255, 0.12), transparent 24%),
    #f4f8fc;
  border: 1px solid rgba(216, 224, 240, 0.92);
  border-radius: 28px;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.22);
  overflow: hidden;
}

.task-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 26px 28px 18px;
  border-bottom: 1px solid rgba(216, 224, 240, 0.92);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(14px);
}

.task-modal__heading {
  min-width: 0;
}

.task-modal__eyebrow {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(63, 140, 255, 0.1);
  color: #3f8cff;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.task-modal__heading h4 {
  margin: 0;
  font-size: 1.7rem;
  line-height: 1.15;
  color: #0a1629;
}

.task-modal__heading p {
  margin: 10px 0 0;
  max-width: 680px;
  color: #6f7d91;
  line-height: 1.6;
}

.task-modal__header-side {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-shrink: 0;
}

.task-modal__header-chips {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.task-modal__close {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.task-modal-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 0;
  min-height: 0;
  align-items: stretch;
}

.task-modal-form {
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 24px;
  gap: 18px;
}

.task-modal-form__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.task-modal-panel {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(216, 224, 240, 0.92);
  border-radius: 24px;
  padding: 22px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.05);
}

.task-modal-panel--lead {
  box-shadow: 0 20px 40px rgba(63, 140, 255, 0.08);
}

.task-modal-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.task-modal-panel__label {
  display: block;
  margin-bottom: 6px;
  color: #7d8592;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.task-modal-panel__head h5 {
  margin: 0;
  color: #0a1629;
  font-size: 1.05rem;
  font-weight: 700;
}

.task-modal-panel__caption {
  color: #7d8592;
  font-size: 0.84rem;
  font-weight: 600;
  text-align: right;
}

.task-modal-field label,
.task-modal-panel .form-group label {
  display: block;
  margin-bottom: 8px;
  color: #7d8592;
  font-size: 0.84rem;
  font-weight: 700;
}

.task-modal-title-input {
  min-height: 56px;
  font-size: 1.18rem;
  font-weight: 700;
  border-radius: 16px;
}

.task-modal-textarea {
  min-height: 152px;
  resize: vertical;
  border-radius: 18px;
}

.task-modal-grid-fields {
  display: grid;
  gap: 16px;
}

.task-modal-grid-fields + .task-modal-grid-fields {
  margin-top: 16px;
}

.task-modal-grid-fields--1 {
  grid-template-columns: minmax(0, 1fr);
}

.task-modal-grid-fields--2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.task-modal-grid-fields--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.task-modal-note {
  border: none;
  border-radius: 18px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

.task-modal-panel--summary {
  background: linear-gradient(180deg, rgba(63, 140, 255, 0.08), rgba(255, 255, 255, 0.94));
}

.task-modal-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.task-modal-summary-item {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(216, 224, 240, 0.92);
}

.task-modal-summary-item span {
  display: block;
  margin-bottom: 8px;
  color: #7d8592;
  font-size: 0.78rem;
  font-weight: 700;
}

.task-modal-summary-item strong {
  color: #0a1629;
  font-size: 1rem;
}

.task-modal__footer {
  padding: 0;
  margin-top: 0;
  border-top: none;
}

.task-modal__submit {
  min-width: 148px;
  border-radius: 14px;
  box-shadow: 0 12px 24px rgba(63, 140, 255, 0.2);
}

.task-modal-side {
  min-height: 0;
  padding: 24px 24px 24px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-modal-side-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(216, 224, 240, 0.92);
  border-radius: 24px;
  padding: 20px;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
}

.task-modal-side-card--hero {
  text-align: center;
}

.task-modal-side-card--hero .task-avatar {
  margin: 0 auto 16px;
}

.task-modal-side-card--hero h5 {
  margin: 0;
  color: #0a1629;
  font-size: 1.05rem;
  font-weight: 700;
}

.task-modal-side-card--hero p {
  margin: 8px 0 0;
  color: #7d8592;
  line-height: 1.5;
}

.task-modal-side-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.task-modal-side-card__head h6 {
  margin: 0;
  color: #0a1629;
  font-size: 0.98rem;
  font-weight: 700;
}

.task-modal-side-card__head span {
  color: #7d8592;
  font-size: 0.78rem;
  line-height: 1.4;
}

.task-modal-side__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-modal-side__list > div {
  padding: 12px 14px;
  border-radius: 16px;
  background: #f7faff;
  border: 1px solid rgba(216, 224, 240, 0.78);
}

.task-modal-side__list span {
  display: block;
  margin-bottom: 6px;
  color: #7d8592;
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.task-modal-side__list strong {
  color: #0a1629;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.task-modal-side__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  justify-content: center;
}

.task-modal-side__pill {
  display: inline-flex;
  align-items: center;
  padding: 7px 10px;
  border-radius: 999px;
  background: #eef4fb;
  color: #5f6f87;
  font-size: 0.78rem;
  font-weight: 700;
  line-height: 1;
}

.task-modal-side-card--chat {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: 260px;
}

.task-modal-side__chat {
  min-height: 0;
  flex: 1 1 auto;
  display: flex;
}

.task-modal-side__chat .task-chat {
  flex: 1;
  min-height: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.task-modal-side__placeholder {
  min-height: 180px;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  background: #f7faff;
  border: 1px dashed rgba(125, 133, 146, 0.34);
  color: #7d8592;
  text-align: center;
}

.task-modal-side__placeholder i {
  font-size: 1.5rem;
  color: #3f8cff;
}

/* Tasks redesign: close to 512/513 reference */
.tasks-view {
  gap: 0;
  padding: 0 !important;
  min-height: 0;
  font-family: Inter, "Segoe UI", sans-serif;
  color: #000;
}

.task-module-topbar,
.task-module-main {
  background: #fff;
  border: 1px solid #e4e4e4;
  box-shadow: none;
}

.task-module-topbar {
  border-radius: 12px 12px 0 0;
  padding: 0 24px;
}

.task-module-main {
  border-top: none;
  border-radius: 0 0 12px 12px;
}

.task-module-topbar__row {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.task-module-topbar__title-group,
.task-module-topbar__actions {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.task-toolbar-inline-filters {
  display: inline-flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.task-toolbar-select {
  min-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-toolbar-select--wide {
  min-width: 260px;
}

.task-toolbar-select span {
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
}

.task-toolbar-select__control {
  min-height: 38px;
  padding: 0 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #fff;
  color: #000;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
  outline: none;
  box-shadow: none;
}

.task-module-topbar__title-group h1 {
  margin: 0;
  color: #000;
  font-size: 24px;
  line-height: 1.2;
  font-weight: 500;
}

.task-segmented {
  display: inline-flex;
  align-items: center;
  gap: 0;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.task-segmented__button {
  min-height: 72px;
  padding: 0 16px;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  background: transparent;
  color: #727272;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
  transition: color 0.18s ease, border-color 0.18s ease;
  box-shadow: none;
}

.task-segmented__button--active {
  color: #000;
  background: transparent;
  border-bottom-color: #000;
  box-shadow: none;
}

.task-toolbar-btn,
.task-sort-box,
.task-page-size-box {
  min-height: 38px;
  padding: 0 12px;
  border: 1px solid #000;
  border-radius: 4px;
  background: #fff;
  color: #000;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
}

.task-toolbar-btn__badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #000;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.task-sort-box {
  min-width: 184px;
  gap: 10px;
}

.task-sort-box__select,
.task-page-size-box__select {
  min-width: 0;
  border: none;
  background: transparent;
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
  outline: none;
}

.task-sort-box__select {
  flex: 1 1 auto;
}

.task-sort-box__dir {
  width: 18px;
  height: 18px;
  border: none;
  border-left: 1px solid #e4e4e4;
  border-radius: 0;
  background: transparent;
  color: #000;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding-left: 10px;
}

.task-toolbar-icon-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  background: #f2f2f2;
  color: #727272;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.task-module-topbar__create-btn {
  min-height: 38px;
  padding: 0 16px;
  border-radius: 4px;
  border: 1px solid #000;
  background: #000;
  color: #fff;
  box-shadow: none;
  font-size: 14px;
  font-weight: 500;
}

.task-module-topbar__create-btn:hover,
.task-module-topbar__create-btn:focus {
  background: #000;
  border-color: #000;
  color: #fff;
}

.task-module-topbar__meta {
  min-height: 56px;
  margin-top: 0;
  padding: 10px 0 16px;
  border-top: 1px solid #e4e4e4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.task-module-topbar__filters,
.task-module-topbar__meta-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.task-module-topbar__pagination {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
}

.task-page-size-box {
  border-color: #e4e4e4;
}

.task-page-size-box span,
.task-module-topbar__count,
.task-module-topbar__hint {
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
}

.task-filter-pill {
  min-height: 30px;
  padding: 0 10px;
  border-radius: 4px;
  border: 1px solid #e4e4e4;
  background: #f7f7f7;
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
}

.task-filter-pill--clear {
  background: #fff;
  border-color: #000;
  color: #000;
}

.task-list-container {
  min-height: 0;
  background: #fff;
}

.task-list-shell {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-list-line {
  display: grid;
  grid-template-columns: minmax(280px, 2.4fr) 110px minmax(160px, 1.2fr) minmax(120px, 1fr) minmax(180px, 1.4fr) 130px;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #e4e4e4;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.task-list-line:hover {
  background: #fcfcfc;
  border-color: #d9d9d9;
}

.task-list-line--completed {
  background: #f3fbf5;
  border-color: #c7e4cc;
}

.task-list-line--completed:hover {
  background: #edf8ef;
  border-color: #b4d9bb;
}

.task-list-line--cancelled {
  background: #fff4f4;
  border-color: #efc8c8;
}

.task-list-line--cancelled:hover {
  background: #ffeded;
  border-color: #e6b4b4;
}

.task-list-line--deferred {
  background: #f4f4f4;
  border-color: #d8d8d8;
}

.task-list-line--deferred:hover {
  background: #ededed;
  border-color: #cdcdcd;
}

.task-list-line__lead {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 0;
}

.task-list-line__checkbox {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border: 1px solid #afafaf;
  border-radius: 4px;
  background: #fff;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
}

.task-list-line__checkbox--done {
  border-color: #000;
  background: #000;
}

.task-list-line__title-wrap {
  min-width: 0;
}

.task-list-line__title-wrap h3 {
  margin: 0;
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
  /* word-break — дополнительно к overflow-wrap, чтобы переноситься
     даже на одно длинное «слово» (URL, кириллица без пробелов).
     line-clamp: 3 — не давать высоте карточки расти бесконечно
     при title 200 символов (~140-150 символов влезает в 3 строки). */
  overflow-wrap: anywhere;
  word-break: break-word;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

.task-list-line__title-wrap p {
  margin: 4px 0 0;
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.task-list-line__cell {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-list-line__cell > span {
  color: #a0a0a0;
  font-size: 12px;
  font-weight: 400;
  line-height: 18px;
}

.task-list-line__cell > strong {
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
  overflow-wrap: anywhere;
}

.task-list-line__cell--labels {
  flex-direction: row;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.task-list-line__cell--assignee {
  justify-content: center;
}

.task-list-line__tail {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
}

.task-list-line__stats {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
  white-space: nowrap;
}

.task-list-line__stats span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.task-list-line__actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.task-list-line__actions .btn-icon {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background: #f2f2f2;
}

.task-person__body > span:first-child {
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
}

.task-person__body > span:last-child {
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
}

.task-list-container--kanban {
  padding: 24px;
  background: #fff;
}

.task-kanban-board {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  min-width: max-content;
}

.task-kanban-column {
  width: 360px;
  min-height: 100%;
  /* Убрали padding-top, чтобы sticky-header мог прилипать к верху
     scroll-области без отступа сверху (top:0 относительно overflow-auto
     родителя `.task-list-container`). Padding возвращён внутри header
     через padding-top, визуальный отступ сохранён. */
  padding: 0 20px 20px;
  background: #fff;
  border: 1px solid #e4e4e4;
  border-radius: 8px;
  box-shadow: none;
  transition: border-color 0.18s ease, background 0.18s ease;
  /* flex-direction column — обязательно для того, чтобы `.task-kanban-column__list`
     с flex: 1 растягивался на всю оставшуюся высоту колонки и drop-zone
     накрывал пустое место под карточками. */
  display: flex;
  flex-direction: column;
}

.task-kanban-column--over {
  /* Раньше менялся весь border + background — выглядело как «столбец
     выделен», пользователь воспринимал колонку как сам перетаскиваемый
     объект. Делаем тоньше: лёгкая «подсветка» внутреннего фона
     `.task-kanban-column__list` через CSS-переменную; рамка не трогается. */
  border-color: #e4e4e4;
  background: #fff;
  transform: none;
  box-shadow: none;
}
.task-kanban-column--over .task-kanban-column__list {
  background: rgba(33, 150, 243, 0.06);
  outline: 2px dashed rgba(33, 150, 243, 0.45);
  outline-offset: -4px;
  border-radius: 8px;
}

.task-kanban-column__header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
  /* Sticky-header: при скролле длинного списка задач название колонки
     остаётся видимым у верха scroll-области (.task-list-container).
     `top: 0` — прилипает к верху overflow-auto родителя. padding-top
     возвращает визуальный отступ, который сняли с `.task-kanban-column`.
     `background: #fff` нужен, иначе карточки задач просвечивают сквозь
     прилипший header при скролле вниз. */
  position: sticky;
  top: 0;
  z-index: 3;
  background: #fff;
  padding-top: 20px;
  padding-bottom: 12px;
}

.task-kanban-column__title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-kanban-column__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--task-kanban-accent);
  box-shadow: none;
}

.task-kanban-column__title-wrap h3 {
  margin: 0;
  color: #000;
  font-size: 20px;
  font-weight: 500;
  line-height: 24px;
}

.task-kanban-column__title-wrap p {
  margin: 0;
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
}

.task-kanban-column__create {
  min-height: 40px;
  border: none;
  border-radius: 4px;
  background: #f2f2f2;
  color: #000;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
}

.task-kanban-column__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  /* Drop-zone — на всю оставшуюся высоту колонки, не только на высоту
     карточек. Раньше при 1-2 задачах под списком пустое место было
     «мёртвым» — задача роняется только в зону самих карточек. */
  flex: 1 1 auto;
  min-height: 240px;
  padding: 4px 0 8px;
  transition: background var(--dur-fast) ease, outline-color var(--dur-fast) ease;
}

.task-kanban-column__empty {
  min-height: 170px;
  padding: 20px;
  border: 1px dashed #d2d2d2;
  border-radius: 4px;
  background: #fafafa;
  color: #727272;
  font-size: 14px;
  line-height: 21px;
}

.task-kanban-card {
  padding: 18px;
  border: 1px solid #e4e4e4;
  border-radius: 4px;
  background: #fff;
  box-shadow: none;
  cursor: pointer;
}

.task-kanban-card:hover {
  transform: none;
  border-color: #d0d0d0;
  box-shadow: none;
}

.task-kanban-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.task-kanban-chip {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
}

.task-kanban-chip--category {
  background: #fbf4ec;
  color: #d28e3d;
}

.task-kanban-chip--low {
  background: #edf5ef;
  color: #4b9967;
}

.task-kanban-chip--normal {
  background: #edf2fe;
  color: #4976f4;
}

.task-kanban-chip--high {
  background: #f7f7e8;
  color: #b1ab1d;
}

.task-kanban-chip--urgent {
  background: #f7eded;
  color: #af4b4b;
}

.task-kanban-chip--auction {
  background: #f4edf7;
  color: #954baf;
}

.task-kanban-card__title-row {
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.task-kanban-card__title-row h4 {
  margin: 0;
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
  overflow-wrap: anywhere;
}

.task-kanban-card__project,
.task-kanban-card__description,
.task-kanban-card__meta span,
.task-kanban-card__assignee span {
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
}

.task-kanban-card__description {
  margin: 0 0 16px;
  -webkit-line-clamp: 2;
}

.task-kanban-card__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
  margin-bottom: 16px;
}

.task-kanban-card__meta strong,
.task-kanban-card__assignee strong {
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
}

.task-kanban-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-kanban-card__actions .btn-icon {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background: #f2f2f2;
}

.task-filters-modal {
  width: min(520px, calc(100vw - 24px));
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e4e4e4;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
}

.task-filters-modal__header {
  padding: 20px 20px 16px;
  border-bottom: 1px solid #e4e4e4;
}

.task-filters-modal__eyebrow {
  margin-bottom: 8px;
  padding: 0;
  border-radius: 0;
  background: transparent;
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0;
}

.task-filters-modal__body {
  gap: 16px;
  padding: 20px;
}

.task-filters-modal__footer {
  padding: 0 20px 20px;
}

.task-modal-overlay {
  padding: 24px;
}

.task-modal {
  width: min(1120px, calc(100vw - 48px));
  height: min(90vh, 980px);
  background: #fff;
  border: 1px solid #e4e4e4;
  border-radius: 8px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.task-modal__header {
  padding: 20px 24px;
  border-bottom: 1px solid #e4e4e4;
  background: #fff;
  backdrop-filter: none;
}

.task-modal__eyebrow {
  display: none;
}

.task-modal__heading h4 {
  margin: 0;
  color: #000;
  font-size: 20px;
  font-weight: 500;
  line-height: 28px;
}

.task-modal__heading p {
  display: none;
}

.task-modal__header-chips .badge {
  border-radius: 4px;
}

.task-modal__close {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background: #fff;
  border: 1px solid #e4e4e4;
  box-shadow: none;
}

.task-modal-grid {
  grid-template-columns: minmax(0, 1fr) 238px;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.task-modal-main {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.task-modal-form {
  padding: 0 24px;
  min-height: 0;
  flex: 1 1 auto;
}

.task-modal-form__body {
  gap: 0;
  padding-bottom: 12px;
}

.task-modal-panel {
  padding: 20px 0;
  border: none;
  border-bottom: 1px solid #e4e4e4;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.task-modal-panel--lead,
.task-modal-panel--summary {
  background: transparent;
  box-shadow: none;
}

.task-modal-panel__head {
  margin-bottom: 14px;
}

.task-modal-panel__label,
.task-modal-side__list span,
.task-modal-side-card__head span {
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
}

.task-modal-panel__head h5,
.task-modal-side-card__head h6,
.task-modal-side-card--hero h5 {
  color: #000;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
}

.task-modal-panel__caption,
.task-modal-side-card--hero p {
  color: #727272;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
}

.task-modal-title-input,
.task-modal-textarea,
.task-modal .form-control {
  border-radius: 4px;
  border-color: #d9d9d9;
  box-shadow: none;
}

.task-modal-title-input {
  min-height: 48px;
  font-size: 16px;
  font-weight: 500;
}

.task-modal-textarea {
  min-height: 120px;
}

.task-modal-summary-grid {
  gap: 12px;
}

.task-modal-summary-item {
  padding: 12px 14px;
  border-radius: 4px;
  background: #fff;
  border: 1px solid #e4e4e4;
}

.task-modal-side {
  padding: 0;
  border-left: 1px solid #e4e4e4;
  gap: 0;
  min-height: 0;
  overflow-y: auto;
}

.task-modal-side-card {
  padding: 20px;
  border: none;
  border-bottom: 1px solid #e4e4e4;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.task-modal-side-card--hero {
  text-align: center;
}

.task-modal-side__list > div {
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.task-modal-side__list {
  gap: 12px;
}

.task-modal-side__list strong {
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
}

.task-modal-side__chips {
  justify-content: flex-start;
}

.task-modal-side__pill {
  padding: 4px 8px;
  border-radius: 4px;
  background: #f2f2f2;
  color: #727272;
  font-size: 12px;
  font-weight: 500;
}

.task-modal-side-card--chat {
  flex: 1 1 auto;
}

.task-modal-side__placeholder {
  min-height: 160px;
  border-radius: 4px;
  border: 1px dashed #d9d9d9;
  background: #fafafa;
  color: #727272;
}

.task-modal-chat-panel {
  padding: 18px 24px 24px;
  border-top: 1px solid #e4e4e4;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.task-modal-chat-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.task-modal-chat-panel__head h6 {
  margin: 0;
  color: #000;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
}

.task-modal-chat-panel__head span {
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
  text-align: right;
}

.task-modal-chat-panel__body {
  min-height: 280px;
  max-height: 320px;
  display: flex;
  min-width: 0;
}

.task-modal-chat-panel__body .task-chat {
  flex: 1;
  min-height: 0;
  border: 1px solid #e4e4e4;
  border-radius: 4px;
  overflow: hidden;
}

.task-modal-chat-panel__placeholder {
  min-height: 160px;
}

@media (max-width: 1200px) {
  .task-modal {
    width: min(1120px, calc(100vw - 24px));
  }

  .task-modal-grid {
    grid-template-columns: 1fr;
  }

  .task-modal-main {
    overflow: visible;
  }

  .task-modal-form {
    padding: 20px 20px 0;
  }

  .task-modal-side {
    padding: 0 20px 20px;
    overflow: visible;
  }

  .task-modal-chat-panel {
    padding: 18px 20px 20px;
  }
}

/* Auction Grid */
.task-subtoolbar {
  min-height: 72px;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e4e4;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  background: #fff;
}

.task-subtoolbar__group {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.task-subtoolbar__field {
  min-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-subtoolbar__field--wide {
  min-width: 260px;
}

.task-subtoolbar__field span,
.task-subtoolbar__meta {
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
}

.task-subtoolbar__field .form-control {
  min-height: 38px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  color: #000;
  box-shadow: none;
}

.auction-shell__body {
  padding: 24px;
  background: #fff;
}

.auction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.auction-card {
  background: #fff;
  border: 1px solid #e4e4e4;
  border-radius: 8px;
  padding: 18px;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: border-color 0.18s ease, background 0.18s ease;
  position: relative;
  cursor: pointer;
}

.auction-card__body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 156px;
}

.auction-card__header-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.auction-card__flags {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 22px;
  min-width: 0;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.auction-delete {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background: #f2f2f2;
}

.auction-card:hover {
  transform: none;
  background: #fcfcfc;
  border-color: #d6d6d6;
  box-shadow: none;
}

.auction-card.auction-awarded {
  opacity: 0.7;
  background: #fafafa;
}

.auction-card.auction-cancelled {
  opacity: 0.5;
}

.auction-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  min-height: 32px;
  gap: 12px;
}

.auction-status-badge {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  line-height: 18px;
}

.status-new { background: #edf2fe; color: #4976f4; }
.status-awarded { background: #edf5ef; color: #4b9967; }
.status-cancelled { background: #f7eded; color: #af4b4b; }

.auction-title {
  margin: 0;
  color: #000;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  min-height: 48px;
  overflow-wrap: anywhere;
}

.auction-desc {
  margin: 0;
  color: #727272;
  font-size: 14px;
  line-height: 21px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.auction-desc--empty {
  min-height: 21px;
  display: block;
}

.auction-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid #e4e4e4;
  min-height: 48px;
}

.auction-budget, .auction-bids {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #727272;
  font-size: 14px;
  line-height: 21px;
}

.auction-budget {
  color: #000;
  font-size: 16px;
}

.auction-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 8px;
  align-items: center;
  margin-top: auto;
}

.auction-block {
  border-top: 1px solid #e4e4e4;
  padding-top: 14px;
  min-height: 34px;
}

.auction-block-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  color: #000;
  font-size: 14px;
  font-weight: 500;
  background: transparent;
  border: none;
  cursor: pointer;
}

.auction-block--spacer {
  visibility: hidden;
  pointer-events: none;
}

.auction-block-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.auction-subtask {
  border: 1px solid #e4e4e4;
  border-radius: 4px;
  background: #fff;
  overflow: hidden;
}

.auction-subtask-toggle {
  width: 100%;
  background: transparent;
  border: none;
  text-align: left;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
}

.auction-subtask-main {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.auction-subtask-title {
  color: #000;
  font-size: 14px;
  font-weight: 500;
  line-height: 21px;
}

.auction-subtask-budget {
  color: #000;
  font-weight: 500;
}

.auction-subtask-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.auction-subtask-details {
  border-top: 1px solid #e4e4e4;
  padding: 12px;
  background: #fcfcfc;
}

.auction-subtask-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.auction-card .btn-primary {
  border: 1px solid #000;
  background: #fff;
  color: #000;
  box-shadow: none;
  min-height: 38px;
  border-radius: 4px;
}

.auction-card .btn-primary:hover,
.auction-card .btn-primary:focus {
  background: #fff;
  border-color: #000;
  color: #000;
}

.auction-card .btn-success {
  border: 1px solid #000;
  background: #000;
  color: #fff;
  box-shadow: none;
  min-height: 38px;
  border-radius: 4px;
}

.auction-card .btn-success:hover,
.auction-card .btn-success:focus {
  background: #000;
  border-color: #000;
  color: #fff;
}

.auction-actions .btn-icon {
  width: 38px;
  height: 38px;
  border-radius: 4px;
  background: #f2f2f2;
}

.auction-actions__placeholder {
  width: 38px;
  height: 38px;
}

.auction-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.auction-items-header {
  font-weight: 600;
}

.auction-item-row {
  display: grid;
  grid-template-columns: minmax(140px, 1.2fr) minmax(140px, 1.4fr) minmax(120px, 0.7fr) minmax(90px, 0.6fr) auto;
  gap: 0.5rem;
  align-items: center;
}

@media (max-width: 768px) {
  .auction-item-row {
    grid-template-columns: 1fr;
  }
}

/* Bid list */
.bid-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bid-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--md-sys-color-surface-variant);
  border-radius: 8px;
}

.bid-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-grow: 1;
}

.avatar-sm {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.bid-price {
  font-size: 1.1rem;
}

/* Rating stars */
.rating-stars {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.rating-star:hover {
  transform: scale(1.1);
}

.task-rating {
  display: inline-flex;
  gap: 2px;
  font-size: 0.85rem;
}

.task-rating .fa-star {
  font-size: 0.85rem;
}

.task-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

.task-card {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  padding: 12px;
  box-shadow: var(--shadow-sm);
}

.task-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.task-card__title {
  font-weight: 600;
  font-size: 0.95rem;
  line-height: 1.3;
}

.task-card__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 12px;
  margin-top: 10px;
}

.task-card__label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
}

.task-card__actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.task-list-container {
  min-height: 0;
}

.task-layout-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: linear-gradient(180deg, rgba(63, 140, 255, 0.04), rgba(63, 140, 255, 0));
}

.task-layout-toolbar__tabs {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: var(--md-sys-color-surface-container-low, rgba(63, 140, 255, 0.08));
  border-radius: 14px;
}

.task-layout-tab {
  min-height: 40px;
  padding: 0 14px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.task-layout-tab--active {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-primary);
  box-shadow: 0 10px 24px rgba(63, 140, 255, 0.12);
}

.task-layout-toolbar__meta {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.task-layout-toolbar__count {
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.task-layout-toolbar__hint {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
}

.task-list-container--kanban {
  /* Board has its own padding (matches Leads kanban) — keep container neutral */
  padding: 0;
  background: transparent;
}

.task-kanban-board {
  display: flex;
  align-items: flex-start;
  gap: 22px;
  min-height: 100%;
  min-width: max-content;
}

.task-kanban-column {
  width: 352px;
  min-height: 100%;
  padding: 18px;
  background: #fbfcfe;
  border: 1px solid rgba(228, 228, 228, 0.95);
  border-radius: 18px;
  box-shadow: none;
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.task-kanban-column--over {
  border-color: var(--task-kanban-accent);
  box-shadow: 0 16px 30px rgba(63, 140, 255, 0.14);
  transform: translateY(-2px);
}

.task-kanban-column__header {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 18px;
}

.task-kanban-column__title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-kanban-column__dot {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--task-kanban-accent);
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--task-kanban-accent) 16%, transparent);
}

.task-kanban-column__title-wrap h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.task-kanban-column__title-wrap p {
  margin: 4px 0 0;
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
}

.task-kanban-column__create {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.1));
  border-radius: 8px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant, #475569);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.78rem;
  transition: background 0.12s ease, color 0.12s ease, border-color 0.12s ease;
}
.task-kanban-column__create:hover {
  background: var(--md-sys-color-primary, #1976d2);
  border-color: var(--md-sys-color-primary, #1976d2);
  color: #fff;
}

.task-kanban-column__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-kanban-column__empty {
  min-height: 80px;
  padding: 14px 18px;
  border: 1px dashed var(--md-sys-color-outline-variant);
  border-radius: 10px;
  color: var(--md-sys-color-on-surface-variant);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  line-height: 1.4;
  font-size: 0.82rem;
  opacity: 0.7;
}

.task-kanban-card {
  padding: 18px;
  border: 1px solid rgba(228, 228, 228, 0.95);
  border-radius: 14px;
  background: #fff;
  box-shadow: none;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.task-kanban-card:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 22, 41, 0.16);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
}

.task-kanban-card--updating {
  opacity: 0.6;
  pointer-events: none;
}

.task-kanban-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.task-kanban-chip {
  padding: 5px 8px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
  line-height: 1;
}

.task-kanban-chip--category {
  background: #eff4fa;
  color: #5f6f87;
}

.task-kanban-chip--low {
  background: #eff7ef;
  color: #5d8c63;
}

.task-kanban-chip--normal {
  background: #e7f1ff;
  color: #2d6cca;
}

.task-kanban-chip--high {
  background: #fff4e5;
  color: #ce8622;
}

.task-kanban-chip--urgent {
  background: #ffe8e8;
  color: #c14949;
}

.task-kanban-chip--auction {
  background: #f3ebff;
  color: #7651b8;
}

.task-kanban-card__title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.task-kanban-card__title-row h4 {
  margin: 0;
  font-size: 1rem;
  line-height: 1.4;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.task-kanban-card__project {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.84rem;
}

.task-kanban-card__description {
  margin: 0 0 16px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

.task-kanban-card__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.task-kanban-card__meta span {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.82rem;
}

.task-kanban-card__meta strong {
  min-width: 0;
  overflow-wrap: anywhere;
  font-weight: 700;
}

.task-kanban-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-kanban-card__assignee {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.task-kanban-card__avatar {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(63, 140, 255, 0.14), rgba(63, 140, 255, 0.35));
  color: var(--md-sys-color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.task-kanban-card__assignee strong,
.task-kanban-card__assignee span {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-kanban-card__assignee strong {
  color: var(--md-sys-color-on-surface);
  font-size: 0.84rem;
}

.task-kanban-card__assignee span {
  margin-top: 2px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.74rem;
}

.task-kanban-card__actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.task-list-container--matrix {
  padding: 16px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 0.96));
  overflow: auto;
}

.task-matrix-board {
  min-height: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.task-matrix-quadrant {
  min-height: 292px;
  padding: 14px;
  border: 1px dashed color-mix(in srgb, var(--task-matrix-accent) 28%, transparent);
  border-radius: 18px;
  background: var(--task-matrix-bg);
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.task-matrix-quadrant--over {
  border-color: var(--task-matrix-accent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--task-matrix-accent) 34%, transparent);
  transform: translateY(-1px);
}

.task-matrix-quadrant__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.task-matrix-quadrant__title {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.task-matrix-quadrant__dot {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--task-matrix-accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--task-matrix-accent) 14%, transparent);
  flex: 0 0 auto;
}

.task-matrix-quadrant__title h3 {
  margin: 0;
  color: var(--md-sys-color-on-surface);
  font-size: 0.98rem;
  font-weight: 800;
  line-height: 1.2;
}

.task-matrix-quadrant__title p {
  margin: 2px 0 0;
  color: var(--task-matrix-accent);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1.15;
  text-transform: uppercase;
}

.task-matrix-quadrant__count {
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.76rem;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.task-matrix-grid {
  flex: 1;
  min-height: 210px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: minmax(68px, auto);
  align-content: start;
  gap: 8px;
}

.task-matrix-card {
  min-width: 0;
  min-height: 68px;
  padding: 8px 9px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  cursor: grab;
  display: grid;
  /* `auto` вместо фиксированных 28px — иначе stack из 2+ аватарок
     (каждая 26px с overlap -8px → 44/62/80px на 2/3/4) обрезается. */
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  transition: transform 0.16s ease, border-color 0.16s ease, opacity 0.16s ease;
}

.task-matrix-card:hover {
  transform: translateY(-1px);
  border-color: rgba(37, 99, 235, 0.22);
}

.task-matrix-card:active {
  cursor: grabbing;
}

.task-matrix-card--updating {
  opacity: 0.6;
  pointer-events: none;
}

.task-matrix-card__main {
  min-width: 0;
}

.task-matrix-card__main h4 {
  margin: 0;
  color: #1f2937;
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.task-matrix-card__meta {
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  color: #64748b;
  font-size: 0.68rem;
}

.task-matrix-card__meta span {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.task-matrix-card__meta strong {
  font-weight: 800;
}

.task-matrix-card__avatar {
  width: 28px;
  height: 28px;
}

.task-matrix-status {
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 0.62rem;
  font-weight: 800;
  white-space: nowrap;
}

.task-matrix-status--new {
  background: rgba(100, 116, 139, 0.12);
  color: #475569;
}

.task-matrix-status--progress {
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
}

.task-matrix-status--pending {
  background: rgba(245, 158, 11, 0.15);
  color: #b45309;
}

.task-matrix-status--completed {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.task-matrix-status--cancelled {
  background: rgba(239, 68, 68, 0.14);
  color: #b91c1c;
}

.task-matrix-status--deferred {
  background: rgba(99, 102, 241, 0.14);
  color: #4338ca;
}

.task-matrix-empty {
  min-height: 68px;
  border: 1px dashed rgba(148, 163, 184, 0.38);
  border-radius: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  grid-column: 1 / -1;
}

@media (max-width: 1400px) {
  .task-matrix-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .task-matrix-board {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .task-matrix-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-container--matrix {
  background: transparent;
}

:global(:root[data-theme="dark"]) .tasks-view .task-matrix-quadrant {
  background: rgba(17, 26, 44, 0.88);
  border-color: rgba(71, 85, 105, 0.6);
}

:global(:root[data-theme="dark"]) .tasks-view .task-matrix-card {
  background: #111a2c;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .task-matrix-card__main h4 {
  color: #eef4ff;
}

:global(:root[data-theme="dark"]) .tasks-view .task-matrix-quadrant__count {
  background: #1b2740;
  color: #cbd5e1;
}

.tasks-filters-toolbar .form-group {
  margin-bottom: 0;
}

.tasks-filter-deal {
  flex: 1 1 320px;
  max-width: 520px;
}

.tasks-controls-group {
  margin-left: 0;
}

.tasks-controls-group .badge,
.tasks-controls-group .small {
  white-space: nowrap;
}

/* Penalty rules layout */
.rules-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.rules-shell__header {
  min-height: 72px;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e4e4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.rules-shell__headline h3 {
  color: #000;
  font-size: 20px;
  font-weight: 500;
  line-height: 24px;
}

.rules-shell__headline p {
  margin: 6px 0 0;
  color: #727272;
  font-size: 14px;
  line-height: 21px;
}

.rules-shell__body {
  background: #fff;
  padding: 24px !important;
}

.rules-block {
  background: #fff;
  border: 1px solid #e4e4e4;
  border-radius: 8px;
  padding: 16px;
}

.rules-block__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.rules-block__header h5 {
  color: #000;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
}

.rules-block__header span {
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
}

.rules-table {
  margin: 0;
}

.rules-table thead th {
  padding: 10px 12px;
  color: #727272;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
  text-transform: none;
  border-top: none;
  border-bottom: 1px solid #e4e4e4;
}

.rules-table tbody td {
  padding: 12px;
  color: #000;
  font-size: 14px;
  font-weight: 400;
  line-height: 21px;
  border-top: none;
  border-bottom: 1px solid #efefef;
}

.rules-table tbody tr:last-child td {
  border-bottom: none;
}

.rules-table .badge {
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.rules-table th:last-child,
.rules-table td:last-child {
  width: 48px;
  text-align: right;
}

.rules-table th:nth-last-child(2),
.rules-table td:nth-last-child(2) {
  width: 90px;
  text-align: center;
}

@media (max-width: 1200px) {
  .rules-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .tasks-view {
    padding: 8px !important;
    height: auto !important;
  }

  .task-module-topbar {
    padding: 0 14px;
    border-radius: 10px 10px 0 0;
  }

  .task-module-main {
    border-radius: 0 0 10px 10px;
  }

  .task-module-topbar__row,
  .task-module-topbar__meta,
  .task-module-topbar__title-group,
  .task-module-topbar__actions,
  .task-module-topbar__meta-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .task-module-topbar__actions,
  .task-module-topbar__meta-actions {
    gap: 10px;
  }

  .task-module-topbar__actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: stretch;
  }

  .task-module-topbar__actions > * {
    width: 100%;
    min-width: 0;
  }

  .task-module-topbar__actions > .task-toolbar-inline-filters,
  .task-module-topbar__actions > .task-segmented,
  .task-module-topbar__actions > .task-module-topbar__create-btn {
    grid-column: 1 / -1;
  }

  .task-module-topbar__meta {
    display: none;
  }

  .task-module-topbar__filters,
  .task-module-topbar__meta-actions {
    width: 100%;
  }

  .task-page-size-box,
  .task-module-topbar__count {
    display: none;
  }

  .task-module-topbar__pagination {
    width: 100%;
    justify-content: space-between;
  }

  .task-segmented {
    width: 100%;
    overflow-x: auto;
  }

  .task-segmented__button {
    flex: 1 0 auto;
    justify-content: center;
    min-height: 52px;
  }

  .task-subtoolbar {
    padding: 14px;
    align-items: flex-start;
  }

  .task-subtoolbar,
  .task-subtoolbar__group {
    flex-direction: column;
  }

  .task-toolbar-inline-filters {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .task-toolbar-select,
  .task-toolbar-select--wide {
    width: 100%;
    min-width: 0;
  }

  .task-subtoolbar__field,
  .task-subtoolbar__field--wide {
    width: 100%;
    min-width: 0;
  }

  .task-toolbar-btn,
  .task-sort-box,
  .task-page-size-box,
  .task-module-topbar__create-btn {
    width: 100%;
  }

  .task-list-shell {
    padding: 14px;
  }

  .task-list-line {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .task-list-line__tail {
    justify-content: space-between;
  }

  .task-list-line__cell--labels,
  .task-list-line__cell--assignee {
    justify-content: flex-start;
  }

  .task-modal-overlay {
    padding: 8px;
  }

  .task-modal__header {
    flex-direction: column;
    align-items: stretch;
    padding: 20px;
  }

  .task-modal__header-side {
    width: 100%;
    justify-content: space-between;
  }

  .task-modal-grid-fields--2,
  .task-modal-grid-fields--3,
  .task-modal-summary-grid {
    grid-template-columns: 1fr;
  }
  
  .tasks-view h1 {
    font-size: 1.25rem;
  }
  
  /* Filters column layout */
  .card.flex-shrink-0 .d-flex.gap-3 {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  
  .card.flex-shrink-0 .form-group {
    min-width: 0 !important;
    width: 100%;
  }

  .tasks-filters-toolbar {
    display: flex !important;
    gap: 8px;
  }

  .tasks-filter-deal {
    max-width: none;
    flex: 1 1 100%;
  }

  .tasks-controls-group {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
  
  /* View toggle */
  .btn-group {
    display: flex;
    width: 100%;
    flex-wrap: wrap;
    gap: 6px;
  }

  .btn-group .btn {
    flex: 1 1 0;
  }

  .tasks-view > .d-flex:first-child .btn.btn-primary {
    width: 100%;
  }
  
  /* Table responsive */
  .table-container {
    overflow-x: auto;
  }
  
  .table {
    min-width: 700px;
  }

  .tasks-view .card.flex-grow-1 {
    overflow: visible;
  }

  .task-list-container {
    overflow: visible;
  }

  .task-list-container--kanban {
    padding: 14px;
    overflow-x: auto !important;
    scroll-snap-type: x mandatory;
    overscroll-behavior-x: contain;
    -webkit-overflow-scrolling: touch;
    touch-action: pan-x;
  }

  .task-kanban-board {
    width: max-content;
    min-width: 100%;
    gap: 12px;
    padding-right: 12px;
  }

  .auction-shell__body,
  .rules-shell__body {
    padding: 14px !important;
  }

  .rules-shell__header {
    padding: 14px;
    align-items: flex-start;
  }

  .task-kanban-column {
    width: min(84vw, 320px);
    padding: 16px;
    scroll-snap-align: start;
  }

  .task-kanban-card__meta {
    grid-template-columns: 1fr;
  }

  .task-modal-form {
    padding: 0 16px 16px;
  }

  .task-modal-side {
    padding: 0;
    border-left: none;
    border-top: 1px solid #e4e4e4;
  }

  .rules-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .task-card__meta {
    grid-template-columns: 1fr;
  }

  .card.flex-shrink-0 .d-flex.gap-3 {
    grid-template-columns: 1fr;
  }

  .tasks-controls-group {
    gap: 6px;
  }

  .task-kanban-column {
    width: min(86vw, 292px);
  }

  .task-modal {
    width: calc(100vw - 12px);
    border-radius: 8px;
  }

  .task-modal__heading h4 {
    font-size: 1.1rem;
  }

  .task-modal-panel,
  .task-modal-side-card {
    padding: 16px;
  }
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin-left: -6px;
  margin-right: -6px;
}

.row > [class*="col-"] {
  padding-left: 6px;
  padding-right: 6px;
  min-width: 0;
}

.col-6 {
  width: 50%;
  flex: 0 0 50%;
  max-width: 50%;
}

.col-md-4,
.col-md-6,
.col-md-8,
.col-md-12 {
  min-width: 0;
}

.g-2 {
  gap: 0.5rem !important;
}

.g-3 {
  gap: 1rem !important;
}

.g-4 {
  gap: 1.5rem !important;
}

@media (max-width: 768px) {
  .row > [class*="col-"] {
    width: 100%;
    max-width: 100%;
    flex: 0 0 100%;
  }

  .col-md-4,
  .col-md-6,
  .col-md-8,
  .col-md-12 {
    width: 100%;
    max-width: 100%;
    flex: 0 0 100%;
  }
}

@media (max-width: 480px) {
  .col-6 {
    width: 100%;
    flex: 0 0 100%;
    max-width: 100%;
  }
}

.task-modal.task-sheet {
  width: min(1320px, calc(100vw - 40px));
  max-width: min(1320px, calc(100vw - 40px)) !important;
  height: min(90vh, 840px);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 368px;
  padding: 0;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #dbe1ea;
  border-radius: 22px;
  box-shadow: 0 22px 58px rgba(15, 23, 42, 0.12);
  transition: width 0.18s ease, max-width 0.18s ease;
}
.task-modal.task-sheet--no-aside {
  width: min(880px, calc(100vw - 40px));
  max-width: min(880px, calc(100vw - 40px)) !important;
  grid-template-columns: minmax(0, 1fr);
}

.task-sheet__main {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.task-sheet__header {
  padding: 22px 28px 18px;
  border-bottom: 1px solid #ebeff5;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.task-sheet__header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.task-sheet__breadcrumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #8a94a6;
  font-size: 14px;
  font-weight: 600;
}

.task-sheet__breadcrumbs i {
  color: #73809a;
}

.task-sheet__window-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.task-sheet__icon-btn {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #98a1b2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.task-sheet__icon-btn:hover {
  background: #f5f7fb;
  color: #4f5d75;
}

.task-sheet__title-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: #0f172a;
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
  padding: 0;
}

.task-sheet__form {
  min-height: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  padding: 0 28px 20px;
}

.task-sheet__scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 30px 0 18px;
  display: flex;
  flex-direction: column;
  gap: 34px;
}

.task-sheet__control-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  padding: 18px;
  border: 1px solid #edf1f6;
  border-radius: 18px;
  background: #f8fafd;
}

.task-sheet__control-card {
  min-width: 0;
}

.task-sheet__control-card label {
  display: block;
  margin-bottom: 10px;
  color: #9aa3b3;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.task-sheet__select-wrap {
  position: relative;
}

.task-sheet__control-select {
  width: 100%;
  min-height: 48px;
  padding: 0 38px 0 42px;
  border: 1px solid #d9e0ea;
  border-radius: 12px;
  background: #ffffff;
  color: #0f172a;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
}

.task-sheet__control-icon {
  position: absolute;
  top: 50%;
  left: 16px;
  transform: translateY(-50%);
  font-size: 14px;
  pointer-events: none;
}

.task-sheet__control-icon--slate {
  color: #8691a4;
}

.task-sheet__control-icon--blue {
  color: #3f8cff;
}

.task-sheet__control-icon--orange {
  color: #ff8b2c;
}

.task-sheet__control-icon--violet {
  color: #9b51ff;
}

.task-sheet__select-wrap--assignee .task-sheet__control-select {
  padding-left: 54px;
}

.task-sheet__assignee-avatar {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0f172a;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}

.task-sheet__assignee-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.task-sheet__section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.task-sheet__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-sheet__section-title {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.task-sheet__section-title h5 {
  margin: 0;
  color: #0f172a;
  font-size: 1.05rem;
  font-weight: 700;
}

.task-sheet__marker {
  width: 4px;
  height: 18px;
  border-radius: 999px;
}

.task-sheet__marker.is-blue {
  background: #2f6fff;
}

.task-sheet__marker.is-violet {
  background: #b04dff;
}

.task-sheet__section-tools {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.task-sheet__section-tool {
  border: none;
  background: transparent;
  color: #8e97a9;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.task-sheet__description {
  min-height: 198px;
  padding: 18px 18px;
  border: 1px solid #e3e8f0;
  border-radius: 16px;
  background: #ffffff;
  resize: vertical;
  box-shadow: none;
  color: #334155;
  font-size: 15px;
  line-height: 1.65;
}

.task-sheet__attachments {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-sheet__attachments-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.task-sheet__attachments-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #334155;
  font-size: 14px;
  font-weight: 700;
}

.task-sheet__attachments-count {
  min-width: 22px;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: #e8efff;
  color: #2f6fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.task-sheet__attachments-note {
  color: #8a94a6;
  font-size: 12px;
  line-height: 1.5;
}

.task-sheet__attachments-dropzone {
  min-height: 78px;
  padding: 14px 16px;
  border: 1px dashed #c8d4e5;
  border-radius: 16px;
  background: #f8fbff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}

.task-sheet__attachments-dropzone.is-dragover {
  border-color: #2f6fff;
  background: #eef4ff;
  box-shadow: inset 0 0 0 1px rgba(47, 111, 255, 0.12);
}

.task-sheet__attachments-dropzone-main {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.task-sheet__attachments-dropzone-main > i {
  color: #2f6fff;
  font-size: 18px;
}

.task-sheet__attachments-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-sheet__attachments-copy strong {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.task-sheet__attachments-copy span {
  color: #8a94a6;
  font-size: 12px;
}

.task-sheet__attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-sheet__attachment-item {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #e3e8f0;
  border-radius: 14px;
  background: #ffffff;
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-sheet__attachment-item--pending {
  background: #fbfcff;
  border-style: dashed;
}

.task-sheet__attachment-main {
  min-width: 0;
  flex: 1 1 auto;
  padding: 0;
  border: none;
  background: transparent;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.task-sheet__attachment-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #eef4ff;
  color: #2f6fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.task-sheet__attachment-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-sheet__attachment-copy strong,
.task-sheet__attachment-copy small {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-sheet__attachment-copy strong {
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
}

.task-sheet__attachment-copy small {
  color: #8a94a6;
  font-size: 12px;
}

.task-sheet__attachment-action {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: #f8fafc;
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.task-sheet__attachment-action:hover {
  background: #eef2f7;
  color: #475569;
}

@media (max-width: 768px) {
  .task-sheet__attachments-head,
  .task-sheet__attachments-dropzone {
    flex-direction: column;
    align-items: stretch;
  }
}

.task-sheet__detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.task-sheet__detail-card {
  padding: 18px 16px;
  border: 1px solid #e6ebf3;
  border-radius: 18px;
  background: #fcfdff;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.task-sheet__detail-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #6e7b92;
  font-size: 15px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.task-sheet__detail-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-sheet__detail-field label {
  margin: 0;
  color: #9aa3b3;
  font-size: 13px;
  font-weight: 600;
}

.task-sheet__mini-input {
  min-height: 42px;
  border-radius: 12px;
  border-color: #dde4ef;
  box-shadow: none;
}

.task-sheet__notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
}

.task-sheet__notice--info {
  background: #eff6ff;
  color: #2563eb;
}

.task-sheet__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.task-sheet__summary-item {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #e6ebf3;
  background: #fbfcff;
}

.task-sheet__summary-item span {
  display: block;
  margin-bottom: 8px;
  color: #9aa3b3;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.task-sheet__summary-item strong {
  color: #0f172a;
  font-size: 15px;
}

.task-sheet__summary-action {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
}

.task-sheet__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 18px;
  border-top: 1px solid #ebeff5;
}

.task-sheet__submit {
  min-width: 156px;
  border-radius: 14px;
}

.task-sheet__chat {
  min-width: 0;
  min-height: 0;
  border-left: 1px solid #ebeff5;
  background: #fbfcfe;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 12px;
}

.task-sheet__chat-inner,
.task-sheet__chat-empty {
  flex: 1;
  min-height: 0;
}

.task-sheet__approval {
  flex: 0 0 auto;
  min-width: 0;
}

.task-sheet__chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  color: #8d96a8;
  text-align: center;
}

.task-sheet__chat-empty i {
  font-size: 1.5rem;
  color: #7d8aa0;
}

@media (max-width: 1440px) {
  .task-modal.task-sheet {
    grid-template-columns: minmax(0, 1fr) 332px;
    width: min(1240px, calc(100vw - 28px));
    max-width: min(1240px, calc(100vw - 28px)) !important;
  }

  .task-sheet__control-strip {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {
  .task-sheet__control-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1180px) {
  .task-modal.task-sheet {
    grid-template-columns: 1fr;
    height: min(94vh, 980px);
  }

  .task-sheet__chat {
    border-left: none;
    border-top: 1px solid #ebeff5;
    min-height: 420px;
  }

  .task-sheet__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .task-modal.task-sheet {
    width: calc(100vw - 12px);
    max-width: calc(100vw - 12px) !important;
    height: calc(100vh - 12px);
    border-radius: 16px;
  }

  .task-sheet__header,
  .task-sheet__form {
    padding-left: 18px;
    padding-right: 18px;
  }

  .task-sheet__control-strip,
  .task-sheet__detail-grid,
  .task-sheet__summary {
    grid-template-columns: 1fr;
  }

  .task-sheet__title-input {
    font-size: 1.45rem;
  }

  .task-sheet__header-top,
  .task-sheet__section-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .task-sheet__window-actions {
    align-self: flex-end;
  }
}

:global(:root[data-theme="dark"]) .tasks-view {
  color: #e5ecf7;
}

:global(:root[data-theme="dark"]) .tasks-view .text-muted,
:global(:root[data-theme="dark"]) .tasks-view .small.text-muted,
:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar__count,
:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar__hint,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__title-wrap p,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__cell > span,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__stats,
:global(:root[data-theme="dark"]) .tasks-view .task-person__body > span:last-child,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__project,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__description,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__meta span,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column__title-wrap p,
:global(:root[data-theme="dark"]) .tasks-view .auction-desc,
:global(:root[data-theme="dark"]) .tasks-view .auction-bids,
:global(:root[data-theme="dark"]) .tasks-view .task-subtoolbar__field span,
:global(:root[data-theme="dark"]) .tasks-view .task-subtoolbar__meta,
:global(:root[data-theme="dark"]) .tasks-view .rules-shell__headline p,
:global(:root[data-theme="dark"]) .tasks-view .rules-block__header span,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__breadcrumbs,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__control-card label,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__detail-field label,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__summary-item span {
  color: #8f9bb2 !important;
}

:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar,
:global(:root[data-theme="dark"]) .tasks-view .task-module-main,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal,
:global(:root[data-theme="dark"]) .tasks-view .task-modal.task-sheet,
:global(:root[data-theme="dark"]) .tasks-view .rules-block,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card,
:global(:root[data-theme="dark"]) .tasks-view .auction-card,
:global(:root[data-theme="dark"]) .tasks-view .auction-subtask,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__detail-card,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__summary-item {
  background: #0f1726;
  border-color: #243044;
  box-shadow: 0 18px 38px rgba(2, 8, 23, 0.36);
}

:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar,
:global(:root[data-theme="dark"]) .tasks-view .task-module-main {
  background: rgba(10, 16, 27, 0.94);
  border-color: rgba(53, 67, 88, 0.88);
  box-shadow: 0 24px 48px rgba(2, 8, 23, 0.34);
}

:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar__title-group h1,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__title-wrap h3,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__cell > strong,
:global(:root[data-theme="dark"]) .tasks-view .task-person__body > span:first-child,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column__title-wrap h3,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__title-row h4,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__meta strong,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__assignee strong,
:global(:root[data-theme="dark"]) .tasks-view .auction-title,
:global(:root[data-theme="dark"]) .tasks-view .auction-budget,
:global(:root[data-theme="dark"]) .tasks-view .auction-subtask-title,
:global(:root[data-theme="dark"]) .tasks-view .auction-subtask-budget,
:global(:root[data-theme="dark"]) .tasks-view .rules-shell__headline h3,
:global(:root[data-theme="dark"]) .tasks-view .rules-block__header h5,
:global(:root[data-theme="dark"]) .tasks-view .rules-table tbody td,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__title-input,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__section-title h5,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__detail-title,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__summary-item strong,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__chat-empty,
:global(:root[data-theme="dark"]) .tasks-view .task-module-main__headline h2,
:global(:root[data-theme="dark"]) .tasks-view .task-module-main__summary span:first-child {
  color: #f3f7ff !important;
}

:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar__row,
:global(:root[data-theme="dark"]) .tasks-view .task-module-topbar__meta,
:global(:root[data-theme="dark"]) .tasks-view .task-subtoolbar,
:global(:root[data-theme="dark"]) .tasks-view .rules-shell__header,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__header,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__footer,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__chat,
:global(:root[data-theme="dark"]) .tasks-view .rules-table thead th,
:global(:root[data-theme="dark"]) .tasks-view .rules-table tbody td,
:global(:root[data-theme="dark"]) .tasks-view .auction-meta,
:global(:root[data-theme="dark"]) .tasks-view .auction-block,
:global(:root[data-theme="dark"]) .tasks-view .auction-subtask-details,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line,
:global(:root[data-theme="dark"]) .tasks-view .task-modal__header,
:global(:root[data-theme="dark"]) .tasks-view .task-modal-panel,
:global(:root[data-theme="dark"]) .tasks-view .task-modal-side,
:global(:root[data-theme="dark"]) .tasks-view .task-modal-side-card,
:global(:root[data-theme="dark"]) .tasks-view .task-modal-chat-panel,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__detail-card,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__summary-item {
  border-color: #243044 !important;
}

:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-btn,
:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-icon-btn,
:global(:root[data-theme="dark"]) .tasks-view .task-segmented,
:global(:root[data-theme="dark"]) .tasks-view .task-sort-box,
:global(:root[data-theme="dark"]) .tasks-view .task-page-size-box,
:global(:root[data-theme="dark"]) .tasks-view .task-filter-pill,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__icon-btn,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__section-tool,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__actions .btn-icon,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__actions .btn-icon,
:global(:root[data-theme="dark"]) .tasks-view .auction-delete,
:global(:root[data-theme="dark"]) .tasks-view .auction-actions .btn-icon {
  background: #141e30;
  border-color: #243044;
  color: #c4d0e6;
}

:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-btn:hover,
:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-icon-btn:hover,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__icon-btn:hover,
:global(:root[data-theme="dark"]) .tasks-view .task-list-line__actions .btn-icon:hover,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card__actions .btn-icon:hover,
:global(:root[data-theme="dark"]) .tasks-view .auction-delete:hover,
:global(:root[data-theme="dark"]) .tasks-view .auction-actions .btn-icon:hover {
  background: #1b2740;
  color: #eef4ff;
}

:global(:root[data-theme="dark"]) .tasks-view .task-segmented__button {
  color: #8f9bb2;
}

:global(:root[data-theme="dark"]) .tasks-view .task-segmented__button--active {
  background: #eef4ff;
  color: #0f1726;
}

:global(:root[data-theme="dark"]) .tasks-view .task-filter-pill {
  border: 1px solid #243044;
  color: #d2dceb;
}

:global(:root[data-theme="dark"]) .tasks-view .task-filter-pill--clear {
  color: #9fb7ff;
  border-color: rgba(100, 136, 255, 0.32);
  background: rgba(49, 85, 201, 0.14);
}

/* ===== Compact toolbar additions ===== */
.task-toolbar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

/* Topbar overall — compact, but keep card-like surface */
.task-module-topbar {
  padding: 8px 12px !important;
  margin-bottom: 6px !important;
  background: var(--md-sys-color-surface, rgba(255,255,255,0.92)) !important;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.06)) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

/* Inline pager in toolbar */
.task-toolbar-pager {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  height: 32px;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.1));
  border-radius: 8px;
  background: var(--md-sys-color-surface, #fff);
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface);
}
.task-toolbar-pager__label {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 600;
  min-width: 38px;
  text-align: center;
}
.task-toolbar-pager__size {
  border: none;
  background: transparent;
  font-size: 0.82rem;
  color: inherit;
  outline: none;
  cursor: pointer;
  padding: 0 4px;
  border-left: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.1));
  margin-left: 4px;
}
.task-toolbar-pager__total {
  font-size: 0.78rem;
  padding-left: 6px;
  border-left: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.08));
}
.task-toolbar-pager .task-toolbar-icon-btn {
  width: 22px;
  height: 22px;
  padding: 0;
}

/* Meta row (filter pills only) — compact */
.task-module-topbar__meta { margin-top: 4px !important; padding-top: 4px !important; border-top: none !important; }

/* Reduce gap between toolbar and table */
.tasks-view .task-module-main { margin-top: 0 !important; }
.task-list-shell { padding: 8px 12px !important; gap: 6px !important; }
.task-title { font-size: 1rem; font-weight: 700; margin: 0; white-space: nowrap; }
.task-segmented--sm .task-segmented__button { padding: 5px 10px; font-size: 0.82rem; }
.hide-md { }
@media (max-width: 1100px) { .hide-md { display: none; } }

.task-search {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 1 320px;
  min-width: 160px;
  height: 32px;
  padding: 0 10px;
  margin-left: auto;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.1));
  border-radius: 8px;
  background: var(--md-sys-color-surface, #fff);
}
.task-search i { color: var(--md-sys-color-on-surface-variant, #94a3b8); font-size: 0.78rem; }
.task-search input { flex: 1; border: none; outline: none; background: transparent; font-size: 0.85rem; color: inherit; }
.task-search__clear {
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  padding: 2px 4px;
}
.task-toolbar-btn--active {
  background: var(--md-sys-color-primary, #1976d2) !important;
  color: #fff !important;
}

/* ===== List header with sortable cells ===== */
.task-list-head {
  display: grid;
  grid-template-columns: minmax(280px, 2.4fr) 110px minmax(160px, 1.2fr) minmax(120px, 1fr) minmax(180px, 1.4fr) 130px;
  gap: 12px;
  padding: 10px 16px;
  background: var(--md-sys-color-surface-container, #f1f5f9);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 700;
}
.task-list-head__lead { display: flex; align-items: center; gap: 8px; }
.task-list-head__select input { cursor: pointer; }
.task-list-head__sort {
  background: transparent;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: inherit;
  color: inherit;
  padding: 0;
}
.task-list-head__sort:hover { color: var(--md-sys-color-on-surface); }
.task-list-head__sort.active { color: var(--md-sys-color-primary, #1976d2); }
.task-list-head__cell { display: flex; align-items: center; }
@media (max-width: 1100px) {
  .task-list-head { display: none; }
}

/* ===== List line: status stripe + selection ===== */
.task-list-line {
  position: relative;
  padding-left: 28px;
}
.task-list-line__stripe {
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 4px;
  border-radius: 4px;
  background: #cbd5e1;
}
.task-list-line--status-new .task-list-line__stripe { background: #94a3b8; }
.task-list-line--status-in_progress .task-list-line__stripe { background: #3b82f6; }
.task-list-line--status-pending .task-list-line__stripe { background: #f59e0b; }
.task-list-line--status-completed .task-list-line__stripe { background: #22c55e; }
.task-list-line--status-cancelled .task-list-line__stripe { background: #ef4444; opacity: 0.5; }
.task-list-line--status-deferred .task-list-line__stripe { background: #6366f1; }
.task-list-line--selected {
  background: var(--md-sys-color-primary-container, rgba(25, 118, 210, 0.08));
}
.task-list-line__select {
  margin-right: 4px;
  display: flex;
  align-items: center;
}
.task-list-line__select input { cursor: pointer; width: 16px; height: 16px; }

/* ===== Floating bulk action bar ===== */
.bulk-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1500;
  background: var(--md-sys-color-primary, #1976d2);
  color: #fff;
  border-radius: 14px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 12px 32px rgba(13, 71, 161, 0.35);
  flex-wrap: wrap;
  max-width: calc(100vw - 32px);
}
.bulk-bar__info { display: flex; align-items: center; gap: 8px; }
.bulk-bar__actions { display: flex; gap: 6px; flex-wrap: wrap; }
.bulk-bar .form-control-sm { height: 30px; padding: 4px 8px; font-size: 0.82rem; min-width: 150px; }
.bulk-bar .btn-outline-secondary { background: transparent; border-color: rgba(255,255,255,0.4); color: #fff; }
.bulk-bar .btn-outline-secondary:hover { background: rgba(255,255,255,0.12); }
.bulk-bar .btn-outline-danger { background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.4); color: #fff; }
.bulk-bar .btn-outline-danger:hover { background: #c62828; border-color: #c62828; }
.bulk-bar-enter-active, .bulk-bar-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.bulk-bar-enter-from, .bulk-bar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
@media (max-width: 600px) {
  .bulk-bar { left: 8px; right: 8px; transform: none; }
  .bulk-bar-enter-from, .bulk-bar-leave-to { transform: translateY(20px); }
}

/* ===== Sheet validation + ₽ suffix + aside ===== */
.task-sheet__title-input.is-invalid {
  border-bottom-color: #c62828 !important;
}
.task-sheet__field-error {
  color: #c62828;
  font-size: 0.78rem;
  margin-top: 4px;
}
.task-sheet__mini-input.is-invalid {
  border-color: #c62828 !important;
}
.task-sheet__money-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.task-sheet__money-input {
  flex: 1;
  padding-right: 28px !important;
}
.task-sheet__money-suffix {
  position: absolute;
  right: 10px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 600;
  pointer-events: none;
}
.task-sheet__aside-toggle { margin-left: auto; }

/* ===== Aside tabs (Approval / Chat) ===== */
.task-sheet__chat {
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}
.task-sheet__aside-pane { padding: 12px; }
.task-sheet__aside-pane--chat { padding: 0 !important; overflow: hidden; }
.task-sheet__aside-tabs {
  display: flex;
  border-bottom: 1px solid var(--md-sys-color-outline-variant, #e5e7eb);
  background: var(--md-sys-color-surface-container-low, #fafbfc);
  flex-shrink: 0;
}
.task-sheet__aside-tab {
  flex: 1;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant, #6b7280);
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}
.task-sheet__aside-tab:hover:not(:disabled) {
  background: var(--md-sys-color-surface-variant, rgba(0,0,0,0.03));
  color: var(--md-sys-color-on-surface);
}
.task-sheet__aside-tab.active {
  color: var(--md-sys-color-primary, #1976d2);
  border-bottom-color: var(--md-sys-color-primary, #1976d2);
  background: var(--md-sys-color-surface, #fff);
  font-weight: 600;
}
.task-sheet__aside-tab:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.task-sheet__aside-tab-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #f59e0b;
  margin-left: 4px;
  display: inline-block;
}
.task-sheet__aside-pane {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.task-sheet__aside-pane--chat { padding: 0; overflow: hidden; }

/* ===== Kanban — column + spacing parity with Leads kanban ===== */
.task-kanban-board {
  /* Stretch columns to fill the board height (default flex behaviour);
     parent .task-list-container--kanban already enables horizontal scroll. */
  align-items: stretch !important;
  min-height: 100% !important;
  min-width: max-content !important;
  gap: var(--space-3) !important;
  padding: var(--space-3) !important;
}
.task-kanban-column {
  /* `gap` requires a flex container — base rules don't set one, so
     declare it here. Without this, the gap silently does nothing. */
  display: flex !important;
  flex-direction: column !important;
  flex: 0 0 280px !important;
  width: 280px !important;
  gap: 10px !important;
  padding: var(--space-2) !important;
  background: var(--color-surface-2) !important;
  border: 0 !important;
  border-radius: var(--radius-md) !important;
  box-shadow: none !important;
}
.task-kanban-column--over {
  background: var(--color-primary-soft) !important;
  outline: 2px dashed var(--color-primary);
  outline-offset: -4px;
  box-shadow: none !important;
  transform: none !important;
}
.task-kanban-column__header {
  flex-direction: row !important;
  align-items: center !important;
  gap: var(--space-2) !important;
  margin-bottom: 0 !important;
  padding: var(--space-2) var(--space-3) !important;
  background: var(--color-surface) !important;
  border-radius: var(--radius-sm) !important;
  flex-shrink: 0 !important;
}
/* Title block: dot + label + count, single row. Override the original
   stacked h3/p layout so it matches `.kanban-header` in Leads. */
.task-kanban-column__title-wrap {
  flex: 1 1 auto !important;
  min-width: 0 !important;
  align-items: center !important;
}
.task-kanban-column__title-wrap > div {
  flex: 1 1 auto !important;
  min-width: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: var(--space-2) !important;
}
.task-kanban-column__title-wrap h3 {
  margin: 0 !important;
  font-size: var(--text-base) !important;
  font-weight: var(--fw-semibold) !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.task-kanban-column__title-wrap p {
  margin: 0 !important;
  flex-shrink: 0 !important;
  font-size: var(--text-xs) !important;
  font-weight: var(--fw-bold) !important;
  line-height: 1.2 !important;
  color: var(--color-text-muted) !important;
  background: var(--color-surface-3) !important;
  padding: 1px var(--space-2) !important;
  border-radius: var(--radius-pill) !important;
}
.task-kanban-column__list { gap: var(--space-2) !important; }
.task-kanban-card {
  padding: 8px 10px !important;
  border-radius: 8px !important;
}
.task-kanban-card__chips { margin-bottom: 4px !important; gap: 4px !important; }
.task-kanban-chip {
  padding: 1px 6px !important;
  font-size: 0.68rem !important;
  line-height: 1.4 !important;
  border-radius: 4px !important;
}
.task-kanban-card__title-row { margin-bottom: 4px !important; gap: 6px !important; }
.task-kanban-card__title-row h4 {
  font-size: 0.85rem !important;
  line-height: 1.2 !important;
}
.task-kanban-card__project,
.task-kanban-card__description,
.task-kanban-card__meta span,
.task-kanban-card__assignee span {
  font-size: 0.72rem !important;
  line-height: 1.3 !important;
}
.task-kanban-card__project { margin-bottom: 2px !important; }
.task-kanban-card__description {
  margin: 2px 0 4px !important;
  -webkit-line-clamp: 1 !important;
}
.task-kanban-card__meta {
  gap: 2px 8px !important;
  margin-bottom: 6px !important;
}
.task-kanban-card__meta strong,
.task-kanban-card__assignee strong {
  font-size: 0.74rem !important;
  line-height: 1.2 !important;
}
.task-kanban-card__footer { gap: 6px !important; }
.task-kanban-card__assignee { gap: 6px !important; }
.task-kanban-card__assignee .task-avatar { width: 22px !important; height: 22px !important; font-size: 0.65rem !important; }
.task-kanban-card__actions { gap: 2px !important; }
.task-kanban-card__actions .btn-icon { width: 24px !important; height: 24px !important; padding: 0 !important; font-size: 0.72rem !important; }
.task-kanban-column__empty {
  min-height: 0 !important;
  border: 2px dashed var(--color-border) !important;
  border-radius: var(--radius-sm) !important;
  padding: var(--space-5) var(--space-3) !important;
  font-size: var(--text-sm) !important;
  color: var(--color-text-muted) !important;
  background: transparent !important;
}
.task-kanban-column__empty br + * { display: none; } /* hide secondary line if any */

:global(:root[data-theme="dark"]) .tasks-view .task-sort-box__select,
:global(:root[data-theme="dark"]) .tasks-view .task-page-size-box__select,
:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-select__control,
:global(:root[data-theme="dark"]) .tasks-view .task-sort-box__dir,
:global(:root[data-theme="dark"]) .tasks-view .task-subtoolbar__field .form-control,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal .form-control,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal .form-select,
:global(:root[data-theme="dark"]) .tasks-view .task-modal .form-control,
:global(:root[data-theme="dark"]) .tasks-view .task-modal .form-select,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__control-select,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__mini-input,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__description {
  background: #101a2c;
  border-color: #273449;
  color: #eef4ff;
  color-scheme: dark;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sort-box__select:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-page-size-box__select:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-select__control:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal .form-control:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal .form-select:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-modal .form-control:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-modal .form-select:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__control-select:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__mini-input:focus,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__description:focus {
  background: #111f35;
  border-color: #4f77ff;
  box-shadow: 0 0 0 3px rgba(79, 119, 255, 0.18);
}

:global(:root[data-theme="dark"]) .tasks-view .task-sort-box i,
:global(:root[data-theme="dark"]) .tasks-view .task-toolbar-select span,
:global(:root[data-theme="dark"]) .tasks-view .task-page-size-box span,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__control-icon--slate {
  color: #8f9bb2;
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-shell,
:global(:root[data-theme="dark"]) .tasks-view .task-list-container--kanban,
:global(:root[data-theme="dark"]) .tasks-view .auction-shell__body,
:global(:root[data-theme="dark"]) .tasks-view .rules-shell__body {
  background: transparent;
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line {
  background: #0f1726;
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line:hover {
  background: #131d30;
  border-color: #314056;
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line--completed {
  background: rgba(23, 77, 49, 0.48);
  border-color: rgba(72, 158, 109, 0.56);
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line--completed:hover {
  background: rgba(28, 91, 58, 0.58);
  border-color: rgba(92, 182, 128, 0.62);
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line--cancelled {
  background: rgba(99, 29, 29, 0.42);
  border-color: rgba(196, 86, 86, 0.58);
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line--cancelled:hover {
  background: rgba(118, 35, 35, 0.5);
  border-color: rgba(214, 99, 99, 0.64);
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line--deferred {
  background: rgba(70, 78, 96, 0.42);
  border-color: rgba(104, 117, 143, 0.52);
}

:global(:root[data-theme="dark"]) .tasks-view .task-list-line--deferred:hover {
  background: rgba(82, 91, 111, 0.52);
  border-color: rgba(122, 136, 166, 0.62);
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column {
  background: #0f1726;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column--over {
  background: #131d30;
  border-color: #5e86ff;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column__create,
:global(:root[data-theme="dark"]) .tasks-view .task-kanban-column__empty {
  background: #121d30;
  border-color: #273449;
  color: #8f9bb2;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card {
  background: #111a2c;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-card:hover {
  background: #152039;
  border-color: #334561;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card {
  background: #0f1726;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card:hover {
  background: #131d30;
  border-color: #334561;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card.auction-awarded {
  background: #112319;
  border-color: #28543d;
  opacity: 1;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card.auction-cancelled {
  background: #2a1518;
  border-color: #5c3136;
  opacity: 0.86;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-subtask,
:global(:root[data-theme="dark"]) .tasks-view .auction-subtask-details {
  background: #121d30;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card .btn-primary {
  background: #121d30;
  border-color: #32425b;
  color: #eef4ff;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card .btn-primary:hover,
:global(:root[data-theme="dark"]) .tasks-view .auction-card .btn-primary:focus {
  background: #18253b;
  border-color: #42567a;
  color: #ffffff;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card .btn-success {
  background: #eef4ff;
  border-color: #eef4ff;
  color: #0f1726;
}

:global(:root[data-theme="dark"]) .tasks-view .auction-card .btn-success:hover,
:global(:root[data-theme="dark"]) .tasks-view .auction-card .btn-success:focus {
  background: #dfe9ff;
  border-color: #dfe9ff;
  color: #0f1726;
}

:global(:root[data-theme="dark"]) .tasks-view .rules-block,
:global(:root[data-theme="dark"]) .tasks-view .rules-shell__body,
:global(:root[data-theme="dark"]) .tasks-view .rules-table,
:global(:root[data-theme="dark"]) .tasks-view .rules-table thead th,
:global(:root[data-theme="dark"]) .tasks-view .rules-table tbody td {
  background: transparent;
}

:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal,
:global(:root[data-theme="dark"]) .tasks-view .task-modal,
:global(:root[data-theme="dark"]) .tasks-view .modal-content,
:global(:root[data-theme="dark"]) .tasks-view .modal-glass {
  background: #0f1726;
  border-color: #243044;
  box-shadow: 0 26px 64px rgba(2, 8, 23, 0.5);
}

:global(:root[data-theme="dark"]) .tasks-view .modal-header,
:global(:root[data-theme="dark"]) .tasks-view .modal-footer,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal__header,
:global(:root[data-theme="dark"]) .tasks-view .task-filters-modal__footer,
:global(:root[data-theme="dark"]) .tasks-view .modal-glass-header,
:global(:root[data-theme="dark"]) .tasks-view .modal-glass-footer {
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .task-modal.task-sheet {
  background: #0c1421;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__main,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__header {
  background: #0c1421;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__icon-btn {
  color: #8f9bb2;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__icon-btn:hover {
  background: #152039;
  color: #f3f7ff;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__control-strip {
  background: #101a2c;
  border-color: #243044;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__detail-card,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__summary-item {
  background: #101a2c;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__notice--info {
  background: rgba(49, 111, 255, 0.16);
  color: #9db7ff;
}

:global(:root[data-theme="dark"]) .tasks-view .task-sheet__chat {
  background: #0f1726;
}

:global(:root[data-theme="dark"]) .tasks-view .task-avatar,
:global(:root[data-theme="dark"]) .tasks-view .task-avatar--sm,
:global(:root[data-theme="dark"]) .tasks-view .task-avatar--md,
:global(:root[data-theme="dark"]) .tasks-view .task-sheet__assignee-avatar {
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-chip--category {
  background: rgba(210, 142, 61, 0.18);
  color: #ffca8a;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-chip--low {
  background: rgba(75, 153, 103, 0.18);
  color: #8fd0a3;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-chip--normal {
  background: rgba(73, 118, 244, 0.18);
  color: #9db7ff;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-chip--high {
  background: rgba(177, 171, 29, 0.18);
  color: #e3de76;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-chip--urgent {
  background: rgba(175, 75, 75, 0.2);
  color: #f2abab;
}

:global(:root[data-theme="dark"]) .tasks-view .task-kanban-chip--auction {
  background: rgba(149, 75, 175, 0.18);
  color: #d7a4f0;
}

:global(:root[data-theme="dark"]) .tasks-view .badge-light,
:global(:root[data-theme="dark"]) .tasks-view .badge-outline-secondary,
:global(:root[data-theme="dark"]) .tasks-view .badge-secondary {
  background: #152039;
  color: #d4deef;
  border-color: #273449;
}

/* Glass modal overlay */
.modal-overlay {
  backdrop-filter: blur(4px);
}

.modal-content {
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border-light, rgba(255,255,255,0.3));
}

/* Confirm overlay */
.confirm-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
  backdrop-filter: blur(4px);
}

.modal-glass {
  width: 480px;
  max-width: 90vw;
  background: var(--md-sys-color-surface-thick, var(--md-sys-color-surface));
  backdrop-filter: var(--glass-blur);
  border-radius: 16px;
  border: 1px solid var(--glass-border-light, rgba(255,255,255,0.3));
  box-shadow: var(--shadow-md, 0 8px 32px rgba(0,0,0,0.2));
  display: flex;
  flex-direction: column;
  animation: modalSlideIn 0.2s ease;
}

.modal-glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.modal-glass-body {
  padding: 16px 20px;
}

.modal-glass-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.btn-ghost {
  background: transparent;
  border: none;
}

@keyframes modalSlideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
<style>
:root[data-theme="dark"] .tasks-view {
  color: #eef4ff;
}

:root[data-theme="dark"] .tasks-view .task-module-topbar,
:root[data-theme="dark"] .tasks-view .task-module-main,
:root[data-theme="dark"] .tasks-view .task-list-container,
:root[data-theme="dark"] .tasks-view .task-list-shell,
:root[data-theme="dark"] .tasks-view .task-list-container--kanban,
:root[data-theme="dark"] .tasks-view .auction-shell,
:root[data-theme="dark"] .tasks-view .rules-shell,
:root[data-theme="dark"] .tasks-view .rules-shell__header,
:root[data-theme="dark"] .tasks-view .rules-shell__body,
:root[data-theme="dark"] .tasks-view .rules-block,
:root[data-theme="dark"] .tasks-view .task-filters-modal,
:root[data-theme="dark"] .tasks-view .task-modal,
:root[data-theme="dark"] .tasks-view .task-modal.task-sheet,
:root[data-theme="dark"] .tasks-view .modal-content,
:root[data-theme="dark"] .tasks-view .modal-glass,
:root[data-theme="dark"] .tasks-view .task-sheet__main,
:root[data-theme="dark"] .tasks-view .task-sheet__header,
:root[data-theme="dark"] .tasks-view .task-sheet__chat,
:root[data-theme="dark"] .tasks-view .task-sheet__chat-empty,
:root[data-theme="dark"] .tasks-view .task-sheet__control-strip,
:root[data-theme="dark"] .tasks-view .task-sheet__detail-card,
:root[data-theme="dark"] .tasks-view .task-sheet__summary-item {
  background: #0f1726 !important;
  border-color: #243044 !important;
  color: #eef4ff !important;
}

:root[data-theme="dark"] .tasks-view .task-module-topbar__row,
:root[data-theme="dark"] .tasks-view .task-module-topbar__meta,
:root[data-theme="dark"] .tasks-view .task-sheet__header,
:root[data-theme="dark"] .tasks-view .task-sheet__chat,
:root[data-theme="dark"] .tasks-view .rules-shell__header,
:root[data-theme="dark"] .tasks-view .modal-header,
:root[data-theme="dark"] .tasks-view .modal-footer,
:root[data-theme="dark"] .tasks-view .task-filters-modal__header,
:root[data-theme="dark"] .tasks-view .task-filters-modal__footer,
:root[data-theme="dark"] .tasks-view .modal-glass-header,
:root[data-theme="dark"] .tasks-view .modal-glass-footer {
  border-color: #243044 !important;
}

:root[data-theme="dark"] .tasks-view .task-module-topbar__title-group h1,
:root[data-theme="dark"] .tasks-view .task-module-main__headline h2,
:root[data-theme="dark"] .tasks-view .rules-shell__headline h3,
:root[data-theme="dark"] .tasks-view .task-sheet__title,
:root[data-theme="dark"] .tasks-view .task-sheet__chat-empty,
:root[data-theme="dark"] .tasks-view .task-list-line__title-wrap h3,
:root[data-theme="dark"] .tasks-view .task-list-line__cell > strong,
:root[data-theme="dark"] .tasks-view .auction-title,
:root[data-theme="dark"] .tasks-view .rules-block__header strong,
:root[data-theme="dark"] .tasks-view .rules-table tbody td,
:root[data-theme="dark"] .tasks-view .rules-table thead th {
  color: #eef4ff !important;
}

:root[data-theme="dark"] .tasks-view .text-muted,
:root[data-theme="dark"] .tasks-view .small.text-muted,
:root[data-theme="dark"] .tasks-view .task-module-topbar__hint,
:root[data-theme="dark"] .tasks-view .task-module-topbar__count,
:root[data-theme="dark"] .tasks-view .task-list-line__title-wrap p,
:root[data-theme="dark"] .tasks-view .task-list-line__cell > span,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__field span,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__meta,
:root[data-theme="dark"] .tasks-view .rules-shell__headline p,
:root[data-theme="dark"] .tasks-view .rules-block__header span,
:root[data-theme="dark"] .tasks-view .auction-desc,
:root[data-theme="dark"] .tasks-view .auction-bids,
:root[data-theme="dark"] .tasks-view .task-sheet__breadcrumbs,
:root[data-theme="dark"] .tasks-view .task-sheet__detail-card span,
:root[data-theme="dark"] .tasks-view .task-sheet__summary-item span {
  color: #8f9bb2 !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line,
:root[data-theme="dark"] .tasks-view .task-kanban-column,
:root[data-theme="dark"] .tasks-view .task-kanban-card,
:root[data-theme="dark"] .tasks-view .auction-card,
:root[data-theme="dark"] .tasks-view .auction-subtask,
:root[data-theme="dark"] .tasks-view .auction-subtask-details {
  background: #111a2c !important;
  border-color: #243044 !important;
  color: #eef4ff !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line:hover,
:root[data-theme="dark"] .tasks-view .task-kanban-card:hover,
:root[data-theme="dark"] .tasks-view .auction-card:hover {
  background: #152039 !important;
  border-color: #334561 !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line--completed {
  background: #112319 !important;
  border-color: #28543d !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line--cancelled {
  background: #2a1518 !important;
  border-color: #5c3136 !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line--deferred {
  background: #18202e !important;
  border-color: #3a465b !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line__checkbox {
  background: #101a2c !important;
  border-color: #3a465b !important;
  color: #0f1726 !important;
}

:root[data-theme="dark"] .tasks-view .task-list-line__checkbox--done {
  background: #eef4ff !important;
  border-color: #eef4ff !important;
}

:root[data-theme="dark"] .tasks-view .task-sort-box,
:root[data-theme="dark"] .tasks-view .task-page-size-box,
:root[data-theme="dark"] .tasks-view .task-filter-pill,
:root[data-theme="dark"] .tasks-view .task-toolbar-icon-btn,
:root[data-theme="dark"] .tasks-view .task-module-topbar__create-btn,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__field,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__sort,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__toggle,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__action,
:root[data-theme="dark"] .tasks-view .task-sheet__icon-btn {
  background: #152039 !important;
  border-color: #273449 !important;
  color: #eef4ff !important;
  box-shadow: none !important;
}

:root[data-theme="dark"] .tasks-view .task-module-topbar__create-btn,
:root[data-theme="dark"] .tasks-view .task-subtoolbar__action--primary {
  background: #eef4ff !important;
  border-color: #eef4ff !important;
  color: #0f1726 !important;
}

:root[data-theme="dark"] .tasks-view .task-sort-box__select,
:root[data-theme="dark"] .tasks-view .task-page-size-box__select,
:root[data-theme="dark"] .tasks-view .task-sheet select,
:root[data-theme="dark"] .tasks-view .task-sheet input,
:root[data-theme="dark"] .tasks-view .task-sheet textarea,
:root[data-theme="dark"] .tasks-view .form-control,
:root[data-theme="dark"] .tasks-view .form-select {
  background: #101a2c !important;
  border-color: #273449 !important;
  color: #eef4ff !important;
  color-scheme: dark;
}

:root[data-theme="dark"] .tasks-view .task-sheet textarea::placeholder,
:root[data-theme="dark"] .tasks-view .form-control::placeholder {
  color: #7f8da8 !important;
}

:root[data-theme="dark"] .tasks-view .badge,
:root[data-theme="dark"] .tasks-view .badge-light,
:root[data-theme="dark"] .tasks-view .badge-secondary,
:root[data-theme="dark"] .tasks-view .badge-outline-secondary {
  background: #152039 !important;
  border-color: #273449 !important;
  color: #d4deef !important;
}

:root[data-theme="dark"] .tasks-view .auction-card .btn-primary,
:root[data-theme="dark"] .tasks-view .auction-card .btn-success,
:root[data-theme="dark"] .tasks-view .auction-card .btn-outline-secondary {
  box-shadow: none !important;
}

:root[data-theme="dark"] .tasks-view .auction-card .btn-primary {
  background: #152039 !important;
  border-color: #273449 !important;
  color: #eef4ff !important;
}

:root[data-theme="dark"] .tasks-view .auction-card .btn-success {
  background: #eef4ff !important;
  border-color: #eef4ff !important;
  color: #0f1726 !important;
}

:root[data-theme="dark"] .tasks-view .task-sheet__notice--info {
  background: rgba(49, 111, 255, 0.16) !important;
  color: #9db7ff !important;
}
</style>
