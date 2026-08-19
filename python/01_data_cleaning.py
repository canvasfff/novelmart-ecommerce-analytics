#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Olist 电商经营分析平台 —— 模块一：数据清洗与特征工程
Olist E-Commerce Business Analytics — Module 1: Data Cleaning & Feature Engineering
=============================================================================

功能概述：
  1. 加载 Olist 原始 9 张 CSV（data/raw）
  2. 数据质量评估：缺失值、重复值、类型、外键完整性
  3. 数据清洗：类型转换、缺失值处理、状态标准化
  4. 特征工程：订单金额、配送时效、商品表现、客户聚合指标
  5. 输出清洗后数据至 data/processed，供后续 EDA / 高级分析 / MySQL 使用

适用环境：Python 3.8+, pandas, numpy
=============================================================================
"""

import os

import numpy as np
import pandas as pd

import common

common.configure_console()
common.ensure_dirs()

PROJECT_DIR = common.PROJECT_DIR
DATA_DIR = common.DATA_DIR
PROCESSED_DIR = common.PROCESSED_DIR
VALID_ORDER_STATUSES = common.VALID_ORDER_STATUSES

pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 220)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

print('=' * 70)
print('Olist 电商经营分析 —— 数据清洗与特征工程')
print(f'项目根目录: {PROJECT_DIR}')
print(f'原始数据目录: {common.RAW_DIR}')
print(f'处理后数据目录: {PROCESSED_DIR}')
print('=' * 70)

# =============================================================================
# 1. 加载原始数据
# =============================================================================
print('\n[1/7] 加载 Olist 原始 CSV...')

customers = common.load_raw('customers')
sellers = common.load_raw('sellers')
products = common.load_raw('products')
orders = common.load_raw('orders')
order_items = common.load_raw('order_items')
payments = common.load_raw('order_payments')
reviews = common.load_raw('order_reviews')
geolocation = common.load_raw('geolocation')
category_translation = common.load_raw('category_translation')

print(f'  customers:            {customers.shape[0]:>9,} 行, {customers.shape[1]} 列')
print(f'  sellers:              {sellers.shape[0]:>9,} 行, {sellers.shape[1]} 列')
print(f'  products:             {products.shape[0]:>9,} 行, {products.shape[1]} 列')
print(f'  orders:               {orders.shape[0]:>9,} 行, {orders.shape[1]} 列')
print(f'  order_items:          {order_items.shape[0]:>9,} 行, {order_items.shape[1]} 列')
print(f'  order_payments:       {payments.shape[0]:>9,} 行, {payments.shape[1]} 列')
print(f'  order_reviews:        {reviews.shape[0]:>9,} 行, {reviews.shape[1]} 列')
print(f'  geolocation:          {geolocation.shape[0]:>9,} 行, {geolocation.shape[1]} 列')
print(f'  category_translation: {category_translation.shape[0]:>9,} 行, {category_translation.shape[1]} 列')

# =============================================================================
# 2. 数据质量评估
# =============================================================================
print('\n[2/7] 数据质量评估...')


def show_missing(df, name):
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) == 0:
        print(f'  {name:20s}: 无缺失值')
    else:
        print(f'  {name:20s}:')
        for col, cnt in missing.items():
            print(f'      {col:35s} {cnt:>9,} ({cnt / len(df) * 100:.2f}%)')


for name, df in [
    ('customers', customers), ('sellers', sellers), ('products', products),
    ('orders', orders), ('order_items', order_items), ('order_payments', payments),
    ('order_reviews', reviews), ('geolocation', geolocation),
    ('category_translation', category_translation),
]:
    show_missing(df, name)

print('\n  --- 主键/逻辑重复检查 ---')
print(f'  customers.customer_id 重复: {customers["customer_id"].duplicated().sum():,}')
print(f'  sellers.seller_id     重复: {sellers["seller_id"].duplicated().sum():,}')
print(f'  products.product_id   重复: {products["product_id"].duplicated().sum():,}')
print(f'  orders.order_id       重复: {orders["order_id"].duplicated().sum():,}')
print(f'  reviews.review_id     重复: {reviews["review_id"].duplicated().sum():,}')
oi_key_dup = order_items.duplicated(subset=['order_id', 'order_item_id']).sum()
pay_key_dup = payments.duplicated(subset=['order_id', 'payment_sequential']).sum()
print(f'  order_items(order_id,order_item_id) 重复: {oi_key_dup:,}')
print(f'  order_payments(order_id,payment_sequential) 重复: {pay_key_dup:,}')

# 外键完整性
print('\n  --- 外键完整性检查 ---')
order_cust_ok = orders['customer_id'].isin(set(customers['customer_id'])).all()
item_order_ok = order_items['order_id'].isin(set(orders['order_id'])).all()
item_product_ok = order_items['product_id'].isin(set(products['product_id'])).all()
item_seller_ok = order_items['seller_id'].isin(set(sellers['seller_id'])).all()
pay_order_ok = payments['order_id'].isin(set(orders['order_id'])).all()
rev_order_ok = reviews['order_id'].isin(set(orders['order_id'])).all()
print(f'  orders.customer_id → customers: {order_cust_ok}')
print(f'  order_items.order_id → orders: {item_order_ok}')
print(f'  order_items.product_id → products: {item_product_ok}')
print(f'  order_items.seller_id → sellers: {item_seller_ok}')
print(f'  order_payments.order_id → orders: {pay_order_ok}')
print(f'  order_reviews.order_id → orders: {rev_order_ok}')

# =============================================================================
# 3. 数据清洗与类型标准化
# =============================================================================
print('\n[3/7] 数据清洗与类型标准化...')

# 3.1 客户表
customers = customers.drop_duplicates(subset=['customer_id']).copy()
customers['customer_city'] = customers['customer_city'].str.strip().str.lower()
customers['customer_state'] = customers['customer_state'].str.strip().str.upper()

# 3.2 卖家表
sellers = sellers.drop_duplicates(subset=['seller_id']).copy()
sellers['seller_city'] = sellers['seller_city'].str.strip().str.lower()
sellers['seller_state'] = sellers['seller_state'].str.strip().str.upper()

# 3.3 商品表：缺失品类归为 unknown，数值缺失统一按 0/中位数填充
products = products.drop_duplicates(subset=['product_id']).copy()
products['product_category_name'] = products['product_category_name'].fillna('unknown').str.strip().str.lower()
products = products.merge(category_translation, on='product_category_name', how='left')
products['product_category_name_english'] = products['product_category_name_english'].fillna('unknown')
numeric_cols = [
    'product_name_lenght', 'product_description_lenght', 'product_photos_qty',
    'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm',
]
for col in numeric_cols:
    products[col] = pd.to_numeric(products[col], errors='coerce')
    products[col] = products[col].fillna(products[col].median() if not products[col].isna().all() else 0).astype(int)

# 3.4 订单表：时间转换
datetime_cols = [
    'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
    'order_delivered_customer_date', 'order_estimated_delivery_date',
]
orders = orders.drop_duplicates(subset=['order_id']).copy()
orders = common.to_datetime_columns(orders, datetime_cols)
orders['order_status'] = orders['order_status'].str.strip().str.lower()
orders['order_status_cn'] = orders['order_status'].map(common.ORDER_STATUS_CN).fillna(orders['order_status'])

# 3.5 订单明细
order_items = order_items.drop_duplicates(subset=['order_id', 'order_item_id']).copy()
order_items = common.to_datetime_columns(order_items, ['shipping_limit_date'])
order_items['price'] = pd.to_numeric(order_items['price'], errors='coerce').fillna(0)
order_items['freight_value'] = pd.to_numeric(order_items['freight_value'], errors='coerce').fillna(0)

# 3.6 支付表
payments = payments.drop_duplicates(subset=['order_id', 'payment_sequential']).copy()
payments['payment_type'] = payments['payment_type'].str.strip().str.lower()
payments['payment_installments'] = pd.to_numeric(payments['payment_installments'], errors='coerce').fillna(0).astype(int)
payments['payment_value'] = pd.to_numeric(payments['payment_value'], errors='coerce').fillna(0)

# 3.7 评论表
reviews = reviews.drop_duplicates(subset=['review_id']).copy()
reviews = common.to_datetime_columns(reviews, ['review_creation_date', 'review_answer_timestamp'])
reviews['review_score'] = reviews['review_score'].astype(int)
reviews['review_comment_title'] = reviews['review_comment_title'].fillna('')
reviews['review_comment_message'] = reviews['review_comment_message'].fillna('')

# 3.8 地理表：按邮编前缀聚合，避免 100 万行冗余数据
geolocation_zip = (
    geolocation.groupby('geolocation_zip_code_prefix')
    .agg(
        geolocation_lat=('geolocation_lat', 'mean'),
        geolocation_lng=('geolocation_lng', 'mean'),
        geolocation_city=('geolocation_city', lambda x: x.mode().iloc[0] if not x.mode().empty else ''),
        geolocation_state=('geolocation_state', lambda x: x.mode().iloc[0] if not x.mode().empty else ''),
    )
    .reset_index()
)

# =============================================================================
# 4. 特征工程：订单/商品/客户聚合指标
# =============================================================================
print('\n[4/7] 特征工程（聚合指标）...')

# 4.1 支付聚合到订单
pay_summary = (
    payments.groupby('order_id')
    .agg(
        payment_count=('payment_sequential', 'count'),
        payment_installments=('payment_installments', 'max'),
        payment_value=('payment_value', 'sum'),
    )
    .reset_index()
)
# 主支付方式：取支付金额最大的一笔
primary_payment = (
    payments.sort_values(['order_id', 'payment_value'], ascending=[True, False])
    .drop_duplicates('order_id')[['order_id', 'payment_type']]
)
pay_summary = pay_summary.merge(primary_payment, on='order_id', how='left')

# 4.2 订单明细聚合到订单
item_summary = (
    order_items.groupby('order_id')
    .agg(
        item_count=('order_item_id', 'count'),
        total_price=('price', 'sum'),
        total_freight=('freight_value', 'sum'),
    )
    .reset_index()
)
item_summary['total_order_value'] = (item_summary['total_price'] + item_summary['total_freight']).round(2)

# 4.3 客户城市/州注入订单
orders = orders.merge(
    customers[['customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 'customer_city', 'customer_state']],
    on='customer_id', how='left',
)
orders = orders.merge(pay_summary, on='order_id', how='left')
orders = orders.merge(item_summary, on='order_id', how='left')
orders['payment_value'] = orders['payment_value'].fillna(0)
orders['payment_count'] = orders['payment_count'].fillna(0).astype(int)
orders['item_count'] = orders['item_count'].fillna(0).astype(int)
orders['total_price'] = orders['total_price'].fillna(0)
orders['total_freight'] = orders['total_freight'].fillna(0)
orders['total_order_value'] = orders['total_order_value'].fillna(0)

# 4.4 配送时效特征（仅已送达订单可计算）
delivered_mask = orders['order_status'] == 'delivered'
orders['delivery_days'] = np.where(
    delivered_mask & orders['order_delivered_customer_date'].notna(),
    (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']).dt.total_seconds() / 86400,
    np.nan,
)
orders['estimated_delivery_days'] = np.where(
    delivered_mask & orders['order_estimated_delivery_date'].notna(),
    (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']).dt.total_seconds() / 86400,
    np.nan,
)
orders['delivery_delay_days'] = np.where(
    delivered_mask & orders['order_delivered_customer_date'].notna() & orders['order_estimated_delivery_date'].notna(),
    (orders['order_delivered_customer_date'] - orders['order_estimated_delivery_date']).dt.total_seconds() / 86400,
    np.nan,
)
orders['is_on_time'] = np.where(
    delivered_mask & orders['delivery_delay_days'].notna(),
    orders['delivery_delay_days'] <= 0,
    np.nan,
)
orders[['delivery_days', 'estimated_delivery_days', 'delivery_delay_days']] = orders[
    ['delivery_days', 'estimated_delivery_days', 'delivery_delay_days']
].round(2)

# 4.5 商品表现聚合：销量、销售额、评论
valid_order_ids = set(orders.loc[orders['order_status'].isin(VALID_ORDER_STATUSES), 'order_id'])
valid_items = order_items[order_items['order_id'].isin(valid_order_ids)].copy()
product_sales = (
    valid_items.groupby('product_id')
    .agg(
        order_count=('order_id', 'nunique'),
        quantity_sold=('order_item_id', 'count'),
        price_sum=('price', 'sum'),
        freight_sum=('freight_value', 'sum'),
    )
    .reset_index()
)
product_sales['revenue'] = (product_sales['price_sum'] + product_sales['freight_sum']).round(2)
product_sales['avg_price'] = (product_sales['price_sum'] / product_sales['quantity_sold']).round(2)

# 评论按商品聚合（通过有效订单明细关联）
product_review = (
    valid_items.merge(reviews[['order_id', 'review_score']], on='order_id', how='inner')
    .groupby('product_id')
    .agg(review_count=('review_score', 'count'), avg_review_score=('review_score', 'mean'))
    .reset_index()
)
product_review['avg_review_score'] = product_review['avg_review_score'].round(2)

products = products.merge(product_sales, on='product_id', how='left')
products = products.merge(product_review, on='product_id', how='left')
products[['order_count', 'quantity_sold', 'price_sum', 'freight_sum', 'revenue', 'review_count']] = products[
    ['order_count', 'quantity_sold', 'price_sum', 'freight_sum', 'revenue', 'review_count']
].fillna(0)
products['avg_price'] = products['avg_price'].fillna(0)
products['avg_review_score'] = products['avg_review_score'].fillna(np.nan)

# 4.6 客户唯一标识聚合（客户价值分析用）
valid_orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
customer_agg = (
    valid_orders.groupby('customer_unique_id')
    .agg(
        first_order_date=('order_purchase_timestamp', 'min'),
        last_order_date=('order_purchase_timestamp', 'max'),
        order_count=('order_id', 'count'),
        total_payment_value=('payment_value', 'sum'),
        avg_order_value=('payment_value', 'mean'),
    )
    .reset_index()
)
customer_info = (
    customers.groupby('customer_unique_id')
    .agg(
        customer_zip_code_prefix=('customer_zip_code_prefix', 'first'),
        customer_city=('customer_city', 'first'),
        customer_state=('customer_state', 'first'),
    )
    .reset_index()
)
customer_agg = customer_agg.merge(customer_info, on='customer_unique_id', how='left')

# 客户评论聚合
customer_review = (
    reviews.merge(orders[['order_id', 'customer_unique_id']], on='order_id', how='left')
    .groupby('customer_unique_id')
    .agg(review_count=('review_id', 'count'), avg_review_score=('review_score', 'mean'))
    .reset_index()
)
customer_agg = customer_agg.merge(customer_review, on='customer_unique_id', how='left')
customer_agg['review_count'] = customer_agg['review_count'].fillna(0).astype(int)
customer_agg['total_payment_value'] = customer_agg['total_payment_value'].round(2)
customer_agg['avg_order_value'] = customer_agg['avg_order_value'].round(2)

# =============================================================================
# 5. 保存清洗后数据
# =============================================================================
print('\n[5/7] 保存清洗后数据...')

common.save_processed(customers, 'customers')
common.save_processed(customer_agg, 'customers_agg')
common.save_processed(sellers, 'sellers')
common.save_processed(products, 'products')
common.save_processed(orders, 'orders')
common.save_processed(order_items, 'order_items')
common.save_processed(payments, 'payments')
common.save_processed(reviews, 'reviews')
common.save_processed(geolocation_zip, 'geolocation_zip')
common.save_processed(category_translation, 'category_translation')

# =============================================================================
# 6. 清洗报告摘要
# =============================================================================
print('\n[6/7] 清洗报告摘要...')
print(f'  有效订单状态: {VALID_ORDER_STATUSES}')
print(f'  有效订单数: {len(valid_orders):,} / {len(orders):,}')
print(f'  有效订单支付总额: R$ {valid_orders["payment_value"].sum():,.2f}')
print(f'  有效订单商品总额: R$ {valid_orders["total_price"].sum():,.2f}')
print(f'  有效订单运费总额: R$ {valid_orders["total_freight"].sum():,.2f}')
print(f'  平均送达时长: {orders["delivery_days"].mean():.2f} 天')
print(f'  准时送达率: {orders["is_on_time"].mean() * 100:.2f}%')
print(f'  客户唯一ID数: {len(customer_agg):,}')
print(f'  商品数: {len(products):,}')

# 写入清洗报告
report_lines = [
    f'Olist 数据清洗报告 {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}',
    f'原始记录数: customers={len(customers):,}, sellers={len(sellers):,}, products={len(products):,}, '
    f'orders={len(orders):,}, order_items={len(order_items):,}, payments={len(payments):,}, reviews={len(reviews):,}',
    f'有效订单口径: {", ".join(VALID_ORDER_STATUSES)}',
    f'有效订单数: {len(valid_orders):,}',
    f'有效订单支付总额: {valid_orders["payment_value"].sum():,.2f} BRL',
    f'平均送达时长: {orders["delivery_days"].mean():.2f} 天',
    f'准时送达率: {orders["is_on_time"].mean() * 100:.2f}%',
    f'外键完整性: orders.customer={order_cust_ok}, items.order={item_order_ok}, '
    f'items.product={item_product_ok}, items.seller={item_seller_ok}, payments.order={pay_order_ok}, reviews.order={rev_order_ok}',
]
report_path = os.path.join(PROCESSED_DIR, f'cleaning_report_{pd.Timestamp.now():%Y%m%d_%H%M%S}.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))
print(f'  清洗报告已写入: {report_path}')

print('\n[7/7] 数据清洗完成 ✅')
