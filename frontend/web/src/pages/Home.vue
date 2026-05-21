<template>
  <div class="terminal-container">
    <!-- 顶部导航栏 -->
    <header class="terminal-header">
      <div class="header-left">
        <div class="logo">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="6" fill="url(#logoGrad)"/>
            <path d="M7 20L10 13L13 17L16 10L21 15" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="logoGrad" x1="0" y1="0" x2="28" y2="28">
                <stop stop-color="#3B82F6"/>
                <stop offset="1" stop-color="#1D4ED8"/>
              </linearGradient>
            </defs>
          </svg>
          <span class="logo-text">QuantTerminal</span>
        </div>
        
        <!-- 搜索框 -->
        <div class="search-box">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
          <input 
            type="text" 
            v-model="searchKeyword" 
            placeholder="输入股票代码或名称搜索..."
            @keyup.enter="handleSearch"
          />
        </div>
      </div>

      <nav class="header-nav">
        <a href="#" class="nav-item active">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9,22 9,12 15,12 15,22"/>
          </svg>
          <span>首页</span>
        </a>
        <a href="#" class="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
          </svg>
          <span>行情</span>
        </a>
        <a href="#" class="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
          <span>财务</span>
        </a>
        <a href="#" class="nav-item" @click.prevent="goToBacktest">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span>回测</span>
        </a>
      </nav>

      <div class="header-right">
        <button class="header-btn" title="刷新数据" @click="refreshData">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23,4 23,10 17,10"/>
            <polyline points="1,20 1,14 7,14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
        </button>
        <div class="time-display">
          <span class="time-text font-mono">{{ currentTime }}</span>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="terminal-main">
      <!-- 左侧：自选股列表 -->
      <div class="watchlist-panel">
        <div class="panel-header">
          <div class="panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
            </svg>
            <span>我的自选</span>
            <span class="stock-count font-mono">({{ watchlist.length }})</span>
          </div>
          <div class="panel-actions">
            <button class="add-btn" @click="showAddDialog = true" title="添加自选">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 股票列表 -->
        <div class="stock-list" v-loading="loading">
          <div 
            v-for="stock in watchlist" 
            :key="stock.code"
            class="stock-item"
            :class="{ active: currentStock === stock.code }"
            @click="selectStock(stock)"
          >
            <div class="stock-info">
              <span class="stock-name">{{ stock.name }}</span>
              <span class="stock-code font-mono">{{ stock.code }}</span>
            </div>
            <div class="stock-price-info">
              <span class="current-price font-mono" :class="getPriceClass(stock.change)">
                {{ formatPrice(stock.price) }}
              </span>
              <div class="price-change font-mono" :class="getPriceClass(stock.change)">
                <span class="change-value">{{ stock.change >= 0 ? '+' : '' }}{{ formatPrice(stock.change) }}</span>
                <span class="change-percent">{{ stock.change >= 0 ? '+' : '' }}{{ formatPercent(stock.pct_change) }}%</span>
              </div>
            </div>
            <div class="mini-chart" ref="'chart-' + stock.code">
              <svg viewBox="0 0 60 30" class="sparkline">
                <polyline 
                  :points="getSparkline(stock.code)" 
                  fill="none" 
                  :stroke="stock.change >= 0 ? '#ef4444' : '#22c55e'" 
                  stroke-width="1.5"
                />
              </svg>
            </div>
          </div>

          <div v-if="watchlist.length === 0 && !loading" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
            </svg>
            <p>暂无自选股</p>
            <button class="add-stock-btn" @click="showAddDialog = true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              添加自选
            </button>
          </div>
        </div>
      </div>

      <!-- 中间：K线图 -->
      <div class="chart-panel">
        <div class="chart-header" v-if="selectedStock">
          <div class="selected-stock-info">
            <h2 class="selected-name">{{ selectedStock.name }}</h2>
            <span class="selected-code font-mono">{{ selectedStock.code }}</span>
          </div>
          <div class="selected-price">
            <span class="price font-mono" :class="getPriceClass(selectedStock.change)">
              {{ formatPrice(selectedStock.price) }}
            </span>
            <span class="change font-mono" :class="getPriceClass(selectedStock.change)">
              {{ selectedStock.change >= 0 ? '+' : '' }}{{ formatPrice(selectedStock.change) }}
              ({{ selectedStock.change >= 0 ? '+' : '' }}{{ formatPercent(selectedStock.pct_change) }}%)
            </span>
          </div>
          <div class="chart-actions">
            <button class="action-btn" title="添加自选" @click="addToWatchlist(selectedStock.code)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
              </svg>
            </button>
            <button class="action-btn" title="分享">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="5" r="3"/>
                <circle cx="6" cy="12" r="3"/>
                <circle cx="18" cy="19" r="3"/>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="chart-toolbar">
          <div class="period-tabs">
            <button 
              v-for="p in periods" 
              :key="p.value"
              :class="['period-tab', { active: currentPeriod === p.value }]"
              @click="changePeriod(p.value)"
            >
              {{ p.label }}
            </button>
          </div>
          <div class="adjust-tabs">
            <button :class="['adjust-tab', { active: adjustType === 'qfq' }]" @click="changeAdjust('qfq')">前复权</button>
            <button :class="['adjust-tab', { active: adjustType === 'hfq' }]" @click="changeAdjust('hfq')">后复权</button>
            <button :class="['adjust-tab', { active: adjustType === 'none' }]" @click="changeAdjust('none')">不复权</button>
          </div>
        </div>

        <div class="chart-info" v-if="chartData.length">
          <div class="ma-indicators">
            <span class="ma-item" style="color: var(--ma5)">MA5: {{ latestMa.ma5 || '--' }}</span>
            <span class="ma-item" style="color: var(--ma10)">MA10: {{ latestMa.ma10 || '--' }}</span>
            <span class="ma-item" style="color: var(--ma20)">MA20: {{ latestMa.ma20 || '--' }}</span>
            <span class="ma-item" style="color: var(--ma30)">MA30: {{ latestMa.ma30 || '--' }}</span>
          </div>
          <span class="volume-info">成交量: {{ formatVolume(latestVolume) }}</span>
        </div>

        <div ref="mainChartRef" class="main-chart"></div>
      </div>

      <!-- 右侧：快捷信息 -->
      <div class="info-panel">
        <!-- 市场概览 -->
        <div class="market-overview">
          <div class="panel-header">
            <span class="panel-title">市场概览</span>
          </div>
          <div class="market-list">
            <div class="market-item" v-for="m in marketData" :key="m.name">
              <span class="market-name">{{ m.name }}</span>
              <span class="market-value font-mono" :class="getPriceClass(m.change)">
                {{ formatPrice(m.value) }}
              </span>
              <span class="market-change font-mono" :class="getPriceClass(m.change)">
                {{ m.change >= 0 ? '+' : '' }}{{ formatPercent(m.change_pct) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- 热门股票 -->
        <div class="hot-stocks">
          <div class="panel-header">
            <span class="panel-title">热门股票</span>
          </div>
          <div class="hot-list">
            <div 
              v-for="(stock, idx) in hotStocks" 
              :key="stock.code"
              class="hot-item"
              @click="selectStock(stock)"
            >
              <span class="hot-rank">{{ idx + 1 }}</span>
              <div class="hot-info">
                <span class="hot-name">{{ stock.name }}</span>
                <span class="hot-code font-mono">{{ stock.code }}</span>
              </div>
              <div class="hot-price font-mono" :class="getPriceClass(stock.change)">
                {{ formatPrice(stock.price) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 涨幅榜 -->
        <div class="rank-panel">
          <div class="panel-header">
            <span class="panel-title">涨幅榜</span>
          </div>
          <div class="rank-list">
            <div 
              v-for="stock in gainers" 
              :key="stock.code"
              class="rank-item"
              @click="selectStock(stock)"
            >
              <span class="rank-name">{{ stock.name }}</span>
              <span class="rank-change font-mono price-up">+{{ formatPercent(stock.pct_change) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 添加自选股弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加自选股"
      width="400px"
      :modal="true"
      class="add-dialog"
    >
      <div class="search-input-wrapper">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
        </svg>
        <input 
          type="text" 
          v-model="addKeyword" 
          placeholder="输入股票代码或名称..."
          @input="searchStocks"
        />
      </div>
      <div class="search-results" v-if="searchResults.length">
        <div 
          v-for="stock in searchResults" 
          :key="stock.code"
          class="search-result-item"
          @click="addToWatchlist(stock.code)"
        >
          <span class="result-name">{{ stock.name }}</span>
          <span class="result-code font-mono">{{ stock.code }}</span>
        </div>
      </div>
    </el-dialog>

    <!-- 底部状态栏 -->
    <footer class="terminal-footer">
      <div class="footer-left">
        <span class="status-item">
          <span class="status-dot" :class="wsStatusClass"></span>
          WebSocket: {{ wsStatusText }}
        </span>
        <span class="status-item">行情延迟: &lt;1s</span>
      </div>
      <div class="footer-center">
        <span class="disclaimer">本系统仅供学习研究使用，预测结果仅供参考，不构成投资建议</span>
      </div>
      <div class="footer-right">
        <span class="version">v4.0.0</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'

const router = useRouter()

// ============ WebSocket 实时行情 ============
const { connectionStatus, quotes, subscribe, unsubscribe } = useWebSocket()

// ============ 状态变量 ============
const loading = ref(false)
const searchKeyword = ref('')
const addKeyword = ref('')
const showAddDialog = ref(false)
const currentTime = ref('')
const mainChartRef = ref(null)
let chartInstance = null
let timeTimer = null

// 自选股列表
const watchlist = ref([])
const currentStock = ref('')
const selectedStock = ref(null)

// K线图配置
const periods = [
  { label: '日', value: 'daily' },
  { label: '周', value: 'weekly' },
  { label: '月', value: 'monthly' }
]
const currentPeriod = ref('daily')
const adjustType = ref('qfq')
const chartData = ref([])

// 市场数据
const marketData = ref([
  { name: '上证指数', value: 3285.67, change: 15.23, change_pct: 0.47 },
  { name: '深证成指', value: 10956.32, change: -23.45, change_pct: -0.21 },
  { name: '创业板指', value: 2156.78, change: 12.34, change_pct: 0.58 },
  { name: '沪深300', value: 3892.12, change: 8.56, change_pct: 0.22 }
])

// 热门股票
const hotStocks = ref([
  { name: '贵州茅台', code: '600519', price: 1688.00, change: 25.60, pct_change: 1.54 },
  { name: '宁德时代', code: '300750', price: 198.50, change: -3.20, pct_change: -1.59 },
  { name: '比亚迪', code: '002594', price: 267.80, change: 5.40, pct_change: 2.06 },
  { name: '中国平安', code: '601318', price: 45.23, change: 0.87, pct_change: 1.96 }
])

// 涨幅榜
const gainers = ref([
  { name: '剑桥科技', code: '603083', pct_change: 10.02 },
  { name: '中科曙光', code: '603019', pct_change: 9.99 },
  { name: '浪潮信息', code: '000977', pct_change: 9.97 },
  { name: '紫光股份', code: '000938', pct_change: 9.95 },
  { name: '科大讯飞', code: '002230', pct_change: 9.93 }
])

// 搜索结果
const searchResults = ref([])

// ============ WebSocket 响应式联动 ============
/** 监听 connectionStatus 变化, 自动管理 WebSocket 连接 */
watch(connectionStatus, (status) => {
  if (status === 'connected') {
    const codes = watchlist.value.map(s => s.code).filter(Boolean)
    if (codes.length > 0) subscribe(codes)
  }
})

/** 监听自选股列表变化，更新 WebSocket 订阅 */
watch(() => watchlist.value.map(s => s.code), (newCodes, oldCodes) => {
  if (connectionStatus.value !== 'connected') return

  const removed = (oldCodes || []).filter(c => !newCodes.includes(c))
  if (removed.length > 0) unsubscribe(removed)

  const added = newCodes.filter(c => !(oldCodes || []).includes(c))
  if (added.length > 0) subscribe(added)
}, { deep: true })

/** 实时行情到达时，同步更新自选股列表中的价格 */
watch(() => quotes.value, (newQuotes) => {
  let hasChange = false
  const updated = watchlist.value.map(stock => {
    const q = newQuotes[stock.code]
    if (q && q.price !== undefined) {
      hasChange = true
      return {
        ...stock,
        name: q.name || stock.name,
        price: q.price,
        change: q.change || 0,
        pct_change: q.pct_change || 0
      }
    }
    return stock
  })
  if (hasChange) {
    watchlist.value = updated
    if (currentStock.value && newQuotes[currentStock.value]) {
      const q = newQuotes[currentStock.value]
      if (selectedStock.value) {
        selectedStock.value = {
          ...selectedStock.value,
          name: q.name || selectedStock.value.name,
          price: q.price,
          change: q.change || 0,
          pct_change: q.pct_change || 0
        }
      }
    }
  }
  const hotUpdated = hotStocks.value.map(stock => {
    const q = newQuotes[stock.code]
    if (q && q.price !== undefined) {
      return {
        ...stock,
        price: q.price,
        change: q.change || 0,
        pct_change: q.pct_change || 0
      }
    }
    return stock
  })
  hotStocks.value = hotUpdated
})

// ============ 计算属性 ============
/** WebSocket 连接状态文本 */
const wsStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '实时在线'
    case 'connecting': return '连接中...'
    default: return '离线'
  }
})

/** WebSocket 连接状态 CSS class */
const wsStatusClass = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return 'online'
    case 'connecting': return 'connecting'
    default: return 'offline'
  }
})

