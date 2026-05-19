<template>
  <div class="home-page">
    <!-- 系统状态卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="card stat-card">
          <div class="stat-value">{{ systemInfo.version || '3.0.0' }}</div>
          <div class="stat-label">系统版本</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="card stat-card">
          <div class="stat-value">{{ systemInfo.cacheInfo?.file_count || 0 }}</div>
          <div class="stat-label">缓存文件数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="card stat-card">
          <div class="stat-value">{{ systemInfo.cacheInfo?.total_size_mb || 0 }} MB</div>
          <div class="stat-label">缓存大小</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="card stat-card">
          <div class="stat-value" :class="healthStatusClass">
            {{ healthInfo.status || 'checking' }}
          </div>
          <div class="stat-label">系统状态</div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据源状态 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">数据源状态</span>
            <el-button type="primary" link @click="loadDatasources">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div v-if="datasources.length > 0">
            <el-tag
              v-for="ds in datasources"
              :key="ds.name"
              :type="ds.available ? 'success' : 'danger'"
              class="ds-tag"
            >
              {{ ds.name }}: {{ ds.available ? '在线' : '离线' }}
            </el-tag>
          </div>
          <el-skeleton v-else :rows="2" />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">快速操作</span>
          </div>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/stock')">
              <el-icon><TrendCharts /></el-icon>
              查看行情
            </el-button>
            <el-button type="success" @click="$router.push('/backtest')">
              <el-icon><DataAnalysis /></el-icon>
              策略回测
            </el-button>
            <el-button type="warning" @click="$router.push('/predict')">
              <el-icon><MagicStick /></el-icon>
              趋势预测
            </el-button>
            <el-button @click="clearCache">
              <el-icon><Delete /></el-icon>
              清空缓存
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 最新回测结果 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">最近回测</span>
        <el-button type="primary" link @click="$router.push('/backtest')">
          查看更多
        </el-button>
      </div>
      <el-table :data="backtestHistory" stripe v-loading="loadingHistory">
        <el-table-column prop="strategy_name" label="策略" width="120" />
        <el-table-column prop="stock_code" label="股票" width="100" />
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column label="总收益率" width="100">
          <template #default="{ row }">
            <span :class="row.total_return >= 0 ? 'price-up' : 'price-down'">
              {{ (row.total_return * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="年化收益率" width="100">
          <template #default="{ row }">
            <span :class="row.annualized_return >= 0 ? 'price-up' : 'price-down'">
              {{ (row.annualized_return * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="max_drawdown" label="最大回撤" width="100">
          <template #default="{ row }">
            {{ (row.max_drawdown * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column prop="win_rate" label="胜率" width="100">
          <template #default="{ row }">
            {{ (row.win_rate * 100).toFixed(2) }}%
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loadingHistory && backtestHistory.length === 0" description="暂无回测记录" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi, backtestApi } from '@/api'

const systemInfo = ref({})
const healthInfo = ref({})
const datasources = ref([])
const backtestHistory = ref([])
const loadingHistory = ref(false)

const healthStatusClass = computed(() => {
  const status = healthInfo.value?.status
  if (status === 'healthy') return 'stat-up'
  if (status === 'degraded') return 'stat-down'
  return ''
})

const loadSystemInfo = async () => {
  try {
    const res = await systemApi.getInfo()
    systemInfo.value = res
    systemInfo.value.cacheInfo = {
      file_count: res.cache_info?.file_count || 0,
      total_size_mb: res.cache_info?.total_size_mb || 0
    }
  } catch (e) {
    console.error('加载系统信息失败:', e)
  }
}

const loadHealthInfo = async () => {
  try {
    healthInfo.value = await systemApi.healthCheck()
  } catch (e) {
    healthInfo.value = { status: 'error' }
  }
}

const loadDatasources = async () => {
  try {
    const res = await systemApi.getDatasources()
    datasources.value = Object.entries(res.sources || {}).map(([name, info]) => ({
      name,
      ...info
    }))
  } catch (e) {
    console.error('加载数据源失败:', e)
  }
}

const loadBacktestHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await backtestApi.getHistory(5)
    backtestHistory.value = res.records || []
  } catch (e) {
    console.error('加载回测历史失败:', e)
  } finally {
    loadingHistory.value = false
  }
}

const clearCache = async () => {
  try {
    await systemApi.clearCache()
    ElMessage.success('缓存已清空')
    loadSystemInfo()
  } catch (e) {
    ElMessage.error('清空缓存失败')
  }
}

onMounted(() => {
  loadSystemInfo()
  loadHealthInfo()
  loadDatasources()
  loadBacktestHistory()
})
</script>

<style scoped>
.home-page {
  max-width: 1400px;
  margin: 0 auto;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  padding: 24px;
}

.mb-16 {
  margin-bottom: 16px;
}

.ds-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
