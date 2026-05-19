/**
 * 回测页面
 */
const { get, post } = require('../../utils/request')

Page({
  data: {
    strategies: [
      { key: 'ma_cross', name: '均线交叉' },
      { key: 'rsi', name: 'RSI策略' },
      { key: 'macd', name: 'MACD策略' },
      { key: 'bollinger', name: '布林带策略' }
    ],
    selectedStrategy: 'ma_cross',
    stockCode: '000001',
    startDate: '2024-01-01',
    endDate: '2025-01-01',
    initialCapital: '100000',
    running: false,
    result: null
  },

  onLoad() {
    // 设置默认日期
    const now = new Date()
    const endDate = now.toISOString().split('T')[0]
    const startDate = new Date(now.setFullYear(now.getFullYear() - 1)).toISOString().split('T')[0]
    this.setData({ startDate, endDate })
  },

  /**
   * 选择策略
   */
  onStrategySelect(e) {
    this.setData({
      selectedStrategy: e.currentTarget.dataset.key,
      result: null
    })
  },

  /**
   * 输入变化
   */
  onInputChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },

  /**
   * 日期变化
   */
  onDateChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },

  /**
   * 运行回测
   */
  async runBacktest() {
    const { stockCode, startDate, endDate, initialCapital, selectedStrategy } = this.data
    
    if (!stockCode) {
      wx.showToast({ title: '请输入股票代码', icon: 'none' })
      return
    }

    this.setData({ running: true, result: null })

    try {
      const params = {
        stock_code: stockCode,
        strategy: selectedStrategy,
        start_date: startDate,
        end_date: endDate,
        initial_capital: parseFloat(initialCapital) || 100000
      }

      const res = await post('/api/backtest/run', params)
      
      if (res.data) {
        this.setData({ result: res.data })
        wx.showToast({ title: '回测完成', icon: 'success' })
      } else {
        wx.showToast({ title: '回测失败', icon: 'none' })
      }
    } catch (err) {
      wx.showToast({ title: err.message || '回测失败', icon: 'none' })
    } finally {
      this.setData({ running: false })
    }
  }
})