const latestMa = computed(() => {
  if (!chartData.value.length) return {}
  const latest = chartData.value[chartData.value.length - 1]
  return {
    ma5: latest.ma5,
    ma10: latest.ma10,
    ma20: latest.ma20,
    ma30: latest.ma30
  }
})

const latestVolume = computed(() => {
  if (!chartData.value.length) return 0
  return chartData.value[chartData.value.length - 1].volume
})

// ============ 格式化函数 ============
const formatPrice = (val) => {
  if (!val && val !== 0) return '--'
  return Number(val).toFixed(2)
}

const formatPercent = (val) => {
  if (!val && val !== 0) return '--'
  return Number(val).toFixed(2)
}

const formatVolume = (val) => {
  if (!val && val !== 0) return '--'
  val = Number(val)
  if (val >= 100000000) return (val / 100000000).toFixed(2) + '亿'
  if (val >= 10000) return (val / 10000).toFixed(2) + '万'
  return val.toFixed(0)
}

const getPriceClass = (val) => {
  if (!val) return ''
  return val > 0 ? 'price-up' : val < 0 ? 'price-down' : ''
}

const getSparkline = (code) => {
  // 模拟生成迷你折线图
  const points = []
  let y = 15
  for (let i = 0; i < 10; i++) {
    y += (Math.random() - 0.5) * 6
    y = Math.max(5, Math.min(25, y))
    points.push(`${i * 7},${y}`)
  }
  return points.join(' ')
}

