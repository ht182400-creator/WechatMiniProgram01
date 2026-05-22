<template>
  <!-- 统一底部状态栏 -->
  <footer class="app-footer">
    <div class="footer-left">
      <span class="status-item">
        <span class="status-dot" :class="wsStatus"></span>
        <span>WebSocket: {{ wsText }}</span>
      </span>
      <span class="status-separator">|</span>
      <span class="status-item">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        行情延迟: &lt;1s
      </span>
      <span class="status-separator">|</span>
      <span class="status-item">数据源: {{ dataSource || '多源聚合' }}</span>
    </div>

    <div class="footer-center">
      <span class="disclaimer">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        本系统仅供学习研究使用，预测结果仅供参考，不构成投资建议
      </span>
    </div>

    <div class="footer-right">
      <span class="version">v4.1.0</span>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  /** WebSocket 状态: connected / disconnected / connecting */
  wsStatus: { type: String, default: 'disconnected' },
  /** WebSocket 状态文本 */
  wsText: { type: String, default: '未连接' },
  /** 当前数据源 */
  dataSource: { type: String, default: '多源聚合' }
})
</script>

<style scoped>
.app-footer {
  display: flex;
  align-items: center;
  height: 28px;
  padding: 0 16px;
  background: #0e1015;
  border-top: 1px solid #1f2229;
  flex-shrink: 0;
  font-size: 11px;
  color: #555a63;
  user-select: none;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.footer-center {
  flex: 1;
  text-align: center;
}

.footer-right {
  flex: 1;
  text-align: right;
  font-family: var(--font-mono, monospace);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-separator {
  opacity: 0.3;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.status-dot.connected { background: #3fb950; }
.status-dot.disconnected { background: #6e7681; }
.status-dot.connecting { background: #e3b341; animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.disclaimer {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.version {
  opacity: 0.5;
}
</style>
