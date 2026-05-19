/**
 * 股票查询页面
 */
const { get } = require('../../utils/request')
const { getChangeColor, getChangeText, debounce } = require('../../utils/helpers')

Page({
  data: {
    searchKey: '',
    stockList: [],
    loading: false,
    page: 1,
    pageSize: 20,
    hasMore: true
  },

  onLoad() {
    this.loadStockList()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, stockList: [], hasMore: true })
    this.loadStockList().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 })
      this.loadStockList()
    }
  },

  /**
   * 搜索输入
   */
  onSearchInput(e) {
    this.setData({ searchKey: e.detail.value })
  },

  /**
   * 搜索
   */
  onSearch: debounce(function() {
    this.setData({ page: 1, stockList: [], hasMore: true })
    this.loadStockList()
  }, 300),

  /**
   * 加载股票列表
   */
  async loadStockList() {
    if (this.data.loading || !this.data.hasMore) return
    
    this.setData({ loading: true })
    
    try {
      const params = {
        page: this.data.page,
        page_size: this.data.pageSize
      }
      
      if (this.data.searchKey) {
        params.keyword = this.data.searchKey
      }
      
      const res = await get('/api/stock/list', params)
      const newList = (res.data || []).map(item => ({
        ...item,
        changeColor: getChangeColor(item.change),
        changeText: getChangeText(item.change)
      }))
      
      this.setData({
        stockList: this.data.page === 1 ? newList : [...this.data.stockList, ...newList],
        hasMore: newList.length >= this.data.pageSize
      })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  /**
   * 点击股票
   */
  onStockTap(e) {
    const code = e.currentTarget.dataset.code
    wx.navigateTo({
      url: `/pages/stock/stock?code=${code}`
    })
  }
})
