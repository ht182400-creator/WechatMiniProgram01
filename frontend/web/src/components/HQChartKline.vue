<template>
  <!-- ECharts K线图封装组件 (v6 — ECharts 替代 HQChart) -->
  <div class="echart-kline-wrapper" ref="wrapperRef">
    <div class="echart-kline-chart" ref="chartRef"></div>
    <!-- 错误状态覆盖层 -->
    <div v-if="hasError" class="echart-error-overlay" @click="manualRetry">
      <span class="error-text">K线图加载失败</span>
      <button class="retry-btn">点击重试</button>
    </div>
    <!-- 指标按钮栏 -->
    <div class="echart-indicators" v-if="showIndicators">
      <button
        v-for="ind in presetIndicators"
        :key="ind.key"
        :class="['ind-btn', { active: activeIndicators.includes(ind.key) }]"
        @click="toggleIndicator(ind.key)"
        :title="ind.label"
      >
        {{ ind.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
/**
 * ECharts K线图组件 (v6 — ECharts 替代 HQChart)
 *
 * 核心改进：
 * 1. 使用 ECharts 5.5+ 替代 HQChart，根除 ChartBorder 崩溃问题
 * 2. 保持与旧版完全相同的 props 接口，父组件无需修改
 * 3. 支持均线(MA/EMA)、布林带(BOLL)、MACD、KDJ、RSI 指标
 * 4. 双格布局：上方 K线+指标叠加，下方成交量柱状图
 * 5. 子指标(MACD/KDJ/RSI)按需展开独立窗口
 * 6. 内置 dataZoom 支持鼠标滚轮缩放和拖拽平移
 * 7. 红涨绿跌配色
 */
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  /** K线数据: [{ date, open, high, low, close, volume, amount }] */
  data: { type: Array, default: () => [] },
  /** 周期: day/week/month/1min/5min/15min/30min/60min */
  period: { type: String, default: 'day' },
  /** 复权类型: qfq/hfq/none */
  adjust: { type: String, default: 'qfq' },
  /** 股票代码（6位数字） */
  code: { type: String, default: '' },
  /** 股票名称 */
  name: { type: String, default: '' },
  /** 是否显示指标按钮 */
  showIndicators: { type: Boolean, default: true },
  /** 高度 */
  height: { type: [String, Number], default: '500px' }
})

const emit = defineEmits(['ready', 'periodChange', 'enterKeyDown'])

const wrapperRef = ref(null)
const chartRef = ref(null)
const hasError = ref(false)
let chartInstance = null
let resizeObserver = null
/** 防抖定时器 */
let watchDebounceTimer = null
/** 上次数据指纹 */
let lastDataFingerprint = ''

/** 预设指标 */
const presetIndicators = [
  { key: 'MA', label: 'MA' },
  { key: 'BOLL', label: 'BOLL' },
  { key: 'MACD', label: 'MACD' },
  { key: 'KDJ', label: 'KDJ' },
  { key: 'RSI', label: 'RSI' },
  { key: 'VOL', label: 'VOL' }
]
const activeIndicators = ref(['MA', 'VOL'])

// =========================================================================
//  指标计算工具函数
// =========================================================================

/**
 * 计算简单移动平均线 (SMA)
 * @param {number[]} values - 收盘价序列
 * @param {number} period - 周期
 * @returns {(number|null)[]} - 等长数组，不足周期处为 null
 */
const calcSMA = (values, period) => {
  const result = []
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null)
      continue
    }
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) sum += values[j]
    result.push(sum / period)
  }
  return result
}

/**
 * 计算指数移动平均线 (EMA)
 * @param {number[]} values - 收盘价序列
 * @param {number} period - 周期
 * @returns {(number|null)[]}
 */
const calcEMA = (values, period) => {
  const result = []
  const k = 2 / (period + 1)
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null)
      continue
    }
    if (i === period - 1) {
      // 第一条使用 SMA 作为种子
      let sum = 0
      for (let j = 0; j < period; j++) sum += values[j]
      result.push(sum / period)
    } else {
      result.push(values[i] * k + result[i - 1] * (1 - k))
    }
  }
  return result
}

