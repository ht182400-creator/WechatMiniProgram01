# -*- coding: utf-8 -*-
"""
数据源管理器 - 统一调度多数据源
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict, Any
from functools import wraps
import pandas as pd

from .base_adapter import BaseDataAdapter
from .akshare_adapter import AKShareAdapter
from .baostock_adapter import BaostockAdapter
from .tushare_adapter import TushareAdapter
from ..config import settings
from ..cache.parquet_cache import ParquetCache

logger = logging.getLogger(__name__)


class DataSourceManager:
    """多数据源管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseDataAdapter] = {}
        self.cache = ParquetCache() if settings.CACHE_ENABLE else None
        self._init_adapters()
    
    def _init_adapters(self):
        """初始化数据源适配器"""
        # 按优先级排序
        if settings.AKSHARE_ENABLE:
            self.adapters['akshare'] = AKShareAdapter()
        
        if settings.BAOSTOCK_ENABLE:
            self.adapters['baostock'] = BaostockAdapter()
        
        if settings.TUSHARE_ENABLE:
            self.adapters['tushare'] = TushareAdapter()
        
        logger.info(f"已初始化 {len(self.adapters)} 个数据源: {list(self.adapters.keys())}")
    
    def connect_all(self) -> Dict[str, bool]:
        """连接所有数据源"""
        results = {}
        for name, adapter in self.adapters.items():
            try:
                results[name] = adapter.connect()
            except Exception as e:
                logger.error(f"连接 {name} 失败: {e}")
                results[name] = False
        return results
    
    def disconnect_all(self):
        """断开所有数据源"""
        for adapter in self.adapters.values():
            try:
                adapter.disconnect()
            except Exception as e:
                logger.error(f"断开适配器失败: {e}")
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        parts = [method]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")
        return "/".join(parts)
    
    def _get_data_with_cache(self, cache_key: str, fetch_func, **kwargs):
        """从缓存或数据源获取数据"""
        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_data
        
        # 从数据源获取
        data = fetch_func(**kwargs)
        
        # 保存到缓存
        if self.cache and not data.empty:
            self.cache.set(cache_key, data)
        
        return data
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表（多数据源兜底）"""
        cache_key = self._get_cache_key("stock_list")
        
        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        # 按优先级尝试各数据源
        for name in ['akshare', 'baostock', 'tushare']:
            if name in self.adapters:
                try:
                    adapter = self.adapters[name]
                    if not adapter.connected:
                        adapter.connect()
                    
                    df = adapter.get_stock_list()
                    if not df.empty:
                        logger.info(f"从 {name} 获取股票列表成功")
                        if self.cache:
                            self.cache.set(cache_key, df)
                        return df
                except Exception as e:
                    logger.warning(f"从 {name} 获取失败，尝试下一个数据源: {e}")
        
        return pd.DataFrame()
    
    def get_daily_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取日线数据（多数据源兜底）"""
        cache_key = self._get_cache_key("daily", code=code, start=start_date, end=end_date, adjust=adjust)
        
        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_data
        
        # 按优先级尝试各数据源
        for name in ['akshare', 'baostock', 'tushare']:
            if name in self.adapters:
                try:
                    adapter = self.adapters[name]
                    if not adapter.connected:
                        adapter.connect()
                    
                    df = adapter.get_daily_data(code, start_date, end_date, adjust)
                    if not df.empty:
                        logger.info(f"从 {name} 获取 {code} 日线数据成功 ({len(df)} 条)")
                        if self.cache:
                            self.cache.set(cache_key, df)
                        return df
                except Exception as e:
                    logger.warning(f"从 {name} 获取 {code} 失败，尝试下一个数据源: {e}")
        
        return pd.DataFrame()
    
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """获取实时行情（优先使用 AKShare）"""
        if not codes:
            return pd.DataFrame()
        
        # 实时数据不使用缓存
        if 'akshare' in self.adapters:
            try:
                adapter = self.adapters['akshare']
                if not adapter.connected:
                    adapter.connect()
                return adapter.get_realtime_quote(codes)
            except Exception as e:
                logger.error(f"获取实时行情失败: {e}")
        
        return pd.DataFrame()
    
    def is_healthy(self) -> bool:
        """检查数据源健康状态"""
        return any(adapter.is_available() for adapter in self.adapters.values())


# 全局数据源管理器实例
_data_source_manager: Optional[DataSourceManager] = None


def get_data_source_manager() -> DataSourceManager:
    """获取数据源管理器单例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager
