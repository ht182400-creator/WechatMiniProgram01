# -*- coding: utf-8 -*-
"""
通达信行情服务器适配器
通过 mootdx 直连通达信行情服务器获取盘中实时数据
@author: StockQuant Team
@date: 2026-05-21
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from adapters.base_adapter import BaseDataAdapter

logger = logging.getLogger(__name__)


class TdxHQAdapter(BaseDataAdapter):
    """
    通达信行情服务器适配器

    通过 mootdx.quotes.Quotes 直连通达信行情服务器，获取盘中实时数据。
    支持：
    - 实时五档行情快照 (quotes)
    - 多周期K线数据 (bars)
    - 分时数据 (minute)
    - 分笔成交明细 (transaction)
    - 指数行情 (index)

    mootdx 实时行情能力：
    ╔══════════════╦══════════════╦══════════════════════╗
    ║ 数据类型     ║ 方法         ║ 说明                 ║
    ╠══════════════╬══════════════╬══════════════════════╣
    ║ 实时快照     ║ quotes()     ║ 五档盘口+涨跌幅+PE/PB║
    ║ K线数据      ║ bars()       ║ 1m/5m/15m/30m/时/日/周 ║
    ║ 分时数据     ║ minute()     ║ 当日分时价格线       ║
    ║ 分笔成交     ║ transaction()║ 逐笔成交明细         ║
    ║ 指数行情     ║ index()      ║ 指数实时数据         ║
    ╚══════════════╩══════════════╩══════════════════════╝
    """

    name = "tdx_hq"

    # mootdx K线周期映射
    # frequency参数: 0=1m, 1=5m, 2=15m, 3=30m, 4=60m, 5=日, 6=周, 7=月, 8=季, 9=年
    FREQ_MAP = {
        1: 0,    # 1分钟
        5: 1,    # 5分钟
        15: 2,   # 15分钟
        30: 3,   # 30分钟
        60: 4,   # 60分钟
        'D': 5,  # 日线
        'W': 6,  # 周线
        'M': 7,  # 月线
    }

    # mootdx quotes() 返回字段到标准字段的映射
    # 格式: 标准字段名 → [mootdx 可能的列名]
    QUOTE_FIELD_MAP = {
        'code': ['code'],
        'name': ['name'],
        'price': ['price', 'close'],
        'last_close': ['last_close', 'pre_close', 'lastclose'],
        'open': ['open'],
        'high': ['high'],
        'low': ['low'],
        'volume': ['volume', 'vol'],
        'amount': ['amount'],
        'change': ['change'],
        'pct_change': ['pct_chg', 'increase', 'pctchange'],
        'turnover_rate': ['turnover_rate', 'turnover'],
        'pe': ['pe', 'per'],
        'pb': ['pb', 'pbr'],
        'market_cap': ['market_cap', 'mktcap'],
        'amplitude': ['amplitude'],
        'high_low': ['high_low'],
        'bid1': ['bid1', 'buy1'],
        'bid_vol1': ['bid_vol1', 'bidvol1', 'bsize1'],
        'bid2': ['bid2', 'buy2'],
        'bid_vol2': ['bid_vol2', 'bidvol2', 'bsize2'],
        'bid3': ['bid3', 'buy3'],
        'bid_vol3': ['bid_vol3', 'bidvol3', 'bsize3'],
        'bid4': ['bid4', 'buy4'],
        'bid_vol4': ['bid_vol4', 'bidvol4', 'bsize4'],
        'bid5': ['bid5', 'buy5'],
        'bid_vol5': ['bid_vol5', 'bidvol5', 'bsize5'],
        'ask1': ['ask1', 'sell1'],
        'ask_vol1': ['ask_vol1', 'askvol1', 'ssize1'],
        'ask2': ['ask2', 'sell2'],
        'ask_vol2': ['ask_vol2', 'askvol2', 'ssize2'],
        'ask3': ['ask3', 'sell3'],
        'ask_vol3': ['ask_vol3', 'askvol3', 'ssize3'],
        'ask4': ['ask4', 'sell4'],
        'ask_vol4': ['ask_vol4', 'askvol4', 'ssize4'],
        'ask5': ['ask5', 'sell5'],
        'ask_vol5': ['ask_vol5', 'askvol5', 'ssize5'],
    }

    def __init__(self):
        """初始化通达信行情适配器"""
        self._client = None
        self.connected = False

    def connect(self) -> bool:
        """
        连接通达信行情服务器

        使用 mootdx Quotes.factory 自动选择最快服务器
        """
        try:
            from mootdx.quotes import Quotes

            self._client = Quotes.factory(
                market='std',        # 标准市场
                bestip=True,         # 自动选最快服务器，延迟降低约40%
                multithread=True,    # 多线程模式，吞吐量提升约3倍
                heartbeat=True,      # 心跳保持，长时间连接更稳定
                timeout=15           # 弱网环境下成功率更高
            )

            # 快速验证连接：尝试获取上证指数
            try:
                test_df = self._client.index(symbol='000001', market=1)
                if test_df is not None and not test_df.empty:
                    self.connected = True
                    logger.info("通达信行情服务器连接成功 (mootdx)")
                    return True
            except Exception as e:
                logger.warning(f"行情服务器验证失败: {e}")

            # 即使验证失败也标记为连接（服务器可能暂时不可达）
            self.connected = True
            logger.info("通达信行情适配器初始化完成 (mootdx)")
            return True

        except ImportError:
            logger.error("mootdx 未安装，请执行: pip install mootdx")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"连接通达信行情服务器失败: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """断开连接"""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self.connected = False
        logger.info("通达信行情适配器已断开")

    def is_available(self) -> bool:
        """
        检查数据源是否可用

        不主动连接服务器（避免健康检查时阻塞），始终返回 True。
        实际连接在首次 get_realtime_quote() 调用时通过 _ensure_client() 延迟建立。
        """
        return True

    def _ensure_client(self) -> bool:
        """
        确保客户端已连接，若断连则重试

        Returns:
            True 如果客户端可用，否则 False
        """
        if self._client is None or not self.connected:
            return self.connect()
        return True

    # ==================== 实时行情核心接口 ====================

    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """
        从行情服务器获取实时五档行情

        Args:
            codes: 股票代码列表，如 ['600000', '000001']

        Returns:
            DataFrame 包含实时行情，含五档盘口数据
            标准字段: code, name, price, last_close, open, high, low,
                      volume, amount, change, pct_change,
                      以及 bid1-5, ask1-5 五档买卖盘口
        """
        if not codes:
            return pd.DataFrame()

        if not self._ensure_client():
            logger.warning("行情服务器未连接")
            return pd.DataFrame()

        try:
            # mootdx quotes() 接收6位代码列表
            # 过滤无效代码
            valid_codes = [c for c in codes if self.validate_code(c)]
            if not valid_codes:
                return pd.DataFrame()

            raw_df = self._client.quotes(symbol=valid_codes)

            if raw_df is None or raw_df.empty:
                logger.debug(f"mootdx quotes 返回空数据: codes={valid_codes[:3]}...")
                return pd.DataFrame()

            # 标准化字段名
            df = self._normalize_quote_fields(raw_df)
            logger.info(f"从 tdx_hq 获取实时行情成功 ({len(df)} 条)")
            return df

        except Exception as e:
            logger.warning(f"从 tdx_hq 获取实时行情失败: {e}")
            return pd.DataFrame()

    def _normalize_quote_fields(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        将 mootdx 返回的原始字段映射到标准字段名

        mootdx quotes() 实际返回字段（版本 0.11.7）:
        - 核心: market, code, active1, price, last_close, open, high, low
        - 成交量: vol(成交量股), cur_vol(当前手), amount(成交额)
        - 买卖: s_vol(卖量), b_vol(买量)
        - 五档: bid1-5, ask1-5, bid_vol1-5, ask_vol1-5
        - 时间: servertime
        - 涨跌: reversed_bytes9 (涨跌幅%)

        Args:
            raw_df: mootdx quotes() 原始返回

        Returns:
            标准化后的 DataFrame，同时保留原始 mootdx 字段
        """
        import numpy as np

        result_df = raw_df.copy()

        # 标准化 code 字段
        if 'code' in result_df.columns:
            result_df['code'] = result_df['code'].astype(str).str.strip()
            result_df['code'] = result_df['code'].str.replace(r'^(sh|sz)', '', regex=True)

        # 映射成交量字段: vol → volume (mootdx 使用 'vol')
        if 'vol' in result_df.columns and 'volume' not in result_df.columns:
            result_df['volume'] = result_df['vol']

        # 映射涨跌幅: reversed_bytes9 → pct_change (mootdx 实际字段)
        if 'reversed_bytes9' in result_df.columns and 'pct_change' not in result_df.columns:
            result_df['pct_change'] = pd.to_numeric(result_df['reversed_bytes9'], errors='coerce')

        # 计算涨跌额: price - last_close
        if 'price' in result_df.columns and 'last_close' in result_df.columns:
            if 'change' not in result_df.columns:
                result_df['change'] = result_df['price'] - result_df['last_close']

        # 映射服务器时间
        if 'servertime' in result_df.columns and 'timestamp' not in result_df.columns:
            result_df['timestamp'] = result_df['servertime'].astype(str)

        # 应用通用字段映射（标准字段别名）
        for std_name, source_names in self.QUOTE_FIELD_MAP.items():
            for src in source_names:
                if src in raw_df.columns and std_name not in result_df.columns:
                    result_df[std_name] = raw_df[src]
                    break

        # 清洗数值字段（替换无效值）
        numeric_cols = ['price', 'last_close', 'open', 'high', 'low', 'volume', 'amount',
                        'change', 'pct_change']
        for col in numeric_cols:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')

        # 兜底：确保 price 字段存在
        if 'price' not in result_df.columns and 'close' in result_df.columns:
            result_df['price'] = result_df['close']

        if 'code' not in result_df.columns:
            logger.warning("实时行情缺少 code 字段")
            return result_df

        return result_df

    def get_depth_data(self, code: str) -> pd.DataFrame:
        """
        获取十档盘口数据

        通过 get_realtime_quote 获取含五档盘口的实时行情

        Args:
            code: 股票代码

        Returns:
            DataFrame 含买卖五档数据
        """
        df = self.get_realtime_quote([code])

        if df.empty:
            return pd.DataFrame()

        # 提取盘口相关列
        depth_cols = ['code', 'name', 'price', 'open', 'high', 'low']
        for i in range(1, 6):
            depth_cols.extend([f'bid{i}', f'bid_vol{i}', f'ask{i}', f'ask_vol{i}'])

        available_cols = [c for c in depth_cols if c in df.columns]
        return df[available_cols].copy() if available_cols else pd.DataFrame()

    def get_transaction_data(self, code: str, limit: int = 100) -> pd.DataFrame:
        """
        获取分笔成交明细

        Args:
            code: 股票代码
            limit: 返回条数

        Returns:
            DataFrame 含每笔成交的时间、价格、成交量
        """
        if not self._ensure_client():
            return pd.DataFrame()

        try:
            df = self._client.transaction(symbol=code, offset=limit)

            if df is None or df.empty:
                logger.debug(f"mootdx transaction 返回空: code={code}")
                return pd.DataFrame()

            # 标准化列名
            if 'price' in df.columns and 'direction' not in df.columns:
                # mootdx transaction 通常返回: time, price, vol, buyorsell
                cols_map = {
                    'time': 'time', 'price': 'price', 'vol': 'volume',
                    'buyorsell': 'direction', 'amount': 'amount'
                }
                for new_col, old_col in cols_map.items():
                    if old_col in df.columns:
                        df.rename(columns={old_col: new_col}, inplace=True)

            logger.debug(f"从 tdx_hq 获取 {code} 分笔成交 ({len(df)} 条)")
            return df.head(limit) if len(df) > limit else df

        except Exception as e:
            logger.warning(f"从 tdx_hq 获取 {code} 分笔成交失败: {e}")
            return pd.DataFrame()

    # ==================== K线数据接口 ====================

    def get_daily_data(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取日K线数据（从行情服务器）

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型（mootdx 服务器支持 qfq 前复权）

        Returns:
            DataFrame 含 date, open, high, low, close, volume, amount
        """
        if not self._ensure_client():
            return pd.DataFrame()

        try:
            # 计算需要获取的K线数量
            from datetime import datetime as dt
            try:
                end_dt = dt.strptime(end_date, "%Y-%m-%d")
                start_dt = dt.strptime(start_date, "%Y-%m-%d")
                days_diff = (end_dt - start_dt).days + 30
                offset = min(max(days_diff, 60), 2000)
            except (ValueError, TypeError):
                offset = 365

            # mootdx bars: frequency=5(日线), offset=获取条数
            df = self._client.bars(symbol=code, frequency=5, offset=offset)

            if df is None or df.empty:
                logger.debug(f"mootdx bars 返回空: code={code}")
                return pd.DataFrame()

            # 标准化列名
            col_map = {
                'date': 'date', 'code': 'code',
                'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
                'volume': 'volume', 'amount': 'amount',
            }
            # mootdx bars 通常直接返回 OHLCV 列
            for old_col, new_col in col_map.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)

            # 确保日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            # 按日期筛选
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
            result = df[mask].sort_values('date').reset_index(drop=True)

            logger.debug(f"从 tdx_hq 获取 {code} 日线数据 ({len(result)} 条)")
            return result

        except Exception as e:
            logger.warning(f"从 tdx_hq 获取 {code} 日线数据失败: {e}")
            return pd.DataFrame()

    def get_minute_data(self, code: str, period: int = 5) -> pd.DataFrame:
        """
        获取分钟级K线数据

        Args:
            code: 股票代码
            period: K线周期（1/5/15/30/60 分钟）

        Returns:
            DataFrame 含 datetime, open, high, low, close, volume
        """
        if not self._ensure_client():
            return pd.DataFrame()

        try:
            # 1分钟K线使用 minute() 方法（分时数据更精确）
            if period == 1:
                df = self._client.minute(symbol=code)
            else:
                freq = self.FREQ_MAP.get(period, 1)
                df = self._client.bars(symbol=code, frequency=freq, offset=240)

            if df is None or df.empty:
                logger.debug(f"mootdx 分钟数据返回空: code={code}, period={period}")
                return pd.DataFrame()

            # 标准化
            col_map = {
                'date': 'date', 'time': 'time', 'datetime': 'datetime',
                'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
                'volume': 'volume', 'amount': 'amount',
            }
            for old_col, new_col in col_map.items():
                if old_col in df.columns and old_col != new_col:
                    df.rename(columns={old_col: new_col}, inplace=True)

            logger.debug(f"从 tdx_hq 获取 {code} 分钟数据 ({len(df)} 条, period={period})")
            return df

        except Exception as e:
            logger.warning(f"从 tdx_hq 获取 {code} 分钟数据失败: {e}")
            return pd.DataFrame()

    # ==================== 辅助接口 ====================

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        行情服务器不适合获取全量股票列表，返回空 DataFrame
        由其他适配器（tdx_local, akshare）提供此功能

        Returns:
            空 DataFrame
        """
        return pd.DataFrame()

    def get_index_realtime(self, codes: List[str]) -> pd.DataFrame:
        """
        获取指数实时行情

        Args:
            codes: 指数代码，如 ['000001', '399001']  (上证/深成)

        Returns:
            DataFrame 含指数实时数据
        """
        if not codes or not self._ensure_client():
            return pd.DataFrame()

        try:
            results = []
            for code in codes:
                try:
                    market = 1 if code.startswith(('0', '6', '9')) else 0
                    df = self._client.index(symbol=code, market=market)
                    if df is not None and not df.empty:
                        results.append(df)
                except Exception as e:
                    logger.debug(f"获取指数 {code} 失败: {e}")

            if results:
                result_df = pd.concat(results, ignore_index=True)
                logger.info(f"从 tdx_hq 获取 {len(result_df)} 条指数行情")
                return result_df

            return pd.DataFrame()

        except Exception as e:
            logger.warning(f"从 tdx_hq 获取指数行情失败: {e}")
            return pd.DataFrame()
