# -*- coding: utf-8 -*-
"""
通达信本地数据适配器
直接从通达信安装目录读取本地K线数据文件
@author: StockQuant Team
@date: 2026-05-21
"""

import os
import struct
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np

from adapters.base_adapter import BaseDataAdapter

logger = logging.getLogger(__name__)


class TdxLocalAdapter(BaseDataAdapter):
    """
    通达信本地数据适配器
    
    数据目录结构：
    - {TdxPath}/vipdoc/sh/lday/  - 上海日K线 (.day文件)
    - {TdxPath}/vipdoc/sz/lday/  - 深圳日K线 (.day文件)
    - {TdxPath}/vipdoc/sh/minline/ - 上海分钟线
    - {TdxPath}/vipdoc/sz/minline/ - 深圳分钟线
    
    .day 文件格式（每条32字节，小端序）：
    - 4字节：日期（YYYYMMDD 整数，如 19991110）
    - 4字节：开盘价（单位：分 = 元 * 100）
    - 4字节：最高价（单位：分）
    - 4字节：最低价（单位：分）
    - 4字节：收盘价（单位：分）
    - 4字节：成交量（股）
    - 4字节：成交额（元）
    """
    
    name = "tdx_local"
    
    # 通达信基准日期：1899-12-30
    TDx_BASE_DATE = datetime(1899, 12, 30)
    
    def __init__(self, tdx_path: str = None):
        """
        初始化通达信本地适配器
        
        Args:
            tdx_path: 通达信安装目录，默认使用 D:\\new_tdx64
        """
        self.tdx_path = tdx_path or r"D:\new_tdx64"
        self.connected = False
        self._day_cache: Dict[str, pd.DataFrame] = {}
        self._stock_info_cache: Optional[pd.DataFrame] = None
        
    def connect(self) -> bool:
        """连接数据源（检查目录是否存在）"""
        try:
            base_path = Path(self.tdx_path)
            if not base_path.exists():
                logger.error(f"通达信目录不存在: {self.tdx_path}")
                return False
            
            # 检查关键目录
            vipdoc = base_path / "vipdoc"
            if not vipdoc.exists():
                logger.error(f"通达信 vipdoc 目录不存在")
                return False
            
            self.connected = True
            logger.info(f"通达信本地数据适配器连接成功: {self.tdx_path}")
            return True
        except Exception as e:
            logger.error(f"连接通达信失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        self._day_cache.clear()
        logger.info("通达信本地适配器已断开")
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self.connect()
    
    def _get_day_file_path(self, code: str) -> Optional[Path]:
        """
        获取股票日K线文件路径
        
        Args:
            code: 股票代码，如 600000, 000001
            
        Returns:
            文件路径，不存在则返回 None
        """
        if not self.validate_code(code):
            return None
        
        market = self.get_market(code)
        
        # 通达信文件命名规则：小写市场前缀 + 股票代码
        filename = f"{market}{code}.day"
        
        paths = [
            Path(self.tdx_path) / "vipdoc" / market / "lday" / filename,
            Path(self.tdx_path) / "vipdoc" / market / "minline" / filename.replace('.day', '.lc1'),
        ]
        
        for p in paths:
            if p.exists():
                return p
        
        return None
    
    def _parse_tdx_date(self, date_int: int) -> datetime:
        """解析通达信日期格式（YYYYMMDD 整数格式）"""
        year = date_int // 10000
        month = (date_int // 100) % 100
        day = date_int % 100
        return datetime(year, month, day)
    
    def _read_day_file(self, file_path: Path) -> pd.DataFrame:
        """
        读取通达信 .day 文件
        
        Args:
            file_path: .day 文件路径
            
        Returns:
            DataFrame 包含日期、开盘、最高、收盘、最低价、成交量、成交额
        """
        records = []
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(32)  # 每条记录32字节
                if len(data) < 32:
                    break
                
                try:
                    # 解包数据（小端序）
                    # 日期(4字节int) + 5个价格(各4字节int) + 成交量(4字节int) + 成交额(4字节int)
                    date_int, open_p, high, low, close, volume, amount = struct.unpack('<IIIIIII', data[:28])
                    
                    # 转换为实际价格（元）
                    records.append({
                        'date': self._parse_tdx_date(date_int),
                        'open': open_p / 100.0,
                        'high': high / 100.0,
                        'low': low / 100.0,
                        'close': close / 100.0,
                        'volume': volume,
                        'amount': amount / 100.0,  # 成交额单位是元
                    })
                except struct.error as e:
                    logger.warning(f"解析 {file_path.name} 失败: {e}")
                    continue
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        从通达信目录获取股票列表
        
        Returns:
            DataFrame 包含 code, name, market 字段
        """
        if self._stock_info_cache is not None:
            return self._stock_info_cache
        
        stocks = []
        
        for market in ['sh', 'sz']:
            lday_dir = Path(self.tdx_path) / "vipdoc" / market / "lday"
            if not lday_dir.exists():
                continue
            
            for file in lday_dir.glob("*.day"):
                filename = file.stem  # 如 'sh600000' 或 'sz000001'
                market_prefix = filename[:2]
                code = filename[2:]
                
                if len(code) == 6 and code.isdigit():
                    stocks.append({
                        'code': code,
                        'market': market,
                        'name': self._get_stock_name_from_code(code, market),
                        'source': 'tdx_local'
                    })
        
        df = pd.DataFrame(stocks)
        self._stock_info_cache = df
        
        logger.info(f"从通达信本地获取 {len(df)} 只股票")
        return df
    
    def _get_stock_name_from_code(self, code: str, market: str) -> str:
        """根据代码获取股票名称（如果有缓存数据）"""
        # 尝试从数据文件读取最近一条记录来判断
        # 实际名称需要从其他来源获取，这里返回代码作为占位
        return code
    
    def get_daily_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取日K线数据
        
        Args        code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型（本地数据不复权）
            
        Returns:
            DataFrame 包含 date, open, high, low, close, volume, amount
        """
        if not self.validate_code(code):
            logger.warning(f"无效的股票代码: {code}")
            return pd.DataFrame()
        
        # 检查缓存
        cache_key = f"{code}_{start_date}_{end_date}"
        if cache_key in self._day_cache:
            df = self._day_cache[cache_key]
        else:
            file_path = self._get_day_file_path(code)
            if file_path is None:
                logger.warning(f"找不到 {code} 的数据文件")
                return pd.DataFrame()
            
            df = self._read_day_file(file_path)
            
            # 缓存完整数据
            self._day_cache[code] = df
        
        if df.empty:
            return df
        
        # 按日期筛选
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
        return df[mask].copy()
    
    def get_minute_data(
        self, 
        code: str, 
        period: int = 5
    ) -> pd.DataFrame:
        """
        获取分钟K线数据
        
        Args:
            code: 股票代码
            period: 周期（1, 5, 15, 30, 60），默认5分钟
            
        Returns:
            DataFrame 包含 datetime, open, high, low, close, volume
        """
        if not self.validate_code(code):
            return pd.DataFrame()
        
        market = self.get_market(code)
        
        # 通达信分钟文件命名规则
        period_map = {1: '.lc', 5: '.lc1', 15: '.lc5', 30: '.lc3', 60: '.lc6'}
        ext = period_map.get(period, '.lc1')
        filename = f"{market}{code}{ext}"
        
        file_path = Path(self.tdx_path) / "vipdoc" / market / "minline" / filename
        
        if not file_path.exists():
            logger.warning(f"找不到 {filename} 文件")
            return pd.DataFrame()
        
        # 分钟数据每条32字节，格式与日K类似
        return self._read_minute_file(file_path)
    
    def _read_minute_file(self, file_path: Path) -> pd.DataFrame:
        """读取通达信分钟数据文件"""
        records = []
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(32)
                if len(data) < 32:
                    break
                
                try:
                    # 分钟数据格式
                    # 4字节：日期
                    # 4字节：时间（HHMM）
                    # 4字节：开盘
                    # 4字节：最高
                    # 4字节：最低
                    # 4字节：收盘
                    # 4字节：成交量
                    # 4字节：成交额（有时是保留字段）
                    date_int, time_int, open_p, high, low, close, volume, _ = struct.unpack('<IIIIIII', data)
                    
                    date = self._parse_tdx_date(date_int)
                    hour = time_int // 100
                    minute = time_int % 100
                    
                    records.append({
                        'datetime': date.replace(hour=hour, minute=minute),
                        'date': date,
                        'time': f"{hour:02d}:{minute:02d}",
                        'open': open_p / 100.,
                        'high': high / 100.0,
                        'low': low / 100.0,
                        'close': close / 100.0,
                        'volume': volume,
                    })
                except struct.error:
                    continue
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df = df.sort_values('datetime').reset_index(drop=True)
        return df
    
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """
        获取实时行情（从通达信本地文件获取最后一条）
        注意：本地文件只能获取日末行情，无法获取盘中实时数据
        
        Args:
            codes: 股票代码列表
            
        Returns:
            DataFrame 包含最新日K数据作为"实时"行情
        """
        results = []
        
        for code in codes:
            # 获取今日数据（如果有）
            today = datetime.now().strftime("%Y-%m-%d")
            df = self.get_daily_data(code, today, today)
            
            if not df.empty:
                row = df.iloc[-1].to_dict()
                row['code'] = code
                row['name'] = self._get_stock_name_from_code(code, self.get_market(code))
                results.append(row)
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        return df
    
    def get_depth_data(self, code: str) -> pd.DataFrame:
        """
        获取盘口数据（本地文件不支持，返回空）
        
        Args:
            code: 股票代码
            
        Returns:
            空 DataFrame
        """
        # 通达信本地文件不包含盘口数据
        return pd.DataFrame()
    
    def get_transaction_data(self, code: str, limit: int = 100) -> pd.DataFrame:
        """
        获取分笔成交数据（本地文件不支持，返回空）
        
        Args:
            code: 股票代码
            limit: 返回条数
            
        Returns:
            空 DataFrame
        """
        # 通达信本地文件不包含分笔成交数据
        return pd.DataFrame()
