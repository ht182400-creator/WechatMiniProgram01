<template>
  <div class="terminal-container">
    <!-- 顶部导航栏（共享组件） -->
    <AppHeader>
      <template #search>
        <div class="search-box">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input type="text" v-model="searchKeyword" placeholder="输入股票代码或名称搜索..."
            @keyup.enter="handleSearch" class="search-input" />
        </div>
      </template>
      <template #actions>
        <button class="btn-icon" title="刷新数据" @click="refreshData">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23,4 23,10 17,10"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10"/></svg>
        </button>
      </template>
    </AppHeader>

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
                {{ stock.price ? formatPrice(stock.price) : '--' }}
              </span>
              <div class="price-change font-mono" :class="getPriceClass(stock.change)">
                <span class="change-value">{{ stock.change ? (stock.change >= 0 ? '+' : '') + formatPrice(stock.change) : '--' }}</span>
                <span class="change-percent">{{ stock.pct_change ? (stock.pct_change >= 0 ? '+' : '') + formatPercent(stock.pct_change) + '%' : '--' }}</span>
              </div>
            </div>
            <!-- 删除按钮 -->
            <button class="remove-btn" @click.stop="removeFromWatchlist(stock.code)" title="移除自选">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
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
              <div class="hot-right">
                <div class="hot-price font-mono" :class="getPriceClass(stock.change)">
                  {{ formatPrice(stock.price) }}
                </div>
                <div class="hot-change font-mono" :class="stock.pct_change > 0 ? 'price-up' : stock.pct_change < 0 ? 'price-down' : ''">
                  {{ stock.pct_change != null ? (stock.pct_change > 0 ? '+' : '') + formatPercent(stock.pct_change) + '%' : '--' }}
                </div>
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
              <span class="rank-price font-mono">{{ stock.price != null ? formatPrice(stock.price) : '--' }}</span>
              <span class="rank-change font-mono" :class="stock.pct_change > 0 ? 'price-up' : stock.pct_change < 0 ? 'price-down' : ''">
                {{ stock.pct_change != null ? (stock.pct_change > 0 ? '+' : '') + formatPercent(stock.pct_change) + '%' : '--' }}
              </span>
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
          @input="debouncedSearch"
        />
      </div>
      <div class="search-results" v-if="searchResults.length">
        <div 
          v-for="stock in searchResults" 
          :key="stock.code"
          class="search-result-item"
          @click="addToWatchlist(stock)"
        >
          <span class="result-name">{{ stock.name }}</span>
          <span class="result-code font-mono">{{ stock.code }}</span>
        </div>
      </div>
      <!-- 搜索中或无结果时的提示 -->
      <div v-else-if="addKeyword.trim().length >= 1" class="search-empty">
        {{ '未找到相关股票，请尝试其他关键词' }}
      </div>
    </el-dialog>


    <!-- 分时明细弹窗（共享组件，回车键打开） -->
    <IntradayDialog v-model="showIntradayDialog" :code="currentStock" :name="selectedStock?.name" :date="intradayTargetDate" />


    <!-- 底部状态栏（共享组件） -->
    <AppFooter :wsStatus="wsStatusClass" :wsText="wsStatusText" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import IntradayDialog from '@/components/IntradayDialog.vue'
import { stockApi } from '@/api/stock.js'

const router = useRouter()

// ============ WebSocket 实时行情 ============
const { connectionStatus, quotes, subscribe, unsubscribe } = useWebSocket()

// ============ 状态变量 ============
const loading = ref(false)
const searchKeyword = ref('')
const addKeyword = ref('')
const showAddDialog = ref(false)
const mainChartRef = ref(null)

// ============ 分时明细弹窗（共享组件，回车键打开）============
const showIntradayDialog = ref(false)
const intradayTargetDate = ref('')

/** 回车键 → 获取 K 线当前日期 → 打开分时窗口 */
const openIntradayDialog = () => {
  if (!currentStock.value || !chartInstance) return
  try {
    const option = chartInstance.getOption()
    const xAxisData = option.xAxis?.[0]?.data || []
    const dz = option.dataZoom?.[0]
    if (dz && xAxisData.length > 0) {
      const endIdx = Math.floor((dz.end / 100) * xAxisData.length) - 1
      intradayTargetDate.value = xAxisData[Math.min(endIdx, xAxisData.length - 1)] || xAxisData[xAxisData.length - 1] || ''
    } else if (xAxisData.length > 0) {
      intradayTargetDate.value = xAxisData[xAxisData.length - 1]
    }
  } catch (_) { intradayTargetDate.value = '' }
  showIntradayDialog.value = true
}
let chartInstance = null

