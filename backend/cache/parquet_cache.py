# -*- coding: utf-8 -*-
"""
Parquet 缓存模块
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from pathlib import Path
from typing import Optional, Any
import pandas as pd
from datetime import datetime, timedelta
import hashlib

from ..config import settings

logger = logging.getLogger(__name__)


class ParquetCache:
    """Parquet 格式缓存管理器"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expire_minutes = settings.CACHE_EXPIRE_MINUTES
        self.max_size = settings.CACHE_MAX_SIZE
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 对key进行hash，避免特殊字符问题
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.parquet"
    
    def _is_expired(self, file_path: Path) -> bool:
        """检查缓存是否过期"""
        if not file_path.exists():
            return True
        
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            expire_time = datetime.now() - timedelta(minutes=self.expire_minutes)
            return mtime < expire_time
        except Exception:
            return True
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        try:
            cache_path = self._get_cache_path(key)
            
            if self._is_expired(cache_path):
                # 删除过期缓存
                if cache_path.exists():
                    cache_path.unlink()
                return None
            
            if cache_path.exists():
                df = pd.read_parquet(cache_path)
                logger.debug(f"缓存读取成功: {key} ({len(df)} 行)")
                return df
            
            return None
        except Exception as e:
            logger.error(f"读取缓存失败 [{key}]: {e}")
            return None
    
    def set(self, key: str, data: pd.DataFrame) -> bool:
        """设置缓存数据"""
        try:
            if data is None or data.empty:
                return False
            
            cache_path = self._get_cache_path(key)
            data.to_parquet(cache_path, index=True)
            logger.debug(f"缓存写入成功: {key} ({len(data)} 行)")
            return True
        except Exception as e:
            logger.error(f"写入缓存失败 [{key}]: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {e}")
            return False
    
    def clear_all(self) -> int:
        """清空所有缓存"""
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.parquet"):
                cache_file.unlink()
                count += 1
            logger.info(f"已清空 {count} 个缓存文件")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
        return count
    
    def get_cache_size(self) -> int:
        """获取缓存文件数量"""
        try:
            return len(list(self.cache_dir.glob("*.parquet")))
        except Exception:
            return 0
    
    def get_cache_info(self) -> dict:
        """获取缓存统计信息"""
        total_size = 0
        file_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.parquet"):
                total_size += cache_file.stat().st_size
                file_count += 1
        except Exception:
            pass
        
        return {
            "file_count": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir)
        }
