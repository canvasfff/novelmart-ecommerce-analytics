# 🛒 NovelMart 电商经营分析平台

> **数据驱动电商运营决策** | Python + NumPy + Pandas + MySQL + Tableau

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.20+-green.svg)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-1.3+-orange.svg)](https://pandas.pydata.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://www.mysql.com/)
[![Tableau](https://img.shields.io/badge/Tableau-2024.x-purple.svg)](https://www.tableau.com/)

---

## 📋 项目简介

本项目基于 **NovelMart E-Commerce Dataset**（NovelMart 电商平台中国区销售与客户行为公开数据集）构建完整的**电商经营分析平台**，覆盖数据探查、存储、清洗、分析到可视化的全流程。数据集包含 **30万+条** 业务记录，时间跨度 2024-01 ~ 2026-06（2.5年），涉及用户、商品、订单、订单明细、评论五大业务模块。

---

## 📊 数据规模

| 数据表 | 记录数 | 说明 |
|--------|--------|------|
| users | 12,000 | 用户基本信息、会员等级、消费统计 |
| products | 5,000 | 商品信息、价格、库存、销量、评分 |
| orders | 55,000 | 订单信息、支付方式、配送、状态 |
| order_items | 194,279 | 订单明细、购买数量、折扣 |
| reviews | 35,000 | 商品评论、评分、认证购买标识 |
| **总计** | **301,279** | **跨2.5年的电商运营数据** |

---

## 🗂️ 项目结构

```
ecommerce-analysis/
├── data/                           # 数据目录
│   ├── data_dictionary.csv         # 数据字典(元数据)
│   ├── users.csv                   # 用户数据 (12,000条)
│   ├── products.csv                # 商品数据 (5,000条)
│   ├── orders.csv                  # 订单数据 (55,000条)
│   ├── order_items.csv             # 订单明细 (194,279条)
│   └── reviews.csv                 # 评论数据 (35,000条)
│
├── sql/                            # MySQL脚本
│   ├── 01_create_database.sql      # 建库建表+视图+存储过程+触发器
│   ├── 02_data_import.sql          # 数据导入脚本
│   └── 03_crud_queries.sql         # CRUD操作+分析查询(30+条SQL)
│
├── python/                         # Python分析脚本
│   ├── 01_data_cleaning.py         # 数据清洗+特征工程
│   ├── 02_exploratory_analysis.py  # 探索性数据分析(EDA)
│   ├── 03_advanced_analysis.py     # 高级分析(RFM/同期群/关联规则)
│   └── 04_visualizations.py        # 数据可视化(12张图表)
│
├── charts/                         # 图表输出
│   ├── monthly_revenue.png         # 月度销售趋势
│   ├── category_sales.png          # 品类销售分布
│   ├── rating_distribution.png     # 评分分布
│   └── ... (12张图表)
│
├── docs/                           # 文档
│   └── technical_roadmap.md        # 技术路线图
│
└── README.md                       # 本文件
```

---

## 🚀 快速开始

### 环境要求

```bash
# Python环境
pip install numpy pandas matplotlib seaborn scipy

# MySQL
# 下载: https://dev.mysql.com/downloads/

# Tableau
# 下载: https://www.tableau.com/products/desktop
```

### 运行步骤

```bash
# Step 1: 数据清洗
python python/01_data_cleaning.py

# Step 2: 探索性分析
python python/02_exploratory_analysis.py

# Step 3: 高级分析
python python/03_advanced_analysis.py

# Step 4: 生成可视化图表
python python/04_visualizations.py

# Step 5: MySQL数据导入
# 1. 在MySQL中执行 sql/01_create_database.sql
# 2. 执行 sql/02_data_import.sql 导入CSV数据
# 3. 执行 sql/03_crud_queries.sql 进行SQL分析

# Step 6: Tableau看板制作
# 完成销售、用户、商品、评论四个主题看板
```

---

## 📈 核心功能

### 1. 数据清洗 (`01_data_cleaning.py`)
- ✅ 缺失值检测与处理
- ✅ 重复数据去重
- ✅ 异常值检测(箱线图法/Z-score)
- ✅ 数据类型转换与标准化
- ✅ 特征工程(分箱/编码/衍生字段)

### 2. 探索性分析 (`02_exploratory_analysis.py`)
- 📊 单变量分布分析
- 📊 双变量相关性分析
- 📊 时间序列趋势分析
- 📊 Top-N排行分析
- 📊 交叉分组统计

### 3. 高级分析 (`03_advanced_analysis.py`)
- 👥 **RFM客户价值分群**: 将用户分为高/中/一般/低价值四类
- 📅 **同期群留存分析**: 按注册月份追踪用户留存率
- 🔗 **商品关联分析**: 发现频繁共购商品组合
- 📉 **趋势预测**: 移动平均和线性回归预测
- ⚠️ **流失预警**: 识别90天未消费的潜在流失用户

### 4. 数据可视化 (`04_visualizations.py`)
12张专业图表，涵盖：
- 销售趋势折线图、品类柱状图、评分饼图
- 用户年龄直方图、散点图、环形图
- 地域分布数据导出(Tableau热力图用)

### 5. MySQL数据库 (`sql/`)
- 5张核心业务表 + 外键约束
- 25个优化索引
- 3个分析视图
- 1个RFM存储过程
- 1个评分自动更新触发器
- 30+条业务分析SQL(覆盖CRUD全场景)

### 6. Tableau看板 (`tableau/`)
- 看板1: 销售运营总览(KPI卡片+趋势+地图+分布)
- 看板2: 用户分析(RFM散点+画像+地域+生命周期)
- 看板3: 商品分析(排名+利润+评分+库存预警)
- 看板4: 评论分析(评分分布+趋势+认证对比)

---

## 🔍 关键数据洞察

1. **用户分层**: 钻石会员(7%)人均消费是普通会员的3.1倍，贡献约16%的总消费额
2. **地域分布**: 北京/上海/广东/浙江四大核心区域合计贡献约39%的订单
3. **支付偏好**: 支付宝(35%)和微信支付(30%)占据主导
4. **评分分布**: 4-5星好评评论占比66%，平均评分3.82
5. **客单价**: 平均客单价约312元，中位数158元（低价日用品购买频次高、高价大件占比低，符合真实电商结构）
6. **复购率**: 全部用户中复购率(>1单)达89.8%（有订单用户中达91.9%）
7. **品类表现**: 七大品类GMV占比较均衡（电子17.5%、家居15.5%、母婴15.0%、服装14.0%等），电子与家居合计约33%
8. **配送偏好**: 普通快递占比50%，加急(25%)与当日达(10%)合计占35%

---

## 🛠️ 技术栈详解

| 技术 | 核心应用 |
|------|---------|
| **NumPy** | 随机数据生成、统计分析、百分位数计算、线性回归 |
| **Pandas** | 数据加载清洗、groupby聚合、pivot_table透视、merge关联、时间序列 |
| **Matplotlib** | 折线图、柱状图、饼图、散点图、直方图、环形图 |
| **MySQL** | DDL建库表索引、DML增删改查、视图、存储过程、触发器、窗口函数 |
| **Tableau** | 数据连接、计算字段、LOD表达式、交互看板、地图可视化 |

---

## 📝 简历项目描述 (Resume-Ready)

> **NovelMart 电商经营分析平台** | Python, NumPy, Pandas, MySQL, Tableau | 2026.07
>
> 基于 NovelMart E-Commerce Dataset（30万+条，2024-2026）独立构建了完整的电商经营分析平台。设计并实现了5张业务数据表(用户/商品/订单/明细/评论)的MySQL数据库，编写了25个优化索引、3个分析视图及RFM存储过程，覆盖CRUD全场景操作。使用Pandas/NumPy完成数据清洗流水线(缺失值处理、异常值检测、特征工程、跨表口径对账)，并进行RFM客户分群、同期群留存分析及商品关联规则挖掘等多维度深度分析。使用Matplotlib产出12张专业数据图表，使用Tableau设计4个交互式业务看板(销售总览/用户分析/商品分析/评论分析)。基于分析结果提炼8条可落地的商业洞察，包括用户价值分层、地域销售策略、品类优化建议等。

---

## 📄 License

MIT License - 仅供学习展示使用

---

## 👤 作者

Cavsin