/** localStorage 自选股持久化 key */
const STORAGE_KEY_WATCHLIST = 'quant_terminal_watchlist'

/**
 * 从 localStorage 加载自选股列表
 * @returns {Array} 自选股数组，格式 [{code, name, price, change, pct_change}]
 */
const loadWatchlistFromStorage = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_WATCHLIST)
    if (saved) {
      const list = JSON.parse(saved)
      if (Array.isArray(list) && list.length > 0) {
        return list
      }
    }
  } catch (e) {
    console.warn('读取自选股缓存失败:', e)
  }
  // 默认自选股（首次使用）
  return [
    { name: '浦发银行', code: '600000', price: 0, change: 0, pct_change: 0 },
    { name: '平安银行', code: '000001', price: 0, change: 0, pct_change: 0 },
    { name: '万科A', code: '000002', price: 0, change: 0, pct_change: 0 },
    { name: '贵州茅台', code: '600519', price: 0, change: 0, pct_change: 0 }
  ]
}

/**
 * 校验并修复自选股列表中的异常名称
 * 若某只股票的 name 不是中文（如显示为代码数字），则通过搜索 API 获取真实中文名
 */
const fixStockNames = async () => {
  /** 判断字符串是否包含中文字符 */
  const hasChinese = (s) => /[\u4e00-\u9fa5]/.test(s || '')

  const needsFix = watchlist.value.filter(s => !hasChinese(s.name))
  if (needsFix.length === 0) return

  console.log(`[Home] 发现 ${needsFix.length} 只股票名称需要修复`)
  for (const stock of needsFix) {
    try {
      const results = await stockApi.search(stock.code)
      if (results && Array.isArray(results)) {
        // 精确匹配或尾部匹配
        const match = results.find(r =>
          r.code === stock.code ||
          r.code?.endsWith(stock.code) ||
          stock.code.endsWith(r.code || '')
        )
        if (match?.name && hasChinese(match.name)) {
          stock.name = match.name
          console.log(`[Home] 名称修复: ${stock.code} → ${match.name}`)
        }
      }
    } catch (e) {
      console.warn(`[Home] 搜索 ${stock.code} 失败:`, e)
    }
  }
  // 保存修复后的结果
  saveWatchlistToStorage(watchlist.value)
}

/** 持久化保存自选股到 localStorage */
const saveWatchlistToStorage = (list) => {
  try {
    // 只保存 code 和 name，价格由实时行情动态填充
    const toSave = list.map(({ code, name }) => ({ code, name }))
    localStorage.setItem(STORAGE_KEY_WATCHLIST, JSON.stringify(toSave))
  } catch (e) {
    console.warn('保存自选股失败:', e)
  }
}

// 自选股列表
const watchlist = ref(loadWatchlistFromStorage())
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

// 市场指数（WebSocket 实时更新）
const marketData = ref([
  { name: '上证指数', code: 'sh000001', value: 0, change: 0, change_pct: 0 },
  { name: '深证成指', code: 'sz399001', value: 0, change: 0, change_pct: 0 },
  { name: '创业板指', code: 'sz399006', value: 0, change: 0, change_pct: 0 },
  { name: '沪深300', code: 'sh000300', value: 0, change: 0, change_pct: 0 }
])

// 热门股票（默认列表，价格由 WebSocket 动态更新）
const hotStocks = ref([
  { name: '贵州茅台', code: '600519', price: null, change: null, pct_change: null },
  { name: '宁德时代', code: '300750', price: null, change: null, pct_change: null },
  { name: '比亚迪', code: '002594', price: null, change: null, pct_change: null },
  { name: '中国平安', code: '601318', price: null, change: null, pct_change: null }
])

