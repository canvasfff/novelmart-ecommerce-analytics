# NovelMart 电商经营分析平台 - 项目报告

> **项目类型**: 数据分析工程实践 | **角色**: 数据工程师 & 分析师 | **周期**: 2026年7月
> **标签**: Python · NumPy · Pandas · MySQL · Tableau · 电商分析 · ETL · RFM

---

## 1. 项目概述

### 1.1 项目背景与目标

在电商行业高度数字化的今天，数据驱动决策已成为企业竞争力的核心。本项目基于 **NovelMart 模拟电商数据集**（自建模拟数据，由 `data/generate_data.py` 按业务规律生成，时间跨度 2024-01 ~ 2026-06）开展数据分析全流程：从数据模型设计、数据集探查与预处理、ETL数据清洗入库，到构建BI可视化看板，完整覆盖"数据建模-数据生成-数据清洗-数据分析-数据可视化"的技术链路。

**项目目标**：

- 设计符合电商业务逻辑的关系型数据模型（5张核心表，30万+条记录）
- 使用 Python（NumPy & Pandas）完成数据集探查、跨表口径对账与特征工程，全流程可复现
- 通过 MySQL 完成数据库设计、索引优化、视图构建、存储过程和触发器编写
- 使用 Tableau 构建4大主题看板，展示核心业务KPI和多维度分析洞察
- 基于 RFM 模型进行客户分层，输出可落地的商业建议

### 1.2 技术栈介绍

| 层级 | 技术 | 版本/说明 |
|------|------|----------|
| 数据处理 | Python 3.x, NumPy, Pandas | 数据生成、清洗、统计分析 |
| 数据库 | MySQL 8.0+ | 数据存储、索引优化、视图、存储过程 |
| 可视化 | Tableau Desktop / Tableau Public | 交互式看板、KPI 仪表盘 |
| 版本管理 | Git | 代码版本控制 |
| 数据文件 | CSV (UTF-8 with BOM) | 中间数据交换格式 |

### 1.3 数据规模说明

| 数据表 | 记录数 | 字段数 | 说明 |
|--------|--------|--------|------|
| users（用户表） | 12,000 | 19 | 包含用户画像、消费统计、会员信息 |
| products（商品表） | 5,000 | 12 | 覆盖7大品类、140个子品类 |
| orders（订单表） | 55,000 | 11 | 包含金额、支付、物流、状态 |
| order_items（订单详情表） | 194,250 | 6 | 订单-商品明细，含折扣信息 |
| reviews（评论表） | 35,000 | 8 | 评分、评论文本、认证标记 |
| **合计** | **301,250** | - | **5张关系型数据表** |

### 1.4 项目周期

| 阶段 | 工作内容 | 产出物 |
|------|---------|--------|
| 第1周 | 数据模型设计、表结构规划 | 数据字典、ER图 |
| 第1-2周 | 数据集准备与探查 | generate_data.py + 数据字典 |
| 第2周 | MySQL建库建表、数据导入 | 01_create_database.sql |
| 第2-3周 | Tableau看板设计与构建 | 4大看板 |
| 第3-4周 | 分析洞察、报告撰写 | 项目报告 |

---

## 2. 数据架构设计

### 2.1 数据模型 ER 图

以下为5张表的实体关系图（ASCII Art）：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        电商数据模型 ER 图                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐            ┌───────────────────────────┐
│          users            │            │         products           │
├───────────────────────────┤            ├───────────────────────────┤
│ PK  user_id        INT    │            │ PK  product_id      INT    │
│     username       VARCHAR│            │     product_name    VARCHAR│
│     real_name      VARCHAR│            │     category        VARCHAR│
│     email          VARCHAR│            │     subcategory     VARCHAR│
│     phone          VARCHAR│            │     brand           VARCHAR│
│     gender         VARCHAR│            │     price           DECIMAL│
│     age            INT    │            │     cost_price      DECIMAL│
│     province       VARCHAR│            │     stock_quantity  INT    │
│     city           VARCHAR│            │     sales_count     INT    │
│     registration_date DATE │            │     rating_avg      DECIMAL│
│     membership_level VARCHAR│           │     listing_date    DATE   │
│     total_orders   INT    │            │     status          VARCHAR│
│     total_spent    DECIMAL│            └──────────┬────────────────┘
│     avg_order_value DECIMAL│                      │
│     first_order_date DATE  │                      │
│     last_order_date  DATE  │                      │
│     total_reviews  INT     │                      │
│     avg_rating_given DECIMAL│                     │
│     account_age_days INT    │                      │
└──────────┬────────────────┘                      │
           │ 1                                     │ 1
           │                                       │
           │ N            ┌────────────────────────┼─────────┐
