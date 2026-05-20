import apiClient from './index.js'

export const predictApi = {
  // 基础预测
  predict: (code, days = 5, modelType = 'rf') => 
    apiClient.post('/predict/predict', null, { params: { code, days, model_type: modelType } }),
  
  // 预测历史
  getHistory: (params = { limit: 20 }) => 
    apiClient.get('/predict/history', { params }),
  history: (params) => 
    apiClient.get('/predict/history', { params }),
  
  // 获取可用模型列表
  getModels: () => 
    apiClient.get('/predict/models'),
  
  // ========== 混合模型训练相关 ==========
  
  /**
   * 训练混合模型
   * @param {Object} params - 训练参数
   */
  trainHybrid: (params) => 
    apiClient.post('/predict/hybrid/train', params),
  
  /**
   * 混合模型预测
   * @param {Object} params - 预测参数
   */
  hybridPredict: (params) => 
    apiClient.post('/predict/hybrid/predict', params),
  
  /**
   * Walk-Forward 交叉验证
   * @param {Object} params - 验证参数
   */
  walkForward: (params) => 
    apiClient.post('/predict/hybrid/walkforward', params),
  
  /**
   * 获取已保存的模型列表
   */
  getSavedModels: () => 
    apiClient.get('/predict/models/saved'),
  
  /**
   * 删除已保存的模型
   * @param {string} modelName - 模型名称
   */
  deleteModel: (modelName) => 
    apiClient.delete(`/predict/models/${encodeURIComponent(modelName)}`)
}

export default predictApi
