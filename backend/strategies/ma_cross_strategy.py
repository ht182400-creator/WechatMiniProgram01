# -*- coding: utf-8 -*-
"""
双均线交叉策略
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Optional, Dict
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, TradingSignal, SignalType

logger = logging.getLogger(__name__)


class MACrossStrategy(BaseStrategy):
    """双均线交叉策略"""
    
    name = "均线交叉 (MA)"
    description = "金叉买入，死叉卖出"
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化均线交叉策略
        
        Args:
            params: {
                'short_window': 短期均线周期 (默认5)
                'long_window': 长期均线周期 (默认20)
                'initial_capital': 初始资金 (默认100000)
            }
        """
        default_params = {
            'short_window': 5,
            'long_window': 20,
        }
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
    
    def on_init(self, data: pd.DataFrame) -> None:
        """策略初始化"""
        self.data = data.copy()
        
        # 计算均线
        short = self.params['short_window']
        long = self.params['long_window']
        
        self.data['sma_short'] = self.data['close'].rolling(window=short).mean()
        self.data['sma_long'] = self.data['close'].rolling(window=long).mean()
        
        # 计算均线交叉
        self.data['ma_cross'] = np.where(
            self.data['sma_short'] > self.data['sma_long'], 1, -1
        )
        self.data['ma_cross_change'] = self.data['ma_cross'].diff()
        
        logger.info(f"均线策略初始化: 短期={short}, 长期={long}")
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """生成交易信号"""
        self.on_init(data)
        
        signals = []
        df = self.data.dropna()
        
        for idx, row in df.iterrows():
            signal_type = SignalType.HOLD
            reason = ""
            
            # 从 date 列获取日期，而非依赖索引
            date_val = row['date']
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
            
            # 金叉 (短期均线上穿长期均线)
            if row['ma_cross_change'] > 0:
                signal_type = SignalType.BUY
                reason = f"金叉: SMA{self.params['short_window']}={row['sma_short']:.2f} > SMA{self.params['long_window']}={row['sma_long']:.2f}"
            
            # 死叉 (短期均线下穿长期均线)
            elif row['ma_cross_change'] < 0:
                signal_type = SignalType.SELL
                reason = f"死叉: SMA{self.params['short_window']}={row['sma_short']:.2f} < SMA{self.params['long_window']}={row['sma_long']:.2f}"
            
            signal = TradingSignal(
                date=date_str,
                signal=signal_type,
                price=row['close'],
                reason=reason,
                confidence=1.0
            )
            signals.append(signal)
            self.add_signal(signal)
        
        return signals
    
    def get_signal_stats(self) -> Dict:
        """获取信号统计"""
        if not self.signals:
            return {}
        
        buy_signals = [s for s in self.signals if s.signal == SignalType.BUY]
        sell_signals = [s for s in self.signals if s.signal == SignalType.SELL]
        
        return {
            'total_signals': len(self.signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'hold_signals': len(self.signals) - len(buy_signals) - len(sell_signals)
        }
