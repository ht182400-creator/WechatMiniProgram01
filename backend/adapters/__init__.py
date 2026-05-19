# -*- coding: utf-8 -*-
"""
数据源适配器模块
"""

from .base_adapter import BaseDataAdapter
from .akshare_adapter import AKShareAdapter
from .baostock_adapter import BaostockAdapter
from .tushare_adapter import TushareAdapter
from .data_source_manager import DataSourceManager, get_data_source_manager

__all__ = [
    'BaseDataAdapter',
    'AKShareAdapter',
    'BaostockAdapter',
    'TushareAdapter',
    'DataSourceManager',
    'get_data_source_manager'
]
