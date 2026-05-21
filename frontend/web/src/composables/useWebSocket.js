import { ref, onUnmounted } from 'vue'

/**
 * WebSocket 实时行情 Composable
 * 
 * 管理 WebSocket 连接生命周期，支持自动重连、订阅管理、行情推送接收。
 * 在 Home.vue 和 StockDetail.vue 中复用，实现页面行情的实时刷新。
 * 
 * @param {Object} options - 配置选项
 * @param {string} [options.url] - WebSocket 地址，默认从当前页面主机推导
 * @param {number} [options.reconnectBase=3000] - 初始重连间隔(ms)
 * @param {number} [options.reconnectMax=30000] - 最大重连间隔(ms)
 * @returns {Object} WebSocket 连接状态与操作方法
 * 
 * @example
 * const { connectionStatus, quotes, subscribe, unsubscribe } = useWebSocket()
 * subscribe(['600000', '000001'])
 * // quotes.value['600000'] => { price: 7.85, change: 0.12, pct_change: 1.55, ... }
 */
export function useWebSocket(options = {}) {
  const {
    url,
    reconnectBase = 3000,
    reconnectMax = 30000
  } = options

  /** 根据当前页面协议和主机自动推导 WebSocket 地址 */
  const wsUrl = url || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/realtime`

  /** WebSocket 连接状态: 'disconnected' | 'connecting' | 'connected' */
  const connectionStatus = ref('disconnected')

  /** 各股票实时行情数据: { [code]: { name, price, open, high, low, volume, amount, change, pct_change, timestamp } } */
  const quotes = ref({})

  /** 当前已订阅的股票代码列表 */
  const subscribedCodes = ref([])

  let ws = null
  let reconnectTimer = null
  let heartbeatTimer = null
  let currentReconnectDelay = reconnectBase
  let isManualClose = false

  /**
   * 建立 WebSocket 连接
   */
  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    isManualClose = false
    connectionStatus.value = 'connecting'

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[WS] 已连接到 ', wsUrl)
        connectionStatus.value = 'connected'
        currentReconnectDelay = reconnectBase
        startHeartbeat()

        // 重新连接后，恢复之前订阅的股票
        if (subscribedCodes.value.length > 0) {
          send({ action: 'subscribe', codes: [...subscribedCodes.value] })
        }
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (e) {
          console.warn('[WS] 消息解析失败:', e)
        }
      }

      ws.onclose = (event) => {
        // 若 module-level ws 已被替换为新连接（如 reconnect() 先关旧建新），
        // 则此次 onclose 属于旧连接的回调，跳过避免覆盖新连接状态
        if (event.target !== ws) {
          return
        }

        console.log(`[WS] 连接关闭 (code: ${event.code})`)
        connectionStatus.value = 'disconnected'
        stopHeartbeat()
        ws = null

        // 非主动关闭则自动重连
        if (!isManualClose) {
          scheduleReconnect()
        }
      }

      ws.onerror = (error) => {
        console.error('[WS] 连接错误:', error)
        // onclose 会在 onerror 之后自动触发，由 onclose 处理重连
      }
    } catch (e) {
      console.error('[WS] 创建连接失败:', e)
      connectionStatus.value = 'disconnected'
      scheduleReconnect()
    }
  }

  /**
   * 处理接收到的消息
   * @param {Object} msg - 服务端推送的消息
   */
  function handleMessage(msg) {
    switch (msg.type) {
      case 'quote':
        // 更新行情数据
        if (msg.code && msg.data) {
          quotes.value = {
            ...quotes.value,
            [msg.code]: {
              ...msg.data,
              timestamp: msg.timestamp || Date.now()
            }
          }
        }
        break

      case 'subscribed':
        // 确认订阅成功
        if (msg.codes) {
          subscribedCodes.value = [...new Set([...subscribedCodes.value, ...msg.codes])]
        }
        break

      case 'unsubscribed':
        // 确认取消订阅
        if (msg.codes) {
          const removeSet = new Set(msg.codes)
          subscribedCodes.value = subscribedCodes.value.filter(c => !removeSet.has(c))
        }
        break

      case 'heartbeat':
        // 心跳消息，仅用于保持连接活跃
        break

      case 'pong':
        // ping/pong 响应
        break

      case 'subscription_list':
        // 服务端返回当前订阅列表
        if (msg.codes) {
          subscribedCodes.value = msg.codes
        }
        break

      default:
        console.debug('[WS] 未知消息类型:', msg.type)
    }
  }

  /**
   * 主动断开连接
   */
  function disconnect() {
    isManualClose = true
    stopHeartbeat()
    clearReconnectTimer()
    if (ws) {
      ws.close(1000, '客户端主动断开')
      ws = null
    }
    connectionStatus.value = 'disconnected'
    subscribedCodes.value = []
  }

  /**
   * 订阅股票行情
   * @param {string[]} codes - 股票代码列表
   */
  function subscribe(codes) {
    if (!codes || codes.length === 0) return

    // 确保连接已建立
    if (connectionStatus.value !== 'connected') {
      connect()
      // 待连接成功后自动订阅
      subscribedCodes.value = [...new Set([...subscribedCodes.value, ...codes])]
      return
    }

    send({ action: 'subscribe', codes })
  }

  /**
   * 取消订阅股票
   * @param {string[]} codes - 股票代码列表，若为空则取消所有订阅
   */
  function unsubscribe(codes) {
    if (!codes || codes.length === 0) {
      // 取消所有订阅
      send({ action: 'unsubscribe', codes: [...subscribedCodes.value] })
      subscribedCodes.value = []
      return
    }

    send({ action: 'unsubscribe', codes })
    const removeSet = new Set(codes)
    subscribedCodes.value = subscribedCodes.value.filter(c => !removeSet.has(c))
  }

  /**
   * 发送消息到服务端
   * @param {Object} data - 消息体
   */
  function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify(data))
      } catch (e) {
        console.error('[WS] 发送消息失败:', e)
      }
    }
  }

  /**
   * 启动心跳定时器
   */
  function startHeartbeat() {
    stopHeartbeat()
    // 每 25 秒发一次 ping，服务端超时是 30 秒
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        send({ action: 'ping' })
      }
    }, 25000)
  }

  /**
   * 停止心跳定时器
   */
  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  /**
   * 安排自动重连（指数退避）
   */
  function scheduleReconnect() {
    clearReconnectTimer()
    if (isManualClose) return

    console.log(`[WS] ${currentReconnectDelay / 1000}s 后尝试重连...`)
    reconnectTimer = setTimeout(() => {
      if (!isManualClose) {
        connect()
      }
    }, currentReconnectDelay)

    // 指数退避，最大不超过 reconnectMax
    currentReconnectDelay = Math.min(currentReconnectDelay * 1.5, reconnectMax)
  }

  /**
   * 清除重连定时器
   */
  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  /**
   * 强制重连
   */
  function reconnect() {
    disconnect()
    isManualClose = false
    currentReconnectDelay = reconnectBase
    connect()
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    disconnect()
  })

  return {
    /** 连接状态 ref: 'disconnected' | 'connecting' | 'connected' */
    connectionStatus,
    /** 行情数据 ref: { [code]: { name, price, open, high, low, volume, amount, change, pct_change, timestamp } } */
    quotes,
    /** 当前订阅代码 ref: string[] */
    subscribedCodes,
    /** 建立连接 */
    connect,
    /** 断开连接 */
    disconnect,
    /** 订阅股票: subscribe(['600000']) */
    subscribe,
    /** 取消订阅股票: unsubscribe(['600000']) */
    unsubscribe,
    /** 发送消息: send({ action: 'ping' }) */
    send,
    /** 强制重连 */
    reconnect
  }
}
