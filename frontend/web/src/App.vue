<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
/* 引入专业金融终端样式 */
@import './styles/professional.css';

/* Element Plus 深色主题覆盖 */
.el-card {
  --el-card-bg-color: var(--bg-card);
  --el-card-border-color: var(--border-default);
  background: var(--bg-card) !important;
  border-color: var(--border-default) !important;
  color: var(--text-primary);
}

.el-button {
  --el-button-bg-color: var(--bg-tertiary);
  --el-button-border-color: var(--border-default);
  --el-button-text-color: var(--text-primary);
  --el-button-hover-bg-color: var(--bg-hover);
  --el-button-hover-border-color: var(--accent-blue);
  --el-button-hover-text-color: var(--text-primary);
}

.el-button--primary {
  --el-button-bg-color: var(--accent-blue);
  --el-button-border-color: var(--accent-blue);
  --el-button-text-color: #ffffff;
  --el-button-hover-bg-color: #2563eb;
  --el-button-hover-border-color: #2563eb;
}

.el-input__wrapper {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--border-default) !important;
  box-shadow: none !important;
}

.el-input__inner {
  color: var(--text-primary) !important;
}

.el-input__inner::placeholder {
  color: var(--text-muted) !important;
}

.el-select__wrapper {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--border-default) !important;
  box-shadow: none !important;
}

.el-tag {
  --el-tag-bg-color: var(--bg-tertiary);
  --el-tag-border-color: var(--border-default);
  --el-tag-text-color: var(--text-secondary);
}

.el-tag--success {
  --el-tag-bg-color: rgba(34, 197, 94, 0.15);
  --el-tag-border-color: rgba(34, 197, 94, 0.3);
  --el-tag-text-color: #22c55e;
}

.el-tag--danger {
  --el-tag-bg-color: rgba(239, 68, 68, 0.15);
  --el-tag-border-color: rgba(239, 68, 68, 0.3);
  --el-tag-text-color: #ef4444;
}

.el-table {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-tertiary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-default);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-muted);
}

.el-descriptions__label {
  color: var(--text-muted) !important;
  background: var(--bg-tertiary) !important;
}

.el-descriptions__content {
  color: var(--text-primary) !important;
  background: var(--bg-card) !important;
}

.el-message {
  --el-message-bg-color: var(--bg-card);
  --el-message-border-color: var(--border-default);
}

.el-loading-mask {
  background-color: rgba(10, 14, 23, 0.9) !important;
}

.el-loading-spinner .circular {
  stroke: var(--accent-blue) !important;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-hover);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
