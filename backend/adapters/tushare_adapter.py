# -*- coding: utf-8 -*-
"""
Tushare 数据源适配器
====================
提供 A 股行情、资金流向、机构持仓、研报评级等专业数据。

数据能力矩阵（preparereadme.MD 5.4 & 5.5）：
  - 个股资金流向：moneyflow（主力/散户净流入）
  - 前十大股东：top10_holders
  - 机构研报：report_rc（评级、目标价）

@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta

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

    # ============================================================
    # 资金流向与机构数据（preparereadme.MD 5.4 & 5.5）
    # ============================================================

    def _to_ts_code(self, code: str) -> str:
        """将 6 位代码转为 tushare 格式: 600000.SH"""
        code = self.normalize_code(code)
        market = self.get_market(code)
        suffix = {'sh': '.SH', 'sz': '.SZ', 'bj': '.BJ'}
        return f"{code}{suffix[market]}"

    def get_moneyflow(self, code: str, days: int = 5) -> Dict[str, Any]:
        """
        获取个股资金流向（主力净流入、超大单、大单、中单、小单）

        Args:
            code: 股票代码
            days: 最近 N 个交易日

        Returns:
            {'code': '600000', 'history': [...], 'summary': {...}}
        """
        try:
            ts_code = self._to_ts_code(code)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days * 3 + 30)).strftime('%Y%m%d')

            df = self.api.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                return {'code': code, 'error': '未获取到资金流向数据'}

            df = df.sort_values('trade_date', ascending=False).head(days)

            history = []
            col_map = {
                'trade_date': 'date',
                'buy_sm_vol': 'small_buy_vol',
                'buy_md_vol': 'medium_buy_vol',
                'buy_lg_vol': 'large_buy_vol',
                'buy_elg_vol': 'super_large_buy_vol',
                'sell_sm_vol': 'small_sell_vol',
                'sell_md_vol': 'medium_sell_vol',
                'sell_lg_vol': 'large_sell_vol',
                'sell_elg_vol': 'super_large_sell_vol',
                'net_mf_vol': 'main_net_inflow_vol',
                'net_mf_amount': 'main_net_inflow_amount',
            }

            for _, row in df.iterrows():
                entry = {}
                for old_k, new_k in col_map.items():
                    if old_k in df.columns:
                        val = row[old_k]
                        entry[new_k] = float(val) if pd.notna(val) else 0
                history.append(entry)

            summary = {}
            if 'net_mf_amount' in df.columns:
                summary[f'近{days}日主力净流入金额合计(万元)'] = round(float(df['net_mf_amount'].sum()), 2)

            return {
                'code': code,
                'history': history,
                'summary': summary,
                'source': 'tushare'
            }
        except Exception as e:
            logger.error(f"获取Tushare资金流向失败 [{code}]: {e}")
            return {'code': code, 'error': str(e)}

    def get_top10_holders(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取前十大股东/流通股东

        Args:
            code: 股票代码
            report_date: 报告期 YYYYMMDD，默认最新

        Returns:
            {'code': '600000', 'top_holders': [...], 'top_float_holders': [...]}
        """
        try:
            ts_code = self._to_ts_code(code)
            if not report_date:
                report_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')

            # 前十大股东
            top10 = self.api.top10_holders(ts_code=ts_code, period=report_date)
            top_holders = []
            if top10 is not None and not top10.empty:
                row = top10.iloc[0] if len(top10) > 0 else None
                if row is not None:
                    for i in range(1, 11):
                        name_col = f'holder{i}_name'
                        ratio_col = f'holder{i}_ratio'
                        if name_col in top10.columns:
                            name = row.get(name_col, '')
                            ratio = row.get(ratio_col, None)
                            if pd.notna(name) and name:
                                top_holders.append({
                                    'rank': i,
                                    'name': str(name),
                                    'ratio': float(ratio) if pd.notna(ratio) else None
                                })

            # 前十大流通股东
            float_top10 = self.api.top10_floatholders(ts_code=ts_code, period=report_date)
            top_float_holders = []
            if float_top10 is not None and not float_top10.empty:
                row = float_top10.iloc[0] if len(float_top10) > 0 else None
                if row is not None:
                    for i in range(1, 11):
                        name_col = f'holder{i}_name'
                        ratio_col = f'holder{i}_ratio'
                        if name_col in float_top10.columns:
                            name = row.get(name_col, '')
                            ratio = row.get(ratio_col, None)
                            if pd.notna(name) and name:
                                top_float_holders.append({
                                    'rank': i,
                                    'name': str(name),
                                    'ratio': float(ratio) if pd.notna(ratio) else None
                                })

            return {
                'code': code,
                'report_date': report_date,
                'top_holders': top_holders,
                'top_float_holders': top_float_holders,
                'source': 'tushare'
            }
        except Exception as e:
            logger.error(f"获取前十大股东失败 [{code}]: {e}")
            return {'code': code, 'error': str(e)}

    def get_research_report(self, code: str, limit: int = 10) -> Dict[str, Any]:
        """
        获取机构研报（最新评级、目标价）

        Args:
            code: 股票代码
            limit: 最多返回几篇

        Returns:
            {'code': '600000', 'reports': [...]}
        """
        try:
            ts_code = self._to_ts_code(code)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            df = self.api.report_rc(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                return {'code': code, 'reports': [], 'error': '未获取到研报数据'}

            # 按公告日期排序（report_rc 接口可能用 ann_date 或 report_date）
            sort_col = 'ann_date' if 'ann_date' in df.columns else df.columns[0]
            df = df.sort_values(sort_col, ascending=False).head(limit)

            # 动态映射可用列名
            col_map = {
                'ann_date': 'date',
                'report_date': 'date',
                'org_name': 'org',
                'author': 'author',
                'title': 'title',
                'rating': 'rating',
                'target_price': 'target_price',
            }

            reports = []
            for _, row in df.iterrows():
                rpt = {}
                for old_k, new_k in col_map.items():
                    if old_k in df.columns:
                        val = row[old_k]
                        if pd.notna(val):
                            rpt[new_k] = float(val) if isinstance(val, (int, float)) else str(val)
                if rpt:  # 至少有一个字段才添加
                    reports.append(rpt)

            return {
                'code': code,
                'reports': reports,
                'total': len(reports),
                'source': 'tushare'
            }
        except Exception as e:
            logger.error(f"获取研报失败 [{code}]: {e}")
            return {'code': code, 'reports': [], 'error': str(e)}
