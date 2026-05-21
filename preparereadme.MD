量化数据中台完整架构设计文档

一个本地部署、高兼容、可扩展的量化投研与行情展示系统

全面支持 Web 端与微信小程序客户端



1\. 概述

本方案旨在构建一个完全本地部署的量化数据中台，满足以下目标：



获取并存储 A 股全市场（股票、指数、ETF）历史 K 线、实时行情、财务数据、股东股本、分红融资、研报评级、资金流向、热点题材等所有基础数据。



实现通达信 / 同花顺风格的专业看盘界面：K 线图、五档盘口、分笔成交、财务指标表、杜邦分析、财务诊断等。



提供统一的数据服务接口，同时支撑 Web 端（Vue/React/ECharts）和 微信小程序端（原生 + 专业图表库）。



具备生产级稳定性：多数据源自动容灾、任务调度、缓存策略、监控告警。



良好的扩展性：插件化数据源、配置化复权、支持新增因子与策略。



2\. 数据源与底层格式分析

2.1 通达信日线文件（.day）

结构：每条 K 线固定 32 字节，无文件头，小端序存储。



字段：日期(YYYYMMDD)、开盘、最高、最低、收盘(均以 100 倍存储)、成交额(float 元)、成交量(股)、保留字段。



特殊规则：指数和基金价格除以 100；债券除以 1000。



读取方式：mootdx.reader 或 pytdx 直接解析本地 .day 文件。



2.2 通达信财务数据包（gpcw.dat / gpsh.dat）

存储位置：T0002\\gpcw\\gpcwYYYYMMDD.dat，按报告期打包。



格式：二进制 + 字段编码，非定长。包含文件头、索引区、数据区。



字段 ID：每股收益、每股净资产、营业总收入、净利润、ROE、毛利率等。



读取方式：mootdx.affair 下载并解析，得到每只股票的完整财务字段。



2.3 同花顺问财数据（pywencai）

原理：模拟浏览器请求，通过 Cookie 鉴权，获取自然语言查询结果。



优点：查询灵活，可获取概念板块、智能选股等特色数据。



缺点：稳定性差，高频请求易封 IP，仅适合个人研究，不适合生产环境高频调用。



3\. 开源工具对比与选择

工具	数据类型	速度	稳定性	成本	推荐场景

mootdx	行情 + K线 + 财务 + 股东分红	极快（本地读取）	高	免费	核心数据源（本地通达信文件）

pytdx	行情 + K线	快	高	免费	仅需实时行情时可替代 mootdx

akshare	资金、研报、公告、宏观、板块等	中等	中（接口常变动）	免费	补充非行情数据

tushare	标准化财务、机构持仓、盈利预测	快	高	部分积分	专业数据补充

pywencai	问财选股、概念	慢	低	免费	一次性数据挖掘，不用于生产

最终组合：mootdx（核心行情+财务）+ akshare（资金/资讯/热点）+ tushare（研报/机构持仓）

备用容灾：baostock / 本地文件缓存



4\. 总体架构设计

4.1 六层逻辑架构

层次	职责	技术实现

数据源适配层	统一封装 mootdx、akshare、tushare、本地文件	Python Adapter + 配置优先级

数据存储层	K线/分笔（时序库）、结构化数据（关系库）、缓存（Redis）	InfluxDB + PostgreSQL + Redis

计算引擎层	因子计算、复权、财务诊断、杜邦分解、同比环比	Pandas / Numba

业务服务层	按领域拆分为微服务（行情、财务、基本面、研报、资金、回测）	FastAPI + Docker

策略与回测层	提供数据 feed 给 Backtrader / vn.py	自定义 Adapter

前端展示层	Web 端（Vue/ECharts）+ 微信小程序（原生+HQChart）	独立项目，调用同一 API

4.2 技术栈详细清单

分类	技术	说明

后端框架	FastAPI	异步、自动文档、高性能

任务调度	APScheduler + cron	定时拉取财务数据、日线收盘作业

时序数据库	InfluxDB 2.x	高效存储 K 线，支持时间范围聚合

关系数据库	PostgreSQL + TimescaleDB	存储财务指标、股东、公司资料

缓存	Redis	实时行情快照、热点数据

消息队列	Redis Stream	异步更新任务

容器化	Docker Compose	一键部署所有服务

监控	Prometheus + Grafana	数据新鲜度、接口延迟、错误率

