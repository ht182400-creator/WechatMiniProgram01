# -*- coding: utf-8 -*-
"""
数据库模型
@author: StockQuant Team
@date: 2026-05-19
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True, comment='股票代码')
    name = Column(String(100), nullable=False, comment='股票名称')
    market = Column(String(10), comment='市场: sh, sz, bj')
    industry = Column(String(100), comment='所属行业')
    list_date = Column(String(10), comment='上市日期')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DailyKLine(Base):
    """日线K线数据表"""
    __tablename__ = 'daily_kline'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment='股票代码')
    date = Column(String(10), nullable=False, index=True, comment='交易日期')
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, comment='收盘价')
    volume = Column(Float, comment='成交量')
    amount = Column(Float, comment='成交额')
    change = Column(Float, comment='涨跌额')
    pct_change = Column(Float, comment='涨跌幅')
    turnover = Column(Float, comment='换手率')
    adjust_flag = Column(String(5), default='qfq', comment='复权类型')
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class TechnicalIndicator(Base):
    """技术指标缓存表"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    indicators = Column(JSON, comment='技术指标JSON')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class BacktestRecord(Base):
    """回测记录表"""
    __tablename__ = 'backtest_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(50), nullable=False, comment='策略名称')
    stock_code = Column(String(10), comment='股票代码')
    start_date = Column(String(10), comment='回测开始日期')
    end_date = Column(String(10), comment='回测结束日期')
    initial_cash = Column(Float, comment='初始资金')
    final_capital = Column(Float, comment='最终资金')
    total_return = Column(Float, comment='总收益率')
    annualized_return = Column(Float, comment='年化收益率')
    max_drawdown = Column(Float, comment='最大回撤')
    sharpe_ratio = Column(Float, comment='夏普比率')
    win_rate = Column(Float, comment='胜率')
    total_trades = Column(Integer, comment='交易次数')
    params = Column(JSON, comment='策略参数')
    created_at = Column(DateTime, default=func.now())


class PredictionRecord(Base):
    """预测记录表"""
    __tablename__ = 'prediction_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment='股票代码')
    date = Column(String(10), nullable=False, comment='预测日期')
    model_name = Column(String(50), comment='模型名称')
    current_price = Column(Float, comment='当前价格')
    predicted_price = Column(Float, comment='预测价格')
    predicted_direction = Column(String(10), comment='预测方向: up, down, neutral')
    confidence = Column(Float, comment='置信度')
    actual_price = Column(Float, comment='实际价格(后续更新)')
    accuracy = Column(Float, comment='准确率(后续计算)')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, comment='配置键')
    config_value = Column(Text, comment='配置值')
    description = Column(String(500), comment='配置说明')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
