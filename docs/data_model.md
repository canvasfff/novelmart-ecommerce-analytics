# NovelMart 电商经营分析平台 - 数据模型 (Entity-Relationship Diagram)

## ER图 (实体关系图)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           电商数据库 ER Diagram                               │
│                      E-commerce Database Schema                               │
└─────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────┐          ┌──────────────────────────┐
│        users             │          │       products           │
├──────────────────────────┤          ├──────────────────────────┤
│ PK  user_id        INT   │          │ PK  product_id     INT   │
│     username   VARCHAR   │          │     product_name VARCHAR  │
│     real_name  VARCHAR   │          │     category    VARCHAR  │
│     email      VARCHAR   │          │     subcategory VARCHAR  │
│     phone      VARCHAR   │          │     brand       VARCHAR  │
│     gender     VARCHAR   │          │     price    DECIMAL     │
│     age            INT   │          │     cost_price DECIMAL   │
│     province   VARCHAR   │          │     stock_quantity INT   │
│     city       VARCHAR   │          │     sales_count    INT   │
│     registration_date    │          │     rating_avg DECIMAL   │
│     membership_level     │          │     listing_date DATE    │
│     total_orders    INT  │          │     status      VARCHAR  │
│     total_spent DECIMAL  │          └────────────┬─────────────┘
│     avg_order_value      │                       │
│     first_order_date     │                       │
│     last_order_date      │                       │
│     total_reviews   INT  │                       │
│     avg_rating_given     │                       │
│     account_age_days INT │                       │
└────────────┬─────────────┘                       │
             │                                     │
             │ 1:N                                 │ 1:N
             │                                     │
             ▼                                     ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│        orders            │          │     order_items          │
├──────────────────────────┤          ├──────────────────────────┤
│ PK  order_id       INT   │───1:N───▶│ PK  item_id        INT   │
│ FK  user_id        INT   │          │ FK  order_id       INT   │
│     order_date  DATETIME │          │ FK  product_id     INT   │
│     total_amount DECIMAL │          │     quantity        INT   │
│     discount_amount      │          │     unit_price  DECIMAL   │
│     actual_amount DECIMAL│          │     discount    DECIMAL   │
│     payment_method       │          └──────────────────────────┘
│     shipping_method      │
│     shipping_cost DECIMAL│
│     order_status VARCHAR │
│     shipping_province    │
│     shipping_city        │
└────────────┬─────────────┘
             │
             │ 1:N
             │
             ▼
┌──────────────────────────┐
│        reviews           │         关系说明:
├──────────────────────────┤         ────────────
│ PK  review_id      INT   │         PK = Primary Key (主键)
│ FK  user_id        INT   │         FK = Foreign Key (外键)
│ FK  product_id     INT   │
│ FK  order_id       INT   │         1:N = 一对多关系
│     rating      TINYINT  │         N:M = 多对多关系
│     review_text   TEXT   │
│     review_date   DATE   │         ──▶ = 引用关系
│     is_verified_purchase │
└──────────────────────────┘


## 表关系说明

| 关系 | 主表 | 从表 | 关联键 | 关系类型 | 说明 |
|------|------|------|--------|---------|------|
| R1 | users | orders | user_id | 1:N | 一个用户可以有多个订单 |
| R2 | orders | order_items | order_id | 1:N | 一个订单包含多个商品明细 |
| R3 | products | order_items | product_id | 1:N | 一个商品可以出现在多个订单中 |
| R4 | orders | reviews | order_id | 1:N | 一个订单可以有多条评论(多商品) |
| R5 | users | reviews | user_id | 1:N | 一个用户可以发表多条评论 |
| R6 | products | reviews | product_id | 1:N | 一个商品可以有多条评论 |


## 数据模型设计思路

### 设计范式
- 遵循**第三范式(3NF)**设计
- 消除数据冗余，保证数据一致性
- 通过外键维护参照完整性
- 在查询性能和数据规范间取得平衡

### 核心设计决策

1. **为什么分离 orders 和 order_items?**
   - 一个订单可以包含多个商品，分离后支持灵活的商品组合
   - 避免订单表中存储重复的订单级信息
   - 支持按商品维度的精细化分析

2. **为什么在 users 表中冗余统计字段?**
   - total_orders、total_spent 等是高频查询字段
   - 适度冗余提升查询性能（牺牲一些存储空间）
   - 通过定期更新或触发器维护一致性

3. **为什么 products 表包含 sales_count?**
   - 销量是最常用的排序和筛选维度
   - 避免每次查询都需要JOIN和聚合
   - 支持实时排行榜查询

4. **review 表关联 order_id 和 product_id 的作用?**
   - 关联order_id: 验证评论来自真实购买(认证购买标识)
   - 关联product_id: 支持商品维度的评分聚合
   - 关联user_id: 支持用户评论行为分析


## 数据流架构

```
[数据生成]                    [数据存储]                    [数据分析]
generate_data.py ──────▶ CSV Files ──────▶ MySQL Database
     │                      │    │               │
     │                      │    │               ├──▶ CRUD操作
     │                      │    │               ├──▶ 聚合查询
     │                      │    │               ├──▶ 窗口函数
     │                      │    │               └──▶ 存储过程
     │                      │    │
     │                      │    └──────────────▶ Python Pandas
     │                      │                        │
     │                      │                        ├──▶ 数据清洗
     │                      │                        ├──▶ EDA分析
     │                      │                        ├──▶ RFM/同期群
     │                      │                        └──▶ 可视化
     │                      │
     │                      └──────────────────▶ Tableau
     │                                               │
     │                                               ├──▶ 看板1: 销售总览
     │                                               ├──▶ 看板2: 用户分析
     │                                               ├──▶ 看板3: 商品分析
     │                                               └──▶ 看板4: 评论分析
```
