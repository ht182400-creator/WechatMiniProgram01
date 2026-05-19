/**
 * 预测页面
 */
const { get, post } = require('../../utils/request')

Page({
  data: {
    stockCode: '000001',
    predictDays: 5,
    dayRange: [3, 5, 7, 10, 15, 20],
    predicting: false,
    result: null,
    history: []
  },

  onLoad() {
    this.loadHistory()
  },

  /**
   * 输入变化
   */
  onInputChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },

  /**
   * 预测天数变化
   */
  onDaysChange(e) {
    const index = e.detail.value
    const days = [3, 5, 7, 10, 15, 20][index]
    this.setData({ predictDays: days })
  },

  /**
   * 执行预测
   */
  async doPredict() {
    const { stockCode, predictDays } = this.data
    
    if (!stockCode) {
      wx.showToast({ title: '请输入股票代码', icon: 'none' })
      return
    }

    this.setData({ predicting: true })

    try {
      const params = {
        stock_code: stockCode,
        days: predictDays
      }

      const res = await post('/api/predict/predict', params)
      
      if (res.data) {
        this.setData({ result: res.data })
        wx.showToast({ title: '预测完成', icon: 'success' })
        // 刷新历史记录
        this.loadHistory()
      } else {
        wx.showToast({ title: '预测失败', icon: 'none' })
      }
    } catch (err) {
      wx.showToast({ title: err.message || '预测失败', icon: 'none' })
    } finally {
      this.setData({ predicting: false })
    }
  },

  /**
   * 加载历史预测
   */
  async loadHistory() {
    try {
      const res = await get('/api/predict/history', {}, '')
      this.setData({ history: res.data || [] })
    } catch (err) {
      console.error('加载历史预测失败', err)
    }
  }
})