// ============ 事件处理 ============
const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push(`/stock/${searchKeyword.value.trim()}`)
  }
}

const selectStock = (stock) => {
  currentStock.value = stock.code
  selectedStock.value = stock
  router.push(`/stock/${stock.code}`)
}

const changePeriod = (period) => {
  currentPeriod.value = period
  loadChartData()
}

const changeAdjust = (type) => {
  adjustType.value = type
  loadChartData()
}

const goToBacktest = () => {
  router.push('/backtest')
}

/**
 * 添加自选股
 * 使用模拟数据初始化，实际行情由 WebSocket 后续推送更新
 */
const addToWatchlist = (code) => {
  if (!watchlist.value.find(s => s.code === code)) {
    watchlist.value.push({
      code,
      name: `股票${code}`,
      price: 10.0 + Math.random() * 50,
      change: (Math.random() - 0.5) * 2,
      pct_change: (Math.random() - 0.5) * 5
    })
    ElMessage.success('已添加到自选')
    showAddDialog.value = false
  } else {
    ElMessage.info('已在自选列表中')
  }
}

const searchStocks = () => {
  // 模拟搜索结果
  if (addKeyword.value.length >= 1) {
    searchResults.value = [
      { name: `股票A${addKeyword.value}`, code: '600000' },
      { name: `股票B${addKeyword.value}`, code: '000001' },
      { name: `股票C${addKeyword.value}`, code: '300001' }
    ]
  } else {
    searchResults.value = []
  }
}

