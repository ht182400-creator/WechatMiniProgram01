# -*- coding: utf-8 -*-
"""
Tushare 数据源适配器
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional
import pandas as pd
from datetime import datetime

from adapters.base_adapter import BaseDataAdapter
from config import settings

logger = logging.getLogger(__name__)


class TushareAdapter(BaseDataAdapter):
    """Tushare 数据源适配器"""
    
    name = "Tushare"
    
    def __init__(self, token: Optional[str] = None):
        self.connected = False
        self.token = token or settings.TUSHARE_TOKEN
        self.api = None
    
    def connect(self) -> bool:
        """连接Tushare数据源"""
        if not self.token:
            logger.warning("未设置 Tushare Token，请设置 TUSHARE_TOKEN 环境变量")
            return False
        
        try:
            import tushare as ts
            self.api = ts.pro_api(self.token)
            self.connected = True
            logger.info("Tushare 数据源连接成功")
            return True
        except ImportError:
            logger.error("请安装 tushare: pip install tushare")
            return False
        except Exception as e:
            logger.error(f"Tushare 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        self.api = None
        logger.info("Tushare 数据源已断开")
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        try:
            df = self.api.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            
            if df is not None and not df.empty:
                df = df.rename(columns={
                    'ts_code': 'code',
                    'name': 'name'
                })
                df['source'] = 'tushare'
                logger.info(f"获取到 {len(df)} 只股票")
            
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取日线数据"""
        try:
            code = self.normalize_code(code)
            # Tushare格式: 600000.SH / 000001.SZ / 920119.BJ
            market = self.get_market(code)
            market_suffix = {'sh': '.SH', 'sz': '.SZ', 'bj': '.BJ'}
            ts_code = f"{code}{market_suffix[market]}"
            
            # adjust: qfq=前复权, hfq=后复权
            df = self.api.pro_bar(
                ts_code=ts_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adj=adjust
            )
            
            if df is not None and not df.empty:
                df = df.rename(columns={
                    'trade_date': 'date',
                    'ts_code': 'code',
                    'vol': 'volume'
                })
                df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                df = df.sort_values('date').reset_index(drop=True)
            
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败 [{code}]: {e}")
            return pd.DataFrame()
    
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """获取实时行情"""
        try:
            import tushare as ts
            if not codes:
                return pd.DataFrame()
            
            codes_str = ','.join([f"{c}.SH" if c.startswith('6') else f"{c}.SZ" if c.startswith(('0', '3')) else f"{c}.BJ" for c in codes])
            df = ts.realtime_quote(ts_code=codes_str)
            
            if df is not None and not df.empty:
                df['code'] = df['code'].str.replace(r'\.SH|\.SZ', '', regex=True)
            
            return df
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return pd.DataFrame()
