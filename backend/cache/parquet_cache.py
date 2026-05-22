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

from config import settings

logger = logging.getLogger(__name__)


class ParquetCache:
    """Parquet 格式缓存管理器（不可用时自动降级为 pickle）"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expire_minutes = settings.CACHE_EXPIRE_MINUTES
        self.max_size = settings.CACHE_MAX_SIZE
        # 检测 parquet 引擎可用性
        self._parquet_available = self._check_parquet_engine()
    
    def _check_parquet_engine(self) -> bool:
        """检测是否有可用的 parquet 引擎"""
        try:
            # 尝试用 pyarrow 写一个简单的 DataFrame
            test_df = pd.DataFrame({'a': [1]})
            test_path = self.cache_dir / '.parquet_test.parquet'
            test_df.to_parquet(test_path)
            pd.read_parquet(test_path)
            test_path.unlink(missing_ok=True)
            logger.info("Parquet 引擎可用 (pyarrow)")
            return True
        except Exception as e:
            logger.warning(f"Parquet 引擎不可用 ({e})，将使用 pickle 格式缓存")
            return False
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径（根据引擎自动选择扩展名）"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        ext = '.parquet' if self._parquet_available else '.pkl'
        return self.cache_dir / f"{key_hash}{ext}"
    
    def _get_cache_path_by_ext(self, key: str, ext: str) -> Path:
        """获取指定扩展名的缓存文件路径"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}{ext}"
    
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
        """获取缓存数据（自动尝试 parquet > pickle）"""
        for ext in ['.parquet', '.pkl']:
            try:
                cache_path = self._get_cache_path_by_ext(key, ext)
                
                if self._is_expired(cache_path):
                    if cache_path.exists():
                        cache_path.unlink()
                    continue
                
                if cache_path.exists():
                    if ext == '.parquet':
                        df = pd.read_parquet(cache_path)
                    else:
                        df = pd.read_pickle(cache_path)
                    logger.debug(f"缓存读取成功: {key} ({len(df)} 行, {ext})")
                    return df
            except Exception as e:
                logger.debug(f"读取 {ext} 缓存失败 [{key}]: {e}")
                continue
        
        return None
    
    def set(self, key: str, data: pd.DataFrame) -> bool:
        """设置缓存数据（优先 parquet，失败则降级为 pickle）"""
        try:
            if data is None or data.empty:
                return False
            
            cache_path = self._get_cache_path(key)
            
            if self._parquet_available:
                try:
                    data.to_parquet(cache_path, index=True)
                    logger.debug(f"缓存写入成功: {key} ({len(data)} 行, parquet)")
                    return True
                except Exception as parquet_err:
                    logger.debug(f"Parquet 写入失败，降级为 pickle: {parquet_err}")
            
            # 降级为 pickle
            pkl_path = self._get_cache_path_by_ext(key, '.pkl')
            data.to_pickle(pkl_path)
            logger.debug(f"缓存写入成功: {key} ({len(data)} 行, pickle)")
            return True
        except Exception as e:
            logger.error(f"写入缓存失败 [{key}]: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存（清除所有格式）"""
        deleted = False
        for ext in ['.parquet', '.pkl']:
            try:
                cache_path = self._get_cache_path_by_ext(key, ext)
                if cache_path.exists():
                    cache_path.unlink()
                    deleted = True
            except Exception as e:
                logger.error(f"删除缓存失败 [{key}{ext}]: {e}")
        return deleted
    
    def clear_all(self) -> int:
        """清空所有缓存（包含 parquet 和 pickle）"""
        count = 0
        try:
            for pattern in ("*.parquet", "*.pkl"):
                for cache_file in self.cache_dir.glob(pattern):
                    cache_file.unlink()
                    count += 1
            logger.info(f"已清空 {count} 个缓存文件")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
        return count
    
    def get_cache_size(self) -> int:
        """获取缓存文件数量"""
        try:
            return len(list(self.cache_dir.glob("*.parquet"))) + len(list(self.cache_dir.glob("*.pkl")))
        except Exception:
            return 0
    
    def get_cache_info(self) -> dict:
        """获取缓存统计信息"""
        total_size = 0
        file_count = 0
        
        try:
            for pattern in ("*.parquet", "*.pkl"):
                for cache_file in self.cache_dir.glob(pattern):
                    total_size += cache_file.stat().st_size
                    file_count += 1
        except Exception:
            pass
        
        return {
            "file_count": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir)
        }
