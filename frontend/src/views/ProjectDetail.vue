<template>
  <div class="project-detail-view h-100 d-flex flex-column">
    <!-- Consolidated Header -->
    <div class="unified-header flex-shrink-0">
       <div class="unified-header-inner">
          <div class="unified-header-left">
             <button class="unified-back-btn" @click="$router.go(-1)">
                <i class="fas fa-arrow-left"></i>
             </button>
             <div class="unified-title-group">
                <h1 class="unified-project-name">{{ project.title }}</h1>
             </div>
          </div>

          <nav
             class="unified-nav"
             @keydown="onTabKeydown"
             role="tablist"
             aria-label="Разделы проекта"
          >
             <button
                v-for="tab in tabs"
                :key="tab.id"
                :id="`tab-${tab.id}`"
                @click="selectTab(tab.id)"
                class="unified-nav-item"
                :class="{ active: activeTab === tab.id }"
                role="tab"
                :aria-selected="activeTab === tab.id ? 'true' : 'false'"
                :aria-controls="`panel-${tab.id}`"
                :tabindex="activeTab === tab.id ? 0 : -1"
             >
                <span>{{ tab.name }}</span>
                <span
                  v-if="tab.id === 'problems' && dealHealthActiveCount"
                  class="unified-nav-count"
                >
                  {{ dealHealthActiveCount }}
                </span>
             </button>
          </nav>

          <div class="unified-nav-hint">
             <i class="fas fa-arrows-left-right"></i>
             <span>Проведите вкладки</span>
          </div>

          <div class="unified-header-right">
             <span class="badge" :class="getStatusClass(project.status)">
                {{ getStatusText(project.status) }}
             </span>
             <button class="unified-action-btn" @click="editProject" title="Редактировать">
                <i class="fas fa-edit"></i>
             </button>
             <button class="unified-action-btn unified-action-btn--danger" @click="deleteProject" title="Удалить">
                <i class="fas fa-trash"></i>
             </button>
          </div>
       </div>
    </div>

    <!-- Content Area -->
    <div class="flex-grow-1 overflow-hidden position-relative">
       <div ref="contentScrollRef" class="h-100 overflow-auto scroll-container p-1">
          <Overview v-if="activeTab === 'overview'" :state="state" />
          <Contracts v-if="activeTab === 'contracts'" :state="state" />
          <Products v-if="activeTab === 'products'" :state="state" />
          <Stages v-if="activeTab === 'stages'" :state="state" />
          <GanttPanel v-if="activeTab === 'gantt'" :state="state" />
          <Dejure v-if="activeTab === 'dejure'" :state="state" />
          <Defacto v-if="activeTab === 'defacto'" :state="state" />
       </div>
    </div>

    <Files v-if="activeTab === 'files'" :state="state" />
    <Problems v-if="activeTab === 'problems'" :state="state" />
    <Letters v-if="activeTab === 'letters'" :state="state" />

    <Modals :state="state" />
  </div>
</template>

<script>
/**
 * ProjectDetail view (decomposed shell).
 *
 * Previously a monolithic ~8500 LOC file. Now a thin composition shell:
 *  - All state, refs, computeds, methods, watchers and lifecycle hooks live in
 *    `views/projectDetail/composables/useProjectDetailState.js` (the entire
 *    former `setup()` body, copied verbatim).
 *  - Each visible tab and the modal cluster live in
 *    `views/projectDetail/parts/*.vue`. Every part receives the whole state
 *    object as a single `state` prop and spreads it in `setup()` so the part's
 *    template can use the original identifiers (`project`, `activeTab`,
 *    `tabs`, helpers like `formatDate`/`getStatusClass`, etc.) unchanged.
 *  - CSS stays in this file but is now non-scoped so it cascades into the
 *    child parts (the original `<style scoped>` would not have, which is the
 *    same pattern used by the decomposed `Tasks.vue`). Class names in the
 *    sheet are domain-prefixed (`.unified-*`, `.kpi-*`, `.task-list-*`,
 *    `.dejure-*`, `.defacto-*`, `.deal-files-*`, `.modal-glass`, etc.) so
 *    collisions with other views are unlikely.
 */
import { useProjectDetailState } from './projectDetail/composables/useProjectDetailState'
import Overview from './projectDetail/parts/Overview.vue'
import Contracts from './projectDetail/parts/Contracts.vue'
import Products from './projectDetail/parts/Products.vue'
import Stages from './projectDetail/parts/Stages.vue'
import GanttPanel from './projectDetail/parts/GanttPanel.vue'
import Dejure from './projectDetail/parts/Dejure.vue'
import Defacto from './projectDetail/parts/Defacto.vue'
import Files from './projectDetail/parts/Files.vue'
import Problems from './projectDetail/parts/Problems.vue'
import Letters from './projectDetail/parts/Letters.vue'
import Modals from './projectDetail/parts/Modals.vue'
// Activity.vue (полноэкранный таймлайн) — оставлен в parts/, но больше
// не подключён: таймлайн отображается в правой колонке Overview.

export default {
  name: 'ProjectDetail',
  components: {
    Overview, Contracts, Products, Stages, GanttPanel, Dejure, Defacto,
    Files, Problems, Letters, Modals
  },
  setup() {
    const state = useProjectDetailState()
    // Header template references unwrapped identifiers directly (project,
    // tabs, activeTab, onTabKeydown, ...). Returning both `state` (for the
    // part components) and a shallow spread lets the shell template use the
    // same identifiers it always used. The `contentScrollRef` template ref
    // also needs to be reachable by name on the rendered component.
    return { state, ...state }
  }
}
</script>

<style>
/* Base utilities */
.fw-500 { font-weight: 500; }
.fw-600 { font-weight: 600; }
.text-right { text-align: right; }
.cursor-pointer { cursor: pointer; }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-sidebar-content { grid-template-columns: 280px 1fr; }
.hover-bg-light:hover { background-color: var(--md-sys-color-surface-container-low); }
.transition-base { transition: all 0.2s; }
.sticky-top { position: sticky; top: 0; z-index: 10; }
.bg-surface { background-color: var(--md-sys-color-surface); }

.project-gantt-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.project-gantt-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 16px 0;
}

.project-gantt-switch {
  display: inline-flex;
  padding: 4px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 999px;
  background: var(--md-sys-color-surface-container-low);
  gap: 4px;
}

.project-gantt-switch-btn {
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
}

.project-gantt-switch-btn.active {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-primary);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
}

.project-gantt-content {
  flex: 1 1 auto;
  min-height: 0;
}

.project-gantt-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}

.deal-files-type-bar {
  background: var(--md-sys-color-surface);
}

.deal-files-type-switcher {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.deal-files-type-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-low);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.16s ease;
}

.deal-files-type-chip:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}

.deal-files-type-chip.active {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
  border-color: rgba(59, 130, 246, 0.22);
}

.deal-files-explorer {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.deal-files-tree-panel,
.deal-files-table-panel {
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface);
  border-radius: 14px;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.deal-files-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.deal-files-panel-head--table {
  padding-bottom: 12px;
}

.deal-files-panel-title {
  margin-top: 2px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.deal-files-tree-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.deal-files-tree-scroll {
  flex: 1;
  overflow: auto;
  padding: 10px 8px 12px;
}

.deal-tree-group-label {
  margin: 10px 8px 6px;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--md-sys-color-on-surface-variant);
}

.deal-tree-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.deal-tree-toggle-btn {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.16s ease, color 0.16s ease;
}

.deal-tree-toggle-btn:hover {
  background: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-on-surface);
}

