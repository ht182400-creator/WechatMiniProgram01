/**
 * 首页
 */
const { get } = require('../../utils/request')
const { formatDate } = require('../../utils/helpers')

Page({
  data: {
    updateTime: '',
    marketData: [
      { name: '上证指数', index: '--', change: '--', changePercent: '--', changeColor: '#999' },
      { name: '深证成指', index: '--', change: '--', changePercent: '--', changeColor: '#999' },
      { name: '创业板', index: '--', change: '--', changePercent: '--', changeColor: '#999' },
      { name: '沪深300', index: '--', change: '--', changePercent: '--', changeColor: '#999' }
    ],
    systemStatus: {
      backend: false,
      dataSource: ''
    }
  },

  onLoad() {
    this.checkSystemStatus()
    this.getMarketOverview()
  },

  onShow() {
    this.setData({
      updateTime: formatDate(new Date(), 'HH:mm:ss')
    })
  },

  onPullDownRefresh() {
    this.checkSystemStatus()
    this.getMarketOverview().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 检查系统状态
   */
  async checkSystemStatus() {
    try {
      const res = await get('/api/system/health', {}, '')
      // 后端返回顶层字段，不是嵌套在 data 里
      this.setData({
        'systemStatus.backend': true,
        'systemStatus.dataSource': res.datasource_available ? 'AKShare' : '离线'
      })
    } catch (err) {
      console.error('后端连接失败:', err)
      this.setData({
        'systemStatus.backend': false,
        'systemStatus.dataSource': '离线'
      })
      wx.showToast({
        title: '后端服务连接失败',
        icon: 'none',
        duration: 2000
      })
    }
  },

  /**
   * 获取市场概览
   */
  async getMarketOverview() {
    try {
      const res = await get('/api/stock/list', { limit: 4 }, '')
      // 后端返回 { total, stocks } 或 { data } 两种格式，兼容处理
      const stockList = res.stocks || res.data || []
      if (stockList.length > 0) {
        const marketData = stockList.slice(0, 4).map((item, index) => {
          const names = ['上证指数', '深证成指', '创业板指', '沪深300']
          return {
            name: item.name || names[index] || '未知',
            index: item.price || '--',
            change: item.change >= 0 ? `+${item.change}` : `${item.change}`,
            changePercent: `${item.change >= 0 ? '+' : ''}${(item.change_percent || 0).toFixed(2)}%`,
            changeColor: item.change >= 0 ? '#ff4d4f' : '#52c41a'
          }
        })
        this.setData({ marketData })
      }
    } catch (err) {
      console.error('获取市场数据失败', err)
    }
  },

  /**
   * 跳转到股票页面
   */
  navigateToStock() {
    wx.switchTab({ url: '/pages/stock/stock' })
  },

  /**
   * 跳转到回测页面
   */
  navigateToBacktest() {
    wx.switchTab({ url: '/pages/backtest/backtest' })
  },

  /**
   * 跳转到预测页面
   */
  navigateToPredict() {
    wx.switchTab({ url: '/pages/predict/predict' })
  },

  /**
   * 显示 API 设置
   */
  showApiSettings() {
    wx.showModal({
      title: 'API 设置',
      editable: true,
      placeholderText: '请输入后端 API 地址',
      success: (res) => {
        if (res.confirm && res.content) {
          const app = getApp()
          app.setApiUrl(res.content)
          wx.showToast({ title: '设置成功', icon: 'success' })
          this.checkSystemStatus()
        }
      }
    })
  }
})