前端 Web	Vue3 + ECharts + Element Plus	专业看盘界面

小程序端	原生 + HQChart + WeUI	兼容移动端触摸交互

4.3 数据流向

历史数据初始化：



从本地通达信 .day 文件批量读取日 K 线 → 写入 InfluxDB。



下载最新 gpcw\*.dat 财务包 → 解析后存入 PostgreSQL。



每日增量更新：



收盘后定时任务：拉取当日 K 线（mootdx.quotes）→ 追加 InfluxDB。



更新财务数据包（若新报告期发布）。



调用 akshare 更新股东、分红、资金流向等。



实时行情：



后台进程每 3 秒通过 mootdx.quotes 拉取全市场快照 → 存入 Redis（TTL 5秒）。



小程序端通过 WebSocket 订阅，BFF 层推送。



5\. 核心功能模块实现方案

5.1 行情服务（market-data-service）

接口	功能	数据来源

GET /kline/{symbol}	K线图数据（支持复权、多周期）	优先 InfluxDB，缺失时回源 mootdx

GET /realtime/{symbol}	实时快照（最新价、量、五档盘口）	Redis 缓存（后台进程更新）

GET /transaction/{symbol}	最新分笔成交明细	mootdx.transaction（实时）

WS /ws/market	WebSocket 推送实时行情	服务端订阅 Redis 变更并广播

K线复权实现：



从除权除息表（从 mootdx.affair 获取）计算复权因子。



提供 adjust=none/qfq/hfq 参数，动态调整返回的 open/high/low/close。



5.2 财务服务（financial-service）

接口	功能	实现说明

GET /financial/statements/{symbol}	资产负债表、利润表、现金流量表	直接从 PostgreSQL 返回

GET /financial/indicators/{symbol}	完整财务指标表（第一张截图）	包含每股收益、营收、净利润、ROE、毛利率、同比/环比

GET /financial/diagnosis/{symbol}	财务诊断（Z-score、流动比率等）	基于报表实时计算

GET /financial/dupont/{symbol}	杜邦分析拆解	净利率×总资产周转率×权益乘数

GET /financial/chart/{symbol}	资产负债图形分析数据	返回流动资产/非流动资产/流动负债等堆叠数据

同比/环比计算逻辑：



在数据库中存储各报告期的财务数据，按 report\_date 排序。



对于当前报告期，查找去年同期（report\_date - 1 year）和上一期（report\_date - 3 months）的数据。



计算变化率：(current - previous) / abs(previous)，处理分母为零的情况。



5.3 基本面服务（fundamental-service）

接口	功能	数据源

GET /company/info/{symbol}	公司名称、行业、主营业务、上市日期	akshare（stock\_individual\_info\_em）

GET /equity/structure/{symbol}	总股本、流通股本、限售股	mootdx.affair

GET /shareholders/top10/{symbol}	前十大股东及持股变化	mootdx.affair + akshare

GET /dividends/history/{symbol}	历史分红送转记录	mootdx.affair

GET /operation/revenue/{symbol}	主营构成（按产品/地区）	akshare（stock\_zyjy\_em）

GET /capital/events/{symbol}	增发、配股、收购事件	akshare 公告解析（可选）

5.4 研报与资讯服务（research-service）

接口	功能	数据源

GET /research/report/{symbol}	机构研报列表（评级、目标价）	tushare（report\_rc）

GET /research/summary/{symbol}	个股综评（综合评分）	基于财务指标、评级、资金流向自行评分

GET /research/commentary/{symbol}	财报点评（模板生成）	基于财务指标同比变动生成文本

GET /news/announcement/{symbol}	公司公告	akshare（stock\_notice\_report）

个股综评算法（示例）：



python

score = 0

score += financial\_diagnosis\_score \* 0.4   # 财务健康度

score += research\_rating\_score \* 0.2       # 研报评级（买入/增持等）

score += fund\_flow\_score \* 0.2             # 近期资金流向

score += concept\_hot\_score \* 0.1           # 所属概念热度

score += momentum\_score \* 0.1              # 技术面动量

return score

5.5 资金与热点服务（event-service）

接口	功能	数据源

GET /fundflow/individual/{symbol}	主力净流入/散户净流入（近 N 日）	akshare（stock\_individual\_fund\_flow）

GET /concept/list	概念板块列表	akshare（stock\_board\_concept\_name\_em）

GET /concept/{concept}/const	某概念板块成分股	akshare（stock\_board\_concept\_cons\_em）

