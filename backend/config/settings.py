# -*- coding: utf-8 -*-
"""
系统配置文件
@author: StockQuant Team
@date: 2026-05-19
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """系统配置类"""
    
    # ==================== 项目路径配置 ====================
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOG_DIR: Path = BASE_DIR / "logs"
    MODEL_DIR: Path = BASE_DIR / "models"
    
    # ==================== 数据库配置 ====================
    DATABASE_URL: str = "sqlite:///./data/stock_quant.db"
    
    # ==================== 数据源配置 ====================
    # AKShare (默认主数据源，免费)
    AKSHARE_ENABLE: bool = True
    
    # Baostock (备用数据源，免费)
    BAOSTOCK_ENABLE: bool = True
    
    # Tushare (需要Token，高频数据需付费)
    TUSHARE_ENABLE: bool = True
    TUSHARE_TOKEN: str = "818c2bf8f8c77b0cafc80d88a05b7741ca9afe324ff5a79750a32879"
    
    # ==================== 缓存配置 ====================
    CACHE_ENABLE: bool = True
    CACHE_EXPIRE_MINUTES: int = 30  # 缓存过期时间(分钟)
    CACHE_MAX_SIZE: int = 500  # 缓存最大条目数
    
    # ==================== 回测配置 ====================
    BACKTEST_COMMISSION: float = 0.0003  # 手续费 0.03%
    BACKTEST_SLIPPAGE: float = 0.0001   # 滑点 0.01%
    BACKTEST_INITIAL_CASH: float = 100000.0  # 初始资金 10万
    
    # ==================== 模型配置 ====================
    MODEL_LOOKBACK_DAYS: int = 60  # 模型回看天数
    MODEL_PREDICT_DAYS: int = 5   # 预测天数
    MODEL_UPDATE_FREQ: str = "weekly"  # 模型更新频率
    
    # ==================== API服务配置 ====================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_WORKERS: int = 1
    
    # ==================== CORS配置 ====================
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 创建必要的目录
def init_directories():
    """初始化项目目录结构"""
    settings = get_settings()
    for dir_path in [settings.DATA_DIR, settings.CACHE_DIR, settings.LOG_DIR, settings.MODEL_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = get_settings()
