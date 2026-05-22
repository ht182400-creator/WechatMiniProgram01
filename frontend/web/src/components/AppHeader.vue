<template>
  <!-- 统一顶部导航栏 -->
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo-link">
        <svg class="logo-icon" width="30" height="30" viewBox="0 0 30 30" fill="none">
          <rect width="30" height="30" rx="7" fill="url(#logoGrad)" />
          <path d="M8 21L10 15L14 18L17 11L21 16" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <defs>
            <linearGradient id="logoGrad" x1="0" y1="0" x2="30" y2="30">
              <stop stop-color="#D4A853"/>
              <stop offset="1" stop-color="#B8860B"/>
            </linearGradient>
          </defs>
        </svg>
        <span class="logo-text">QuantTerminal</span>
      </router-link>

      <!-- 搜索框（可选） -->
      <slot name="search" />
    </div>

    <!-- 导航项 -->
    <nav class="header-nav">
      <template v-for="item in navItems" :key="item.to">
        <router-link
          :to="item.to"
          :class="['nav-item', { active: isActive(item.to) }]"
        >
          <!-- SVG 图标 -->
          <svg v-if="item.icon" width="17" height="17" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
          >
            <path v-for="(d, di) in item.icon" :key="di" :d="d" />
          </svg>
          <span>{{ item.label }}</span>
        </router-link>
      </template>
    </nav>

    <!-- 右侧操作区 -->
    <div class="header-right">
      <slot name="actions" />
      <div class="time-badge">
        <span class="time-dot"></span>
        <span class="time-text">{{ timeDisplay }}</span>
      </div>
    </div>
  </header>
</template>

<script setup>
/**
 * 统一顶部导航栏组件
 * 所有页面共享，减少代码重复
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  /** 导航项列表 */
  navItems: {
    type: Array,
    default: () => [
      { to: '/',          label: '首页', icon: ['M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z', 'M9 22V12h6v10'] },
      { to: '/stock',     label: '行情', icon: ['M22 12h-4l-3 9-6-18-3 9H2'] },
      { to: '/finance',   label: '财务', icon: ['M3 3h18v18H3z', 'M3 9h18', 'M9 21V9'] },
      { to: '/backtest',  label: '回测', icon: ['M18 20V10', 'M12 20V4', 'M6 20v-6'] },
      { to: '/predict',   label: '智能预测', icon: ['M12 2a4 4 0 014 4v1h3a1 1 0 011 1v12a1 1 0 01-1 1H5a1 1 0 01-1-1V8a1 1 0 011-1h3V6a4 4 0 014-4z', 'M9 14a3 3 0 016 0'] },
      { to: '/train',     label: '训练', icon: ['M12 2L2 7l10 5 10-5-10-5z', 'M2 17l10 5 10-5', 'M2 12l10 5 10-5'] }
    ]
  }
})

const route = useRoute()

/** 判断当前路由是否激活 */
const isActive = (to) => {
  if (to === '/') return route.name === 'Home'
  if (to === '/stock') return route.name === 'StockList' || route.name === 'StockDetail'
  return route.path.startsWith(to)
}

// 实时时间
const timeDisplay = ref('')
let timeInterval = null

const updateTime = () => {
  const now = new Date()
  timeDisplay.value = now.toLocaleTimeString('zh-CN', { hour12: false })
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
})
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  height: 52px;
  padding: 0 18px;
  background: #111318;
  border-bottom: 1px solid #1f2229;
  flex-shrink: 0;
  gap: 20px;
  user-select: none;
  z-index: 100;
}

/* ---- 左侧 ---- */
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 9px;
  text-decoration: none;
  color: inherit;
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  font-family: var(--font-display, 'Outfit', sans-serif);
  font-size: 17px;
  font-weight: 700;
  color: #c9cdd4;
  letter-spacing: -0.3px;
}

/* ---- 导航 ---- */
.header-nav {
  display: flex;
  align-items: center;
  gap: 3px;
  flex: 1;
  justify-content: center;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 13px;
  border-radius: 7px;
  color: #8b949e;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.18s ease;
  white-space: nowrap;
  position: relative;
}

.nav-item:hover {
  color: #c9cdd4;
  background: rgba(212, 168, 83, 0.06);
}

.nav-item.active {
  color: #d4a853;
  background: rgba(212, 168, 83, 0.1);
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 13px;
  right: 13px;
  height: 2px;
  background: #d4a853;
  border-radius: 1px 1px 0 0;
}

/* ---- 右侧 ---- */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 5px;
  background: #1a1d24;
  border: 1px solid #252830;
}

.time-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3fb950;
  animation: timePulse 2s ease-in-out infinite;
}

@keyframes timePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.time-text {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 12px;
  color: #8b949e;
}
</style>
