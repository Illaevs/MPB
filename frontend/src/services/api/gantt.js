import { get, post, put, del } from './_client'

export const listDeals = (options) => get('/api/v1/deals/', undefined, options)
export const listSubcontractors = (options) =>
  get('/api/v1/subcontractors/', undefined, options)

export const listDealStages = (dealId, options) =>
  get(`/api/v1/stages/deal/${dealId}`, undefined, options)

export const listSubcontractorStages = (subcontractorId, options) =>
  get(`/api/v1/subcontractor-stages/subcontractor/${subcontractorId}`, undefined, options)

export const createDealStage = (payload, options) =>
  post('/api/v1/stages/', payload, options)
export const updateDealStage = (stageId, payload, options) =>
  put(`/api/v1/stages/${stageId}`, payload, options)
export const removeDealStage = (stageId, options) =>
  del(`/api/v1/stages/${stageId}`, options)

export const createSubcontractorStage = (payload, options) =>
  post('/api/v1/subcontractor-stages/', payload, options)
export const updateSubcontractorStage = (stageId, payload, options) =>
  put(`/api/v1/subcontractor-stages/${stageId}`, payload, options)
export const removeSubcontractorStage = (stageId, options) =>
  del(`/api/v1/subcontractor-stages/${stageId}`, options)

export const dealDefacto = (dealId, options) =>
  get(`/api/v1/deals/${dealId}/defacto`, undefined, options)
