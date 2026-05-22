<template>
  <div class="finance-page">
    <AppHeader />

    <!-- 页面级导航栏：返回主页 -->
    <div class="page-header">
      <div class="header-left">
        <router-link to="/" class="back-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回主页
        </router-link>
        <span class="page-title">财务分析</span>
      </div>
    </div>

    <!-- 查询配置 -->
    <el-card class="config-card">
      <el-form :model="config" inline>
        <el-form-item label="股票代码">
          <el-input v-model="config.code" placeholder="如: 600000" style="width: 130px"
            @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item label="报告期">
          <el-select v-model="config.reportDate" placeholder="选择报告期" style="width: 160px"
            :loading="datesLoading" @change="loadData">
            <el-option
              v-for="d in reportDates"
              :key="d.value"
              :label="d.label"
              :value="d.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData" :loading="loading">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;vertical-align:-2px">
              <polyline points="23,4 23,10 17,10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 核心财务指标卡片 -->
    <div v-if="indicators && indicators.indicators" class="metrics-grid">
      <el-card v-for="(item, idx) in metricCards" :key="idx" class="metric-card">
        <div class="metric-label">{{ item.label }}</div>
        <div class="metric-value" :class="item.colorClass">
          {{ formatValue(indicators.indicators[item.field]) }}
        </div>
        <div v-if="item.subField" class="metric-sub">
          同比 {{ formatChange(indicators.indicators[item.subField]) }}
        </div>
      </el-card>
    </div>

    <!-- Tab 切换区域 -->
    <el-card style="margin-top: 16px;">
      <template #header>
        <el-tabs v-model="activeTab" @tab-change="onTabChange">
          <el-tab-pane label="财务指标" name="indicators" />
          <el-tab-pane label="资产负债表" name="balance" />
          <el-tab-pane label="利润表" name="income" />
          <el-tab-pane label="现金流量表" name="cashflow" />
          <el-tab-pane label="历史趋势" name="history" />
        </el-tabs>
      </template>

      <!-- 财务指标详情表格 -->
      <div v-show="activeTab === 'indicators'" class="tab-content">
        <div class="table-scroll-wrapper">
          <el-table :data="indicatorRows" stripe size="small" border
            v-loading="loading && activeTab === 'indicators'"
            empty-text="请输入股票代码查询"
            style="width: 100%"
            :height="tableHeight">
            <el-table-column prop="name" label="指标名称" width="200" fixed />
            <el-table-column prop="value" label="最新值" width="140">
              <template #default="{ row }">
                <span :class="row.colorClass || ''">{{ row.formatted }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="80" align="center" />
            <el-table-column prop="desc" label="说明" />
          </el-table>
        </div>
      </div>

      <!-- 资产负债表 -->
      <div v-show="activeTab === 'balance'" class="tab-content">
        <div class="table-scroll-wrapper">
          <el-table :data="balanceRows" stripe size="small" border
            v-loading="loading && activeTab === 'balance'"
            empty-text="暂无资产负债数据"
            style="width: 100%"
            :height="tableHeight">
            <el-table-column prop="name" label="项目" width="220" fixed />
            <el-table-column prop="value" label="金额（万元）" width="180" align="right">
              <template #default="{ row }">{{ formatNumber(row.value) }}</template>
            </el-table-column>
            <el-table-column prop="ratio" label="占比" width="100" align="center">
              <template #default="{ row }">{{ row.ratio ? row.ratio + '%' : '-' }}</template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 利润表 -->
      <div v-show="activeTab === 'income'" class="tab-content">
        <div class="table-scroll-wrapper">
          <el-table :data="incomeRows" stripe size="small" border
            v-loading="loading && activeTab === 'income'"
            empty-text="暂无利润表数据"
            style="width: 100%"
            :height="tableHeight">
            <el-table-column prop="name" label="项目" width="240" fixed />
            <el-table-column prop="value" label="金额（万元）" width="180" align="right">
              <template #default="{ row }">{{ formatNumber(row.value) }}</template>
            </el-table-column>
            <el-table-column prop="yoy" label="同比增长" width="120" align="center">
              <template #default="{ row }">
                <span v-if="row.yoy !== null" :class="row.yoy >= 0 ? 'price-up' : 'price-down'">
                  {{ row.yoy >= 0 ? '+' : '' }}{{ row.yoy.toFixed(2) }}%
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 现金流量表 -->
      <div v-show="activeTab === 'cashflow'" class="tab-content">
        <div class="table-scroll-wrapper">
          <el-table :data="cashflowRows" stripe size="small" border
            v-loading="loading && activeTab === 'cashflow'"
            empty-text="暂无现金流量数据"
            style="width: 100%"
            :height="tableHeight">
            <el-table-column prop="name" label="项目" width="260" fixed />
            <el-table-column prop="value" label="金额（万元）" width="180" align="right">
              <template #default="{ row }">{{ formatNumber(row.value) }}</template>
            </el-table-column>
            <el-table-column prop="note" label="备注" />
          </el-table>
        </div>
      </div>

      <!-- 历史趋势图表 -->
      <div v-show="activeTab === 'history'" class="tab-content history-section">
        <div ref="chartRef" class="chart-container"></div>
        <div class="table-scroll-wrapper" style="margin-top: 12px;">
          <el-table :data="historyRows" stripe size="small" border
            v-loading="loading && activeTab === 'history'"
            empty-text="暂无历史数据"
            style="width: 100%"
            :height="historyTableHeight">
            <el-table-column prop="report_date" label="报告期" width="120" fixed />
            <el-table-column v-for="col in historyColumns" :key="col.prop"
              :prop="col.prop" :label="col.label" width="130" align="right">
              <template #default="{ row }">{{ formatNumber(row[col.prop]) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

/** 页面状态 */
const config = reactive({
  code: '600000',
  reportDate: ''
})
const loading = ref(false)
const datesLoading = ref(false)
const activeTab = ref('indicators')
const indicators = ref(null)
const balanceSheet = ref(null)
const incomeStatement = ref(null)
const cashflowStatement = ref(null)
const historyData = ref(null)
const reportDates = ref([])

/** 图表实例 */
const chartRef = ref(null)
let chartInstance = null

/** 窗口高度响应式变量 */
const windowHeight = ref(window.innerHeight)

/** 更新窗口高度 */
function updateWindowHeight() {
  windowHeight.value = window.innerHeight
}

/**
 * 表格动态高度：自适应填充到视口底部
 * 扣除：页面padding(40) + 导航条(72) + 配置卡(60) + 指标卡片(80) + tab头(50) + 底部留白(60)
 */
const tableHeight = computed(() => Math.max(300, windowHeight.value - 362))

/**
 * 历史趋势表格高度：需额外扣除图表容器(300)
 */
const historyTableHeight = computed(() => Math.max(200, tableHeight.value - 312))

/** 全局导航栏 */
import AppHeader from '@/components/AppHeader.vue'

/** API 基础地址 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 加载可用报告期列表
 */
async function loadReportDates() {
  try {
    datesLoading.value = true
    const res = await fetch(`${API_BASE}/api/financial/report-dates`)
    const data = await res.json()
    const dates = data.report_dates || []
    // 默认选最新一期
    if (dates.length > 0) {
      config.reportDate = dates[0]
      // 如果还没加载过数据，自动触发一次
      if (!indicators.value) {
        await loadData()
      }
    }
    reportDates.value = dates.map(d => ({
      value: d,
      label: formatDateLabel(d)
    }))
  } catch (e) {
    console.error('获取报告期失败:', e)
  } finally {
    datesLoading.value = false
  }
}

/**
 * 格式化日期显示标签（20260331 → 2026-03-31）
 */
function formatDateLabel(dateStr) {
  if (!dateStr || dateStr.length !== 8) return dateStr
  return `${dateStr.slice(0,4)}-${dateStr.slice(4,6)}-${dateStr.slice(6)}`
}

/**
 * 统一加载所有财务数据
 */
async function loadData() {
  if (!config.code.trim()) return
  loading.value = true
  try {
    const params = `code=${encodeURIComponent(config.code)}${config.reportDate ? '&report_date=' + config.reportDate : ''}`
    /* 并行请求各模块数据 */
    const [indiRes, balRes, incRes, cfRes, histRes] = await Promise.allSettled([
      fetch(`${API_BASE}/api/financial/indicators?${params}`),
      fetch(`${API_BASE}/api/financial/balance-sheet?${params}`),
      fetch(`${API_BASE}/api/financial/income?${params}`),
      fetch(`${API_BASE}/api/financial/cashflow?${params}`),
      fetch(`${API_BASE}/api/financial/history?code=${encodeURIComponent(config.code)}&limit=8`)
    ])

    if (indiRes.status === 'fulfilled') {
      indicators.value = await indiRes.value.json()
    }
    if (balRes.status === 'fulfilled') {
      balanceSheet.value = await balRes.value.json()
    }
    if (incRes.status === 'fulfilled') {
      incomeStatement.value = await incRes.value.json()
    }
    if (cfRes.status === 'fulfilled') {
      cashflowStatement.value = await cfRes.value.json()
    }
    if (histRes.status === 'fulfilled') {
      historyData.value = await histRes.value.json()
    }

    /* 渲染当前激活 tab 的图表 */
    await nextTick()
    renderChart()
  } catch (e) {
    console.error('加载数据失败:', e)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * Tab 切换回调，重新渲染图表
 */
function onTabChange(tab) {
  if (tab === 'history') {
    nextTick(() => renderChart())
  }
}

/* ==================== 核心指标卡片配置 ==================== */

/** 指标卡片的定义列表（字段名对应后端返回的中文名称） */
const metricCards = computed(() => [
  { label: '每股收益(元)', field: '基本每股收益', subField: null, colorClass: '' },
  { label: '每股净资产(元)', field: '每股净资产', subField: null, colorClass: '' },
  { label: 'ROE(%)', field: '净资产收益率', subField: null, colorClass: '' },
  { label: '净利润增长率(%)', field: '净利润增长率(%)', subField: null, colorClass: 'price-up' },
  { label: '营收增长率(%)', field: '营业收入增长率(%)', subField: null, colorClass: '' },
  { label: '毛利率(%)', field: '销售毛利率(%)(非金融类指标)', subField: null, colorClass: '' },
])

/**
 * 将原始值格式化为可读字符串
 */
function formatValue(val) {
  if (val == null || val === '') return '-'
  if (typeof val === 'number') {
    if (Math.abs(val) >= 1e8) return (val / 1e8).toFixed(2) + '亿'
    if (Math.abs(val) >= 1e4) return (val / 1e4).toFixed(2) + '万'
    return val.toFixed(2)
  }
  return String(val)
}

/**
 * 格式化变化率
 */
function formatChange(val) {
  if (val == null || val === '') return '-'
  const num = Number(val)
  if (isNaN(num)) return '-'
  return (num >= 0 ? '+' : '') + num.toFixed(2) + '%'
}

/**
 * 数字格式化（万元级别）
 */
function formatNumber(val) {
  if (val == null || val === '') return '-'
  const num = Number(val)
  if (isNaN(num)) return '-'
  if (Math.abs(num) >= 1e8) return (num / 1e8).toFixed(2) + '亿'
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

/* ==================== 表格行数据计算 ==================== */

/** 财务指标详情行（动态生成，基于后端实际返回字段） */
const indicatorRows = computed(() => {
  if (!indicators.value?.indicators) return []
  const d = indicators.value.indicators
  // 字段名映射：后端中文名 → 显示名 + 说明
  const fieldMap = {
    '基本每股收益': { unit: '元', desc: '归属母公司股东净利润 / 总股本' },
    '扣除非经常性损益每股收益': { unit: '元', desc: '扣非后每股收益' },
    '每股未分配利润': { unit: '元', desc: '每股未分配利润' },
    '每股净资产': { unit: '元', desc: '归母净资产 / 总股本' },
    '每股资本公积金': { unit: '元', desc: '每股资本公积' },
    '净资产收益率': { unit: '%', desc: '净利润 / 平均净资产' },
    '每股经营现金流量': { unit: '元', desc: '经营现金流 / 总股本' },
    '营业收入增长率(%)': { unit: '%', desc: '营业收入同比增长率' },
    '净利润增长率(%)': { unit: '%', desc: '与上年同期相比的变化率' },
    '净资产增长率(%)': { unit: '%', desc: '净资产同比增长率' },
    '总资产增长率(%)': { unit: '%', desc: '总资产同比增长率' },
    '营业利润增长率(%)': { unit: '%', desc: '营业利润同比增长率' },
    '销售毛利率(%)(非金融类指标)': { unit: '%', desc: '(营收 - 成本) / 营收' },
    '销售净利率(%)': { unit: '%', desc: '净利润 / 营收' },
    '资产负债率(%)': { unit: '%', desc: '负债总额 / 总资产' },
    '流动比率(非金融类指标)': { unit: '', desc: '流动资产 / 流动负债' },
    '速动比率(非金融类指标)': { unit: '', desc: '(流动资产-存货)/流动负债' },
    '权益乘数(%)': { unit: '%', desc: '1 / (1 - 资产负债率)' },
  }
  return Object.entries(d)
    .filter(([, val]) => val != null)
    .map(([key, val]) => ({
      name: key,
      value: val,
      unit: fieldMap[key]?.unit || '',
      formatted: typeof val === 'number' ? (key.includes('率') || key.includes('%') ? val.toFixed(2) + '%' : formatValue(val)) : String(val),
      desc: fieldMap[key]?.desc || ''
    }))
})

/** 资产负债表行（动态生成） */
const balanceRows = computed(() => {
  if (!balanceSheet.value?.balance_sheet) return []
  const d = balanceSheet.value.balance_sheet
  const totalAssets = d['资产总计'] || 1
  const rows = Object.entries(d).filter(([, val]) => val != null)
    .map(([name, value]) => ({
      name,
      value,
      ratio: totalAssets && value ? (Number(value) / Number(totalAssets) * 100).toFixed(1) : '-'
    }))
  // 排序：资产类在前，负债/权益在后
  const order = ['货币资金', '应收账款', '存货', '流动资产合计', '固定资产', '无形资产',
    '商誉', '非流动资产合计', '资产总计', '短期借款', '应付账款', '流动负债合计',
    '长期借款', '非流动负债合计', '负债合计', '实收资本（或股本）', '资本公积',
    '盈余公积', '未分配利润', '所有者权益（或股东权益）合计']
  return rows.sort((a, b) => (order.indexOf(a.name) - order.indexOf(b.name)) || 0)
})

/** 利润表行（动态生成） */
const incomeRows = computed(() => {
  if (!incomeStatement.value?.income_statement) return []
  const d = incomeStatement.value.income_statement
  return Object.entries(d)
    .filter(([, val]) => val != null)
    .map(([name, value]) => ({ name, value, yoy: null }))
})

/** 现金流量表行（动态生成） */
const cashflowRows = computed(() => {
  if (!cashflowStatement.value?.cashflow) return []
  const d = cashflowStatement.value.cashflow
  const noteMap = {
    '经营活动现金流入小计': '经营相关现金收入合计',
    '经营活动现金流出小计': '经营相关现金支出合计',
    '经营活动产生的现金流量净额': '企业核心造血能力',
    '投资活动现金流入小计': '投资相关现金收入',
    '投资活动现金流出小计': '购建/处置长期资产的支出',
    '投资活动产生的现金流量净额': '投资活动净现金流',
    '筹资活动现金流入小计': '融资相关现金收入',
    '筹资活动现金流出小计': '融资、分红等支出',
    '筹资活动产生的现金流量净额': '筹资活动净现金流',
    '现金及现金等价物净增加额': '三项活动汇总',
    '期初现金及现金等价物余额': '期初余额',
    '期末现金及现金等价物余额': '期末余额',
    '销售商品、提供劳务收到的现金': '主营业务回款',
    '购买商品、接受劳务支付的现金': '采购支付',
  }
  return Object.entries(d)
    .filter(([, val]) => val != null)
    .map(([name, value]) => ({ name, value, note: noteMap[name] || '' }))
})

/** 历史趋势列定义（后端返回 fields + history） */
const historyColumns = computed(() => {
  if (!historyData.value?.fields || !historyData.value?.history) return []
  // 取第一条记录的所有字段（排除 report_date）作为列
  const firstRow = historyData.value.history[0] || {}
  return Object.keys(firstRow)
    .filter(k => k !== 'report_date')
    .map(key => ({ prop: key, label: key }))
})

/** 历史趋势表格行 */
const historyRows = computed(() => historyData.value?.history || [])

/* ==================== ECharts 图表渲染 ==================== */

/**
 * 渲染历史趋势图表
 */
function renderChart() {
  if (activeTab.value !== 'history' || !historyData.value?.history?.length || !chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const rows = historyData.value.history.slice().reverse() /* 时间正序 */
  const colDefs = historyColumns.value

  const categories = rows.map(r => r.report_date)

  /* 取前5个关键指标绘制折线图 */
  const series = colDefs.slice(0, 5).map(col => ({
    name: col.label,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    data: rows.map(r => r[col.prop] == null ? null : Number(r[col.prop])),
    lineStyle: { width: 2 }
  }))

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(36, 41, 49, 0.95)',
      borderColor: '#30363d',
      textStyle: { color: '#c9cdd4', fontSize: 12 }
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#8b949e', fontSize: 11 },
      itemWidth: 16,
      itemHeight: 3
    },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: '#30363d' } },
      axisLabel: { color: '#6e7681', fontSize: 10, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } },
      axisLabel: { color: '#6e7681', fontSize: 10 }
    },
    series,
  }, true)
}

