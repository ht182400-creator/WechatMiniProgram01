import apiClient from './index.js'

export const stockApi = {
  list: (params) => apiClient.get('/stock/list', { params }),
  getList: () => apiClient.get('/stock/list'),
  detail: (code) => apiClient.get(`/stock/${code}`),
  kline: (code, params) => apiClient.get(`/stock/${code}/kline`, { params }),
  search: (keyword) => apiClient.get('/stock/search', { params: { keyword } }),
  getRealtime: (code) => apiClient.get('/stock/realtime', { params: { codes: code } }),
  getChartData: (code, chartType, days) => apiClient.get('/stock/chart', { params: { code, chart_type: chartType, days } }),
  getIndicators: (code, days) => apiClient.get('/stock/indicators', { params: { code, days } })
}

export default stockApi
