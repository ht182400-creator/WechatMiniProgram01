import apiClient from './index.js'

export const backtestApi = {
  run: (params) => apiClient.post('/backtest/run', params),
  getHistory: (params = {}) => apiClient.get('/backtest/history', { params }),
  history: (params = {}) => apiClient.get('/backtest/history', { params }),
  detail: (id) => apiClient.get(`/backtest/${id}`),
  getStrategies: () => apiClient.get('/backtest/strategies')
}

export default backtestApi
