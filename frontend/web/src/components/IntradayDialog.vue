<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="(v) => emit('update:modelValue', v)"
    :title="dialogTitle"
    width="860px"
    :modal="true"
    class="intraday-dialog"
    @open="onOpen"
    @close="onClose"
  >
    <!-- 顶部统计栏 -->
    <div v-if="intradayData.stats?.open" class="intraday-stats">
      <span>开: <b>{{ intradayData.stats.open }}</b></span>
      <span>高: <b>{{ intradayData.stats.high }}</b></span>
      <span>低: <b>{{ intradayData.stats.low }}</b></span>
      <span>收: <b>{{ intradayData.stats.close }}</b></span>
      <span>量: <b>{{ formatVolume(intradayData.stats.total_volume) }}</b></span>
      <span :class="{ up: intradayData.stats.change > 0, down: intradayData.stats.change < 0 }">
        {{ intradayData.stats.change >= 0 ? '+' : '' }}{{ intradayData.stats.change }}
        ({{ intradayData.stats.pct_change >= 0 ? '+' : '' }}{{ intradayData.stats.pct_change }}%)
      </span>
    </div>

    <!-- 主内容区 -->
    <div class="intraday-body">
      <!-- 左侧：价格档位列表 -->
      <div class="price-ladder">
        <div v-for="(p, i) in sortedPriceLadder" :key="i" class="ladder-row" :class="{ up: p.pct > 0, down: p.pct < 0 }">
          <span class="lp-price">{{ p.price.toFixed(2) }}</span>
          <span class="lp-pct">{{ p.pct >= 0 ? '+' : '' }}{{ p.pct.toFixed(2) }}%</span>
          <span class="lp-vol">{{ formatVolume(p.volume) }}</span>
        </div>
      </div>

      <!-- 中间：分时图 -->
      <div class="intraday-chart-area">
        <div ref="chartRef" style="width:100%;height:100%"></div>
      </div>

      <!-- 右侧：分笔成交 -->
      <div class="tick-list">
        <div class="tick-header">
          <span>时间</span><span>价格</span><span>量</span><span></span>
        </div>
        <div class="tick-body" ref="tickBodyRef">
          <div v-for="(t, i) in intradayData.transactions" :key="i" class="tick-row" :class="{ buy: t.direction === 'B', sell: t.direction === 'S' }">
            <span>{{ String(t.time || '').substring(0, 5) }}</span>
            <span>{{ Number(t.price || 0).toFixed(2) }}</span>
            <span>{{ t.volume }}</span>
            <span class="dir">{{ t.direction === 'B' ? '买' : t.direction === 'S' ? '卖' : '' }}</span>
          </div>
          <div v-if="!intradayData.transactions?.length" class="tick-empty">暂无分笔数据</div>
        </div>
      </div>
    </div>

    <!-- 底部提示 -->
    <template #footer>
      <span class="intraday-tip">Enter 关闭 | 数据对应 K 线选中日期</span>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * IntradayDialog — 分时明细弹窗（复用组件）
 * 用于 Home.vue / StockDetail.vue 中 Enter 键打开的分时盘口窗口
 * Props:
 *   modelValue - 控制显示/隐藏 (v-model)
 *   code       - 股票代码
 *   name       - 股票名称（可选）
 *   date       - 目标日期 YYYY-MM-DD（可选，不传则用当天）
 */
