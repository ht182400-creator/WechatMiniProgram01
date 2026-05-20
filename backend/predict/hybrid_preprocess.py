# -*- coding: utf-8 -*-
"""
混合模型数据预处理模块
为 LSTM + LightGBM 混合模型准备特征数据

@author: StockQuant Team
@date: 2026-05-20
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from typing import Tuple, Optional


class HybridDataPreprocessor:
    """
    混合模型的数据预处理
    
    将原始日线数据分离为：
    - LSTM 输入：时序数据（价格、成交量等）
    - LightGBM 输入：技术指标特征
    """
    
    def __init__(self, seq_length: int = 20, forecast_horizon: int = 5):
        """
        Args:
            seq_length: LSTM 回看窗口长度
            forecast_horizon: 预测周期（天数）
        """
        self.seq_length = seq_length
        self.forecast_horizon = forecast_horizon
        self.scaler_lstm = MinMaxScaler()
        self.scaler_lgb = StandardScaler()
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: 原始日线数据
            
        Returns:
            添加了技术指标的 DataFrame
        """
        df = df.copy()
        
        # 移动平均线
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma_ratio'] = df['ma5'] / df['ma20']
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 波动率指标
        df['daily_return'] = df['close'].pct_change()
        df['volatility'] = df['daily_return'].rolling(20).std()
        
        # 成交量指标
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # 布林带
        df['bb_mid'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_mid'] + 2 * bb_std
        df['bb_lower'] = df['bb_mid'] - 2 * bb_std
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = df['tr'].rolling(14).mean()
        
        # OBV (On-Balance Volume)
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['obv'] = obv
        
        # KDJ 指标
        low14 = df['low'].rolling(14).min()
        high14 = df['high'].rolling(14).max()
        df['rsv'] = (df['close'] - low14) / (high14 - low14) * 100
        df['kdj_k'] = df['rsv'].ewm(com=2, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[Tuple[np.ndarray, np.ndarray], np.ndarray]:
        """
        从原始日线数据提取特征，分离 LSTM 和 LightGBM 的输入
        
        Args:
            df: 日线数据，包含 open, high, low, close, volume
            
        Returns:
            X_lstm: (samples, seq_length, features) 用于 LSTM
            X_lgb: (samples, n_features) 用于 LightGBM
            y: 目标标签 (0/1，涨跌)
        """
        df = self._calculate_technical_indicators(df)
        
        # 创建目标标签：未来 forecast_horizon 日的收益率
        future_return = df['close'].pct_change(self.forecast_horizon).shift(-self.forecast_horizon)
        df['label_class'] = (future_return > 0.01).astype(int)  # 1: 上涨 >1%，0: 不涨
        
        # 定义特征列
        lstm_feature_cols = ['close', 'volume', 'ma5', 'ma10', 'rsi', 'macd', 
                            'volatility', 'volume_ratio', 'atr', 'obv']
        
        lgb_feature_cols = ['rsi', 'macd_hist', 'volatility', 'volume_ratio',
                          'ma_ratio', 'bb_upper', 'bb_lower', 'atr', 'obv',
                          'kdj_k', 'kdj_d', 'kdj_j']
        
        # 移除包含 NaN 的行
        required_cols = list(set(lstm_feature_cols + lgb_feature_cols + ['label_class', 'close', 'volume']))
        df_clean = df.dropna(subset=required_cols)
        
        # 确保有足够的数据
        if len(df_clean) < self.seq_length + self.forecast_horizon + 10:
            raise ValueError(f"数据不足，需要至少 {self.seq_length + self.forecast_horizon + 10} 条数据")
        
        # 构建样本
        X_lstm = []
        X_lgb = []
        y = []
        
        # 重置索引以便正确迭代
        df_clean = df_clean.reset_index(drop=True)
        
        for i in range(self.seq_length, len(df_clean) - self.forecast_horizon):
            # LSTM 输入：前 seq_length 天的时序数据
            seq_data = df_clean[lstm_feature_cols].iloc[i - self.seq_length:i].values
            X_lstm.append(seq_data)
            
            # LightGBM 输入：当天及历史特征
            features = df_clean.iloc[i][lgb_feature_cols].values
            X_lgb.append(features)
            
            # 目标
            y.append(df_clean['label_class'].iloc[i])
        
        return (np.array(X_lstm), np.array(X_lgb)), np.array(y)
    
    def get_latest_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取最新数据的特征（用于预测）
        
        Args:
            df: 日线数据
            
        Returns:
            last_lstm: (1, seq_length, features) 最新 LSTM 输入
            last_lgb: (1, n_features) 最新 LightGBM 输入
        """
        (X_lstm, X_lgb), _ = self.prepare_features(df)
        
        # 返回最后一条数据
        return X_lstm[-1:], X_lgb[-1:]
    
    def get_feature_names_lgb(self) -> list:
        """返回 LightGBM 使用的特征名称"""
        return ['rsi', 'macd_hist', 'volatility', 'volume_ratio',
                'ma_ratio', 'bb_upper', 'bb_lower', 'atr', 'obv',
                'kdj_k', 'kdj_d', 'kdj_j']
    
    def get_feature_names_lstm(self) -> list:
        """返回 LSTM 使用的特征名称"""
        return ['close', 'volume', 'ma5', 'ma10', 'rsi', 'macd', 
                'volatility', 'volume_ratio', 'atr', 'obv']