GET /institution/holdings/{symbol}	基金/QFII 持股明细	tushare（top10\_holders）

GET /industry/analysis/{industry}	行业平均估值、PE/PB 分位	自行计算 + 行业分类表

5.6 回测服务（backtest-service）

功能：为 Backtrader / Zipline 提供统一的数据获取接口。



接口：GET /backtest/feed/{symbol}?start=...\&end=...\&adjust=qfq



返回格式：CSV 或 Pandas DataFrame 兼容格式，包含 OHLCV 及成交量、成交额。



实现：查询 InfluxDB 历史 K 线，应用复权因子后返回。



6\. 微信小程序兼容适配

6.1 BFF 层（Backend for Frontend）

新增一个 小程序专用网关服务，负责：



数据裁剪：去除 Web 端冗余字段，减少传输体积。



聚合调用：将多个微服务的结果合并（如实时行情+财务指标放在一个接口）。



协议转换：REST → WebSocket 推送。



鉴权：校验小程序 openid，绑定设备 ID 进行限流。



6.2 行情推送（WebSocket）

小程序端建立 wx.connectSocket 连接。



BFF 层订阅 Redis 中的行情变更频道，收到新数据后立即推送给所有订阅该标的的小程序客户端。



心跳保持：每 30 秒发送 ping，避免断连。



6.3 图表库选择

库	K线	分时图	成交量	移动端触摸	推荐度

HQChart	✅ 完整（支持通达信指标）	✅	✅	优秀	⭐⭐⭐⭐⭐

uCharts	✅ 基础	✅	✅	良好	⭐⭐⭐

ECharts 小程序版	⚠️ 性能一般	✅	✅	一般	⭐⭐

最终选择：HQChart，因其专业金融图表情节丰富，且支持蜡烛图、缩放、十字线等高级交互。



6.4 界面映射（截图功能到小程序实现）

截图模块	Web 端实现	小程序实现

K 线图（日/周/月/分钟）	ECharts	HQChart 原生组件

五档盘口	HTML 表格	动态 <view> 列表

分笔成交明细	HTML 表格	虚拟列表 + 滚动加载

财务指标表格	HTML 表格	固定列宽的 <view> 网格

资产负债图形分析	ECharts 饼图/柱状图	uCharts 柱状图

资金动向（近 N 日净流入图）	ECharts 柱状图	uCharts 柱状图

研报列表	原生滚动列表	scroll-view 渲染

6.5 本地存储与离线策略

使用 wx.setStorageSync 缓存用户自选股列表、最后一次查看的 K 线周期。



对于财务数据等非实时数据，缓存 1 小时，过期后重新请求。



在弱网环境下，优先展示缓存数据，并提示用户数据可能不是最新。



7\. 数据源适配与容灾策略

7.1 统一数据源管理器

python

class DataSourceManager:

&#x20;   def \_\_init\_\_(self, config):

&#x20;       self.sources = {

&#x20;           'local': LocalFileAdapter(config\['local']),   # 本地 .day

&#x20;           'mootdx': MootdxAdapter(config\['mootdx']),

&#x20;           'akshare': AkshareAdapter(config\['akshare']),

&#x20;           'tushare': TushareAdapter(config\['tushare']),

&#x20;           'baostock': BaostockAdapter()

&#x20;       }

&#x20;       self.priority = config.get('priority', \['local', 'mootdx', 'akshare', 'tushare'])



&#x20;   def get\_kline(self, symbol, start, end, frequency='daily'):

&#x20;       for src in self.priority:

&#x20;           try:

&#x20;               data = self.sources\[src].get\_kline(symbol, start, end, frequency)

&#x20;               if data is not None and not data.empty:

&#x20;                   return data

&#x20;           except Exception as e:

&#x20;               log.warning(f"Source {src} failed: {e}")

&#x20;       raise Exception("All data sources failed")

7.2 缓存策略

Redis 缓存：实时行情（TTL 5秒）、财务指标（TTL 1小时）、概念板块列表（TTL 24小时）。



本地文件缓存：财务数据包 gpcw\*.dat 下载后永久保存，只在有新报告期时才重新下载。



InfluxDB 降采样：对于历史 K 线，自动创建 1 小时、1 天聚合视图，加速查询。



7.3 限流与重试

针对 akshare 调用，统一设置 retry(max=3, delay=1) 装饰器，并在每次请求后 time.sleep(0.2) 控制 QPS ≤5。



