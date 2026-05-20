# -*- coding: utf-8 -*-
"""
RSI 策略
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """RSI 超买超卖策略"""
    
    name = "RSI超买超卖 (RSI)"
    description = "RSI低于30买入，高于70卖出"
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化 RSI 策略
        
        Args:
            params: {
                'rsi_period': RSI周期 (默认14)
                'oversold': 超卖阈值 (默认30)
                'overbought': 超买阈值 (默认70)
            }
        """
        default_params = {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
        }
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
    
    def on_init(self, data: pd.DataFrame) -> None:
        """策略初始化"""
        self.data = data.copy()
        
        period = self.params['rsi_period']
        
        # 计算 RSI
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        self.data['rsi'] = 100 - (100 / (1 + rs))
        
        logger.info(f"RSI策略初始化: 周期={period}, 超卖={self.params['oversold']}, 超买={self.params['overbought']}")
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """生成交易信号"""
        self.on_init(data)
        
        signals = []
        df = self.data.dropna()
        
        prev_rsi = None
        for idx, row in df.iterrows():
            signal_type = SignalType.HOLD
            reason = ""
            
            # 从 date 列获取日期
            date_val = row['date']
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
            
            # RSI 从超卖区域上穿
            if prev_rsi is not None and prev_rsi < self.params['oversold'] and row['rsi'] >= self.params['oversold']:
                signal_type = SignalType.BUY
                reason = f"RSI从超卖回升: {prev_rsi:.2f} -> {row['rsi']:.2f}"
            
            # RSI 从超买区域下穿
            elif prev_rsi is not None and prev_rsi > self.params['overbought'] and row['rsi'] <= self.params['overbought']:
                signal_type = SignalType.SELL
                reason = f"RSI从超买回落: {prev_rsi:.2f} -> {row['rsi']:.2f}"
            
            prev_rsi = row['rsi']
            
            signal = TradingSignal(
                date=date_str,
                signal=signal_type,
                price=row['close'],
                reason=reason,
                confidence=abs(row['rsi'] - 50) / 50  # 置信度基于RSI偏离程度
            )
            signals.append(signal)
            self.add_signal(signal)
        
        return signals