/**
 * 计算布林带 (BOLL)
 * @param {number[]} values - 收盘价序列
 * @param {number} period - 周期，默认 20
 * @param {number} multiplier - 标准差倍数，默认 2
 * @returns {{ upper: (number|null)[], mid: (number|null)[], lower: (number|null)[] }}
 */
const calcBOLL = (values, period = 20, multiplier = 2) => {
  const mid = calcSMA(values, period)
  const upper = []
  const lower = []

  for (let i = 0; i < values.length; i++) {
    if (mid[i] === null) {
      upper.push(null)
      lower.push(null)
      continue
    }
    // 计算 period 窗口内的标准差
    let sumSq = 0
    for (let j = i - period + 1; j <= i; j++) {
      sumSq += (values[j] - mid[i]) ** 2
    }
    const std = Math.sqrt(sumSq / period)
    upper.push(+(mid[i] + multiplier * std).toFixed(4))
    lower.push(+(mid[i] - multiplier * std).toFixed(4))
  }

  return { upper, mid, lower }
}

/**
 * 计算 MACD
 * @param {number[]} closes - 收盘价序列
 * @returns {{ dif: (number|null)[], dea: (number|null)[], histogram: (number|null)[] }}
 */
const calcMACD = (closes) => {
  const ema12 = calcEMA(closes, 12)
  const ema26 = calcEMA(closes, 26)
  const dif = []
  const dea = []
  const histogram = []

  for (let i = 0; i < closes.length; i++) {
    if (ema12[i] === null || ema26[i] === null) {
      dif.push(null)
      dea.push(null)
      histogram.push(null)
      continue
    }
    const dVal = ema12[i] - ema26[i]
    dif.push(+dVal.toFixed(4))
    // DEA: 9-period EMA of DIF
    if (i < 25 + 8) { // ema26 starts at 25, need 9 more for dea
      if (i >= 25 && i < 25 + 8) {
        // 累积填充
        let validDifs = dif.filter(v => v !== null)
        if (validDifs.length >= 9) {
          let sum = 0
          for (let j = validDifs.length - 9; j < validDifs.length; j++) sum += validDifs[j]
          dea.push(+((sum / 9)).toFixed(4))
        } else {
          dea.push(null)
        }
      } else {
        dea.push(null)
      }
    } else {
      // EMA of DIF with period 9
      const k = 2 / 10
      dea.push(+(dVal * k + dea[i - 1] * (1 - k)).toFixed(4))
    }
    if (dea[i] !== null) {
      histogram.push(+((dVal - dea[i]) * 2).toFixed(4))
    } else {
      histogram.push(null)
    }
  }
  return { dif, dea, histogram }
}

/**
 * 计算 KDJ
 * @param {number[]} highs - 最高价序列
 * @param {number[]} lows - 最低价序列
 * @param {number[]} closes - 收盘价序列
 * @param {number} n - 周期，默认 9
 * @returns {{ k: (number|null)[], d: (number|null)[], j: (number|null)[] }}
 */
const calcKDJ = (highs, lows, closes, n = 9) => {
  const k = []
  const d = []
  const j = []

  for (let i = 0; i < closes.length; i++) {
    if (i < n - 1) {
      k.push(null)
      d.push(null)
      j.push(null)
      continue
    }
    // 计算 n 周期内的最高价和最低价
    let highest = -Infinity
    let lowest = Infinity
    for (let m = i - n + 1; m <= i; m++) {
      if (highs[m] > highest) highest = highs[m]
      if (lows[m] < lowest) lowest = lows[m]
    }
    // RSV
    const rsv = lowest === highest ? 50 : ((closes[i] - lowest) / (highest - lowest)) * 100

    // K, D 递推
    const prevK = i === n - 1 ? 50 : k[i - 1]
    const prevD = i === n - 1 ? 50 : d[i - 1]
    const kVal = (2 / 3) * prevK + (1 / 3) * rsv
    const dVal = (2 / 3) * prevD + (1 / 3) * kVal
    const jVal = 3 * kVal - 2 * dVal

    k.push(+kVal.toFixed(2))
    d.push(+dVal.toFixed(2))
    j.push(+jVal.toFixed(2))
  }
  return { k, d, j }
}

