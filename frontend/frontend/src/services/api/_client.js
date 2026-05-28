import axios from 'axios'

/**
 * Тонкая обёртка над глобальным axios, общая для всех доменных API-модулей.
 *
 * Зачем:
 * - Один источник правды по baseURL/timeout.
 * - Возврат уже распакованного response.data (бизнес-код не должен знать про .data).
 * - Поддержка AbortController через { signal } — для отмены запросов на смене страниц.
 *
 * Interceptor'ы (CSRF, 401-refresh) уже навешены в services/http.js на сам axios,
 * поэтому здесь мы не дублируем эту логику.
 */

const DEFAULT_TIMEOUT = 60_000

export async function request({
  method = 'get',
  url,
  params,
  data,
  headers,
  signal,
  responseType,
  timeout,
  withCredentials = true,
} = {}) {
  if (!url) {
    throw new Error('api request: url is required')
  }
  const response = await axios.request({
    method,
    url,
    params,
    data,
    headers,
    signal,
    responseType,
    timeout: timeout ?? DEFAULT_TIMEOUT,
    withCredentials,
  })
  return response.data
}

export const get = (url, params, options) =>
  request({ method: 'get', url, params, ...options })

export const post = (url, data, options) =>
  request({ method: 'post', url, data, ...options })

export const put = (url, data, options) =>
  request({ method: 'put', url, data, ...options })

export const patch = (url, data, options) =>
  request({ method: 'patch', url, data, ...options })

export const del = (url, options) =>
  request({ method: 'delete', url, ...options })

/**
 * Для случаев, когда нужно работать с самим Response (download blob и т.п.):
 * возвращает полный axios response, а не только .data.
 */
export async function rawRequest(options) {
  if (!options?.url) {
    throw new Error('api rawRequest: url is required')
  }
  return axios.request({
    timeout: DEFAULT_TIMEOUT,
    withCredentials: true,
    ...options,
  })
}
