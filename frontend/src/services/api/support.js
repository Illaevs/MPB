import { get, post, patch, del } from './_client'

/** Тех. поддержка — тикет-система. */
const BASE = '/api/v1/support'

export const listTickets = (params, options) =>
  get(`${BASE}/tickets`, params, options)

export const getTicket = (id, options) =>
  get(`${BASE}/tickets/${id}`, undefined, options)

export const createTicket = (formData, options) =>
  post(`${BASE}/tickets`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const updateTicket = (id, payload, options) =>
  patch(`${BASE}/tickets/${id}`, payload, options)

export const addMessage = (ticketId, formData, options) =>
  post(`${BASE}/tickets/${ticketId}/messages`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const updateMessage = (messageId, payload, options) =>
  patch(`${BASE}/messages/${messageId}`, payload, options)

export const deleteMessage = (messageId, options) =>
  del(`${BASE}/messages/${messageId}`, options)

export const createTaskFromTicket = (ticketId, payload, options) =>
  post(`${BASE}/tickets/${ticketId}/create-task`, payload, options)