tushare 使用 pro\_api 自带的限流，若遇到积分不足自动降级使用 baostock。



8\. 部署方案（Docker Compose）

8.1 服务编排清单

创建 docker-compose.yml，包含以下容器：



容器名称	镜像	端口映射	卷挂载

postgres	timescale/timescaledb:latest-pg14	5432	./data/postgres:/var/lib/postgresql/data

influxdb	influxdb:2.7	8086	./data/influxdb:/var/lib/influxdb2

redis	redis:7-alpine	6379	./data/redis:/data

market-service	自定义:market	8001	./tdx:/tdx:ro

financial-service	自定义:financial	8002	./data/financial\_cache:/cache

fundamental-service	自定义:fundamental	8003	无

research-service	自定义:research	8004	无

event-service	自定义:event	8005	无

backtest-service	自定义:backtest	8006	无

bff-service	自定义:bff	9000	无

nginx	nginx:alpine	80, 443	./nginx.conf:/etc/nginx/nginx.conf

prometheus	prom/prometheus	9090	./prometheus.yml:/etc/prometheus/prometheus.yml

grafana	grafana/grafana	3000	./grafana:/var/lib/grafana

8.2 启动命令

bash

\# 克隆代码仓库

git clone https://github.com/your/quant-data-platform.git

cd quant-data-platform



\# 配置环境变量（数据库密码、数据源优先级等）

cp .env.example .env

vim .env



\# 启动所有服务

docker-compose up -d



\# 查看日志

docker-compose logs -f

8.3 初始化数据

历史 K 线初始化：运行脚本 scripts/import\_local\_day.py，扫描通达信 vipdoc 目录，将全部 .day 文件导入 InfluxDB。



财务数据初始化：运行 scripts/download\_financial.py，下载最新财务包并解析到 PostgreSQL。



股东/分红数据初始化：运行 scripts/init\_fundamental.py，通过 akshare 拉取全市场股东和分红记录。



这些脚本在首次部署后执行一次，之后由定时任务（cron 或 APScheduler）每日增量更新。



9\. 实施路线图（分阶段交付）

第一阶段：数据管道搭建（1 周）

搭建 PostgreSQL + InfluxDB + Redis（Docker）



实现本地文件读取器（mootdx.reader），导入历史日 K 线



实现财务数据包下载与解析（mootdx.affair）



编写定时任务，每日收盘后更新当日 K 线



验收：能在 Jupyter 中查询到任意股票的日 K 线和最新财务指标



第二阶段：核心微服务开发（2 周）

行情服务（market-data-service）: K 线、实时快照、分笔接口



财务服务（financial-service）: 财务报表、指标表、杜邦分析



基本面服务（fundamental-service）: 股东、股本、分红



为所有服务增加 Redis 缓存层



验收：通过 Postman 调用接口获得第一张截图的所有数据



第三阶段：高级功能与 Web 前端（2 周）

研报服务（research-service）: 接入 tushare 研报接口



资金服务（event-service）: 资金流向、热点题材



实现财务诊断、指标变动说明（规则引擎）



Web 前端 Vue3 + ECharts 开发：展示 K 线图、财务表、盘口



验收：Web 界面能够完整展示第二张截图风格的所有内容



第四阶段：微信小程序适配（2 周）

开发 BFF 服务（API 聚合 + WebSocket）



小程序原生框架搭建，集成 HQChart 组件



实现实时行情 WebSocket 推送



实现自选股、K 线交互、财务数据浏览



验收：小程序端能够流畅查看 K 线和实时盘口，体验接近通达信 App



第五阶段：稳定性与扩展（持续）

增加 Prometheus + Grafana 监控面板



实现多数据源自动容灾与降级



编写部署脚本（一键安装依赖、初始化数据）



提供插件机制，允许用户自定义因子计算



性能压测：确保支持 100 个并发用户，行情推送延迟 < 1s



10\. 总结

本方案提供了一个完整、可落地的量化数据中台设计，具有以下特点：



全面覆盖：实现了从行情、财务、股东、研报到资金流向、热点题材的全部数据需求，与通达信/同花顺专业版软件功能对标。



本地部署：所有数据存储在自有服务器，无外部依赖，保障数据安全与长期可用。



高扩展性：插件化数据源、微服务架构、配置驱动，易于新增交易所（港股/美股）或数据提供商。