// 涨幅榜（默认占位，可后续对接涨跌榜API）
const gainers = ref([
  { name: '剑桥科技', code: '603083', price: null, pct_change: null },
  { name: '中科曙光', code: '603019', price: null, pct_change: null },
  { name: '浪潮信息', code: '000977', price: null, pct_change: null },
  { name: '紫光股份', code: '000938', price: null, pct_change: null },
  { name: '科大讯飞', code: '002230', price: null, pct_change: null }
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

/** 实时行情到达时，同步更新所有面板数据 */
watch(() => quotes.value, (newQuotes) => {
  let hasChange = false

  /**
   * 安全合并股票名称
   * 仅当 WS 推送来的 name 包含中文字符时才使用，否则保留本地已有名称
   * 防止后端推送数字/代码等异常值覆盖已修复的中文名称
   */
  const safeName = (wsName, localName) => {
    if (wsName && /[\u4e00-\u9fa5]/.test(wsName)) return wsName
    return localName
  }

  // ── 更新自选股价格 ──
  const updated = watchlist.value.map(stock => {
    const q = newQuotes[stock.code]
    if (q && q.price !== undefined) {
      hasChange = true
      return { ...stock, name: safeName(q.name, stock.name), price: q.price, change: q.change || 0, pct_change: q.pct_change || 0 }
    }
    return stock
  })
  if (hasChange) {
    watchlist.value = updated
    // 同步更新当前选中股票
    if (currentStock.value && newQuotes[currentStock.value]) {
      const q = newQuotes[currentStock.value]
      if (selectedStock.value) {
        selectedStock.value = {
          ...selectedStock.value,
          name: safeName(q.name, selectedStock.value.name),
          price: q.price,
          change: q.change || 0,
          pct_change: q.pct_change || 0
        }
      }
    }
  }

  // ── 更新热门股票价格 ──
  const hotUpdated = hotStocks.value.map(stock => {
    const q = newQuotes[stock.code]
    if (q && q.price !== undefined) {
      return { ...stock, price: q.price, change: q.change || 0, pct_change: q.pct_change || 0 }
    }
    return stock
  })
  hotStocks.value = hotUpdated

  // ── 更新涨幅榜价格（与热门股票同理） ──
  const gainersUpdated = gainers.value.map(stock => {
    const q = newQuotes[stock.code]
    if (q && q.price !== undefined) {
      return { ...stock, price: q.price, change: q.change || 0, pct_change: q.pct_change || 0 }
    }
    return stock
  })
  gainers.value = gainersUpdated

  // ── 更新市场指数 ──
  /**
   * 查找行情数据，兼容带前缀(sh000001)和不带前缀(000001)两种 code 格式
   * 后端 WS 推送的 code 取决于数据源返回格式，可能与前端存储的 marketData.code 不一致
   */
  const findQuote = (code) => {
    // 精确匹配
    if (newQuotes[code]) return newQuotes[code]
    // 去掉 sh/sz 前缀再匹配
    const stripped = code.replace(/^(sh|sz|SH|SZ)/i, '')
    if (newQuotes[stripped]) return newQuotes[stripped]
    return null
  }
  const marketUpdated = marketData.value.map(m => {
    const q = findQuote(m.code)
    if (q && q.price !== undefined) {
      return { ...m, value: q.price, change: q.change || 0, change_pct: q.pct_change || 0 }
    }
    return m
  })
  marketData.value = marketUpdated
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
    case 'connected': return 'connected'
    case 'connecting': return 'connecting'
    default: return 'disconnected'
  }
})

const latestMa = computed(() => {
  if (!chartData.value.length) return {}
  const latest = chartData.value[chartData.value.length - 1]
  /** 格式化 MA 值到2位小数 */
  const fmt = (v) => (v != null && !isNaN(v)) ? Number(v).toFixed(2) : '--'
  return {
    ma5: fmt(latest.ma5),
    ma10: fmt(latest.ma10),
    ma20: fmt(latest.ma20),
    ma30: fmt(latest.ma30)
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

/**
 * 添加自选股
 * 从搜索结果获取真实名称，保存到 localStorage，并订阅 WebSocket 行情
 */
const addToWatchlist = async (codeOrItem) => {
  // 兼容传入 code 字符串或搜索结果对象
  const code = typeof codeOrItem === 'string' ? codeOrItem : (codeOrItem.code || '')
  const name = typeof codeOrItem === 'string' ? '' : (codeOrItem.name || '')

  if (!code) {
    ElMessage.warning('无效的股票代码')
    return
  }

  // 去重检查
  if (watchlist.value.find(s => s.code === code)) {
    ElMessage.info('已在自选列表中')
    return
  }

  const newStock = { code, name: name || `股票${code}`, price: 0, change: 0, pct_change: 0 }
  watchlist.value.push(newStock)
  saveWatchlistToStorage(watchlist.value)

  // 订阅 WebSocket 实时行情
  if (connectionStatus.value === 'connected') subscribe([code])

  ElMessage.success('已添加到自选')
  showAddDialog.value = false
  addKeyword.value = ''
  searchResults.value = []
}

/** 从搜索列表移除自选股 */
const removeFromWatchlist = (code) => {
  const idx = watchlist.value.findIndex(s => s.code === code)
  if (idx > -1) {
    watchlist.value.splice(idx, 1)
    saveWatchlistToStorage(watchlist.value)
    if (connectionStatus.value === 'connected') unsubscribe([code])
    ElMessage.success('已从自选移除')
  }
}

/**
 * 搜索股票（调用真实后端 API）
 */
/**
 * 执行股票搜索
 * 后端返回 { total, stocks: [...] } 格式，需取 stocks 字段
 */
const searchStocks = async () => {
  const keyword = addKeyword.value.trim()
  if (keyword.length < 1) {
    searchResults.value = []
    return
  }
  try {
    const res = await stockApi.search(keyword)
    // 兼容两种返回格式：数组直接返回 / { total, stocks } 对象格式
    const list = Array.isArray(res) ? res : (res?.stocks || [])
    if (list.length > 0) {
      searchResults.value = list.slice(0, 10)
    } else {
      searchResults.value = []
    }
  } catch (e) {
    console.warn('搜索失败:', e)
    searchResults.value = []
  }
}

// 防抖搜索
let searchDebounceTimer = null
const debouncedSearch = () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => searchStocks(), 300)
}

const refreshData = () => {
  loadChartData()
  ElMessage.success('数据已刷新')
}

// ============ K线图 ============
const loadChartData = async () => {
  if (!selectedStock.value) return
  const code = selectedStock.value.code

  try {
    const res = await stockApi.getChartData(code, currentPeriod.value, 120, adjustType.value)
    const dataList = res.chart_data || []
    if (dataList.length > 0) {
      chartData.value = dataList
      // 用最新K线收盘价初始化当前股票价格（WS推送到达前的兜底）
      const lastBar = dataList[dataList.length - 1]
      if (lastBar?.close > 0 && (!selectedStock.value.price || selectedStock.value.price === 0)) {
        selectedStock.value = { ...selectedStock.value, price: lastBar.close }
        // 同步更新自选股列表中的价格
        const wlIdx = watchlist.value.findIndex(s => s.code === code)
        if (wlIdx >= 0) {
          watchlist.value[wlIdx] = { ...watchlist.value[wlIdx], price: lastBar.close }
        }
      }
      updateChart()
    }
  } catch (e) {
    console.warn('加载K线数据失败:', e)
    // API 失败时保持空状态，不显示模拟数据
  }
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
        lineStyle: { color: '#58a6ff', opacity: 0.5 },
        crossStyle: { color: '#58a6ff', opacity: 0.5 }
      },
      backgroundColor: 'rgba(36, 41, 49, 0.95)',
      borderColor: '#30363d',
      textStyle: { color: '#c9cdd4', fontFamily: 'JetBrains Mono', fontSize: 12 },
      /**
       * 自定义 K 线 tooltip 格式化
       * OHLC + MA 均线值统一保留2位小数
       */
      formatter(params) {
        if (!params || !params.length) return ''
        let html = `<div style="margin-bottom:4px;font-weight:bold;color:#f0f6fc">${params[0].axisValue}</div>`
        for (const p of params) {
          // 跳过无值的空数据点
          if (p.value == null || (Array.isArray(p.value) && p.value[1] == null)) continue
          const v = Array.isArray(p.value) ? p.value[1] : p.value
          const fmtVal = typeof v === 'number' ? v.toFixed(2) : v
          const marker = p.marker ? `<span style="display:inline-block;margin-right:4px">${p.marker}</span>` : ''
          html += `<div style="line-height:1.6">${marker}${p.seriesName}: <b>${fmtVal}</b></div>`
        }
        return html
      }
    },
    legend: {
      data: ['MA5', 'MA10', 'MA20', 'MA30'],
      top: 0,
      right: 10,
      textStyle: { color: '#8b949e' }
    },
    grid: [
      { left: '10px', right: '10px', top: '40px', height: '52%' },
      { left: '10px', right: '10px', top: '73%', height: '18%', bottom: '8%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#30363d' } },
        axisTick: { show: false },
        axisLabel: { color: '#6e7681', fontSize: 10 }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#30363d' } },
        axisTick: { show: false },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6e7681', fontSize: 10 }
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
      { type: 'slider', xAxisIndex: [0, 1], bottom: '2%', height: '15px', borderColor: '#30363d' }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#f85149',
          color0: '#3fb950',
          borderColor: '#da3633',
          borderColor0: '#238636'
        }
      },
      {
        name: 'MA5', type: 'line', data: chartData.value.map(d => d.ma5),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#e3b341', width: 1 }, symbol: 'none'
      },
      {
        name: 'MA10', type: 'line', data: chartData.value.map(d => d.ma10),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#58a6ff', width: 1 }, symbol: 'none'
      },
      {
        name: 'MA20', type: 'line', data: chartData.value.map(d => d.ma20),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#56d4dd', width: 1 }, symbol: 'none'
      },
      {
        name: 'MA30', type: 'line', data: chartData.value.map(d => d.ma30),
        xAxisIndex: 0, yAxisIndex: 0, smooth: true,
        lineStyle: { color: '#bc8cff', width: 1 }, symbol: 'none'
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

// =========================================================================
//  键盘方向键控制 K 线时间轴（仿通达信）
// =========================================================================

/**
 * Home 页面 K 线图键盘事件处理
 * 与 HQChartKline 组件中的实现逻辑一致
 */
const handleChartKeydown = (e) => {
  if (!chartInstance) return
  // 仅在无输入框聚焦时生效
  const tag = document.activeElement?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  const option = chartInstance.getOption()
  const dz = option.dataZoom?.[0]
  if (!dz) return

  const start = dz.start ?? 0
  const end = dz.end ?? 100
  const range = end - start
  const shiftStep = Math.max(range * 0.1, 2)
  const zoomStep = 5

  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault()
      chartInstance.dispatchAction({ type: 'dataZoom', start: Math.max(0, start - shiftStep), end: Math.max(0, start - shiftStep) + range })
      break
    case 'ArrowRight':
      e.preventDefault()
      chartInstance.dispatchAction({ type: 'dataZoom', start: Math.min(100, end + shiftStep) - range, end: Math.min(100, end + shiftStep) })
      break
    case 'ArrowUp':
      e.preventDefault()
      { const r = Math.min(100, range + zoomStep), c = (start + end) / 2
        chartInstance.dispatchAction({ type: 'dataZoom', start: Math.max(0, c - r/2), end: Math.min(100, c + r/2) }) }
      break
    case 'ArrowDown':
      e.preventDefault()
      { const r = Math.max(10, range - zoomStep), c = (start + end) / 2
        chartInstance.dispatchAction({ type: 'dataZoom', start: Math.max(0, c - r/2), end: Math.min(100, c + r/2) }) }
      break
    case 'Home':
      e.preventDefault()
      chartInstance.dispatchAction({ type: 'dataZoom', start: 100 - range, end: 100 })
      break
    case 'End':
      e.preventDefault()
      chartInstance.dispatchAction({ type: 'dataZoom', start: 0, end: range })
      break
    case 'Enter':
      // 回车键 → 打开当日分时明细窗口
      e.preventDefault()
      openIntradayDialog()
      break
  }
}