/**
 * 计算 RSI
 * @param {number[]} closes - 收盘价序列
 * @param {number} period - 周期，默认 14
 * @returns {(number|null)[]}
 */
const calcRSI = (closes, period = 14) => {
  const result = []
  let avgGain = 0
  let avgLoss = 0

  for (let i = 0; i < closes.length; i++) {
    if (i === 0) {
      result.push(null)
      continue
    }
    const change = closes[i] - closes[i - 1]
    const gain = change > 0 ? change : 0
    const loss = change < 0 ? -change : 0

    if (i < period) {
      avgGain = ((avgGain * (i - 1)) + gain) / i
      avgLoss = ((avgLoss * (i - 1)) + loss) / i
      if (i === period) {
        result.push(+(100 - 100 / (1 + avgGain / (avgLoss || 0.001))).toFixed(2))
      } else {
        result.push(null)
      }
    } else {
      avgGain = (avgGain * (period - 1) + gain) / period
      avgLoss = (avgLoss * (period - 1) + loss) / period
      result.push(+(100 - 100 / (1 + avgGain / (avgLoss || 0.001))).toFixed(2))
    }
  }
  return result
}

// =========================================================================
//  ECharts Option 构建
// =========================================================================

/**
 * 根据当前周期和原始日期值，生成适合该周期的 X 轴标签
 *
 * 不同周期的数据来自后端不同接口，日期格式各异：
 * - 分钟线: "2026-01-15 09:30" 或 "14:30" → 截取时间部分 "HH:mm"
 * - 日线:   "2026-01-15"       → 保持原样
 * - 周线:   "2026-W03"         → 保持原样或转换
 * - 月线:   "2026-01"          → 保持原样
 */
const formatDateLabel = (rawDate) => {
  const s = String(rawDate || '').trim()
  if (!s) return ''

  // 包含时间部分（分钟线特征）
  if (s.includes(':') && s.includes(' ') || /^\d{1,2}:\d{2}$/.test(s)) {
    // 提取 HH:mm 部分
    const match = s.match(/(\d{1,2}:\d{2})/)
    return match ? match[1] : s
  }

  // 纯日期格式：日/周/月保持原样
  return s
}

/**
 * 根据 activeIndicators 动态构建 ECharts option
 * 采用多 grid 布局：主图(K线) → 成交量 → 子指标(MACD/KDJ/RSI)
 */