.deal-tree-toggle-btn.is-placeholder {
  cursor: default;
  pointer-events: none;
  opacity: 0;
}

.deal-tree-node {
  width: 100%;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  padding: 8px 12px;
  border-radius: 10px;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  text-align: left;
  transition: background 0.16s ease, color 0.16s ease;
}

.deal-tree-node:hover {
  background: var(--md-sys-color-surface-container-low);
}

.deal-tree-node.active {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
}

.deal-tree-node span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.deal-tree-node--root {
  font-weight: 600;
}

.deal-files-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.deal-files-table {
  width: 100%;
}

.deal-files-size-col {
  width: 120px;
}

.deal-files-modified-col {
  width: 170px;
}

.deal-files-actions-col {
  width: 104px;
}

.deal-file-link {
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  text-align: left;
  color: inherit;
  min-width: 0;
  cursor: pointer;
}

.deal-file-link--table {
  padding: 0;
}

.deal-file-link span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* =============================================
   Unified Header (Project Name + Tabs + Actions)
   ============================================= */

.unified-header {
  padding: 0 20px;
  background: var(--md-sys-color-surface);
  backdrop-filter: var(--glass-blur);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--glass-border-light, rgba(255, 255, 255, 0.3));
  margin-bottom: 16px;
}

.unified-header-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 56px;
}

/* Left: Back + Title */
.unified-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-shrink: 1;
}

.unified-back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
  transition: all 0.15s;
  flex-shrink: 0;
}

.unified-back-btn:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}

.unified-title-group {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.unified-project-name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unified-obj-name {
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100ch;
  flex-shrink: 1;
  min-width: 0;
}

/* Center: Navigation */
.unified-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
  flex-shrink: 0;
  outline: none;
}

.unified-nav-hint {
  display: none;
}

.unified-nav-item {
  position: relative;
  padding: 8px 14px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
  font-size: 0.82rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s;
  white-space: nowrap;
  letter-spacing: 0.01em;
}

.unified-nav-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  margin-left: 6px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.14);
  color: #dc2626;
  font-size: 0.72rem;
  font-weight: 700;
}

.unified-nav-item:hover {
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-container-low);
}

.unified-nav-item.active {
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
  font-weight: 600;
}

.unified-nav-item:focus-visible {
  outline: 2px solid var(--md-sys-color-primary);
  outline-offset: 1px;
}

/* Right: Status + Actions */
.unified-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  margin-left: 8px;
}

.unified-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
  transition: all 0.15s;
}

.unified-action-btn:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}

.unified-action-btn--danger:hover {
  background: var(--color-danger-container, #ffebee);
  color: var(--color-danger, #c62828);
  border-color: var(--color-danger, #c62828);
}

/* Legacy aliases kept for backward compat in other tabs */
.project-header {
  display: none;
}

.project-tabs {
  display: none;
}

/* Card Title */
.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

/* .overview-layout больше не используется — Overview переехал на
   .project-overview-shell (единая «коробка» как у лидов). См. ниже. */

.overview-kpis {
  align-items: stretch;
}

.overview-main {
  grid-template-columns: minmax(320px, 1fr) minmax(360px, 1fr);
  min-height: 0;
}

.glass-card {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--glass-border-light, rgba(255, 255, 255, 0.3));
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(12px) saturate(130%);
  -webkit-backdrop-filter: blur(12px) saturate(130%);
}

.kpi-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kpi-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.kpi-card-label {
  font-size: 0.82rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--md-sys-color-on-surface-variant);
}

.kpi-card-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.kpi-progress {
  height: 8px;
  border-radius: 999px;
  background: var(--md-sys-color-surface-container);
  overflow: hidden;
}

.kpi-progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.25s ease;
}

.kpi-progress-fill--primary {
  background: linear-gradient(90deg, var(--md-sys-color-primary), #4a90ff);
}

.contracts-link-controls {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 240px;
}

.contracts-linker-popover {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  padding: 10px;
  background: var(--md-sys-color-surface-container-low);
}

.estimate-toolbar {
  background: var(--md-sys-color-surface-container-low);
}

.estimate-search {
  flex: 1;
  min-width: 240px;
}

.estimate-sort {
  max-width: 210px;
}

.estimate-add-btn {
  margin-left: auto;
  white-space: nowrap;
}

.deal-product-invoices-col {
  min-width: 148px;
  max-width: 220px;
}

.deal-product-invoice-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 210px;
}

.deal-product-invoice-chip {
  display: inline-flex;
  align-items: center;
  max-width: 72px;
  min-height: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.14);
  border: 1px solid rgba(245, 158, 11, 0.28);
  color: #92400e;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.deal-product-invoice-chip--more {
  background: rgba(15, 23, 42, 0.08);
  border-color: rgba(15, 23, 42, 0.12);
  color: var(--md-sys-color-on-surface-variant);
}

:global(:root[data-theme="dark"]) .glass-card {
  background: var(--md-sys-color-surface);
  border-color: var(--glass-border-light, rgba(255, 255, 255, 0.12));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}

:global(:root[data-theme="dark"]) .contracts-linker-popover,
:global(:root[data-theme="dark"]) .estimate-toolbar {
  background: var(--md-sys-color-surface-container);
  border-color: var(--glass-border-light, rgba(255, 255, 255, 0.12));
}

/* Info Grid */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.info-row:last-child {
  border-bottom: none;
}

.separator {
  height: 1px;
  background: var(--md-sys-color-outline-variant);
}

/* ============================================================
   Единая «коробка» Обзора (1-в-1 с .lead-detail-body у лидов).
   Обе колонки + все .card внутри получают одну общую рамку 12px,
   индивидуальные рамки/тени снимаются.
   ============================================================ */
