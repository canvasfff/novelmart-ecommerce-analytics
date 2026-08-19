#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Olist 电商经营分析平台 —— 模块二：探索性数据分析（EDA）
Olist E-Commerce Business Analytics — Module 2: Exploratory Data Analysis
=============================================================================

功能概述：
  1. 核心经营 KPI 概览
  2. 订单状态、支付方式、评分分布
  3. 品类 / 州 / 城市维度分析
  4. 时间序列：月度订单、营收、评论
  5. Top-N 排行：商品、卖家、品类
  6. 配送时效与准时率分析
  7. 导出 EDA 结果 CSV 到 data/processed/eda_results

适用环境：Python 3.8+, pandas, numpy
=============================================================================
"""

import os

import numpy as np
import pandas as pd

import common

common.configure_console()
common.ensure_dirs()

PROCESSED_DIR = common.PROCESSED_DIR
EDA_OUTPUT_DIR = common.EDA_DIR
VALID_ORDER_STATUSES = common.VALID_ORDER_STATUSES

pd.set_option('display.max_columns', 60)
pd.set_option('display.width', 240)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

print('=' * 70)
print('Olist 电商经营分析 —— 探索性数据分析 (EDA)')
print('=' * 70)

# =============================================================================
# 1. 加载数据
# =============================================================================
print('\n[1/8] 加载清洗后数据...')

customers = common.load_processed('customers')
customers_agg = common.load_processed('customers_agg')
sellers = common.load_processed('sellers')
products = common.load_processed('products')
orders = common.load_processed('orders')
order_items = common.load_processed('order_items')
payments = common.load_processed('payments')
reviews = common.load_processed('reviews')
geolocation_zip = common.load_processed('geolocation_zip')
category_translation = common.load_processed('category_translation')

common.to_datetime_columns(orders, [
    'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
    'order_delivered_customer_date', 'order_estimated_delivery_date',
])
common.to_datetime_columns(reviews, ['review_creation_date', 'review_answer_timestamp'])
common.to_datetime_columns(customers_agg, ['first_order_date', 'last_order_date'])
common.to_datetime_columns(order_items, ['shipping_limit_date'])

print(f'  加载完成: customers={len(customers):,}, customers_unique={len(customers_agg):,}, '
      f'sellers={len(sellers):,}, products={len(products):,}, orders={len(orders):,}, '
      f'order_items={len(order_items):,}, payments={len(payments):,}, reviews={len(reviews):,}')

# 业务口径：有效订单
valid_orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
valid_order_ids = set(valid_orders['order_id'])
valid_items = order_items[order_items['order_id'].isin(valid_order_ids)].copy()

# 合并明细与商品/订单，构造宽表
product_cols = ['product_id', 'product_category_name', 'product_category_name_english']
order_items_full = (
    valid_items
    .merge(products[product_cols], on='product_id', how='left')
    .merge(valid_orders[['order_id', 'customer_state', 'order_purchase_timestamp']],
           on='order_id', how='left')
)
order_items_full['order_year_month'] = order_items_full['order_purchase_timestamp'].dt.strftime('%Y-%m')
order_items_full['line_total'] = order_items_full['price'] + order_items_full['freight_value']

# =============================================================================
# 2. 核心 KPI
# =============================================================================
print('\n[2/8] 核心经营 KPI...')

kpi = {
    '总订单数': len(orders),
    '有效订单数': len(valid_orders),
    '有效订单支付总额(BRL)': valid_orders['payment_value'].sum(),
    '有效订单商品总额(BRL)': valid_orders['total_price'].sum(),
    '有效订单运费总额(BRL)': valid_orders['total_freight'].sum(),
    '平均客单价(BRL)': valid_orders['payment_value'].mean(),
    '唯一客户数': customers_agg['customer_unique_id'].nunique(),
    '唯一商品数': products['product_id'].nunique(),
    '唯一卖家数': sellers['seller_id'].nunique(),
    '评论数': len(reviews),
    '平均评分': reviews['review_score'].mean(),
    '好评率(4-5星)': (reviews['review_score'] >= 4).mean() * 100,
    '平均送达时长(天)': orders['delivery_days'].mean(),
    '准时送达率(%)': orders['is_on_time'].mean() * 100,
}
for k, v in kpi.items():
    if isinstance(v, float):
        print(f'  {k:20s}: {v:,.2f}')
    else:
        print(f'  {k:20s}: {v:,.0f}')

kpi_df = pd.DataFrame([{'指标': k, '数值': v} for k, v in kpi.items()])
kpi_df.to_csv(os.path.join(EDA_OUTPUT_DIR, 'kpi_summary.csv'), index=False, encoding='utf-8-sig')

# =============================================================================
# 3. 单变量分布
# =============================================================================
print('\n[3/8] 单变量分布...')

# 3.1 订单状态
status_dist = orders['order_status'].value_counts().rename_axis('order_status').reset_index(name='订单数')
status_dist['占比(%)'] = (status_dist['订单数'] / len(orders) * 100).round(2)
status_dist['中文状态'] = status_dist['order_status'].map(common.ORDER_STATUS_CN)
print('\n  --- 订单状态分布 ---')
print(status_dist.to_string(index=False))

# 3.2 支付方式
payment_dist = (
    payments.groupby('payment_type')
    .agg(支付笔数=('payment_value', 'count'), 支付总额=('payment_value', 'sum'))
    .sort_values('支付总额', ascending=False)
    .reset_index()
)
payment_dist['中文支付方式'] = payment_dist['payment_type'].map(common.PAYMENT_TYPE_CN)
print('\n  --- 支付方式分布 ---')
print(payment_dist.to_string(index=False))

# 3.3 评论评分
rating_dist = reviews['review_score'].value_counts().sort_index().rename_axis('评分').reset_index(name='评论数')
rating_dist['占比(%)'] = (rating_dist['评论数'] / len(reviews) * 100).round(2)
print('\n  --- 评论评分分布 ---')
print(rating_dist.to_string(index=False))

# 3.4 商品品类（按商品数）
cat_product = (
    products['product_category_name_english']
    .value_counts().rename_axis('category').reset_index(name='商品数')
    .head(15)
)
print('\n  --- 商品数 Top15 品类 ---')
print(cat_product.to_string(index=False))

# =============================================================================
# 4. 双变量 / 多维分析
# =============================================================================
print('\n[4/8] 双变量与多维分析...')

# 4.1 品类销售额
category_sales = (
    order_items_full.groupby('product_category_name_english')
    .agg(
        商品件数=('order_item_id', 'count'),
        商品金额=('price', 'sum'),
        运费金额=('freight_value', 'sum'),
        总销售额=('line_total', 'sum'),
    )
    .sort_values('总销售额', ascending=False)
    .reset_index()
)
category_sales['销售额占比(%)'] = (category_sales['总销售额'] / category_sales['总销售额'].sum() * 100).round(2)
print('\n  --- 品类销售表现 ---')
print(category_sales.head(15).to_string(index=False))

# 4.2 州维度销售
state_sales = (
    valid_orders.groupby('customer_state')
    .agg(
        订单数=('order_id', 'count'),
        支付总额=('payment_value', 'sum'),
        平均客单价=('payment_value', 'mean'),
    )
    .sort_values('支付总额', ascending=False)
    .reset_index()
)
print('\n  --- 州销售表现 ---')
print(state_sales.to_string(index=False))

# 4.3 州维度客户数
state_customers = (
    customers_agg.groupby('customer_state')
    .agg(客户数=('customer_unique_id', 'count'), 人均支付=('total_payment_value', 'mean'))
    .sort_values('客户数', ascending=False)
    .reset_index()
)
print('\n  --- 州客户分布 ---')
print(state_customers.to_string(index=False))

# 4.4 平均配送时效与准时率
delivery_state = (
    valid_orders[valid_orders['order_status'] == 'delivered']
    .groupby('customer_state')
    .agg(
        订单数=('order_id', 'count'),
        平均送达天数=('delivery_days', 'mean'),
        准时率=('is_on_time', 'mean'),
    )
    .sort_values('订单数', ascending=False)
    .reset_index()
)
delivery_state['准时率(%)'] = (delivery_state['准时率'] * 100).round(2)
delivery_state['平均送达天数'] = delivery_state['平均送达天数'].round(2)
print('\n  --- 州配送表现 ---')
print(delivery_state.to_string(index=False))

# =============================================================================
# 5. 时间序列分析
# =============================================================================
print('\n[5/8] 时间序列分析...')

orders['order_year_month'] = orders['order_purchase_timestamp'].dt.strftime('%Y-%m')
valid_orders['order_year_month'] = valid_orders['order_purchase_timestamp'].dt.strftime('%Y-%m')
monthly = (
    valid_orders.groupby('order_year_month')
    .agg(
        订单数=('order_id', 'count'),
        支付总额=('payment_value', 'sum'),
        平均客单价=('payment_value', 'mean'),
        购买客户数=('customer_unique_id', 'nunique'),
    )
    .reset_index()
    .sort_values('order_year_month')
)
print('\n  --- 月度订单/营收趋势 ---')
print(monthly.to_string(index=False))

reviews['review_year_month'] = reviews['review_creation_date'].dt.strftime('%Y-%m')
monthly_reviews = (
    reviews.groupby('review_year_month')
    .agg(评论数=('review_id', 'count'), 平均评分=('review_score', 'mean'))
    .reset_index()
    .sort_values('review_year_month')
)
print('\n  --- 月度评论趋势 ---')
print(monthly_reviews.to_string(index=False))

# =============================================================================
# 6. Top-N 分析
# =============================================================================
print('\n[6/8] Top-N 排行分析...')

# 6.1 Top 商品（按销售额）
top_products = (
    order_items_full.groupby(['product_id', 'product_category_name_english'])
    .agg(销量=('order_item_id', 'count'), 销售额=('line_total', 'sum'))
    .sort_values('销售额', ascending=False)
    .head(20)
    .reset_index()
)
print('\n  --- Top20 商品（销售额）---')
print(top_products.to_string(index=False))

# 6.2 Top 卖家（按销售额）
top_sellers = (
    valid_items.groupby('seller_id')
    .agg(订单数=('order_id', 'nunique'), 销售额=('price', 'sum'), 运费=('freight_value', 'sum'))
    .reset_index()
)
top_sellers['总销售额'] = top_sellers['销售额'] + top_sellers['运费']
top_sellers = top_sellers.sort_values('总销售额', ascending=False).head(20)
print('\n  --- Top20 卖家 ---')
print(top_sellers.to_string(index=False))

# 6.3 Top 州/城市
top_cities = (
    valid_orders.groupby(['customer_state', 'customer_city'])
    .agg(订单数=('order_id', 'count'), 支付总额=('payment_value', 'sum'))
    .sort_values('支付总额', ascending=False)
    .head(20)
    .reset_index()
)
print('\n  --- Top20 城市 ---')
print(top_cities.to_string(index=False))

# =============================================================================
# 7. 相关性分析
# =============================================================================
print('\n[7/8] 相关性分析...')

# 商品价格与销量/评论关系
prod_corr = products[['avg_price', 'quantity_sold', 'revenue', 'review_count']].corr()
print('  --- 商品价格/销量/评论相关性 ---')
print(prod_corr.round(3).to_string())

# 订单金额与配送时效关系（已送达订单）
order_corr = valid_orders[['payment_value', 'item_count', 'delivery_days', 'delivery_delay_days']].corr()
print('  --- 订单金额/明细数/配送时效相关性 ---')
print(order_corr.round(3).to_string())

# =============================================================================
# 8. 导出 EDA 结果
# =============================================================================
print('\n[8/8] 导出 EDA 结果...')

exports = {
    'status_distribution.csv': status_dist,
    'payment_distribution.csv': payment_dist,
    'rating_distribution.csv': rating_dist,
    'category_product_count.csv': cat_product,
    'category_sales.csv': category_sales,
    'state_sales.csv': state_sales,
    'state_customers.csv': state_customers,
    'state_delivery.csv': delivery_state,
    'monthly_sales.csv': monthly,
    'monthly_reviews.csv': monthly_reviews,
    'top_products.csv': top_products,
    'top_sellers.csv': top_sellers,
    'top_cities.csv': top_cities,
    'product_correlation.csv': prod_corr.reset_index().rename(columns={'index': '指标'}),
    'order_correlation.csv': order_corr.reset_index().rename(columns={'index': '指标'}),
}
for filename, df in exports.items():
    path = os.path.join(EDA_OUTPUT_DIR, filename)
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f'  saved: {path}')

print('\nEDA 完成 ✅')