const refreshData = () => {
  ElMessage.success('数据已刷新')
}

// ============ K线图 ============
const loadChartData = () => {
  // 模拟K线数据
  const mockData = []
  let basePrice = selectedStock.value?.price || 10.0
  const now = new Date()
  
  for (let i = 100; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    
    const open = basePrice
    const change = (Math.random() - 0.5) * 1.5
    const close = basePrice + change
    const high = Math.max(open, close) + Math.random() * 0.5
    const low = Math.min(open, close) - Math.random() * 0.5
    const volume = Math.floor(Math.random() * 10000000) + 1000000
    
    // 计算均线
    const ma5 = basePrice + (Math.random() - 0.5) * 0.5
    const ma10 = basePrice + (Math.random() - 0.5) * 0.8
    const ma20 = basePrice + (Math.random() - 0.5) * 1.0
    const ma30 = basePrice + (Math.random() - 0.5) * 1.2
    
    mockData.push({
      date: date.toISOString().split('T')[0],
      open,
      high,
      low,
      close,
      volume,
      ma5,
      ma10,
      ma20,
      ma30
    })
    
    basePrice = close
  }
  
  chartData.value = mockData
  updateChart()
}

const updateChart = () => {
  if (!chartInstance || !chartData.value.length) return

  const dates = chartData.value.map(d => d.date)
  const ohlc = chartData.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = chartData.value.map(d => d.volume)
  const volumesColor = chartData.value.map(d => 
    d.close >= d.open ? 'rgba(239, 68, 68, 0.5)' : 'rgba(34, 197, 94, 0.5)'
  )

  const option = {
    backgroundColor: 'transparent',
    animation: true,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: { color: '#3b82f6', opacity: 0.5 },
        crossStyle: { color: '#3b82f6', opacity: 0.5 }
      },
      backgroundColor: 'rgba(21, 28, 44, 0.95)',
      borderColor: '#1e293b',
      textStyle: { color: '#e8edf5', fontFamily: 'JetBrains Mono' }
    },
    legend: {
      data: ['MA5', 'MA10', 'MA20', 'MA30'],
      top: 0,
      right: 10,
      textStyle: { color: '#8b99ad' }
    },
    grid: [
      { left: '10px', right: '10px', top: '40px', height: '55%' },
      { left: '10px', right: '10px', top: '75%', height: '20%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisTick: { show: false },
        axisLabel: { color: '#5c6a7e', fontSize: 10 }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisTick: { show: false },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#5c6a7e', fontSize: 10 }
      },
      {
        scale: true,
        gridIndex: 1,
        splitLine: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], bottom: '2%', height: '15px', borderColor: '#1e293b' }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef4444',
          color0: '#22c55e',
          borderColor: '#dc2626',
          borderColor0: '#16a34a'
        }
      },
      {
        name: 'MA5', type: 'line', data: chartData.value.map(d => d.ma5),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#f59e0b', width: 1 }, symbol: 'none'
      },
      {
        name: 'MA10', type: 'line', data: chartData.value.map(d => d.ma10),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#3b82f6', width: 1 }, symbol: 'none'
      },
      {
        name: 'MA20', type: 'line', data: chartData.value.map(d => d.ma20),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#22d3ee', width: 1 }, symbol: 'none'
      },
      {
        name: 'MA30', type: 'line', data: chartData.value.map(d => d.ma30),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#a78bfa', width: 1 }, symbol: 'none'
      },
      {
        name: '成交量', type: 'bar', data: volumes,
        xAxisIndex: 1, yAxisIndex: 1,
        itemStyle: { color: (params) => volumesColor[params.dataIndex] }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

const initChart = () => {
  if (mainChartRef.value && !chartInstance) {
    chartInstance = echarts.init(mainChartRef.value)
    window.addEventListener('resize', () => {
      chartInstance && chartInstance.resize()
    })
  }
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-')
}

// ============ 生命周期 ============
onMounted(() => {
  // 初始化时间
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  
  // 初始化自选股列表（行情由 WebSocket 实时更新）
  watchlist.value = [
    { name: '浦发银行', code: '600000', price: 7.85, change: 0.12, pct_change: 1.55 },
    { name: '平安银行', code: '000001', price: 11.23, change: -0.08, pct_change: -0.71 },
    { name: '万科A', code: '000002', price: 8.45, change: 0.25, pct_change: 3.05 },
    { name: '贵州茅台', code: '600519', price: 1688.00, change: 25.60, pct_change: 1.54 }
  ]
  
  selectedStock.value = watchlist.value[0]
  currentStock.value = selectedStock.value.code
  
  // 初始化图表
  initChart()
  loadChartData()
  
  // 启动 WebSocket 连接（自动订阅自选股 + 热门股）
  subscribe(watchlist.value.map(s => s.code).concat(hotStocks.value.map(s => s.code)))
})

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
/* ============ 容器 ============ */
.terminal-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

/* ============ 顶部导航 ============ */
.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-text {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-box input {
  width: 240px;
  height: 34px;
  padding: 0 12px 0 36px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.search-box input:focus {
  border-color: var(--accent-blue);
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--text-muted);
}

.header-nav {
  display: flex;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  font-size: 13px;
  cursor: pointer;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--bg-active);
  color: var(--accent-blue);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.header-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-accent);
}