import { ref, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { stockApi } from '@/api/stock.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  code: { type: String, default: '' },
  name: { type: String, default: '' },
  date: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

// ============ 状态 ============
const chartRef = ref(null)
const tickBodyRef = ref(null)
let chartInstance = null
const intradayData = ref({ code: '', date: '', stats: {}, minutes: [], transactions: [] })

/** 弹窗标题 */
const dialogTitle = computed(() => {
  const n = props.name || ''
  const c = intradayData.value.code || props.code || ''
  const d = intradayData.value.date || ''
  return n ? `${n}(${c}) ${d}` : c ? `${c} ${d}` : '分时明细'
})

/** 价格档位（按价格聚合，降序） */
const sortedPriceLadder = computed(() => {
  const mins = intradayData.value.minutes || []
  if (!mins.length) return []
  const priceMap = new Map()
  const openPrice = intradayData.value.stats?.open || 0
  for (const m of mins) {
    const pk = Number(m.price ?? m.close ?? 0)
    if (!pk) continue
    if (priceMap.has(pk)) {
      priceMap.get(pk).volume += (m.volume || 0)
    } else {
      priceMap.set(pk, { price: pk, volume: m.volume || 0 })
    }
  }
  const ladder = Array.from(priceMap.values())
  ladder.sort((a, b) => b.price - a.price)
  for (const p of ladder) {
    p.pct = openPrice ? ((p.price - openPrice) / openPrice) * 100 : 0
  }
  return ladder.slice(0, 30)
})

// ============ 格式化 ============
const formatVolume = (val) => {
  if (!val && val !== 0) return '--'
  val = Number(val)
  if (val >= 100000000) return (val / 100000000).toFixed(2) + '亿'
  if (val >= 10000) return (val / 10000).toFixed(2) + '万'
  return val.toFixed(0)
}

// ============ 生命周期 ============

/** 弹窗打开 → 拉取数据 */
const onOpen = async () => {
  if (!props.code) return
  intradayData.value = { code: '', date: '', stats: {}, minutes: [], transactions: [] }
  try {
    const res = await stockApi.getIntraday(props.code, props.date)
    if (res.data && (res.data.minutes?.length || res.data.transactions?.length)) {
      intradayData.value = {
        code: props.code,
        date: res.data.date || props.date,
        stats: res.data.stats || {},
        minutes: res.data.minutes || [],
        transactions: res.data.transactions || [],
      }
      await nextTick()
      renderChart()
    } else {
      ElMessage.warning('暂无该日分时数据')
      emit('update:modelValue', false)
    }
  } catch (err) {
    console.error('加载分时数据失败:', err)
    ElMessage.error('加载分时数据失败')
    emit('update:modelValue', false)
  }
}

/** 关闭弹窗 → 销毁图表 */
const onClose = () => {
  if (chartInstance) {
    try { chartInstance.dispose() } catch (_) {}
    chartInstance = null
  }
}

/** 渲染分时走势图 */
const renderChart = () => {
  if (!chartRef.value) return
  if (chartInstance) { try { chartInstance.dispose() } catch (_) {} }
  chartInstance = echarts.init(chartRef.value)

  const mins = intradayData.value.minutes || []
  if (!mins.length) return

  const times = mins.map(m => String(m.time || '').substring(0, 5))
  const prices = mins.map(m => m.close ?? m.price ?? 0)
  const volumes = mins.map(m => m.volume || 0)
  const openPrice = intradayData.value.stats?.open || prices[0] || 0

  // 均价线
  const avgPrices = []
  let cumVol = 0, cumAmt = 0
  for (const m of mins) {
    cumVol += (m.volume || 0)
    cumAmt += ((m.amount || (m.close ?? m.price) * m.volume) || 0)
    avgPrices.push(cumVol > 0 ? cumAmt / cumVol : (prices[0] || 0))
  }

  const yestClose = openPrice
  const volColors = mins.map(m => {
    const p = m.close ?? m.price ?? 0
    return p >= yestClose ? 'rgba(239,68,68,0.65)' : 'rgba(34,197,94,0.65)'
  })

  const allPrices = [...prices, yestClose, ...avgPrices].filter(p => p > 0)
  const priceMin = Math.min(...allPrices)
  const priceMax = Math.max(...allPrices)
  const pricePadding = (priceMax - priceMin) * 0.1 || priceMax * 0.02

  chartInstance.setOption({
    grid: [
      { left: 8, right: 12, top: 5, bottom: '55%', height: '40%' },
      { left: 8, right: 12, top: '52%', bottom: 5, height: '28%' },
    ],
    xAxis: [
      { type: 'category', data: times, gridIndex: 0, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#30363d' } }, axisTick: { show: false }, splitLine: { show: true, lineStyle: { color: '#21262d' } } },
      { type: 'category', data: times, gridIndex: 1, axisLabel: { color: '#6e7681', fontSize: 9, interval: Math.max(1, Math.floor(times.length / 6)) }, axisLine: { lineStyle: { color: '#30363d' } }, axisTick: { show: false }, splitLine: { show: true, lineStyle: { color: '#21262d' } } },
    ],
    yAxis: [
      { type: 'value', gridIndex: 0, scale: true, min: priceMin - pricePadding, max: priceMax + pricePadding, axisLabel: { color: '#c9d1d9', fontSize: 10, formatter: v => v.toFixed(2) }, axisLine: { show: false }, splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } } },
      { type: 'value', gridIndex: 1, axisLabel: { color: '#6e7681', fontSize: 9 }, axisLine: { show: false }, splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } } },
    ],
    series: [
      { type: 'line', data: prices, xAxisIndex: 0, yAxisIndex: 0, smooth: true, symbol: 'none', lineStyle: { color: '#ffffff', width: 1.5 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(255,255,255,0.08)' }, { offset: 1, color: 'rgba(255,255,255,0)' }]) }, markLine: { silent: true, symbol: 'none', lineStyle: { color: '#ffe57f', width: 1, type: 'dashed' }, data: [{ yAxis: yestClose, label: { formatter: `昨收:${yestClose.toFixed(2)}`, color: '#ffe57f', fontSize: 10 } }] } },
      { type: 'line', data: avgPrices, xAxisIndex: 0, yAxisIndex: 0, smooth: true, symbol: 'none', lineStyle: { color: '#e3b341', width: 1, type: 'dotted' } },
      { type: 'bar', data: volumes, xAxisIndex: 1, yAxisIndex: 1, itemStyle: { color: (idx) => volColors[idx.dataIndex] }, barMaxWidth: 4 },
    ],
  }, true)
}
</script>

