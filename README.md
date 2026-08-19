# 🛒 Olist 电商经营分析平台

> **基于巴西 Olist 真实电商公开数据集构建的完整数据分析平台**
> Python + NumPy + Pandas + MySQL + Tableau

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.20+-green.svg)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-1.3+-orange.svg)](https://pandas.pydata.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://www.mysql.com/)
[![Tableau](https://img.shields.io/badge/Tableau-2024.x-purple.svg)](https://www.tableau.com/)

---

## 📋 项目简介

本项目使用 **Olist Brazilian E-Commerce Public Dataset**（巴西 Olist 电商平台真实脱敏订单数据，2016-2018 年），构建完整的**电商经营分析平台**，覆盖数据探查、清洗、存储、分析到可视化的全流程。

与模拟数据项目不同，本项目基于真实业务数据，包含 **99,441 张订单、94,990 位唯一客户、32,951 个商品、3,095 个卖家、112,650 条订单明细、103,886 条支付记录、100,000 条评论**，数据结构更贴近真实电商场景（多支付方式、多商品订单、多阶段物流状态、葡萄牙语品类等）。

---

## 📊 数据规模

| 数据表 | 记录数 | 说明 |
|--------|--------|------|
| customers | 99,441 | 订单级客户记录 |
| customers_agg | 94,990 | 唯一客户聚合（用于用户分析） |
| sellers | 3,095 | 卖家信息 |
| products | 32,951 | 商品信息（含品类英文翻译） |
| orders | 99,441 | 订单主表（含支付/物流衍生字段） |
| order_items | 112,650 | 订单明细（商品+卖家+价格+运费） |
| order_payments | 103,886 | 支付记录（支持多期/多方式） |
| order_reviews | 100,000 | 订单评论与评分 |
| geolocation | 1,000,163 | 邮编级地理坐标（清洗后聚合 19,015 条） |
| category_translation | 71 | 葡萄牙语→英语品类翻译 |

### 📐 指标口径说明

- **有效订单**：`delivered / shipped / invoiced / processing / created / approved`
  （`canceled` 与 `unavailable` 不计入营收、复购、RFM 等经营指标）
- **营收/支付金额**：基于 `order_payments.payment_value` 聚合，商品口径另提供 `price + freight_value`
- **客户维度**：`customer_unique_id` 为唯一客户标识；`customer_id` 为订单级客户标识
- **评论维度**：Olist 评论挂靠在订单上，评分按订单维度统计；品类评分通过订单明细关联

---

## 🗂️ 项目结构

```
ecommerce-analysis/
├── data/
│   ├── raw/                         # Olist 原始 CSV（真实公开数据集）
│   ├── processed/                   # 清洗后 CSV + EDA/高级分析结果
│   └── data_dictionary.csv          # 数据字典（原始表 + 派生表）
│
├── python/                          # Python 分析脚本
│   ├── common.py                    # 公共配置与业务口径
│   ├── 01_data_cleaning.py          # 数据清洗 + 特征工程
│   ├── 02_exploratory_analysis.py   # 探索性数据分析 EDA
│   ├── 03_advanced_analysis.py      # RFM / 同期群 / 关联 / 预测
│   ├── 04_visualizations.py         # 12 张可视化图表
│   └── convert_to_docx.py           # 报告 Markdown → Word
│
├── sql/                             # MySQL 脚本
│   ├── 01_create_database.sql       # 建库建表 + 视图 + 存储过程 + 触发器
│   ├── 02_data_import.sql           # LOAD DATA 导入清洗后 CSV
│   └── 03_crud_queries.sql          # CRUD + 40+ 条业务分析 SQL
│
├── charts/                          # Matplotlib 图表输出（12 张 PNG + CSV）
├── docs/                            # 项目文档
├── tableau/                         # Tableau 看板制作指南
├── run_all.py                       # 一键运行脚本
├── requirements.txt
└── README.md
```

---

## 🚀 快速开始

### 环境要求

```bash
pip install -r requirements.txt
```

需要 MySQL 8.0+ 与 Tableau Desktop / Public（可选）。

### 运行步骤

```bash
# 方式一：一键运行（清洗 → EDA → 高级分析 → 可视化）
python run_all.py

# 方式二：分步运行
python python/01_data_cleaning.py     # 数据清洗
python python/02_exploratory_analysis.py  # EDA
python python/03_advanced_analysis.py     # RFM/同期群/关联/预测
python python/04_visualizations.py        # 12 张图表

# Step 5: MySQL 数据导入
# 1. 执行 sql/01_create_database.sql 建库建表
# 2. 修改 sql/02_data_import.sql 中的 CSV 路径后执行
# 3. 执行 sql/03_crud_queries.sql 进行 SQL 分析

# Step 6: Tableau 看板制作（参考 tableau/dashboard_guide.md）
```

> 注：`data/processed/` 为运行产物，已在 `.gitignore` 中忽略；`data/raw/` 为 Olist 公开数据集，可在 Kaggle 搜索 "Brazilian E-Commerce Public Dataset by Olist" 获取。

---

## 📈 核心功能

### 1. 数据清洗 (`01_data_cleaning.py`)
- ✅ 9 张原始 CSV 加载与质量评估（缺失/重复/外键）
- ✅ 类型转换、缺失值处理、状态标准化
- ✅ 特征工程：订单支付总额、配送时效、商品表现、客户聚合
- ✅ 清洗报告输出到 `data/processed/`

### 2. 探索性分析 (`02_exploratory_analysis.py`)
- 📊 核心 KPI：订单数、营收、客单价、评分、准时率
- 📊 订单状态 / 支付方式 / 评分 / 品类 / 州分布
- 📊 月度趋势、Top-N 排行、相关性与配送分析
- 📊 15+ 个结果 CSV 输出到 `data/processed/eda_results/`

### 3. 高级分析 (`03_advanced_analysis.py`)
- 👥 **RFM 客户价值分群**：R/F/M 四分位打分 + 8 类客户分层
- 📅 **同期群留存分析**：按首购月份追踪留存矩阵
- 🧺 **品类关联规则**：支持度 / 置信度 / 提升度
- 📉 **销售预测**：3 月移动平均 + 指数平滑
- ⚠️ **流失风险分层**：活跃 / 沉默 / 流失风险 / 已流失
- 💰 **CLV 估算**：平均客单价 × 购买频次

### 4. 数据可视化 (`04_visualizations.py`)
12 张专业图表，涵盖月度营收、品类销售、支付方式、评分分布、商品/卖家排行、客户分群、订单状态、配送时效、价格-评分关系、周内下单规律，并导出 Tableau 地图/报表用 CSV。

### 5. MySQL 数据库 (`sql/`)
- 9 张核心业务表 + 外键约束 + 优化索引
- 3 个分析视图：订单事实 / 商品表现 / 客户价值
- 1 个 RFM 存储过程
- 1 个评分校验触发器
- 40+ 条业务分析 SQL（CRUD、窗口函数、留存、复购、配送等）

### 6. Tableau 看板 (`tableau/`)
- 看板1：销售运营总览（KPI + 趋势 + 州地图 + 支付分布）
- 看板2：客户分析（RFM + 生命周期 + 地域画像）
- 看板3：商品分析（品类销售 + 商品排行 + 卖家分析）
- 看板4：评论与履约分析（评分分布 + 品类评分 + 配送时效）

---

## 🔍 关键数据洞察

1. **营收规模**：有效订单 98,207 单，支付总额约 **R$ 1,574 万**，平均客单价约 **R$ 160.26**
2. **支付偏好**：信用卡占绝对主导（73.9%），银行单据 boleto 占 19.0%，分期支付特征明显
3. **评分表现**：平均评分 **4.07**，4-5 星好评率 **76.7%**，差评(1-2星)约 15.0%
4. **品类结构**：health_beauty、watches_gifts、bed_bath_table 为销售额 Top3，合计约 25.3% GMV
5. **地域集中**：SP 州订单 41,127 单、营收约 R$ 588 万（占 37.4%），圣保罗市为最大单一城市
6. **配送时效**：平均送达 **12.56 天**，准时送达率 **91.9%**；SP 平均 8.8 天，北部州可达 20+ 天
7. **客户价值**：重要价值客户约 1.24 万人，人均消费 R$ 272.7；超过 60% 客户处于流失风险及以上状态
8. **复购特征**：Olist 平台以低频订单为主，多品类购物篮较少（仅 785 单含 ≥2 个品类），说明平台以单品类购买为主，交叉销售仍有提升空间

---

## 🛠️ 技术栈详解

| 技术 | 核心应用 |
|------|---------|
| **NumPy** | 数值统计、百分位数、线性拟合、模拟抽样 |
| **Pandas** | 数据清洗、groupby 聚合、pivot_table、merge 关联、时间序列 |
| **Matplotlib** | 折线图、柱状图、饼图、散点图、直方图 |
| **MySQL** | DDL 建库表索引、DML CRUD、视图、存储过程、触发器、窗口函数 |
| **Tableau** | 数据连接、计算字段、地图、交互看板 |

---

## 📝 简历项目描述 (Resume-Ready)

> **Olist 电商经营分析平台** | Python, Pandas, NumPy, MySQL, Tableau | 2026.08
>
> 基于巴西 Olist 真实电商公开数据集（约 10 万订单、9.5 万客户、3.3 万商品）独立构建完整的电商经营分析平台。完成 9 张业务表的 MySQL 建模与导入，编写 40+ 条分析 SQL（含窗口函数、RFM 存储过程、视图、触发器）。使用 Pandas/NumPy 构建数据清洗流水线（缺失值、重复值、外键校验、特征工程），并进行 RFM 客户分群、同期群留存、品类关联规则、销售预测、配送履约分析。使用 Matplotlib 产出 12 张专业图表，设计 4 个 Tableau 业务看板。基于分析结果提炼 8 条可落地商业洞察，包括品类策略、地域运营、支付优化与物流改进建议。

---

## 📄 License

MIT License - 数据版权归 Olist / Kaggle 原始发布者所有，仅供学习展示使用。

---

## 👤 作者

Cavsin
