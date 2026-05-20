# -*- coding: utf-8 -*-
"""
回测引擎
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

from strategies import BaseStrategy, TradingSignal, SignalType, Position, Trade
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_cash: float = 100000.0      # 初始资金
    commission: float = 0.0003           # 手续费 0.03%
    slippage: float = 0.0001            # 滑点 0.01%
    position_size: int = 100            # 最小交易单位
    

@dataclass
class BacktestResult:
    """回测结果"""
    total_trades: int = 0               # 总交易次数
    winning_trades: int = 0             # 盈利次数
    losing_trades: int = 0              # 亏损次数
    total_return: float = 0.0           # 总收益率
    annualized_return: float = 0.0      # 年化收益率
    max_drawdown: float = 0.0           # 最大回撤
    sharpe_ratio: float = 0.0           # 夏普比率
    win_rate: float = 0.0               # 胜率
    avg_profit: float = 0.0             # 平均盈利
    avg_loss: float = 0.0               # 平均亏损
    profit_factor: float = 0.0          # 盈亏比
    final_capital: float = 0.0          # 最终资金
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        初始化回测引擎
        
        Args:
            config: 回测配置
        """
        self.config = config or BacktestConfig(
            initial_cash=settings.BACKTEST_INITIAL_CASH,
            commission=settings.BACKTEST_COMMISSION,
            slippage=settings.BACKTEST_SLIPPAGE
        )
        
        self.strategy: Optional[BaseStrategy] = None
        self.data: Optional[pd.DataFrame] = None
        self.current_capital = self.config.initial_cash
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
    def set_strategy(self, strategy: BaseStrategy) -> None:
        """设置策略"""
        self.strategy = strategy
        logger.info(f"设置策略: {strategy.name}")
    
    def set_data(self, data: pd.DataFrame) -> None:
        """设置回测数据"""
        self.data = data.copy()
        logger.info(f"设置回测数据: {len(data)} 条K线")
    
    def run(self) -> BacktestResult:
        """
        运行回测
        
        Returns:
            回测结果
        """
        if self.strategy is None:
            raise ValueError("请先设置策略")
        
        if self.data is None or self.data.empty:
            raise ValueError("请先设置回测数据")
        
        logger.info("=" * 50)
        logger.info(f"开始回测: {self.strategy.name}")
        logger.info(f"初始资金: {self.config.initial_cash:,.2f}")
        logger.info(f"手续费: {self.config.commission:.2%}")
        logger.info(f"滑点: {self.config.slippage:.2%}")
        logger.info("=" * 50)
        
        # 重置状态
        self.current_capital = self.config.initial_cash
        self.position = None
        self.trades = []
        self.equity_curve = []
        
        # 生成交易信号
        signals = self.strategy.generate_signals(self.data)
        
        # 模拟交易
        for signal in signals:
            self._execute_signal(signal)
        
        # 平仓（如果有持仓）
        if self.position and not self.data.empty:
            last_row = self.data.iloc[-1]
            # 从 date 列获取日期，而非索引
            last_date = last_row['date']
            if hasattr(last_date, 'strftime'):
                date_str = last_date.strftime('%Y-%m-%d')
            else:
                date_str = str(last_date)
            self._close_position(date=date_str, price=last_row['close'])
        
        # 计算回测指标
        result = self._calculate_metrics()
        
        logger.info("=" * 50)
        logger.info(f"回测完成!")
        logger.info(f"总收益率: {result.total_return:.2%}")
        logger.info(f"年化收益率: {result.annualized_return:.2%}")
        logger.info(f"最大回撤: {result.max_drawdown:.2%}")
        logger.info(f"夏普比率: {result.sharpe_ratio:.2f}")
        logger.info(f"胜率: {result.win_rate:.2%}")
        logger.info("=" * 50)
        
        return result
    
    def _execute_signal(self, signal: TradingSignal) -> None:
        """执行交易信号"""
        # 每次都记录权益曲线
        self._record_equity(signal.date)
        
        if signal.signal == SignalType.HOLD:
            return
        
        if signal.signal == SignalType.BUY and self.position is None:
            self._open_position(signal)
        elif signal.signal == SignalType.SELL and self.position is not None:
            self._close_position(signal.date, signal.price)
    
    def _open_position(self, signal: TradingSignal) -> None:
        """开仓"""
        # 计算可买入数量（向下取整到最小交易单位）
        buy_amount = self.current_capital * 0.95 / signal.price  # 预留5%手续费
        quantity = int(buy_amount / self.config.position_size) * self.config.position_size
        
        if quantity <= 0:
            logger.warning(f"资金不足，无法买入: {signal.date}")
            return
        
        # 扣除手续费和滑点
        cost = quantity * signal.price
        commission = cost * self.config.commission
        slippage_cost = cost * self.config.slippage
        total_cost = cost + commission + slippage_cost
        
        if total_cost > self.current_capital:
            logger.warning(f"资金不足: 需要{total_cost:.2f}, 持有{self.current_capital:.2f}")
            return
        
        # 创建持仓
        self.position = Position(
            code=self.strategy.name,
            quantity=quantity,
            avg_cost=signal.price,
            current_price=signal.price
        )
        
        self.current_capital -= total_cost
        
        # 记录交易
        trade = Trade(
            date=signal.date,
            action='buy',
            code=self.position.code,
            price=signal.price,
            quantity=quantity,
            commission=commission,
            slippage=slippage_cost,
            total_amount=total_cost
        )
        self.trades.append(trade)
        
        logger.info(f"[买入] {signal.date} 价格:{signal.price:.2f} 数量:{quantity} 总额:{total_cost:.2f} 原因:{signal.reason}")
    
    def _close_position(self, date: str, price: float) -> None:
        """平仓"""
        if self.position is None:
            return
        
        # 计算卖出金额
        revenue = self.position.quantity * price
        commission = revenue * self.config.commission
        slippage_cost = revenue * self.config.slippage
        net_revenue = revenue - commission - slippage_cost
        
        self.current_capital += net_revenue
        
        # 记录交易
        trade = Trade(
            date=date,
            action='sell',
            code=self.position.code,
            price=price,
            quantity=self.position.quantity,
            commission=commission,
            slippage=slippage_cost,
            total_amount=net_revenue
        )
        self.trades.append(trade)
        
        profit = net_revenue - (self.position.quantity * self.position.avg_cost)
        logger.info(f"[卖出] {date} 价格:{price:.2f} 数量:{self.position.quantity} 盈利:{profit:.2f}")
        
        # 清空持仓
        self.position = None
    
    def _record_equity(self, date: str) -> None:
        """记录权益曲线"""
        position_value = 0
        if self.position is not None:
            # 使用持仓均价或最新价格计算市值
            last_price = self.position.current_price or self.position.avg_cost
            position_value = self.position.quantity * last_price
        
        self.equity_curve.append({
            'date': date,
            'cash': round(self.current_capital, 2),
            'position_value': round(position_value, 2),
            'total_value': round(self.current_capital + position_value, 2)
        })
    
    def _calculate_metrics(self) -> BacktestResult:
        """计算回测指标"""
        if not self.trades:
            return BacktestResult(final_capital=self.current_capital)
        
        # 统计交易
        buy_trades = [t for t in self.trades if t.action == 'buy']
        sell_trades = [t for t in self.trades if t.action == 'sell']
        
        # 计算盈亏
        profits = []
        for i in range(0, len(sell_trades)):
            buy = buy_trades[min(i, len(buy_trades) - 1)]
            sell = sell_trades[i]
            profit = sell.total_amount - buy.total_amount
            profits.append(profit)
        
        winning_trades = len([p for p in profits if p > 0])
        losing_trades = len([p for p in profits if p < 0])
        
        total_return = (self.current_capital - self.config.initial_cash) / self.config.initial_cash
        
        # 计算年化收益率
        if len(self.equity_curve) >= 2:
            days = (pd.to_datetime(self.equity_curve[-1]['date']) - 
                   pd.to_datetime(self.equity_curve[0]['date'])).days
            years = max(days / 365, 0.01)
            annualized_return = (1 + total_return) ** (1 / years) - 1
        else:
            annualized_return = 0
        
        # 计算最大回撤
        max_drawdown = 0
        if self.equity_curve:
            values = [e['total_value'] for e in self.equity_curve]
            peak = values[0]
            for v in values:
                if v > peak:
                    peak = v
                drawdown = (peak - v) / peak
                max_drawdown = max(max_drawdown, drawdown)
        
        # 计算夏普比率
        sharpe_ratio = 0
        if len(self.equity_curve) > 1:
            returns = pd.Series([e['total_value'] for e in self.equity_curve]).pct_change().dropna()
            if returns.std() != 0:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        
        return BacktestResult(
            total_trades=len(sell_trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=winning_trades / len(sell_trades) if sell_trades else 0,
            avg_profit=np.mean([p for p in profits if p > 0]) if winning_trades > 0 else 0,
            avg_loss=np.mean([p for p in profits if p < 0]) if losing_trades > 0 else 0,
            profit_factor=abs(np.mean([p for p in profits if p > 0]) / 
                            np.mean([p for p in profits if p < 0])) if losing_trades > 0 and winning_trades > 0 else 0,
            final_capital=self.current_capital,
            trades=self.trades,
            equity_curve=self.equity_curve
        )
