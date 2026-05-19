# 股票量化分析与预测系统 V3.0

> 基于 Vue 3 + FastAPI 的量化投资研究平台

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Vue](https://img.shields.io/badge/Vue-3.4-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 项目简介

股票量化分析与预测系统是一套完整的量化投资研究平台，支持：

- 🗂️ **数据采集**: A股实时/历史数据，多数据源冗余
- 📊 **技术指标**: MA、RSI、MACD、KDJ、布林带等
- 📈 **策略回测**: 多种量化策略验证
- 🤖 **趋势预测**: 机器学习涨跌预测
- 🎨 **可视化**: K线图表、权益曲线

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│                  前端层 (Vue 3)                      │
│  ┌──────────────────┐    ┌──────────────────┐       │
│  │   Web管理端       │    │   微信小程序      │       │
│  └──────────────────┘    └──────────────────┘       │
└───────────────────────────┬─────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────┐
│              后端层 (FastAPI Python)                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 数据采集 │ │ 因子计算 │ │ 回测引擎 │ │ 预测模型 │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
└───────────────────────────┬─────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   SQLite     │   │   Parquet   │   │   数据源     │
│   数据库      │   │   缓存       │   │  多源冗余    │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 🚀 快速开始

### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动服务
python main.py
# 或
uvicorn main:app --reload --port 8000
```

### 2. 前端启动

```bash
# 新开终端
cd frontend/web

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 浏览器访问 http://localhost:5173
```

## 📁 项目结构

```
WechatMiniProgram01/
├── backend/                    # Python FastAPI 后端
│   ├── main.py                # 应用入口
│   ├── config/                # 配置模块
│   ├── adapters/              # 数据源适配器
│   ├── cache/                 # 缓存模块
│   ├── factors/               # 因子模块
│   ├── strategies/            # 策略模块
│   ├── engine/                # 回测引擎
│   ├── sentiment/             # 舆情分析
│   ├── models/                # 数据模型
│   ├── api/                   # API路由
│   └── scripts/               # 工具脚本
│
├── frontend/
│   ├── web/                   # Vue 3 Web 前端
│   └── miniprogram/           # 微信小程序
│
└── docs/                      # 技术文档
    ├── 00_项目总览.md
    ├── 01_技术实现文档.md
    ├── 02_数据结构文档.md
    ├── 03_测试文档.md
    ├── 04_实施文档.md
    └── 05_环境配置文档.md
```

## 🔧 核心功能

| 功能 | 说明 | API |
|------|------|-----|
| 股票列表 | 获取所有A股股票 | `GET /api/stock/list` |
| 日线数据 | K线历史数据 | `GET /api/stock/daily` |
| 技术指标 | MA/RSI/MACD等 | `GET /api/stock/indicators` |
| K线图表 | ECharts数据 | `GET /api/stock/chart` |
| 策略回测 | 验证交易策略 | `POST /api/backtest/run` |
| 趋势预测 | ML涨跌预测 | `POST /api/predict/predict` |

## 📦 技术栈

### 后端
- **Web框架**: FastAPI 0.109+
- **数据库**: SQLite / PostgreSQL
- **数据处理**: pandas, numpy
- **机器学习**: scikit-learn, xgboost
- **数据源**: AKShare, Baostock, Tushare

### 前端
- **框架**: Vue 3 + Composition API
- **UI库**: Element Plus 2.5+
- **图表**: ECharts 5.5+
- **构建**: Vite 5
- **状态**: Pinia

## 📝 API 文档

启动服务后访问:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ⚙️ 配置

### 数据源配置

```python
# backend/.env
AKSHARE_ENABLE=true      # 默认启用
BAOSTOCK_ENABLE=true     # 备用数据源
TUSHARE_ENABLE=false     # 需要Token
TUSHARE_TOKEN=your_token  # Tushare Token
```

### 回测参数

```python
BACKTEST_COMMISSION = 0.0003   # 手续费 0.03%
BACKTEST_SLIPPAGE = 0.0001     # 滑点 0.01%
BACKTEST_INITIAL_CASH = 100000 # 初始资金 10万
```

## 🧪 支持的策略

| 策略 | 说明 | 参数 |
|------|------|------|
| ma_cross | 均线金叉死叉 | short_window, long_window |
| rsi | RSI超买超卖 | rsi_period, oversold, overbought |
| macd | MACD交叉 | fast, slow, signal |
| bollinger | 布林带 | bb_period, bb_std |

## 📊 回测指标

| 指标 | 说明 |
|------|------|
| 总收益率 | 期末/期初 - 1 |
| 年化收益率 | (1+总收益)^(252/交易日) - 1 |
| 最大回撤 | 最高点到最低点跌幅 |
| 夏普比率 | (年化收益-无风险利率)/年化波动率 |
| 胜率 | 盈利次数/总交易次数 |
| 盈亏比 | 平均盈利/平均亏损 |

## 🔒 安全说明

- ✅ Pydantic 输入验证
- ✅ SQLAlchemy 防注入
- ✅ CORS 跨域控制
- ✅ 请求频率限制（可选）

## 📚 文档

详细技术文档请查看 `/docs` 目录：

- [项目总览](docs/00_项目总览.md)
- [技术实现文档](docs/01_技术实现文档.md)
- [数据结构文档](docs/02_数据结构文档.md)
- [测试文档](docs/03_测试文档.md)
- [实施文档](docs/04_实施文档.md)
- [环境配置文档](docs/05_环境配置文档.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## ⚠️ 免责声明

**本系统仅供学习研究使用，预测结果仅供参考，不构成任何投资建议。股票投资有风险，入市需谨慎！**

---

⭐ 如果这个项目对您有帮助，请给个 Star！
