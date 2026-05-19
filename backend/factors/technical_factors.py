# -*- coding: utf-8 -*-
"""
技术因子计算模块
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TechnicalFactors:
    """技术指标因子计算"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化技术因子计算器
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
        """
        self.data = data.copy()
        self._validate_data()
    
    def _validate_data(self):
        """验证数据格式"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in self.data.columns]
        if missing:
            raise ValueError(f"缺少必需列: {missing}")
    
    def add_all_indicators(self) -> pd.DataFrame:
        """添加所有技术指标"""
        df = self.data.copy()
        df = self.add_moving_averages(df)
        df = self.add_macd(df)
        df = self.add_rsi(df)
        df = self.add_bollinger_bands(df)
        df = self.add_kdj(df)
        df = self.add_obv(df)
        df = self.add_atr(df)
        df = self.add_volatility(df)
        return df
    
    def add_moving_averages(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """添加移动平均线"""
        df = df or self.data.copy()
        
        # 简单移动平均 SMA
        for period in [5, 10, 20, 30, 60, 120, 250]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        
        # 指数移动平均 EMA
        for period in [12, 26, 50, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # MACD 均线
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # 金叉死叉信号
        df['ma5_ma20_cross'] = np.where(
            df['sma_5'] > df['sma_20'], 1, -1
        )
        df['ma10_ma60_cross'] = np.where(
            df['sma_10'] > df['sma_60'], 1, -1
        )
        
        return df
    
    def add_macd(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """添加 MACD 指标"""
        df = df or self.data.copy()
        
        # MACD 基本计算
        df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - \
                     df['close'].ewm(span=26, adjust=False).mean()
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # MACD 金叉死叉信号
        df['macd_cross'] = np.where(df['macd'] > df['macd_signal'], 1, -1)
        df['macd_hist_change'] = df['macd_hist'].diff()
        
        return df
    
    def add_rsi(self, df: Optional[pd.DataFrame] = None, period: int = 14) -> pd.DataFrame:
        """添加 RSI 相对强弱指标"""
        df = df or self.data.copy()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # 超买超卖信号
        df['rsi_signal'] = np.where(df[f'rsi_{period}'] > 70, 'overbought',
                           np.where(df[f'rsi_{period}'] < 30, 'oversold', 'neutral'))
        
        return df
    
    def add_bollinger_bands(self, df: Optional[pd.DataFrame] = None, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """添加布林带指标"""
        df = df or self.data.copy()
        
        df[f'bb_middle_{period}'] = df['close'].rolling(window=period).mean()
        df[f'bb_std_{period}'] = df['close'].rolling(window=period).std()
        
        df[f'bb_upper_{period}'] = df[f'bb_middle_{period}'] + std_dev * df[f'bb_std_{period}']
        df[f'bb_lower_{period}'] = df[f'bb_middle_{period}'] - std_dev * df[f'bb_std_{period}']
        
        # 布林带位置
        df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / \
                                       (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])
        
        return df
    
    def add_kdj(self, df: Optional[pd.DataFrame] = None, period: int = 9) -> pd.DataFrame:
        """添加 KDJ 随机指标"""
        df = df or self.data.copy()
        
        low_n = df['low'].rolling(window=period, min_periods=1).min()
        high_n = df['high'].rolling(window=period, min_periods=1).max()
        
        df['kdj_k'] = 100 * (df['close'] - low_n) / (high_n - low_n).replace(0, 1)
        df['kdj_d'] = df['kdj_k'].rolling(window=3).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        # KDJ 金叉死叉信号
        df['kdj_cross'] = np.where(df['kdj_k'] > df['kdj_d'], 1, -1)
        
        return df
    
    def add_obv(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """添加 OBV 能量潮指标"""
        df = df or self.data.copy()
        
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        df['obv'] = obv
        df['obv_ma'] = df['obv'].rolling(window=20).mean()
        
        return df
    
    def add_atr(self, df: Optional[pd.DataFrame] = None, period: int = 14) -> pd.DataFrame:
        """添加 ATR 平均真实波幅"""
        df = df or self.data.copy()
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df[f'atr_{period}'] = true_range.rolling(window=period).mean()
        
        return df
    
    def add_volatility(self, df: Optional[pd.DataFrame] = None, period: int = 20) -> pd.DataFrame:
        """添加波动率指标"""
        df = df or self.data.copy()
        
        # 历史波动率
        df[f'volatility_{period}'] = df['close'].pct_change().rolling(window=period).std() * np.sqrt(252) * 100
        
        return df
    
    def add_volume_indicators(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """添加成交量指标"""
        df = df or self.data.copy()
        
        # 成交量移动平均
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        
        # 量比
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        
        # 换手率 (需要额外数据)
        if 'turnover' not in df.columns:
            df['turnover'] = 0.0
        
        return df
    
    def get_latest_indicators(self, n: int = 1) -> dict:
        """获取最新的技术指标值"""
        if self.data.empty:
            return {}
        
        df = self.add_all_indicators()
        latest = df.tail(n).iloc[-1].to_dict()
        
        # 提取关键指标
        indicators = {
            'close': latest.get('close'),
            'sma_5': latest.get('sma_5'),
            'sma_20': latest.get('sma_20'),
            'sma_60': latest.get('sma_60'),
            'rsi_14': latest.get('rsi_14'),
            'macd': latest.get('macd'),
            'macd_signal': latest.get('macd_signal'),
            'macd_hist': latest.get('macd_hist'),
            'kdj_k': latest.get('kdj_k'),
            'kdj_d': latest.get('kdj_d'),
            'kdj_j': latest.get('kdj_j'),
        }
        
        return {k: v for k, v in indicators.items() if v is not None and not pd.isna(v)}
