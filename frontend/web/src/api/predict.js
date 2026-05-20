import apiClient from './index.js'

export const predictApi = {
  predict: (code, days = 5, modelType = 'rf') => apiClient.post('/predict/predict', null, { params: { code, days, model_type: modelType } }),
  getHistory: (params = { limit: 20 }) => apiClient.get('/predict/history', { params }),
  history: (params) => apiClient.get('/predict/history', { params })
}

export default predictApi