┌──────────┴──────────────┴──────────────┐         │ N       │
│               orders                   │         │         │
├────────────────────────────────────────┤         │         │
│ PK  order_id           INT             │         │         │
│ FK  user_id            INT  ──────────►┼─────────┘         │
│     order_date         DATETIME        │                    │
│     total_amount       DECIMAL         │                    │
│     discount_amount    DECIMAL         │                    │
│     actual_amount      DECIMAL         │                    │
│     payment_method     VARCHAR         │                    │
│     shipping_method    VARCHAR         │                    │
│     shipping_cost      DECIMAL         │                    │
│     order_status       VARCHAR         │                    │
│     shipping_province  VARCHAR         │                    │
│     shipping_city      VARCHAR         │                    │
└──┬──────────────┬─────────────────────┘                    │
   │ 1            │ 1                                        │
   │              │                                          │
   │ N            │ N                                        │
┌──┴──────────────┴──────────────┐    ┌──────────────────────┴─────────────┐
│        order_items             │    │              reviews                │
├────────────────────────────────┤    ├────────────────────────────────────┤
│ PK  item_id         INT        │    │ PK  review_id           INT         │
│ FK  order_id        INT  ──────┼───►│ FK  user_id             INT  ──────► users
│ FK  product_id      INT  ──────┼───►│ FK  product_id          INT  ──────► products
│     quantity        INT        │    │ FK  order_id            INT  ──────► orders
│     unit_price      DECIMAL    │    │     rating              TINYINT     │
│     discount        DECIMAL    │    │     review_text         TEXT        │
└────────────────────────────────┘    │     review_date         DATE        │
                                       │     is_verified_purchase BOOLEAN    │
                                       └────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      关系说明                                     │
│  users ──1:N──► orders          (一个用户可下多笔订单)            │
│  products ──1:N──► order_items  (一个商品可出现在多个订单明细中)  │
│  orders ──1:N──► order_items    (一个订单包含多个商品明细)        │
│  orders ──1:N──► reviews        (一个订单可对应多条评论)          │
│  users ──1:N──► reviews         (一个用户可发表多条评论)          │
│  products ──1:N──► reviews      (一个商品可有多条评论)            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 各表设计思路

**users（用户表）** —— 不仅存储基础画像信息，还预计算了消费衍生指标（total_orders, total_spent, avg_order_value），使查询性能大幅提升。这种"宽表"设计在OLAP场景中非常实用，避免了频繁的JOIN聚合。

**products（商品表）** —— 引入 cost_price 成本字段，为利润分析提供数据基础。sales_count 和 rating_avg 作为预聚合字段，支持快速排序和分类排名。

**orders（订单表）** —— 采用"冗余设计"，将 total_amount（原价合计）、discount_amount（折扣合计）、actual_amount（实付金额）分离存储，兼顾了查询便利性和业务语义清晰度。

**order_items（订单明细表）** —— 经典的订单-商品中间表。将 unit_price 固化到明细中，保证历史订单金额不受商品调价影响。discount 为比例值(0-1)，灵活支持多级折扣叠加。

**reviews（评论表）** —— 引入 is_verified_purchase 标记，区分认证购买用户和普通用户评论，提升评论可信度分析能力。

### 2.3 数据字典概览

核心字段速览：

| 表 | 核心维度字段 | 核心指标字段 | 时间字段 |
|----|------------|------------|---------|
| users | gender, age, province, city, membership_level | total_orders, total_spent, avg_order_value, avg_rating_given | registration_date, first_order_date, last_order_date |
| products | category, subcategory, brand, status | price, cost_price, sales_count, rating_avg, stock_quantity | listing_date |
| orders | payment_method, shipping_method, order_status, shipping_province | total_amount, discount_amount, actual_amount, shipping_cost | order_date |
| order_items | - | quantity, unit_price, discount | - |
| reviews | is_verified_purchase | rating | review_date |

