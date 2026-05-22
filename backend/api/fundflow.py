# -*- coding: utf-8 -*-
"""
资金流向与热点数据 API
=======================
提供个股资金流向、板块资金流向、概念板块、机构持仓等端点。

按 preparereadme.MD 5.5 资金与热点服务设计：
  - akshare: 主力/散户净流入、概念板块、板块资金排行
  - tushare: 主力净流入金额、前十大股东、研报评级

@author: StockQuant Team
@date: 2026-05-21
"""

import logging
from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional, Dict, Any

from adapters import get_data_source_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 个股资金流向
# ============================================================

@router.get("/individual/{code}", summary="获取个股资金流向")
async def get_fund_flow(
    code: str = Path(..., description="股票代码"),
    days: int = Query(5, description="最近 N 个交易日", ge=1, le=30),
    source: Optional[str] = Query(None, description="数据源: akshare / tushare，默认自动选最优")
) -> Dict[str, Any]:
    """
    获取个股资金流向数据，包括主力净流入、超大单/大单/中单/小单的买卖情况。

    数据来源优先级：akshare > tushare（两者互补）。

    示例: /api/fundflow/individual/600000?days=5
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_fund_flow(code, days=days, preferred=source)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资金流向失败: {str(e)}")


# ============================================================
# 板块资金流向
# ============================================================

@router.get("/sector", summary="获取板块资金流向排行")
async def get_sector_fund_flow(
    indicator: str = Query("今日", description="指标周期: 今日 / 5日 / 10日"),
    days: int = Query(5, description="排行数量", ge=5, le=30)
) -> Dict[str, Any]:
    """
    获取板块资金流向排行榜（主力净流入前N名）。

    示例: /api/fundflow/sector?indicator=今日&days=10
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_sector_fund_flow(indicator=indicator, days=days)
        if 'error' in result:
            return {"sectors": [], "indicator": indicator, "total": 0, "message": result['error']}
        return result
    except Exception as e:
        logger.error(f"板块资金流向异常: {type(e).__name__}: {e}")
        return {"sectors": [], "indicator": indicator, "total": 0, "message": f"服务暂不可用: {type(e).__name__}"}


# ============================================================
# 概念板块
# ============================================================

@router.get("/concept/list", summary="获取概念板块列表")
async def get_concept_list() -> Dict[str, Any]:
    """
    获取所有概念板块名称列表。

    示例: /api/fundflow/concept/list
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_concept_list()
        if 'error' in result:
            return {"concepts": [], "total": 0, "message": result['error']}
        return result
    except Exception as e:
        logger.error(f"概念列表异常: {type(e).__name__}: {e}")
        return {"concepts": [], "total": 0, "message": f"服务暂不可用: {type(e).__name__}"}


@router.get("/concept/stocks", summary="获取概念板块成分股")
async def get_concept_stocks(
    concept: str = Query(..., description="概念名称，如 人工智能")
) -> Dict[str, Any]:
    """
    获取指定概念板块的成分股列表。

    示例: /api/fundflow/concept/stocks?concept=人工智能
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_concept_stocks(concept)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概念成分股失败: {str(e)}")


# ============================================================
# 机构持仓与研究
# ============================================================

@router.get("/holders/{code}", summary="获取前十大股东")
async def get_top10_holders(
    code: str = Path(..., description="股票代码"),
    report_date: Optional[str] = Query(None, description="报告期 YYYYMMDD，默认最新")
) -> Dict[str, Any]:
    """
    获取前十大股东和前十大流通股东名单及持股比例。

    数据来源: tushare

    示例: /api/fundflow/holders/600000
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_top10_holders(code, report_date)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股东信息失败: {str(e)}")


@router.get("/research/{code}", summary="获取机构研报")
async def get_research_report(
    code: str = Path(..., description="股票代码"),
    limit: int = Query(10, description="最多返回几篇", ge=1, le=20)
) -> Dict[str, Any]:
    """
    获取机构研报列表，包括评级、目标价、研究员等信息。

    数据来源: tushare

    示例: /api/fundflow/research/600000?limit=5
    """
    try:
        data_manager = get_data_source_manager()
        result = data_manager.get_research_report(code, limit=limit)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取研报失败: {str(e)}")
