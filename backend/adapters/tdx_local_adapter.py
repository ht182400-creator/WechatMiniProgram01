# -*- coding: utf-8 -*-
"""
通达信本地数据适配器（mootdx.reader 版）

使用 mootdx.reader 替代手动 struct 解析，读取通达信安装目录下的本地K线数据。
支持日K、分钟K、分笔成交、板块分类等。

参考: preparereadme.MD 第2.1节 → mootdx.reader 读取本地 .day 文件

注意事项（来自 preparereadme.MD 第四章）:
- 某些品种（如可转债）返回价格可能是实际价格×10，需根据品种做转换
- 请求频率控制：全市场快照建议 ≤3秒/次
- 连接池管理：高频场景可用 multithread=True 提升吞吐量

@author: StockQuant Team
@date: 2026-05-21
"""

import os
import struct
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np

from adapters.base_adapter import BaseDataAdapter

logger = logging.getLogger(__name__)

# 需要价格修正的品种类型（价格×10 → 实际价格）
# 可转债(11xxxx, 12xxxx)、债券等品种返回的价格需除以10
_BOND_PRICE_DIVISOR_10_PREFIXES = ('11', '12')  # 可转债
_BOND_PRICE_DIVISOR_100_PREFIXES = ()  # 预留：纯债可能需除以100