.time-display {
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.time-text {
  font-size: 12px;
  color: var(--text-secondary);
}

/* ============ 主内容区 ============ */
.terminal-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 12px;
  gap: 12px;
}

/* ============ 自选股面板 ============ */
.watchlist-panel {
  width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-muted);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.panel-title svg {
  color: var(--accent-gold);
}

.stock-count {
  font-weight: 400;
  color: var(--text-muted);
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--accent-blue);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-btn:hover {
  background: #2563eb;
}

.stock-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.stock-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.stock-item:hover {
  background: var(--bg-hover);
}

.stock-item.active {
  background: var(--bg-active);
  border: 1px solid var(--border-accent);
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.stock-code {
  font-size: 11px;
  color: var(--text-muted);
}

.stock-price-info {
  text-align: right;
}

.current-price {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.price-change {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 11px;
}

.mini-chart {
  width: 60px;
  height: 30px;
}

.sparkline {
  width: 100%;
  height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-muted);
  text-align: center;
}

.empty-state svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin-bottom: 16px;
  font-size: 13px;
}

.add-stock-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--accent-blue);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-stock-btn:hover {
  background: #2563eb;
}

/* ============ K线图面板 ============ */
.chart-panel {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-muted);
  gap: 20px;
}

.selected-stock-info {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.selected-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.selected-code {
  font-size: 13px;
  color: var(--text-muted);
}

.selected-price {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.selected-price .price {
  font-size: 28px;
  font-weight: 600;
}

.selected-price .change {
  font-size: 14px;
}

.chart-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-accent);
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-muted);
}

