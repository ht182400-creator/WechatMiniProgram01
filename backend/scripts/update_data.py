# -*- coding: utf-8 -*-
"""
数据更新脚本 - 增量更新股票数据
@author: StockQuant Team
@date: 2026-05-19
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import init_directories
from adapters import get_data_source_manager
from models import db_manager, Stock, DailyKLine, get_db_session

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def update_stock_list():
    """更新股票列表"""
    logger.info("=" * 50)
    logger.info("开始更新股票列表...")
    
    data_manager = get_data_source_manager()
    df = data_manager.get_stock_list()
    
    if df.empty:
        logger.error("获取股票列表失败")
        return False
    
    try:
        with get_db_session() as session:
            for _, row in df.iterrows():
                stock = session.query(Stock).filter(
                    Stock.code == row['code']
                ).first()
                
                if stock:
                    stock.name = row.get('name', stock.name)
                    stock.updated_at = datetime.now()
                else:
                    stock = Stock(
                        code=row['code'],
                        name=row.get('name', ''),
                        market=row.get('market', ''),
                        industry=row.get('industry', '')
                    )
                    session.add(stock)
        
        logger.info(f"股票列表更新完成: {len(df)} 只股票")
        return True
    except Exception as e:
        logger.error(f"更新股票列表失败: {e}")
        return False


def update_daily_data(codes: list = None, days: int = 5):
    """
    更新日线数据
    
    Args:
        codes: 股票代码列表，None表示更新所有
        days: 更新最近N天数据
    """
    logger.info("=" * 50)
    logger.info(f"开始更新日线数据 (最近{days}天)...")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    data_manager = get_data_source_manager()
    
    try:
        with get_db_session() as session:
            # 获取需要更新的股票
            if codes:
                stocks = session.query(Stock).filter(Stock.code.in_(codes)).all()
            else:
                stocks = session.query(Stock).filter(Stock.is_enabled == True).all()
            
            success_count = 0
            fail_count = 0
            
            for stock in stocks:
                try:
                    # 获取数据
                    df = data_manager.get_daily_data(
                        stock.code, 
                        start_date, 
                        end_date
                    )
                    
                    if df.empty:
                        continue
                    
                    # 保存数据
                    for _, row in df.iterrows():
                        # 检查是否已存在
                        existing = session.query(DailyKLine).filter(
                            DailyKLine.code == stock.code,
                            DailyKLine.date == str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date'])
                        ).first()
                        
                        if not existing:
                            kline = DailyKLine(
                                code=stock.code,
                                date=str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date']),
                                open=float(row.get('open', 0)),
                                high=float(row.get('high', 0)),
                                low=float(row.get('low', 0)),
                                close=float(row.get('close', 0)),
                                volume=float(row.get('volume', 0)),
                                amount=float(row.get('amount', 0)),
                                change=float(row.get('change', 0)),
                                pct_change=float(row.get('pct_change', 0)),
                                turnover=float(row.get('turnover', 0))
                            )
                            session.add(kline)
                    
                    success_count += 1
                    logger.info(f"更新 {stock.code} 成功: {len(df)} 条")
                    
                except Exception as e:
                    fail_count += 1
                    logger.warning(f"更新 {stock.code} 失败: {e}")
        
        logger.info("=" * 50)
        logger.info(f"日线数据更新完成: 成功 {success_count}, 失败 {fail_count}")
        return True
        
    except Exception as e:
        logger.error(f"更新日线数据失败: {e}")
        return False


def update_all(days: int = 5):
    """更新所有数据"""
    logger.info("=" * 60)
    logger.info("开始全量数据更新...")
    logger.info("=" * 60)
    
    # 初始化数据库
    db_manager.create_tables()
    
    # 更新股票列表
    update_stock_list()
    
    # 更新日线数据
    update_daily_data(days=days)
    
    logger.info("=" * 60)
    logger.info("全量数据更新完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="股票数据更新脚本")
    parser.add_argument('--days', type=int, default=5, help='更新最近N天数据')
    parser.add_argument('--codes', type=str, help='指定股票代码，逗号分隔')
    
    args = parser.parse_args()
    
    codes = args.codes.split(',') if args.codes else None
    
    if codes:
        update_daily_data(codes=codes, days=args.days)
    else:
        update_all(days=args.days)
