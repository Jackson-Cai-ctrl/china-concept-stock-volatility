# China Concept Stocks: Historical Risk Analysis

<p align="center"><strong>中概股与 A 股代表性概念板块的历史收益、波动与回撤分析</strong></p>
<p align="center">行情采集 · 描述性统计 · 图表与报告导出</p>

> 这是一个基于历史行情的分析脚本项目。它不训练股价预测模型，也不进行因果识别或事件研究；统计结果用于观察样本期内的表现差异，不构成投资建议。

## 项目概览

项目由两个脚本组成：先从公开数据接口采集代表性股票、宏观指标和概念板块数据，再读取本地 CSV，对股票和人工定义的类别计算历史表现指标，并输出图表与 Markdown 报告。

~~~mermaid
flowchart LR
    A[yfinance 股票行情] --> C[本地 CSV 数据]
    B[AKShare 宏观及概念接口] --> C
    C --> D[字段标准化与缺失检查]
    D --> E[收益率 / 波动率 / 回撤]
    E --> F[年度与类别对比]
    F --> G[图表和 Markdown 报告]
~~~

## 分析内容

| 模块 | 处理内容 |
|---|---|
| 行情采集 | 采集脚本配置的代表性 A 股、港股和美股日线数据，时间范围设为 2023-01-01 至 2026-03-31 |
| 宏观及板块数据 | 通过 AKShare 获取 CPI、GDP、PMI、货币供应量、LPR 等序列，并抓取概念板块列表及有限的成分股样本 |
| 数据质量 | 统计不同股票 CSV 的记录数和收盘价缺失情况 |
| 收益表现 | 按年份计算样本期价格变化率 |
| 风险指标 | 计算日收益率、20 日滚动年化波动率、年度年化波动率及滚动/年度最大回撤 |
| 类别比较 | 按脚本内维护的股票类别聚合收益、波动和回撤，并计算年度类别收益相关性 |
| 结果输出 | 生成 CSV、PNG 图表和 Markdown 分析报告 |

年化波动率按日收益率标准差乘以 √252 计算。股票类别由代码内静态映射表指定，不是从成分股数据自动推导。

## 运行方法

需要可访问互联网的 Python 环境。当前仓库没有锁定依赖文件，可安装以下包：

~~~bash
python -m venv .venv
python -m pip install akshare yfinance pandas numpy matplotlib seaborn tabulate
~~~

采集和分析脚本会把 CSV、图片和报告写入**当前工作目录**。建议在独立目录运行，避免生成物混入源码目录：

~~~bash
mkdir run-data
cd run-data
python ../akshare_stock_data_2023_2026.py
python ../china_concept_stocks_analysis.py
~~~

Windows PowerShell 可在仓库根目录执行：

~~~powershell
python -m venv .venv
python -m pip install akshare yfinance pandas numpy matplotlib seaborn tabulate
New-Item -ItemType Directory -Force run-data
Set-Location run-data
python ../akshare_stock_data_2023_2026.py
python ../china_concept_stocks_analysis.py
~~~

先运行采集脚本，分析脚本再读取当前目录中符合 `stock_*_2023_2026.csv` 命名规则的行情文件。接口响应、代码映射或上游 API 变化可能导致部分数据缺失；运行后应检查成功条数、日期范围和缺失率。

## 主要产物

| 产物 | 生成内容 |
|---|---|
| `stock_*_2023_2026.csv` | 每只代表性股票的日线数据 |
| `macro_*_2023_2026.csv` | 获取成功的宏观指标数据 |
| `concept_boards_2023_2026.csv` | 概念板块列表 |
| `concept_*_constituents.csv` | 脚本额外抓取的概念成分股样本 |
| `stock_metrics_summary_2023_2026.csv` | 采集阶段的股票指标摘要 |
| `yearly_volatility_analysis_2023_2026.csv` | 年度收益、年化波动和最大回撤明细 |
| `china_concept_stocks_analysis_report.md` | 缺失情况、年度表现、类别统计和相关性摘要 |
| `industry_year_return_heatmap.png` 等 | 年度类别收益热力图、波动比较、趋势及收益分布图 |

## 代码结构

~~~text
.
├── akshare_stock_data_2023_2026.py
├── china_concept_stocks_analysis.py
└── README.md
~~~

- `akshare_stock_data_2023_2026.py`：调用 yfinance 和 AKShare，下载数据并生成采集摘要图表。
- `china_concept_stocks_analysis.py`：从当前目录发现股票 CSV，计算年度指标、类别差异、相关性并写出分析报告。

## 结果解读与边界

- 样本是脚本列出的代表性股票，不是全部中概股、A 股或完整概念板块。
- 数据区间写在采集脚本中；要分析新的时间窗口，需要同步检查接口参数、过滤逻辑和报告标题。
- 宏观 CSV 会被采集并读取，但当前主分析没有把这些序列与股票收益构造成正式事件窗口、回归或因果模型。`analyze_volatility_causes` 主要汇总年度行业表现。
- 类别相关性来自有限的年度聚合观测，样本点少，只能用于探索性对比，不能据此推导稳定的分散化效果。
- 年化波动、收益和回撤是历史统计量，不预测未来表现。代码生成的配置提示也不代表个性化投资建议。
