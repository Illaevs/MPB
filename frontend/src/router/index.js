import { createRouter, createWebHistory } from 'vue-router'
import { hasSectionAccess } from '../utils/permissions'
import { useAuthStore } from '../stores/auth'
import { useUiPreferences } from '../composables/useUiPreferences'
import Login from '../views/Login.vue'
import { isTestPortalVariant } from '../config/appVariant'

// Все «обычные» страницы — lazy. Login оставляем eager, чтобы
// при первом заходе на /login не было сетевого делея и flash'а.
const lazy = (importer) => importer

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Home',
    component: lazy(() => import('../views/Home.vue'))
  },
  {
    path: '/projects',
    name: 'Projects',
    component: lazy(() => import('../views/Projects.vue')),
    meta: { section: 'projects' }
  },
  {
    path: '/data-health',
    name: 'DataHealth',
    component: lazy(() => import('../views/DataHealth.vue')),
    meta: { section: 'data_health' }
  },
  {
    path: '/search',
    name: 'Search',
    component: lazy(() => import('../views/Search.vue')),
    // section не указан — поиск доступен любому авторизованному;
    // per-entity ACL применяется внутри backend search-роутера.
  },
  {
    path: '/reglaments',
    name: 'Reglaments',
    component: lazy(() => import('../views/Reglaments.vue')),
    // Нормативная база — общесправочник, доступ любому авторизованному.
    // Backend сам гейтит запись (upload/admin) через CurrentUser.
  },
  {
    path: '/leads',
    name: 'Leads',
    component: lazy(() => import('../views/Leads.vue')),
    meta: { section: 'leads' }
  },
  {
    path: '/leads/:id',
    name: 'LeadDetail',
    component: lazy(() => import('../views/LeadDetail.vue')),
    meta: { section: 'leads' }
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: lazy(() => import('../views/ProjectDetail.vue')),
    meta: { section: 'projects' }
  },
  {
    path: '/gantt',
    name: 'Gantt',
    component: lazy(() => import('../views/Gantt.vue')),
    meta: { section: 'projects' }
  },
  {
    path: '/finance',
    name: 'Finance',
    component: lazy(() => import('../views/Finance.vue')),
    meta: { section: 'finance' }
  },
  {
    path: '/treasury',
    name: 'Treasury',
    component: lazy(() => import('../views/Treasury.vue')),
    meta: { section: 'treasury' }
  },
  {
    path: '/income-expense',
    name: 'IncomeExpense',
    component: lazy(() => import('../views/IncomeExpense.vue')),
    meta: { section: 'income_expense' }
  },
  {
    path: '/companies',
    name: 'Companies',
    component: lazy(() => import('../views/Companies.vue')),
    meta: { section: 'companies' }
  },
  // Event bus admin routes — для observability outbox-пайплайна
  // (counts, DLQ, retry, causation chains). Доступ резолвится бэком
  // через is_superuser; в nav.js access='roles' ограничивает видимость
  // ссылки только пользователям с правом на матрицу ролей.
  {
    path: '/integrations/outbox',
    name: 'IntegrationsOutbox',
    component: lazy(() => import('../views/IntegrationsOutbox.vue')),
  },
  {
    path: '/integrations/subscriptions',
    name: 'IntegrationsSubscriptions',
    component: lazy(() => import('../views/IntegrationsSubscriptions.vue')),
  },
  {
    path: '/contracts',
    name: 'Contracts',
    component: lazy(() => import('../views/Contracts.vue')),
    meta: { section: 'contracts' }
  },
  {
    path: '/contracts/:id',
    name: 'ContractDetail',
    component: lazy(() => import('../views/ContractDetail.vue')),
    meta: { section: 'contracts' }
  },
  {
    path: '/catalog',
    name: 'Catalog',
    component: lazy(() => import('../views/Catalog.vue')),
    meta: { section: 'catalog' }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: lazy(() => import('../views/Tasks.vue')),
    meta: { section: 'tasks' }
  },
  {
    path: '/messenger',
    name: 'Messenger',
    component: lazy(() => import('../views/Messenger.vue')),
    meta: { section: 'global_chat' }
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: lazy(() => import('../views/Calendar.vue')),
    meta: { section: 'calendar' }
  },
  {
    path: '/legal-work',
    name: 'LegalWork',
    component: lazy(() => import('../views/LegalWork.vue')),
    meta: { section: 'legal_work' }
  },
  {
    path: '/legal-work/:id',
    name: 'LegalWorkDetail',
    component: lazy(() => import('../views/LegalWorkDetail.vue')),
    meta: { section: 'legal_work' }
  },
  {
    path: '/executor',
    name: 'ExecutorPanel',
    component: lazy(() => import('../views/ExecutorPanel.vue')),
    meta: { section: 'executor' }
  },
  {
    path: '/customer',
    name: 'CustomerPanel',
    component: lazy(() => import('../views/CustomerPanel.vue')),
    meta: { section: 'customer_portal' }
  },
  {
    path: '/outgoing-registry',
    name: 'OutgoingRegistry',
    component: lazy(() => import('../views/OutgoingRegistry.vue')),
    meta: { section: 'outgoing_registry' }
  },
  {
    path: '/outgoing-registry-v2',
    name: 'OutgoingRegistryV2',
    component: lazy(() => import('../views/OutgoingRegistryV2.vue')),
    meta: { section: 'outgoing_registry' }
  },
  {
    path: '/outgoing-templates-v2',
    name: 'OutgoingTemplatesV2Admin',
    component: lazy(() => import('../views/OutgoingTemplatesV2Admin.vue')),
    meta: { section: 'outgoing_registry' }
  },
  {
    path: '/tenders',
    name: 'TendersAdmin',
    component: lazy(() => import('../views/TendersAdmin.vue')),
    meta: { section: 'tenders_admin' }
  },
  {
    path: '/tenders-subcontractor',
    name: 'TendersSubcontractor',
    component: lazy(() => import('../views/TendersSubcontractor.vue')),
    meta: { section: 'tenders_subcontractor' }
  },
  {
    path: '/accreditations',
    name: 'AccreditationsAdmin',
    component: lazy(() => import('../views/AccreditationsAdmin.vue')),
    meta: { section: 'accreditations_admin' }
  },
  {
    path: '/accreditations-subcontractor',
    name: 'AccreditationsSubcontractor',
    component: lazy(() => import('../views/AccreditationsSubcontractor.vue')),
    meta: { section: 'accreditations_subcontractor' }
  },
  {
    path: '/users',
    name: 'Users',
    component: lazy(() => import('../views/Users.vue')),
    meta: { section: 'users' }
  },
  {
    path: '/roles',
    name: 'Roles',
    component: lazy(() => import('../views/Roles.vue')),
    meta: { section: 'roles' }
  },
  {
    path: '/org-structure',
    name: 'OrgStructure',
    component: lazy(() => import('../views/OrgStructure.vue')),
    meta: { section: 'org_structure' }
  },
  {
    path: '/approvals',
    name: 'Approvals',
    component: lazy(() => import('../views/Approvals.vue')),
    meta: { section: 'roles' }
  },
  {
    path: '/my-approvals',
    name: 'MyApprovals',
    component: lazy(() => import('../views/MyApprovals.vue'))
  },
  {
    path: '/document-templates',
    name: 'DocumentTemplates',
    component: lazy(() => import('../views/DocumentTemplates.vue')),
    meta: { section: 'document_templates' }
  },
  {
    path: '/document-registry',
    name: 'DocumentRegistry',
    component: lazy(() => import('../views/DocumentRegistry.vue')),
    meta: { section: 'document_registry' }
  },
  {
    path: '/files-catalog',
    name: 'FilesCatalog',
    component: lazy(() => import('../views/FilesCatalog.vue')),
    meta: { section: 'files_catalog' }
  },
  {
    path: '/mail',
    name: 'Mail',
    component: lazy(() => import('../views/Mail.vue')),
    meta: { section: 'mail' }
  },
  {
    path: '/work-results-reviews',
    name: 'WorkResultsReviews',
    component: lazy(() => import('../views/WorkResultsReviews.vue')),
    meta: { section: 'work_results_reviews' }
  },
  {
    path: '/support',
    name: 'Support',
    component: lazy(() => import('../views/Support.vue')),
    meta: { section: 'support' }
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: lazy(() => import('../views/Notifications.vue'))
  },
  {
    path: '/audit-logs',
    name: 'AuditLogs',
    component: lazy(() => import('../views/AuditLogs.vue')),
    meta: { section: 'roles' }
  },
  {
    path: '/workday',
    name: 'Workday',
    component: lazy(() => import('../views/Workday.vue')),
    // Гард по секции не ставим: страница сама фильтрует — обычный
    // юзер видит только свои сессии, admin (workday_admin) — всех.
  },
  {
    path: '/me',
    name: 'MyProfile',
    component: lazy(() => import('../views/MyProfile.vue')),
    // Профиль доступен любому авторизованному; гарда по секции нет.
  },
  {
    path: '/absences',
    name: 'Absences',
    component: lazy(() => import('../views/Absences.vue')),
    // Раздел `absences` — collection-gate включён на бэке; страница
    // сама показывает только релевантные пользователю записи.
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  const isPublic = to.meta?.public

  // Первая проверка сессии: всегда дёргаем бэк, чтобы он подтвердил
  // или опроверг pending-флоу (2FA challenge/setup). Раньше условие
  // включало `!pendingTwoFactorSetup` — из-за этого зомби-pending
  // из sessionStorage прошлой попытки переживал смену БД/REQUIRE_2FA
  // и фронт упорно гнал юзера на форму setup, минуя бэк.
  if (!auth.sessionChecked) {
    await auth.restoreSession()
  } else if (!isPublic && !auth.accessToken && !auth.pendingTwoFactor && !auth.pendingTwoFactorSetup) {
    try {
      await auth.restoreSession(true)
    } catch (e) {
      // ignore restore errors, redirect handled below
    }
  }

  // Доверяем бэку: setup нужен ровно тогда, когда бэк его явно
  // запросил (через login/session → pendingTwoFactorSetup в стор).
  // Раньше тут была дополнительная «защита» по `user.two_factor_enabled
  // === false`, которая загоняла любого пользователя без 2FA в форму
  // setup — даже если бэк отключил требование (REQUIRE_TWO_FACTOR=false
  // на локалке). Это формировало мёртвую петлю: TOTP-код с
  // короткоживущим серверным секретом не сходился, фронт не выпускал.
  const requiresTwoFactorSetup = isTestPortalVariant
    ? false
    : Boolean(auth.pendingTwoFactorSetup)
  if (!isPublic && !auth.accessToken) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  if (requiresTwoFactorSetup && to.path !== '/login') {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  if (to.path === '/login' && auth.accessToken && !requiresTwoFactorSetup) {
    return next(from.fullPath && from.fullPath !== '/login' ? from.fullPath : '/')
  }

  const permissionEntries = Object.entries(auth.permissions || {}).filter(([key, value]) => {
    if (key === '__superuser__') return false
    return Boolean(value?.read_all || value?.read_assigned)
  })
  const customerOnlySession =
    hasSectionAccess('customer_portal', auth.permissions) &&
    permissionEntries.length === 1 &&
    permissionEntries[0][0] === 'customer_portal'

  if (to.path === '/' && customerOnlySession) {
    return next('/customer')
  }

  // Пользовательская стартовая страница: редиректим только корень и
  // только если цель доступна (иначе остаёмся на '/', без цикла —
  // next(startPage) уводит to.path с '/' и блок повторно не сработает).
  if (to.path === '/' && !customerOnlySession) {
    const startPage = useUiPreferences().prefs.startPage
    if (startPage && startPage !== '/') {
      const resolved = router.resolve(startPage)
      const sec = resolved?.meta?.section
      if (
        resolved?.name &&
        resolved.path !== '/' &&
        (!sec || hasSectionAccess(sec, auth.permissions))
      ) {
        return next(startPage)
      }
    }
  }

  const section = to.meta?.section
  if (!section) return next()
  if (hasSectionAccess(section, auth.permissions)) return next()
  return next('/')
})

export default router
