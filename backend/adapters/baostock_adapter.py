# -*- coding: utf-8 -*-
"""
Baostock 数据源适配器
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List
import pandas as pd
import baostock as bs

from .base_adapter import BaseDataAdapter

logger = logging.getLogger(__name__)


class BaostockAdapter(BaseDataAdapter):
    """Baostock 数据源适配器"""
    
    name = "Baostock"
    
    def __init__(self):
        self.connected = False
        self.login_result = None
    
    def connect(self) -> bool:
        """连接Baostock数据源"""
        try:
            self.login_result = bs.login()
            if self.login_result.error_code == '0':
                self.connected = True
                logger.info("Baostock 数据源连接成功")
                return True
            else:
                logger.error(f"Baostock 登录失败: {self.login_result.error_msg}")
                return False
        except ImportError:
            logger.error("请安装 baostock: pip install baostock")
            return False
        except Exception as e:
            logger.error(f"Baostock 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            bs.logout()
            self.connected = False
            logger.info("Baostock 数据源已断开")
        except Exception as e:
            logger.error(f"Baostock 断开失败: {e}")
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        try:
            rs = bs.query_all_stock()
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            df.columns = ['code', 'name', 'ipo_date', 'out_date', 'stock_type']
            df = df[df['stock_type'].isin(['1', '2'])]  # 1=上交所, 2=深交所
            df['source'] = 'baostock'
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
            # Baostock格式: sh.600000 / sz.000001 / bj.920119
            market = self.get_market(code)
            bs_code = f"{market}.{code}"
            
            # adjust: 2=前复权, 1=后复权, 0=不复权
            adjust_map = {"qfq": "2", "hfq": "1", "none": "0"}
            adjust_type = adjust_map.get(adjust, "2")
            
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,adjustflag",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag=adjust_type
            )
            
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            
            if data_list:
                df = pd.DataFrame(data_list, columns=rs.fields)
                df['date'] = pd.to_datetime(df['date'])
                df['code'] = code
                df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                df['open'] = pd.to_numeric(df['open'], errors='coerce')
                df['high'] = pd.to_numeric(df['high'], errors='coerce')
                df['low'] = pd.to_numeric(df['low'], errors='coerce')
                
                # 计算涨跌
                df['change'] = df['close'].diff()
                df['pct_change'] = df['close'].pct_change() * 100
                
                df = df.sort_values('date').reset_index(drop=True)
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取日线数据失败 [{code}]: {e}")
            return pd.DataFrame()
    
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """获取实时行情 - Baostock不直接支持，需使用其他方式"""
        logger.warning("Baostock 不支持实时行情查询，建议使用 AKShare")
        return pd.DataFrame()
