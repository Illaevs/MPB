import { post } from './_client'

/**
 * Глобальный полнотекстовый поиск (Step 0).
 *
 * Backend: `POST /api/v1/search` (FTS5 + BM25 + ACL).
 * Возвращает `{ items: [{entity_type, entity_id, title, snippet, score}], total, query }`.
 *
 * Step 1 (semantic): тот же эндпоинт автоматически переключится на
 * hybrid rank (BM25 + cosine), когда модель embedding'ов будет
 * подключена и в типе накопится ≥20 записей.
 *
 * Параметры:
 *  - query: строка запроса
 *  - entity_types: опциональный массив (deal, contract, task, lead,
 *    company, document, outgoing_document, kp_document, mail_message,
 *    legal_case, support_ticket, task_message, task_subtask,
 *    subcontractor_card)
 *  - limit / offset: пагинация (limit 1-100, default 20)
 */

const BASE = '/api/v1/search'

export const search = (
  { query, entity_types = null, limit = 20, offset = 0 } = {},
  options,
) =>
  post(
    BASE,
    {
      query,
      entity_types,
      limit,
      offset,
    },
    options,
  )