/** 绑定键盘事件 */
window.addEventListener('keydown', handleChartKeydown)

// ============ 生命周期 ============
onMounted(async () => {
  // 从 localStorage 恢复自选股列表
  const saved = loadWatchlistFromStorage()
  watchlist.value = saved

  // 校验并修复异常名称（非中文名称 → 通过搜索 API 获取真实名称）
  await fixStockNames()

  // 设置默认选中
  if (watchlist.value.length > 0) {
    selectedStock.value = { ...watchlist.value[0] }
    currentStock.value = selectedStock.value.code
  }

  // 初始化图表
  initChart()
  loadChartData()

  // 收集所有需要订阅的代码：自选股 + 热门股 + 市场指数
  const allCodes = [
    ...watchlist.value.map(s => s.code),
    ...hotStocks.value.map(s => s.code),
    ...marketData.value.map(m => m.code),
    ...gainers.value.map(g => g.code)
  ].filter(Boolean)

  // 启动 WebSocket 连接并订阅所有股票
  if (allCodes.length > 0) subscribe(allCodes)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleChartKeydown)
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
  grid-template-columns: 1fr auto auto auto;
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

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  opacity: 0;
  transition: all 0.15s;
}
.stock-item:hover .remove-btn { opacity: 1; }
.remove-btn:hover {
  background: rgba(239,68,68,0.15);
  color: #ef4444;
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

/** 热门股票右侧：价格 + 涨跌幅容器 */
.hot-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
}

.hot-change {
  font-size: 11px;
  opacity: 0.85;
}

.rank-name {
  flex: 1;
  font-size: 12px;
}

.rank-price {
  font-size: 12px;
  min-width: 60px;
  text-align: right;
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

/** 搜索结果为空时的提示 */
.search-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
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
