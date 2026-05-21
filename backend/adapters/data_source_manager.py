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

from adapters.base_adapter import BaseDataAdapter
from adapters.tdx_local_adapter import TdxLocalAdapter
from adapters.tdx_hq_adapter import TdxHQAdapter
from adapters.akshare_adapter import AKShareAdapter
from adapters.baostock_adapter import BaostockAdapter
from adapters.tushare_adapter import TushareAdapter
from config import settings
from cache.parquet_cache import ParquetCache

logger = logging.getLogger(__name__)


class DataSourceManager:
    """多数据源管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseDataAdapter] = {}
        self.cache = ParquetCache() if settings.CACHE_ENABLE else None
        self._init_adapters()
    
    def _init_adapters(self):
        """初始化数据源适配器"""
        # 数据源分类：
        #   实时行情: tdx_hq > tdx_local > akshare > baostock > tushare
        #   历史K线:  tdx_local > akshare > baostock > tushare > tdx_hq
        
        # 1. 通达信行情服务器（mootdx，盘中实时数据最高优先级，延迟连接）
        try:
            self.adapters['tdx_hq'] = TdxHQAdapter()
            logger.info("已注册通达信行情服务器适配器 (mootdx, 延迟连接)")
        except Exception as e:
            logger.warning(f"通达信行情服务器适配器注册失败: {e}")
        
        # 2. 通达信本地数据（本地文件，历史K线最高优先级）
        try:
            self.adapters['tdx_local'] = TdxLocalAdapter()
            if self.adapters['tdx_local'].connect():
                logger.info("已初始化通达信本地数据适配器")
        except Exception as e:
            logger.warning(f"通达信本地适配器初始化失败: {e}")
        
        # 3. AKShare（免费数据源）
        if settings.AKSHARE_ENABLE:
            self.adapters['akshare'] = AKShareAdapter()
        
        # 4. Baostock（免费数据源）
        if settings.BAOSTOCK_ENABLE:
            self.adapters['baostock'] = BaostockAdapter()
        
        # 5. Tushare（需要积分）
        if settings.TUSHARE_ENABLE:
            self.adapters['tushare'] = TushareAdapter()
        
        logger.info(f"已初始化 {len(self.adapters)} 个数据源: {list(self.adapters.keys())}")
    
    def connect_all(self) -> Dict[str, bool]:
        """
        连接所有数据源（tdx_hq 除外，其使用延迟连接）

        Returns:
            {数据源名: 是否成功}
        """
        results = {}
        for name, adapter in self.adapters.items():
            # tdx_hq 使用延迟连接（首次请求行情时才连服务器）
            if name == 'tdx_hq':
                results[name] = True  # 标记为已就绪（延迟连接）
                continue
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
        
        # 按优先级尝试各数据源（本地文件优先）
        for name in ['tdx_local', 'akshare', 'baostock', 'tushare']:
            if name in self.adapters:
                try:
                    adapter = self.adapters[name]
                    if not adapter.connected:
                        adapter.connect()
                    
                    df = adapter.get_stock_list()
                    if not df.empty:
                        logger.info(f"从 {name} 获取股票列表成功 ({len(df)} 只)")
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
        
        # 按优先级尝试各数据源（本地文件优先）
        for name in ['tdx_local', 'akshare', 'baostock', 'tushare']:
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
        """
        获取实时行情（多数据源兜底）

        优先级: tdx_hq(行情服务器,盘中实时) > tdx_local(本地文件) > akshare > baostock > tushare
        """
        if not codes:
            return pd.DataFrame()
        
        # 实时数据不使用缓存，按优先级尝试各数据源
        # tdx_hq 优先：直连通达信行情服务器获取盘中实时五档数据
        # tdx_local 兜底：非交易时间使用本地日K数据
        for name in ['tdx_hq', 'tdx_local', 'akshare', 'baostock', 'tushare']:
            if name in self.adapters:
                try:
                    adapter = self.adapters[name]
                    if not adapter.connected:
                        adapter.connect()
                    
                    df = adapter.get_realtime_quote(codes)
                    if not df.empty:
                        logger.info(f"从 {name} 获取实时行情成功 ({len(df)} 条)")
                        return df
                    else:
                        logger.debug(f"从 {name} 获取实时行情为空 (codes: {codes[:3]}...)，尝试下一个数据源")
                except Exception as e:
                    logger.warning(f"从 {name} 获取实时行情失败，尝试下一个数据源: {e}")
        
        logger.error(f"所有数据源均无法获取实时行情: {codes}")
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