/** 窗口 resize 时重绘图表 */
function handleResize() {
  chartInstance?.resize()
}

/* ==================== 生命周期 ==================== */
onMounted(() => {
  loadReportDates()
  window.addEventListener('resize', handleResize)
  window.addEventListener('resize', updateWindowHeight)
})

onUnmounted(() => {
  chartInstance?.dispose()
  chartInstance = null
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('resize', updateWindowHeight)
})
</script>

<style scoped>
.finance-page {
  min-height: 100vh;
  padding: 16px 20px;
  max-width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

/* ===== 导航栏：简洁文字行（无卡片背景） ===== */
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: linear-gradient(180deg, #1e2535 0%, #151c2e 100%);
  border: 1px solid #2a3348;
  border-radius: 8px;
  color: #8b949e;
  text-decoration: none;
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

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #c9cdd4);
}

/* ===== 配置区 ===== */
.config-card { margin-bottom: 16px; }

/* ===== 指标卡片网格 ===== */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-top: 16px;
}
.metric-card {
  padding: 16px !important;
  text-align: center;
}
.metric-label {
  font-size: 12px;
  color: var(--text-muted, #6e7681);
  margin-bottom: 8px;
}
.metric-value {
  font-family: var(--font-mono, monospace);
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary, #c9cdd4);
  margin-bottom: 4px;
}
.metric-sub {
  font-size: 11px;
  color: var(--text-secondary, #8b949e);
}

/* ===== Tab 内容区 ===== */
.tab-content {
  min-height: 300px;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
}
.history-section {
  position: relative;
  display: flex;
  flex-direction: column;
}

/* 表格滚动容器 - 统一所有 tab 的表格展示 */
.table-scroll-wrapper {
  width: 100%;
  overflow-x: auto;
  flex: 1;
}

.chart-container {
  width: 100%;
  height: 280px;
  flex-shrink: 0;
  margin-bottom: 12px;
}

/* ===== 价格颜色 ===== */
.price-up { color: var(--color-up, #f85149) !important; font-weight: 500; }
.price-down { color: var(--color-down, #3fb950) !important; font-weight: 500; }

/* Element Plus 暗色覆盖 */
:deep(.el-card) { background: var(--bg-card); border-color: var(--border-default); }
:deep(.el-card__header) { padding: 12px 16px; border-bottom: 1px solid var(--border-default); }
:deep(.el-card .el-card__body) { padding: 8px !important; }
:deep(.el-tabs__nav-wrap::after) { background-color: var(--border-default); }
:deep(.el-tabs__item) { color: var(--text-secondary, #8b949e); }
:deep(.el-tabs__item.is-active) { color: #58a6ff; }
:deep(.el-tabs__active-bar) { background-color: #58a6ff; }
:deep(.el-table th.el-table__cell) { background-color: var(--bg-tertiary, #2d333b) !important; }
:deep(.el-table .cell) { padding: 4px 8px; }
</style>
