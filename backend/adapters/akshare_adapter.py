# -*- coding: utf-8 -*-
"""
AKShare 数据源适配器
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta

from .base_adapter import BaseDataAdapter

logger = logging.getLogger(__name__)


class AKShareAdapter(BaseDataAdapter):
    """AKShare 数据源适配器"""
    
    name = "AKShare"
    
    def __init__(self):
        self.connected = False
    
    def connect(self) -> bool:
        """连接AKShare数据源"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True
            logger.info("AKShare 数据源连接成功")
            return True
        except ImportError:
            logger.error("请安装 akshare: pip install akshare")
            return False
        except Exception as e:
            logger.error(f"AKShare 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info("AKShare 数据源已断开")
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            df = self.ak.stock_info_a_code_name()
            df.columns = ['code', 'name']
            df['source'] = 'akshare'
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
            
            # 判断市场
            if code.startswith('6'):
                symbol = f"sh{code}"
            else:
                symbol = f"sz{code}"
            
            df = self.ak.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust=adjust
            )
            
            if df is not None and not df.empty:
                df = df.rename(columns={
                    '日期': 'date',
                    '股票代码': 'code',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
            
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败 [{code}]: {e}")
            return pd.DataFrame()
    
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """获取实时行情"""
        try:
            if not codes:
                return pd.DataFrame()
            
            codes_str = ','.join([self._format_realtime_code(c) for c in codes])
            df = self.ak.stock_zh_a_spot_em()
            
            if df is not None and not df.empty:
                df = df[df['代码'].isin(codes)]
                df = df.rename(columns={
                    '代码': 'code',
                    '名称': 'name',
                    '最新价': 'close',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '最高': 'high',
                    '最低': 'low',
                    '今开': 'open',
                    '昨收': 'pre_close',
                    '量比': 'volume_ratio',
                    '换手率': 'turnover',
                    '市盈率-动态': 'pe',
                    '市净率': 'pb',
                    '总市值': 'total_market_cap',
                    '流通市值': 'float_market_cap'
                })
            
            return df
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return pd.DataFrame()
    
    def _format_realtime_code(self, code: str) -> str:
        """格式化实时行情股票代码"""
        code = self.normalize_code(code)
        if code.startswith('6'):
            return f"1.{code}"  # 上海
        else:
            return f"0.{code}"  # 深圳
    
    def get_index_data(self, code: str = "000001", start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """获取指数数据"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            
            df = self.ak.stock_zh_index_daily_em(
                symbol=f"sh{code}" if code.startswith('0') or code.startswith('9') else f"sz{code}"
            )
            
            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            return df
        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            return pd.DataFrame()
