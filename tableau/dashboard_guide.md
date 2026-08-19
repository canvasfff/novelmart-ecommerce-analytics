# Tableau 看板制作指南 - Olist 电商经营分析平台

## 环境准备

- **推荐版本**: Tableau Desktop 2024.x 或 Tableau Public（免费）
- **下载地址**: https://www.tableau.com/products/desktop
- **Tableau Public**: https://public.tableau.com/

## 数据源准备

建议使用 `data/processed/` 下清洗后的 CSV，已包含业务口径与衍生字段：

| 文件 | 用途 |
|------|------|
| `orders.csv` | 订单事实表（营收、时间、州、物流） |
| `customers_agg.csv` | 客户维度（RFM 基础数据） |
| `products.csv` | 商品维度（品类、销售额、评分） |
| `order_items.csv` | 订单明细（商品、卖家、价格、运费） |
| `payments.csv` | 支付明细 |
| `reviews.csv` | 评论评分 |
| `geolocation_zip.csv` | 邮编级经纬度（地图） |
| `state_sales.csv`（charts/） | 州级聚合，可直接做地图 |

### 数据连接建议

1. 打开 Tableau → 连接「文本文件」；
2. 分别导入上述 CSV；
3. 建立关系：
   - `orders.customer_unique_id` = `customers_agg.customer_unique_id`
   - `orders.order_id` = `order_items.order_id`
   - `order_items.product_id` = `products.product_id`
   - `orders.order_id` = `payments.order_id`
   - `orders.order_id` = `reviews.order_id`
4. 使用「数据提取」模式提升性能。

> ⚠️ **口径提醒**：所有营收、订单、RFM 指标请使用筛选器过滤
> `order_status IN ('delivered','shipped','invoiced','processing','created','approved')`。

---

## 看板1：销售运营总览 (Sales Overview Dashboard)

### KPI 指标卡
| 指标 | 计算字段 |
|------|---------|
| 总营收 | `SUM([payment_value])` |
| 有效订单数 | `COUNTD([order_id])` |
| 平均客单价 | `SUM([payment_value]) / COUNTD([order_id])` |
| 唯一客户数 | `COUNTD([customer_unique_id])` |
| 平均评分 | `AVG([review_score])` |
| 准时送达率 | `AVG([is_on_time])` |

### 图表组件
1. 月度营收趋势（折线图）：`MONTH(order_purchase_timestamp)` / `SUM(payment_value)`
2. 品类销售占比（条形图/树状图）：`product_category_name_english` / `SUM(price+freight_value)`
3. 州级营收地图（地图）：`customer_state` / `SUM(payment_value)`
4. 支付方式分布（环形图）：`payment_type` / `COUNTD(order_id)`

### 筛选器
日期范围、订单状态、州、品类。

---

## 看板2：客户分析 (Customer Analytics Dashboard)

### 图表组件
1. **RFM 散点图**：`frequency` / `monetary`，颜色按 `recency` 分段
2. **客户分群柱状图**：`customer_segment`（来自 advanced_results/rfm_customers.csv） / 客户数
3. **客户生命周期**：`first_order_date` 同期群 / 留存率
4. **州客户分布**：`customer_state` / `COUNTD(customer_unique_id)`

### 推荐数据源
- `customers_agg.csv`
- `advanced_results/rfm_customers.csv`
- `advanced_results/customer_lifecycle.csv`
- `advanced_results/cohort_retention.csv`

---

## 看板3：商品分析 (Product Analytics Dashboard)

### 图表组件
1. **品类销售额排行**：`product_category_name_english` / `SUM(revenue)`
2. **Top 商品**：`product_id` / `quantity_sold` / `revenue`
3. **商品价格 vs 评分**：`avg_price` / `avg_review_score`，颜色品类
4. **Top 卖家**：`seller_id` / `SUM(price+freight_value)`

### 推荐数据源
- `products.csv`
- `order_items.csv`
- `charts/top_products.csv`

---

## 看板4：评论与履约分析 (Review & Fulfillment Dashboard)

### 图表组件
1. **评分分布**：`review_score` / `COUNT(review_id)`
2. **品类平均评分**：`product_category_name_english` / `AVG(review_score)`
3. **月度评论趋势**：`MONTH(review_creation_date)` / `COUNT(review_id)`，颜色评分段
4. **州配送时效**：`customer_state` / `AVG(delivery_days)` 与 `AVG(is_on_time)`

### 推荐数据源
- `reviews.csv`
- `orders.csv`
- `advanced_results/delivery_performance.csv`

---

## 计算字段示例

```tableau
// 有效订单标志
[order_status] IN ('delivered','shipped','invoiced','processing','created','approved')

// 客户价值分段（基于 customers_agg）
IF [total_payment_value] >= 500 THEN "高价值"
ELSEIF [total_payment_value] >= 200 THEN "中价值"
ELSE "普通价值"
END

// 月度同比
(ZN(SUM([payment_value])) - LOOKUP(ZN(SUM([payment_value])), -12)) /
ABS(LOOKUP(ZN(SUM([payment_value])), -12))
```

## 配色建议
- 主色：`#2A78D6`（蓝）
- 辅助：`#EB6834`（橙）、`#1BAF7A`（绿）、`#E34948`（红）
- 背景：`#FCFCFB`

## 分享方式
- Tableau Public：免费发布到云端；
- Tableau Reader：打包 `.twbx` 分享；
- 图片导出：用于项目报告。
