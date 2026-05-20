import apiClient from './index.js'

export const systemApi = {
  health: () => apiClient.get('/system/health'),
  healthCheck: () => apiClient.get('/system/health'),
  getInfo: () => apiClient.get('/system/info'),
  info: () => apiClient.get('/system/info'),
  strategies: () => apiClient.get('/system/strategies'),
  getDatasources: () => apiClient.get('/system/datasources'),
  datasources: () => apiClient.get('/system/datasources'),
  clearCache: () => apiClient.post('/system/cache/clear')
}

export default systemApi
