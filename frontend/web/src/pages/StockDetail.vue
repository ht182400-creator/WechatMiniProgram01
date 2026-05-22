<template>
  <div class="terminal-container">
    <!-- 顶部导航栏（共享组件） -->
    <AppHeader>
      <template #search>
        <div class="search-box">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input type="text" v-model="searchKeyword" placeholder="输入股票代码或名称..."
            @keyup.enter="handleSearch" class="search-input" />
        </div>
      </template>
      <template #actions>
        <button class="btn-icon" title="刷新数据" @click="refreshAll">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23,4 23,10 17,10"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10"/></svg>
        </button>
      </template>
    </AppHeader>

    <!-- 页面级导航栏：返回主页 -->
    <div class="page-header">
      <div class="header-left">
        <router-link to="/" class="back-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回主页
        </router-link>
        <span class="page-title">行情详情</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <main class="terminal-main">
      <!-- 左侧行情区 -->
      <div class="left-panel">
        <!-- 股票信息头部 -->
        <div class="stock-info-card animate-in">
          <div class="si-left">
            <div class="stock-name-row">
              <h1 class="stock-name">{{ stockInfo.name || '加载中...' }}</h1>
              <span class="stock-code font-mono">{{ stockCode }}</span>
            </div>
            <div class="stock-current-price font-mono" :class="priceChange >= 0 ? 'price-up' : 'price-down'">
              {{ formatPrice(stockInfo.price || stockInfo.close) }}
            </div>
            <div class="stock-change-row font-mono" :class="priceChange >= 0 ? 'price-up' : 'price-down'">
              <span>{{ priceChange >= 0 ? '+' : '' }}{{ formatPrice(priceChange) }}</span>
              <span>({{ priceChangePct >= 0 ? '+' : '' }}{{ formatPercent(priceChangePct) }}%)</span>
            </div>
          </div>
          <div class="stock-meta-grid">
            <div class="stock-meta-item">
              <span class="stock-meta-label">开盘</span>
              <span class="stock-meta-value font-mono">{{ formatPrice(stockInfo.open || stockInfo.pre_close) }}</span>
            </div>
            <div class="stock-meta-item">
              <span class="stock-meta-label">最高</span>
              <span class="stock-meta-value font-mono price-up">{{ formatPrice(stockInfo.high) }}</span>
            </div>
            <div class="stock-meta-item">
              <span class="stock-meta-label">最低</span>
              <span class="stock-meta-value font-mono price-down">{{ formatPrice(stockInfo.low) }}</span>
            </div>
            <div class="stock-meta-item">
              <span class="stock-meta-label">成交量</span>
              <span class="stock-meta-value font-mono">{{ formatVolume(stockInfo.volume) }}</span>
            </div>
            <div class="stock-meta-item">
              <span class="stock-meta-label">成交额</span>
              <span class="stock-meta-value font-mono">{{ formatAmount(stockInfo.amount) }}</span>
            </div>
            <div class="stock-meta-item">
              <span class="stock-meta-label">换手率</span>
              <span class="stock-meta-value font-mono">{{ formatPercent(stockInfo.turnover) }}</span>
            </div>
          </div>
        </div>

        <!-- K线图表 - HQChart -->
        <div class="chart-card card animate-in" style="animation-delay: 0.05s">
          <div class="chart-toolbar">
            <div class="period-tabs">
              <button v-for="p in periods" :key="p.value"
                :class="['period-tab', { active: currentPeriod === p.value }]"
                @click="changePeriod(p.value)">{{ p.label }}</button>
            </div>
            <div class="adjust-tabs">
              <button :class="['adjust-tab', { active: adjustType === 'qfq' }]" @click="changeAdjust('qfq')">前复权</button>
              <button :class="['adjust-tab', { active: adjustType === 'hfq' }]" @click="changeAdjust('hfq')">后复权</button>
              <button :class="['adjust-tab', { active: adjustType === 'none' }]" @click="changeAdjust('none')">不复权</button>
            </div>
          </div>
          <!-- v-if 确保数据加载后才能渲染图表，避免 HQChart 在空数据下 Init 导致 ChartBorder 崩溃 -->
          <HQChartKline v-if="chartData.length > 0" ref="hqChartRef"
            :data="chartData"
            :period="hqPeriod"
            :adjust="adjustType"
            :code="stockCode"
            :name="stockInfo.name"
            :height="'460px'"
            @ready="onChartReady"
            @enterKeyDown="onEnterKeyDown"
          />
          <div v-else class="chart-placeholder">
            <div class="loading-spinner"></div>
            <span class="loading-text">K线数据加载中...</span>
          </div>
        </div>

        <!-- 分笔成交 - 虚拟滚动 -->
        <div class="chart-card card animate-in" style="animation-delay:0.1s;flex:1;min-height:0;display:flex;flex-direction:column;">
          <div class="card-header">
            <span class="card-title">分笔成交</span>
            <span class="text-muted font-mono text-xs">共 {{ transactionList.length }} 笔</span>
          </div>
          <div class="virtual-scroll" style="flex:1;min-height:0;">
            <table class="data-table">
              <thead><tr>
                <th>时间</th><th>价格</th><th>涨跌</th><th>成交量</th><th>性质</th>
              </tr></thead>
              <tbody>
                <tr v-for="(t, idx) in transactionList" :key="idx" :class="getTransactionClass(t)">
                  <td class="font-mono">{{ t.time }}</td>
                  <td class="font-mono" :class="getPriceClass(t.change)">{{ formatPrice(t.price) }}</td>
                  <td class="font-mono" :class="getPriceClass(t.change)">{{ t.change >= 0 ? '+' : '' }}{{ formatPrice(t.change) }}</td>
                  <td class="font-mono">{{ formatVolume(t.volume) }}</td>
                  <td><span class="tag" :class="t.type === 'buy' ? 'tag-up' : t.type === 'sell' ? 'tag-down' : ''">{{ t.type === 'buy' ? '买盘' : t.type === 'sell' ? '卖盘' : '中性' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 右侧信息区 -->
      <div class="right-panel">
        <!-- 五档盘口 - 带量柱可视化 -->
        <div class="card animate-in" style="animation-delay:0.02s">
          <div class="card-header">
            <span class="card-title">五档盘口</span>
          </div>
          <div class="card-body" style="padding:8px 12px;">
            <div class="quote-grid">
              <template v-for="i in 5" :key="'q-'+i">
                <div class="quote-row sell">
                  <span class="quote-label sell">卖{{6-i}}</span>
                  <div class="quote-bar-wrap">
                    <div class="quote-bar sell" :style="{ width: quoteBarWidth(quoteData[5-i]?.sellVolume, 'sell') + '%' }"></div>
                    <div class="quote-bar-label font-mono">{{ formatVolume(quoteData[5-i]?.sellVolume) }}</div>
                  </div>
                  <div class="quote-price sell font-mono">{{ formatPrice(quoteData[5-i]?.price) }}</div>
                  <div class="quote-bar-wrap empty"></div>
                </div>
              </template>
              <div style="height:1px;background:var(--border-default);margin:2px 0;"></div>
              <template v-for="i in 5" :key="'qb-'+i">
                <div class="quote-row buy">
                  <div class="quote-bar-wrap empty"></div>
                  <div class="quote-price buy font-mono">{{ formatPrice(quoteData[i-1]?.price) }}</div>
                  <div class="quote-bar-wrap">
                    <div class="quote-bar buy" :style="{ width: quoteBarWidth(quoteData[i-1]?.buyVolume, 'buy') + '%' }"></div>
                    <div class="quote-bar-label font-mono">{{ formatVolume(quoteData[i-1]?.buyVolume) }}</div>
                  </div>
                  <span class="quote-label buy">买{{i}}</span>
                </div>
              </template>
            </div>
            <div class="divider" style="margin:8px 0;"></div>
            <div class="flex justify-between text-xs">
              <span><span class="text-muted">卖盘 </span><span class="price-down font-mono">{{ formatVolume(sellTotal) }}</span></span>
              <span><span class="text-muted">买盘 </span><span class="price-up font-mono">{{ formatVolume(buyTotal) }}</span></span>
              <span><span class="text-muted">净差 </span><span class="font-mono" :class="netDiff >= 0 ? 'price-up' : 'price-down'">{{ netDiff >= 0 ? '+' : '' }}{{ formatVolume(netDiff) }}</span></span>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="card animate-in" style="animation-delay:0.04s">
          <div class="card-header"><span class="card-title">快捷操作</span></div>
          <div class="card-body" style="padding:12px 14px;display:flex;flex-direction:column;gap:6px;">
            <button class="btn btn-primary btn-sm" style="width:100%">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/></svg>
              加自选
            </button>
            <button class="btn btn-sm" style="width:100%">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              分享
            </button>
            <button class="btn btn-sm" style="width:100%">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
              价格预警
            </button>
          </div>
        </div>

        <!-- 技术指标 -->
        <div class="card animate-in" style="animation-delay:0.06s;flex:1;min-height:0;overflow-y:auto;">
          <div class="card-header">
            <span class="card-title">技术指标</span>
            <button class="btn-icon" @click="loadIndicators" title="刷新">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23,4 23,10 17,10"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10"/></svg>
            </button>
          </div>
          <div v-if="indicators" class="card-body stagger-in" style="padding:8px 14px;">
            <div style="margin-bottom:10px;">
              <div class="text-xs text-muted" style="margin-bottom:4px;">趋势指标</div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>MA5</span><span class="font-mono">{{ formatPrice(indicators.sma_5) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>MA10</span><span class="font-mono">{{ formatPrice(indicators.sma_10) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>MA20</span><span class="font-mono">{{ formatPrice(indicators.sma_20) }}</span></div>
              <div class="flex justify-between text-xs"><span>MA60</span><span class="font-mono">{{ formatPrice(indicators.sma_60) }}</span></div>
            </div>
            <div style="margin-bottom:10px;">
              <div class="text-xs text-muted" style="margin-bottom:4px;">超买超卖</div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>RSI(14)</span><span class="font-mono" :class="getRsiClass(indicators.rsi_14)">{{ formatNumber(indicators.rsi_14) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>KDJ-K</span><span class="font-mono">{{ formatNumber(indicators.kdj_k) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>KDJ-D</span><span class="font-mono">{{ formatNumber(indicators.kdj_d) }}</span></div>
              <div class="flex justify-between text-xs"><span>KDJ-J</span><span class="font-mono" :class="getKdjClass(indicators.kdj_j)">{{ formatNumber(indicators.kdj_j) }}</span></div>
            </div>
            <div style="margin-bottom:10px;">
              <div class="text-xs text-muted" style="margin-bottom:4px;">MACD</div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>DIF</span><span class="font-mono" :class="getPriceClass(indicators.macd)">{{ formatNumber(indicators.macd, 4) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>DEA</span><span class="font-mono" :class="getPriceClass(indicators.macd_signal)">{{ formatNumber(indicators.macd_signal, 4) }}</span></div>
              <div class="flex justify-between text-xs"><span>MACD</span><span class="font-mono" :class="getPriceClass(indicators.macd_hist)">{{ formatNumber(indicators.macd_hist, 4) }}</span></div>
            </div>
            <div>
              <div class="text-xs text-muted" style="margin-bottom:4px;">波动率</div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>布林上轨</span><span class="font-mono">{{ formatPrice(indicators.bb_upper_20) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>布林中轨</span><span class="font-mono">{{ formatPrice(indicators.bb_middle_20) }}</span></div>
              <div class="flex justify-between text-xs" style="margin-bottom:2px;"><span>布林下轨</span><span class="font-mono">{{ formatPrice(indicators.bb_lower_20) }}</span></div>
              <div class="flex justify-between text-xs"><span>ATR(14)</span><span class="font-mono">{{ formatNumber(indicators.atr_14, 2) }}</span></div>
            </div>
          </div>
          <div v-else class="empty-state"><span class="text-muted text-xs">加载技术指标...</span></div>
        </div>
      </div>
    </main>

    <!-- 底部状态栏（共享组件） -->
    <AppFooter :wsStatus="wsStatusClass" :wsText="wsStatusText" />

    <!-- 分时明细弹窗（共享组件，回车键打开） -->
    <IntradayDialog v-model="showIntradayDialog" :code="stockCode" :name="stockInfo.name" :date="intradayTargetDate" />

    <!-- 加载遮罩 -->
    <div v-if="loading" class="loading-overlay">
      <div style="text-align:center;">
        <div class="spinner"></div>
        <div class="loading-text">加载数据中...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { stockApi } from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import HQChartKline from '@/components/HQChartKline.vue'
import IntradayDialog from '@/components/IntradayDialog.vue'

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
    case 'connected': return 'connected'
    case 'connecting': return 'connecting'
    default: return 'disconnected'
  }
})

// ============ 状态变量 ============
const stockCode = computed(() => route.params.code || '600000')
const searchKeyword = ref('')
const loading = ref(false)
const hqChartRef = ref(null)
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

// ============ 分时明细弹窗（共享组件，回车键打开）============
const showIntradayDialog = ref(false)
const intradayTargetDate = ref('')
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

/** 前端周期值 -> HQChart 周期值 */
const hqPeriod = computed(() => {
  const map = { '1min': '1min', '5min': '5min', '15min': '15min', '30min': '30min', '60min': '60min', 'daily': 'day', 'weekly': 'week', 'monthly': 'month' }
  return map[currentPeriod.value] || 'day'
})

/** 实时行情到达时，同步更新股票信息 */
watch(() => quotes.value[stockCode.value], (quote) => {
  if (quote && quote.price !== undefined) {
    // ★ 保护中文名不被 WebSocket 的空值/数字覆盖
    const currentName = stockInfo.value.name || ''
    const isNameChinese = /[\u4e00-\u9fa5]/.test(currentName)
    const quoteName = quote.name

    stockInfo.value = {
      ...stockInfo.value,
      // 仅在当前名称非中文时才接受 WebSocket 推送的名称
      name: (isNameChinese ? currentName : (quoteName || currentName)),
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
/**
 * 加载股票基本信息（含中文名）
 *
 * 名称获取优先级：
 * 1. /stock/realtime 返回的 name
 * 2. /stock/search 搜索结果匹配
 * 3. /stock/list 股票列表匹配
 */
const loadStockInfo = async () => {
  try {
    const code = stockCode.value
    const res = await stockApi.getRealtime(code)
    if (res.data && res.data.length > 0) {
      const info = res.data[0]

      // 如果 realtime 未返回有效中文名，尝试从搜索接口获取
      if (!info.name || /^\d+$/.test(info.name) || !/[\u4e00-\u9fa5]/.test(info.name)) {
        let foundName = null

        // 方案1: 搜索接口
        try {
          const searchRes = await stockApi.search(code)
          if (searchRes.stocks && searchRes.stocks.length > 0) {
            // 宽松匹配：code 包含或被包含
            const found = searchRes.stocks.find(s =>
              s.code === code ||
              s.code === String(code) ||
              s.code.endsWith(code) ||
              code.endsWith(s.code)
            )
            if (found?.name && /[\u4e00-\u9fa5]/.test(found.name)) {
              foundName = found.name
            }
          }
        } catch (_) {}

        // 方案2: 股票列表接口（如果搜索没找到）
        if (!foundName) {
          try {
            const listRes = await stockApi.getList()
            if (listRes.stocks && listRes.stocks.length > 0) {
              const found = listRes.stocks.find(s =>
                s.code === code ||
                s.code === String(code) ||
                s.code.endsWith(code)
              )
              if (found?.name && /[\u4e00-\u9fa5]/.test(found.name)) {
                foundName = found.name
              }
            }
          } catch (_) {}
        }

        if (foundName) {
          info.name = foundName
        } else {
          console.warn(`[股票名称] 无法获取 ${code} 的中文名`)
        }
      }

      stockInfo.value = { ...info }
    } else {
      // realtime 无数据时，尝试搜索接口兜底
      let foundStock = null

      try {
        const searchRes = await stockApi.search(code)
        if (searchRes.stocks && searchRes.stocks.length > 0) {
          foundStock = searchRes.stocks.find(s =>
            s.code === code || s.code === String(code) || s.code.endsWith(code)
          )
        }
      } catch (_) {}

      if (foundStock) {
        stockInfo.value = { ...foundStock }
      } else {
        console.warn(`[股票信息] realtime 和搜索均无数据: ${code}`)
      }
    }
  } catch (e) {
    console.error('加载股票信息失败:', e)
  }
}

/**
 * 根据当前周期加载K线数据
 *
 * - 分钟线 (1min/5min/15min/30min/60min) → 调用 /stock/minute 端点
 *   返回格式: { data: [{ time, open, close, high, low, volume }] }
 * - 日线/周线/月线 → 调用 /stock/chart 端点
 *   返回格式: { chart_data: [{ date, open, close, high, low, volume }] }
 */
const loadChartData = async () => {
  // 先清空旧数据（避免切换周期时显示错误数据）
  chartData.value = []

  try {
    const code = stockCode.value
    const period = currentPeriod.value

    // 判断是否为分钟线周期
    const minutePeriods = ['1min', '5min', '15min', '30min', '60min']
    const isMinute = minutePeriods.includes(period)

    if (isMinute) {
      // ★ 分钟线：调用独立分钟数据接口
      const res = await stockApi.getMinuteData(code, period)
      const rawList = res.data || []
      if (rawList.length === 0) {
        console.warn(`[K线] 分钟数据为空: ${code} ${period}，可能当前非交易时间或数据源不支持`)
        // 不设置 chartData，保持空数组 → 显示 "K线数据加载中..." 占位
        return
      }
      // 统一为前端期望的 date 字段格式（分钟数据用 time 字段）
      chartData.value = rawList.map(d => ({
        date: d.time || d.date || '',
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
        amount: d.amount || 0
      }))
    } else {
      // ★ 日/周/月：调用图表数据接口
      const res = await stockApi.getChartData(code, period, 120, adjustType.value)
      const dataList = res.chart_data || []
      if (dataList.length === 0) {
        console.warn(`[K线] 图表数据为空: ${code} ${period}`)
        return
      }
      chartData.value = dataList
    }
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

/**
 * 加载分笔成交数据（真实 API）
 */
const loadTransaction = async () => {
  try {
    const code = stockCode.value
    const res = await stockApi.getTransaction(code, 100)
    const txList = res.data || []

    if (txList.length > 0) {
      // 真实数据：转换字段名适配前端模板
      transactionList.value = txList.map(t => ({
        time: t.time || '',
        price: t.price || 0,
        change: (t.price || 0) - (stockInfo.value.open || stockInfo.value.pre_close || t.price || 0),
        volume: t.volume || 0,
        type: (t.direction === 'B') ? 'buy' : (t.direction === 'S') ? 'sell' : 'neutral'
      }))
    } else {
      // 无真实数据时显示空提示（不再使用随机模拟）
      transactionList.value = []
    }
  } catch (e) {
    console.warn('加载分笔成交失败:', e)
    transactionList.value = []
  }
}

/** HQChartKline 回车键回调 → 获取当前 K 线日期 → 打开分时弹窗 */
const onEnterKeyDown = () => {
  if (!stockCode.value) return
  let targetDate = ''
  try {
    if (hqChartRef.value?.chartInstance) {
      const option = hqChartRef.value.chartInstance.getOption()
      const xAxisData = option.xAxis?.[0]?.data || []
      const dz = option.dataZoom?.[0]
      if (dz && xAxisData.length > 0) {
        const endIdx = Math.floor((dz.end / 100) * xAxisData.length) - 1
        targetDate = xAxisData[Math.min(endIdx, xAxisData.length - 1)] || xAxisData[xAxisData.length - 1] || ''
      } else if (xAxisData.length > 0) {
        targetDate = xAxisData[xAxisData.length - 1]
      }
    }
    if (!targetDate && chartData.value.length > 0) {
      targetDate = chartData.value[chartData.value.length - 1].date || ''
    }
  } catch (_) {
    if (chartData.value.length > 0) {
      targetDate = chartData.value[chartData.value.length - 1].date || ''
    }
  }
  intradayTargetDate.value = targetDate
  showIntradayDialog.value = true
}

/**
 * 加载五档盘口数据（使用真实 API）
 *
 * 后端 /stock/depth 返回 bids/asks 数组：
 * bids = [[价格, 成交量], ...]  买一到买十
 * asks = [[价格, 成交量], ...]  卖一卖到卖十
 */
const loadQuoteData = async () => {
  try {
    const res = await stockApi.getDepth(stockCode.value)

    // 后端返回格式: { code, bids: [[price, vol], ...], asks: [[price, vol], ...] }
    const bids = res.bids || []
    const asks = res.asks || []

    if (bids.length === 0 && asks.length === 0) {
      // 真实数据不可用时 fallback 到基于当前价的模拟盘口
      const basePrice = stockInfo.value.price || stockInfo.value.close || 10.0
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
      return
    }

    // 将 bids/asks 合并为前端期望的 5 档格式
    // bids[0]=买一, bids[4]=买五; asks[0]=卖一, asks[4]=卖五
    const merged = []
    for (let i = 0; i < 5; i++) {
      const askPrice = (i < asks.length) ? asks[i][0] : null
      const askVol = (i < asks.length) ? asks[i][1] : 0
      const bidPrice = (i < bids.length) ? bids[i][0] : null
      const bidVol = (i < bids.length) ? bids[i][1] : 0

      merged.push({
        price: bidPrice || askPrice || 0,
        sellVolume: askVol,
        sellCount: 0,
        buyVolume: bidVol,
        buyCount: 0
      })
    }
    quoteData.value = merged
  } catch (e) {
    console.warn('加载盘口数据失败，使用模拟数据:', e)
    // fallback: 保持原有 mock 逻辑
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
}

// ============ HQChart 回调 ============
const onChartReady = (instance) => {
  // HQChart 实例就绪，可在此执行后续操作
}

/** 五档盘口量柱宽度百分比 */
const quoteBarWidth = (vol, side) => {
  if (!vol) return 0
  const maxVol = Math.max(
    ...quoteData.value.map(q => Math.max(q.sellVolume || 0, q.buyVolume || 0)),
    1
  )
  return Math.min((vol / maxVol) * 100, 100)
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

// ============ 生命周期 ============
onMounted(async () => {
  loading.value = true

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
/* ============ 页面顶部导航：简洁文字行 ============ */
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.header-left { display: flex; align-items: center; gap: 12px; }

.back-link {
  position: relative;
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px;
  background: linear-gradient(180deg, #1e2535 0%, #151c2e 100%);
  border: 1px solid #2a3348;
  border-radius: 8px;
  color: #8b949e; text-decoration: none;
  font-size: 13px;
  box-shadow:
    0 2px 0 #0d1117,
    0 4px 8px rgba(0,0,0,0.3),
    inset 0 1px 0 rgba(255,255,255,0.04);
  transition: all 0.25s ease;
  overflow: hidden;
}
/* 闪烁光泽 */
.back-link::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(88,166,255,0.06),
    rgba(88,166,255,0.12),
    rgba(88,166,255,0.06),
    transparent
  );
  animation: btnShimmer 3s ease-in-out infinite;
}
@keyframes btnShimmer {
  0%, 100% { left: -100%; }
  50% { left: 120%; }
}
.back-link:hover {
  background: linear-gradient(180deg, #253050 0%, #1a2540 100%);
  color: #58a6ff;
  border-color: #58a6ff;
  box-shadow:
    0 2px 0 #0d1829,
    0 6px 16px rgba(88,166,255,0.15),
    0 0 20px rgba(88,166,255,0.08),
    inset 0 1px 0 rgba(255,255,255,0.06);
  transform: translateY(-1px);
}
.back-link:active {
  transform: translateY(1px);
  box-shadow:
    0 1px 0 #0d1117,
    0 2px 4px rgba(0,0,0,0.3);
}
.page-title { font-size: 16px; font-weight: 600; color: var(--text-primary, #c9cdd4); }

.header-nav { display: flex; gap: 4px; }
.nav-item {
  display: flex; align-items: center; padding: 8px 14px;
  color: var(--text-secondary, #8b949e); text-decoration: none;
  border-radius: 8px; font-size: 13px; transition: all 0.2s;
}
.nav-item:hover { background: rgba(88,166,255,0.08); color: #c9cdd4; }
.nav-item.active { background: #58a6ff; color: white; }

/* ============ 搜索框 ============ */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 220px;
  height: 32px;
  padding: 0 10px 0 32px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 12.5px;
  font-family: var(--font-mono);
  outline: none;
  transition: border-color var(--duration-fast) var(--ease-out);
}
.search-input:focus { border-color: var(--border-focus); }
.search-input::placeholder { color: var(--text-muted); }

.search-icon {
  position: absolute;
  left: 8px;
  color: var(--text-muted);
  pointer-events: none;
}

/* ============ 布局 ============ */
.terminal-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 10px;
  gap: 10px;
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  min-width: 0;
}

.right-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex-shrink: 0;
}

/* ============ 图表卡片 ============ */
.chart-card {
  min-height: 350px;
  display: flex;
  flex-direction: column;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-muted);
  flex-shrink: 0;
}

.period-tabs,
.adjust-tabs {
  display: flex;
  gap: 3px;
}

.period-tab,
.adjust-tab {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 11.5px;
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.period-tab:hover,
.adjust-tab:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.period-tab.active,
.adjust-tab.active {
  background: var(--accent-gold-light);
  color: var(--accent-gold);
  border-color: var(--border-accent);
}

/* ============ 图表加载占位 ============ */
.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 460px;
  gap: 16px;
  background: var(--bg-primary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-muted);
  border-top-color: var(--accent-gold-light);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: var(--text-muted);
  font-size: 13px;
  font-family: var(--font-mono);
}

/* ============ 分笔成交行样式 ============ */
.row-up td { background: var(--color-up-bg) !important; }
.row-down td { background: var(--color-down-bg) !important; }

/* ============ 响应式 ============ */
@media (max-width: 1200px) {
  .right-panel { width: 260px; }
}

@media (max-width: 900px) {
  .terminal-main { flex-direction: column; }
  .left-panel { flex: none; height: 60%; }
  .right-panel { width: 100%; flex: 1; }
}
</style>
