<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="200px" class="sidebar">
          <div class="logo">
            <el-icon><DataLine /></el-icon>
            <span>股票量化系统</span>
          </div>
          <el-menu
            :default-active="route.path"
            router
            class="sidebar-menu"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/stock">
              <el-icon><TrendCharts /></el-icon>
              <span>股票行情</span>
            </el-menu-item>
            <el-menu-item index="/backtest">
              <el-icon><DataAnalysis /></el-icon>
              <span>策略回测</span>
            </el-menu-item>
            <el-menu-item index="/predict">
              <el-icon><MagicStick /></el-icon>
              <span>趋势预测</span>
            </el-menu-item>
            <el-menu-item index="/train">
              <el-icon><Box /></el-icon>
              <span>模型训练</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-container>
          <!-- 顶部导航 -->
          <el-header class="header">
            <div class="header-left">
              <h2>{{ pageTitle }}</h2>
            </div>
            <div class="header-right">
              <el-button type="primary" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新数据
              </el-button>
            </div>
          </el-header>

          <!-- 主内容 -->
          <el-main class="main-content">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const route = useRoute()

const pageTitle = computed(() => {
  const titles = {
    '/': '首页概览',
    '/stock': '股票行情',
    '/backtest': '策略回测',
    '/predict': '趋势预测',
    '/train': '模型训练'
  }
  return titles[route.path] || '股票量化系统'
})

const refreshData = () => {
  ElMessage.success('数据刷新成功')
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 16px;
  font-weight: bold;
  color: #fff;
  border-bottom: 1px solid #002140;
}

.logo .el-icon {
  font-size: 24px;
  color: #409eff;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

::deep(.el-menu) {
  background: transparent;
}

::deep(.el-menu-item) {
  color: #fff;
}

::deep(.el-menu-item:hover),
::deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
}
</style>
