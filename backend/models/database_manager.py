# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
@author: StockQuant Team
@date: 2026-05-19
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

try:
    from config import settings
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings

from .database import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
            poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = True
        logger.info(f"数据库初始化完成: {settings.DATABASE_URL}")
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("数据库表创建完成")
    
    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("数据库表已删除")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的便捷函数"""
    with db_manager.get_session() as session:
        yield session
