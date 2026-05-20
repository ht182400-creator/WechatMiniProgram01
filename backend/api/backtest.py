# -*- coding: utf-8 -*-
"""
策略回测API
@author: StockQuant Team
@date: 2026-05-19
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from adapters import get_data_source_manager
from engine import BacktestEngine, BacktestConfig
from strategies import get_strategy, list_strategies, STRATEGY_REGISTRY
from models import get_db_session, BacktestRecord

router = APIRouter()


class BacktestRequest(BaseModel):
    """回测请求参数"""
    code: str
    strategy_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_cash: float = 100000
    params: Optional[List[Dict[str, float]]] = None


@router.get("/strategies", summary="获取策略列表")
async def get_strategies() -> Dict[str, Any]:
    """获取所有可用策略"""
    strategies = list_strategies()
    return {
        "total": len(strategies),
        "strategies": strategies
    }


@router.post("/run", summary="运行回测")
async def run_backtest(request: BacktestRequest) -> Dict[str, Any]:
    """运行回测"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        code = request.code
        strategy_name = request.strategy_name
        initial_cash = request.initial_cash
        
        # 默认回测时间
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = request.start_date or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        logger.info(f"开始回测: 股票={code}, 策略={strategy_name}, 时间={start_date}至{end_date}")
        
        # 获取数据
        try:
            data_manager = get_data_source_manager()
            df = data_manager.get_daily_data(code, start_date, end_date)
            logger.info(f"获取数据成功: {len(df)} 条")
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"获取 {code} 数据失败")
        
        # 解析策略参数
        strategy_params = {}
        if request.params:
            try:
                for item in request.params:
                    strategy_params.update(item)
            except Exception:
                raise HTTPException(status_code=400, detail="策略参数格式错误")
        
        # 创建策略
        try:
            strategy = get_strategy(strategy_name, strategy_params)
            logger.info(f"创建策略成功: {strategy.name}")
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            raise HTTPException(status_code=400, detail=f"创建策略失败: {str(e)}")
        
        # 创建回测配置
        config = BacktestConfig(
            initial_cash=initial_cash,
            commission=0.0003,
            slippage=0.0001
        )
        
        # 创建并运行回测引擎
        try:
            engine = BacktestEngine(config)
            engine.set_strategy(strategy)
            engine.set_data(df)
            result = engine.run()
            logger.info(f"回测执行成功: 总收益率={result.total_return:.4f}")
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            raise HTTPException(status_code=500, detail=f"回测执行失败: {str(e)}")
        
        # 保存回测记录（失败不影响主流程）
        db_saved = False
        try:
            with get_db_session() as session:
                record = BacktestRecord(
                    strategy_name=strategy.name,
                    stock_code=code,
                    start_date=start_date,
                    end_date=end_date,
                    initial_cash=initial_cash,
                    final_capital=result.final_capital,
                    total_return=result.total_return,
                    annualized_return=result.annualized_return,
                    max_drawdown=result.max_drawdown,
                    sharpe_ratio=result.sharpe_ratio,
                    win_rate=result.win_rate,
                    total_trades=result.total_trades,
                    params=strategy_params
                )
                session.add(record)
                # session.commit() 由 context manager 自动调用
                db_saved = True
                logger.info("回测记录已保存")
        except Exception as e:
            logger.warning(f"保存回测记录失败(不影响结果): {e}")
        
        return {
            "success": True,
            "code": code,
            "strategy": strategy.name,
            "period": {
                "start": start_date,
                "end": end_date,
                "days": len(df)
            },
            "config": {
                "initial_cash": initial_cash,
                "commission": config.commission,
                "slippage": config.slippage
            },
            "result": {
                "final_capital": round(result.final_capital, 2),
                "total_return": round(result.total_return, 4),
                "annualized_return": round(result.annualized_return, 4),
                "max_drawdown": round(result.max_drawdown, 4),
                "sharpe_ratio": round(result.sharpe_ratio, 4),
                "win_rate": round(result.win_rate, 4),
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "avg_profit": round(result.avg_profit, 2),
                "avg_loss": round(result.avg_loss, 2),
                "profit_factor": round(result.profit_factor, 4)
            },
            "equity_curve": result.equity_curve[-100:] if len(result.equity_curve) > 100 else result.equity_curve,
            # 交易明细
            "trades": [
                {
                    "date": t.date,
                    "action": t.action,
                    "price": round(t.price, 2),
                    "quantity": t.quantity,
                    "amount": round(t.total_amount, 2),
                    "commission": round(t.commission, 2),
                    "slippage": round(t.slippage, 2)
                }
                for t in result.trades
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"回测失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")


@router.get("/history", summary="获取回测历史")
async def get_backtest_history(
    limit: int = Query(20, description="返回条数")
) -> Dict[str, Any]:
    """获取历史回测记录"""
    try:
        with get_db_session() as session:
            records = session.query(BacktestRecord).order_by(
                BacktestRecord.created_at.desc()
            ).limit(limit).all()
            
            return {
                "total": len(records),
                "records": [
                    {
                        "id": r.id,
                        "strategy_name": r.strategy_name,
                        "stock_code": r.stock_code,
                        "start_date": r.start_date,
                        "end_date": r.end_date,
                        "total_return": r.total_return,
                        "annualized_return": r.annualized_return,
                        "max_drawdown": r.max_drawdown,
                        "sharpe_ratio": r.sharpe_ratio,
                        "win_rate": r.win_rate,
                        "total_trades": r.total_trades,
                        "params": r.params,
                        "created_at": str(r.created_at)
                    }
                    for r in records
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.get("/compare", summary="策略对比")
async def compare_strategies(
    code: str = Query(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="回测开始日期"),
    end_date: Optional[str] = Query(None, description="回测结束日期"),
    initial_cash: float = Query(100000, description="初始资金")
) -> Dict[str, Any]:
    """对比多个策略"""
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # 获取数据
        data_manager = get_data_source_manager()
        df = data_manager.get_daily_data(code, start_date, end_date)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"获取 {code} 数据失败")
        
        # 回测所有策略
        results = []
        config = BacktestConfig(initial_cash=initial_cash)
        
        for name in ['ma_cross', 'rsi', 'macd', 'bollinger']:
            try:
                strategy = get_strategy(name)
                engine = BacktestEngine(config)
                engine.set_strategy(strategy)
                engine.set_data(df)
                result = engine.run()
                
                results.append({
                    "strategy": strategy.name,
                    "total_return": round(result.total_return, 4),
                    "annualized_return": round(result.annualized_return, 4),
                    "max_drawdown": round(result.max_drawdown, 4),
                    "sharpe_ratio": round(result.sharpe_ratio, 4),
                    "win_rate": round(result.win_rate, 4),
                    "total_trades": result.total_trades
                })
            except Exception:
                pass
        
        return {
            "code": code,
            "period": {"start": start_date, "end": end_date},
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略对比失败: {str(e)}")