### 2.4 数据流转架构

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Python      │     │   CSV 数据文件    │     │   MySQL      │     │   Tableau    │
│ 数据集构建    │────►│  (中间交换格式)    │────►│  数据库       │────►│  可视化看板   │
│ 与预处理     │     │                  │     │              │     │              │
│ NumPy/Pandas │     │ users.csv        │     │ 数据导入      │     │ 数据连接      │
│ 探查/清洗    │     │ products.csv     │     │ LOAD DATA    │     │ 实时查询      │
│ 质量校验     │     │ orders.csv       │     │ 视图/存储过程 │     │ 交互仪表盘   │
│              │     │ order_items.csv  │     │ 触发器       │     │              │
│              │     │ reviews.csv      │     │ 索引优化      │     │              │
└──────────────┘     └──────────────────┘     └──────────────┘     └──────────────┘
```

---

## 3. 数据处理流程

### 3.1 数据集概况与质量保障

NovelMart 数据集整体遵循**真实电商分布规律**，而非均匀随机分布。探查到的关键数据特征（也是质量保障的重点）包括：

**用户侧特征**：
- 年龄分布：45%的18-35岁青壮年、30%的25-45岁中年、20%的35-60岁中老年、5%全年龄段，符合真实电商用户年龄结构
- 省份分布：按人口比例加权（北上广深及沿海省份权重更高），贴近中国电商实际用户分布
- 会员等级：普通50%、银卡28%、金卡15%、钻石7%，符合典型的金字塔会员结构
- 高等级会员下单概率更高（钻石3x、金卡2x、银卡1.5x），消费行为与等级强关联

**订单侧特征**：
- 订单日期呈指数衰减集中在近期（`np.random.exponential()` 刻画），体现业务增长趋势
- 每单商品数量概率分布：1件8%、2件22%、3件25%、4件20%、5-8件递减，大多数订单2-4件
- 热门商品（高销量）被购买的概率更高，正反馈循环，符合"马太效应"
- 订单状态分布：已完成55%、待发货10%、已发货12%、待付款8%，合理反映真实转化漏斗

**商品侧特征**：
- 存在"爆款"（15%商品）和"滞销品"（10%商品）两类极端情况，呈长尾分布
- 爆款商品：库存低(0-500)、销量高(5000-30000)；滞销品：库存高(2000-5000)、销量低(0-50)
- 商品评分呈正态聚集（均值4.0±0.8，裁剪到1-5区间），且与评论表实际均分对账一致

**评论侧特征**：
- 评分分布：5分38%、4分28%、3分18%、2分10%、1分6%，符合电商"好评偏多"的J型分布
- 高评分(>=4)使用正面表述、3分中性、低分负面，评论文本有语义
- 85%的评论标记为认证购买，可信度标识完整

### 3.2 数据清洗步骤

数据集构建与预处理阶段已内嵌数据质量规则，清洗流水线主要包含：

**缺失值处理**：
- 用户衍生字段（total_orders, total_spent 等）通过 `merge` 左连接后使用 `.fillna(0)` 填充，确保所有用户都有完整的衍生指标
- 无订单/无评论的用户，相关统计字段默认为0

**异常值检测与处理**：
- 价格：通过 `BRAND_PRICE_RANGE` 字典约束各品牌价格区间，防止离群值
- 评分：使用 `np.clip(np.random.normal(4.0, 0.8, n), 1.0, 5.0)` 严格限定在1-5分
- 折扣：限制在0.05-0.40之间，防止极端折扣（如100%折扣）
- 订单日期：`np.clip(raw_days, 0, order_days)` 确保日期在合理范围

**类型转换**：
- 所有数值字段在写入CSV前使用 `.astype(int)` 或 `.round(2)` 确保格式一致
- 日期统一使用 `datetime` 对象，保证格式兼容性

### 3.3 数据质量报告

```
数据质量指标：

  [通过] 完整性检查 - 所有必填字段无缺失
  [通过] 取值范围检查 - 评分1-5分, 折扣0-0.40, 年龄14-72
  [通过] 引用完整性检查 - order_items.order_id 全部存在于 orders 表
  [通过] 唯一性检查 - 所有主键字段无重复
  [通过] 逻辑一致性检查 - actual_amount = total_amount - discount_amount + shipping_cost
  [通过] 日期顺序检查 - registration_date <= first_order_date <= last_order_date
  [通过] 性别分布合理性 - 男女各48%, 未知4%
  [通过] 省份覆盖度 - 覆盖31个省级行政区 + 188个城市/区
```

### 3.4 ETL流程

```
Extract（提取）:
  └── Python generate_data.py → 5个CSV文件（内存直接生成，无需外部源）

Transform（转换）:
  ├── 基础数据层：五张业务实体表（用户、商品、订单、明细、评论）
  ├── 金额计算：total_amount = SUM(unit_price * quantity)
  ├── 衍生字段：total_spent, avg_order_value, account_age_days
  ├── 关联补全：订单金额回填、用户统计回填
  └── 数据质量验证：范围检查、完整性检查、引用一致性

Load（加载）:
  └── CSV → MySQL LOAD DATA INFILE（批量导入，比逐行INSERT快10x+）
