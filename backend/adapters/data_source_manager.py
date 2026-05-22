# -*- coding: utf-8 -*-
"""
数据源管理器 - 统一调度多数据源
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict, Any
from functools import wraps
import pandas as pd

from adapters.base_adapter import BaseDataAdapter
from adapters.tdx_local_adapter import TdxLocalAdapter
from adapters.tdx_hq_adapter import TdxHQAdapter
from adapters.tdx_finance_adapter import TdxFinanceAdapter
from adapters.akshare_adapter import AKShareAdapter
from adapters.baostock_adapter import BaostockAdapter
from adapters.tushare_adapter import TushareAdapter
from config import settings
from cache.parquet_cache import ParquetCache

logger = logging.getLogger(__name__)


class DataSourceManager:
    """多数据源管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseDataAdapter] = {}
        self.cache = ParquetCache() if settings.CACHE_ENABLE else None
        self._init_adapters()
    
    def _init_adapters(self):
        """初始化数据源适配器"""
        # 数据源分类：
        #   实时行情: tdx_hq > tdx_local > akshare > baostock > tushare
        #   历史K线:  tdx_local > akshare > baostock > tushare > tdx_hq
        
        # 1. 通达信行情服务器（mootdx，盘中实时数据最高优先级，延迟连接）
        try:
            self.adapters['tdx_hq'] = TdxHQAdapter()
            logger.info("已注册通达信行情服务器适配器 (mootdx, 延迟连接)")
        except Exception as e:
            logger.warning(f"通达信行情服务器适配器注册失败: {e}")
        
        # 2. 通达信本地数据（本地文件，历史K线最高优先级）
        try:
            self.adapters['tdx_local'] = TdxLocalAdapter()
            if self.adapters['tdx_local'].connect():
                logger.info("已初始化通达信本地数据适配器")
        except Exception as e:
            logger.warning(f"通达信本地适配器初始化失败: {e}")
        
        # 3. AKShare（免费数据源）
        if settings.AKSHARE_ENABLE:
            self.adapters['akshare'] = AKShareAdapter()
        
        # 4. Baostock（免费数据源）
        if settings.BAOSTOCK_ENABLE:
            self.adapters['baostock'] = BaostockAdapter()
        
        # 5. Tushare（需要积分）
        if settings.TUSHARE_ENABLE:
            self.adapters['tushare'] = TushareAdapter()
        
        # 6. 通达信财务数据（mootdx.affair，延迟连接）
        try:
            self.adapters['tdx_finance'] = TdxFinanceAdapter()
            logger.info("已注册通达信财务数据适配器 (mootdx.affair, 延迟连接)")
        except Exception as e:
            logger.warning(f"通达信财务适配器注册失败: {e}")
        
        logger.info(f"已初始化 {len(self.adapters)} 个数据源: {list(self.adapters.keys())}")
    
    def connect_all(self) -> Dict[str, bool]:
        """
        连接所有数据源（tdx_hq / tdx_finance 除外，其使用延迟连接）

        Returns:
            {数据源名: 是否成功}
        """
        results = {}
        for name, adapter in self.adapters.items():
            # tdx_hq / tdx_finance 使用延迟连接（首次请求时才建立连接）
            if name in ('tdx_hq', 'tdx_finance'):
                results[name] = True  # 标记为已就绪（延迟连接）
                continue
            try:
                results[name] = adapter.connect()
            except Exception as e:
                logger.error(f"连接 {name} 失败: {e}")
                results[name] = False
        return results
    
    def disconnect_all(self):
        """断开所有数据源"""
        for adapter in self.adapters.values():
            try:
                adapter.disconnect()
            except Exception as e:
                logger.error(f"断开适配器失败: {e}")
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        parts = [method]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")
        return "/".join(parts)
    
    def _get_data_with_cache(self, cache_key: str, fetch_func, **kwargs):
        """从缓存或数据源获取数据"""
        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_data
        
        # 从数据源获取
        data = fetch_func(**kwargs)
        
        # 保存到缓存
        if self.cache and not data.empty:
            self.cache.set(cache_key, data)
        
        return data
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表（多数据源兜底，优先使用有中文名的数据源）"""
        cache_key = self._get_cache_key("stock_list")
        
        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        # 按优先级尝试各数据源（本地文件优先，但需要验证名称质量）
        for name in ['tdx_local', 'akshare', 'baostock', 'tushare']:
            if name in self.adapters:
                try:
                    adapter = self.adapters[name]
                    if not adapter.connected:
                        adapter.connect()
                    
                    df = adapter.get_stock_list()
                    if not df.empty:
                        # 验证名称质量：检查是否包含中文名
                        has_chinese_names = self._check_chinese_names(df)
                        if not has_chinese_names:
                            logger.info(f"从 {name} 获取股票列表成功但无中文名，尝试下一个数据源")
                            continue  # 回退到下一个数据源
                        logger.info(f"从 {name} 获取股票列表成功 ({len(df)} 只，含中文名)")
                        if self.cache:
                            self.cache.set(cache_key, df)
                        return df
                except Exception as e:
                    logger.warning(f"从 {name} 获取失败，尝试下一个数据源: {e}")
        
        return pd.DataFrame()
    
    def _check_chinese_names(self, df: pd.DataFrame) -> bool:
        """检查 DataFrame 的 name 列是否包含中文名"""
        import re
        if 'name' not in df.columns:
            return False
        # 抽样检查前20条，只要有一条含中文就算有
        sample = df['name'].head(20).dropna().astype(str)
        if sample.empty:
            return False
        return any(bool(re.search(r'[\u4e00-\u9fa5]', str(n))) for n in sample)
    
    def get_daily_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取日线数据（多数据源兜底）"""
        cache_key = self._get_cache_key("daily", code=code, start=start_date, end=end_date, adjust=adjust)
        
        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_data
        
        # 按优先级尝试各数据源
        # 需要复权时跳过 tdx_local（本地 .day 文件不支持复权处理）
        if adjust and adjust != "none":
            data_sources = ['akshare', 'baostock', 'tushare', 'tdx_local']
        else:
            data_sources = ['tdx_local', 'akshare', 'baostock', 'tushare']
        
        for name in data_sources:
            if name in self.adapters:
                try:
                    adapter = self.adapters[name]
                    if not adapter.connected:
                        adapter.connect()
                    
                    df = adapter.get_daily_data(code, start_date, end_date, adjust)
                    if not df.empty:
                        logger.info(f"从 {name} 获取 {code} 日线数据成功 ({len(df)} 条, adjust={adjust})")
                        if self.cache:
                            self.cache.set(cache_key, df)
                        return df
                except Exception as e:
                    logger.warning(f"从 {name} 获取 {code} 失败，尝试下一个数据源: {e}")
        
        return pd.DataFrame()
    
    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """
        获取实时行情（多数据源兜底）

        优先级: tdx_hq(行情服务器,盘中实时) > tdx_local(本地文件) > akshare > baostock > tushare
        自动识别指数代码，路由到 get_index_realtime() 获取正确的指数点位数据
        """
        if not codes:
            return pd.DataFrame()
        
        # ── 分离指数代码与股票代码 ──
        # 指数代码特征：必须同时满足：
        #   1. 带 sh/sz 前缀（去前缀后与原值不同）
        #   2. 去前缀后的值在已知指数集合中
        # 这样可避免纯 6 位股票代码如 000001（平安银行）被误判为指数
        INDEX_CODES = {'000001', '399001', '399006', '000300', '000016', '000905',
                       '000010', '000009', '000006', '399005', '399301', '399306',
                       '000688'}

        def strip_prefix(c):
            """去掉 sh/sz 前缀"""
            import re
            return re.sub(r'^(sh|sz|SH|SZ)', '', c)

        stock_codes = []
        index_codes = []
        for c in codes:
            clean = strip_prefix(c)
            # 只有带前缀的代码才可能是指数（如 sh000001 → 000001）
            # 纯数字代码（000001=平安银行）始终作为股票处理
            had_prefix = (clean != c)
            if had_prefix and clean in INDEX_CODES:
                index_codes.append(clean)
            else:
                stock_codes.append(c)
        
        results = []
        
        # ── 获取指数实时数据（使用 index() 接口） ──
        if index_codes:
            for name in ['tdx_hq']:
                if name in self.adapters:
                    try:
                        adapter = self.adapters[name]
                        if hasattr(adapter, 'get_index_realtime'):
                            if not adapter.connected:
                                adapter.connect()
                            df = adapter.get_index_realtime(index_codes)
                            if not df.empty:
                                results.append(df)
                                logger.info(f"从 {name} 获取指数行情成功 ({len(df)} 条)")
                                break
                    except Exception as e:
                        logger.warning(f"从 {name} 获取指数行情失败: {e}")
        
        # ── 获取股票实时数据（使用 quotes() 接口） ──
        if stock_codes:
            for name in ['tdx_hq', 'tdx_local', 'akshare', 'baostock', 'tushare']:
                if name in self.adapters:
                    try:
                        adapter = self.adapters[name]
                        if not adapter.connected:
                            adapter.connect()
                        
                        df = adapter.get_realtime_quote(stock_codes)
                        if not df.empty:
                            results.append(df)
                            logger.info(f"从 {name} 获取股票行情成功 ({len(df)} 条)")
                            break
                        else:
                            logger.debug(f"从 {name} 获取股票行情为空 (codes: {stock_codes[:3]}...)，尝试下一个")
                    except Exception as e:
                        logger.warning(f"从 {name} 获取股票行情失败，尝试下一个: {e}")
        
        if not results:
            logger.error(f"所有数据源均无法获取实时行情: {codes}")
            return pd.DataFrame()
        
        # 合并指数 + 股票结果
        import pandas as pd
        combined = pd.concat(results, ignore_index=True)
        logger.info(f"获取实时行情共 {len(combined)} 条（指数:{len(index_codes)}, 股票:{len(stock_codes)}）")
        return combined
    
    def is_healthy(self) -> bool:
        """检查数据源健康状态"""
        return any(adapter.is_available() for adapter in self.adapters.values())

    # ============================================================
    # 财务数据方法（tdx_finance 适配器）
    # ============================================================

    def _ensure_finance_adapter(self) -> Optional['TdxFinanceAdapter']:
        """确保财务适配器已连接，返回适配器实例或 None"""
        adapter = self.adapters.get('tdx_finance')
        if not adapter:
            return None
        if not adapter.connected:
            adapter.connect()
        return adapter

    def get_financial_indicators(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取核心财务指标

        Args:
            code: 股票代码
            report_date: 报告期（YYYYMMDD），默认最新
        """
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_financial_indicators(code, report_date)

    def get_financial_history(self, code: str, fields: List[str] = None, limit: int = 10) -> Dict[str, Any]:
        """获取历史财务数据"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_financial_history(code, fields, limit)

    def get_balance_sheet(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """获取资产负债表"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_balance_sheet(code, report_date)

    def get_income_statement(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """获取利润表"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_income_statement(code, report_date)

    def get_cashflow_statement(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """获取现金流量表"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_cashflow_statement(code, report_date)

    def get_equity_structure(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """获取股本结构"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_equity_structure(code, report_date)

    def get_shareholder_info(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """获取股东与机构持仓"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_shareholder_info(code, report_date)

    def get_financial_summary(self, code: str) -> Dict[str, Any]:
        """获取财务概览"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return {'code': code, 'error': '财务数据源不可用'}
        return adapter.get_financial_summary(code)

    def list_report_dates(self, valid_only: bool = True) -> List[str]:
        """列出可用报告期（默认仅返回有有效数据的日期）"""
        adapter = self._ensure_finance_adapter()
        if not adapter:
            return []
        return adapter.list_report_dates(valid_only=valid_only)

    # ============================================================
    # 资金流向与热点数据（preparereadme.MD 5.5）
    # ============================================================

    def get_fund_flow(self, code: str, days: int = 5, preferred: str = None) -> Dict[str, Any]:
        """
        获取个股资金流向（多数据源兜底）
        优先级: akshare > tushare
        注意: akshare 有 get_fund_flow(), tushare 有 get_moneyflow()，方法名不同
        """
        order = ['akshare', 'tushare'] if not preferred else [preferred]
        errors = []
        for name in order:
            adapter = self.adapters.get(name)
            if not adapter or not adapter.connected:
                try:
                    adapter.connect()
                except Exception as e:
                    errors.append(f"{name}: {e}")
                    continue

            try:
                # akshare 用 get_fund_flow, tushare 用 get_moneyflow
                if name == 'tushare':
                    result = adapter.get_moneyflow(code, days)
                else:
                    result = adapter.get_fund_flow(code, days)
                if 'error' not in result:
                    return result
                errors.append(f"{name}: {result['error']}")
            except Exception as e:
                errors.append(f"{name}: {e}")
                logger.warning(f"从 {name} 获取资金流向失败: {e}")

        logger.error(f"资金流向获取失败: {'; '.join(errors)}")
        return {'code': code, 'error': f'所有数据源均无法获取资金流向数据: {"; ".join(errors)}'}

    def get_sector_fund_flow(self, indicator: str = "今日", days: int = 5) -> Dict[str, Any]:
        """获取板块资金流向排行（akshare）"""
        adapter = self.adapters.get('akshare')
        if not adapter or not adapter.connected:
            try:
                adapter.connect()
            except Exception:
                return {'sectors': [], 'error': 'akshare 不可用', 'indicator': indicator}
        try:
            return adapter.get_sector_fund_flow(indicator, top_n=days)
        except BaseException as e:
            # akshare 某些接口可能导致进程级异常（如 os._exit），捕获所有异常
            logger.error(f"akshare get_sector_fund_flow 异常: {type(e).__name__}: {e}")
            return {'sectors': [], 'error': f'akshare异常: {type(e).__name__}', 'indicator': indicator}

    def get_concept_list(self) -> Dict[str, Any]:
        """获取概念板块列表（akshare）"""
        adapter = self.adapters.get('akshare')
        if not adapter or not adapter.connected:
            try:
                adapter.connect()
            except Exception:
                return {'concepts': [], 'error': 'akshare 不可用'}
        try:
            return adapter.get_concept_list()
        except BaseException as e:
            # akshare 某些接口可能导致进程级异常，捕获所有异常
            logger.error(f"akshare get_concept_list 异常: {type(e).__name__}: {e}")
            return {'concepts': [], 'error': f'akshare异常: {type(e).__name__}'}

    def get_concept_stocks(self, concept_name: str) -> Dict[str, Any]:
        """获取概念成分股（akshare）"""
        adapter = self.adapters.get('akshare')
        if not adapter or not adapter.connected:
            try:
                adapter.connect()
            except Exception:
                return {'concept': concept_name, 'stocks': [], 'error': 'akshare 不可用'}
        try:
            return adapter.get_concept_stocks(concept_name)
        except Exception as e:
            return {'concept': concept_name, 'stocks': [], 'error': str(e)}

    def get_top10_holders(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """获取前十大股东（tushare）"""
        adapter = self.adapters.get('tushare')
        if not adapter or not adapter.connected:
            try:
                adapter.connect()
            except Exception:
                return {'code': code, 'error': 'tushare 不可用'}
        try:
            return adapter.get_top10_holders(code, report_date)
        except Exception as e:
            return {'code': code, 'error': str(e)}

    def get_research_report(self, code: str, limit: int = 10) -> Dict[str, Any]:
        """获取机构研报（tushare）"""
        adapter = self.adapters.get('tushare')
        if not adapter or not adapter.connected:
            try:
                adapter.connect()
            except Exception:
                return {'code': code, 'reports': [], 'error': 'tushare 不可用'}
        try:
            return adapter.get_research_report(code, limit)
        except Exception as e:
            return {'code': code, 'reports': [], 'error': str(e)}

    # ============================================================
    # 分钟K线数据（tdx_local > tdx_hq > akshare）
    # ============================================================

    def get_minute_data(self, code: str, period: int = 5) -> pd.DataFrame:
        """
        获取分钟级K线数据（多数据源兜底）

        Args:
            code: 股票代码
            period: K线周期（1/5/15/30/60 分钟）

        Returns:
            DataFrame 含 datetime, open, high, low, close, volume
        """
        # 分钟数据不使用缓存，按优先级尝试各数据源
        for name in ['tdx_local', 'tdx_hq', 'akshare']:
            adapter = self.adapters.get(name)
            if not adapter:
                continue
            try:
                # 检查适配器是否支持分钟数据
                if not hasattr(adapter, 'get_minute_data'):
                    continue
                if not adapter.connected:
                    adapter.connect()
                df = adapter.get_minute_data(code, period)
                if df is not None and not df.empty:
                    logger.info(f"从 {name} 获取 {code} 分钟数据成功 ({len(df)} 条, period={period})")
                    return df
            except Exception as e:
                logger.warning(f"从 {name} 获取 {code} 分钟数据失败: {e}")

        logger.warning(f"所有数据源均无法获取分钟数据: {code}, period={period}")
        return pd.DataFrame()

    # ============================================================
    # 十档盘口数据（tdx_hq 优先）
    # ============================================================

    def get_depth_data(self, code: str) -> pd.DataFrame:
        """
        获取十档盘口数据

        Args:
            code: 股票代码

        Returns:
            DataFrame 含 bid_price, bid_volume, ask_price, ask_volume
        """
        # 盘口数据仅行情服务器可提供实时数据
        for name in ['tdx_hq', 'tdx_local']:
            adapter = self.adapters.get(name)
            if not adapter:
                continue
            try:
                if not hasattr(adapter, 'get_depth_data'):
                    continue
                if not adapter.connected:
                    adapter.connect()
                df = adapter.get_depth_data(code)
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"从 {name} 获取盘口数据失败: {e}")

        return pd.DataFrame()

    # ============================================================
    # 分笔成交数据
    # ============================================================

    def get_transaction_data(self, code: str, limit: int = 100) -> pd.DataFrame:
        """
        获取分笔成交数据

        Args:
            code: 股票代码
            limit: 返回条数

        Returns:
            DataFrame 含 time, price, volume, direction, amount
        """
        for name in ['tdx_hq', 'tdx_local', 'akshare']:
            adapter = self.adapters.get(name)
            if not adapter:
                continue
            try:
                if not hasattr(adapter, 'get_transaction_data'):
                    continue
                if not adapter.connected:
                    adapter.connect()
                df = adapter.get_transaction_data(code, limit)
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"从 {name} 获取分笔成交失败: {e}")

        return pd.DataFrame()


# 全局数据源管理器实例
_data_source_manager: Optional[DataSourceManager] = None


def get_data_source_manager() -> DataSourceManager:
    """获取数据源管理器单例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager
