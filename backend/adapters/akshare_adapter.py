# -*- coding: utf-8 -*-
"""
AKShare 数据源适配器
====================
提供 A 股行情、资金流向、概念板块、行业数据等免费数据。

数据能力矩阵（preparereadme.MD 5.5 资金与热点服务）：
  - 个股资金流向：stock_individual_fund_flow
  - 概念板块列表：stock_board_concept_name_em
  - 概念板块成分股：stock_board_concept_cons_em
  - 板块资金流向排行：stock_sector_fund_flow_rank

@author: StockQuant Team
@date: 2026-05-19
"""

import logging
import time
from typing import List, Optional, Dict, Any
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
            if df.empty:
                logger.warning("AKShare 返回空股票列表")
                return pd.DataFrame()
            # 防御性列名处理：取前两列作为 code 和 name（兼容不同AKShare版本）
            if len(df.columns) >= 2:
                df = df.iloc[:, :2].copy()
                df.columns = ['code', 'name']
            elif len(df.columns) == 1:
                df.columns = ['code']
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
            
            # 判断市场（上交所sh / 深交所sz / 北交所bj）
            market = self.get_market(code)
            symbol = f"{market}{code}"
            
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
        market = self.get_market(code)
        market_num = {'sh': '1', 'sz': '0', 'bj': '0'}
        return f"{market_num[market]}.{code}"
    
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

    # ============================================================
    # 资金流向与热点数据（preparereadme.MD 5.5）
    # ============================================================

    def get_fund_flow(self, code: str, days: int = 5) -> Dict[str, Any]:
        """
        获取个股资金流向（主力/超大单/大单/中单/小单净流入）

        Args:
            code: 股票代码，如 "600000"
            days: 返回最近 N 个交易日的数据，默认 5

        Returns:
            {
                'code': '600000',
                'history': [{日期, 主力净流入, 超大单净流入, ...}, ...],
                'summary': {近N日主力净流入合计, 近N日总成交额, ...}
            }
        """
        try:
            market = self.get_market(code)
            symbol = f"{market}{code}"
            # akshare 返回最近约100个交易日的资金流向
            df = self.ak.stock_individual_fund_flow(stock=code, market=market)
            time.sleep(0.3)  # 控制请求频率

            if df is None or df.empty:
                return {'code': code, 'error': '未获取到资金流向数据'}

            # 标准化列名
            rename_map = {}
            for col in df.columns:
                if '日期' in str(col):
                    rename_map[col] = 'date'
                elif '主力净流入' in str(col) and '净占比' not in str(col):
                    rename_map[col] = 'main_net_inflow'
                elif '超大单净流入' in str(col):
                    rename_map[col] = 'super_large_net_inflow'
                elif '大单净流入' in str(col):
                    rename_map[col] = 'large_net_inflow'
                elif '中单净流入' in str(col):
                    rename_map[col] = 'medium_net_inflow'
                elif '小单净流入' in str(col):
                    rename_map[col] = 'small_net_inflow'
                elif '收盘价' in str(col):
                    rename_map[col] = 'close'
                elif '涨跌幅' in str(col):
                    rename_map[col] = 'pct_change'

            df = df.rename(columns=rename_map)
            df = df.head(days)

            # 构造历史列表
            history = []
            keep_cols = ['date', 'main_net_inflow', 'super_large_net_inflow',
                         'large_net_inflow', 'medium_net_inflow', 'small_net_inflow',
                         'close', 'pct_change']
            for _, row in df.iterrows():
                entry = {}
                for c in keep_cols:
                    if c in df.columns:
                        val = row[c]
                        entry[c] = float(val) if pd.notna(val) and isinstance(val, (int, float)) else str(val)
                history.append(entry)

            # 汇总统计
            summary = {}
            if 'main_net_inflow' in df.columns:
                summary[f'近{days}日主力净流入合计'] = round(df['main_net_inflow'].sum(), 2)

            return {
                'code': code,
                'history': history,
                'summary': summary,
                'source': 'akshare'
            }
        except Exception as e:
            logger.error(f"获取资金流向失败 [{code}]: {e}")
            return {'code': code, 'error': str(e)}

    def get_concept_list(self) -> Dict[str, Any]:
        """
        获取概念板块列表

        Returns:
            {'concepts': ['人工智能', '芯片', ...], 'total': N}
        """
        try:
            df = self.ak.stock_board_concept_name_em()
            if df is None or df.empty:
                return {'concepts': [], 'total': 0, 'error': '未获取到概念列表'}

            concepts = df['板块名称'].tolist() if '板块名称' in df.columns else df.iloc[:, 0].tolist()
            return {
                'concepts': concepts,
                'total': len(concepts),
                'source': 'akshare'
            }
        except Exception as e:
            logger.error(f"获取概念板块列表失败: {e}")
            return {'concepts': [], 'total': 0, 'error': str(e)}

    def get_concept_stocks(self, concept_name: str) -> Dict[str, Any]:
        """
        获取指定概念板块的成分股

        Args:
            concept_name: 概念名称，如 "人工智能"

        Returns:
            {'concept': '人工智能', 'stocks': [{'code': '000001', 'name': '平安银行'}, ...]}
        """
        try:
            df = self.ak.stock_board_concept_cons_em(symbol=concept_name)
            if df is None or df.empty:
                return {'concept': concept_name, 'stocks': [], 'error': f'未找到概念 "{concept_name}" 的成分股'}

            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', ''))
                })

            return {
                'concept': concept_name,
                'stocks': stocks,
                'total': len(stocks),
                'source': 'akshare'
            }
        except Exception as e:
            logger.error(f"获取概念成分股失败 [{concept_name}]: {e}")
            return {'concept': concept_name, 'stocks': [], 'error': str(e)}

    def get_sector_fund_flow(self, indicator: str = "今日", top_n: int = 5) -> Dict[str, Any]:
        """
        获取板块资金流向排行（按主力净流入排序）

        Args:
            indicator: 指标类型，"今日"、"5日"、"10日"
            top_n: 返回前 N 个板块

        Returns:
            {'sectors': [...], 'indicator': '今日', 'total': N}
        """
        try:
            # akshare stock_sector_fund_flow_rank 仅支持 indicator 参数
            df = self.ak.stock_sector_fund_flow_rank(indicator=indicator)
            time.sleep(0.3)

            if df is None or df.empty:
                return {'sectors': [], 'indicator': indicator, 'error': '未获取到板块资金流向'}

            # 标准化列名
            rename_map = {}
            for col in df.columns:
                c = str(col)
                if '名称' in c:
                    rename_map[col] = 'name'
                elif '主力净流入' in c and '净占比' not in c:
                    rename_map[col] = 'main_net_inflow'
                elif '主力净流入' in c and '净占比' in c:
                    rename_map[col] = 'main_net_inflow_ratio'
                elif '涨跌幅' in c:
                    rename_map[col] = 'pct_change'
                elif '超大单' in c:
                    rename_map[col] = 'super_large_inflow'
                elif '大单' in c:
                    rename_map[col] = 'large_inflow'

            df = df.rename(columns=rename_map)
            keep_cols = ['name', 'main_net_inflow', 'main_net_inflow_ratio', 'pct_change', 'super_large_inflow', 'large_inflow']

            sectors = []
            for _, row in df.head(top_n).iterrows():
                sector_data = {}
                for c in keep_cols:
                    if c in df.columns:
                        val = row[c]
                        try:
                            if pd.isna(val):
                                continue
                            # iterrows 返回的 value 可能是 np.generic，需要安全转换
                            if hasattr(val, 'item'):  # numpy scalar
                                val = val.item()
                            sector_data[c] = float(val) if isinstance(val, (int, float)) else str(val)
                        except (TypeError, ValueError):
                            continue
                if sector_data.get('name'):
                    sectors.append(sector_data)

            return {
                'indicator': indicator,
                'sectors': sectors,
                'total': len(sectors),
                'source': 'akshare'
            }
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {e}")
            return {'sectors': [], 'indicator': indicator, 'error': str(e)}
