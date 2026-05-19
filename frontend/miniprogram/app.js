/**
 * 应用入口文件
 * 股票量化分析与预测系统 - 微信小程序
 */
App({
  globalData: {
    // API 基础地址 - 请根据实际部署环境修改
    apiBaseUrl: 'http://localhost:8000',
    // 用户信息
    userInfo: null,
    // 股票列表缓存
    stockListCache: []
  },

  onLaunch() {
    // 检查网络状态
    this.checkNetwork()
    // 初始化数据
    this.initData()
  },

  /**
   * 检查网络状态
   */
  checkNetwork() {
    wx.onNetworkStatusChange(res => {
      if (!res.isConnected) {
        wx.showToast({
          title: '网络已断开',
          icon: 'none'
        })
      }
    })
  },

  /**
   * 初始化数据
   */
  initData() {
    // 尝试获取本地缓存的股票列表
    const cachedList = wx.getStorageSync('stockList')
    if (cachedList) {
      this.globalData.stockListCache = cachedList
    }
  },

  /**
   * 获取 API 地址
   * @returns {string} API 基础地址
   */
  getApiUrl() {
    // 支持自定义 API 地址
    const customUrl = wx.getStorageSync('customApiUrl')
    return customUrl || this.globalData.apiBaseUrl
  },

  /**
   * 设置自定义 API 地址
   * @param {string} url - API 地址
   */
  setApiUrl(url) {
    this.globalData.apiBaseUrl = url
    wx.setStorageSync('customApiUrl', url)
  }
})
