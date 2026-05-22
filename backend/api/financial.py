# -*- coding: utf-8 -*-
"""
财务数据API
@author: StockQuant Team
@date: 2026-05-21
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List

from adapters import get_data_source_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/report-dates", summary="获取可用报告期列表")
async def get_report_dates(
    all_dates: bool = Query(False, description="是否显示全部日期（含无数据的未来占位文件）")
) -> Dict[str, Any]:
    """
    列出可用的财务报告期日期。
    默认仅返回本地已有有效数据的报告期，避免显示未来日期的空占位。
    传入 all_dates=true 可查看服务器全部文件列表。
    """
    try:
        data_manager = get_data_source_manager()
        dates = data_manager.list_report_dates(valid_only=not all_dates)
        return {
            "total": len(dates),
            "report_dates": dates,
            "filters_applied": "valid_only" if not all_dates else "all"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告期列表失败: {str(e)}")


@router.get("/indicators", summary="获取核心财务指标")
async def get_financial_indicators(
    code: str = Query(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期日期 YYYYMMDD，默认最新")
) -> Dict[str, Any]:
    """
    获取核心财务指标（每股收益、ROE、增长率等）
    
    示例: /api/financial/indicators?code=600000&report_date=20260331
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_financial_indicators(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务指标失败: {str(e)}")


@router.get("/history", summary="获取历史财务数据")
async def get_financial_history(
    code: str = Query(..., description="股票代码"),
    limit: int = Query(10, description="最多返回几个报告期", ge=1, le=50)
) -> Dict[str, Any]:
    """
    获取某只股票跨多个报告期的财务数据趋势
    
    示例: /api/financial/history?code=600000&limit=8
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_financial_history(code, limit=limit)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务历史失败: {str(e)}")


@router.get("/balance-sheet", summary="获取资产负债表")
async def get_balance_sheet(
    code: str = Query(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期日期 YYYYMMDD")
) -> Dict[str, Any]:
    """获取资产负债表核心数据"""
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_balance_sheet(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产负债表失败: {str(e)}")


@router.get("/income", summary="获取利润表")
async def get_income_statement(
    code: str = Query(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期日期 YYYYMMDD")
) -> Dict[str, Any]:
    """获取利润表核心数据"""
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_income_statement(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取利润表失败: {str(e)}")


@router.get("/cashflow", summary="获取现金流量表")
async def get_cashflow_statement(
    code: str = Query(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期日期 YYYYMMDD")
) -> Dict[str, Any]:
    """获取现金流量表核心数据"""
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_cashflow_statement(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取现金流量表失败: {str(e)}")


@router.get("/equity", summary="获取股本结构")
async def get_equity_structure(
    code: str = Query(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期日期 YYYYMMDD")
) -> Dict[str, Any]:
    """获取股本结构数据（总股本、流通股本等）"""
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_equity_structure(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股本结构失败: {str(e)}")


@router.get("/shareholders", summary="获取股东持仓信息")
async def get_shareholder_info(
    code: str = Query(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期日期 YYYYMMDD")
) -> Dict[str, Any]:
    """获取股东人数、机构持仓等数据"""
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_shareholder_info(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股东持仓失败: {str(e)}")


@router.get("/summary", summary="获取财务概览")
async def get_financial_summary(
    code: str = Query(..., description="股票代码")
) -> Dict[str, Any]:
    """
    获取某只股票的财务全貌（单次请求返回所有分类）
    
    包含：核心指标、资产负债表、利润表、现金流量表、股本结构、股东持仓
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_financial_summary(code)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务概览失败: {str(e)}")