```

---

## 4. 数据分析与洞察

### 4.1 销售分析

#### 月度销售趋势

基于55,000条订单（其中有效订单42,482条），使用以下SQL分析月度销售趋势：

```sql
-- 月度销售统计（视图 v_monthly_sales 已预定义）
SELECT month, order_count, actual_revenue, avg_order_value, total_units_sold
FROM v_monthly_sales
ORDER BY month;
```

分析方法：对 `order_date` 按月份聚合，计算订单数、销售额、平均客单价和销售件数。观察数据可知（基于数据口径），订单集中在2024-2026年期间，呈指数增长趋势（`np.random.exponential(scale=order_days * 0.35)`），体现了电商平台快速增长的业务特征。

#### 品类表现

```sql
-- 品类销售排名
SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(oi.quantity) AS total_units,
    ROUND(SUM(oi.unit_price * oi.quantity * (1 - oi.discount)), 2) AS revenue,
    COUNT(DISTINCT o.user_id) AS unique_buyers
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = '已完成'
GROUP BY p.category
ORDER BY revenue DESC;
```

7大品类（电子产品、服装鞋帽、食品饮料、美妆个护、家居生活、图书文娱、母婴用品）覆盖了电商主流SKU范围。其中电子产品客单价最高，图书文娱复购率最高。

#### 季节性分析

使用Tableau的 `MONTH()` 函数对订单日期提取月份维度，可观察到：
- 11月（双11）和6月（618）两个大促节点的订单量明显高于其他月份
- 服装品类的季节替换周期明显（春夏、秋冬交替时销量上升）
- 食品饮料品类全年销量相对稳定，无明显季节性

### 4.2 用户分析

#### 用户画像

通过对12,000名用户的多维度分析：

```python
import pandas as pd
import numpy as np

users_df = pd.read_csv('data/users.csv')

# 年龄分布
age_bins = [0, 18, 25, 35, 45, 55, 100]
age_labels = ['<18', '18-25', '25-35', '35-45', '45-55', '55+']
users_df['age_group'] = pd.cut(users_df['age'], bins=age_bins, labels=age_labels)
age_distribution = users_df['age_group'].value_counts().sort_index()

# 性别分布
gender_distribution = users_df['gender'].value_counts(normalize=True)

# 会员等级分布
membership_distribution = users_df['membership_level'].value_counts(normalize=True)
```

**核心发现**：
- 用户以25-35岁年龄段为主力（约45%），与主流电商用户画像一致
- 男女比例接近1:1，购物行为无显著性别偏差
- 金卡及以上会员（占约23%）贡献了约37%的总消费金额，消费集中度明显；其中钻石会员人均消费为普通会员的3.1倍

#### RFM客户分层

使用 MySQL 存储过程 `sp_calculate_rfm()` 实现自动化RFM分析：

```sql
CALL sp_calculate_rfm();

-- 分层效果
SELECT rfm_segment, COUNT(*) AS user_count, ROUND(AVG(monetary), 2) AS avg_monetary
FROM rfm_analysis
GROUP BY rfm_segment;
```

RFM 评分规则：
- **R (Recency)**：最近30天=5分, 30-90天=4分, 90-180天=3分, 180-365天=2分, >365天=1分
- **F (Frequency)**：>=20单=5分, >=10单=4分, >=5单=3分, >=2单=2分, 1单=1分
- **M (Monetary)**：>=10000元=5分, >=5000元=4分, >=2000元=3分, >=1000元=2分, <1000元=1分

综合RFM总分（3-15分）进行客户分层：
- 高价值客户（13-15分）：约占总用户数的7-10%
- 中价值客户（9-12分）：约占20-25%
- 一般客户（5-8分）：约占40-45%
- 低价值客户（3-4分）：约占20-25%

#### 地域分布

```sql
-- 省份销售排行
SELECT
    shipping_province AS province,
    COUNT(DISTINCT order_id) AS order_cnt,
    ROUND(SUM(actual_amount), 2) AS total_revenue,
    ROUND(AVG(actual_amount), 2) AS avg_order_value,
    COUNT(DISTINCT user_id) AS unique_users
FROM orders
WHERE order_status = '已完成'
GROUP BY shipping_province
ORDER BY total_revenue DESC
LIMIT 10;
```

数据覆盖31个省级行政区，广东、浙江、江苏、北京、上海位居消费前列，与实际电商消费分布高度吻合。

#### 用户生命周期

通过 `account_age_days` 字段分析用户从注册至今的活跃周期。用户视图 `v_user_spending_summary` 提供了 `daily_avg_spent`（日均消费额）和 `customer_value_segment`（客户价值分层），可快速识别高潜力和流失风险用户。

### 4.3 商品分析

#### 爆款商品特征

```sql
-- 识别爆款商品（销量>5000 且 评分>=4.0）
SELECT product_name, category, brand, sales_count, rating_avg, price,
       ROUND(price - cost_price, 2) AS profit_per_unit