const buildOption = () => {
  const data = props.data || []
  if (data.length === 0) return {}

  const rawDates = data.map(d => d.date)
  const dates = rawDates.map(formatDateLabel)
  const ohlc = data.map(d => [d.open, d.close, d.low, d.high])
  const volumes = data.map(d => d.volume)
  const closes = data.map(d => d.close)
  const highs = data.map(d => d.high)
  const lows = data.map(d => d.low)

  const hasMA = activeIndicators.value.includes('MA')
  const hasBOLL = activeIndicators.value.includes('BOLL')
  const hasVOL = activeIndicators.value.includes('VOL')
  const hasMACD = activeIndicators.value.includes('MACD')
  const hasKDJ = activeIndicators.value.includes('KDJ')
  const hasRSI = activeIndicators.value.includes('RSI')

  // 成交量颜色
  const volumeColors = data.map(d =>
    d.close >= d.open ? 'rgba(248,81,73,0.45)' : 'rgba(63,185,80,0.45)'
  )
  const volumeBorders = data.map(d =>
    d.close >= d.open ? '#da3633' : '#238636'
  )

  // 计算各指标
  let ma5 = [], ma10 = [], ma20 = [], ma30 = [], ma60 = []
  if (hasMA) {
    ma5 = calcSMA(closes, 5)
    ma10 = calcSMA(closes, 10)
    ma20 = calcSMA(closes, 20)
    ma30 = calcSMA(closes, 30)
    ma60 = calcSMA(closes, 60)
  }

  let boll = { upper: [], mid: [], lower: [] }
  if (hasBOLL) {
    boll = calcBOLL(closes, 20, 2)
  }

  let macd = { dif: [], dea: [], histogram: [] }
  if (hasMACD) {
    macd = calcMACD(closes)
  }

  let kdj = { k: [], d: [], j: [] }
  if (hasKDJ) {
    kdj = calcKDJ(highs, lows, closes, 9)
  }

  let rsi6 = [], rsi12 = [], rsi24 = []
  if (hasRSI) {
    rsi6 = calcRSI(closes, 6)
    rsi12 = calcRSI(closes, 12)
    rsi24 = calcRSI(closes, 24)
  }

  // 动态构建 grid / xAxis / yAxis / series
  const grids = []
  const xAxes = []
  const yAxes = []
  const series = []
  const dataZooms = []

  // ── 计算需要多少个子指标窗口 ──
  const subIndicators = []
  if (hasMACD) subIndicators.push('MACD')
  if (hasKDJ) subIndicators.push('KDJ')
  if (hasRSI) subIndicators.push('RSI')

  // ── 布局百分比 ──
  const subCount = subIndicators.length
  const mainBottom = subCount === 0 ? 62 : (subCount === 1 ? 52 : (subCount === 2 ? 47 : 44))
  const volTop = mainBottom + 2
  const volBottom = volTop + 13

  // Grid 0: 主图 K线（right 留足空间防止 Y 轴标签和最新 K 线被裁切）
  grids.push({ left: '8%', right: '4%', top: 40, bottom: `${100 - mainBottom}%` })
  // xAxis 0: 主图 x 轴
  xAxes.push({
    type: 'category',
    data: dates,
    gridIndex: 0,
    boundaryGap: true,
    axisLine: { lineStyle: { color: '#30363d' } },
    axisTick: { show: false },
    axisLabel: { color: '#6e7681', fontSize: 10 },
    splitLine: { show: false }
  })
  // yAxis 0: 主图 y 轴
  yAxes.push({
    scale: true,
    gridIndex: 0,
    splitLine: { lineStyle: { color: '#252830', type: 'dashed' } },
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#6e7681', fontSize: 10 },
    position: 'right'
  })

  // Grid 1: 成交量
  if (hasVOL) {
    grids.push({ left: '8%', right: '4%', top: `${volTop}%`, height: `${volBottom - volTop}%` })
    xAxes.push({
      type: 'category',
      data: dates,
      gridIndex: 1,
      boundaryGap: true,
      axisLine: { lineStyle: { color: '#30363d' } },
      axisTick: { show: false },
      axisLabel: { show: false },
      splitLine: { show: false }
    })
    yAxes.push({
      scale: true,
      gridIndex: 1,
      splitLine: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false }
    })
  }

  // 子指标 grids (MACD, KDJ, RSI)
  let subGridStart = volBottom + 2
  const subGridHeight = subCount > 0 ? Math.min((100 - subGridStart - 2 * (subCount - 1)) / subCount, 18) : 0
  const subColors = {
    MACD: { dif: '#e3b341', dea: '#58a6ff', histogram_up: 'rgba(248,81,73,0.4)', histogram_down: 'rgba(63,185,80,0.4)' },
    KDJ: { k: '#e3b341', d: '#58a6ff', j: '#bc8cff' },
    RSI: { rsi6: '#e3b341', rsi12: '#58a6ff', rsi24: '#bc8cff' }
  }

  subIndicators.forEach((key, idx) => {
    const top = subGridStart + idx * (subGridHeight + 2)
    // 子指标 grid 索引：有 VOL 时从 2 开始，无 VOL 时从 1 开始
    const gIdx = (hasVOL ? 2 : 1) + idx
    grids.push({ left: '8%', right: '4%', top: `${top}%`, height: `${subGridHeight}%` })
    xAxes.push({
      type: 'category',
      data: dates,
      gridIndex: gIdx,
      boundaryGap: true,
      axisLine: { lineStyle: { color: '#30363d' } },
      axisTick: { show: false },
      axisLabel: idx === subIndicators.length - 1 ? { color: '#6e7681', fontSize: 10 } : { show: false },
      splitLine: { show: false }
    })
    yAxes.push({
      scale: true,
      gridIndex: gIdx,
      splitLine: { lineStyle: { color: '#252830', type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6e7681', fontSize: 10 },
      position: 'right'
    })

    // 添加子指标系列
    switch (key) {
      case 'MACD':
        series.push({
          name: 'MACD柱', type: 'bar', data: macd.histogram,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          itemStyle: {
            color: (params) => {
              const v = macd.histogram[params.dataIndex]
              return v >= 0 ? subColors.MACD.histogram_up : subColors.MACD.histogram_down
            }
          }
        })
        series.push({
          name: 'DIF', type: 'line', data: macd.dif,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.MACD.dif, width: 1 }, symbol: 'none'
        })
        series.push({
          name: 'DEA', type: 'line', data: macd.dea,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.MACD.dea, width: 1 }, symbol: 'none'
        })
        break
      case 'KDJ':
        series.push({
          name: 'K', type: 'line', data: kdj.k,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.KDJ.k, width: 1 }, symbol: 'none'
        })
        series.push({
          name: 'D', type: 'line', data: kdj.d,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.KDJ.d, width: 1 }, symbol: 'none'
        })
        series.push({
          name: 'J', type: 'line', data: kdj.j,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.KDJ.j, width: 1 }, symbol: 'none'
        })
        break
      case 'RSI':
        series.push({
          name: 'RSI6', type: 'line', data: rsi6,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.RSI.rsi6, width: 1 }, symbol: 'none'
        })
        series.push({
          name: 'RSI12', type: 'line', data: rsi12,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.RSI.rsi12, width: 1 }, symbol: 'none'
        })
        series.push({
          name: 'RSI24', type: 'line', data: rsi24,
          xAxisIndex: gIdx, yAxisIndex: gIdx,
          lineStyle: { color: subColors.RSI.rsi24, width: 1 }, symbol: 'none'
        })
        break
    }
  })

  // ── 主图系列: K线 ──
  series.push({
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
  })

  // ── 主图叠加: MA 均线 ──
  if (hasMA) {
    const maConfigs = [
      { name: 'MA5', data: ma5, color: '#e3b341' },
      { name: 'MA10', data: ma10, color: '#58a6ff' },
      { name: 'MA20', data: ma20, color: '#56d4dd' },
      { name: 'MA30', data: ma30, color: '#bc8cff' },
      { name: 'MA60', data: ma60, color: '#f778ba' }
    ]
    maConfigs.forEach(m => {
      series.push({
        name: m.name, type: 'line', data: m.data,
        xAxisIndex: 0, yAxisIndex: 0,
        smooth: true, symbol: 'none',
        lineStyle: { color: m.color, width: 1 }
      })
    })
  }

  // ── 主图叠加: BOLL 布林带 ──
  if (hasBOLL) {
    const bollColors = { upper: '#f85149', mid: '#e3b341', lower: '#3fb950' }
    ;[
      { name: 'BOLL-上轨', data: boll.upper, color: bollColors.upper },
      { name: 'BOLL-中轨', data: boll.mid, color: bollColors.mid },
      { name: 'BOLL-下轨', data: boll.lower, color: bollColors.lower }
    ].forEach(b => {
      series.push({
        name: b.name, type: 'line', data: b.data,
        xAxisIndex: 0, yAxisIndex: 0,
        smooth: true, symbol: 'none',
        lineStyle: { color: b.color, width: 1, type: 'dashed' }
      })
    })
  }

  // ── 成交量柱状图 ──
  if (hasVOL) {
    series.push({
      name: '成交量',
      type: 'bar',
      data: volumes,
      xAxisIndex: 1,
      yAxisIndex: 1,
      itemStyle: {
        color: (params) => volumeColors[params.dataIndex],
        borderColor: (params) => volumeBorders[params.dataIndex],
        borderWidth: 0.5
      }
    })
  }

  // ── dataZoom 缩放：动态收集所有有效的 grid 索引 ──
  const zoomXAxisIndices = [0] // 主图始终参与
  if (hasVOL) zoomXAxisIndices.push(1) // 成交量
  subIndicators.forEach((_, i) => zoomXAxisIndices.push(2 + i)) // 子指标
  dataZooms.push(
    { type: 'inside', xAxisIndex: zoomXAxisIndices, start: 0, end: 100 }
  )
  dataZooms.push(
    {
      type: 'slider',
      xAxisIndex: zoomXAxisIndices,
      bottom: '0%',
      height: '14px',
      borderColor: '#30363d',
      dataBackground: { lineStyle: { color: '#58a6ff', opacity: 0.4 }, areaStyle: { color: 'rgba(88,166,255,0.15)' } },
      selectedDataBackground: { lineStyle: { color: '#58a6ff' }, areaStyle: { color: 'rgba(88,166,255,0.25)' } },
      handleStyle: { color: '#58a6ff' },
      textStyle: { color: '#6e7681', fontSize: 10 }
    }
  )

  // ── 构建 legend data ──
  const legendData = []
  if (hasMA) legendData.push('MA5', 'MA10', 'MA20', 'MA30', 'MA60')
  if (hasBOLL) legendData.push('BOLL-上轨', 'BOLL-中轨', 'BOLL-下轨')
  if (hasVOL) legendData.push('成交量')
  if (hasMACD) legendData.push('DIF', 'DEA')
  if (hasKDJ) legendData.push('K', 'D', 'J')
  if (hasRSI) legendData.push('RSI6', 'RSI12', 'RSI24')

  return {
    backgroundColor: 'transparent',
    animation: true,
    textStyle: { fontFamily: 'JetBrains Mono, monospace' },

    title: {
      text: `${props.name || ''} ${props.code ? `(${props.code})` : ''}`.trim(),
      left: 10,
      top: 6,
      textStyle: { color: '#c9cdd4', fontSize: 13, fontWeight: 'normal' }
    },

    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { color: '#58a6ff', opacity: 0.4 } },
      backgroundColor: 'rgba(36,41,49,0.96)',
      borderColor: '#30363d',
      textStyle: { color: '#c9cdd4', fontSize: 11 },
      formatter: (params) => {
        if (!params || params.length === 0) return ''
        let html = `<div style="font-weight:bold;margin-bottom:4px;">${params[0].axisValue}</div>`
        params.forEach(p => {
          if (p.seriesName === '成交量' || p.seriesName === 'MACD柱') return
          const val = typeof p.value === 'number' ? p.value.toFixed(2) : '—'
          const marker = p.marker || ''
          html += `<div>${marker} ${p.seriesName}: ${val}</div>`
        })
        // 成交量单独显示
        const volParam = params.find(p => p.seriesName === '成交量')
        if (volParam && typeof volParam.value === 'number') {
          const volStr = volParam.value >= 1e8
            ? (volParam.value / 1e8).toFixed(2) + '亿'
            : volParam.value >= 1e4
              ? (volParam.value / 1e4).toFixed(1) + '万'
              : volParam.value
          html += `<div>${volParam.marker || ''} 成交量: ${volStr}</div>`
        }
        return html
      }
    },

    legend: legendData.length > 0 ? {
      data: legendData,
      top: 2,
      right: 4,
      textStyle: { color: '#8b949e', fontSize: 10 },
      itemWidth: 12,
      itemHeight: 8
    } : undefined,

    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    dataZoom: dataZooms,
    series
  }
}

