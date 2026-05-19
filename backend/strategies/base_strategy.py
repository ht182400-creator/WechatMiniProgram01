# -*- coding: utf-8 -*-
"""
策略基类定义
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """交易信号类型"""
    BUY = "buy"           # 买入
    SELL = "sell"         # 卖出
    HOLD = "hold"         # 持有
    CLOSE_LONG = "close_long"   # 平多
    CLOSE_SHORT = "close_short" # 平空


@dataclass
class TradingSignal:
    """交易信号"""
    date: str
    signal: SignalType
    price: float
    quantity: int = 0
    reason: str = ""
    confidence: float = 0.0  # 信号置信度 0-1


@dataclass
class Position:
    """持仓信息"""
    code: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def profit_loss(self) -> float:
        return (self.current_price - self.avg_cost) * self.quantity
    
    @property
    def profit_loss_pct(self) -> float:
        if self.avg_cost == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost * 100


@dataclass
class Trade:
    """交易记录"""
    date: str
    action: str  # buy, sell
    code: str
    price: float
    quantity: int
    commission: float
    slippage: float
    total_amount: float


class BaseStrategy(ABC):
    """策略基类"""
    
    name: str = "BaseStrategy"
    description: str = ""
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化策略
        
        Args:
            params: 策略参数字典
        """
        self.params = params or {}
        self.data: Optional[pd.DataFrame] = None
        self.signals: List[TradingSignal] = []
    
    @abstractmethod
    def on_init(self, data: pd.DataFrame) -> None:
        """
        策略初始化
        
        Args:
            data: K线数据
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[TradingSignal]:
        """
        生成交易信号
        
        Args:
            data: K线数据
            
        Returns:
            交易信号列表
        """
        pass
    
    def add_signal(self, signal: TradingSignal) -> None:
        """添加交易信号"""
        self.signals.append(signal)
    
    def get_latest_signal(self) -> Optional[TradingSignal]:
        """获取最新交易信号"""
        return self.signals[-1] if self.signals else None
    
    def validate_params(self) -> bool:
        """验证策略参数"""
        return True
    
    def get_params(self) -> Dict:
        """获取策略参数"""
        return self.params.copy()
    
    def set_params(self, params: Dict) -> None:
        """设置策略参数"""
        self.params.update(params)