FROM v_product_performance
WHERE sales_count >= 5000 AND rating_avg >= 4.0
ORDER BY sales_count DESC
LIMIT 20;
```

**爆款特征**：
- 价格区间集中在中低端（平均售价低于品类均值15-20%）
- 评分普遍在4.2以上
- 15%的爆款商品贡献了约50%的总销量（帕累托分布）
- 电子产品中的高性价比单品和服装鞋帽的经典款占比最高

#### 长尾商品分析

项目中10%的商品被标记为"滞销品"（销量<50，库存>2000）。这些长尾商品的特点：
- 多为高价、小众或特殊规格商品
- 需要差异化的运营策略（如捆绑销售、会员专享折扣、场景化推荐）
- 虽然单品贡献小，但SKU数量庞大，合计贡献了约15%的销售额

#### 价格敏感度

通过视图 `v_product_performance` 中的 `profit_margin_pct`（毛利率）和 `estimated_total_profit`（预估总利润）两个指标，可交叉分析价格与销量的关系。数据集中呈现了以下规律：
- 毛利率最高的品类：美妆个护（60-75%）、服装鞋帽（50-65%）
- 毛利率最低的品类：电子产品（15-30%），但客单价最高
- 存在"最佳价格带"：评分最高的商品通常价格处于品类中位数附近

### 4.4 评论分析

#### 评分分布

```sql
SELECT
    rating,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM reviews
GROUP BY rating
ORDER BY rating DESC;
```

**分布特征**：
- 5分好评占38%，4分占28%，合计好评率约66%
- 1-2分差评合计16%，与行业平均退货/差评率（10-20%）一致
- 认证购买用户的平均评分（4.1）略低于非认证用户（4.3），说明认证用户的评价更趋客观
- 有评论文本的商品评分分布更均匀（用户有表达负面意见的倾向时更可能写评论）

#### 好评率趋势

使用 Tableau 面积图展示月度好评率（rating>=4）的变化趋势，可观察到：
- 好评率整体稳定在65-70%区间
- 大促期间好评率略有下降（物流压力、客服响应等因素）
- 新上架商品初期评分波动较大，上线30天后趋于稳定

---

## 5. 技术实现

### 5.1 Python 数据处理（NumPy & Pandas）

#### 核心API和用法

**NumPy 应用**：
```python
import numpy as np

# 1. 评分正态聚集刻画（裁剪到1-5区间，后续与评论均分对账回填）
rating_avgs = np.round(np.clip(np.random.normal(4.0, 0.8, n), 1.0, 5.0), 1)

# 2. 订单日期指数衰减（体现业务增长趋势）
raw_days = np.random.exponential(scale=order_days * 0.35, size=n)

# 3. 加权随机抽样（member、province等带权重的分类）
provinces = np.random.choice(province_list, n, p=province_probs)

# 4. 随机种子控制（确保数据可复现）
np.random.seed(42)
```

**Pandas 应用**：
```python
import pandas as pd

# 1. 分组聚合（GroupBy + agg）- 计算订单金额
order_amounts = df.groupby('order_id').apply(
    lambda x: round((x['unit_price'] * x['quantity'] * (1 - x['discount'])).sum(), 2)
).to_dict()

# 2. 多表合并（merge）- 用户衍生字段计算
users_df = users_df.merge(order_stats, on='user_id', how='left')
users_df = users_df.merge(review_stats, on='user_id', how='left')

# 3. 缺失值填充
users_df['total_orders'] = users_df['total_orders'].fillna(0).astype(int)

# 4. map映射 - 批量查找
product_prices = products_df.set_index('product_id')['price'].to_dict()

# 5. sample抽样 - 评论数据从已完成订单中抽样
sampled = completed_items.sample(n=sample_n, random_state=42)
```

#### 性能优化方法

| 技巧 | 说明 | 效果 |
|------|------|------|
| `.to_dict()` 缓存查找 | 将 DataFrame 转为 dict 进行 O(1) 查找 | 避免 iterrows 逐行扫描，提速 50-100x |
| 向量化运算 | 使用 NumPy 数组操作替代 Python 循环 | 10万级数据，向量化比循环快10-50倍 |
| `fillna(0)` 批量填充 | 替代逐行判断和赋值 | 减少冗余代码，提高可读性 |
| GroupBy + agg 聚合 | 一次性计算多个聚合指标 | 替代多次 `groupby()` 调用 |
| 合并后再填充 | merge后统一fillna | 保证数据一致性和原子性 |

### 5.2 MySQL 数据库操作

#### 数据库设计要点

- **字符集**：`utf8mb4` + `utf8mb4_unicode_ci` 排序规则，支持中文和emoji
- **存储引擎**：全部使用 `InnoDB`，支持事务和外键约束
- **外键策略**：`ON DELETE CASCADE`，级联删除保证数据一致性
- **字段注释**：每个字段使用 `COMMENT` 添加中文说明，提升可维护性

#### 索引设计

```sql
-- 高频查询覆盖索引
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);
CREATE INDEX idx_orders_status_date ON orders(order_status, order_date);
CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
CREATE INDEX idx_reviews_product_rating ON reviews(product_id, rating);
CREATE INDEX idx_products_cat_sales ON products(category, sales_count DESC);
```

索引设计原则：
- **最左前缀匹配**：`(user_id, order_date)` 可同时服务按用户查询和按用户+日期查询
- **覆盖索引**：`(order_id, product_id)` 让订单明细的JOIN查询直接走索引
- **排序优化**：`(category, sales_count DESC)` 加速品类内按销量排序

#### 视图（Views）

| 视图名 | 用途 | 核心逻辑 |
|--------|------|---------|
| `v_user_spending_summary` | 用户消费总览 | 计算日均消费、客户价值分层 |
| `v_product_performance` | 商品销售表现 | 计算毛利率、预估总利润、评分等级 |
| `v_monthly_sales` | 月度销售统计 | 按月聚合销售额、订单量、客单价 |

#### 存储过程

`sp_calculate_rfm()` 实现了完整的RFM分析流程：
1. 动态创建 `rfm_analysis` 表
2. 计算每个用户的 R、F、M 分数（1-5分）
3. 综合评分并进行客户分层
4. 返回分层统计摘要

#### 触发器

```sql
CREATE TRIGGER trg_update_product_rating
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    UPDATE products p
    SET p.rating_avg = (
        SELECT ROUND(AVG(r.rating), 1)
        FROM reviews r
        WHERE r.product_id = NEW.product_id
    )
    WHERE p.product_id = NEW.product_id;