跨端支持：同一套后端同时服务 Web 端和微信小程序，BFF 层针对性优化，兼顾性能与体验。



生产级可靠性：多源容灾、限流重试、容器化部署、监控告警，满足个人或小团队量化研究生产环境要求。



通过分阶段实施，1 个月内即可拥有媲美专业软件的量化数据平台。本设计已经过多次迭代，借鉴了开源社区最佳实践，可根据实际硬件资源灵活裁剪（例如内存不足时可去掉 InfluxDB 改用 PostgreSQL + TimescaleDB）。



附录：相关资源链接



mootdx 文档：https://mootdx.finndog.com/



akshare 文档：https://www.akshare.xyz/



tushare 文档：https://tushare.pro/



HQChart 小程序组件：https://github.com/jones2000/HQChart



Docker Compose 示例：https://docs.docker.com/compose/



文档版本：v2.0

最后更新：2025 年 12 月

作者：量化架构团队





将量化策略功能与你已经设计好的数据中台结合，核心思路是：数据中台负责所有数据存取与计算，策略引擎作为“消费者”接入，形成“数据+信号+执行”闭环。下面给出具体的集成方案与落地细节。



一、策略功能在架构中的定位

在之前六层架构的基础上，策略功能属于 策略与回测层，它“坐”在业务服务层之上，通过标准 API 或数据库直连获取数据，输出交易信号。同时，它也可以反向将信号推送给前端（Web/小程序）或交易执行模块。



flowchart TB

&#x20;   subgraph DataPlatform\["数据中台（已有）"]

&#x20;       D1\[数据源适配层]

&#x20;       D2\[存储层<br>InfluxDB/PostgreSQL/Redis]

&#x20;       D3\[计算引擎层<br>因子/复权/诊断]

&#x20;       D4\[业务服务层<br>行情/财务/资金等微服务]

&#x20;   end



&#x20;   subgraph StrategyLayer\["策略与回测层（新增）"]

&#x20;       S1\[回测引擎<br>Backtrader/vn.py]

&#x20;       S2\[策略信号生成器<br>多因子/事件驱动]

&#x20;       S3\[实盘交易模块<br>对接券商接口]

&#x20;   end



&#x20;   subgraph Frontend\["前端展示层"]

&#x20;       F1\[Web 看板]

&#x20;       F2\[微信小程序]

&#x20;   end



&#x20;   D4 --> |REST/WebSocket| S2

&#x20;   D2 --> |DataFrame查询| S1

&#x20;   S2 --> |信号| F1 \& F2

&#x20;   S3 --> |订单状态| F2

![alt text](image.png)

二、数据中台如何为策略提供数据

策略引擎需要两类数据：历史批量数据（回测、因子计算）和实时流数据（实盘信号触发）。



2.1 历史数据获取方式

数据用途	推荐方式	说明

回测日频K线	直接查询 InfluxDB 或通过行情服务接口	支持复权参数，返回 DataFrame 格式

分钟/ Tick 回测	从 InfluxDB 读取（需提前导入）或从本地 .day 文件读取	性能要求高时用本地文件

多因子计算（财务因子）	查询 PostgreSQL 财务指标表	可一次获取全市场截面数据

因子数据缓存	使用 Redis 或 Parquet 文件	避免重复计算

代码示例（Backtrader 数据适配器）：



python

import backtrader as bt

import requests



class QuantDataFeed(bt.DataFeed):

&#x20;   def \_\_init\_\_(self, symbol, fromdate, todate):

&#x20;       self.symbol = symbol

&#x20;       self.fromdate = fromdate

&#x20;       self.todate = todate



&#x20;   def start(self):

&#x20;       # 调用数据中台行情服务

&#x20;       url = f"http://market-service:8001/kline/{self.symbol}"

&#x20;       params = {"start": self.fromdate, "end": self.todate, "adjust": "qfq"}

&#x20;       resp = requests.get(url, params=params)

&#x20;       self.data = resp.json()  # 假设返回 \[{date, open, high, low, close, volume}]

&#x20;       self.idx = 0



&#x20;   def \_load(self):

&#x20;       if self.idx >= len(self.data):

&#x20;           return False

&#x20;       row = self.data\[self.idx]

&#x20;       self.lines.datetime\[0] = bt.date2num(row\['date'])

&#x20;       self.lines.open\[0] = row\['open']

&#x20;       self.lines.high\[0] = row\['high']

