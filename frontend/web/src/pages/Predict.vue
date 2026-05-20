<template>
  <div class="predict-page">
    <!-- 预测配置 -->
    <el-card class="config-card">
      <el-form :model="config" inline>
        <el-form-item label="股票代码">
          <el-input v-model="config.code" placeholder="如: 600000" style="width: 120px" />
        </el-form-item>
        <el-form-item label="预测模型">
          <el-select v-model="config.modelType" style="width: 150px">
            <el-option label="随机森林 (RF)" value="rf" />
            <el-option label="梯度提升 (GB)" value="gb" />
            <el-option label="LSTM+LightGBM 混合模型" value="hybrid" />
          </el-select>
        </el-form-item>
        <!-- 混合模型：选择已保存的模型 -->
        <el-form-item v-if="config.modelType === 'hybrid'" label="已保存模型">
          <el-select v-model="config.selectedModel" filterable placeholder="选择要使用的模型" style="width: 280px">
            <el-option 
              v-for="m in filteredSavedModels" 
              :key="m.name" 
              :label="m.name" 
              :value="m.name"
            >
              <span>{{ m.name }}</span>
              <span style="float:right;color:#999;font-size:12px">
                {{ m.files?.lstm === 'True' ? 'LSTM' : '' }} 
                {{ m.files?.lightgbm === 'True' ? 'LightGBM' : '' }}
              </span>
            </el-option>
          </el-select>
          <el-button size="small" @click="loadSavedModels" style="margin-left:8px">刷新</el-button>
          <div v-if="config.code && filteredSavedModels.length === 0" style="color:#e6a23c;font-size:12px;margin-top:4px">
            暂无股票 {{ config.code }} 的已保存模型，请先到训练页面训练
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runPredict" :loading="loading">
            <el-icon><MagicStick /></el-icon>
            开始预测
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预测结果 -->
    <div v-if="prediction">
      <el-row :gutter="16" class="mb-16">
        <el-col :span="8">
          <el-card class="result-card">
            <div class="result-header">
              <el-icon :size="40" :color="prediction.signal === 'BUY' ? '#67c23a' : prediction.signal === 'SELL' ? '#f56c6c' : '#909399'">
                <TrendCharts />
              </el-icon>
            </div>
            <div class="result-signal" :class="prediction.signal === 'BUY' ? 'signal-buy' : prediction.signal === 'SELL' ? 'signal-sell' : 'signal-hold'">
              {{ prediction.signal }}
            </div>
            <div class="result-label">交易信号</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="result-card">
            <div class="result-value">{{ prediction.predicted_direction }}</div>
            <div class="result-label">预测方向</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="result-card">
            <div class="result-value">{{ prediction.confidence }}%</div>
            <div class="result-label">置信度</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="mb-16">
        <template #header>
          <span>预测详情</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="当前价格">
            {{ prediction.current_price }}
          </el-descriptions-item>
          <el-descriptions-item label="预测天数">
            {{ prediction.forecast_days }}
          </el-descriptions-item>
          <el-descriptions-item label="预测价格区间">
            {{ prediction.predicted_price_range?.low }} - {{ prediction.predicted_price_range?.high }}
          </el-descriptions-item>
          <el-descriptions-item label="模型准确率">
            {{ prediction.model_accuracy ? prediction.model_accuracy.toFixed(1) + '%' : '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <!-- 历史预测 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">预测历史</span>
        </div>
      </template>
      <el-table :data="history" stripe v-loading="loadingHistory">
        <el-table-column prop="code" label="股票" width="85" />
        <el-table-column prop="date" label="目标日期" width="105" />
        <el-table-column label="T+N" width="55">
          <template #default="{ row }">
            {{ getForecastDay(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型" width="135">
          <template #default="{ row }">
            {{ formatModelName(row.model_name) }}
          </template>
        </el-table-column>
        <el-table-column label="预测价格" width="90">
          <template #default="{ row }">
            {{ row.predicted_price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="实际价格" width="90">
          <template #default="{ row }">
            {{ row.actual_price != null ? row.actual_price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="方向" width="70">
          <template #default="{ row }">
            <el-tag :type="row.predicted_direction === '上涨' ? 'success' : row.predicted_direction === '下跌' ? 'danger' : 'info'" size="small">
              {{ row.predicted_direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="75">
          <template #default="{ row }">
            {{ row.confidence?.toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column label="准确率" width="80">
          <template #default="{ row }">
            <!-- 注意：0.0 是 falsy，必须用 null/undefined 判断 -->
            <span :class="row.accuracy === 100 ? 'accuracy-hit' : row.accuracy === 0 && row.accuracy !== null ? 'accuracy-miss' : ''">
              {{ row.accuracy != null ? row.accuracy.toFixed(0) + '%' : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="回填日期" width="105">
          <template #default="{ row }">
            {{ row.updated_at ? row.updated_at.substring(0, 10) : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import { predictApi } from '@/api/predict'

const router = useRouter()
const route = useRoute()

const config = ref({
  code: '600000',
  modelType: 'rf',
  selectedModel: ''
})
const prediction = ref(null)
const history = ref([])
const loading = ref(false)
const loadingHistory = ref(false)
const savedModels = ref([])

/** 根据当前股票代码过滤模型列表 */
const filteredSavedModels = computed(() => {
  if (!config.value.code) return savedModels.value
  return savedModels.value.filter(m => m.name.startsWith(config.value.code + '_'))
})

/** 股票代码变化时清空不匹配的已选模型 */
watch(() => config.value.code, (newCode) => {
  if (config.value.selectedModel && !config.value.selectedModel.startsWith(newCode + '_')) {
    config.value.selectedModel = ''
  }
})

/** 模型名称映射 */
const modelNameMap = {
  'rf_model': '随机森林 (RF)',
  'rf': '随机森林 (RF)',
  'gb_model': '梯度提升 (GB)',
  'gb': '梯度提升 (GB)',
  'hybrid_model': 'LSTM+LightGBM 混合模型',
  'hybrid': 'LSTM+LightGBM 混合模型'
}

/** 格式化模型名称 */
const formatModelName = (name) => {
  return modelNameMap[name] || name
}

/**
 * 计算预测目标是第几个交易日（T+N）
 */
const getForecastDay = (row) => {
  if (!row.created_at || !row.date) return '-'
  const created = new Date(row.created_at)
  const target = new Date(row.date)
  // 计算工作日差（简化：排除周末的日历日差）
  let diff = Math.ceil((target - created) / (1000 * 60 * 60 * 24))
  if (diff <= 0) return 'T+0'
  // 粗略估算工作日（跳过周末，约 5/7 比例）
  const weekdays = Math.round(diff * 5 / 7) || 1
  return `T+${weekdays}`
}

/**
 * 执行预测（根据模型类型调用不同 API）
 */
const runPredict = async () => {
  if (!config.value.code) {
    ElMessage.warning('请输入股票代码')
    return
  }

  // 混合模型需要选择已保存的模型
  if (config.value.modelType === 'hybrid' && !config.value.selectedModel) {
    ElMessage.warning('请先选择一个已保存的混合模型')
    return
  }

  loading.value = true
  try {
    if (config.value.modelType === 'hybrid') {
      // 调用混合模型预测接口
      const res = await predictApi.hybridPredict({
        code: config.value.code,
        model_name: config.value.selectedModel
      })
      prediction.value = res
      ElMessage.success('混合模型预测完成')
    } else {
      // 调用传统模型预测接口
      const res = await predictApi.predict(config.value.code, 5, config.value.modelType)
      prediction.value = res
      ElMessage.success('预测完成')
    }
    loadHistory()
  } catch (e) {
    const errorMsg = e.response?.data?.detail || e.message || '未知错误'
    ElMessage.error('预测失败: ' + errorMsg.substring(0, 100))
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await predictApi.getHistory(null, 20)
    history.value = res.records || []
  } catch (e) {
    console.error('加载历史失败:', e)
  } finally {
    loadingHistory.value = false
  }
}

/**
 * 加载已保存的混合模型列表
 */
const loadSavedModels = async () => {
  try {
    const response = await predictApi.getSavedModels()
    savedModels.value = response.models || []
  } catch (e) {
    console.error('加载模型列表失败:', e)
  }
}

onMounted(() => {
  loadHistory()

  // 读取从训练页面跳转过来的参数
  if (route.query.code) {
    config.value.code = route.query.code
  }
  if (route.query.model === 'hybrid') {
    config.value.modelType = 'hybrid'
    // 加载模型列表
    loadSavedModels().then(() => {
      // 优先使用传入的modelName参数
      const targetModel = route.query.modelName
      if (targetModel && savedModels.value.some(m => m.name === targetModel)) {
        config.value.selectedModel = targetModel
      } else if (savedModels.value.length > 0) {
        // 否则匹配当前股票代码的最新模型
        const matchedModel = savedModels.value
          .filter(m => m.name.startsWith(route.query.code))
          .pop() || savedModels.value[savedModels.value.length - 1]
        if (matchedModel) {
          config.value.selectedModel = matchedModel.name
        }
      }
    })
  }
})
</script>

<style scoped>
.predict-page {
  max-width: 1200px;
  margin: 0 auto;
}

.config-card {
  margin-bottom: 16px;
}

.mb-16 {
  margin-bottom: 16px;
}

.result-card {
  text-align: center;
  padding: 24px;
}

.result-header {
  margin-bottom: 12px;
}

.result-signal {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.result-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.result-label {
  font-size: 14px;
  color: #999;
}

.signal-buy {
  color: #67c23a;
}

.signal-sell {
  color: #f56c6c;
}

.signal-hold {
  color: #909399;
}

/* 准确率命中/未命中样式 */
.accuracy-hit {
  color: #67c23a;
  font-weight: bold;
}
.accuracy-miss {
  color: #f56c6c;
  font-weight: bold;
}
</style>
