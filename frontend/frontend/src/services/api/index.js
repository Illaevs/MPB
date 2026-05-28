/**
 * Единая точка входа для API-слоя.
 *
 * Использование:
 *   import { api } from '@/services/api'
 *   const list = await api.companies.list({ search })
 *
 * Доменные модули добавляются по мере миграции (см. roadmap Phase 2).
 */

import * as companies from './companies'
import * as users from './users'
import * as roles from './roles'
import * as categories from './categories'
import * as products from './products'

import * as leads from './leads'
import * as deals from './deals'
import * as projects from './projects'
import * as tasks from './tasks'
import * as contracts from './contracts'

import * as outgoing from './outgoing'
import * as documentRegistry from './documentRegistry'
import * as documentTemplates from './documentTemplates'
import * as files from './files'

import * as mail from './mail'
import * as messenger from './messenger'
import * as notifications from './notifications'

import * as treasury from './treasury'
import * as incomeExpense from './incomeExpense'
import * as finance from './finance'

import * as tenders from './tenders'
import * as accreditations from './accreditations'
import * as workResults from './workResults'

import * as legal from './legal'
import * as audit from './audit'
import * as approvals from './approvals'
import * as auth from './auth'
import * as calendar from './calendar'
import * as gantt from './gantt'
import * as executor from './executor'
import * as customer from './customer'
import * as dataHealth from './dataHealth'
import * as ai from './ai'
import * as home from './home'

export const api = {
  // Reference data
  companies,
  users,
  roles,
  categories,
  products,
  // CRM core
  leads,
  deals,
  projects,
  tasks,
  contracts,
  // Documents & files
  outgoing,
  documentRegistry,
  documentTemplates,
  files,
  // Comms
  mail,
  messenger,
  notifications,
  // Finance
  treasury,
  incomeExpense,
  finance,
  // Contragent workflows
  tenders,
  accreditations,
  workResults,
  // Admin & misc
  legal,
  audit,
  approvals,
  auth,
  calendar,
  gantt,
  executor,
  customer,
  dataHealth,
  ai,
  home,
}

export { request, get, post, put, patch, del, rawRequest } from './_client'