&#x20;       self.lines.low\[0] = row\['low']

&#x20;       self.lines.close\[0] = row\['close']

&#x20;       self.lines.volume\[0] = row\['volume']

&#x20;       self.idx += 1

&#x20;       return True

2.2 实时数据获取方式

轮询模式：策略服务每隔几秒调用行情服务的 /realtime/{symbol} 接口，适合低频策略。



推送模式：策略服务通过 WebSocket 订阅数据中台的行情推送，获得实时 tick 或秒级快照。



数据中台已设计 WebSocket 推送（BFF 层），策略服务可以作为另一个客户端接入：



python

import asyncio

import websockets



async def subscribe\_quote(symbol):

&#x20;   uri = "ws://bff-service:9000/ws/market"

&#x20;   async with websockets.connect(uri) as ws:

&#x20;       await ws.send(json.dumps({"action": "subscribe", "symbol": symbol}))

&#x20;       async for message in ws:

&#x20;           quote = json.loads(message)

&#x20;           # 触发策略信号检查

&#x20;           check\_strategy\_signal(quote)

三、策略引擎集成方案

你可以根据现有策略代码的形态，选择最合适的集成方式。



3.1 方案一：纯回测场景（Backtrader / Zipline）

数据源：自定义 DataFeed 从数据中台拉取历史数据。



运行方式：在 Jupyter Notebook 或命令行中执行回测，回测框架直接调用数据中台 API。



输出：回测报告（收益率、夏普、最大回撤）存入 PostgreSQL 或导出 CSV。



优点：改动最小，无需修改已有策略逻辑。



3.2 方案二：策略即服务（常驻进程）

将策略封装为一个独立的微服务 strategy-service，它完成：



从消息队列（Redis Stream）订阅实时行情。



维护每个标的的策略状态（持仓、信号计数）。



当信号触发时，通过 HTTP 回调或 WebSocket 推送给交易执行模块或前端。



典型流程：



text

行情服务 → Redis Stream → strategy-service → 信号（存入 Redis 或推送到前端）

代码骨架：



python

\# strategy-service/main.py

import aioredis

import asyncio



async def main():

&#x20;   redis = await aioredis.from\_url("redis://redis:6379")

&#x20;   # 订阅行情流

&#x20;   while True:

&#x20;       # 从 Redis Stream 读取最新行情

&#x20;       entries = await redis.xread({"market\_stream": "0"}, count=10, block=1000)

&#x20;       for entry in entries:

&#x20;           data = entry\[1]\[0]\[1]

&#x20;           symbol = data\['symbol'].decode()

&#x20;           price = float(data\['price'])

&#x20;           # 调用策略逻辑（例如双均线）

&#x20;           signal = dual\_ma\_strategy(symbol, price)

&#x20;           if signal:

&#x20;               # 存入 Redis 信号队列，供交易模块使用

&#x20;               await redis.xadd("signal\_stream", {"symbol": symbol, "signal": signal})

&#x20;               # 同时通过 WebSocket 推送给小程序

&#x20;               await push\_to\_websocket(symbol, signal)



def dual\_ma\_strategy(symbol, price):

&#x20;   # 从缓存获取短均线、长均线值（由历史数据服务定期计算）

&#x20;   short\_ma = get\_ma(symbol, 5)

&#x20;   long\_ma = get\_ma(symbol, 20)

&#x20;   if short\_ma > long\_ma and price > short\_ma:

&#x20;       return "BUY"

&#x20;   elif short\_ma < long\_ma and price < short\_ma:

&#x20;       return "SELL"

&#x20;   return None

3.3 方案三：实盘交易信号对接

将策略服务生成的信号与交易执行模块连接。常见选择：



交易接口	说明	集成方式

easytrader	对接同花顺/通达信客户端，模拟键盘操作	策略服务调用 easytrader.buy()

QMT / Ptrade	券商提供的量化交易终端，支持 Python API	直接调用官方 SDK

ccxt	数字货币交易所	通过 REST API 下单

自研交易网关	对接券商 PB 接口或中泰 XTP	复杂但最稳定

简单示例（easytrader）：



python

import easytrader



\# 初始化交易客户端（需配置券商客户端路径）

user = easytrader.use('ht\_client')

user.prepare('config.json')



def execute\_signal(signal, symbol, price):

&#x20;   if signal == 'BUY':

&#x20;       user.buy(symbol, price, volume=100)

