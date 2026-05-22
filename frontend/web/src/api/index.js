import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  /** 增加到60s：akshare/baostock外部数据源首次抓取可能较慢 */
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => config,
  error => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

/** 请求拦截器：添加防缓存时间戳 */
apiClient.interceptors.request.use(
  config => {
    // 对 GET 请求添加 _t 时间戳防止缓存
    if (config.method === 'get') {
      config.params = config.params || {}
      config.params._t = Date.now()
    }
    return config
  },
  error => Promise.reject(error)
)

// API 模块
export { systemApi } from './system'
export { stockApi } from './stock'
export { backtestApi } from './backtest'
export { predictApi } from './predict'

export default apiClient
