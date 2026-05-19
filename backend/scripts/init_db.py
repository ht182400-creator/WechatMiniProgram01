# -*- coding: utf-8 -*-
"""
数据库初始化脚本
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import db_manager, Stock, SystemConfig
from config import init_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    logger.info("=" * 50)
    logger.info("开始初始化数据库...")
    
    # 创建表
    db_manager.create_tables()
    logger.info("数据库表创建完成")
    
    # 初始化系统配置
    try:
        with db_manager.get_session() as session:
            configs = [
                {"key": "data_update_time", "value": "16:00", "desc": "数据更新时间"},
                {"key": "default_lookback_days", "value": "60", "desc": "默认回看天数"},
                {"key": "default_predict_days", "value": "5", "desc": "默认预测天数"},
            ]
            
            for cfg in configs:
                existing = session.query(SystemConfig).filter(
                    SystemConfig.config_key == cfg["key"]
                ).first()
                
                if not existing:
                    config = SystemConfig(
                        config_key=cfg["key"],
                        config_value=cfg["value"],
                        description=cfg["desc"]
                    )
                    session.add(config)
            
            logger.info("系统配置初始化完成")
    except Exception as e:
        logger.warning(f"系统配置初始化跳过: {e}")
    
    logger.info("=" * 50)
    logger.info("数据库初始化完成!")
    logger.info("=" * 50)


if __name__ == "__main__":
    init_database()
