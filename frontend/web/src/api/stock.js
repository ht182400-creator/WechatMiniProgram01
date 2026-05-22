import apiClient from './index.js'

export const stockApi = {
  // 股票列表与搜索
  list: (params) => apiClient.get('/stock/list', { params }),
  getList: () => apiClient.get('/stock/list'),
  detail: (code) => apiClient.get(`/stock/${code}`),
  kline: (code, params) => apiClient.get(`/stock/${code}/kline`, { params }),
  search: (keyword) => apiClient.get('/stock/search', { params: { keyword } }),
  
  // 实时行情
  getRealtime: (code) => apiClient.get('/stock/realtime', { params: { codes: code } }),
  
  // K线与图表数据（支持复权类型：qfq/hfq/none）
  getChartData: (code, chartType, days, adjustType = 'qfq') =>
    apiClient.get('/stock/chart', { params: { code, chart_type: chartType, days, adjust: adjustType } }),
  getMinuteData: (code, period) => apiClient.get('/stock/minute', { params: { code, period } }),
  
  // 技术指标
  getIndicators: (code, days) => apiClient.get('/stock/indicators', { params: { code, days } }),
  
  // 十档盘口
  getDepth: (code) => apiClient.get('/stock/depth', { params: { code } }),
  
  // 分笔成交
  getTransaction: (code, limit) => apiClient.get('/stock/transaction', { params: { code, limit } }),
  
  // 分时明细（回车弹窗用）
  getIntraday: (code, date) => apiClient.get('/stock/intraday', { params: { code, date: date || '' } })
}

export default stockApi
