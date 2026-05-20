<template>
  <div class="train-page">
    <!-- 参数配置 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">模型训练参数配置</span>
          <el-tag type="info">LSTM + LightGBM 混合模型</el-tag>
        </div>
      </template>
      
      <el-form :model="form" label-width="130px" class="param-form">
        <el-row :gutter="24">
          <!-- 基础配置 -->
          <el-col :span="12">
            <el-divider content-position="left"><span class="section-title">基础配置</span></el-divider>
            
            <el-form-item label="股票代码">
              <el-input v-model="form.code" placeholder="如: 600000">
                <template #append>
                  <el-button @click="loadStockInfo">检测</el-button>
                </template>
              </el-input>
              <div class="param-desc">目标股票的 A 股代码（6位数字），如：600000 浦发银行、000001 平安银行</div>
            </el-form-item>
            
            <el-form-item label="数据开始日期">
              <el-date-picker 
                v-model="form.startDate" 
                type="date" 
                placeholder="选择日期"
                style="width: 100%"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
              <div class="param-desc">训练数据的起始日期。越早的数据量越多，模型学习更充分，但早期数据可能相关性较低</div>
            </el-form-item>
            
            <el-form-item label="数据结束日期">
              <el-date-picker 
                v-model="form.endDate" 
                type="date" 
                placeholder="选择日期"
                style="width: 100%"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
              <div class="param-desc">训练数据的截止日期。默认为今天，留出最近部分作为验证/测试</div>
            </el-form-item>
            
            <el-form-item label="预测周期(天)">
              <el-slider v-model="form.forecastDays" :min="1" :max="30" show-input />
              <div class="param-desc">模型要预测的未来天数范围。短周期(3-5天)准确率更高；长周期(>10天)不确定性增大</div>
            </el-form-item>
          </el-col>
          
          <!-- LSTM 配置 -->
          <el-col :span="12">
            <el-divider content-position="left"><span class="section-title">LSTM 参数</span></el-divider>
            
            <el-form-item label="回看窗口">
              <el-slider v-model="form.seqLength" :min="5" :max="60" show-input />
              <div class="param-desc">LSTM 输入的历史交易日数量。<b>推荐 10-30 天</b>。太小则信息不足导致欠拟合，过大则引入噪声</div>
            </el-form-item>
            
            <el-form-item label="隐藏层大小">
              <el-slider v-model="form.lstmHidden" :min="32" :max="512" :step="32" show-input />
              <div class="param-desc">LSTM 神经元数量，控制模型容量。<b>推荐 64-256</b>。数据少用小值(64-128)，数据多用大值(128-256)</div>
            </el-form-item>
            
            <el-form-item label="LSTM 层数">
              <el-slider v-model="form.lstmLayers" :min="1" :max="4" :step="1" show-input />
              <div class="param-desc">堆叠的 LSTM 层数。<b>推荐 1-3 层</b>。层数越多表达能力越强，但也更容易过拟合</div>
            </el-form-item>
            
            <el-form-item label="Dropout">
              <el-slider v-model="form.lstmDropout" :min="0" :max="0.5" :step="0.05" :precision="2" show-input />
              <div class="param-desc">随机失活比例，用于防止过拟合。<b>推荐 0.1-0.3</b>。训练数据少时适当提高(0.3)，数据充足时降低(0.15)</div>
            </el-form-item>
            
            <el-form-item label="训练轮数(Epochs)">
              <el-slider v-model="form.lstmEpochs" :min="10" :max="200" :step="10" show-input />
              <div class="param-desc">完整遍历训练数据的次数。<b>推荐 30-100</b>。配合早停机制使用，过大会过拟合</div>
            </el-form-item>
            
            <el-form-item label="学习率(LR)">
              <el-input-number v-model="form.lstmLr" :min="0.0001" :max="0.01" :step="0.0001" :precision="4" style="width: 100%" />
              <div class="param-desc">权重更新步长。<b>推荐 0.001</b>。太大则训练震荡不收敛，太小则收敛极慢</div>
            </el-form-item>
            
            <el-form-item label="批次大小(BatchSize)">
              <el-slider v-model="form.lstmBatchSize" :min="8" :max="128" :step="8" show-input />
              <div class="param-desc">每批处理的样本数量。<b>推荐 16-64</b>。小批量更新频繁、噪声大但泛化好；大批量稳定但内存消耗高</div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="24">
          <!-- LightGBM 配置 -->
          <el-col :span="12">
            <el-divider content-position="left"><span class="section-title">LightGBM 参数</span></el-divider>
            
            <el-form-item label="树数量(N_Estimators)">
              <el-slider v-model="form.lgbNEstimators" :min="50" :max="500" :step="50" show-input />
              <div class="param-desc">梯度提升树的棵数。<b>推荐 100-300</b>。越多精度越高，但超过一定数量后收益递减且变慢</div>
            </el-form-item>
            
            <el-form-item label="学习率(LearningRate)">
              <el-input-number v-model="form.learningRate" :min="0.001" :max="0.1" :step="0.005" :precision="3" style="width: 100%" />
              <div class="param-desc">每棵树对最终结果的贡献系数。<b>推荐 0.01-0.05</b>。小学习率需要更多树来补偿</div>
            </el-form-item>
          </el-col>
          
          <!-- 训练配置 -->
          <el-col :span="12">
            <el-divider content-position="left"><span class="section-title">训练配置</span></el-divider>
            
            <el-form-item label="验证集比例">
              <el-slider v-model="form.validationSplit" :min="0.1" :max="0.4" :step="0.05" :precision="2" show-input />
              <div class="param-desc">从训练数据中划分多少比例用于验证。<b>推荐 0.2(20%)</b>。验证集越大评估越可靠，但训练样本减少</div>
            </el-form-item>
            
            <el-form-item label="保存模型">
              <el-switch v-model="form.saveModel" />
              <div class="param-desc">开启后训练完成的模型将保存到本地，后续可直接加载使用而无需重新训练</div>
            </el-form-item>
            
            <el-form-item label="自定义名称">
              <el-input v-model="form.modelName" placeholder="可选，如: my_model_001" clearable />
              <div class="param-desc">为保存的模型指定自定义名称，方便管理和识别。留空将自动生成（格式：股票代码_时间戳）</div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 参数预设 -->
        <el-divider content-position="left">参数预设</el-divider>
        <div class="preset-buttons">
          <el-button size="small" @click="applyPreset('fast')">快速训练</el-button>
          <el-button size="small" @click="applyPreset('balanced')">均衡训练</el-button>
          <el-button size="small" @click="applyPreset('accurate')">高精度</el-button>
          <el-button size="small" type="info" @click="showAdvanced = !showAdvanced">
            {{ showAdvanced ? '收起高级选项' : '高级选项' }}
          </el-button>
        </div>
        
        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" size="large" @click="startTraining" :loading="training" :disabled="!form.code">
            <el-icon v-if="!training"><VideoPlay /></el-icon>
            {{ training ? '训练中...' : '开始训练' }}
          </el-button>
          <el-button size="large" @click="startWalkForward" :loading="walkingForward" :disabled="!form.code">
            <el-icon><DataAnalysis /></el-icon>
            Walk-Forward 验证
          </el-button>
          <el-button @click="resetForm">重置参数</el-button>
        </div>
      </el-form>
    </el-card>
    
    <!-- 训练进度 -->
    <el-card v-if="training || progressLogs.length > 0" class="progress-card">
      <template #header>
        <span class="card-title">训练进度</span>
      </template>
      <div class="progress-container">
        <el-progress :percentage="progress" :status="progressStatus" :stroke-width="20" />
        <div class="progress-logs">
          <div v-for="(log, idx) in progressLogs" :key="idx" class="log-item" :class="log.type">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 训练结果 -->
    <div v-if="result">
      <el-divider content-position="left">训练结果</el-divider>
      
      <!-- 评估指标 -->
      <el-row :gutter="16" class="mb-16">
        <el-col :span="8">
          <el-card class="metric-card">
            <div class="metric-value" :class="getMetricClass(result.metrics?.accuracy)">
              {{ result.metrics?.accuracy?.toFixed(1) || 0 }}%
            </div>
            <div class="metric-label">准确率 (Accuracy)</div>
            <div class="metric-desc">预测正确的比例</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="metric-card">
            <div class="metric-value" :class="getMetricClass(result.metrics?.f1)">
              {{ result.metrics?.f1?.toFixed(1) || 0 }}%
            </div>
            <div class="metric-label">F1 分数</div>
            <div class="metric-desc">精确率和召回率的调和平均</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="metric-card">
            <div class="metric-value" :class="getMetricClass(result.metrics?.auc)">
              {{ result.metrics?.auc?.toFixed(1) || 0 }}%
            </div>
            <div class="metric-label">AUC</div>
            <div class="metric-desc">区分能力的度量</div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 其他指标 -->
      <el-card class="mb-16">
        <template #header>
          <span class="card-title">完整评估指标</span>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="准确率">
            {{ result.metrics?.accuracy?.toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="精确率">
            {{ result.metrics?.precision?.toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="召回率">
            {{ result.metrics?.recall?.toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="F1 分数">
            {{ result.metrics?.f1?.toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="AUC">
            {{ result.metrics?.auc?.toFixed(2) }}%
          </el-descriptions-item>
          <el-descriptions-item label="训练耗时">
            {{ result.train_duration_seconds }} 秒
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
      
      <!-- 特征重要性 -->
      <el-card class="mb-16">
        <template #header>
          <span class="card-title">特征重要性排序</span>
        </template>
        <div class="feature-importance">
          <div v-for="(value, key, idx) in result.feature_importance" :key="key" class="feature-item">
            <div class="feature-name">
              <span class="feature-rank">{{ idx + 1 }}</span>
              {{ formatFeatureName(key) }}
            </div>
            <div class="feature-bar-container">
              <el-progress 
                :percentage="(value * 100).toFixed(1)" 
                :stroke-width="16"
                :color="getFeatureColor(idx)"
              />
            </div>
            <span class="feature-value">{{ (value * 100).toFixed(2) }}%</span>
          </div>
        </div>
      </el-card>
      
      <!-- 训练信息 -->
      <el-card class="mb-16">
        <template #header>
          <span class="card-title">训练信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="股票代码">
            <el-tag type="primary">{{ result.code }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="训练日期">
            {{ result.train_date }}
          </el-descriptions-item>
          <el-descriptions-item label="数据周期">
            {{ result.data_period?.start }} 至 {{ result.data_period?.end }}
          </el-descriptions-item>
          <el-descriptions-item label="样本数量">
            {{ result.samples?.total }} (训练: {{ result.samples?.train }}, 验证: {{ result.samples?.validation }})
          </el-descriptions-item>
          <el-descriptions-item label="模型路径" :span="2">
            <el-input :value="result.model_path" readonly>
              <template #append>
                <el-button @click="copyPath(result.model_path)">复制</el-button>
              </template>
            </el-input>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
    
    <!-- Walk-Forward 验证结果 -->
    <div v-if="walkForwardResult">
      <el-divider content-position="left">Walk-Forward 验证结果</el-divider>
      
      <el-card class="mb-16">
        <template #header>
          <span class="card-title">汇总统计</span>
        </template>
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-value">{{ walkForwardResult.summary?.avg_accuracy || 0 }}%</div>
              <div class="stat-label">平均准确率</div>
              <div class="stat-desc">± {{ walkForwardResult.summary?.std_accuracy || 0 }}%</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-value">{{ walkForwardResult.summary?.avg_f1 || 0 }}%</div>
              <div class="stat-label">平均 F1</div>
              <div class="stat-desc">± {{ walkForwardResult.summary?.std_f1 || 0 }}%</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-value">{{ walkForwardResult.summary?.avg_auc || 0 }}%</div>
              <div class="stat-label">平均 AUC</div>
              <div class="stat-desc">± {{ walkForwardResult.summary?.std_auc || 0 }}%</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-value">{{ walkForwardResult.summary?.total_windows || 0 }}</div>
              <div class="stat-label">验证窗口数</div>
              <div class="stat-desc">{{ walkForwardResult.parameters?.train_window }}天训练 / {{ walkForwardResult.parameters?.test_window }}天测试</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
      
      <el-card class="mb-16">
        <template #header>
          <span class="card-title">结果解读</span>
        </template>
        <el-alert :title="walkForwardResult.interpretation?.overall" type="success" :closable="false">
          <ul class="interpretation-list">
            <li>{{ walkForwardResult.interpretation?.accuracy }}</li>
            <li>{{ walkForwardResult.interpretation?.stability }}</li>
          </ul>
        </el-alert>
        
        <!-- 指标详细解释 -->
        <el-divider content-position="left">评估指标说明</el-divider>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="准确率 (Accuracy)">
            <b>含义：</b>预测正确的比例 = (真阳 + 真阴) / 总样本<br>
            <b>解读：</b>准确率越高越好，但需注意类别不平衡问题。<br>
            <span style="color: #67c23a;">&ge;60%</span> 良好 | <span style="color: #e6a23c;">50-60%</span> 一般 | <span style="color: #f56c6c;">&lt;50%</span> 较差（接近随机）
          </el-descriptions-item>
          <el-descriptions-item label="F1 分数">
            <b>含义：</b>精确率和召回率的调和平均，用于衡量不平衡数据集的分类性能<br>
            <b>公式：</b>F1 = 2 × (精确率 × 召回率) / (精确率 + 召回率)<br>
            <b>解读：</b>F1 越高表示模型在少数类预测上越准确。<br>
            <span style="color: #67c23a;">&ge;0.5</span> 良好 | <span style="color: #e6a23c;">0.3-0.5</span> 一般 | <span style="color: #f56c6c;">&lt;0.3</span> 较差
          </el-descriptions-item>
          <el-descriptions-item label="AUC (ROC曲线下面积)">
            <b>含义：</b>模型区分正负样本能力的度量，值域 [0, 1]<br>
            <b>解读：</b>AUC = 0.5 表示随机猜测，AUC = 1.0 表示完美分类。<br>
            <span style="color: #67c23a;">&ge;0.7</span> 良好 | <span style="color: #e6a23c;">0.55-0.7</span> 一般 | <span style="color: #f56c6c;">&lt;0.55</span> 较差（接近随机）
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
      
      <!-- 各窗口详情 -->
      <el-card class="mb-16">
        <template #header>
          <span class="card-title">各窗口详细结果</span>
        </template>
        <el-table :data="walkForwardResult.window_details" stripe>
          <el-table-column prop="window_id" label="窗口" width="80" />
          <el-table-column label="训练区间" width="160">
            <template #default="{ row }">
              {{ row.train_period }}
            </template>
          </el-table-column>
          <el-table-column label="测试区间" width="160">
            <template #default="{ row }">
              {{ row.test_period }}
            </template>
          </el-table-column>
          <el-table-column prop="accuracy" label="准确率" width="100">
            <template #default="{ row }">
              <span :class="getMetricClass(row.accuracy)">{{ row.accuracy.toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="f1" label="F1" width="100">
            <template #default="{ row }">
              <span :class="getMetricClass(row.f1)">{{ row.f1.toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="auc" label="AUC" width="100">
            <template #default="{ row }">
              <span :class="getMetricClass(row.auc)">{{ row.auc.toFixed(1) }}%</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    
    <!-- 已保存模型 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">已保存的模型</span>
          <el-button size="small" @click="loadSavedModels">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <el-table :data="savedModels" stripe v-loading="loadingModels">
        <el-table-column prop="name" label="模型名称" />
        <el-table-column label="配置" width="300">
          <template #default="{ row }">
            <el-tag size="small" type="info">seq_len={{ row.config?.seq_length }}</el-tag>
            <el-tag size="small" type="info">hidden={{ row.config?.lstm_hidden }}</el-tag>
            <el-tag size="small" type="info">layers={{ row.config?.lstm_layers }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.files?.lstm === 'True'" type="success" size="small">LSTM</el-tag>
            <el-tag v-if="row.files?.lightgbm === 'True'" type="success" size="small">LightGBM</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="useModel(row)">使用</el-button>
            <el-button size="small" type="danger" @click="deleteModel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loadingModels && savedModels.length === 0" description="暂无保存的模型" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { predictApi } from '@/api/predict'
import { useRouter } from 'vue-router'

const router = useRouter()

// 表单数据
const form = reactive({
  code: '',
  startDate: '',
  endDate: '',
  forecastDays: 5,
  seqLength: 20,
  lstmHidden: 128,
  lstmLayers: 2,
  lstmDropout: 0.2,
  lstmEpochs: 50,
  lstmLr: 0.001,
  lstmBatchSize: 32,
  lgbNEstimators: 200,
  learningRate: 0.05,
  validationSplit: 0.2,
  saveModel: true,
  modelName: ''
})

// 训练状态
const training = ref(false)
const walkingForward = ref(false)
const progress = ref(0)
const progressStatus = ref('')
const progressLogs = ref([])
const result = ref(null)
const walkForwardResult = ref(null)

// 已保存模型
const savedModels = ref([])
const loadingModels = ref(false)

// 高级选项显示
const showAdvanced = ref(false)

// 预设配置
const presets = {
  fast: {
    seqLength: 10,
    lstmHidden: 64,
    lstmLayers: 1,
    lstmEpochs: 20,
    lgbNEstimators: 100,
    lstmDropout: 0.1
  },
  balanced: {
    seqLength: 20,
    lstmHidden: 128,
    lstmLayers: 2,
    lstmEpochs: 50,
    lgbNEstimators: 200,
    lstmDropout: 0.2
  },
  accurate: {
    seqLength: 30,
    lstmHidden: 256,
    lstmLayers: 3,
    lstmEpochs: 100,
    lgbNEstimators: 300,
    lstmDropout: 0.3
  }
}

/**
 * 应用预设配置
 */
const applyPreset = (preset) => {
  const config = presets[preset]
  if (config) {
    Object.assign(form, config)
    ElMessage.success(`已应用「${preset === 'fast' ? '快速训练' : preset === 'balanced' ? '均衡训练' : '高精度'}」预设`)
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(form, {
    code: '',
    startDate: '',
    endDate: '',
    forecastDays: 5,
    seqLength: 20,
    lstmHidden: 128,
    lstmLayers: 2,
    lstmDropout: 0.2,
    lstmEpochs: 50,
    lstmLr: 0.001,
    lstmBatchSize: 32,
    lgbNEstimators: 200,
    learningRate: 0.05,
    validationSplit: 0.2,
    saveModel: true,
    modelName: ''
  })
  result.value = null
  walkForwardResult.value = null
  progressLogs.value = []
  progress.value = 0
}

/**
 * 加载股票信息
 */
const loadStockInfo = () => {
  if (!form.code) {
    ElMessage.warning('请输入股票代码')
    return
  }
  // 简单的日期设置
  if (!form.endDate) {
    const today = new Date()
    form.endDate = today.toISOString().split('T')[0]
  }
  if (!form.startDate) {
    const oneYearAgo = new Date()
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1)
    form.startDate = oneYearAgo.toISOString().split('T')[0]
  }
  ElMessage.success(`股票 ${form.code} 参数已设置`)
}

/**
 * 添加日志
 */
const addLog = (message, type = 'info') => {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  progressLogs.value.push({ time, message, type })
}

/**
 * 开始训练
 */
const startTraining = async () => {
  if (!form.code) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  training.value = true
  progress.value = 0
  progressLogs.value = []
  result.value = null
  walkForwardResult.value = null
  
  addLog('开始准备训练数据...', 'info')
  
  try {
    // 构建请求参数
    const params = {
      code: form.code,
      start_date: form.startDate || undefined,
      end_date: form.endDate || undefined,
      seq_length: form.seqLength,
      forecast_days: form.forecastDays,
      lstm_hidden: form.lstmHidden,
      lstm_layers: form.lstmLayers,
      lstm_dropout: form.lstmDropout,
      lstm_epochs: form.lstmEpochs,
      lstm_lr: form.lstmLr,
      lstm_batch_size: form.lstmBatchSize,
      lgb_n_estimators: form.lgbNEstimators,
      learning_rate: form.learningRate,
      validation_split: form.validationSplit,
      save_model: form.saveModel,
      model_name: form.modelName || undefined
    }
    
    addLog('正在请求训练接口...', 'info')
    progress.value = 10
    
    const response = await predictApi.trainHybrid(params)
    
    progress.value = 90
    addLog('训练完成，正在分析结果...', 'success')
    
    result.value = response
    progress.value = 100
    progressStatus.value = 'success'
    
    addLog(`训练成功！准确率: ${response.metrics?.accuracy?.toFixed(2)}%`, 'success')
    addLog(`模型已保存至: ${response.model_path}`, 'success')
    
    ElMessage.success('模型训练完成！')
    
    // 刷新已保存模型列表
    loadSavedModels()
    
  } catch (e) {
    progressStatus.value = 'exception'
    // 尝试提取后端返回的详细错误信息
    const errorDetail = e.response?.data?.detail || e.message || '未知错误'
    const errorMsg = `训练失败: ${errorDetail}`
    
    addLog(errorMsg, 'error')
    // 使用更详细的错误提示弹窗
    if (e.response?.status === 400 && errorDetail.includes('\n')) {
      // 多行详细错误信息，显示详情弹窗
      ElMessage.error({
        message: '训练失败，请查看日志了解详情',
        duration: 0,
        showClose: true
      })
    } else {
      ElMessage.error('训练失败: ' + errorDetail.substring(0, 100))
    }
  } finally {
    training.value = false
  }
}

/**
 * 开始 Walk-Forward 验证
 */
const startWalkForward = async () => {
  if (!form.code) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  walkingForward.value = true
  progress.value = 0
  progressLogs.value = []
  result.value = null
  walkForwardResult.value = null
  
  addLog('开始 Walk-Forward 交叉验证...', 'info')
  
  try {
    // Walk-Forward 使用较小的默认窗口以适应不同数据量
    const params = {
      code: form.code,
      start_date: form.startDate || undefined,
      end_date: form.endDate || undefined,
      seq_length: form.seqLength,
      forecast_days: form.forecastDays,
      lstm_hidden: form.lstmHidden,
      lgb_n_estimators: form.lgbNEstimators,
      learning_rate: form.learningRate,
      train_window: 120,
      test_window: 15,
      lstm_epochs: Math.min(20, form.lstmEpochs)
    }
    
    addLog('正在执行滚动验证...', 'info')
    progress.value = 30
    
    const response = await predictApi.walkForward(params)
    
    progress.value = 90
    walkForwardResult.value = response
    
    addLog(`验证完成: ${response.summary?.total_windows} 个窗口`, 'success')
    addLog(`平均准确率: ${response.summary?.avg_accuracy?.toFixed(2)}%`, 'success')
    addLog(response.interpretation?.overall, 'success')
    
    ElMessage.success('Walk-Forward 验证完成！')
    
  } catch (e) {
    // 尝试提取后端返回的详细错误信息
    const errorDetail = e.response?.data?.detail || e.message || '未知错误'
    const errorMsg = `验证失败: ${errorDetail}`
    
    addLog(errorMsg, 'error')
    
    if (e.response?.status === 400 && errorDetail.includes('\n')) {
      ElMessage.error({
        message: '验证失败，请查看日志了解详情',
        duration: 0,
        showClose: true
      })
    } else {
      ElMessage.error('验证失败: ' + errorDetail.substring(0, 100))
    }
  } finally {
    walkingForward.value = false
    progress.value = 100
  }
}

/**
 * 加载已保存的模型
 */
const loadSavedModels = async () => {
  loadingModels.value = true
  try {
    const response = await predictApi.getSavedModels()
    savedModels.value = response.models || []
  } catch (e) {
    console.error('加载模型列表失败:', e)
  } finally {
    loadingModels.value = false
  }
}

/**
 * 使用已保存的模型
 */
const useModel = (model) => {
  ElMessageBox.confirm(`确定要使用模型「${model.name}」进行预测吗？`, '使用模型', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'info'
  }).then(() => {
    // 跳转到预测页面，传递股票代码和模型名称
    router.push({
      path: '/predict',
      query: { 
        code: model.name.split('_')[0],
        model: 'hybrid',
        modelName: model.name,
        useSaved: 'true'
      }
    })
  }).catch(() => {})
}

/**
 * 删除模型
 */
const deleteModel = async (model) => {
  try {
    await ElMessageBox.confirm(`确定要删除模型「${model.name}」吗？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await predictApi.deleteModel(model.name)
    ElMessage.success('模型已删除')
    loadSavedModels()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 复制路径
 */
const copyPath = (path) => {
  navigator.clipboard.writeText(path)
  ElMessage.success('路径已复制')
}

/**
 * 获取指标样式类
 */
const getMetricClass = (value) => {
  if (value >= 60) return 'metric-good'
  if (value >= 50) return 'metric-medium'
  return 'metric-bad'
}

/**
 * 格式化特征名称
 */
const formatFeatureName = (name) => {
  const nameMap = {
    'rsi': 'RSI 相对强弱指数',
    'macd_hist': 'MACD 柱状图',
    'volatility': '波动率',
    'volume_ratio': '成交量比率',
    'ma_ratio': '均线比率',
    'bb_upper': '布林带上轨',
    'bb_lower': '布林带下轨',
    'atr': 'ATR 平均真实波幅',
    'obv': 'OBV 能量潮',
    'kdj_k': 'KDJ K值',
    'kdj_d': 'KDJ D值',
    'kdj_j': 'KDJ J值'
  }
  return nameMap[name] || name
}

/**
 * 获取特征颜色
 */
const getFeatureColor = (idx) => {
  const colors = ['#67c23a', '#409eff', '#e6a23c', '#f56c6c', '#909399']
  return colors[idx % colors.length]
}

onMounted(() => {
  // 设置默认日期
  const today = new Date()
  const oneYearAgo = new Date()
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1)
  
  form.endDate = today.toISOString().split('T')[0]
  form.startDate = oneYearAgo.toISOString().split('T')[0]
  
  // 加载已保存的模型
  loadSavedModels()
})
</script>

<style scoped>
.train-page {
  max-width: 1400px;
  margin: 0 auto;
}

.config-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: bold;
  font-size: 16px;
}

.mb-16 {
  margin-bottom: 16px;
}

/* 参数表单布局 */
.param-form {
  padding-right: 20px;
}

.param-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

/* 统一标签宽度并右对齐，使左右两列文字对齐 */
.param-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
  line-height: 28px;
  width: 130px;
  text-align-last: justify; /* 两端对齐 */
  text-align: right;
}

/* 参数说明文字 */
.param-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-top: 6px;
  padding-left: 4px;
  border-left: 2px solid #e4e7ed;
  padding-left: 10px;
  white-space: normal;
  word-break: break-all;
}

.section-title {
  font-weight: 600;
  color: #409eff;
}

/* 滑块和输入框样式 */
:deep(.el-slider) {
  width: 100%;
  padding-right: 12px;
}

:deep(.el-slider__input) {
  width: 70px;
}

:deep(.el-input-number) {
  width: 100%;
}

/* 右侧列滑块额外右间距 */
:deep(.el-col:nth-child(2) .el-slider),
:deep(.el-col:last-child .el-slider) {
  padding-right: 16px;
}

:deep(.el-col:nth-child(2) .el-input-number),
:deep(.el-col:last-child .el-input-number) {
  margin-right: 4px;
}

.preset-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.progress-card {
  margin-bottom: 16px;
}

.progress-container {
  padding: 16px;
}

.progress-logs {
  max-height: 200px;
  overflow-y: auto;
  margin-top: 16px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.log-item {
  padding: 4px 8px;
  display: flex;
  gap: 12px;
}

.log-item.info {
  color: #409eff;
}

.log-item.success {
  color: #67c23a;
}

.log-item.error {
  color: #f56c6c;
}

.log-time {
  color: #999;
  flex-shrink: 0;
}

.metric-card {
  text-align: center;
  padding: 20px;
}

.metric-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.metric-desc {
  font-size: 12px;
  color: #999;
}

.metric-good {
  color: #67c23a;
}

.metric-medium {
  color: #e6a23c;
}

.metric-bad {
  color: #f56c6c;
}

.feature-importance {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-name {
  width: 160px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: #409eff;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
}

.feature-bar-container {
  flex: 1;
}

.feature-value {
  width: 60px;
  text-align: right;
  font-weight: bold;
}

.stat-card {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.stat-desc {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 4px;
}

.interpretation-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.interpretation-list li {
  margin-bottom: 4px;
}

:deep(.el-slider) {
  width: 100%;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>
