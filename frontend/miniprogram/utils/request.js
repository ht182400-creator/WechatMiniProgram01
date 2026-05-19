/**
 * HTTP 请求工具类
 * 基于 wx.request 封装，统一处理 API 调用
 */

/**
 * 获取应用实例
 */
const app = getApp()

/**
 * API 请求封装
 * @param {Object} options - 请求配置
 * @returns {Promise} 请求结果
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const apiUrl = app.globalData.apiBaseUrl
    
    wx.showLoading({
      title: options.loadingText || '加载中...',
      mask: true
    })

    wx.request({
      url: `${apiUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success(res) {
        wx.hideLoading()
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject({
            code: res.statusCode,
            message: res.data?.message || '请求失败'
          })
        }
      },
      fail(err) {
        wx.hideLoading()
        reject({
          code: -1,
          message: '网络请求失败，请检查网络连接'
        })
      }
    })
  })
}

/**
 * GET 请求
 * @param {string} url - 请求地址
 * @param {Object} data - 请求参数
 * @param {string} loadingText - 加载提示文字
 * @returns {Promise}
 */
function get(url, data = {}, loadingText = '加载中...') {
  return request({
    url,
    method: 'GET',
    data,
    loadingText
  })
}

/**
 * POST 请求
 * @param {string} url - 请求地址
 * @param {Object} data - 请求数据
 * @param {string} loadingText - 加载提示文字
 * @returns {Promise}
 */
function post(url, data = {}, loadingText = '提交中...') {
  return request({
    url,
    method: 'POST',
    data,
    loadingText
  })
}

/**
 * 上传文件
 * @param {string} filePath - 文件路径
 * @param {string} name - 文件字段名
 * @param {Object} formData - 附加表单数据
 * @returns {Promise}
 */
function uploadFile(filePath, name = 'file', formData = {}) {
  return new Promise((resolve, reject) => {
    const apiUrl = app.globalData.apiBaseUrl
    
    wx.showLoading({
      title: '上传中...',
      mask: true
    })

    wx.uploadFile({
      url: `${apiUrl}/api/upload`,
      filePath,
      name,
      formData,
      success(res) {
        wx.hideLoading()
        if (res.statusCode === 200) {
          resolve(JSON.parse(res.data))
        } else {
          reject({
            code: res.statusCode,
            message: '上传失败'
          })
        }
      },
      fail(err) {
        wx.hideLoading()
        reject({
          code: -1,
          message: '上传失败，请检查网络连接'
        })
      }
    })
  })
}

module.exports = {
  request,
  get,
  post,
  uploadFile
}
