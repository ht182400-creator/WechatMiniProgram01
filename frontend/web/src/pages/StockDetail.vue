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
            placeholder="输入股票代码或名称..."
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
        <a href="#" class="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span>回测</span>
        </a>
      </nav>

      <div class="header-right">
        <button class="header-btn" title="刷新数据" @click="refreshAll">
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
      <!-- 左侧行情区 -->
      <div class="left-panel">
        <!-- 股票信息头部 -->
        <div class="stock-header-card">
          <div class="stock-main-info">
            <div class="stock-name-code">
              <h1 class="stock-name">{{ stockInfo.name || '加载中...' }}</h1>
              <span class="stock-code font-mono">{{ stockCode }}</span>
            </div>
            <div class="stock-price-info">
              <div class="current-price font-mono" :class="priceChange >= 0 ? 'price-up' : 'price-down'">
                {{ formatPrice(stockInfo.price || stockInfo.close) }}
              </div>
              <div class="price-change font-mono" :class="priceChange >= 0 ? 'price-up' : 'price-down'">
                <span class="change-value">{{ priceChange >= 0 ? '+' : '' }}{{ formatPrice(priceChange) }}</span>
                <span class="change-percent">({{ priceChangePct >= 0 ? '+' : '' }}{{ formatPercent(priceChangePct) }}%)</span>
              </div>
            </div>
          </div>
          
          <div class="stock-indicators">
            <div class="indicator-item">
              <span class="indicator-label">开盘</span>
              <span class="indicator-value font-mono">{{ formatPrice(stockInfo.open || stockInfo.pre_close) }}</span>
            </div>
            <div class="indicator-item">
              <span class="indicator-label">最高</span>
              <span class="indicator-value font-mono price-up">{{ formatPrice(stockInfo.high) }}</span>
            </div>
            <div class="indicator-item">
              <span class="indicator-label">最低</span>
              <span class="indicator-value font-mono price-down">{{ formatPrice(stockInfo.low) }}</span>
            </div>
            <div class="indicator-item">
              <span class="indicator-label">成交量</span>
              <span class="indicator-value font-mono">{{ formatVolume(stockInfo.volume) }}</span>
            </div>
            <div class="indicator-item">
              <span class="indicator-label">成交额</span>
              <span class="indicator-value font-mono">{{ formatAmount(stockInfo.amount) }}</span>
            </div>
            <div class="indicator-item">
              <span class="indicator-label">换手率</span>
              <span class="indicator-value font-mono">{{ formatPercent(stockInfo.turnover) }}</span>
            </div>
          </div>
        </div>

        <!-- K线图表 -->
        <div class="chart-card">
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
              <button 
                :class="['adjust-tab', { active: adjustType === 'qfq' }]"
                @click="changeAdjust('qfq')"
              >前复权</button>
              <button 
                :class="['adjust-tab', { active: adjustType === 'hfq' }]"
                @click="changeAdjust('hfq')"
              >后复权</button>
              <button 
                :class="['adjust-tab', { active: adjustType === 'none' }]"
                @click="changeAdjust('none')"
              >不复权</button>
            </div>
          </div>
          <div class="chart-info">
            <div class="ma-indicators">
              <span class="ma-item" style="color: var(--ma5)">MA5: {{ latestMa.ma5 || '--' }}</span>
              <span class="ma-item" style="color: var(--ma10)">MA10: {{ latestMa.ma10 || '--' }}</span>
              <span class="ma-item" style="color: var(--ma20)">MA20: {{ latestMa.ma20 || '--' }}</span>
              <span class="ma-item" style="color: var(--ma30)">MA30: {{ latestMa.ma30 || '--' }}</span>
            </div>
            <span class="volume-info">成交量: {{ formatVolume(latestVolume) }}</span>
          </div>
          <div ref="chartRef" class="kline-chart"></div>
        </div>

        <!-- 分笔成交 -->
        <div class="transaction-card">
          <div class="card-header">
            <span class="card-title">分笔成交</span>
            <span class="card-subtitle font-mono">共 {{ transactionList.length }} 笔</span>
          </div>
          <div class="transaction-table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>价格</th>
                  <th>涨跌</th>
                  <th>成交量</th>
                  <th>性质</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(t, idx) in transactionList" :key="idx" :class="getTransactionClass(t)">
                  <td class="font-mono">{{ t.time }}</td>
                  <td class="font-mono" :class="getPriceClass(t.change)">{{ formatPrice(t.price) }}</td>
                  <td class="font-mono" :class="getPriceClass(t.change)">
                    {{ t.change >= 0 ? '+' : '' }}{{ formatPrice(t.change) }}
                  </td>
                  <td class="font-mono">{{ formatVolume(t.volume) }}</td>
                  <td>
                    <span class="transaction-type" :class="t.type">
                      {{ t.type === 'buy' ? '买盘' : t.type === 'sell' ? '卖盘' : '中性' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 右侧信息区 -->
      <div class="right-panel">
        <!-- 五档盘口 -->
        <div class="quote-card">
          <div class="card-header">
            <span class="card-title">五档盘口</span>
          </div>
          <div class="quote-content">
            <div class="quote-table">
              <div class="quote-header">
                <span>卖盘</span>
                <span>价格</span>
                <span>买盘</span>
              </div>
              <div 
                v-for="i in 5" 
                :key="'quote-' + i"
                class="quote-row"
              >
                <div class="quote-cell sell">
                  <span class="quote-volume font-mono">{{ formatVolume(quoteData[6-i]?.sellVolume) }}</span>
                </div>
                <div class="quote-cell price font-mono" :class="getPriceClass(quoteData[6-i]?.priceChange)">
                  {{ formatPrice(quoteData[6-i]?.price) }}
                </div>
                <div class="quote-cell buy">
                  <span class="quote-volume font-mono">{{ formatVolume(quoteData[6-i]?.buyVolume) }}</span>
                </div>
              </div>
            </div>
            <div class="quote-summary">
              <div class="summary-row">
                <span class="summary-label">卖盘总量</span>
                <span class="summary-value sell-total font-mono">{{ formatVolume(sellTotal) }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">买盘总量</span>
                <span class="summary-value buy-total font-mono">{{ formatVolume(buyTotal) }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">净买卖差</span>
                <span class="summary-value net-diff font-mono" :class="netDiff >= 0 ? 'price-up' : 'price-down'">
                  {{ netDiff >= 0 ? '+' : '' }}{{ formatVolume(netDiff) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="action-card">
          <div class="card-header">
            <span class="card-title">快捷操作</span>
          </div>
          <div class="action-buttons">
            <button class="action-btn primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
              </svg>
              加自选
            </button>
            <button class="action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="5" r="3"/>
                <circle cx="6" cy="12" r="3"/>
                <circle cx="18" cy="19" r="3"/>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
              </svg>
              分享
            </button>
            <button class="action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              价格预警
            </button>
          </div>
        </div>

        <!-- 技术指标 -->
        <div class="indicators-card">
          <div class="card-header">
            <span class="card-title">技术指标</span>
            <button class="refresh-btn" @click="loadIndicators">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23,4 23,10 17,10"/>
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10"/>
              </svg>
            </button>
          </div>
          <div class="indicators-grid" v-if="indicators">
            <div class="indicator-group">
              <div class="group-title">趋势指标</div>
              <div class="indicator-row">
                <span class="ind-label">MA5</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.sma_5) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">MA10</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.sma_10) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">MA20</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.sma_20) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">MA60</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.sma_60) }}</span>
              </div>
            </div>
            <div class="indicator-group">
              <div class="group-title">超买超卖</div>
              <div class="indicator-row">
                <span class="ind-label">RSI(14)</span>
                <span class="ind-value font-mono" :class="getRsiClass(indicators.rsi_14)">
                  {{ formatNumber(indicators.rsi_14, 2) }}
                </span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">KDJ-K</span>
                <span class="ind-value font-mono">{{ formatNumber(indicators.kdj_k, 2) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">KDJ-D</span>
                <span class="ind-value font-mono">{{ formatNumber(indicators.kdj_d, 2) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">KDJ-J</span>
                <span class="ind-value font-mono" :class="getKdjClass(indicators.kdj_j)">
                  {{ formatNumber(indicators.kdj_j, 2) }}
                </span>
              </div>
            </div>
            <div class="indicator-group">
              <div class="group-title">MACD</div>
              <div class="indicator-row">
                <span class="ind-label">DIF</span>
                <span class="ind-value font-mono" :class="getPriceClass(indicators.macd)">
                  {{ formatNumber(indicators.macd, 4) }}
                </span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">DEA</span>
                <span class="ind-value font-mono" :class="getPriceClass(indicators.macd_signal)">
                  {{ formatNumber(indicators.macd_signal, 4) }}
                </span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">MACD</span>
                <span class="ind-value font-mono" :class="getPriceClass(indicators.macd_hist)">
                  {{ formatNumber(indicators.macd_hist, 4) }}
                </span>
              </div>
            </div>
            <div class="indicator-group">
              <div class="group-title">波动率</div>
              <div class="indicator-row">
                <span class="ind-label">布林上轨</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.bb_upper_20) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">布林中轨</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.bb_middle_20) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">布林下轨</span>
                <span class="ind-value font-mono">{{ formatPrice(indicators.bb_lower_20) }}</span>
              </div>
              <div class="indicator-row">
                <span class="ind-label">ATR(14)</span>
                <span class="ind-value font-mono">{{ formatNumber(indicators.atr_14, 2) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="indicators-loading">
            <span class="loading-text">加载技术指标...</span>
          </div>
        </div>
      </div>
    </main>

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

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <span>加载数据中...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { stockApi } from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'

const route = useRoute()
const router = useRouter()

// ============ WebSocket 实时行情 ============
const { connectionStatus, quotes, subscribe, unsubscribe } = useWebSocket()

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

// ============ 状态变量 ============
const stockCode = computed(() => route.params.code || '600000')
const searchKeyword = ref('')
const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null
let updateTimer = null

// 股票信息
const stockInfo = ref({
  name: '',
  price: 0,
  open: 0,
  high: 0,
  low: 0,
  close: 0,
  volume: 0,
  amount: 0,
  turnover: 0,
  last_close: 0,
  pre_close: 0
})
const chartData = ref([])
const indicators = ref(null)
const transactionList = ref([])
const quoteData = ref([
  { price: 0, sellVolume: 0, sellCount: 0, buyVolume: 0, buyCount: 0 },
  { price: 0, sellVolume: 0, sellCount: 0, buyVolume: 0, buyCount: 0 },
  { price: 0, sellVolume: 0, sellCount: 0, buyVolume: 0, buyCount: 0 },
  { price: 0, sellVolume: 0, sellCount: 0, buyVolume: 0, buyCount: 0 },
  { price: 0, sellVolume: 0, sellCount: 0, buyVolume: 0, buyCount: 0 }
])

// K线图配置
const periods = [
  { label: '1分', value: '1min' },
  { label: '5分', value: '5min' },
  { label: '15分', value: '15min' },
  { label: '30分', value: '30min' },
  { label: '60分', value: '60min' },
  { label: '日', value: 'daily' },
  { label: '周', value: 'weekly' },
  { label: '月', value: 'monthly' }
]
const currentPeriod = ref('daily')
const adjustType = ref('qfq')

// 时间显示
const currentTime = ref('')
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

/** 实时行情到达时，同步更新股票信息 */
watch(() => quotes.value[stockCode.value], (quote) => {
  if (quote && quote.price !== undefined) {
    stockInfo.value = {
      ...stockInfo.value,
      name: quote.name || stockInfo.value.name,
      price: quote.price,
      open: quote.open || stockInfo.value.open,
      high: quote.high || stockInfo.value.high,
      low: quote.low || stockInfo.value.low,
      volume: quote.volume || stockInfo.value.volume,
      amount: quote.amount || stockInfo.value.amount
    }
  }
})

// ============ 计算属性 ============
const priceChange = computed(() => {
  const info = stockInfo.value
  if (info.price && info.last_close) {
    return info.price - info.last_close
  }
  if (info.close && info.pre_close) {
    return info.close - info.pre_close
  }
  return 0
})

const priceChangePct = computed(() => {
  const info = stockInfo.value
  if (info.pct_chg !== undefined && info.pct_chg !== null) {
    return Number(info.pct_chg)
  }
  const base = info.last_close || info.pre_close || 1
  return (priceChange.value / base) * 100
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

const sellTotal = computed(() => {
  return quoteData.value.reduce((sum, q) => sum + (q.sellVolume || 0), 0)
})

const buyTotal = computed(() => {
  return quoteData.value.reduce((sum, q) => sum + (q.buyVolume || 0), 0)
})

const netDiff = computed(() => buyTotal.value - sellTotal.value)

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

const formatAmount = (val) => {
  if (!val && val !== 0) return '--'
  val = Number(val)
  if (val >= 100000000) return (val / 100000000).toFixed(2) + '亿'
  if (val >= 10000) return (val / 10000).toFixed(2) + '万'
  return val.toFixed(0)
}

const formatNumber = (val, decimals = 2) => {
  if (!val && val !== 0) return '--'
  return Number(val).toFixed(decimals)
}

// ============ 样式辅助函数 ============
const getPriceClass = (val) => {
  if (!val) return ''
  return val > 0 ? 'price-up' : val < 0 ? 'price-down' : ''
}

const getRsiClass = (rsi) => {
  if (!rsi) return ''
  if (rsi > 70) return 'price-up'
  if (rsi < 30) return 'price-down'
  return ''
}

const getKdjClass = (kdj) => {
  if (!kdj) return ''
  if (kdj > 80) return 'price-up'
  if (kdj < 20) return 'price-down'
  return ''
}

const getTransactionClass = (t) => {
  if (!t.change) return ''
  return t.change > 0 ? 'row-up' : t.change < 0 ? 'row-down' : ''
}

// ============ 数据加载 ============
const loadStockInfo = async () => {
  try {
    const res = await stockApi.getRealtime(stockCode.value)
    if (res.data && res.data.length > 0) {
      stockInfo.value = res.data[0]
    }
  } catch (e) {
    console.error('加载股票信息失败:', e)
  }
}

const loadChartData = async () => {
  try {
    const res = await stockApi.getChartData(stockCode.value, currentPeriod.value, 120, adjustType.value)
    chartData.value = res.chart_data || []
    updateChart()
  } catch (e) {
    console.error('加载图表数据失败:', e)
  }
}

const loadIndicators = async () => {
  try {
    const res = await stockApi.getIndicators(stockCode.value, 60)
    indicators.value = res.indicators || {}
  } catch (e) {
    console.error('加载技术指标失败:', e)
  }
}

const loadTransaction = async () => {
  const mockTransactions = []
  const basePrice = stockInfo.value.price || 10.0
  for (let i = 0; i < 20; i++) {
    const change = (Math.random() - 0.5) * 0.1
    const price = basePrice + change
    mockTransactions.push({
      time: `14:${String(30 - i).padStart(2, '0')}`,
      price: price,
      change: change,
      volume: Math.floor(Math.random() * 10000) + 1000,
      type: Math.random() > 0.5 ? 'buy' : Math.random() > 0.5 ? 'sell' : 'neutral'
    })
  }
  transactionList.value = mockTransactions
}

const loadQuoteData = async () => {
  const basePrice = stockInfo.value.price || 10.0
  const mockQuote = []
  for (let i = 5; i >= 1; i--) {
    mockQuote.push({
      price: basePrice - i * 0.01,
      sellVolume: Math.floor(Math.random() * 50000) + 10000,
      sellCount: Math.floor(Math.random() * 20) + 5,
      buyVolume: Math.floor(Math.random() * 50000) + 10000,
      buyCount: Math.floor(Math.random() * 20) + 5
    })
  }
  quoteData.value = mockQuote
}

// ============ 图表渲染 ============
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
    animationDuration: 300,
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
        axisLabel: { show: false },
        splitLine: { show: false }
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
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 70,
        end: 100
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: '2%',
        height: '15px',
        borderColor: '#1e293b',
        fillerColor: 'rgba(59, 130, 246, 0.1)',
        handleStyle: { color: '#3b82f6' },
        textStyle: { color: '#5c6a7e' }
      }
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
        name: 'MA5',
        type: 'line',
        data: chartData.value.map(d => d.ma5),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        lineStyle: { color: '#f59e0b', width: 1 },
        symbol: 'none'
      },
      {
        name: 'MA10',
        type: 'line',
        data: chartData.value.map(d => d.ma10),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        lineStyle: { color: '#3b82f6', width: 1 },
        symbol: 'none'
      },
      {
        name: 'MA20',
        type: 'line',
        data: chartData.value.map(d => d.ma20),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        lineStyle: { color: '#22d3ee', width: 1 },
        symbol: 'none'
      },
      {
        name: 'MA30',
        type: 'line',
        data: chartData.value.map(d => d.ma30),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        lineStyle: { color: '#a78bfa', width: 1 },
        symbol: 'none'
      },
      {
        name: '成交量',
        type: 'bar',
        data: volumes,
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: { color: (params) => volumesColor[params.dataIndex] }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

// ============ 事件处理 ============
const changePeriod = (period) => {
  currentPeriod.value = period
  loadChartData()
}

const changeAdjust = (type) => {
  adjustType.value = type
  loadChartData()
}

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push(`/stock/${searchKeyword.value.trim()}`)
  }
}

const refreshAll = async () => {
  loading.value = true
  await Promise.all([
    loadStockInfo(),
    loadChartData(),
    loadIndicators(),
    loadTransaction(),
    loadQuoteData()
  ])
  loading.value = false
}

const initChart = () => {
  if (chartRef.value && !chartInstance) {
    chartInstance = echarts.init(chartRef.value)
    window.addEventListener('resize', () => {
      chartInstance && chartInstance.resize()
    })
  }
}

// ============ 生命周期 ============
onMounted(async () => {
  loading.value = true
  updateTime()
  setInterval(updateTime, 1000)
  
  initChart()
  
  await Promise.all([
    loadStockInfo(),
    loadChartData(),
    loadIndicators(),
    loadTransaction(),
    loadQuoteData()
  ])
  
  loading.value = false
  
  // 订阅当前股票的 WebSocket 实时行情
  subscribe([stockCode.value])
  
  // 保留定时轮询作为兜底（WebSocket 断线时使用）
  updateTimer = setInterval(refreshAll, 30000)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (updateTimer) {
    clearInterval(updateTimer)
  }
  // 取消 WebSocket 订阅
  unsubscribe([stockCode.value])
})

watch(stockCode, (newCode, oldCode) => {
  // 取消旧股票订阅
  if (oldCode) unsubscribe([oldCode])
  // 订阅新股票
  if (newCode) subscribe([newCode])
  // 刷新数据
  refreshAll()
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

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.right-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  flex-shrink: 0;
}

/* ============ 股票信息头部 ============ */
.stock-header-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
}

.stock-main-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.stock-name-code {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-name {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.stock-code {
  font-size: 14px;
  color: var(--text-muted);
}

.stock-price-info {
  text-align: right;
}

.current-price {
  font-size: 36px;
  font-weight: 600;
  line-height: 1;
}

.price-change {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  font-size: 14px;
}

.stock-indicators {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-muted);
}

.indicator-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.indicator-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.indicator-value {
  font-size: 13px;
  color: var(--text-primary);
}

/* ============ K线图表 ============ */
.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 12px;
  flex: 1;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
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
  border-color: var(--accent-blue);
}

.chart-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  margin-bottom: 8px;
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

.kline-chart {
  flex: 1;
  min-height: 300px;
}

/* ============ 分笔成交 ============ */
.transaction-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  max-height: 280px;
  display: flex;
  flex-direction: column;
}

.transaction-table-wrapper {
  flex: 1;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th {
  position: sticky;
  top: 0;
  padding: 8px 12px;
  text-align: left;
  background: var(--bg-tertiary);
  color: var(--text-muted);
  font-weight: 500;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  padding: 6px 12px;
  border-bottom: 1px solid var(--border-muted);
}

.data-table tr:hover td {
  background: var(--bg-hover);
}

.row-up td {
  background: rgba(239, 68, 68, 0.05);
}

.row-down td {
  background: rgba(34, 197, 94, 0.05);
}

.transaction-type {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 500;
}

.transaction-type.buy {
  background: var(--color-up-light);
  color: var(--color-up);
}

.transaction-type.sell {
  background: var(--color-down-light);
  color: var(--color-down);
}

.transaction-type.neutral {
  background: var(--bg-tertiary);
  color: var(--text-muted);
}

/* ============ 右侧面板 ============ */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-muted);
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-subtitle {
  font-size: 11px;
  color: var(--text-muted);
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.refresh-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* ============ 五档盘口 ============ */
.quote-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.quote-content {
  padding: 12px;
}

.quote-table {
  margin-bottom: 12px;
}

.quote-header {
  display: grid;
  grid-template-columns: 1fr 80px 1fr;
  padding: 6px 8px;
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quote-header span:first-child,
.quote-header span:last-child {
  text-align: center;
}

.quote-row {
  display: grid;
  grid-template-columns: 1fr 80px 1fr;
  padding: 6px 8px;
  align-items: center;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.quote-row:hover {
  background: var(--bg-hover);
}

.quote-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.quote-cell.sell {
  align-items: flex-start;
}

.quote-cell.buy {
  align-items: flex-end;
}

.quote-cell.price {
  font-weight: 600;
  font-size: 13px;
}

.quote-volume {
  font-size: 12px;
}

.quote-summary {
  padding-top: 12px;
  border-top: 1px solid var(--border-muted);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
}

.summary-label {
  font-size: 12px;
  color: var(--text-muted);
}

.summary-value {
  font-size: 12px;
  font-weight: 500;
}

/* ============ 快捷操作 ============ */
.action-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-accent);
}

.action-btn.primary {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.action-btn.primary:hover {
  background: #2563eb;
  border-color: #2563eb;
}

/* ============ 技术指标 ============ */
.indicators-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.indicators-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 12px;
  overflow-y: auto;
}

.indicator-group {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 10px;
}

.group-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.indicator-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.ind-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.ind-value {
  font-size: 12px;
  color: var(--text-primary);
}

.indicators-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-text {
  color: var(--text-muted);
  font-size: 13px;
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

/* ============ 加载状态 ============ */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 14, 23, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-default);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
