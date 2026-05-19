<template>
  <div class="stock-detail-page" v-loading="loading">
    <!-- 股票信息 -->
    <el-card class="info-card">
      <div class="stock-header">
        <div class="stock-title">
          <h2>{{ stockCode }}</h2>
          <el-tag type="success">{{ stockInfo.name }}</el-tag>
        </div>
        <div class="stock-price">
          <span class="current-price">{{ stockInfo.close || '--' }}</span>
          <span :class="['change', priceChange >= 0 ? 'price-up' : 'price-down']">
            {{ priceChange >= 0 ? '+' : '' }}{{ priceChange?.toFixed(2) || '--' }}
            ({{ priceChangePct?.toFixed(2) || '--' }}%)
          </span>
        </div>
      </div>
    </el-card>

    <!-- K线图表 -->
    <el-card class="chart-card">
      <div ref="chartRef" class="kline-chart"></div>
    </el-card>

    <!-- 技术指标 -->
    <el-card class="indicators-card">
      <template #header>
        <div class="card-header">
          <span>技术指标</span>
          <el-button type="primary" link @click="loadIndicators">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </template>
      <el-descriptions :column="3" border v-if="indicators">
        <el-descriptions-item label="收盘价">{{ indicators.close }}</el-descriptions-item>
        <el-descriptions-item label="MA5">{{ indicators.sma_5?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="MA20">{{ indicators.sma_20?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="MA60">{{ indicators.sma_60?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="RSI14">
          <span :class="getRsiClass(indicators.rsi_14)">
            {{ indicators.rsi_14?.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="MACD">{{ indicators.macd?.toFixed(4) }}</el-descriptions-item>
        <el-descriptions-item label="KDJ-K">{{ indicators.kdj_k?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="KDJ-D">{{ indicators.kdj_d?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="KDJ-J">{{ indicators.kdj_j?.toFixed(2) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { stockApi } from '@/api'

const route = useRoute()
const chartRef = ref(null)
let chartInstance = null

const stockCode = computed(() => route.params.code)
const stockInfo = ref({})
const chartData = ref([])
const indicators = ref({})
const loading = ref(false)

const priceChange = computed(() => stockInfo.value.pct_change || 0)
const priceChangePct = computed(() => stockInfo.value.pct_change || 0)

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
    const res = await stockApi.getChartData(stockCode.value, 'daily', 120)
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

const updateChart = () => {
  if (!chartInstance || chartData.value.length === 0) return

  const dates = chartData.value.map(d => d.date)
  const ohlc = chartData.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = chartData.value.map(d => d.volume)
  const ma5 = chartData.value.map(d => d.ma5)
  const ma20 = chartData.value.map(d => d.ma20)
  const ma60 = chartData.value.map(d => d.ma60)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['MA5', 'MA20', 'MA60'],
      top: 10
    },
    grid: [
      { left: '10%', right: '8%', height: '50%' },
      { left: '10%', right: '8%', top: '65%', height: '15%' }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, boundaryGap: false },
      { type: 'category', data: dates, gridIndex: 1, boundaryGap: false }
    ],
    yAxis: [
      { scale: true, gridIndex: 0 },
      { scale: true, gridIndex: 1 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true
      },
      {
        name: 'MA60',
        type: 'line',
        data: ma60,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true
      },
      {
        name: '成交量',
        type: 'bar',
        data: volumes,
        xAxisIndex: 1,
        yAxisIndex: 1
      }
    ]
  }

  chartInstance.setOption(option)
}

const getRsiClass = (rsi) => {
  if (!rsi) return ''
  if (rsi > 70) return 'price-up' // 超买
  if (rsi < 30) return 'price-down' // 超卖
  return ''
}

const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }
}

onMounted(async () => {
  loading.value = true
  initChart()
  await Promise.all([
    loadStockInfo(),
    loadChartData(),
    loadIndicators()
  ])
  loading.value = false
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(stockCode, () => {
  loadStockInfo()
  loadChartData()
  loadIndicators()
})
</script>

<style scoped>
.stock-detail-page {
  max-width: 1400px;
  margin: 0 auto;
}

.info-card {
  margin-bottom: 16px;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stock-title h2 {
  margin: 0;
}

.current-price {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.change {
  font-size: 16px;
  margin-left: 12px;
}

.chart-card {
  margin-bottom: 16px;
}

.kline-chart {
  height: 500px;
}

.indicators-card {
  margin-bottom: 16px;
}
</style>