.project-overview-shell {
  border: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
  border-radius: 12px;
  background: var(--md-sys-color-surface, #fff);
  overflow: hidden;
  /* scroll-container оборачивает Overview с p-1 (4px), у лидов это
     убирается через .lead-detail-body .scroll-container { padding:0 }
     — у нас shell ВНУТРИ scroll-container, поэтому компенсируем
     negative-margin'ом, чтобы рамка прилегала к самой границе. */
  margin: -4px;
  height: calc(100% + 8px);
}
.project-overview-shell .card,
.project-overview-shell .dashboard-left .card,
.project-overview-shell .dashboard-right,
.project-overview-shell .glass-card,
.project-overview-shell .composer {
  border: none;
  border-radius: 0;
  /* !important нужен, чтобы перебить .card { box-shadow: var(--shadow-sm) }
     из main.css (там без префикса селектора, повышенная специфичность
     даёт shell-селектор, но дочерние .card.composer внутри scoped-стилей
     DealTimeline могут перебивать обратно). */
  box-shadow: none !important;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
/* НЕ задаём grid-template-columns — наследуем из main.css `450px 1fr`,
   ровно как у лидов. Иначе колонки превращаются в 50:50, что и было
   причиной "разной ширины блоков с лидом". */
.project-overview-shell .dashboard-grid {
  gap: 0;
  height: 100%;
}
.project-overview-shell .dashboard-grid .dashboard-right {
  border-left: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
}
.project-overview-shell .dashboard-left {
  gap: 0;
}
.project-overview-shell .dashboard-left > .card + .card {
  border-top: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
}

/* В контексте Overview-shell базовый info-grid/info-row из main.css
   (gap:12px, align-items:baseline, без padding/border) — но локальные
   правила .info-row { padding:8px 0; border-bottom } ниже в этом же
   файле перебивают их для других вкладок ProjectDetail. Здесь отменяем
   эти переопределения, чтобы строки выглядели как у лидов. */
.project-overview-shell .info-grid {
  gap: 12px;
}
.project-overview-shell .info-row {
  align-items: baseline;
  padding: 0;
  border-bottom: none;
}

/* Блок «Привязанные ГИПы» встроен в общую info-grid — без подложки,
   без рамки. */
.project-gip-actions {
  padding-top: 4px;
}
.project-gip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 0;
}

@media (max-width: 992px) {
  .project-overview-shell .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .project-overview-shell .dashboard-grid .dashboard-right {
    border-left: none;
    border-top: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
  }
}

/* ============================================================
   Inline-edit стиль (тот же, что в LeadDetail)
   ============================================================ */
.info-row--editable {
  cursor: text;
  border-radius: 6px;
  padding: 2px 6px;
  margin: 0 -6px;
  transition: background 0.12s ease;
}
.info-row--editable:hover {
  background: var(--md-sys-color-surface-container-low, rgba(15, 23, 42, 0.04));
}
.info-row--editable:hover .info-row__value::after {
  content: '\f303';  /* fa-pen */
  font-family: 'Font Awesome 6 Free';
  font-weight: 900;
  margin-left: 8px;
  font-size: 0.7rem;
  opacity: 0.45;
}
.info-edit-input {
  flex: 1;
  min-width: 0;
  max-width: 60%;
  margin-left: auto;
  text-align: right;
  padding: 3px 8px;
  border: 1px solid var(--md-sys-color-primary, #1976d2);
  border-radius: 6px;
  font: inherit;
  font-weight: 500;
  background: var(--md-sys-color-surface, #fff);
  color: inherit;
  outline: none;
}
.info-edit-input:focus {
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.15);
}
.info-edit-input:disabled { opacity: 0.6; }

/* ============================================================
   Финансовый мини-виджет в шапке правой колонки Обзора
   3 цифры строкой + единая плашка-прогресс под ними.
   ============================================================ */
.project-money-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.project-money-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.project-money-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.project-money-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--md-sys-color-on-surface-variant);
}
.project-money-value {
  font-size: 1.05rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.project-money-progress {
  position: relative;
  height: 8px;
  border-radius: 999px;
  /* Серый = неоплаченная часть (фон всей плашки). */
  background: var(--md-sys-color-surface-container-high, rgba(15, 23, 42, 0.12));
  overflow: hidden;
}
.project-money-progress__fill {
  /* Зелёный = оплаченная часть, ширина = paymentProgressPercent%. */
  position: absolute;
  inset: 0 auto 0 0;
  background: var(--color-success, #2e7d32);
  border-radius: 999px;
  transition: width 0.25s ease;
}

/* Tables */
.table-container {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  overflow: hidden;
}

.contracts-table-container {
  overflow-x: auto;
}

.contracts-table-container .table {
  min-width: 520px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
}

.table th {
  background: var(--md-sys-color-surface-container);
  padding: 10px 12px;
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--md-sys-color-on-surface-variant);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  vertical-align: middle;
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover {
  background: var(--md-sys-color-surface-container-low);
}

.table tfoot {
  background: var(--md-sys-color-surface-container);
}

.table tfoot td {
  padding: 12px;
  font-weight: 600;
}

/* Status Badges */
.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.badge-sm {
  padding: 3px 8px;
  font-size: 0.7rem;
}

.badge-success { background: var(--color-success-container, #e8f5e9); color: var(--color-success, #2e7d32); }
.badge-primary { background: var(--md-sys-color-primary-container, #e3f2fd); color: var(--md-sys-color-primary, #1565c0); }
.badge-warning { background: var(--color-warning-container, #fff3e0); color: var(--color-warning, #e65100); }
.badge-danger { background: var(--color-danger-container, #ffebee); color: var(--color-danger, #c62828); }
.badge-info { background: var(--color-info-container, #e1f5fe); color: var(--color-info, #0277bd); }
.badge-secondary { background: var(--md-sys-color-surface-container, #eceff1); color: var(--md-sys-color-on-surface-variant, #546e7a); }
.badge-outline { background: transparent; border: 1px solid var(--md-sys-color-outline); color: var(--md-sys-color-on-surface-variant); }

/* Stat Box */
.stat-box {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  background: var(--md-sys-color-surface-container-low);
}

/* Product Row (Defacto) */
.product-row {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.product-header {
  border-radius: 8px 8px 0 0;
}

.product-body {
  border-radius: 0 0 8px 8px;
}

.icon-box {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
}

/* Progress Bar */
.progress-bar {
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Subcontractor/Stage Cards */
.bg-primary-container {
  background: var(--md-sys-color-primary-container) !important;
}

.border-primary {
  border-color: var(--md-sys-color-primary) !important;
}

/* Button Icon */
.btn-icon {
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: transparent;
  border: 1px solid var(--md-sys-color-outline-variant);
  cursor: pointer;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: var(--md-sys-color-surface-container);
}

.btn-icon.text-danger {
  color: var(--color-danger, #c62828);
}

.btn-icon.text-danger:hover {
  background: var(--color-danger-container, #ffebee);
}

/* Modal improvements */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border-light, rgba(255, 255, 255, 0.3));
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  animation: modalSlideIn 0.2s ease;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.modal-header h4 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.modal-body {
  padding: 20px 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 1.1rem;
  padding: 4px;
}

/* Card Header */
.card-header {
  background: var(--md-sys-color-surface-container-low);
  backdrop-filter: var(--glass-blur);
}

/* Text Colors */
.text-primary { color: var(--md-sys-color-primary); }
.text-success { color: var(--color-success, #2e7d32); }
.text-danger { color: var(--color-danger, #c62828); }
.text-warning { color: var(--color-warning, #e65100); }
.text-muted { color: var(--md-sys-color-on-surface-variant); }
.text-light-gray { color: var(--md-sys-color-outline-variant, #bdbdbd); }

/* Spinner */
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Scrollbar */
.scroll-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.scroll-container::-webkit-scrollbar-track {
  background: transparent;
}

.scroll-container::-webkit-scrollbar-thumb {
  background: var(--md-sys-color-outline-variant);
  border-radius: 4px;
}

.scroll-container::-webkit-scrollbar-thumb:hover {
  background: var(--md-sys-color-outline);
}

/* Confirm / Glass Modal (Teleported) */
.confirm-overlay {
  z-index: 2100;
}

.modal-glass {
  width: 480px;
  max-width: 90vw;
  background: var(--md-sys-color-surface-thick, var(--md-sys-color-surface));
  backdrop-filter: var(--glass-blur);
  border-radius: 16px;
  border: 1px solid var(--glass-border-light, rgba(255, 255, 255, 0.3));
  box-shadow: var(--shadow-md, 0 8px 32px rgba(0, 0, 0, 0.2));
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

.stage-close-modal {
  width: 440px;
}

.stage-close-warning {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--color-warning-container, #fff3e0);
  color: var(--color-warning, #e65100);
  border: 1px solid rgba(230, 81, 0, 0.18);
  font-size: 0.9rem;
}

.stage-close-input--warning {
  border-color: var(--color-warning, #e65100) !important;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.12);
}

.btn-ghost {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 8px;
  transition: background 0.15s;
}

.btn-ghost:hover {
  background: var(--md-sys-color-surface-container);
}

/* =============================================
   DE-JURE TAB — Modern SaaS Redesign
   ============================================= */

.dejure-layout {
  gap: 0;
}

/* Row 1: Top bar with segmented control */
.dejure-topbar {
  padding: 16px 20px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px 12px 0 0;
}

/* Segmented Control */
.segmented-control {
  display: inline-flex;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
  overflow-x: auto;
}

.segment-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.segment-item:hover {
  background: var(--md-sys-color-surface-container);
}

.segment-item.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.segment-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.08);
  color: inherit;
}

.segment-item.active .segment-count {
  background: rgba(255, 255, 255, 0.25);
}

/* Filter badge */
.dejure-filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container, var(--md-sys-color-primary));
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
}

.dejure-filter-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.6rem;
  color: inherit;
  transition: background 0.15s;
}

.dejure-filter-close:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* Select */
.dejure-select {
  padding: 7px 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  font-size: 0.85rem;
  min-width: 180px;
  outline: none;
  transition: border-color 0.15s;
}

.dejure-select:focus {
  border-color: var(--md-sys-color-primary);
}

/* Primary button */
.dejure-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.dejure-btn-primary:hover {
  filter: brightness(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Ghost button */
.dejure-btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px dashed var(--md-sys-color-outline-variant);
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
  transition: all 0.15s;
}

.dejure-btn-ghost:hover {
  border-color: var(--md-sys-color-primary);
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
}

/* Row 2: Contract pills bar */
.dejure-contracts-bar {
  padding: 12px 20px;
  background: var(--md-sys-color-surface-container-low);
  border-left: 1px solid var(--md-sys-color-outline-variant);
  border-right: 1px solid var(--md-sys-color-outline-variant);
}

.contract-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.contract-pill:hover {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-low);
}

.contract-pill.active {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.pill-number {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.contract-pill.active .pill-number {
  color: var(--md-sys-color-on-primary);
  font-weight: 700;
}

.contract-pill.active .pill-amount {
  color: rgba(255, 255, 255, 0.85);
}

.pill-amount {
  font-size: 0.75rem;
  color: var(--md-sys-color-on-surface-variant);
}

.project-letters-toolbar {
  background: var(--md-sys-color-surface-container-low);
}

.project-letters-sort {
  min-width: 220px;
}

.project-activity-toolbar {
  background: var(--md-sys-color-surface-container-low);
}

.project-activity-filter {
  min-width: 220px;
}

.project-activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-activity-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 18px;
  gap: 14px;
  align-items: start;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 14px;
  background: var(--md-sys-color-surface);
  text-align: left;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  cursor: pointer;
}

.project-activity-row:hover {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.project-activity-row__icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-primary);
}

.project-activity-row__main {
  min-width: 0;
}

.project-activity-row__head {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
  margin-bottom: 8px;
}

.project-activity-row__time {
  flex-shrink: 0;
  font-size: 0.78rem;
  color: var(--md-sys-color-on-surface-variant);
}

.project-activity-row__title {
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 4px;
}

.project-activity-row__summary {
  color: var(--md-sys-color-on-surface);
  line-height: 1.45;
  word-break: break-word;
}

.project-activity-row__meta {
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
}

.project-activity-row__arrow {
  min-height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
}

.project-health-row {
  display: flex;
  align-items: stretch;
  gap: 12px;
}

.project-health-row__main {
  flex: 1;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.78);
  padding: 16px 18px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.project-health-row__main:hover {
  transform: translateY(-1px);
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.project-health-row__actions {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.project-letters-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-letter-row {
  display: grid;
  grid-template-columns: minmax(220px, 1.1fr) minmax(250px, 1.2fr) minmax(280px, 1.6fr) minmax(220px, 1.1fr);
  gap: 16px;
  align-items: start;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 14px;
  background: var(--md-sys-color-surface);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.project-letter-row:hover {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.project-letter-row__cell {
  min-width: 0;
}

.project-letter-row__label {
  margin-bottom: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--md-sys-color-on-surface-variant);
}

.project-letter-row__value {
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
  word-break: break-word;
}

.project-letter-row__cell--subject .project-letter-row__value {
  font-weight: 600;
}

.project-letter-file {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  background: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.project-letter-file:hover {
  border-color: var(--md-sys-color-primary);
  background: color-mix(in srgb, var(--md-sys-color-primary) 8%, var(--md-sys-color-surface-container-low));
}

.project-letter-file span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-letter-row__empty {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.875rem;
}

/* Row 3: Main content area */
.dejure-content {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-top: none;
  border-radius: 0 0 12px 12px;
  padding: 20px;
}

.dejure-contract-meta {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

/* Two-column grid */
.dejure-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* Panel (card-like section for Products / Stages) */
.dejure-panel {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dejure-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--md-sys-color-surface-container-low);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dejure-panel-title {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--md-sys-color-on-surface);
}

.dejure-panel-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  background: var(--md-sys-color-outline-variant);
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 11px;
  font-size: 0.7rem;
  font-weight: 600;
}

.dejure-panel-body {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Empty state (small) */
.dejure-empty-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 24px 0;
  color: var(--md-sys-color-outline-variant);
  font-size: 0.8rem;
}

.dejure-empty-mini i {
  font-size: 1.5rem;
}

/* Empty state (large) */
.dejure-empty-state {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-top: none;
  border-radius: 0 0 12px 12px;
  min-height: 200px;
}

/* Item row */
.dejure-item {
  padding: 10px 12px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 10px;
  transition: background 0.15s;
}

.dejure-item:hover {
  background: var(--md-sys-color-surface-container);
}

.dejure-item-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.dejure-item-main--stage {
  align-items: flex-start;
}

.dejure-stage-title {
  min-width: 0;
}

.dejure-item-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dejure-stage-name {
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-break: break-word;
  line-height: 1.35;
}

.dejure-item-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.dejure-item-price {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  margin-top: 4px;
}

.dejure-item-price-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.dejure-item-tax {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  background: rgba(76, 175, 80, 0.12);
  color: #2e7d32;
}

.dejure-item-edit {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

/* Stage meta row */
.dejure-stage-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.dejure-stage-cost {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 600;
  background: rgba(33, 150, 243, 0.12);
  color: var(--md-sys-color-primary);
}

.dejure-stage-close {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 8px;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.72rem;
  cursor: pointer;
}

.dejure-stage-close input {
  width: 12px;
  height: 12px;
  margin: 0;
}

/* Stage status badge */
.dejure-stage-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface-variant);
}

.dejure-stage--planned {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface-variant);
}

.dejure-stage--in_progress {
  background: var(--color-info-container, #e1f5fe);
  color: var(--color-info, #0277bd);
}

.dejure-stage--completed {
  background: var(--color-success-container, #e8f5e9);
  color: var(--color-success, #2e7d32);
}

.dejure-stage--delayed {
  background: var(--color-danger-container, #ffebee);
  color: var(--color-danger, #c62828);
}

/* Deal stages tab: visual-only state indicator (no text status) */
.stage-state-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.stage-state-dot--active {
  background: #ffffff;
}

.stage-state-dot--overdue {
  background: var(--color-danger, #d32f2f);
}

.stage-state-dot--closed {
  background: var(--color-success, #2e7d32);
}

.stage-state-dot--partial {
  background: var(--color-warning, #f9a825);
}

.stage-closing-docs-cell {
  min-width: 160px;
}

.stage-closing-docs {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.stage-closing-doc-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid rgba(25, 118, 210, 0.24);
  border-radius: 999px;
  background: rgba(33, 150, 243, 0.08);
  color: var(--md-sys-color-primary);
  padding: 2px 7px;
  font-size: 0.72rem;
  line-height: 1.2;
  cursor: pointer;
  white-space: nowrap;
}

.stage-closing-doc-chip:hover {
  background: rgba(33, 150, 243, 0.16);
  border-color: rgba(25, 118, 210, 0.38);
}

.stage-closing-doc-chip strong {
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.stage-tree-toggle {
  width: 20px;
  height: 20px;
  padding: 0;
  color: var(--md-sys-color-on-surface-variant);
}

.stage-tree-toggle:hover {
  background: var(--md-sys-color-surface-container-high);
}

.stage-tree-spacer {
  width: 20px;
  height: 20px;
  display: inline-block;
  flex: 0 0 20px;
}

.stage-order-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.stage-drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  cursor: grab;
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 6px;
  user-select: none;
  -webkit-user-drag: element;
  touch-action: none;
}

.stage-drag-handle:hover {
  background: var(--md-sys-color-surface-container-high);
}

.stage-drag-handle:active {
  cursor: grabbing;
}

.stage-drop-row {
  position: relative;
}

.stage-drag-self {
  opacity: 0.7;
}

.stage-drop-row td {
  box-shadow: inset 0 3px 0 var(--md-sys-color-primary);
  background: color-mix(in srgb, var(--md-sys-color-primary) 6%, transparent);
}

.stage-drop-row td:first-child {
  position: relative;
}

.stage-drop-row td:first-child::before {
  content: '';
  position: absolute;
  left: 6px;
  top: -7px;
  width: 0;
  height: 0;
  border-top: 7px solid transparent;
  border-bottom: 7px solid transparent;
  border-left: 10px solid var(--md-sys-color-primary);
}

.dejure-item.stage-drop-row {
  box-shadow:
    inset 0 3px 0 var(--md-sys-color-primary),
    0 0 0 1px color-mix(in srgb, var(--md-sys-color-primary) 35%, transparent);
  background: color-mix(in srgb, var(--md-sys-color-primary) 7%, var(--md-sys-color-surface));
}

.dejure-item.stage-drop-row::before {
  content: '';
  position: absolute;
  left: 8px;
  top: -7px;
  width: 0;
  height: 0;
  border-top: 7px solid transparent;
  border-bottom: 7px solid transparent;
  border-left: 10px solid var(--md-sys-color-primary);
}

.stage-dropzone-cell {
  padding: 8px 12px !important;
}

.stage-root-dropzone,
.stage-drop-hint {
  border: 1px dashed var(--md-sys-color-outline-variant);
  border-radius: 10px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.75rem;
  transition: all 0.15s ease;
}

.stage-root-dropzone {
  padding: 10px 12px;
  text-align: center;
  background: var(--md-sys-color-surface-container-low);
}

.stage-root-dropzone--active,
.stage-drop-hint--active {
  border-color: var(--md-sys-color-primary);
  background: color-mix(in srgb, var(--md-sys-color-primary) 14%, transparent);
  color: var(--md-sys-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--md-sys-color-primary) 30%, transparent);
}

.stage-relation-cell {
  min-width: 210px;
}

.stage-relation-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stage-relation-line {
  display: block;
  line-height: 1.25;
  white-space: normal;
}

.stage-dependency-picker {
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--md-sys-color-surface);
}

.stage-dependency-picker__item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  line-height: 1.3;
}

.stage-dependency-config-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stage-dependency-config-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 110px;
  gap: 12px;
  align-items: center;
}

.stage-dependency-config-item__name {
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  line-height: 1.35;
}

.stage-drop-hint {
  margin-top: 6px;
  padding: 6px 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.stage-drop-hint--inline {
  margin-top: 8px;
}

.stage-drag-cursor {
  position: fixed;
  z-index: 4000;
  pointer-events: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(12, 22, 41, 0.92);
  color: #fff;
  box-shadow: 0 12px 28px rgba(12, 22, 41, 0.18);
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
}

.stage-drag-cursor--reorder {
  background: rgba(46, 109, 255, 0.95);
}

.stage-drag-cursor--child {
  background: rgba(108, 70, 255, 0.95);
}

.stage-drag-cursor--root {
  background: rgba(33, 150, 83, 0.95);
}

/* Icon button (small) */
.dejure-btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.7rem;
  transition: all 0.15s;
}

.dejure-btn-icon:hover {
  background: var(--md-sys-color-surface-container);
}

.dejure-btn-icon--danger:hover {
  background: var(--color-danger-container, #ffebee);
  color: var(--color-danger, #c62828);
}

/* Small button */
.dejure-btn-sm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface);
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.15s;
}

.dejure-btn-sm:hover {
  background: var(--md-sys-color-surface-container);
}

.dejure-btn-sm--primary {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border-color: var(--md-sys-color-primary);
}

.dejure-btn-sm--primary:hover {
  filter: brightness(1.1);
}

/* Input (inline) */
.dejure-input {
  padding: 6px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  font-size: 0.8rem;
  outline: none;
  width: 100%;
  transition: border-color 0.15s;
}

.dejure-input:focus {
  border-color: var(--md-sys-color-primary);
}

/* Add form area */
.dejure-add-form {
  padding: 12px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 10px;
  border: 1px dashed var(--md-sys-color-outline-variant);
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

:global(:root[data-theme="dark"]) #panel-stages,
:global(:root[data-theme="dark"]) #panel-dejure,
:global(:root[data-theme="dark"]) #panel-gantt,
:global(:root[data-theme="dark"]) #panel-activity {
  background: rgba(12, 22, 41, 0.88);
  border-color: rgba(148, 163, 184, 0.22);
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.28);
}

:global(:root[data-theme="dark"]) #panel-stages .card-header,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-topbar,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-contracts-bar,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-panel-header,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-contract-meta,
:global(:root[data-theme="dark"]) #panel-gantt .card-header,
:global(:root[data-theme="dark"]) #panel-activity .card-header,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-toolbar {
  background: rgba(15, 23, 42, 0.94);
  border-color: rgba(148, 163, 184, 0.18);
}

:global(:root[data-theme="dark"]) #panel-stages .card-title,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-panel-title,
:global(:root[data-theme="dark"]) #panel-dejure .pill-number,
:global(:root[data-theme="dark"]) #panel-stages .table td,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-item-name,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-stage-meta .text-muted,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-contract-meta .text-muted,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-empty-state,
:global(:root[data-theme="dark"]) #panel-gantt,
:global(:root[data-theme="dark"]) #panel-activity .card-title,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-row__title,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-row__summary {
  color: #e5edf9;
}

:global(:root[data-theme="dark"]) #panel-dejure .dejure-item-tax {
  background: rgba(74, 222, 128, 0.16);
  color: rgba(187, 247, 208, 0.96);
}

:global(:root[data-theme="dark"]) #panel-stages .text-muted,
:global(:root[data-theme="dark"]) #panel-dejure .text-muted,
:global(:root[data-theme="dark"]) #panel-dejure .pill-amount,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-panel-count,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-empty-mini,
:global(:root[data-theme="dark"]) #panel-stages .small.text-muted,
:global(:root[data-theme="dark"]) #panel-dejure .small.text-muted,
:global(:root[data-theme="dark"]) #panel-activity .text-muted,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-row__time,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-row__meta,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-row__arrow {
  color: #94a3b8 !important;
}

:global(:root[data-theme="dark"]) #panel-stages .table-container,
:global(:root[data-theme="dark"]) #panel-stages .table th,
:global(:root[data-theme="dark"]) #panel-stages .table td,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-content,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-panel,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-item,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-empty-state,
:global(:root[data-theme="dark"]) #panel-activity .project-activity-row {
  border-color: rgba(148, 163, 184, 0.18);
}

:global(:root[data-theme="dark"]) #panel-stages .table th {
  background: rgba(30, 41, 59, 0.96);
  color: #8fa2c7;
}

:global(:root[data-theme="dark"]) #panel-stages .table td {
  background: transparent;
}

:global(:root[data-theme="dark"]) #panel-stages .table tbody tr:hover td {
  background: rgba(59, 130, 246, 0.08);
}

:global(:root[data-theme="dark"]) #panel-stages .btn-outline-primary,
:global(:root[data-theme="dark"]) #panel-stages .btn-outline-secondary,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-btn-ghost,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-btn-sm,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-btn-icon,
:global(:root[data-theme="dark"]) #panel-stages .btn-icon {
  background: rgba(30, 41, 59, 0.92);
  border-color: rgba(148, 163, 184, 0.18);
  color: #dbe6f5;
}

:global(:root[data-theme="dark"]) #panel-stages .btn-outline-primary:hover,
:global(:root[data-theme="dark"]) #panel-stages .btn-outline-secondary:hover,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-btn-ghost:hover,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-btn-sm:hover,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-btn-icon:hover,
:global(:root[data-theme="dark"]) #panel-stages .btn-icon:hover {
  background: rgba(59, 130, 246, 0.14);
  border-color: rgba(96, 165, 250, 0.3);
  color: #f8fbff;
}

:global(:root[data-theme="dark"]) #panel-dejure .segmented-control,
:global(:root[data-theme="dark"]) #panel-dejure .contract-pill,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-filter-badge,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-select,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-input,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-add-form {
  background: rgba(15, 23, 42, 0.88);
  border-color: rgba(148, 163, 184, 0.18);
  color: #e5edf9;
}

:global(:root[data-theme="dark"]) #panel-dejure .segment-item {
  color: #9fb0c9;
}

:global(:root[data-theme="dark"]) #panel-dejure .segment-item:hover,
:global(:root[data-theme="dark"]) #panel-dejure .contract-pill:hover,
:global(:root[data-theme="dark"]) #panel-dejure .dejure-item:hover {
  background: rgba(59, 130, 246, 0.1);
}

:global(:root[data-theme="dark"]) #panel-dejure .segment-item.active,
:global(:root[data-theme="dark"]) #panel-dejure .contract-pill.active {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-color: rgba(96, 165, 250, 0.35);
}

:global(:root[data-theme="dark"]) #panel-activity .project-activity-row {
  background: rgba(15, 23, 42, 0.9);
}

:global(:root[data-theme="dark"]) #panel-activity .project-activity-row__icon {
  background: rgba(30, 41, 59, 0.92);
  color: #93c5fd;
}

:global(:root[data-theme="dark"]) #panel-activity .project-activity-row:hover {
  background: rgba(30, 41, 59, 0.98);
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.32);
}

:global(:root[data-theme="dark"]) #panel-dejure .stage-root-dropzone,
:global(:root[data-theme="dark"]) #panel-dejure .stage-drop-hint,
:global(:root[data-theme="dark"]) #panel-stages .stage-root-dropzone,
:global(:root[data-theme="dark"]) #panel-stages .stage-drop-hint {
  background: rgba(15, 23, 42, 0.72);
  border-color: rgba(148, 163, 184, 0.2);
  color: #9fb0c9;
}

:global(:root[data-theme="dark"]) #panel-dejure .stage-root-dropzone--active,
:global(:root[data-theme="dark"]) #panel-dejure .stage-drop-hint--active,
:global(:root[data-theme="dark"]) #panel-stages .stage-root-dropzone--active,
:global(:root[data-theme="dark"]) #panel-stages .stage-drop-hint--active {
  background: rgba(37, 99, 235, 0.18);
  border-color: rgba(96, 165, 250, 0.42);
  color: #bfdbfe;
}

:global(:root[data-theme="dark"]) .modal-content,
:global(:root[data-theme="dark"]) .modal-glass,
:global(:root[data-theme="dark"]) #panel-stages + .modal-overlay .modal-content,
:global(:root[data-theme="dark"]) #panel-dejure + .modal-overlay .modal-content {
  background: rgba(12, 22, 41, 0.96);
  border-color: rgba(148, 163, 184, 0.18);
  color: #e5edf9;
}

:global(:root[data-theme="dark"]) .modal-header,
:global(:root[data-theme="dark"]) .modal-footer,
:global(:root[data-theme="dark"]) .modal-glass-header,
:global(:root[data-theme="dark"]) .modal-glass-footer {
  background: rgba(15, 23, 42, 0.96);
  border-color: rgba(148, 163, 184, 0.18);
}

:global(:root[data-theme="dark"]) .modal-body .form-control,
:global(:root[data-theme="dark"]) .modal-body .form-select,
:global(:root[data-theme="dark"]) .modal-body textarea,
:global(:root[data-theme="dark"]) .modal-body select,
:global(:root[data-theme="dark"]) .modal-body input {
  background: rgba(15, 23, 42, 0.9);
  border-color: rgba(148, 163, 184, 0.18);
  color: #e5edf9;
}

:global(:root[data-theme="dark"]) .stage-close-warning {
  background: rgba(120, 53, 15, 0.32);
  color: #fdba74;
  border-color: rgba(251, 146, 60, 0.28);
}

:global(:root[data-theme="dark"]) .modal-body .bg-light,
:global(:root[data-theme="dark"]) .modal-body .border.rounded {
  background: rgba(15, 23, 42, 0.72) !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
}

/* Mobile Responsive */
@media (max-width: 992px) {
  .dashboard-grid {
    grid-template-columns: 1fr !important;
    height: auto;
  }

  .dashboard-left,
  .dashboard-right {
    max-height: none;
    overflow: visible;
  }

  .dejure-two-col {
    grid-template-columns: 1fr;
  }

  .dejure-topbar .d-flex {
    flex-wrap: wrap;
  }

  .segmented-control {
    max-width: 100%;
    overflow-x: auto;
  }

  .overview-kpis {
    grid-template-columns: 1fr !important;
  }

  .overview-main {
    grid-template-columns: 1fr !important;
  }

  .contracts-link-controls {
    min-width: 0;
    width: 100%;
  }

  .project-letter-row {
    grid-template-columns: 1fr 1fr;
  }

  .project-letters-sort {
    min-width: 180px;
  }
}

@media (max-width: 768px) {
  .unified-header {
    padding: 0 12px;
    margin-bottom: 10px !important;
  }

  .unified-header-inner {
    flex-wrap: wrap;
    height: auto;
    padding: 10px 0;
    gap: 8px;
  }

  .unified-header-left {
    width: 100%;
    order: 1;
  }

  .unified-project-name {
    font-size: 1rem !important;
  }

  .unified-obj-name {
    display: none;
  }

  .unified-nav {
    order: 3;
    width: 100%;
    margin-left: 0;
    overflow-x: auto;
    padding-bottom: 2px;
    position: relative;
    mask-image: linear-gradient(to right, transparent, black 16px, black calc(100% - 16px), transparent);
  }

  .unified-nav::before,
  .unified-nav::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 18px;
    pointer-events: none;
    z-index: 1;
  }

  .unified-nav::before {
    left: 0;
    margin-right: -18px;
    background: linear-gradient(90deg, var(--md-sys-color-surface) 15%, rgba(255, 255, 255, 0));
  }

  .unified-nav::after {
    right: 0;
    margin-left: -18px;
    background: linear-gradient(270deg, var(--md-sys-color-surface) 15%, rgba(255, 255, 255, 0));
  }

  .unified-nav-item {
    padding: 6px 10px;
    font-size: 0.78rem;
  }

  .unified-header-right {
    order: 2;
    margin-left: auto;
  }

  .unified-nav-hint {
    order: 4;
    width: 100%;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--md-sys-color-on-surface-variant);
    padding-top: 2px;
  }

  .scroll-container {
    padding: 0 !important;
  }

  .info-grid {
    gap: 6px;
  }

  .info-row {
    font-size: 14px;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    border-bottom: none;
    border: 1px solid var(--md-sys-color-outline-variant);
    border-radius: 10px;
    padding: 10px 12px;
    background: var(--md-sys-color-surface-container-low);
    margin-bottom: 2px;
  }

  .info-row .text-right {
    text-align: left;
  }

  .info-row .text-muted {
    font-size: 12px;
  }

  .estimate-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .estimate-search,
  .estimate-sort {
    min-width: 0;
    max-width: 100%;
  }

  .estimate-add-btn {
    margin-left: 0;
    width: 100%;
  }

  .kpi-card-value {
    font-size: 1.45rem;
  }

  .overview-kpis {
    grid-template-columns: 1fr !important;
  }

  .dejure-topbar {
    padding: 12px;
  }

  .dejure-topbar .d-flex.align-center.gap-3 {
    flex-direction: column;
    align-items: stretch;
  }

  .dejure-topbar .ml-auto {
    margin-left: 0;
  }

  .project-letters-toolbar {
    align-items: stretch;
  }

  .project-activity-toolbar {
    align-items: stretch;
  }

  .project-activity-filter {
    width: 100%;
    min-width: 0;
  }

  .project-letters-sort {
    width: 100%;
    min-width: 0;
  }

  .project-activity-row {
    grid-template-columns: 42px minmax(0, 1fr);
    gap: 12px;
  }

  .project-activity-row__head {
    flex-wrap: wrap;
    align-items: flex-start;
    gap: 6px;
  }

  .project-activity-row__time {
    width: 100%;
  }

  .project-activity-row__arrow {
    display: none;
  }

  .project-letter-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-grid .full-span,
  .form-grid .span-2 {
    grid-column: span 1;
  }

  .row {
    margin-left: -6px;
    margin-right: -6px;
    display: flex;
    flex-wrap: wrap;
  }

  .row > [class*="col-"] {
    padding-left: 6px;
    padding-right: 6px;
    width: 100%;
    max-width: 100%;
    flex: 0 0 100%;
  }

  .col-6,
  .col-md-4,
  .col-md-6,
  .col-md-8,
  .col-md-12 {
    width: 100%;
    max-width: 100%;
    flex: 0 0 100%;
  }
}

/* =============================================================
   REFERENCE DESIGN ALIGNMENT (visual cleanup pass)

   All selectors below are scoped under `.project-detail-view`
   so they take precedence over the legacy rules higher up in
   this file and inside subcomponents (parts/*.vue use non-scoped
   styles that cascade into this view).

   Approach: keep markup untouched, override surface colours,
   radii, paddings, shadows, badge palettes to match the design
   system established in Tasks / Leads / Projects-list / Lead form
   modal. Material-3 colour tokens map onto the new `--color-*`
   palette; hardcoded rgba()/hex/border-radius values are flattened
   onto `--radius-{sm,md,lg}`, `--shadow-{sm,md,lg}`, etc.
   ============================================================= */

/* ---------- Unified header ---------- */
.project-detail-view .unified-header {
  background: var(--color-surface);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.project-detail-view .unified-back-btn,
.project-detail-view .unified-action-btn {
  border-color: var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
}
.project-detail-view .unified-back-btn:hover,
.project-detail-view .unified-action-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.project-detail-view .unified-action-btn--danger:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-color: var(--color-danger);
}
.project-detail-view .unified-project-name { color: var(--color-text); }
.project-detail-view .unified-obj-name { color: var(--color-text-muted); }
.project-detail-view .unified-nav-item {
  color: var(--color-text-muted);
  border-radius: var(--radius-md);
}
.project-detail-view .unified-nav-item:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.project-detail-view .unified-nav-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.project-detail-view .unified-nav-item:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
.project-detail-view .unified-nav-count {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

/* ---------- Surface cards (.card, .glass-card, .kpi-card) ---------- */
.project-detail-view .card,
.project-detail-view .glass-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  padding: 0;
  margin: 0;
}
.project-detail-view .kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  /* .project-detail-view .glass-card задаёт padding:0 — возвращаем
     внутренний отступ KPI-карточкам (у них нет утилитарного p-4). */
  padding: 18px 20px;
}
.project-detail-view .card-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface);
}
.project-detail-view .card-title {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  margin: 0;
}

/* ---------- Tables (.table head & rows under the reference) ---------- */
.project-detail-view .table th {
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  padding: 10px 14px;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.4px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--color-border);
}
.project-detail-view .table td {
  padding: 12px 14px;
  font-size: var(--text-base);
  border-bottom: 1px solid var(--color-border-subtle);
  color: var(--color-text);
}
.project-detail-view .table tbody tr:hover { background: var(--color-surface-2); }
.project-detail-view .table tfoot { background: var(--color-surface-2); }

/* ---------- Badges — soft palette tokens ---------- */
.project-detail-view .badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  background: var(--color-surface-2);
  color: var(--color-text-muted);
}
.project-detail-view .badge-success,
.project-detail-view .badge-status-active { background: var(--color-success-soft); color: var(--color-success); }
.project-detail-view .badge-primary,
.project-detail-view .badge-info,
.project-detail-view .badge-status-completed { background: var(--color-info-soft, var(--color-primary-soft)); color: var(--color-info, var(--color-primary)); }
.project-detail-view .badge-warning,
.project-detail-view .badge-status-on_hold { background: var(--color-warning-soft); color: var(--color-warning); }
.project-detail-view .badge-danger { background: var(--color-danger-soft); color: var(--color-danger); }
.project-detail-view .badge-secondary,
.project-detail-view .badge-outline { background: transparent; color: var(--color-text-muted); border: 1px solid var(--color-border); }