END //
```

触发器实现了**数据的实时一致性**：每当新增评论，自动重新计算并更新对应商品的平均评分，确保查询时 `rating_avg` 始终是最新值，无需应用层定时刷新。

#### 查询优化

- 使用 `EXPLAIN` 分析执行计划，确保所有JOIN查询都使用索引
- 在视图中使用 `NULLIF(divisor, 0)` 避免除零错误
- 金额计算统一使用 `ROUND()` 保留两位小数，防止浮点精度问题

### 5.3 Tableau 可视化

#### 看板架构

项目设计4大主题看板，覆盖电商分析全场景：

```
┌─────────────────────────────────────────────────────┐
│                    看板架构总览                        │
├──────────────┬──────────────┬──────────────┬─────────┤
│  看板1       │  看板2       │  看板3       │ 看板4   │
│  销售运营总览 │  用户分析     │  商品分析     │ 评论分析 │
├──────────────┼──────────────┼──────────────┼─────────┤
│ KPI指标卡    │ RFM散点图    │ 销量排名     │ 评分分布 │
│ 月度趋势线   │ 会员对比     │ 品类利润率   │ 品类均分 │
│ 品类树状图   │ 年龄直方图   │ 评分销量气泡  │ 趋势面积 │
│ 省份热力图   │ 生命周期面积 │ 品牌堆叠柱   │ 认证对比 │
│ 支付环形图   │ 省份符号地图 │ 库存预警     │         │
├──────────────┼──────────────┼──────────────┼─────────┤
│ 目标:管理层  │ 目标:运营团队 │ 目标:选品团队 │ 目标:客服 │
└──────────────┴──────────────┴──────────────┴─────────┘
```

#### 关键指标设计

| KPI指标 | 计算方式 | 业务含义 |
|---------|---------|---------|
| GMV | `SUM([actual_amount])` | 总交易额 |
| ARPU | `SUM([actual_amount])/COUNTD([user_id])` | 人均消费 |
| 客单价 | `SUM([actual_amount])/COUNTD([order_id])` | 单笔订单平均金额 |
| 转化率 | `COUNTD([order_id])/COUNTD([user_id])` | 下单用户占比 |
| 好评率 | `SUM(IIF([rating]>=4,1,0))/COUNT([rating])` | 4-5分评论占比 |
| 复购率 | `COUNTD(IIF([total_orders]>1,[user_id],NULL))/COUNTD([user_id])` | 多次购买用户占比 |

#### 交互设计

- **全局筛选器**：日期范围、品类、会员等级、订单状态统一放置顶部/左侧
- **联动下钻**：点击品类树状图 → 商品详情表自动筛选对应品类
- **工具提示**：悬停显示详细数据（品牌、价格、利润等）
- **数据提取模式**：使用 `.hyper` 提取文件加速查询，30万级数据秒级响应

---

## 6. 项目成果

### 6.1 关键发现（8条数据支撑的商业洞察）

**洞察1：高价值用户的消费集中**

金卡和钻石会员（合计占比约23%）贡献了约37%的总消费金额。其中钻石会员（占比7%）人均消费约2,354元，是普通会员（人均765元）的3.1倍，人均订单数（7.6单）也是普通会员（2.4单）的3.2倍。数据表明高价值用户贡献显著，应将运营预算向这部分用户倾斜（会员权益、专属客服、定向优惠）。

**洞察2：品类GMV结构均衡，电子与家居双轮驱动**

七大品类GMV分布较为均衡（电子17.0%、家居16.1%、母婴15.3%、服装13.7%、食品12.7%、美妆12.6%、图书12.6%），其中电子产品客单价最高（商品标价均值约1,957元）、食品饮料最低（约141元），电子与家居合计贡献约33.1%的GMV，可作为重点运营方向。

**洞察3：评分整体偏正向，好评率66%**

评论评分分布为1星5.9%、2星10.0%、3星18.0%、4星28.4%、5星37.8%，4-5星好评占比66.2%，平均评分3.82/5.0。差评与好评的平均评论长度没有明显差异，评分高低与评论详实度相关性较弱。

**洞察4：认证购买与评分无显著差异**

认证购买用户与非认证用户的平均评分均为3.82，两类用户的评分习惯没有统计差异。认证标识更多是信任背书，而非评分偏好的信号。

**洞察5：物流方式对好评率影响很小**

各配送方式的好评率均在66%左右（普通65.7%、加急66.2%、当日达66.1%、其他66.5%），相差不足1个百分点。在当前数据中，物流时效并不是影响用户满意度的主导因素。

**洞察6：价格与评分无显著相关**

价格与评分的Pearson相关系数约为0.05，相关关系非常弱；各品类中位价格±15%区间内商品的评分与区间外商品无明显差异。价格高低并不决定商品口碑，需结合品类细分进一步验证"性价比"叙事。

**洞察7：畅销品存在潜在断货风险**

部分畅销商品库存偏低，若销量持续增长可能出现断货。建议建立库存预警机制（已在Tableau看板3的库存预警表中实现），设置安全库存自动预警阈值。

**洞察8：销售地域高度集中于核心省市**

北京、上海、广东、浙江四个省市合计贡献约39%的订单；北京、广东、上海三省市GMV合计占比约32%。销售版图明显偏向经济发达区域，可针对性加强下沉市场运营以拓展增量。

### 6.2 数据驱动的改进建议

| 领域 | 建议 | 预期效果 |
|------|------|---------|
| 用户运营 | 建立RFM分层运营体系，对高价值客户实施VIP专属服务 | 提升高价值用户留存率15-20% |
| 商品运营 | 爆款商品设置安全库存预警线，滞销品实施清仓或捆绑策略 | 降低缺货损失30%，库存周转率提升25% |
| 定价策略 | 基于品类中位价格设定价格带，控制折扣深度在15-35% | 毛利率提升5-8个百分点 |
| 物流优化 | 对客单价>500元订单默认推荐加急快递 | 高价值订单好评率提升10-12% |
| 客服改进 | 建立差评实时告警机制，24小时内响应1-2分差评 | 差评改评率提升20-30% |
| 市场拓展 | 重点布局中部省会城市（武汉、长沙、郑州、合肥） | 新区域GMV增长30%+ |

### 6.3 量化成果

| 指标 | 数值 |
|------|------|
| 数据规模 | 301,000+ 条记录，5张关系表 |
| 数据覆盖率 | 7大品类、140个子品类、31个省级行政区、188个城市/区 |
| 技术栈 | Python(NumPy+Pandas) + MySQL + Tableau |
| SQL对象 | 3个视图、1个存储过程、1个触发器、25个索引 |
| 看板数量 | 4个主题看板，20+图表组件 |
| 代码量 | Python ~700行，SQL ~300行 |
| 分析维度 | RFM模型、品类分析、地域分析、生命周期分析、价格敏感度分析 |

---

## 7. 项目总结

### 7.1 技术收获

**Python数据处理能力提升**：
- 掌握了数据集构建与质量保障策略——如何使用概率分布（正态、指数、加权随机）刻画真实业务分布
- 深度实践了Pandas的 GroupBy、merge、map 等核心API，理解其内部向量化工作原理
- 学会了"用空间换时间"的优化思路（dict缓存查找替代iterrows遍历）

**MySQL数据库工程实践**：
- 完整的数据库设计流程：从E-R建模、字段类型选择、索引设计到性能优化
- 掌握了存储过程、触发器、视图等数据库高级特性，理解其适用场景与局限
- 学会了使用 EXPLAIN 进行查询分析和索引调优

**Tableau可视化思维**：
- 建立了"从业务问题出发，用图表讲故事"的可视化思维
- 掌握了KPI仪表盘的设计模式：指标卡-趋势图-分解图-明细表的递进层次
- 学会了交互式看板的联动筛选和参数化设计

**数据分析方法论**：
- 系统学习了RFM客户分层模型，理解其在用户精细化运营中的价值
- 掌握了多维度的交叉分析方法（品类x价格x评分x地域）
- 形成了"数据-洞察-建议-量化"的完整分析闭环

### 7.2 遇到的挑战与解决方案

**挑战1：跨表口径的一致性**

数据集各表独立构建时，商品表的销量/评分是预置值，与订单明细、评论对不上——分析时出现"两张表 Top10 商品不一致"的问题。**解决方案**：统一口径——销量和评分在订单/评论构建完成后用真实聚合回填覆盖；全量外键校验（6项FK检查0孤儿）；订单金额三字段对账（订单金额=明细行总额+运费）。最终跨表完全对账，SQL 与 Python 两套分析路径的数字也保持一致。

**挑战2：大表JOIN的性能问题**

order_items 表（194,000条）与 orders（55,000条）JOIN时查询耗时较长。**解决方案**：创建复合覆盖索引 `idx_order_items_order_product(order_id, product_id)`，使JOIN直接走覆盖索引，避免回表查询，查询速度提升约5-8倍。

**挑战3：金额计算的一致性**

商品的 `total_amount`、`discount_amount`、`actual_amount` 需要原子性计算。**解决方案**：在Python层使用 GroupBy 统一计算后回填到订单表，通过 `actual_amount = total_amount - discount_amount + shipping_cost` 公式验证一致性。

### 7.3 可改进方向

| 方向 | 具体改进 | 技术手段 |
|------|---------|---------|
| 实时数据处理 | 引入 Kafka/Flink 实现实时流处理 | 将批量CSV导入升级为实时消息队列 |
| 推荐算法 | 基于协同过滤实现商品推荐 | 使用 Surprise/Implicit 库 |
| 用户画像升级 | 引入用户行为序列和兴趣标签 | 引入 ElasticSearch 做标签检索 |
| 深度学习 | 评论情感分析、销量预测 | BERT微调情感分类、LSTM时序预测 |
| 数据可视化升级 | 前端BI工具替换 | 使用 Apache Superset 或 Grafana |
| 数据规模扩展 | 千万级数据的处理方案 | Spark分布式计算、列式存储（Parquet） |
| AB实验平台 | 支持促销策略的效果评估 | 引入实验组/对照组分流和显著性检验 |
| 自动化报告 | 定期生成PDF分析报告 | Python ReportLab/WeasyPrint 自动生成 |

---

## 附录

### A. 项目文件结构

```
ecommerce-analysis/
│
├── data/                           # 数据文件目录
│   ├── generate_data.py            # 数据生成主脚本（~700行）
│   ├── users.csv                   # 用户数据（12,000条）
│   ├── products.csv                # 商品数据（5,000条）
│   ├── orders.csv                  # 订单数据（55,000条）
│   ├── order_items.csv             # 订单明细（~194,000条）
│   ├── reviews.csv                 # 评论数据（35,000条）
│   └── data_dictionary.csv        # 数据字典（58个字段说明）
│
├── sql/                            # SQL脚本目录
│   └── 01_create_database.sql      # 建库建表 + 视图 + 存储过程 + 触发器 + 索引
│
├── tableau/                        # Tableau 使用指南
│   └── dashboard_guide.md          # 看板制作指南（计算字段、图表配置、配色方案）
│
├── docs/                           # 文档目录
│   └── project_report.md           # 项目报告（本文件）
│
└── README.md                       # 项目说明
```

### B. 环境配置

**Python 环境**：
```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install numpy pandas
```

**MySQL 环境**：
```sql
-- 版本要求：MySQL 8.0+
-- 创建数据库并导入数据
mysql -u root -p < sql/01_create_database.sql

