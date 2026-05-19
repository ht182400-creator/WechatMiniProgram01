/**
 * 辅助函数
 */

/**
 * 格式化日期
 * @param {Date|string|number} date - 日期
 * @param {string} format - 格式
 * @returns {string}
 */
function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''
  
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
    .replace('ss', second)
}

/**
 * 格式化数字，保留指定小数位
 * @param {number} num - 数字
 * @param {number} decimals - 小数位
 * @returns {string}
 */
function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '--'
  return Number(num).toFixed(decimals)
}

/**
 * 格式化百分比
 * @param {number} num - 数字 (0-1 或 0-100)
 * @param {boolean} isPercent - 是否已是百分比
 * @returns {string}
 */
function formatPercent(num, isPercent = false) {
  if (num === null || num === undefined) return '--'
  const value = isPercent ? num : num * 100
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

/**
 * 格式化金额
 * @param {number} amount - 金额
 * @returns {string}
 */
function formatAmount(amount) {
  if (amount === null || amount === undefined) return '--'
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(2) + '亿'
  } else if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

/**
 * 颜色转换
 * @param {number} value - 涨跌值
 * @returns {string}
 */
function getChangeColor(value) {
  if (value > 0) return '#ff4d4f'
  if (value < 0) return '#52c41a'
  return '#999999'
}

/**
 * 获取涨跌文字
 * @param {number} value - 涨跌值
 * @returns {string}
 */
function getChangeText(value) {
  if (value > 0) return '涨'
  if (value < 0) return '跌'
  return '平'
}

/**
 * 防抖函数
 * @param {Function} fn - 要防抖的函数
 * @param {number} delay - 延迟时间
 * @returns {Function}
 */
function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * 节流函数
 * @param {Function} fn - 要节流的函数
 * @param {number} delay - 间隔时间
 * @returns {Function}
 */
function throttle(fn, delay = 300) {
  let lastTime = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastTime >= delay) {
      lastTime = now
      fn.apply(this, args)
    }
  }
}

/**
 * 深拷贝
 * @param {any} obj - 要拷贝的对象
 * @returns {any}
 */
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  const cloned = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key])
    }
  }
  return cloned
}

module.exports = {
  formatDate,
  formatNumber,
  formatPercent,
  formatAmount,
  getChangeColor,
  getChangeText,
  debounce,
  throttle,
  deepClone
}
