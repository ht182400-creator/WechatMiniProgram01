# -*- coding: utf-8 -*-
"""
数据源适配器基类
@author: StockQuant Team
@date: 2026-05-19
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime


class BaseDataAdapter(ABC):
    """数据源适配器抽象基类"""
    
    name: str = "Base"
    
    @abstractmethod
    def connect(self) -> bool:
        """连接数据源"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        pass
    
    @abstractmethod
    def get_daily_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取日线数据"""
        pass
    
    @abstractmethod
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """获取实时行情"""
        pass
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        try:
            return self.connect()
        except Exception:
            return False
    
    def validate_code(self, code: str) -> bool:
        """验证股票代码格式"""
        # A股格式: 600000, 000001, 300001, 920xxx(北交所)
        if len(code) == 6 and code.isdigit():
            return True
        return False

    @staticmethod
    def get_market(code: str) -> str:
        """根据股票代码判断所属市场

        Returns:
            'sh' - 上交所(6开头), 'sz' - 深交所(0/3开头), 'bj' - 北交所(8/920开头)
        """
        code = code.strip()
        if code.startswith('6'):
            return 'sh'
        elif code.startswith(('0', '3')):
            return 'sz'
        elif code.startswith(('8', '9')):
            return 'bj'
        # 兜底：无法识别的归为深交所
        return 'sz'
    
    def normalize_code(self, code: str) -> str:
        """标准化股票代码"""
        code = code.strip()
        if not code.isdigit():
            raise ValueError(f"无效的股票代码: {code}")
        return code
    
    def format_date(self, date: Any) -> str:
        """格式化日期"""
        if isinstance(date, str):
            return date
        elif isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date)