/* ---------- Modals (.modal-glass family → LeadFormModal-style) ---------- */
.project-detail-view .modal-glass,
body > .modal-glass {
  /* Selectors cover both in-view and Teleported instances. */
  width: min(680px, 100%);
  max-height: 92vh;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  overflow: hidden;
}
.project-detail-view .modal-glass .modal-glass-header,
body > .modal-glass .modal-glass-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.project-detail-view .modal-glass .modal-glass-body,
body > .modal-glass .modal-glass-body {
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.project-detail-view .modal-glass .modal-glass-footer,
body > .modal-glass .modal-glass-footer {
  padding: 12px 18px;
  border-top: 1px solid var(--color-border-subtle);
  gap: 8px;
}

/* ---------- Pass 2: tab-specific surface tweaks ---------- */

/* Files tab — tree/table panels */
.project-detail-view .deal-files-tree-panel,
.project-detail-view .deal-files-table-panel {
  border-color: var(--color-border-subtle);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
}
.project-detail-view .deal-files-panel-head,
.project-detail-view .deal-files-tree-actions {
  border-bottom-color: var(--color-border-subtle);
}
.project-detail-view .deal-files-panel-title { color: var(--color-text); }
.project-detail-view .deal-files-type-chip {
  border-color: var(--color-border-subtle);
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  border-radius: var(--radius-pill);
}
.project-detail-view .deal-files-type-chip:hover {
  background: var(--color-surface-3);
  color: var(--color-text);
}
.project-detail-view .deal-files-type-chip.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: var(--color-primary-soft);
}
.project-detail-view .deal-tree-node {
  border-radius: var(--radius-md);
  color: var(--color-text);
}
.project-detail-view .deal-tree-node:hover { background: var(--color-surface-2); }
.project-detail-view .deal-tree-node.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.project-detail-view .deal-tree-toggle-btn {
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
}
.project-detail-view .deal-tree-toggle-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}

