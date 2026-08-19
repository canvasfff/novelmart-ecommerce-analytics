# Olist 电商经营分析平台 - 数据模型 (Entity-Relationship Diagram)

## ER 图（核心业务关系）

```
┌────────────────────────┐         ┌────────────────────────┐
│      customers         │         │       sellers          │
├────────────────────────┤         ├────────────────────────┤
│ PK customer_id         │         │ PK seller_id           │
│     customer_unique_id │         │     seller_zip_prefix  │
│     customer_zip       │         │     seller_city        │
│     customer_city      │         │     seller_state       │
│     customer_state     │         └───────────┬────────────┘
└───────────┬────────────┘                     │
            │ 1:N                              │ 1:N
            ▼                                  ▼
┌────────────────────────┐         ┌────────────────────────┐
│        orders          │         │      order_items       │
├────────────────────────┤         ├────────────────────────┤
│ PK order_id            │──1:N───▶│ PK (order_id,          │
│ FK customer_id         │         │     order_item_id)     │
│     order_status       │         │ FK order_id            │
│     purchase_timestamp │         │ FK product_id          │
│     delivered_date     │         │ FK seller_id           │
│     payment_value      │         │     price              │
│     delivery_days      │         │     freight_value      │
└───────────┬────────────┘         └───────────┬────────────┘
            │                                 │
            │ 1:N                             │ 1:N
            ▼                                 ▼
┌────────────────────────┐         ┌────────────────────────┐
│    order_payments      │         │       products         │
├────────────────────────┤         ├────────────────────────┤
│ PK (order_id,          │         │ PK product_id          │
│     payment_sequential)│         │     category_name      │
│ FK order_id            │         │     category_english   │
│     payment_type       │         │     weight/dimensions  │
│     installments       │         │     sales aggregates   │
│     payment_value      │         └────────────────────────┘
└────────────────────────┘

┌────────────────────────┐
│    order_reviews       │         ┌────────────────────────┐
├────────────────────────┤         │   category_translation │
│ PK review_id           │         ├────────────────────────┤
│ FK order_id            │         │ PK product_category_pt │
│     review_score       │         │     category_english   │
│     comment/message    │         └────────────────────────┘
│     creation_date      │
└────────────────────────┘

┌────────────────────────┐
│     geolocation        │
├────────────────────────┤
│     zip_code_prefix    │
│     lat / lng          │
│     city / state       │
└────────────────────────┘
```

## 表关系说明

| 关系 | 主表 | 从表 | 关联键 | 关系类型 | 说明 |
|------|------|------|--------|---------|------|
| R1 | customers | orders | customer_id | 1:N | 一个订单级客户可有多张订单 |
| R2 | orders | order_items | order_id | 1:N | 一个订单可包含多个商品 |
| R3 | products | order_items | product_id | 1:N | 一个商品可出现在多个订单明细 |
| R4 | sellers | order_items | seller_id | 1:N | 一个卖家可提供多个商品明细 |
| R5 | orders | order_payments | order_id | 1:N | 一个订单可有多期/多种支付 |
| R6 | orders | order_reviews | order_id | 1:N | 一个订单可有一条或多条评论 |
| R7 | products | category_translation | product_category_name | N:1 | 葡萄牙语品类翻译为英文 |

## 数据模型设计思路

### 设计范式
- 事实表与维度表分离，符合**星型/雪花模型**思想
- 订单、明细、支付、评论分表存储，避免数据冗余
- 通过外键维护参照完整性
- 在原始表基础上增加**衍生聚合字段**（订单支付总额、商品销售额、客户消费汇总），兼顾查询性能

### 核心设计决策

1. **为什么 customers 区分 customer_id 和 customer_unique_id？**
   - Olist 中同一真实客户可能生成多个 `customer_id`，因此用户分析必须使用 `customer_unique_id` 做去重，避免高估用户数。

2. **为什么 order_items 使用复合主键 (order_id, order_item_id)？**
   - Olist 没有全局 item_id，`order_item_id` 是订单内序号；复合主键保证唯一性，同时支持多商品订单。

3. **为什么订单表冗余支付聚合字段？**
   - 高频经营指标（支付金额、支付方式、明细行数）在订单表直接冗余，减少每次分析的 JOIN 成本。

4. **为什么评论表只关联 order_id，不直接关联 product_id？**
   - Olist 评论是订单级评价；若需要品类评分，通过 `order_reviews → orders → order_items → products` 关联实现。

5. **为什么 geolocation 按邮编前缀聚合？**
   - 原始地理数据 100 万行，按邮编前缀聚合后约 1.9 万行，足以支撑州/城市地图分析，同时大幅减少存储。

## 数据流架构

```
[Olist 原始 CSV]          [清洗/特征工程]            [存储/分析]
data/raw ────────────▶ python/01_data_cleaning.py ──▶ data/processed
     │                        │                           │
     │                        │                           ├──▶ Python EDA / 高级分析
     │                        │                           ├──▶ MySQL 建表导入
     │                        │                           └──▶ Tableau 看板
     └────────────────────────┘
```
