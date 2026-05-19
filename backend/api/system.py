# -*- coding: utf-8 -*-
"""
系统管理API
@author: StockQuant Team
@date: 2026-05-19
"""

from fastapi import APIRouter
from typing import Dict, Any
import psutil
from pathlib import Path

from ..config import settings
from ..cache import ParquetCache
from ..adapters import get_data_source_manager

router = APIRouter()


@router.get("/info", summary="系统信息")
async def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    cache = ParquetCache()
    cache_info = cache.get_cache_info()
    
    return {
        "name": "股票量化分析与预测系统",
        "version": "3.0.0",
        "data_dir": str(settings.DATA_DIR),
        "cache_dir": str(settings.CACHE_DIR),
        "cache_info": cache_info,
        "python_version": "3.9+",
        "platform": "Windows/Linux"
    }


@router.get("/datasources", summary="数据源状态")
async def get_datasources() -> Dict[str, Any]:
    """获取数据源连接状态"""
    data_manager = get_data_source_manager()
    
    return {
        "total": len(data_manager.adapters),
        "sources": {
            name: {
                "available": adapter.is_available(),
                "connected": adapter.connected
            }
            for name, adapter in data_manager.adapters.items()
        }
    }


@router.post("/cache/clear", summary="清空缓存")
async def clear_cache() -> Dict[str, Any]:
    """清空所有缓存"""
    cache = ParquetCache()
    count = cache.clear_all()
    return {"success": True, "cleared": count}


@router.get("/cache/stats", summary="缓存统计")
async def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    cache = ParquetCache()
    return cache.get_cache_info()


@router.get("/health", summary="健康检查")
async def health_check() -> Dict[str, Any]:
    """系统健康检查"""
    try:
        # 检查磁盘空间
        disk = psutil.disk_usage('.')
        
        # 检查数据源
        data_manager = get_data_source_manager()
        datasource_ok = data_manager.is_healthy()
        
        return {
            "status": "healthy" if datasource_ok else "degraded",
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_used_percent": disk.percent,
            "datasource_available": datasource_ok
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
