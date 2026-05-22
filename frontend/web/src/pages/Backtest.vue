<template>
  <div class="backtest-page">
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
        <span class="page-title">策略回测</span>
      </div>
    </div>

    <!-- 回测配置 -->
    <el-card class="config-card">
      <el-form :model="config" inline>
        <el-form-item label="股票代码">
          <el-input v-model="config.code" placeholder="如: 600000" style="width: 120px" />
        </el-form-item>
        <el-form-item label="策略">
          <el-select v-model="config.strategy" style="width: 180px">
            <el-option
              v-for="s in strategies"
              :key="s.name"
              :label="formatStrategyName(s.name)"
              :value="s.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number v-model="config.initialCash" :min="10000" :step="10000" style="width: 140px" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="config.startDate" type="date" style="width: 140px" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="config.endDate" type="date" style="width: 140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runBacktest" :loading="running">
            <el-icon><VideoPlay /></el-icon>
            运行回测
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 回测结果 -->
    <div v-if="result">
      <el-row :gutter="16" class="result-stats">
        <el-col :span="6">
          <div class="card stat-card">
            <div :class="['stat-value', result.total_return >= 0 ? 'stat-up' : 'stat-down']">
              {{ (result.total_return * 100).toFixed(2) }}%
            </div>
            <div class="stat-label">总收益率</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div :class="['card', 'stat-card', result.annualized_return >= 0 ? 'stat-up' : 'stat-down']">
            <div class="stat-value">{{ (result.annualized_return * 100).toFixed(2) }}%</div>
            <div class="stat-label">年化收益率</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="card stat-card">
            <div class="stat-value">{{ (result.max_drawdown * 100).toFixed(2) }}%</div>
            <div class="stat-label">最大回撤</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="card stat-card">
            <div class="stat-value">{{ result.sharpe_ratio.toFixed(2) }}</div>
            <div class="stat-label">夏普比率</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="mb-16">
        <el-col :span="12">
          <div class="card">
            <div class="card-header"><span class="card-title">交易统计</span></div>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总交易次数">{{ result.total_trades }}</el-descriptions-item>
              <el-descriptions-item label="盈利次数">{{ result.winning_trades }}</el-descriptions-item>
              <el-descriptions-item label="亏损次数">{{ result.losing_trades }}</el-descriptions-item>
              <el-descriptions-item label="胜率">{{ (result.win_rate * 100).toFixed(2) }}%</el-descriptions-item>
              <el-descriptions-item label="平均盈利">{{ result.avg_profit.toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="平均亏损">{{ result.avg_loss.toFixed(2) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <div class="card-header"><span class="card-title">权益曲线</span></div>
            <div ref="equityChartRef" class="equity-chart"></div>
          </div>
        </el-col>
      </el-row>

      <!-- 交易明细 -->
      <el-card v-if="result.trades?.length" class="mb-16">
        <template #header>
          <div class="card-header">
            <span class="card-title">交易明细</span>
            <span class="card-subtitle">共 {{ result.trades.length }} 笔交易</span>
          </div>
        </template>
        <el-table :data="result.trades" stripe size="small" max-height="300">
          <el-table-column prop="date" label="日期" width="110" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-tag :type="row.action === 'buy' ? 'success' : 'danger'" size="small">
                {{ row.action === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="价格" width="100" align="right">
            <template #default="{ row }">
              {{ row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100" align="right" />
          <el-table-column label="金额" width="120" align="right">
            <template #default="{ row }">
              {{ row.amount.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="手续费" width="100" align="right">
            <template #default="{ row }">
              {{ row.commission.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="滑点" width="100" align="right">
            <template #default="{ row }">
              {{ row.slippage.toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 历史回测 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">回测历史</span>
        </div>
      </template>
      <el-table :data="history" stripe>
        <el-table-column label="策略" width="140">
          <template #default="{ row }">
            {{ formatStrategyName(row.strategy_name) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock_code" label="股票" width="100" />
        <el-table-column label="收益率" width="100">
          <template #default="{ row }">
            <span :class="row.total_return >= 0 ? 'price-up' : 'price-down'">
              {{ (row.total_return * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_trades" label="交易次数" width="100" />
        <el-table-column prop="win_rate" label="胜率" width="100">
          <template #default="{ row }">
            {{ (row.win_rate * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="回测时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { backtestApi } from '@/api'
import dayjs from 'dayjs'
import AppHeader from '@/components/AppHeader.vue'

const strategies = ref([])
const config = ref({
  code: '600000',
  strategy: 'ma_cross',
  initialCash: 100000,
  startDate: dayjs().subtract(1, 'year').toDate(),
  endDate: new Date()
})
const result = ref(null)
const history = ref([])
const running = ref(false)
const equityChartRef = ref(null)
let equityChart = null

// 策略名称映射（中文+英文）
const strategyNameMap = {
  'ma_cross': '均线交叉 (MA)',
  'MACrossStrategy': '均线交叉 (MA)',
  'rsi': 'RSI超买超卖 (RSI)',
  'RSIStrategy': 'RSI超买超卖 (RSI)',
  'macd': 'MACD指标 (MACD)',
  'MACDStrategy': 'MACD指标 (MACD)',
  'bollinger': '布林带 (BOLL)',
  'BollingerStrategy': '布林带 (BOLL)'
}

/** 格式化策略名称为中文+英文 */
const formatStrategyName = (name) => {
  return strategyNameMap[name] || name
}

const loadStrategies = async () => {
  try {
    const res = await backtestApi.getStrategies()
    strategies.value = res.strategies || []
  } catch (e) {
    console.error('加载策略列表失败:', e)
  }
}

const loadHistory = async () => {
  try {
    const res = await backtestApi.getHistory({ limit: 10 })
    history.value = res.records || []
  } catch (e) {
    console.error('加载历史失败:', e)
  }
}

const runBacktest = async () => {
  if (!config.value.code) {
    ElMessage.warning('请输入股票代码')
    return
  }

  running.value = true
  try {
    const res = await backtestApi.run({
      code: config.value.code,
      strategy_name: config.value.strategy,
      start_date: dayjs(config.value.startDate).format('YYYY-MM-DD'),
      end_date: dayjs(config.value.endDate).format('YYYY-MM-DD'),
      initial_cash: config.value.initialCash
    })
    // 保存完整响应，包含 result、trades、equity_curve
    result.value = { ...res.result, trades: res.trades, equity_curve: res.equity_curve }
    ElMessage.success('回测完成')
    loadHistory()
    nextTick(() => updateEquityChart())
  } catch (e) {
    ElMessage.error('回测失败: ' + (e.message || '未知错误'))
  } finally {
    running.value = false
  }
}

const updateEquityChart = () => {
  // 权益曲线数据在 result.equity_curve（已在runBacktest中合并）
  if (!equityChartRef.value || !result.value?.equity_curve?.length) return

  if (!equityChart) {
    equityChart = echarts.init(equityChartRef.value)
  }

  const data = result.value.equity_curve
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: '总权益',
      type: 'line',
      data: data.map(d => d.total_value),
      smooth: true,
      areaStyle: { opacity: 0.3 }
    }]
  }

  equityChart.setOption(option)
}

onMounted(() => {
  loadStrategies()
  loadHistory()
})

onUnmounted(() => {
  if (equityChart) {
    equityChart.dispose()
  }
})
</script>

<style scoped>
.backtest-page {
  min-height: 100vh;
  padding: 16px 20px;
  box-sizing: border-box;
  max-width: 100%;
  overflow-y: auto;
  overflow-y: auto;
}

/* ============ 页面顶部导航 ============ */
/* ===== 页面顶部导航：简洁文字行 ===== */
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

/* ============ 表格深色主题（已由App.vue全局统一处理） ============ */
.config-card {
  margin-bottom: 16px;
}

.result-stats {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.mb-16 {
  margin-bottom: 16px;
}

.equity-chart {
  height: 250px;
}
</style>
