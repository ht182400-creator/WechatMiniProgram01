<template>
  <div class="predict-page">
    <!-- 预测配置 -->
    <el-card class="config-card">
      <el-form :model="config" inline>
        <el-form-item label="股票代码">
          <el-input v-model="config.code" placeholder="如: 600000" style="width: 120px" />
        </el-form-item>
        <el-form-item label="预测模型">
          <el-select v-model="config.modelType" style="width: 120px">
            <el-option label="随机森林" value="rf" />
            <el-option label="梯度提升" value="gb" />
          </el-select>
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
            {{ prediction.prediction_days }}
          </el-descriptions-item>
          <el-descriptions-item label="预测价格区间">
            {{ prediction.predicted_price_range?.low }} - {{ prediction.predicted_price_range?.high }}
          </el-descriptions-item>
          <el-descriptions-item label="模型准确率">
            {{ prediction.model_accuracy }}%
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
        <el-table-column prop="code" label="股票" width="100" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="model_name" label="模型" width="100" />
        <el-table-column label="当前价格" width="100">
          <template #default="{ row }">
            {{ row.current_price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="预测方向" width="100">
          <template #default="{ row }">
            <el-tag :type="row.predicted_direction === '上涨' ? 'success' : row.predicted_direction === '下跌' ? 'danger' : 'info'">
              {{ row.predicted_direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            {{ row.confidence?.toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column label="准确率" width="100">
          <template #default="{ row }">
            {{ row.accuracy ? row.accuracy.toFixed(1) + '%' : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { predictApi } from '@/api'

const config = ref({
  code: '600000',
  modelType: 'rf'
})
const prediction = ref(null)
const history = ref([])
const loading = ref(false)
const loadingHistory = ref(false)

const runPredict = async () => {
  if (!config.value.code) {
    ElMessage.warning('请输入股票代码')
    return
  }

  loading.value = true
  try {
    const res = await predictApi.predict(config.value.code, 5, config.value.modelType)
    prediction.value = res
    ElMessage.success('预测完成')
    loadHistory()
  } catch (e) {
    ElMessage.error('预测失败: ' + (e.message || '未知错误'))
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

onMounted(() => {
  loadHistory()
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
</style>