.period-tabs, .adjust-tabs {
  display: flex;
  gap: 4px;
}

.period-tab, .adjust-tab {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.period-tab:hover, .adjust-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.period-tab.active, .adjust-tab.active {
  background: var(--accent-blue);
  color: white;
}

.chart-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-muted);
}

.ma-indicators {
  display: flex;
  gap: 16px;
}

.ma-item {
  font-family: var(--font-mono);
  font-size: 12px;
}

.volume-info {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
}

.main-chart {
  flex: 1;
  min-height: 400px;
}

/* ============ 右侧信息面板 ============ */
.info-panel {
  width: 260px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
}

.market-overview, .hot-stocks, .rank-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.market-list, .hot-list, .rank-list {
  padding: 8px;
}

.market-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 8px;
  padding: 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.market-item:hover {
  background: var(--bg-hover);
}

.market-name {
  color: var(--text-secondary);
}

.market-value {
  font-weight: 500;
}

.market-change {
  font-size: 11px;
}

.hot-item, .rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.hot-item:hover, .rank-item:hover {
  background: var(--bg-hover);
}

.hot-rank {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
}

.hot-item:nth-child(1) .hot-rank {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.hot-item:nth-child(2) .hot-rank {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.hot-item:nth-child(3) .hot-rank {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.hot-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hot-name {
  font-size: 13px;
  font-weight: 500;
}

.hot-code {
  font-size: 10px;
  color: var(--text-muted);
}

.hot-price {
  font-size: 12px;
  font-weight: 500;
}

.rank-name {
  flex: 1;
  font-size: 12px;
}

.rank-change {
  font-size: 12px;
  font-weight: 500;
}

/* ============ 添加自选弹窗 ============ */
.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  margin-bottom: 12px;
}

.search-input-wrapper input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}

.search-input-wrapper svg {
  color: var(--text-muted);
}

.search-results {
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.search-result-item:hover {
  background: var(--bg-hover);
}

.result-name {
  font-size: 13px;
}

.result-code {
  font-size: 12px;
  color: var(--text-muted);
}

/* ============ 底部状态栏 ============ */
.terminal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 28px;
  padding: 0 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-default);
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.footer-left, .footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transition: all var(--transition-normal);
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
}

.status-dot.connecting {
  background: #f59e0b;
  box-shadow: 0 0 6px #f59e0b;
  animation: pulse 0.8s ease-in-out infinite;
}

.status-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
}

.disclaimer {
  color: var(--text-muted);
}
</style>