/* Gantt tab — segmented switch */
.project-detail-view .project-gantt-switch {
  border-color: var(--color-border);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 3px;
}
.project-detail-view .project-gantt-switch-btn {
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  font-weight: var(--fw-medium);
}
.project-detail-view .project-gantt-switch-btn.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  box-shadow: none;
}

/* Activity tab — flatten double-radius rows */
.project-detail-view .project-activity-row {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

/* DeJure / Defacto — surface-level harmonisation */
.project-detail-view .contracts-linker-popover {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}
.project-detail-view .estimate-toolbar {
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
}

/* ---------- Confirm overlay (delete dialogs) ---------- */
body > .confirm-overlay .modal-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
}

/* ---------- Health count pill (overview chip in stages list) ---------- */
.project-detail-view .project-health-count {
  border-color: var(--color-warning-soft);
  background: var(--color-warning-soft);
  color: var(--color-warning);
}
.project-detail-view .project-health-count--error {
  border-color: var(--color-danger-soft);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

/* ---------- Inline elements ---------- */
.project-detail-view .hover-bg-light:hover { background-color: var(--color-surface-2); }
.project-detail-view .bg-surface { background-color: var(--color-surface); }

/* ---------- Letters tab — toolbar + rows + filter pills ---------- */
.project-detail-view .project-letters-toolbar,
.project-detail-view .project-activity-toolbar {
  background: var(--color-surface);
  border-bottom-color: var(--color-border-subtle) !important;
}
.project-detail-view .project-letter-row {
  background: var(--color-surface);
  border-color: var(--color-border-subtle);
  border-radius: var(--radius-md);
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.project-detail-view .project-letter-row:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-2);
  box-shadow: none;
  transform: none;
}
.project-detail-view .project-letter-row__label { color: var(--color-text-muted); }
.project-detail-view .project-letter-row__value { color: var(--color-text); }
.project-detail-view .project-letter-row__empty { color: var(--color-text-muted); }
.project-detail-view .project-letter-file {
  border-color: var(--color-border-subtle);
  background: var(--color-surface-2);
  color: var(--color-primary);
  border-radius: var(--radius-md);
}
.project-detail-view .project-letter-file:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

