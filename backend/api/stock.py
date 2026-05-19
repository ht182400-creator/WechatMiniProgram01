# -*- coding: utf-8 -*-
"""
股票数据API
@author: StockQuant Team
@date: 2026-05-19
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from ..adapters import get_data_source_manager
from ..factors import TechnicalFactors
from ..models import get_db_session, Stock, DailyKLine

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
            'sma_5': float(latest_row['sma_5']) if pd.notna(latest_row.get('sma_5')) else None,
            'sma_20': float(latest_row['sma_20']) if pd.notna(latest_row.get('sma_20')) else None,
            'sma_60': float(latest_row['sma_60']) if pd.notna(latest_row.get('sma_60')) else None,
            'rsi_14': float(latest_row['rsi_14']) if pd.notna(latest_row.get('rsi_14')) else None,
            'macd': float(latest_row['macd']) if pd.notna(latest_row.get('macd')) else None,
            'macd_signal': float(latest_row['macd_signal']) if pd.notna(latest_row.get('macd_signal')) else None,
            'kdj_k': float(latest_row['kdj_k']) if pd.notna(latest_row.get('kdj_k')) else None,
            'kdj_d': float(latest_row['kdj_d']) if pd.notna(latest_row.get('kdj_d')) else None,
            'kdj_j': float(latest_row['kdj_j']) if pd.notna(latest_row.get('kdj_j')) else None,
        }
        
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
    days: int = Query(120, description="数据天数")
) -> Dict[str, Any]:
    """获取K线图表数据"""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
        
        data_manager = get_data_source_manager()
        df = data_manager.get_daily_data(code, start_date, end_date)
        
        if df.empty:
            return {"code": code, "chart_data": []}
        
        # 计算技术指标
        factors = TechnicalFactors(df)
        df_with_indicators = factors.add_all_indicators()
        
        # 准备ECharts数据格式
        chart_data = []
        for _, row in df_with_indicators.tail(days).iterrows():
            chart_data.append({
                "date": str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date']),
                "open": float(row['open']),
                "close": float(row['close']),
                "high": float(row['high']),
                "low": float(row['low']),
                "volume": float(row['volume']),
                "ma5": float(row['sma_5']) if pd.notna(row.get('sma_5')) else None,
                "ma20": float(row['sma_20']) if pd.notna(row.get('sma_20')) else None,
                "ma60": float(row['sma_60']) if pd.notna(row.get('sma_60')) else None,
                "rsi": float(row['rsi_14']) if pd.notna(row.get('rsi_14')) else None,
                "macd": float(row['macd']) if pd.notna(row.get('macd')) else None,
                "macd_signal": float(row['macd_signal']) if pd.notna(row.get('macd_signal')) else None,
                "macd_hist": float(row['macd_hist']) if pd.notna(row.get('macd_hist')) else None,
            })
        
        return {
            "code": code,
            "chart_type": chart_type,
            "chart_data": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")
