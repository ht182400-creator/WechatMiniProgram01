# -*- coding: utf-8 -*-
"""
基本面因子模块
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class FundamentalFactors:
    """基本面因子计算"""
    
    def __init__(self, data: Optional[pd.DataFrame] = None, finance_data: Optional[Dict] = None):
        """
        初始化基本面因子计算器
        
        Args:
            data: 价格数据
            finance_data: 财务数据字典
        """
        self.data = data
        self.finance_data = finance_data or {}
    
    def calculate_valuation(self, code: str) -> Dict:
        """计算估值指标"""
        price_data = self.data.tail(1) if self.data is not None else None
        finance = self.finance_data.get(code, {})
        
        # 获取最新价格
        current_price = price_data['close'].iloc[-1] if price_data is not None and not price_data.empty else 0
        
        return {
            'pe_ratio': finance.get('pe_ratio'),        # 市盈率
            'pb_ratio': finance.get('pb_ratio'),         # 市净率
            'ps_ratio': finance.get('ps_ratio'),         # 市销率
            'pcf_ratio': finance.get('pcf_ratio'),       # 市现率
            'market_cap': finance.get('total_market_cap'),  # 总市值
            'float_market_cap': finance.get('float_market_cap'),  # 流通市值
        }
    
    def calculate_growth(self, code: str) -> Dict:
        """计算成长性指标"""
        finance = self.finance_data.get(code, {})
        
        return {
            'revenue_growth': finance.get('revenue_growth'),    # 营收增长率
            'profit_growth': finance.get('profit_growth'),      # 利润增长率
            'roe': finance.get('roe'),                         # 净资产收益率
            'gross_margin': finance.get('gross_margin'),        # 毛利率
            'net_margin': finance.get('net_margin'),            # 净利率
        }
    
    def calculate_financial_health(self, code: str) -> Dict:
        """计算财务健康指标"""
        finance = self.finance_data.get(code, {})
        
        return {
            'current_ratio': finance.get('current_ratio'),      # 流动比率
            'quick_ratio': finance.get('quick_ratio'),        # 速动比率
            'debt_ratio': finance.get('debt_ratio'),           # 资产负债率
            'cash_ratio': finance.get('cash_ratio'),          # 现金比率
        }
    
    def calculate_operation(self, code: str) -> Dict:
        """计算运营指标"""
        finance = self.finance_data.get(code, {})
        
        return {
            'inventory_turnover': finance.get('inventory_turnover'),  # 存货周转率
            'asset_turnover': finance.get('asset_turnover'),        # 资产周转率
            'receivable_turnover': finance.get('receivable_turnover'),  # 应收账款周转率
        }
    
    def get_all_factors(self, code: str) -> Dict:
        """获取所有基本面因子"""
        return {
            **self.calculate_valuation(code),
            **self.calculate_growth(code),
            **self.calculate_financial_health(code),
            **self.calculate_operation(code)
        }