/* ---------- Activity rows — flatten radii + hover uplift ---------- */
.project-detail-view .project-activity-row {
  background: var(--color-surface);
  border-color: var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: none;
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.project-detail-view .project-activity-row:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-2);
  box-shadow: none;
  transform: none;
}
.project-detail-view .project-activity-row__icon {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-radius: var(--radius-sm);
}
.project-detail-view .project-activity-row__time { color: var(--color-text-muted); }
.project-detail-view .project-activity-row__title,
.project-detail-view .project-activity-row__summary { color: var(--color-text); }

/* ---------- DeJure tab surfaces ---------- */
.project-detail-view .dejure-content {
  background: var(--color-surface);
  border-color: var(--color-border-subtle);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

/* ---------- Contract pills (Letters & DeJure shared pattern) ---------- */
.project-detail-view .contract-pill {
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border-subtle);
  background: var(--color-surface);
  color: var(--color-text);
  padding: 6px 14px;
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.project-detail-view .contract-pill:hover { background: var(--color-surface-2); }
.project-detail-view .contract-pill.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

/* ---------- Stages tab — closing-doc chips, tree toggle, drag handle ---------- */
.project-detail-view .stage-closing-doc-chip {
  border-color: var(--color-primary-soft);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-radius: var(--radius-pill);
}
.project-detail-view .stage-closing-doc-chip:hover {
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  border-color: var(--color-primary);
}
.project-detail-view .stage-closing-doc-chip strong { color: var(--color-text); }
.project-detail-view .stage-tree-toggle,
.project-detail-view .stage-drag-handle {
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
}
.project-detail-view .stage-tree-toggle:hover,
.project-detail-view .stage-drag-handle:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.project-detail-view .stage-state-dot--active { background: var(--color-text-muted); }

/* ---------- Defacto tab — product rows ---------- */
.project-detail-view .product-row {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: none;
}
.project-detail-view .product-header { border-radius: var(--radius-md) var(--radius-md) 0 0; }
.project-detail-view .product-body { border-radius: 0 0 var(--radius-md) var(--radius-md); }
.project-detail-view .product-header.bg-light { background: var(--color-surface-2); }

/* ---------- Modal product (wider modal — keep its width override) ---------- */
.project-detail-view .modal-content.modal-product {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
  backdrop-filter: none;
}

/* ---------- Inline monospace currency cells (used as `style="..."`) ---------- */
.project-detail-view td[style*="monospace"] {
  font-variant-numeric: tabular-nums;
}

/* ---------- Dark theme parity ---------- */
:root[data-theme="dark"] .project-detail-view .unified-header,
:root[data-theme="dark"] .project-detail-view .card,
:root[data-theme="dark"] .project-detail-view .glass-card,
:root[data-theme="dark"] .project-detail-view .kpi-card,
:root[data-theme="dark"] .project-detail-view .deal-files-tree-panel,
:root[data-theme="dark"] .project-detail-view .deal-files-table-panel,
:root[data-theme="dark"] .project-detail-view .project-activity-row {
  border-color: var(--color-border);
}
:root[data-theme="dark"] .project-detail-view .card-header,
:root[data-theme="dark"] .project-detail-view .deal-files-panel-head,
:root[data-theme="dark"] .project-detail-view .deal-files-tree-actions {
  border-bottom-color: var(--color-border);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .project-detail-view .unified-header,
  :root:not([data-theme="light"]) .project-detail-view .card,
  :root:not([data-theme="light"]) .project-detail-view .glass-card,
  :root:not([data-theme="light"]) .project-detail-view .kpi-card,
  :root:not([data-theme="light"]) .project-detail-view .deal-files-tree-panel,
  :root:not([data-theme="light"]) .project-detail-view .deal-files-table-panel,
  :root:not([data-theme="light"]) .project-detail-view .project-activity-row {
    border-color: var(--color-border);
  }
}

</style>
