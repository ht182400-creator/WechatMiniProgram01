# -*- coding: utf-8 -*-
"""
MACD 策略
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class MACDStrategy(BaseStrategy):
    """MACD 策略"""
    
    name = "MACD指标 (MACD)"
    description = "MACD金叉买入，死叉卖出"
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化 MACD 策略
        
        Args:
            params: {
                'fast_period': 快线周期 (默认12)
                'slow_period': 慢线周期 (默认26)
                'signal_period': 信号线周期 (默认9)
            }
        """
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
        }
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
    
    def on_init(self, data: pd.DataFrame) -> None:
        """策略初始化"""
        self.data = data.copy()
        
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        signal = self.params['signal_period']
        
        # 计算 MACD
        ema_fast = self.data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.data['close'].ewm(span=slow, adjust=False).mean()
        
        self.data['macd'] = ema_fast - ema_slow
        self.data['macd_signal'] = self.data['macd'].ewm(span=signal, adjust=False).mean()
        self.data['macd_hist'] = self.data['macd'] - self.data['macd_signal']
        
        # MACD 交叉
        self.data['macd_cross'] = np.where(
            self.data['macd'] > self.data['macd_signal'], 1, -1
        )
        self.data['macd_cross_change'] = self.data['macd_cross'].diff()
        
        logger.info(f"MACD策略初始化: 快线={fast}, 慢线={slow}, 信号线={signal}")
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """生成交易信号"""
        self.on_init(data)
        
        signals = []
        df = self.data.dropna()
        
        for idx, row in df.iterrows():
            signal_type = SignalType.HOLD
            reason = ""
            
            # 从 date 列获取日期
            date_val = row['date']
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
            
            # MACD 金叉
            if row['macd_cross_change'] > 0:
                signal_type = SignalType.BUY
                reason = f"MACD金叉: MACD={row['macd']:.4f}, Signal={row['macd_signal']:.4f}"
            
            # MACD 死叉
            elif row['macd_cross_change'] < 0:
                signal_type = SignalType.SELL
                reason = f"MACD死叉: MACD={row['macd']:.4f}, Signal={row['macd_signal']:.4f}"
            
            signal = TradingSignal(
                date=date_str,
                signal=signal_type,
                price=row['close'],
                reason=reason,
                confidence=abs(row['macd_hist']) / (abs(row['macd']) + 0.0001)
            )
            signals.append(signal)
            self.add_signal(signal)
        
        return signals
