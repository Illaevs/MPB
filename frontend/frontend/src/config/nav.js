/**
 * Конфигурация сайдбара.
 *
 * - `pinned`     — отдельные ссылки в самой верхней части сайдбара.
 * - `sections`   — группы со сворачиваемым заголовком.
 *   Каждый item: { to, icon, label, access }.
 *   access: null — всегда показывать; string — ключ секции в матрице прав.
 *   `requireAny`: список секций; секция отображается, если хотя бы к одной есть доступ.
 *
 * Этот файл — единый источник правды; sidebar/header/collapsed-icons
 * рендерятся из него (AppSidebar.vue).
 */

export const navPinned = [
  { to: '/', icon: 'fa-home', label: 'Главная', access: null },
]

export const navSections = [
  {
    key: 'work',
    title: 'Работа',
    items: [
      { to: '/projects',             icon: 'fa-project-diagram',    label: 'Сделки',            access: 'projects' },
      { to: '/leads',                icon: 'fa-bullhorn',           label: 'Лиды',              access: 'leads' },
      { to: '/tasks',                icon: 'fa-tasks',              label: 'Задачи',            access: 'tasks' },
      { to: '/my-approvals',         icon: 'fa-clipboard-check',    label: 'Мои согласования',  access: null },
      { to: '/calendar',             icon: 'fa-calendar-days',      label: 'Календарь',         access: 'calendar' },
      { to: '/gantt',                icon: 'fa-chart-gantt',        label: 'План-график',       access: 'projects' },
      { to: '/data-health',          icon: 'fa-triangle-exclamation', label: 'Контроль данных', access: 'projects' },
      { to: '/legal-work',           icon: 'fa-scale-balanced',     label: 'Суды',              access: 'legal_work' },
      { to: '/work-results-reviews', icon: 'fa-clipboard-check',    label: 'Согласования РР',   access: 'work_results_reviews' },
    ],
  },
  {
    key: 'customer',
    title: 'Заказчик',
    requireAny: ['customer_portal'],
    items: [
      { to: '/customer', icon: 'fa-user-check', label: 'Кабинет заказчика', access: 'customer_portal' },
    ],
  },
  {
    key: 'comms',
    title: 'Коммуникации',
    items: [
      { to: '/messenger', icon: 'fa-comments', label: 'Мессенджер', access: 'global_chat' },
      { to: '/mail',      icon: 'fa-at',       label: 'Почта',      access: 'mail' },
    ],
  },
  {
    key: 'finance',
    title: 'Финансы',
    items: [
      { to: '/finance',         icon: 'fa-money-bill-wave', label: 'Финансы',     access: 'finance' },
      { to: '/treasury',        icon: 'fa-landmark',        label: 'Казначейство', access: 'treasury' },
      { to: '/income-expense',  icon: 'fa-scale-balanced',  label: 'ДДС',         access: 'income_expense' },
    ],
  },
  {
    key: 'docs',
    title: 'Документы',
    items: [
      { to: '/outgoing-registry', icon: 'fa-envelope',      label: 'Исходящие',     access: 'outgoing_registry' },
      { to: '/contracts',         icon: 'fa-file-contract', label: 'Договоры',      access: 'contracts' },
      { to: '/document-registry', icon: 'fa-folder-open',   label: 'Документация',  access: 'document_registry' },
      { to: '/files-catalog',     icon: 'fa-hdd',           label: 'Файлы',         access: 'files_catalog' },
    ],
  },
  {
    key: 'contragents',
    title: 'Контрагенты',
    items: [
      { to: '/companies',       icon: 'fa-users',       label: 'Контрагенты',  access: 'companies' },
      { to: '/catalog',         icon: 'fa-boxes',       label: 'Каталог',      access: 'catalog' },
      { to: '/tenders',         icon: 'fa-gavel',       label: 'Тендеры',      access: 'tenders_admin' },
      { to: '/accreditations',  icon: 'fa-certificate', label: 'Аккредитации', access: 'accreditations_admin' },
    ],
  },
  {
    key: 'subcontractor',
    title: 'Подрядчик',
    requireAny: ['executor', 'tenders_subcontractor', 'accreditations_subcontractor'],
    items: [
      { to: '/executor',                    icon: 'fa-helmet-safety',     label: 'Исполнитель',             access: 'executor' },
      { to: '/tenders-subcontractor',       icon: 'fa-people-carry-box',  label: 'Тендеры (подрядчик)',     access: 'tenders_subcontractor' },
      { to: '/accreditations-subcontractor', icon: 'fa-id-card',          label: 'Аккредитации (подрядчик)', access: 'accreditations_subcontractor' },
    ],
  },
  {
    key: 'admin',
    title: 'Админ',
    requireAny: ['users', 'roles', 'document_templates'],
    items: [
      { to: '/users',              icon: 'fa-user-cog',         label: 'Пользователи',       access: 'users' },
      { to: '/roles',              icon: 'fa-shield-alt',       label: 'Роли и права',       access: 'roles' },
      { to: '/approvals',          icon: 'fa-diagram-project',  label: 'Согласования',       access: 'roles' },
      { to: '/audit-logs',         icon: 'fa-clipboard-list',   label: 'Журнал действий',    access: 'roles' },
      { to: '/document-templates', icon: 'fa-file-word',        label: 'Шаблоны документов', access: 'document_templates' },
    ],
  },
]

/** Плоский список всех ссылок — для collapsed sidebar (только иконки). */
export const navFlatItems = [
  // customer_portal в этом режиме поднимается наверх (повторяет логику App.vue)
  { to: '/customer', icon: 'fa-user-check', access: 'customer_portal' },
  ...navSections.flatMap(s => s.items),
]