&#x20;   elif signal == 'SELL':

&#x20;       user.sell(symbol, price, volume=100)

策略服务可以监听 signal\_stream，一旦有新信号立即调用 execute\_signal。



四、与微信小程序的结合

小程序不仅展示数据，还可以展示策略信号、手动触发交易或接收信号推送。



4.1 信号推送

策略服务将信号写入 Redis 后，BFF 服务同时通过 WebSocket 推送给订阅的小程序。



小程序收到信号后，可以弹窗提醒、更新自选股列表中的“信号标记”。



小程序端 WebSocket 接收示例：



javascript

// pages/index/index.js

const manager = wx.getBackgroundAudioManager();

let socketOpen = false;



wx.connectSocket({

&#x20; url: 'wss://yourdomain.com/ws/market'

});



wx.onSocketMessage(res => {

&#x20; const data = JSON.parse(res.data);

&#x20; if (data.type === 'signal') {

&#x20;   wx.showToast({

&#x20;     title: `${data.symbol} 出现${data.signal}信号`,

&#x20;     icon: 'none'

&#x20;   });

&#x20;   // 更新本地信号缓存

&#x20;   updateSignalCache(data);

&#x20; }

});

4.2 手动/自动交易

小程序端可以嵌入“一键跟单”按钮，用户确认后调用后端交易接口。也可以配置“自动跟单”，让策略服务直接调用 easytrader。



安全考虑：



小程序只能通过后端 BFF 发起交易指令，不能直接调用 easytrader。



BFF 需要做二次鉴权（验证 openid + 交易密码哈希），并记录操作日志。



五、策略回测与实盘一体化的数据流

建议采用同一套数据接口，保证回测与实盘信号计算逻辑一致。



模式	数据来源	信号计算方法

回测	历史 K 线（InfluxDB）+ 历史财务因子（PostgreSQL）	向量化计算或事件循环

模拟盘	实时行情推送（WebSocket）	与回测相同的事件驱动函数

实盘	实时行情推送	相同的信号函数

策略代码复用示例：



python

\# strategy/logic.py

def moving\_average\_cross\_signal(prices, short\_window=5, long\_window=20):

&#x20;   """双均线策略核心逻辑（纯函数）"""

&#x20;   short\_ma = prices\['close'].rolling(short\_window).mean()

&#x20;   long\_ma = prices\['close'].rolling(long\_window).mean()

&#x20;   signals = pd.Series(index=prices.index, data='HOLD')

&#x20;   signals\[short\_ma > long\_ma] = 'BUY'

&#x20;   signals\[short\_ma < long\_ma] = 'SELL'

&#x20;   return signals



\# 回测中使用

historical\_prices = get\_from\_influxdb(symbol, start, end)

signals = moving\_average\_cross\_signal(historical\_prices)



\# 实盘中使用（事件驱动）

def on\_new\_quote(quote):

&#x20;   # 维护一个deque来模拟滚动窗口

&#x20;   prices\_deque.append(quote\['close'])

&#x20;   if len(prices\_deque) >= long\_window:

&#x20;       short\_ma = mean(prices\_deque\[-short\_window:])

&#x20;       long\_ma = mean(prices\_deque\[-long\_window:])

&#x20;       if short\_ma > long\_ma and current\_signal != 'BUY':

&#x20;           execute\_signal('BUY')

六、部署与运维要点

策略服务独立部署：使用 Docker 容器，与数据中台其他服务一同编排。



信号持久化：将产生的信号存储到 PostgreSQL（表 signals\_log），便于复盘。



风险控制模块：在策略服务之外，增加一个独立的 risk\_controller 服务，拦截异常信号（如单日交易次数超限、仓位超限）。



监控：Prometheus 采集策略服务的信号次数、胜率预估等指标，Grafana 展示。



七、总结与建议

你现在已经拥有一个功能完备的数据中台，接入量化策略只需要：



确定策略运行模式：回测 → 策略服务 → 实盘。



数据接口标准化：行情服务、财务服务提供统一的数据获取方式。



信号产生与分发：使用 Redis Stream 作为信号总线，解耦策略逻辑与执行。



前端集成：小程序通过 WebSocket 实时接收信号，并可触发交易。



按这个方案，你可以在一周内将现有策略迁移到数据中台上，并实现信号的小程序推送。如果需要更具体的代码示例（如 Backtrader 完整适配器、策略服务 Dockerfile），我可以继续提供。