// =========================================================================
//  图表生命周期
// =========================================================================

/** 销毁图表实例 */
const destroyChart = () => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chartInstance) {
    try {
      chartInstance.dispose()
    } catch (e) {
      console.warn('[ECharts] 销毁实例异常:', e)
    }
    chartInstance = null
  }
}

/** 初始化 / 重建 ECharts 实例 */
const initChart = () => {
  if (!chartRef.value) return

  const rawData = props.data
  if (!rawData || rawData.length === 0) {
    hasError.value = false
    return
  }

  // 防重复：指纹必须包含指标状态，否则切换指标时被跳过
  const indKey = activeIndicators.value.sort().join(',')
  const fingerprint = `${rawData.length}-${props.code}-${props.period}-${indKey}`
  if (fingerprint === lastDataFingerprint && chartInstance) {
    return
  }
  lastDataFingerprint = fingerprint
  hasError.value = false

  try {
    // ★ 关键：如果实例已存在且之前出错，先销毁重建（避免部分更新导致的内部不一致）
    if (chartInstance) {
      try { chartInstance.dispose() } catch (_) {}
      chartInstance = null
    }

    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
    }

    const option = buildOption()

    // ★ 使用 requestAnimationFrame 确保 setOption 不在 Vue 更新周期内调用
    requestAnimationFrame(() => {
      if (!chartInstance) return
      try {
        chartInstance.setOption(option, true) // true = notMerge，完全替换

        // 连接 ResizeObserver
        if (!resizeObserver && wrapperRef.value) {
          resizeObserver = new ResizeObserver(() => {
            if (chartInstance) chartInstance.resize()
          })
          resizeObserver.observe(wrapperRef.value)
        }

        emit('ready', chartInstance)
      } catch (e) {
        console.error('[ECharts] setOption 异常:', e)
        hasError.value = true
        // ★ setOption 失败时销毁损坏的实例
        try { chartInstance.dispose() } catch (_) {}
        chartInstance = null
      }
    })
  } catch (e) {
    console.error('[ECharts] 初始化异常:', e)
    hasError.value = true
  }
}

