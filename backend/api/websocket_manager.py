# -*- coding: utf-8 -*-
"""
WebSocket 实时行情服务
提供股票实时行情推送功能
@author: StockQuant Team
@date: 2026-05-21
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, List, Any
from fastapi import WebSocket, WebSocketDisconnect
import pandas as pd

from adapters import get_data_source_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket 连接管理器
    
    管理客户端连接，支持：
    - 订阅/取消订阅股票
    - 广播消息到指定订阅者
    - 心跳检测
    """
    
    def __init__(self):
        # 股票代码 -> 订阅的 WebSocket 连接集合
        self._subscriptions: Dict[str, Set[WebSocket]] = {}
        # WebSocket 连接 -> 订阅的股票代码集合
        self._client_subscriptions: Dict[WebSocket, Set[str]] = {}
        # 活跃连接
        self._active_connections: Set[WebSocket] = set()
        # 锁
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket) -> bool:
        """接受并注册 WebSocket 连接"""
        try:
            await websocket.accept()
            async with self._lock:
                self._active_connections.add(websocket)
                self._client_subscriptions[websocket] = set()
            logger.info(f"WebSocket 连接已建立 (总计: {len(self._active_connections)})")
            return True
        except Exception as e:
            logger.error(f"WebSocket 连接失败: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """断开并清理 WebSocket 连接"""
        async with self._lock:
            # 从所有订阅中移除
            codes = self._client_subscriptions.get(websocket, set())
            for code in codes:
                if code in self._subscriptions:
                    self._subscriptions[code].discard(websocket)
            
            # 清理连接
            self._active_connections.discard(websocket)
            self._client_subscriptions.pop(websocket, None)
            
            logger.info(f"WebSocket 连接已断开 (剩余: {len(self._active_connections)})")
    
    async def subscribe(self, websocket: WebSocket, codes: List[str]):
        """
        订阅股票行情
        
        Args:
            websocket: WebSocket 连接
            codes: 股票代码列表
        """
        async with self._lock:
            for code in codes:
                # 添加到订阅列表
                if code not in self._subscriptions:
                    self._subscriptions[code] = set()
                self._subscriptions[code].add(websocket)
                
                # 记录客户端订阅
                if websocket in self._client_subscriptions:
                    self._client_subscriptions[websocket].add(code)
            
            logger.debug(f"订阅更新: {codes}, 连接订阅总数: {len(self._client_subscriptions.get(websocket, set()))}")
    
    async def unsubscribe(self, websocket: WebSocket, codes: List[str]):
        """取消订阅股票"""
        async with self._lock:
            for code in codes:
                if code in self._subscriptions:
                    self._subscriptions[code].discard(websocket)
                if websocket in self._client_subscriptions:
                    self._client_subscriptions[websocket].discard(code)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"发送消息失败: {e}")
    
    async def broadcast(self, message: dict, codes: Optional[List[str]] = None):
        """
        广播消息
        
        Args:
            message: 消息内容
            codes: 如果指定，只发送给订阅了这些股票的客户端
        """
        if codes is None:
            # 发送给所有活跃连接
            targets = self._active_connections
        else:
            # 只发送给订阅了指定股票的连接
            targets = set()
            for code in codes:
                if code in self._subscriptions:
                    targets.update(self._subscriptions[code])
        
        if not targets:
            return
        
        # 并发发送
        tasks = []
        for websocket in targets:
            try:
                tasks.append(websocket.send_json(message))
            except Exception:
                pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    @property
    def connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self._active_connections)
    
    @property
    def subscription_count(self) -> int:
        """获取订阅总数"""
        return sum(len(s) for s in self._subscriptions.values())


class RealtimeQuoteService:
    """
    实时行情服务
    
    定期从数据源获取最新行情并推送给订阅者
    """
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._data_manager = get_data_source_manager()
        # 缓存上一次的行情数据用于计算涨跌
        self._last_quotes: Dict[str, dict] = {}
        # 更新间隔（秒）
        self._interval = 5
    
    async def start(self):
        """启动实时行情推送服务"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info("实时行情推送服务已启动")
    
    async def stop(self):
        """停止实时行情推送服务"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("实时行情推送服务已停止")
    
    async def _update_loop(self):
        """更新循环"""
        while self._running:
            try:
                await self._push_quotes()
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"行情推送异常: {e}")
                await asyncio.sleep(self._interval)
    
    async def _push_quotes(self):
        """获取并推送最新行情"""
        # 获取所有订阅的股票代码
        codes = list(self.manager._subscriptions.keys())
        if not codes:
            return
        
        try:
            # 批量获取实时行情
            df = self._data_manager.get_realtime_quote(codes)
            
            if df.empty:
                return
            
            # 推送每只股票的行情
            for _, row in df.iterrows():
                code = str(row.get('code', ''))
                
                # 构造推送数据（price 优先，mootdx quotes() 不返回 close 字段）
                quote = {
                    'type': 'quote',
                    'code': code,
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'name': row.get('name', code),
                        'price': float(row.get('price', row.get('close', 0))),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'volume': float(row.get('volume', 0)),
                        'amount': float(row.get('amount', 0)),
                    }
                }
                
                # 计算涨跌
                last = self._last_quotes.get(code, {})
                last_price = last.get('price', quote['data']['price'])
                quote['data']['change'] = quote['data']['price'] - last_price
                
                if last_price > 0:
                    quote['data']['pct_change'] = (quote['data']['change'] / last_price) * 100
                
                self._last_quotes[code] = quote['data']
                
                # JSON安全清洗：NaN/Infinity → 0，确保 json.dumps 可序列化
                quote = self._sanitize_for_json(quote)
                
                # 广播给订阅者
                await self.manager.broadcast(quote, [code])
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
    
    @staticmethod
    def _sanitize_for_json(obj):
        """递归替换 NaN/Infinity 为 0，确保 JSON 序列化不报错"""
        import math
        
        if isinstance(obj, dict):
            return {k: RealtimeQuoteService._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [RealtimeQuoteService._sanitize_for_json(v) for v in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return 0.0
            return obj
        return obj
    
    async def push_heartbeat(self):
        """推送心跳消息"""
        await self.manager.broadcast({
            'type': 'heartbeat',
            'timestamp': datetime.now().isoformat(),
            'connections': self.manager.connection_count
        })


# 全局实例
_connection_manager: Optional[ConnectionManager] = None
_realtime_service: Optional[RealtimeQuoteService] = None


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器单例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_realtime_service() -> RealtimeQuoteService:
    """获取实时行情服务单例"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeQuoteService(get_connection_manager())
    return _realtime_service


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点处理函数
    
    协议：
    - 客户端发送 {"action": "subscribe", "codes": ["600000", "000001"]}
    - 客户端发送 {"action": "unsubscribe", "codes": ["600000"]}
    - 服务端推送 {"type": "quote", "code": "600000", "data": {...}}
    - 服务端推送 {"type": "heartbeat", "timestamp": "..."}
    """
    manager = get_connection_manager()
    
    # 接受连接
    if not await manager.connect(websocket):
        return
    
    try:
        # 启动实时行情服务
        service = get_realtime_service()
        if not service._running:
            await service.start()
        
        # 持续处理消息
        while True:
            try:
                # 接收客户端消息
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                message = json.loads(data)
                
                action = message.get('action', '')
                codes = message.get('codes', [])
                
                if action == 'subscribe' and codes:
                    await manager.subscribe(websocket, codes)
                    await manager.send_personal_message({
                        'type': 'subscribed',
                        'codes': codes,
                        'message': f'已订阅 {len(codes)} 只股票'
                    }, websocket)
                    
                elif action == 'unsubscribe' and codes:
                    await manager.unsubscribe(websocket, codes)
                    await manager.send_personal_message({
                        'type': 'unsubscribed',
                        'codes': codes,
                        'message': f'已取消订阅'
                    }, websocket)
                    
                elif action == 'ping':
                    await manager.send_personal_message({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }, websocket)
                    
                elif action == 'list':
                    # 返回当前订阅列表
                    subs = list(manager._client_subscriptions.get(websocket, set()))
                    await manager.send_personal_message({
                        'type': 'subscription_list',
                        'codes': subs
                    }, websocket)
                    
            except asyncio.TimeoutError:
                # 发送心跳
                await service.push_heartbeat()
            except json.JSONDecodeError:
                logger.warning(f"无效的JSON消息: {data[:100]}")
                
    except WebSocketDisconnect:
        logger.info("客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
    finally:
        await manager.disconnect(websocket)
