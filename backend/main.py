# -*- coding: utf-8 -*-
"""
股票量化分析与预测系统 - 主应用入口
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings, init_directories
from models import db_manager
from adapters import get_data_source_manager
from api import stock, backtest, predict, system

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
    logger.info("股票量化分析与预测系统 V3.0 启动中...")
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
    
    logger.info("=" * 60)
    logger.info("系统启动完成!")
    logger.info("=" * 60)
    
    yield
    
    # 关闭时
    logger.info("系统关闭中...")
    data_manager.disconnect_all()
    logger.info("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="股票量化分析与预测系统 V3.0",
    description="""
## 系统概述
本系统提供股票数据采集、技术指标计算、策略回测和趋势预测功能。

## 架构特点
- **多数据源**：支持 AKShare、Baostock、Tushare 多源数据
- **本地缓存**：Parquet 格式缓存，提升查询性能
- **策略引擎**：支持多种量化策略的回测
- **预测模型**：基于机器学习的趋势预测

## 主要功能
- **股票数据**：实时行情、历史K线数据
- **技术指标**：MA、RSI、MACD、布林带等
- **策略回测**：MA金叉死叉、RSI、MACD、布林带策略
- **趋势预测**：基于机器学习的涨跌预测
- **舆情分析**：新闻情绪分析

## 免责声明
⚠️ **风险提示**：本系统仅供学习研究使用，预测结果仅供参考，
不构成任何投资建议。股票投资有风险，入市需谨慎！
    """,
    version="3.0.0",
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

# 注册路由
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(stock.router, prefix="/api/stock", tags=["股票数据"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["策略回测"])
app.include_router(predict.router, prefix="/api/predict", tags=["趋势预测"])


@app.get("/", tags=["首页"])
async def root():
    """系统首页"""
    return {
        "name": "股票量化分析与预测系统",
        "version": "3.0.0",
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
        "version": "3.0.0",
        "data_sources": {
            name: adapter.is_available() 
            for name, adapter in data_manager.adapters.items()
        },
        "cache_enabled": settings.CACHE_ENABLE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level="info"
    )
