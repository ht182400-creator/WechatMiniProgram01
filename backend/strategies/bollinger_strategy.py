# -*- coding: utf-8 -*-
"""
布林带策略
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class BollingerStrategy(BaseStrategy):
    """布林带策略"""
    
    name = "布林带 (BOLL)"
    description = "价格触及下轨买入，触及上轨卖出"
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化布林带策略
        
        Args:
            params: {
                'bb_period': 布林带周期 (默认20)
                'bb_std': 标准差倍数 (默认2)
                'buy_threshold': 买入阈值 (默认0.1, 即触及下轨附近)
                'sell_threshold': 卖出阈值 (默认0.9, 即触及上轨附近)
            }
        """
        default_params = {
            'bb_period': 20,
            'bb_std': 2,
            'buy_threshold': 0.1,
            'sell_threshold': 0.9,
        }
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
    
    def on_init(self, data: pd.DataFrame) -> None:
        """策略初始化"""
        self.data = data.copy()
        
        period = self.params['bb_period']
        std = self.params['bb_std']
        
        # 计算布林带
        self.data['bb_middle'] = self.data['close'].rolling(window=period).mean()
        self.data['bb_std'] = self.data['close'].rolling(window=period).std()
        self.data['bb_upper'] = self.data['bb_middle'] + std * self.data['bb_std']
        self.data['bb_lower'] = self.data['bb_middle'] - std * self.data['bb_std']
        
        # 布林带位置
        self.data['bb_position'] = (self.data['close'] - self.data['bb_lower']) / \
                                   (self.data['bb_upper'] - self.data['bb_lower'] + 0.0001)
        
        logger.info(f"布林带策略初始化: 周期={period}, 标准差={std}")
    
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
            
            # 价格触及下轨附近 (买入)
            if row['bb_position'] <= self.params['buy_threshold']:
                signal_type = SignalType.BUY
                reason = f"价格触及下轨: 位置={row['bb_position']:.2%}, 价格={row['close']:.2f}"
            
            # 价格触及上轨附近 (卖出)
            elif row['bb_position'] >= self.params['sell_threshold']:
                signal_type = SignalType.SELL
                reason = f"价格触及上轨: 位置={row['bb_position']:.2%}, 价格={row['close']:.2f}"
            
            signal = TradingSignal(
                date=date_str,
                signal=signal_type,
                price=row['close'],
                reason=reason,
                confidence=abs(row['bb_position'] - 0.5) * 2  # 置信度基于偏离程度
            )
            signals.append(signal)
            self.add_signal(signal)
        
        return signals