/** 手动重试 */
const manualRetry = () => {
  hasError.value = false
  lastDataFingerprint = ''
  nextTick(() => initChart())
}

/** 刷新（数据变化时） */
const refresh = () => {
  const rawData = props.data
  if (!rawData || rawData.length === 0) return
  nextTick(() => initChart())
}

/** 切换指标：修改 activeIndicators → 重置指纹 → 重建图表 */
const toggleIndicator = (key) => {
  const idx = activeIndicators.value.indexOf(key)
  if (idx > -1) {
    activeIndicators.value.splice(idx, 1)
  } else {
    activeIndicators.value.push(key)
  }
  // ★ 强制重置指纹，确保 initChart() 不被跳过
  lastDataFingerprint = ''
  nextTick(() => initChart())
}

// =========================================================================
//  键盘方向键控制（仿通达信）
// =========================================================================

/**
 * 键盘方向键控制 K 线时间轴（仿通达信交互）
 *
 * 按键映射：
 *   ← 左箭头 : 视图向左平移（查看更早的数据）
 *   → 右箭头 : 视图向右平移（查看更新的数据）
 *   ↑ 上箭头 : 缩小（显示更多K线）
 *   ↓ 下箭头 : 放大（显示更少K线，聚焦细节）
 *   Home     : 跳转到最新数据
 *   End      : 跳转到最老数据
 */
