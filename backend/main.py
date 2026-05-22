# -*- coding: utf-8 -*-
"""
股票量化分析与预测系统 - 主应用入口
@author: StockQuant Team
@date: 2026-05-21
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.websockets import WebSocket
from contextlib import asynccontextmanager

from config import settings, init_directories
from models import db_manager
from adapters import get_data_source_manager
from api import stock, backtest, predict, system, financial, fundflow
from api.websocket_manager import websocket_endpoint, get_realtime_service

# 初始化目录
init_directories()

# 配置日志
log_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_DIR / 'app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 确保日志目录存在
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 60)
    logger.info("股票量化分析与预测系统 V4.0 启动中...")
    logger.info("=" * 60)
    
    # 初始化数据库
    db_manager.create_tables()
    logger.info("数据库初始化完成")
    
    # 初始化数据源
    data_manager = get_data_source_manager()
    results = data_manager.connect_all()
    for name, success in results.items():
        status = "✓" if success else "✗"
        logger.info(f"数据源 {name}: {status}")
    
    # 启动实时行情服务（会在第一个WebSocket连接时真正激活）
    realtime_service = get_realtime_service()
    
    logger.info("=" * 60)
    logger.info("系统启动完成!")
    logger.info("=" * 60)
    
    yield
    
    # 关闭时
    logger.info("系统关闭中...")
    await realtime_service.stop()
    data_manager.disconnect_all()
    logger.info("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="股票量化分析与预测系统 V4.0",
    description="""
## 系统概述
本系统提供股票数据采集、技术指标计算、策略回测和趋势预测功能。

## 架构特点
- **多数据源**：支持通达信本地、AKShare、Baostock、Tushare 多源数据，自动容灾
- **本地缓存**：Parquet 格式缓存，提升查询性能
- **策略引擎**：支持多种量化策略的回测
- **预测模型**：基于机器学习的趋势预测
- **实时推送**：WebSocket 支持股票实时行情推送

## 主要功能
- **股票数据**：实时行情、历史K线数据（含分钟级）
- **技术指标**：MA、RSI、MACD、布林带、KDJ、ATR 等
- **策略回测**：MA金叉死叉、RSI、MACD、布林带策略
- **趋势预测**：基于机器学习的涨跌预测
- **舆情分析**：新闻情绪分析

## WebSocket 实时行情
连接 `ws://host/ws/realtime` 可订阅实时股票行情推送。

## 免责声明
⚠️ **风险提示**：本系统仅供学习研究使用，预测结果仅供参考，
不构成任何投资建议。股票投资有风险，入市需谨慎！
    """,
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """禁用 API 响应缓存，确保浏览器始终获取最新数据"""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # 对所有 API 响应禁用缓存
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response


app.add_middleware(NoCacheMiddleware)

# 注册路由
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(stock.router, prefix="/api/stock", tags=["股票数据"])
app.include_router(financial.router, prefix="/api/financial", tags=["财务数据"])
app.include_router(fundflow.router, prefix="/api/fundflow", tags=["资金流向"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["策略回测"])
app.include_router(predict.router, prefix="/api/predict", tags=["趋势预测"])


# WebSocket 端点
@app.websocket("/ws/realtime")
async def realtime_websocket(websocket: WebSocket):
    """
    实时行情 WebSocket 端点
    
    客户端协议：
    1. 连接后发送 {"action": "subscribe", "codes": ["600000", "000001"]} 订阅股票
    2. 接收推送 {"type": "quote", "code": "600000", "data": {...}}
    3. 发送 {"action": "ping"} 心跳探测
    """
    await websocket_endpoint(websocket)


@app.get("/", tags=["首页"])
async def root():
    """系统首页"""
    return {
        "name": "股票量化分析与预测系统",
        "version": "4.0.0",
        "docs": "/docs",
        "message": "欢迎使用股票量化分析与预测系统！"
    }


@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查"""
    data_manager = get_data_source_manager()
    return {
        "status": "healthy",
        "service": "stock-quant-api",
        "version": "4.0.0",
        "data_sources": {
            name: adapter.is_available() 
            for name, adapter in data_manager.adapters.items()
        },
        "cache_enabled": settings.CACHE_ENABLE
    }


if __name__ == "__main__":
    import logging as _logging
    import uvicorn

    # ── 静默 Windows IOCP 客户端断连产生的 WinError 64 噪声日志 ──
    #   ERROR_NETNAME_DELETED (64): "指定的网络名不再可用。"
    #   浏览器/WebSocket 客户端关闭连接时，Windows ProactorEventLoop 会将其记录为
    #   "Task exception was never retrieved" 和 "Accept failed on a socket"。
    #   这些日志对排查问题无帮助，通过 logging 过滤器在全局层面静默。
    class WinError64Filter(_logging.Filter):
        def filter(self, record):
            msg = record.getMessage()
            # 过滤 WinError 64 相关的噪声日志（asyncio + uvicorn accept）
            if '指定的网络名不再可用' in msg:
                return False
            if 'WinError 64' in msg:
                return False
            return True

    # 挂载到 asyncio logger（覆盖子进程 + reload 场景）
    _logging.getLogger('asyncio').addFilter(WinError64Filter())
    # uvicorn.error 也可能输出 Accept failed
    _logging.getLogger('uvicorn.error').addFilter(WinError64Filter())

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level="info"
    )
