# -*- coding: utf-8 -*-
"""
策略模块 - 支持多策略注册
"""
from .base_strategy import BaseStrategy, TradingSignal, SignalType, Position, Trade
from .ma_cross_strategy import MACrossStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_strategy import BollingerStrategy

# 策略注册表
STRATEGY_REGISTRY = {
    'ma_cross': MACrossStrategy,
    'rsi': RSIStrategy,
    'macd': MACDStrategy,
    'bollinger': BollingerStrategy,
}


def get_strategy(strategy_name: str, params: dict = None) -> BaseStrategy:
    """
    获取策略实例
    
    Args:
        strategy_name: 策略名称
        params: 策略参数
        
    Returns:
        策略实例
    """
    strategy_class = STRATEGY_REGISTRY.get(strategy_name.lower())
    if strategy_class is None:
        raise ValueError(f"未知的策略: {strategy_name}")
    return strategy_class(params)


def list_strategies() -> list:
    """列出所有可用策略"""
    return [
        {
            'name': name,
            'class': cls.__name__,
            'description': cls.description
        }
        for name, cls in STRATEGY_REGISTRY.items()
    ]


__all__ = [
    'BaseStrategy',
    'TradingSignal', 
    'SignalType',
    'Position',
    'Trade',
    'MACrossStrategy',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerStrategy',
    'STRATEGY_REGISTRY',
    'get_strategy',
    'list_strategies'
]
