# -*- coding: utf-8 -*-
"""
通达信财务数据适配器 (mootdx.affair)
======================================
基于 preparereadme.MD 架构设计，使用 mootdx.affair 解析通达信财务数据包 (gpcw*.zip)，
提供财务报表指标、股本结构、股东持仓、分红送转等完整数据。

数据来源：
  - 通达信服务器 gpcwYYYYMMDD.zip 财务包（通过 mootdx.affair 下载并解析）
  - 585 个财务字段，覆盖资产负债表、利润表、现金流量表核心指标
  - 含股本结构、股东人数、机构持仓、分红送转等扩展字段

缓存策略：
  - .zip 文件缓存于 ${tdxdir}/vipdoc/cw/ 目录
  - 解析后的 DataFrame 按报告期缓存在内存中（本会话有效）

注意事项 (preparereadme.MD)：
  - 服务器地址可能变动 → 依赖 tdx_hq 连接，已有 bestip=True 保障
  - 请求频率控制 → 财务包下载为大文件，非高频操作，本次按需下载
  - 数据校验 → 财务数据为浮点数，单位可能为万元/元，按字段区分
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

from .base_adapter import BaseDataAdapter

logger = logging.getLogger(__name__)

# 通达信安装目录（财务缓存目录）
TDX_DIR = r'D:\new_tdx64'
CW_CACHE_DIR = os.path.join(TDX_DIR, 'vipdoc', 'cw')

# 按需导入字段分组
# 核心财务指标（每股类 + ROE）
KEY_INDICATORS = [
    '基本每股收益', '扣除非经常性损益每股收益', '每股未分配利润',
    '每股净资产', '每股资本公积金', '净资产收益率', '每股经营现金流量',
    '营业收入增长率(%)', '净利润增长率(%)', '净资产增长率(%)',
    '总资产增长率(%)', '营业利润增长率(%)',
    '销售毛利率(%)(非金融类指标)', '销售净利率(%)',
    '资产负债率(%)', '流动比率(非金融类指标)', '速动比率(非金融类指标)',
    '权益乘数(%)',
]

# 资产负债表核心字段
BALANCE_SHEET_CORE = [
    '货币资金', '应收账款', '存货', '流动资产合计', '固定资产', '无形资产',
    '商誉', '非流动资产合计', '资产总计', 
    '短期借款', '应付账款', '流动负债合计', '长期借款', '非流动负债合计',
    '负债合计', '实收资本（或股本）', '资本公积', '盈余公积', '未分配利润',
    '所有者权益（或股东权益）合计',
]

# 利润表核心字段
INCOME_CORE = [
    '营业总收入(万元)', '营业总成本(万元)',
    '其中：营业收入', '其中：营业成本', 
    '销售费用', '管理费用', '财务费用', '研发费用(利润表)',
    '投资收益', '三、营业利润', '四、利润总额',
    '减：所得税', '五、净利润', '归属于母公司所有者的净利润',
    '扣除非经常性损益后的净利润',
    '息税前利润(EBIT)', '息税折旧摊销前利润(EBITDA)',
    '稀释每股收益(元)', '基本每股收益（单季度）',
]

# 现金流量表核心字段
CASHFLOW_CORE = [
    '经营活动现金流入小计', '经营活动现金流出小计', '经营活动产生的现金流量净额',
    '投资活动现金流入小计', '投资活动现金流出小计', '投资活动产生的现金流量净额',
    '筹资活动现金流入小计', '筹资活动现金流出小计', '筹资活动产生的现金流量净额',
    '现金及现金等价物净增加额', '期初现金及现金等价物余额', '期末现金及现金等价物余额',
    '销售商品、提供劳务收到的现金', '购买商品、接受劳务支付的现金',
]

# 股本结构字段
EQUITY_STRUCTURE = [
    '总股本', '已上市流通A股', '已上市流通B股', '已上市流通H股',
    '自由流通股(股)', '受限流通A股(股)',
]

# 股东持仓字段
SHAREHOLDER_FIELDS = [
    '股东人数(户)', '第一大股东的持股数量', '十大流通股东持股数量合计(股)',
    '十大股东持股数量合计(股)', '机构总量（家）', '机构持股总量(股)',
    'QFII机构数', 'QFII持股量', '券商机构数', '券商持股量',
    '保险机构数', '保险持股量', '基金机构数', '基金持股量',
    '社保机构数', '社保持股量', '私募机构数', '私募持股量',
    '银行机构数(家)(机构持股)', '银行持股量(股)(机构持股)',
    '一般法人机构数(家)(机构持股)', '一般法人持股量(股)(机构持股)',
    '信托机构数(家)(机构持股)', '信托持股量(股)(机构持股)',
    '国家队持股数量（万股)',
]


class TdxFinanceAdapter(BaseDataAdapter):
    """
    通达信财务数据适配器

    基于 mootdx.affair，从通达信服务器按需下载并解析财务数据包 (gpcw*.zip)。
    覆盖核心财务报表指标、股本结构、股东持仓、机构持股等 585 个字段。

    Attributes:
        _report_cache: Dict[str, pd.DataFrame] — 报告期 → DataFrame 内存缓存
        _available_files: List[Dict] — 可用的财务文件列表（从 Affair.files() 获取）
    """

    def __init__(self):
        super().__init__()
        self.name = "tdx_finance"
        self.source_name = "tdx_finance"
        self.source_priority = 1  # 财务数据最高优先级（本地解析优先于网络API）
        self.connected = False
        
        # 内存缓存：{report_date_str: DataFrame}
        self._report_cache: Dict[str, pd.DataFrame] = {}
        
        # 可用的财务文件列表（延迟加载）
        self._available_files: Optional[List[Dict]] = None
        
        # 缓存目录
        self._cw_dir = CW_CACHE_DIR
        os.makedirs(self._cw_dir, exist_ok=True)

    # ============================================================
    # 抽象方法 stub 实现（非行情适配器，返回空）
    # ============================================================

    def get_stock_list(self) -> pd.DataFrame:
        """财务适配器不提供股票列表"""
        return pd.DataFrame()

    def get_daily_data(self, code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
        """财务适配器不提供日线数据"""
        return pd.DataFrame()

    def get_realtime_quote(self, codes: List[str]) -> pd.DataFrame:
        """财务适配器不提供实时行情"""
        return pd.DataFrame()

    # ============================================================
    # 生命周期管理
    # ============================================================

    def connect(self) -> bool:
        """
        连接财务数据源（加载可用文件列表）
        
        Returns:
            bool: 是否成功获取文件列表
        """
        try:
            self._available_files = self._get_file_list()
            self.connected = len(self._available_files) > 0
            if self.connected:
                logger.info(f"[tdx_finance] 连接成功，{len(self._available_files)} 个财务报告文件可用")
            else:
                logger.warning("[tdx_finance] 连接成功但无可用的财务文件")
            return self.connected
        except Exception as e:
            logger.error(f"[tdx_finance] 连接失败: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """断开连接，清空内存缓存"""
        self._report_cache.clear()
        self._available_files = None
        self.connected = False
        logger.info("[tdx_finance] 已断开")

    def is_available(self) -> bool:
        """检测财务数据源是否可用"""
        return True  # 财务适配器按需连接，始终标记为可用

    # ============================================================
    # 内部方法：文件管理 & 数据加载
    # ============================================================

    def _get_file_list(self) -> List[Dict]:
        """
        获取可用财务文件列表（优先使用缓存）
        
        Returns:
            [{'filename': 'gpcw20260331.zip', 'hash': '...', 'filesize': int}, ...]
        """
        if self._available_files is None:
            from mootdx.affair import Affair
            self._available_files = Affair.files()
            logger.debug(f"[tdx_finance] 获取到 {len(self._available_files)} 个财务文件")
        return self._available_files

    def _ensure_report_loaded(self, report_date: str) -> Optional[pd.DataFrame]:
        """
        确保指定报告期的数据已加载到内存缓存。
        如果本地无 .zip 文件，则从服务器下载。

        Args:
            report_date: 报告期日期，格式 YYYYMMDD，如 "20260331"

        Returns:
            DataFrame 或 None
        """
        filename = f"gpcw{report_date}.zip"
        
        # 1. 检查内存缓存
        if report_date in self._report_cache:
            return self._report_cache[report_date]
        
        # 2. 确保本地文件存在
        filepath = os.path.join(self._cw_dir, filename)
        if not os.path.exists(filepath):
            logger.info(f"[tdx_finance] 本地无 {filename}，正在从服务器下载...")
            try:
                from mootdx.affair import Affair
                Affair.fetch(downdir=self._cw_dir, filename=filename)
                time.sleep(0.5)  # 下载后稍等
            except Exception as e:
                logger.error(f"[tdx_finance] 下载 {filename} 失败: {e}")
                return None
        
        if not os.path.exists(filepath):
            logger.warning(f"[tdx_finance] 文件不存在: {filepath}")
            return None
        
        # 3. 解析并缓存
        try:
            from mootdx.affair import Affair
            df = Affair.parse(downdir=self._cw_dir, filename=filename)
            if df is not None and len(df) > 0:
                self._report_cache[report_date] = df
                logger.info(f"[tdx_finance] 已加载 {report_date} 财务数据: {len(df)} 只股票, {len(df.columns)} 字段")
                return df
            else:
                logger.warning(f"[tdx_finance] 解析 {filename} 返回空数据")
                return None
        except Exception as e:
            logger.error(f"[tdx_finance] 解析 {filename} 失败: {e}")
            return None

    def _get_stock_data(self, code: str, report_date: str) -> Optional[pd.Series]:
        """
        获取单只股票在指定报告期的所有财务数据

        Args:
            code: 股票代码，如 "600000"
            report_date: 报告期日期，如 "20260331"

        Returns:
            Series 或 None
        """
        df = self._ensure_report_loaded(report_date)
        if df is None or len(df) == 0:
            return None
        
        # 尝试多种代码格式，精确匹配优先
        for c in [code, code.zfill(6), code.lstrip('0').zfill(6) if code.lstrip('0') else '0']:
            if c in df.index:
                row = df.loc[c]
                # df.loc 可能返回 DataFrame（如果有重复索引）
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
                return row
        
        logger.debug(f"[tdx_finance] 股票 {code} 在 {report_date} 中未找到")
        return None

    def _extract_fields(self, series: pd.Series, fields: List[str]) -> Dict[str, Any]:
        """
        从 Series 中提取指定字段，过滤 NaN 和零值

        Args:
            series: 单行财务数据（Series 或 DataFrame 的第一行）
            fields: 需要的字段名列表

        Returns:
            {字段名: 值} 字典（已过滤 NaN 和零值）
        """
        if series is None:
            return {}
        
        # 如果意外传入 DataFrame，取第一行
        if isinstance(series, pd.DataFrame):
            series = series.iloc[0]
        
        if not isinstance(series, pd.Series) or len(series) == 0:
            return {}
        
        result = {}
        for field in fields:
            if field in series.index:
                val = series[field]
                try:
                    if pd.isna(val):
                        continue
                    if val == 0 or val == 0.0:
                        continue
                    result[field] = float(val) if isinstance(val, (int, float, np.floating)) else val
                except (TypeError, ValueError):
                    # 非标量值，跳过
                    continue
        return result

    # ============================================================
    # 公开 API：报告期管理
    # ============================================================

    def list_report_dates(self, valid_only: bool = True) -> List[str]:
        """
        列出可用的报告期日期。

        通达信服务器会预先创建未来报告期的空占位文件（如当前是2026年5月，
        但服务器已有 gpcw20260930.zip 占位文件，仅164字节无实际数据）。
        为避免混淆，默认只返回本地已有有效数据的报告期。

        Args:
            valid_only: True=仅返回本地已有有效数据的报告期（文件>10KB），
                       False=返回服务器列表中的所有日期

        Returns:
            ['20260331', '20251231', '20250930', ...] 按日期降序排列
        """
        files = self._get_file_list()
        dates = []
        for f in files:
            fn = f['filename']  # gpcw20260331.zip
            try:
                d = fn.replace('gpcw', '').replace('.zip', '')
                if d.isdigit() and len(d) == 8:
                    if valid_only:
                        # 仅保留本地有有效数据的报告期（跳过空占位文件）
                        filepath = os.path.join(self._cw_dir, fn)
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 10240:
                            dates.append(d)
                    else:
                        dates.append(d)
            except (ValueError, AttributeError):
                continue
        
        dates.sort(reverse=True)
        return dates

    def get_latest_report_date(self) -> Optional[str]:
        """
        获取最新的、本地已有有效数据的报告期日期。
        从最新日期往前找，跳过空占位文件（<1KB），直到找到可用的文件。
        如果本地没有有效文件，会自动下载最新文件。
        """
        dates = self.list_report_dates()
        for d in dates:
            filepath = os.path.join(self._cw_dir, f"gpcw{d}.zip")
            if os.path.exists(filepath) and os.path.getsize(filepath) > 10240:  # 有效文件通常 >10KB
                return d
        
        # 如果都没有有效本地文件，下载最新并返回
        if dates:
            latest = dates[0]
            logger.info(f"[tdx_finance] 本地无有效财务文件，下载最新报告期: {latest}")
            try:
                df = self._ensure_report_loaded(latest)
                if df is not None and len(df) > 0:
                    return latest
            except Exception as e:
                logger.error(f"[tdx_finance] 下载最新财务文件失败: {e}")
        
        return dates[0] if dates else None

    # ============================================================
    # 公开 API：财务数据查询
    # ============================================================

    def get_financial_indicators(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取核心财务指标（每股收益、ROE、增长率等）

        Args:
            code: 股票代码
            report_date: 报告期，默认使用最新

        Returns:
            {
                'code': '600000',
                'report_date': '20260331',
                'indicators': {
                    '基本每股收益': 0.52, '每股净资产': 22.63,
                    '净资产收益率': 2.14, '营业收入增长率(%)': 15.3, ...
                }
            }
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        indicators = self._extract_fields(series, KEY_INDICATORS)
        
        return {
            'code': code,
            'report_date': report_date,
            'indicators': indicators
        }

    def get_financial_history(self, code: str, fields: List[str] = None, 
                               limit: int = 10) -> Dict[str, Any]:
        """
        获取某只股票的历史财务数据（跨多个报告期）

        Args:
            code: 股票代码
            fields: 需要的字段列表，默认使用 KEY_INDICATORS
            limit: 最多返回几个报告期

        Returns:
            {
                'code': '600000',
                'history': [
                    {'report_date': '20260331', '基本每股收益': 0.52, ...},
                    {'report_date': '20251231', '基本每股收益': 2.01, ...},
                    ...
                ]
            }
        """
        if fields is None:
            fields = KEY_INDICATORS
        
        # 使用 valid_only=True 跳过未来的空占位文件，但要扫描足够多的日期
        # 以确保收集到 limit 条有效记录
        valid_dates = self.list_report_dates(valid_only=True)
        scan_limit = min(len(valid_dates), limit * 3)  # 最多扫描 limit*3 个，避免无限循环
        dates = valid_dates[:scan_limit]
        history = []
        
        for rd in dates:
            series = self._get_stock_data(code, rd)
            if series is not None:
                entry = {'report_date': rd}
                entry.update(self._extract_fields(series, fields))
                if len(entry) > 1:  # 至少有数据（不只是 report_date）
                    history.append(entry)
        
        return {
            'code': code,
            'fields': fields,
            'history': history
        }

    def get_balance_sheet(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取资产负债表核心数据

        Args:
            code: 股票代码
            report_date: 报告期，默认最新

        Returns:
            {'code': '600000', 'report_date': '20260331', 
             'balance_sheet': {'资产总计': ..., '负债合计': ..., ...}}
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        bs_data = self._extract_fields(series, BALANCE_SHEET_CORE)
        
        return {
            'code': code,
            'report_date': report_date,
            'balance_sheet': bs_data
        }

    def get_income_statement(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取利润表核心数据

        Args:
            code: 股票代码
            report_date: 报告期，默认最新

        Returns:
            {'code': '600000', 'report_date': '20260331', 
             'income': {'营业收入': ..., '净利润': ..., ...}}
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        income_data = self._extract_fields(series, INCOME_CORE)
        
        return {
            'code': code,
            'report_date': report_date,
            'income_statement': income_data
        }

    def get_cashflow_statement(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取现金流量表核心数据

        Args:
            code: 股票代码
            report_date: 报告期，默认最新

        Returns:
            {'code': '600000', 'report_date': '20260331', 
             'cashflow': {'经营活动产生的现金流量净额': ..., ...}}
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        cf_data = self._extract_fields(series, CASHFLOW_CORE)
        
        return {
            'code': code,
            'report_date': report_date,
            'cashflow': cf_data
        }

    def get_equity_structure(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取股本结构数据

        Args:
            code: 股票代码
            report_date: 报告期，默认最新

        Returns:
            {'code': '600000', 'report_date': '20260331', 
             'equity': {'总股本': ..., '已上市流通A股': ..., ...}}
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        equity_data = self._extract_fields(series, EQUITY_STRUCTURE)
        
        return {
            'code': code,
            'report_date': report_date,
            'equity_structure': equity_data
        }

    def get_shareholder_info(self, code: str, report_date: str = None) -> Dict[str, Any]:
        """
        获取股东与机构持仓数据

        Args:
            code: 股票代码
            report_date: 报告期，默认最新

        Returns:
            {'code': '600000', 'report_date': '20260331', 
             'shareholders': {'股东人数(户)': ..., '机构总量（家）': ..., ...}}
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        sh_data = self._extract_fields(series, SHAREHOLDER_FIELDS)
        
        return {
            'code': code,
            'report_date': report_date,
            'shareholders': sh_data
        }

    def get_full_report(self, code: str, report_date: str = None, 
                         field_filter: List[str] = None) -> Dict[str, Any]:
        """
        获取某只股票在指定报告期的完整财务数据（全部字段）。

        Args:
            code: 股票代码
            report_date: 报告期，默认最新
            field_filter: 可选的字段过滤列表，如不指定则返回所有非空字段

        Returns:
            {
                'code': '600000', 'report_date': '20260331',
                'data': {'基本每股收益': 0.52, '每股净资产': 22.63, ...}
            }
        """
        if report_date is None:
            report_date = self.get_latest_report_date()
            if not report_date:
                return {'code': code, 'error': '无可用报告期'}
        
        series = self._get_stock_data(code, report_date)
        if series is None:
            return {'code': code, 'report_date': report_date, 'error': '未找到数据'}
        
        if field_filter:
            data = self._extract_fields(series, field_filter)
        else:
            # 返回所有非空的命名列（排除 colNNN 占位列）
            data = {}
            for col, val in series.items():
                if pd.notna(val) and val != 0:
                    if not col.startswith('col'):  # 过滤未命名的占位列
                        data[col] = float(val) if isinstance(val, (int, float)) else val
        
        return {
            'code': code,
            'report_date': report_date,
            'data': data
        }

    def get_financial_summary(self, code: str) -> Dict[str, Any]:
        """
        获取某只股票的财务概览（结合最新所有分类数据）

        Args:
            code: 股票代码

        Returns:
            包含 indicators、balance_sheet、income、cashflow、equity、shareholders 的汇总
        """
        latest = self.get_latest_report_date()
        if not latest:
            return {'code': code, 'error': '无可用报告期'}
        
        # 并行加载同一报告期的各类数据（相同缓存，不会重复解析）
        summary = {
            'code': code,
            'report_date': latest,
            'indicators': self.get_financial_indicators(code, latest).get('indicators', {}),
            'balance_sheet': self.get_balance_sheet(code, latest).get('balance_sheet', {}),
            'income': self.get_income_statement(code, latest).get('income_statement', {}),
            'cashflow': self.get_cashflow_statement(code, latest).get('cashflow', {}),
            'equity': self.get_equity_structure(code, latest).get('equity_structure', {}),
            'shareholders': self.get_shareholder_info(code, latest).get('shareholders', {}),
        }
        
        return summary
