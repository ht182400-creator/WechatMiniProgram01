# -*- coding: utf-8 -*-
"""
股票数据API
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from adapters import get_data_source_manager
from factors import TechnicalFactors
from models import get_db_session, Stock, DailyKLine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", summary="获取股票列表")
async def get_stock_list() -> Dict[str, Any]:
    """获取所有股票列表"""
    try:
        data_manager = get_data_source_manager()
        df = data_manager.get_stock_list()
        
        if df.empty:
            return {"total": 0, "stocks": []}
        
        return {
            "total": len(df),
            "stocks": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")


@router.get("/search", summary="搜索股票")
async def search_stock(keyword: str = Query(..., min_length=1, description="搜索关键词")) -> Dict[str, Any]:
    """搜索股票"""
    try:
        data_manager = get_data_source_manager()
        df = data_manager.get_stock_list()
        
        if df.empty:
            return {"total": 0, "stocks": []}
        
        # 模糊搜索
        mask = df['name'].str.contains(keyword, na=False) | df['code'].str.contains(keyword, na=False)
        result = df[mask]
        
        return {
            "total": len(result),
            "stocks": result.head(50).to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/daily", summary="获取日线数据")
async def get_daily_data(
    code: str = Query(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型: qfq/hfq/none")
) -> Dict[str, Any]:
    """获取股票日线数据"""
    try:
        # 默认获取近一年数据
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        data_manager = get_data_source_manager()
        df = data_manager.get_daily_data(code, start_date, end_date, adjust)
        
        if df.empty:
            return {"total": 0, "data": [], "code": code}
        
        return {
            "total": len(df),
            "code": code,
            "start_date": start_date,
            "end_date": end_date,
            "adjust": adjust,
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/realtime", summary="获取实时行情")
async def get_realtime_quote(codes: str = Query(..., description="股票代码，多个用逗号分隔")) -> Dict[str, Any]:
    """获取股票实时行情"""
    try:
        code_list = [c.strip() for c in codes.split(',')]
        
        if len(code_list) > 50:
            raise HTTPException(status_code=400, detail="最多支持50个股票代码")
        
        data_manager = get_data_source_manager()
        df = data_manager.get_realtime_quote(code_list)
        
        return {
            "total": len(df),
            "data": df.to_dict('records') if not df.empty else []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.get("/indicators", summary="获取技术指标")
async def get_technical_indicators(
    code: str = Query(..., description="股票代码"),
    days: int = Query(60, description="数据天数")
) -> Dict[str, Any]:
    """获取股票技术指标"""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")  # 多取30天用于计算
        
        data_manager = get_data_source_manager()
        df = data_manager.get_daily_data(code, start_date, end_date)
        
        if df.empty:
            return {"code": code, "indicators": {}}
        
        # 计算技术指标
        factors = TechnicalFactors(df)
        df_with_indicators = factors.add_all_indicators()
        
        # 返回最近days条数据
        latest = df_with_indicators.tail(days)
        
        # 提取最新指标值
        latest_row = latest.iloc[-1]
        indicators = {
            'date': str(latest_row.name.date()) if hasattr(latest_row.name, 'date') else str(latest_row.name),
            'close': float(latest_row['close']),
            'open': float(latest_row['open']),
            'high': float(latest_row['high']),
            'low': float(latest_row['low']),
            'volume': float(latest_row['volume']),
            # 均线指标
            'sma_5': float(latest_row['sma_5']) if pd.notna(latest_row.get('sma_5')) else None,
            'sma_10': float(latest_row['sma_10']) if pd.notna(latest_row.get('sma_10')) else None,
            'sma_20': float(latest_row['sma_20']) if pd.notna(latest_row.get('sma_20')) else None,
            'sma_60': float(latest_row['sma_60']) if pd.notna(latest_row.get('sma_60')) else None,
            'sma_120': float(latest_row['sma_120']) if pd.notna(latest_row.get('sma_120')) else None,
            # RSI 指标
            'rsi_14': float(latest_row['rsi_14']) if pd.notna(latest_row.get('rsi_14')) else None,
            # MACD 指标
            'macd': float(latest_row['macd']) if pd.notna(latest_row.get('macd')) else None,
            'macd_signal': float(latest_row['macd_signal']) if pd.notna(latest_row.get('macd_signal')) else None,
            'macd_hist': float(latest_row['macd_hist']) if pd.notna(latest_row.get('macd_hist')) else None,
            # KDJ 指标
            'kdj_k': float(latest_row['kdj_k']) if pd.notna(latest_row.get('kdj_k')) else None,
            'kdj_d': float(latest_row['kdj_d']) if pd.notna(latest_row.get('kdj_d')) else None,
            'kdj_j': float(latest_row['kdj_j']) if pd.notna(latest_row.get('kdj_j')) else None,
            # 布林带指标
            'bb_upper_20': float(latest_row['bb_upper_20']) if pd.notna(latest_row.get('bb_upper_20')) else None,
            'bb_middle_20': float(latest_row['bb_middle_20']) if pd.notna(latest_row.get('bb_middle_20')) else None,
            'bb_lower_20': float(latest_row['bb_lower_20']) if pd.notna(latest_row.get('bb_lower_20')) else None,
            'bb_position_20': float(latest_row['bb_position_20']) if pd.notna(latest_row.get('bb_position_20')) else None,
            # ATR 指标
            'atr_14': float(latest_row['atr_14']) if pd.notna(latest_row.get('atr_14')) else None,
            # OBV 指标
            'obv': float(latest_row['obv']) if pd.notna(latest_row.get('obv')) else None,
            # 波动率
            'volatility_20': float(latest_row['volatility_20']) if pd.notna(latest_row.get('volatility_20')) else None,
            # 信号指标
            'ma5_ma20_cross': int(latest_row['ma5_ma20_cross']) if pd.notna(latest_row.get('ma5_ma20_cross')) else None,
            'macd_cross': int(latest_row['macd_cross']) if pd.notna(latest_row.get('macd_cross')) else None,
            'kdj_cross': int(latest_row['kdj_cross']) if pd.notna(latest_row.get('kdj_cross')) else None,
        }
        
        # 过滤掉 None 值
        indicators = {k: v for k, v in indicators.items() if v is not None}
        
        return {
            "code": code,
            "indicators": indicators,
            "data_count": len(latest)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算指标失败: {str(e)}")


@router.get("/chart", summary="获取K线图表数据")
async def get_chart_data(
    code: str = Query(..., description="股票代码"),
    chart_type: str = Query("daily", description="图表类型: daily/weekly/monthly"),
    days: int = Query(120, description="数据天数"),
    adjust: str = Query("qfq", description="复权类型: qfq(前复权)/hfq(后复权)/none(不复权)")
) -> Dict[str, Any]:
    """
    获取K线图表数据

    支持日线(daily)、周线(weekly)、月线(monthly)三种周期。
    周/月线通过重采样日线数据生成。
    支持前复权(qfq)、后复权(hfq)、不复权(none)。
    """
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        # 周/月线需要更多原始数据来重采样
        multiplier = {'daily': 1, 'weekly': 7, 'monthly': 30}.get(chart_type, 1)
        start_date = (datetime.now() - timedelta(days=days * multiplier + 60)).strftime("%Y-%m-%d")

        data_manager = get_data_source_manager()
        df = data_manager.get_daily_data(code, start_date, end_date, adjust)

        if df.empty:
            return {"code": code, "chart_data": []}

        # ── 周/月线重采样（将日线聚合为周线/月线）──
        if chart_type in ('weekly', 'monthly'):
            # 确保 date 列为 datetime 类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')

            # 设置重采样频率
            freq = 'W' if chart_type == 'weekly' else 'ME'

            # OHLC 重采样：开盘取第一个，收盘取最后一个，高低取最值，成交量求和
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            # 兼容不同列名的情况
            if 'amount' in df.columns:
                ohlc_dict['amount'] = 'sum'

            df = df.resample(freq).apply(ohlc_dict)

            # 展平多级列名（resample + apply 多列时会创建 MultiIndex）
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 移除空行（非交易日产生的 NaN）
            df = df.dropna(subset=['open', 'close'], how='all')
            df = df.reset_index()
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

        # 计算技术指标
        factors = TechnicalFactors(df)
        df_with_indicators = factors.add_all_indicators()

        # 根据请求数量截取（周/月线条数更少）
        limit = days * (3 if chart_type != 'daily' else 1)
        chart_df = df_with_indicators.tail(limit)

        # 准备ECharts数据格式
        chart_data = []
        for _, row in chart_df.iterrows():
            date_val = row.get('date', '')
            # 格式化日期：周线显示周一日期，月线显示当月1号
            if hasattr(date_val, 'date'):
                date_str = str(date_val.date())
            elif hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)

            chart_data.append({
                "date": date_str,
                "open": float(row['open']),
                "close": float(row['close']),
                "high": float(row['high']),
                "low": float(row['low']),
                "volume": float(row['volume']),
                # 均线指标
                "ma5": float(row['sma_5']) if pd.notna(row.get('sma_5')) else None,
                "ma10": float(row['sma_10']) if pd.notna(row.get('sma_10')) else None,
                "ma20": float(row['sma_20']) if pd.notna(row.get('sma_20')) else None,
                "ma30": float(row['sma_30']) if pd.notna(row.get('sma_30')) else None,
                "ma60": float(row['sma_60']) if pd.notna(row.get('sma_60')) else None,
                "ma120": float(row['sma_120']) if pd.notna(row.get('sma_120')) else None,
                # MACD 指标
                "macd": float(row['macd']) if pd.notna(row.get('macd')) else None,
                "macd_signal": float(row['macd_signal']) if pd.notna(row.get('macd_signal')) else None,
                "macd_hist": float(row['macd_hist']) if pd.notna(row.get('macd_hist')) else None,
                # RSI 指标
                "rsi": float(row['rsi_14']) if pd.notna(row.get('rsi_14')) else None,
                # KDJ 指标
                "kdj_k": float(row['kdj_k']) if pd.notna(row.get('kdj_k')) else None,
                "kdj_d": float(row['kdj_d']) if pd.notna(row.get('kdj_d')) else None,
                "kdj_j": float(row['kdj_j']) if pd.notna(row.get('kdj_j')) else None,
                # 布林带指标
                "bb_upper": float(row['bb_upper_20']) if pd.notna(row.get('bb_upper_20')) else None,
                "bb_middle": float(row['bb_middle_20']) if pd.notna(row.get('bb_middle_20')) else None,
                "bb_lower": float(row['bb_lower_20']) if pd.notna(row.get('bb_lower_20')) else None,
                # ATR 指标
                "atr": float(row['atr_14']) if pd.notna(row.get('atr_14')) else None,
            })

        return {
            "code": code,
            "chart_type": chart_type,
            "chart_data": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")


@router.get("/depth", summary="获取十档盘口数据")
async def get_stock_depth(
    code: str = Query(..., description="股票代码")
) -> Dict[str, Any]:
    """
    获取股票十档盘口数据（买卖各10档）
    
    返回数据包含：
    - bids: 买单盘口 [价格, 成交量]
    - asks: 卖单盘口 [价格, 成交量]
    """
    try:
        data_manager = get_data_source_manager()
        
        # 尝试获取十档数据
        try:
            df = data_manager.get_depth_data(code)
            
            if df is not None and not df.empty:
                return {
                    "code": code,
                    "timestamp": datetime.now().isoformat(),
                    "bids": df[['bid_price', 'bid_volume']].head(10).values.tolist() if 'bid_price' in df.columns else [],
                    "asks": df[['ask_price', 'ask_volume']].head(10).values.tolist() if 'ask_price' in df.columns else [],
                }
        except Exception:
            pass
        
        # 十档数据不可用时，通过实时行情获取当前价并生成模拟五档
        try:
            quote_df = data_manager.get_realtime_quote([code])
            if not quote_df.empty:
                row = quote_df.iloc[0]
                current_price = float(row.get('price', row.get('close', 0)))
                bid_price = current_price - 0.01
                ask_price = current_price + 0.01
                
                bids = [[round(bid_price - i * 0.01, 2), 1000 + i * 100] for i in range(10)]
                asks = [[round(ask_price + i * 0.01, 2), 1000 + i * 100] for i in range(10)]
                
                return {
                    "code": code,
                    "timestamp": datetime.now().isoformat(),
                    "current_price": current_price,
                    "bids": bids,
                    "asks": asks,
                }
        except Exception as e:
            logger.warning(f"盘口数据fallback失败: {e}")
        
        return {
            "code": code,
            "timestamp": datetime.now().isoformat(),
            "bids": [],
            "asks": [],
            "message": "十档数据暂不可用"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取盘口数据失败: {str(e)}")


@router.get("/minute", summary="获取分钟级K线数据")
async def get_minute_data(
    code: str = Query(..., description="股票代码"),
    period: str = Query("5", description="周期: 1/5/15/30/60 分钟")
) -> Dict[str, Any]:
    """
    获取股票分钟级K线数据
    
    Args:
        code: 股票代码
        period: K线周期（1/5/15/30/60分钟）
    """
    try:
        # 兼容前端传入 "1min" / "5min" 等格式
        period_str = str(period).replace('min', '').replace(' ', '').strip()
        period = int(period_str)
        if period not in [1, 5, 15, 30, 60]:
            raise HTTPException(status_code=400, detail="周期仅支持 1/5/15/30/60 分钟")
        
        data_manager = get_data_source_manager()
        
        # 获取分钟数据
        try:
            df = data_manager.get_minute_data(code, period)
            
            if df is not None and not df.empty:
                minute_data = []
                for _, row in df.tail(100).iterrows():
                    minute_data.append({
                        "time": str(row['datetime']) if 'datetime' in row else str(row['date']),
                        "open": float(row['open']),
                        "close": float(row['close']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "volume": float(row['volume']),
                    })
                
                return {
                    "code": code,
                    "period": period,
                    "total": len(minute_data),
                    "data": minute_data
                }
        except Exception as e:
            logger.warning(f"获取分钟数据失败: {str(e)}")
        
        # 如果数据源不支持，返回提示
        return {
            "code": code,
            "period": period,
            "total": 0,
            "data": [],
            "message": "分钟级数据暂不可用，请检查数据源配置"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分钟数据失败: {str(e)}")


@router.get("/intraday", summary="获取分时明细数据（回车查看当日K线）")
async def get_intraday_data(
    code: str = Query(..., description="股票代码"),
    date: str = Query("", description="日期 YYYY-MM-DD，默认当天")
) -> Dict[str, Any]:
    """
    获取股票分时明细数据，用于回车弹窗展示
    
    返回：分钟K线列表 + 分笔成交列表 + 当日统计
    """
    from datetime import date as _date, datetime as _dt, timedelta as _td
    try:
        data_manager = get_data_source_manager()
        target_date = date or _date.today().strftime('%Y-%m-%d')
        
        # ── 获取1分钟K线 ──
        minute_list = []
        minute_df = None
        
        # 尝试各适配器获取分钟数据
        try:
            minute_df = data_manager.get_minute_data(code, period=1)
            if minute_df is not None and not minute_df.empty:
                # 如果指定了日期且不是今天，尝试过滤（本地数据源支持历史日期）
                if target_date != _date.today().strftime('%Y-%m-%d'):
                    if 'datetime' in minute_df.columns:
                        minute_df = minute_df[minute_df['datetime'].astype(str).str.startswith(target_date)]
                    elif 'date' in minute_df.columns:
                        minute_df = minute_df[minute_df['date'].astype(str).str.startswith(target_date)]
                
                for _, row in minute_df.iterrows():
                    minute_list.append({
                        "time": str(row.get('time', row.get('datetime', ''))),
                        "price": float(row.get('close', row.get('price', 0))),
                        "open": float(row.get('open', 0)),
                        "high": float(row.get('high', 0)),
                        "low": float(row.get('low', 0)),
                        "volume": float(row.get('volume', 0)),
                        "amount": float(row.get('amount', 0)),
                    })
        except Exception as e:
            logger.debug(f"获取 {code} 分钟数据失败: {e}")
        
        # ── 获取分笔成交（最近100条）──
        transaction_list = []
        try:
            tx_df = data_manager.get_transaction_data(code, limit=100)
            if tx_df is not None and not tx_df.empty:
                for _, row in tx_df.iterrows():
                    transaction_list.append({
                        "time": str(row.get('time', '')),
                        "price": float(row.get('price', 0)),
                        "volume": float(row.get('volume', 0)),
                        "direction": str(row.get('direction', 'N')),
                    })
        except Exception as e:
            logger.debug(f"获取 {code} 分笔数据失败: {e}")
        
        # ── 计算分时统计 ──
        stats = {}
        if minute_list:
            prices = [m["price"] for m in minute_list]
            volumes = [m["volume"] for m in minute_list]
            open_price = minute_list[0]["open"]
            
            stats = {
                "open": round(open_price, 2),
                "close": round(prices[-1], 2),
                "high": round(max(m["high"] for m in minute_list), 2) if minute_list else 0,
                "low": round(min(m["low"] for m in minute_list), 2) if minute_list else 0,
                "total_volume": sum(volumes),
                "change": round(prices[-1] - open_price, 2) if open_price else 0,
                "pct_change": round((prices[-1] - open_price) / open_price * 100, 2) if open_price and open_price > 0 else 0,
            }
        
        return {
            "code": code,
            "date": target_date,
            "stats": stats,
            "minutes": minute_list,
            "transactions": transaction_list,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分时数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分时数据失败: {str(e)}")


@router.get("/transaction", summary="获取分笔成交数据")
async def get_transaction_data(
    code: str = Query(..., description="股票代码"),
    limit: int = Query(100, description="返回条数，默认100")
) -> Dict[str, Any]:
    """
    获取股票分笔成交数据
    
    返回每笔成交的时间、价格、成交量、买卖方向
    """
    try:
        if limit > 500:
            limit = 500
        
        data_manager = get_data_source_manager()
        
        try:
            df = data_manager.get_transaction_data(code, limit)
            
            if df is not None and not df.empty:
                transaction_data = []
                for _, row in df.iterrows():
                    transaction_data.append({
                        "time": str(row.get('time', '')),
                        "price": float(row['price']),
                        "volume": float(row['volume']),
                        "direction": str(row.get('direction', 'N')),  # N-中性 B-买 S-卖
                        "amount": float(row.get('amount', 0)),
                    })
                
                return {
                    "code": code,
                    "total": len(transaction_data),
                    "data": transaction_data
                }
        except Exception:
            pass
        
        return {
            "code": code,
            "total": 0,
            "data": [],
            "message": "分笔成交数据暂不可用"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成交数据失败: {str(e)}")
