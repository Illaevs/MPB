import { get, post, put, patch, del } from './_client'

const BASE = '/api/v1/deals'
const STAGES_BASE = '/api/v1/stages'
const SUB_STAGES_BASE = '/api/v1/subcontractor-stages'
const SUB_PRODUCTS_BASE = '/api/v1/subcontractor-products'
const DEFACTO_BASE = '/api/v1/defacto'

/* ---- CRUD ---- */

export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

/* ---- Активность ---- */

export const activity = (id, params, options) =>
  get(`${BASE}/${id}/activity`, params, options)

/* ---- Папки ---- */

export const folders = (id, options) =>
  get(`${BASE}/${id}/folders`, undefined, options)

/* ---- ГИПы ---- */

export const getGips = (id, options) =>
  get(`${BASE}/${id}/gips`, undefined, options)

export const updateGips = (id, payload, options) =>
  put(`${BASE}/${id}/gips`, payload, options)

/* ---- НДС ---- */

export const updateVat = (id, payload, options) =>
  patch(`${BASE}/${id}/vat`, payload, options)

/* ---- De-jure / De-facto ---- */

export const getDejure = (id, options) =>
  get(`${BASE}/${id}/dejure`, undefined, options)

export const getDefacto = (id, options) =>
  get(`${BASE}/${id}/defacto`, undefined, options)

/* ---- Этапы сделки (stages) ---- */

export const listStages = (dealId, options) =>
  get(`${STAGES_BASE}/deal/${dealId}`, undefined, options)

export const listStageProducts = (dealId, options) =>
  get(`${STAGES_BASE}/deal/${dealId}/products`, undefined, options)

export const listStageDependencies = (dealId, options) =>
  get(`${STAGES_BASE}/deal/${dealId}/dependencies`, undefined, options)

export const createStage = (payload, options) =>
  post(`${STAGES_BASE}/`, payload, options)

export const updateStage = (stageId, payload, options) =>
  put(`${STAGES_BASE}/${stageId}`, payload, options)

export const removeStage = (stageId, options) =>
  del(`${STAGES_BASE}/${stageId}`, options)

export const copyStage = (stageId, payload, options) =>
  post(`${STAGES_BASE}/${stageId}/copy`, payload, options)

export const updateStageProducts = (stageId, payload, options) =>
  put(`${STAGES_BASE}/${stageId}/products`, payload, options)

export const updateStageDependency = (stageId, payload, options) =>
  put(`${STAGES_BASE}/${stageId}/dependency`, payload, options)

/* ---- Субподрядные этапы ---- */

export const getSubStage = (stageId, options) =>
  get(`${SUB_STAGES_BASE}/${stageId}`, undefined, options)

export const createSubStage = (payload, options) =>
  post(`${SUB_STAGES_BASE}/`, payload, options)

export const updateSubStage = (stageId, payload, options) =>
  put(`${SUB_STAGES_BASE}/${stageId}`, payload, options)

export const removeSubStage = (stageId, options) =>
  del(`${SUB_STAGES_BASE}/${stageId}`, options)

export const updateSubStageDependency = (stageId, payload, options) =>
  put(`${SUB_STAGES_BASE}/${stageId}/dependency`, payload, options)

export const listSubStageDependencies = (subcontractorId, options) =>
  get(`${SUB_STAGES_BASE}/subcontractor/${subcontractorId}/dependencies`, undefined, options)

/* ---- Субподрядные товары ---- */

export const createSubProduct = (payload, options) =>
  post(`${SUB_PRODUCTS_BASE}/`, payload, options)

export const updateSubProduct = (productId, payload, options) =>
  put(`${SUB_PRODUCTS_BASE}/${productId}`, payload, options)

export const removeSubProduct = (productId, options) =>
  del(`${SUB_PRODUCTS_BASE}/${productId}`, options)

/* ---- De-facto: assignments & subtasks ---- */

export const updateAssignment = (assignmentId, payload, options) =>
  put(`${DEFACTO_BASE}/assignments/${assignmentId}`, payload, options)

export const autoSubtasks = (assignmentId, options) =>
  post(`${DEFACTO_BASE}/assignments/${assignmentId}/subtasks/auto`, undefined, options)

export const createSubtask = (payload, options) =>
  post(`${DEFACTO_BASE}/subtasks`, payload, options)

export const updateSubtask = (subtaskId, payload, options) =>
  put(`${DEFACTO_BASE}/subtasks/${subtaskId}`, payload, options)

export const removeSubtask = (subtaskId, options) =>
  del(`${DEFACTO_BASE}/subtasks/${subtaskId}`, options)
