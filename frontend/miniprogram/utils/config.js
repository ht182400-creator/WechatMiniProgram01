/**
 * 配置文件
 */

// API 端点定义
const API = {
  // 系统接口
  system: {
    health: '/api/system/health',
    info: '/api/system/info'
  },
  // 股票接口
  stock: {
    list: '/api/stock/list',
    search: '/api/stock/search',
    detail: '/api/stock/detail',
    history: '/api/stock/history',
    realtime: '/api/stock/realtime'
  },
  // 回测接口
  backtest: {
    run: '/api/backtest/run',
    result: '/api/backtest/result',
    strategies: '/api/backtest/strategies'
  },
  // 预测接口
  predict: {
    predict: '/api/predict/predict',
    history: '/api/predict/history'
  }
}

// 策略类型
const STRATEGIES = {
  MA_CROSS: 'ma_cross',
  RSI: 'rsi',
  MACD: 'macd',
  BOLLINGER: 'bollinger'
}

// 策略配置
const STRATEGY_CONFIG = {
  ma_cross: {
    name: '均线交叉策略',
    params: ['short_ma', 'long_ma']
  },
  rsi: {
    name: 'RSI 策略',
    params: ['period', 'overbought', 'oversold']
  },
  macd: {
    name: 'MACD 策略',
    params: ['fast', 'slow', 'signal']
  },
  bollinger: {
    name: '布林带策略',
    params: ['period', 'std_dev']
  }
}

module.exports = {
  API,
  STRATEGIES,
  STRATEGY_CONFIG
}