const handleKeydown = (e) => {
  if (!chartInstance) return
  // 仅在无输入框聚焦时生效，避免干扰正常输入
  const tag = document.activeElement?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  const option = chartInstance.getOption()
  const dz = option.dataZoom?.[0] // inside dataZoom
  if (!dz) return

  const start = dz.start ?? 0
  const end = dz.end ?? 100
  const range = end - start
  /** 单次平移量：可视窗口的 10% */
  const shiftStep = Math.max(range * 0.1, 2)
  /** 单次缩放量：5% */
  const zoomStep = 5

  switch (e.key) {
    case 'ArrowLeft': {
      e.preventDefault()
      const newStart = Math.max(0, start - shiftStep)
      const newEnd = newStart + range
      chartInstance.dispatchAction({ type: 'dataZoom', start: newStart, end: newEnd })
      break
    }
    case 'ArrowRight': {
      e.preventDefault()
      const newEnd = Math.min(100, end + shiftStep)
      const newStart = newEnd - range
      chartInstance.dispatchAction({ type: 'dataZoom', start: newStart, end: newEnd })
      break
    }
    case 'ArrowUp': {
      e.preventDefault()
      const newRange = Math.min(100, range + zoomStep)
      const center = (start + end) / 2
      chartInstance.dispatchAction({
        type: 'dataZoom',
        start: Math.max(0, center - newRange / 2),
        end: Math.min(100, center + newRange / 2)
      })
      break
    }
    case 'ArrowDown': {
      e.preventDefault()
      const newRange = Math.max(10, range - zoomStep)
      const center = (start + end) / 2
      chartInstance.dispatchAction({
        type: 'dataZoom',
        start: Math.max(0, center - newRange / 2),
        end: Math.min(100, center + newRange / 2)
      })
      break
    }
    case 'Home':
      e.preventDefault()
      chartInstance.dispatchAction({ type: 'dataZoom', start: 100 - range, end: 100 })
      break
    case 'End':
      e.preventDefault()
      chartInstance.dispatchAction({ type: 'dataZoom', start: 0, end: range })
      break
    case 'Enter':
      // 回车键 → 通知父组件打开分时明细弹窗（仿通达信）
      e.preventDefault()
      emit('enterKeyDown')
      break
  }
}

