# Olist 原始数据

本目录存放 **Olist Brazilian E-Commerce Public Dataset** 原始 CSV 文件，数据来源于 Olist / Kaggle 公开数据集。

- 官方数据集名: Brazilian E-Commerce Public Dataset by Olist
- 时间范围: 2016-09 ~ 2018-10
- 下载地址: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- License: CC BY-NC-SA 4.0（仅限学习展示）

## 文件说明

| 文件 | 说明 |
|------|------|
| olist_customers_dataset.csv | 客户表 |
| olist_geolocation_dataset.csv | 邮编级地理坐标 |
| olist_orders_dataset.csv | 订单表 |
| olist_order_items_dataset.csv | 订单明细 |
| olist_order_payments_dataset.csv | 支付记录 |
| olist_order_reviews_dataset.csv | 评论评分 |
| olist_products_dataset.csv | 商品表 |
| olist_sellers_dataset.csv | 卖家表 |
| product_category_name_translation.csv | 品类翻译 |

> 该目录默认被 `.gitignore` 忽略，避免大文件进入 Git 仓库。若需在 Git 中包含数据，可删除 `.gitignore` 中 `data/raw/` 一行。
