# -*- coding: utf-8 -*-
"""
数据源适配器模块
"""

from .base_adapter import BaseDataAdapter
from .tdx_local_adapter import TdxLocalAdapter
from .tdx_hq_adapter import TdxHQAdapter
from .akshare_adapter import AKShareAdapter
from .baostock_adapter import BaostockAdapter
from .tushare_adapter import TushareAdapter
from .data_source_manager import DataSourceManager, get_data_source_manager

__all__ = [
    'BaseDataAdapter',
    'TdxLocalAdapter',
    'TdxHQAdapter',
    'AKShareAdapter',
    'BaostockAdapter',
    'TushareAdapter',
    'DataSourceManager',
    'get_data_source_manager'
]
