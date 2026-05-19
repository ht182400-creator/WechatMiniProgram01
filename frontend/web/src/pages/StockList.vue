<template>
  <div class="stock-list-page">
    <!-- 搜索栏 -->
    <div class="card search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索股票代码或名称"
        clearable
        @keyup.enter="handleSearch"
        style="max-width: 400px"
      >
        <template #append>
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 股票列表 -->
    <div class="card">
      <el-table
        :data="stocks"
        stripe
        v-loading="loading"
        @row-click="handleRowClick"
        style="cursor: pointer"
      >
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="market" label="市场" width="80">
          <template #default="{ row }">
            <el-tag size="small">
              {{ row.market?.toUpperCase() || 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" min-width="120" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="viewDetail(row.code)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        layout="prev, pager, next"
        style="margin-top: 16px; justify-content: center"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { stockApi } from '@/api'

const router = useRouter()

const stocks = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const loadStocks = async () => {
  loading.value = true
  try {
    let res
    if (searchKeyword.value) {
      res = await stockApi.search(searchKeyword.value)
    } else {
      res = await stockApi.getList()
    }
    total.value = res.total || 0
    stocks.value = res.stocks || []
  } catch (e) {
    console.error('加载股票列表失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadStocks()
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const handleRowClick = (row) => {
  router.push(`/stock/${row.code}`)
}

const viewDetail = (code) => {
  router.push(`/stock/${code}`)
}

onMounted(() => {
  loadStocks()
})
</script>

<style scoped>
.stock-list-page {
  max-width: 1400px;
  margin: 0 auto;
}

.search-bar {
  display: flex;
  gap: 16px;
  align-items: center;
}
</style>