/** 图表就绪后绑定/解绑键盘事件 */
const bindKeyboardEvents = () => {
  window.addEventListener('keydown', handleKeydown)
}
const unbindKeyboardEvents = () => {
  window.removeEventListener('keydown', handleKeydown)
}

// =========================================================================
//  Watch 监听
// =========================================================================

watch(() => props.data, () => {
  if (watchDebounceTimer) clearTimeout(watchDebounceTimer)
  watchDebounceTimer = setTimeout(() => refresh(), 200)
}, { deep: true })

watch(() => props.code, () => {
  if (watchDebounceTimer) clearTimeout(watchDebounceTimer)
  lastDataFingerprint = ''
  nextTick(() => initChart())
})

// period / adjust 变化：发出事件让父组件重新加载数据
watch(() => props.period, (newVal) => {
  emit('periodChange', newVal)
})

// =========================================================================
//  生命周期
// =========================================================================

onMounted(() => {
  bindKeyboardEvents()
  nextTick(() => {
    setTimeout(() => initChart(), 200)
  })
})

onUnmounted(() => {
  unbindKeyboardEvents()
  if (watchDebounceTimer) {
    clearTimeout(watchDebounceTimer)
    watchDebounceTimer = null
  }
  destroyChart()
})

defineExpose({ refresh, chartInstance })
</script>

<style scoped>
.echart-kline-wrapper {
  position: relative;
  width: 100%;
  height: v-bind(height);
  background: #0d1117;
  border-radius: 4px;
  overflow: hidden;
}

.echart-kline-chart {
  width: 100%;
  height: calc(100% - 36px);
}

/* 错误覆盖层 */
.echart-error-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(13, 17, 23, 0.92);
  z-index: 10;
  cursor: pointer;
}
.echart-error-overlay:hover {
  background: rgba(13, 17, 23, 0.96);
}

.error-text {
  color: #f85149;
  font-size: 13px;
}

.retry-btn {
  padding: 6px 20px;
  border: 1px solid #58a6ff;
  border-radius: 6px;
  background: rgba(88, 166, 255, 0.1);
  color: #58a6ff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.retry-btn:hover {
  background: rgba(88, 166, 255, 0.2);
}

/* 指标按钮栏 */
.echart-indicators {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  height: 36px;
  background: #161b22;
  border-top: 1px solid #252830;
  overflow-x: auto;
}
.echart-indicators::-webkit-scrollbar {
  height: 0;
}

.ind-btn {
  flex-shrink: 0;
  padding: 2px 10px;
  border: 1px solid #30363d;
  border-radius: 3px;
  background: transparent;
  color: #6e7681;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}
.ind-btn:hover {
  color: #c9cdd4;
  border-color: #58a6ff;
}
.ind-btn.active {
  background: rgba(88, 166, 255, 0.12);
  color: #79c0ff;
  border-color: #58a6ff;
}
</style>