<style scoped>
/* 覆盖弹窗内部样式 */
:deep(.el-dialog) {
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 10px;
  box-shadow: 0 0 40px rgba(0,0,0,0.7);
}
:deep(.el-dialog__header) { background: #1a1f2e; border-bottom: 1px solid #30363d; padding: 12px 16px; margin: 0; }
:deep(.el-dialog__title) { color: #c9d1d9; font-size: 14px; font-weight: 600; }
:deep(.el-dialog__body) { padding: 0 !important; }
:deep(.el-dialog__footer) { padding: 8px 16px; border-top: 1px solid #30363d; }

.intraday-stats {
  display: flex; gap: 20px; padding: 8px 16px;
  background: #161b22; border-bottom: 1px solid #30363d;
  font-size: 13px; color: #c9d1d9;
}
.intraday-stats b { color: #e6edf3; }
.intraday-stats .up { color: #f85149; }
.intraday-stats .down { color: #3fb950; }

.intraday-body { display: flex; height: 400px; }

.price-ladder {
  width: 160px; background: #0d1117; overflow-y: auto;
  border-right: 1px solid #30363d; flex-shrink: 0;
}
.ladder-row { display: flex; justify-content: space-between; align-items: center; padding: 2px 8px; font-size: 12px; color: #c9d1d9; line-height: 1.6; }
.ladder-row.up .lp-price, .ladder-row.up .lp-pct { color: #f85149; }
.ladder-row.down .lp-price, .ladder-row.down .lp-pct { color: #3fb950; }
.lp-vol { color: #6e7681; font-size: 11px; }

.intraday-chart-area { flex: 1; min-width: 300px; border-right: 1px solid #30363d; position: relative; }

.tick-list { width: 200px; flex-shrink: 0; display: flex; flex-direction: column; background: #0d1117; }
.tick-header { display: flex; padding: 4px 8px; background: #161b22; border-bottom: 1px solid #30363d; font-size: 11px; color: #6e7681; }
.tick-header span:nth-child(1) { width: 45px; }
.tick-header span:nth-child(2) { width: 55px; text-align: right; }
.tick-header span:nth-child(3) { width: 45px; text-align: right; }
.tick-header span:nth-child(4) { flex: 1; }
.tick-body { flex: 1; overflow-y: auto; }
.tick-row { display: flex; padding: 2px 8px; font-size: 11px; color: #c9d1d9; line-height: 1.5; font-family: monospace; }
.tick-row.buy .dir { color: #f85149; }
.tick-row.sell .dir { color: #3fb950; }
.tick-row span:nth-child(1) { width: 45px; }
.tick-row span:nth-child(2) { width: 55px; text-align: right; }
.tick-row span:nth-child(3) { width: 45px; text-align: right; }
.tick-row span:nth-child(4) { flex: 1; }
.tick-empty { padding: 30px 10px; text-align: center; color: #6e7681; font-size: 13px; }

.intraday-tip { color: #6e7681; font-size: 12px; }
</style>
