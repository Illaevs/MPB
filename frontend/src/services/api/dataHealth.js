import { get, post, rawRequest } from './_client'

const BASE = '/api/v1/data-health'

export const listIssues = (params, options) =>
  get(`${BASE}/issues`, params, options)

export const listDealIssues = (dealId, params, options) =>
  get(`${BASE}/deals/${dealId}/issues`, params, options)

export const listIssueGroups = (params, options) =>
  get(`${BASE}/issues/groups`, params, options)

export const ignoreIssue = (issueId, payload, options) =>
  post(`${BASE}/issues/${issueId}/ignore`, payload, options)

export const openIssue = (issueId, options) =>
  post(`${BASE}/issues/${issueId}/open`, undefined, options)

export const downloadReportPdf = (params, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/report.pdf`,
    params,
    responseType: 'blob',
    ...options,
  })
