<template>
  <el-config-provider :locale="zhCn">
    <router-view v-slot="{ Component }">
      <transition name="page-fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
/* 引入专业金融终端样式 */
@import './styles/professional.css';

/* ==========================================================================
   Element Plus 深色主题 — 全局覆盖
   ========================================================================== */

/* ── ElCard ── */
.el-card {
  --el-card-bg-color: var(--bg-card);
  --el-card-border-color: var(--border-default);
  background: var(--bg-card) !important;
  border-color: var(--border-default) !important;
  color: var(--text-primary);
  border-radius: var(--radius-md) !important;
}

.el-card__header {
  border-bottom-color: var(--border-muted) !important;
  padding: 10px 16px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--text-muted) !important;
}

.el-card__body {
  color: var(--text-primary);
}

/* ── ElButton ── */
.el-button {
  --el-button-bg-color: var(--bg-tertiary);
  --el-button-border-color: var(--border-default);
  --el-button-text-color: var(--text-secondary);
  --el-button-hover-bg-color: var(--bg-hover);
  --el-button-hover-border-color: var(--border-accent);
  --el-button-hover-text-color: var(--text-primary);
  font-family: var(--font-ui);
}

.el-button--primary {
  --el-button-bg-color: var(--accent-gold);
  --el-button-border-color: var(--accent-gold);
  --el-button-text-color: #1a1c21;
  --el-button-hover-bg-color: var(--accent-gold-dim);
  --el-button-hover-border-color: var(--accent-gold-dim);
  --el-button-hover-text-color: #1a1c21;
  font-weight: 600;
}

/* ── ElInput ── */
.el-input__wrapper {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--border-default) !important;
  box-shadow: none !important;
  border-radius: var(--radius-sm) !important;
}

.el-input__wrapper.is-focus {
  border-color: var(--border-focus) !important;
}

.el-input__inner {
  color: var(--text-primary) !important;
  font-family: var(--font-mono);
}

.el-input__inner::placeholder {
  color: var(--text-muted) !important;
}

/* ── ElSelect ── */
.el-select__wrapper {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--border-default) !important;
  box-shadow: none !important;
  border-radius: var(--radius-sm) !important;
}

/* ── ElTag ── */
.el-tag {
  --el-tag-bg-color: var(--bg-tertiary);
  --el-tag-border-color: var(--border-default);
  --el-tag-text-color: var(--text-secondary);
}

/* ── ElTable ── */
.el-table {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-tertiary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-default);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-muted);
  --el-fill-color-lighter: rgba(27, 30, 38, 0.6);
  --el-fill-color-light: rgba(24, 27, 35, 0.4);
}

.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background-color: rgba(27, 30, 38, 0.6) !important;
  color: var(--text-primary) !important;
}

.el-table th.el-table__cell {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-muted) !important;
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.el-table td.el-table__cell {
  color: var(--text-primary) !important;
}

/* ── ElDescriptions ── */
.el-descriptions__label {
  color: var(--text-muted) !important;
  background: var(--bg-tertiary) !important;
}

.el-descriptions__content {
  color: var(--text-primary) !important;
  background: var(--bg-card) !important;
}

/* ── ElMessage ── */
.el-message {
  --el-message-bg-color: var(--bg-card);
  --el-message-border-color: var(--border-default);
}

/* ── ElDialog / ElDrawer ── */
.el-dialog {
  --el-dialog-bg-color: var(--bg-card);
  --el-dialog-border-color: var(--border-default);
  border-radius: var(--radius-lg) !important;
}

.el-drawer {
  --el-drawer-bg-color: var(--bg-card);
  --el-drawer-border-color: var(--border-default);
}

/* ── ElPopover ── */
.el-popover {
  background: var(--bg-card) !important;
  border-color: var(--border-default) !important;
}

/* ── ElLoading ── */
.el-loading-mask {
  background-color: var(--bg-overlay) !important;
}

.el-loading-spinner .circular {
  stroke: var(--accent-gold) !important;
}

/* ── ElPagination ── */
.el-pagination {
  --el-pagination-bg-color: var(--bg-card);
  --el-pagination-button-bg-color: var(--bg-tertiary);
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-hover-color: var(--accent-gold);
}

/* ── ElTabs ── */
.el-tabs__header {
  margin-bottom: 12px !important;
}

.el-tabs__item {
  color: var(--text-muted) !important;
  font-weight: 500;
  transition: color var(--duration-fast) var(--ease-out);
}

.el-tabs__item:hover {
  color: var(--text-secondary) !important;
}

.el-tabs__item.is-active {
  color: var(--accent-gold) !important;
}

.el-tabs__active-bar {
  background-color: var(--accent-gold) !important;
}

.el-tabs__nav-wrap::after {
  background-color: var(--border-default) !important;
  height: 1px !important;
}

/* ── 下拉菜单 ── */
.el-select-dropdown {
  background: var(--bg-card) !important;
  border-color: var(--border-default) !important;
}

.el-select-dropdown__item {
  color: var(--text-secondary) !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}

.el-select-dropdown__item.selected {
  color: var(--accent-gold) !important;
}

/* ── ElForm ── */
.el-form-item__label {
  color: var(--text-secondary) !important;
  font-size: 13px;
}

/* ── ElMenu ── */
.el-menu {
  --el-menu-bg-color: var(--bg-primary);
  --el-menu-text-color: var(--text-secondary);
  --el-menu-hover-bg-color: var(--bg-hover);
  --el-menu-border-color: var(--border-default);
  border-right-color: var(--border-default) !important;
}

/* ==========================================================================
   页面切换动画
   ========================================================================== */
.page-fade-enter-active {
  transition: opacity 0.2s var(--ease-out), transform 0.2s var(--ease-out);
}

.page-fade-leave-active {
  transition: opacity 0.12s var(--ease-out), transform 0.12s var(--ease-out);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