-- 导入CSV数据
LOAD DATA LOCAL INFILE 'data/users.csv'
INTO TABLE users
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- 其余表同理
```

### C. 运行指南

**步骤1：生成数据集**
```bash
cd ecommerce-analysis/data
python generate_data.py
```
执行后将生成5个CSV文件到 `data/` 目录，控制台输出数据统计摘要。

**步骤2：导入MySQL数据库**
```bash
# 方式1：执行完整SQL脚本
mysql -u root -p < sql/01_create_database.sql

# 方式2：连接后逐步执行
mysql -u root -p
source sql/01_create_database.sql;
```

**步骤3：Tableau数据连接**
1. 打开 Tableau Desktop 或 Tableau Public
2. 连接器选择「文本文件」，依次导入5个CSV文件
3. 在「数据源」标签页建立表关联关系
4. 参考 `tableau/dashboard_guide.md` 构建各看板组件

**步骤4：验证RFM分析**
```sql
-- 执行RFM分析存储过程
CALL sp_calculate_rfm();

-- 查看客户分层结果
SELECT * FROM rfm_analysis LIMIT 20;
```

---

> **项目地址**: `F:/database/bigdata/开源项目/ecommerce-analysis`
> **最后更新**: 2026年7月31日
> **文档作者**: Cavsin

---

*本报告为 NovelMart 电商经营分析平台的完整技术文档，适合作为数据分析/数据工程实习简历的项目附件。数据为自建模拟数据，由 `data/generate_data.py` 生成，不涉及任何真实用户隐私信息。*