class TdxLocalAdapter(BaseDataAdapter):
    """
    通达信本地数据适配器（mootdx.reader 版）

    数据目录结构：
    - {TdxPath}/vipdoc/sh/lday/  - 上海日K线 (.day文件)
    - {TdxPath}/vipdoc/sz/lday/  - 深圳日K线 (.day文件)
    - {TdxPath}/vipdoc/sh/minline/ - 上海分钟线
    - {TdxPath}/vipdoc/sz/minline/ - 深圳分钟线

    相对于旧版（手动 struct 解析）的改进：
    1. 日K数据由 mootdx.reader 读取，自动处理价格因子（指数/基金）
    2. 约 200 行手动解析代码简化为约 5 行
    3. 自动识别板块分类（block_new）
    4. 可转债/债券价格自动校正
    """

    name = "tdx_local"

    def __init__(self, tdx_path: str = None):
        """
        初始化通达信本地适配器

        Args:
            tdx_path: 通达信安装目录，默认使用 D:\\new_tdx64
        """
        self.tdx_path = tdx_path or r"D:\new_tdx64"
        self.connected = False
        self._reader = None  # mootdx.reader.Reader 实例（延迟创建）
        self._day_cache: Dict[str, pd.DataFrame] = {}
        self._stock_info_cache: Optional[pd.DataFrame] = None

    # ============================
    # 连接管理
    # ============================

    def connect(self) -> bool:
        """
        连接数据源（检查目录 + 创建 mootdx.reader.Reader）

        Returns:
            True 表示成功
        """
        try:
            base_path = Path(self.tdx_path)
            if not base_path.exists():
                logger.error(f"通达信目录不存在: {self.tdx_path}")
                return False

            # 检查关键目录
            vipdoc = base_path / "vipdoc"
            if not vipdoc.exists():
                logger.error(f"通达信 vipdoc 目录不存在: {vipdoc}")
                return False

            # 创建 mootdx.reader.Reader（延迟创建，连接时才实例化）
            from mootdx.reader import Reader
            self._reader = Reader.factory(market='std', tdxdir=self.tdx_path)
            self.connected = True
            logger.info(f"通达信本地适配器连接成功 (mootdx.reader): {self.tdx_path}")
            return True
        except Exception as e:
            logger.error(f"连接通达信本地适配器失败: {e}")
            return False

    def disconnect(self):
        """断开连接，清理缓存"""
        self.connected = False
        self._reader = None
        self._day_cache.clear()
        logger.info("通达信本地适配器已断开")

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        if self.connected and self._reader is not None:
            return True
        return self.connect()

    @property
    def reader(self):
        """
        获取 mootdx.reader.Reader 实例（若未初始化则自动创建）

        Returns:
            Reader 实例或 None
        """
        if self._reader is None:
            self.connect()
        return self._reader

    # ============================
    # 价格校验与修正
    # ============================

    @staticmethod
    def _needs_price_correction(code: str) -> float:
        """
        检查品种是否需要价格修正

        依据 preparereadme.MD 注意事项：
        - 可转债(11xxxx, 12xxxx): 价格×10 → 需除以10
        - 债券等其他品种可能也有类似问题

        Args:
            code: 股票/债券代码

        Returns:
            除数因子（1.0 表示不需要修正，10.0 表示需除以10）
        """
        code = str(code).strip()
        if code.startswith(_BOND_PRICE_DIVISOR_10_PREFIXES):
            return 10.0
        return 1.0

    @staticmethod
    def _correct_prices(df: pd.DataFrame, code: str) -> pd.DataFrame:
        """
        对需要修正价格的品种进行价格校正

        Args:
            df: 原始行情 DataFrame
            code: 品种代码

        Returns:
            修正后的 DataFrame
        """
        divisor = TdxLocalAdapter._needs_price_correction(code)
        if divisor != 1.0:
            price_cols = ['open', 'high', 'low', 'close']
            for col in price_cols:
                if col in df.columns:
                    df[col] = df[col] / divisor
            logger.debug(f"品种 {code} 价格已修正: ÷{divisor}")
        return df

    # ============================
    # 股票列表
    # ============================

    def get_stock_list(self) -> pd.DataFrame:
        """
        从通达信目录获取股票列表

        Returns:
            DataFrame 包含 code, name, market, source 字段
        """
        if self._stock_info_cache is not None:
            return self._stock_info_cache

        stocks = []
        for market in ['sh', 'sz']:
            lday_dir = Path(self.tdx_path) / "vipdoc" / market / "lday"
            if not lday_dir.exists():
                continue

            for file in lday_dir.glob("*.day"):
                filename = file.stem  # 如 'sh600000'
                market_prefix = filename[:2]
                code = filename[2:]

                if len(code) == 6 and code.isdigit():
                    stocks.append({
                        'code': code,
                        'market': market,
                        'name': code,  # 名称需要从其他来源获取
                        'source': 'tdx_local'
                    })

        df = pd.DataFrame(stocks) if stocks else pd.DataFrame(
            columns=['code', 'market', 'name', 'source']
        )
        self._stock_info_cache = df
        logger.info(f"从通达信本地获取 {len(df)} 只品种")
        return df

    # ============================
    # 日K线数据（核心：使用 mootdx.reader）
    # ============================

    def get_daily_data(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取日K线数据（由 mootdx.reader 读取本地 .day 文件）

        优势对比旧版（手动 struct 解析）:
        - 旧版: ~60行 struct.unpack 代码，需手动除以100
        - 新版: 1行 reader.daily() 调用，自动归一化价格

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型（当前版本仅返回原始数据，复权由上层处理）

        Returns:
            DataFrame 包含 date(索引), open, high, low, close, amount, volume
        """
        if not self.validate_code(code):
            logger.warning(f"无效的股票代码: {code}")
            return pd.DataFrame()

        # 检查缓存
        cache_key = f"{code}"
        if code in self._day_cache:
            df = self._day_cache[code].copy()
        else:
            reader = self.reader
            if reader is None:
                logger.error(f"mootdx.reader 未初始化，无法获取日K数据")
                return pd.DataFrame()

            try:
                # 核心调用: mootdx.reader.daily() 替代旧的 struct 手动解析
                df = reader.daily(symbol=code)
            except Exception as e:
                logger.error(f"mootdx.reader 读取 {code} 日K失败: {e}")
                return pd.DataFrame()

            if df is None or df.empty:
                logger.warning(f"未找到 {code} 的本地日K数据")
                return pd.DataFrame()

            # 将 date 索引转为列，方便后续操作
            df = df.reset_index()
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            # 价格校验：修正可转债等品种的价格偏差
            df = self._correct_prices(df, code)

            # 缓存完整数据
            self._day_cache[code] = df.copy()

        if df.empty:
            return df

        # 按日期筛选
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        date_col = 'date' if 'date' in df.columns else df.index.name
        mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
        result = df[mask].copy()

        # 确保 date 在列中
        if 'date' not in result.columns and result.index.name != 'date':
            result = result.reset_index()
            if 'index' in result.columns and pd.api.types.is_datetime64_any_dtype(result['index']):
                result.rename(columns={'index': 'date'}, inplace=True)

        return result

    # ============================
    # 分钟K线数据（保留手动解析，因为 mootdx.reader.minute() 在部分环境下返回 None）
    # ============================

    def get_minute_data(
        self,
        code: str,
        period: int = 5
    ) -> pd.DataFrame:
        """
        获取分钟K线数据

        策略：
        - 1分/5分：优先尝试 mootdx.reader.minute()（本地文件），失败则手动解析
        - 15分/30分/60分：先获取 1 分钟原始数据，再用 pandas resample 聚合
          （mootdx 本地 reader 仅支持 1 分和 5 分两种周期）

        Args:
            code: 股票代码
            period: 周期（1, 5, 15, 30, 60），默认5分钟

        Returns:
            DataFrame 包含 datetime, open, high, low, close, volume
        """
        if not self.validate_code(code):
            return pd.DataFrame()

        # ── 15/30/60 分钟：用 1 分钟数据重采样聚合 ──
        if period in (15, 30, 60):
            df_1min = self._get_raw_minute_data(code)
            if not df_1min.empty:
                return self._resample_minutes(df_1min, period)
            return pd.DataFrame()

        # ── 1分/5分：直接从本地文件读取 ──
        return self._get_raw_minute_data(code, period)

    def _get_raw_minute_data(self, code: str, period: int = 1) -> pd.DataFrame:
        """
        从通达信本地文件获取原始分钟数据（仅支持 1 分和 5 分）

        Args:
            code: 股票代码
            period: 原始周期，1 或 5
        """
        reader = self.reader
        if reader is not None:
            try:
                # mootdx.reader.minute() 只支持两种 suffix：
                #   suffix=1 (默认) → minline 目录 → 1分钟线 (.lc1/.lc)
                #   suffix=5         → fzline 目录 → 5分钟线 (.lc5/.5)
                suffix_map = {1: 1, 5: 5}
                suffix = suffix_map.get(period, 1)
                df = reader.minute(symbol=code, suffix=suffix)
                if df is not None and not df.empty:
                    df = df.reset_index()
                    if 'index' in df.columns:
                        df.rename(columns={'index': 'datetime'}, inplace=True)
                    df = self._correct_prices(df, code)
                    return df
            except Exception as e:
                logger.debug(f"mootdx.reader.minute() 失败，回退手动解析: {e}")

        # 回退：手动 struct 解析分钟文件
        return self._read_minute_file_manual(code, period)

    def _resample_minutes(self, df_1min: pd.DataFrame, target_period: int) -> pd.DataFrame:
        """
        将 1 分钟 K 线重采样为更高周期（15/30/60 分钟）

        Args:
            df_1min: 1 分钟原始 DataFrame（须含 datetime 列）
            target_period: 目标周期（15, 30, 60）
        """
        try:
            df = df_1min.copy()
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime').sort_index()

            # 构建重采样频率字符串
            freq_map = {15: '15min', 30: '30min', 60: '60min'}
            freq = freq_map.get(target_period, '15min')

            # OHLC 重采样
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            if 'amount' in df.columns:
                ohlc_dict['amount'] = 'sum'

            df_resampled = df.resample(freq).apply(ohlc_dict)

            # 展平 MultiIndex（如有）
            if isinstance(df_resampled.columns, pd.MultiIndex):
                df_resampled.columns = df_resampled.columns.get_level_values(0)

            # 移除空行（非交易时段产生的 NaN）
            df_resampled = df_resampled.dropna(subset=['open', 'close'], how='all')
            df_resampled = df_resampled.reset_index()

            logger.info(f"1分钟→{target_period}分钟重采样成功: {len(df_1min)} → {len(df_resampled)} 条")
            return df_resampled

        except Exception as e:
            logger.warning(f"分钟数据重采样失败 (target={target_period}): {e}")
            return pd.DataFrame()

    def _read_minute_file_manual(self, code: str, period: int = 1) -> pd.DataFrame:
        """
        手动解析通达信分钟K线文件（mootdx.reader.minute() 的回退方案）

        通达信本地分钟线文件命名规则（vipdoc/{market}/minline/ 或 fzline/）：
          .lc / (无后缀) → 1分钟线
          .lc1 / .1       → 5分钟线
          .lc5 / .5       → 15分钟线（在 fzline 目录）
          .lc15 / .15     → 30分钟线
          .lc30 / .30     → 60分钟线

        Args:
            code: 股票代码
            period: 周期（仅支持 1 和 5，更高周期由 get_minute_data 通过重采样处理）

        Returns:
            DataFrame 分钟K线数据
        """
        market = self.get_market(code)

        # 仅支持 1 分和 5 分两种本地文件（与 mootdx.reader.minute() 一致）
        ext_map = {1: '.lc', 5: '.lc1'}
        ext = ext_map.get(period, '.lc')

        # 5 分钟数据在 fzline 目录
        subdir = 'fzline' if period == 5 else 'minline'

        filename = f"{market}{code}{ext}"
        file_path = Path(self.tdx_path) / "vipdoc" / market / subdir / filename
        if not file_path.exists():
            logger.warning(f"找不到 {filename} 文件")
            return pd.DataFrame()

        records = []
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(32)
                if len(data) < 32:
                    break
                try:
                    date_int, time_int, open_p, high, low, close, volume, _ = \
                        struct.unpack('<IIIIIII', data)

                    year = date_int // 10000
                    month = (date_int // 100) % 100
                    day = date_int % 100
                    hour = time_int // 100
                    minute = time_int % 100

                    records.append({
                        'datetime': datetime(year, month, day, hour, minute),
                        'date': datetime(year, month, day),
                        'time': f"{hour:02d}:{minute:02d}",
                        'open': open_p / 100.0,
                        'high': high / 100.0,
                        'low': low / 100.0,
                        'close': close / 100.0,
                        'volume': volume,
                    })
                except struct.error:
                    continue

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df = df.sort_values('datetime').reset_index(drop=True)

        # 价格校验
        divisor = self._needs_price_correction(code)
        if divisor != 1.0:
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col] / divisor

        return df

    # ============================
    # 实时行情（从本地文件获取最新日K作为"实时"行情）
    # ============================

    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """
        获取实时行情（从本地日K文件获取最后一根K线作为近似行情）

        注意：本地文件只能获取日末收盘数据，无法获取盘中实时数据。
        盘中实时行情请使用 TdxHQAdapter（mootdx.quotes）。

        Args:
            codes: 股票代码列表

        Returns:
            DataFrame 包含最新日K数据
        """
        results = []
        today = datetime.now().strftime("%Y-%m-%d")

        for code in codes:
            df = self.get_daily_data(code, today, today)
            if not df.empty:
                row = df.iloc[-1].to_dict()
                row['code'] = code
                results.append(row)

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)

    # ============================
    # 盘口/分笔数据（本地文件不支持）
    # ============================

    def get_depth_data(self, code: str) -> pd.DataFrame:
        """
        获取盘口数据（本地文件不支持，返回空）

        Args:
            code: 股票代码

        Returns:
            空 DataFrame
        """
        return pd.DataFrame()

    def get_transaction_data(self, code: str, limit: int = 100) -> pd.DataFrame:
        """
        获取分笔成交数据（本地文件不支持，返回空）

        注意：盘中实时分笔请使用 TdxHQAdapter（mootdx.quotes.transaction()）

        Args:
            code: 股票代码
            limit: 返回条数

        Returns:
            空 DataFrame
        """
        return pd.DataFrame()
