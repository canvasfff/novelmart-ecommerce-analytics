#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Olist 电商经营分析平台 —— 模块三：高级分析
Olist E-Commerce Business Analytics — Module 3: Advanced Analytics
=============================================================================

功能概述：
  1. RFM 客户价值分群
  2. 同期群（Cohort）留存分析
  3. 商品品类关联规则（购物篮分析）
  4. 月度销售趋势预测（移动平均 / 指数平滑）
  5. 客户流失风险分层
  6. 客户生命周期价值（CLV）估算
  7. 配送履约质量分析
  8. 导出所有分析结果到 data/processed/advanced_results

适用环境：Python 3.8+, pandas, numpy
=============================================================================
"""

import os
from collections import Counter
from datetime import timedelta
from itertools import combinations

import numpy as np
import pandas as pd

import common

common.configure_console()
common.ensure_dirs()

ADV_OUTPUT_DIR = common.ADV_DIR
VALID_ORDER_STATUSES = common.VALID_ORDER_STATUSES

pd.set_option('display.max_columns', 60)
pd.set_option('display.width', 240)
pd.set_option('display.float_format', lambda x: '%.4f' % x)

print('=' * 70)
print('Olist 电商经营分析 —— 高级分析模块')
print('=' * 70)

# =============================================================================
# 1. 加载数据
# =============================================================================
print('\n[1/8] 加载数据...')

customers_agg = common.load_processed('customers_agg')
products = common.load_processed('products')
orders = common.load_processed('orders')
order_items = common.load_processed('order_items')
reviews = common.load_processed('reviews')

common.to_datetime_columns(orders, [
    'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
    'order_delivered_customer_date', 'order_estimated_delivery_date',
])
common.to_datetime_columns(customers_agg, ['first_order_date', 'last_order_date'])
common.to_datetime_columns(reviews, ['review_creation_date', 'review_answer_timestamp'])
common.to_datetime_columns(order_items, ['shipping_limit_date'])

valid_orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
valid_order_ids = set(valid_orders['order_id'])
valid_items = order_items[order_items['order_id'].isin(valid_order_ids)].copy()
print(f'  加载完成: customers_unique={len(customers_agg):,}, products={len(products):,}, '
      f'orders={len(orders):,}, order_items={len(order_items):,}, reviews={len(reviews):,}')
print(f'  有效订单: {len(valid_orders):,} 条, 有效订单明细: {len(valid_items):,} 条')

# =============================================================================
# 2. RFM 客户价值分群
# =============================================================================
print('\n[2/8] RFM 客户价值分群...')

reference_date = valid_orders['order_purchase_timestamp'].max() + timedelta(days=1)
print(f'  RFM 参考日期: {reference_date.date()}')

rfm = (
    valid_orders.groupby('customer_unique_id')
    .agg(
        recency=('order_purchase_timestamp', lambda x: (reference_date - x.max()).days),
        frequency=('order_id', 'count'),
        monetary=('payment_value', 'sum'),
    )
    .reset_index()
)
rfm = rfm.merge(
    customers_agg[['customer_unique_id', 'customer_state', 'customer_city',
                   'first_order_date', 'last_order_date', 'avg_order_value']],
    on='customer_unique_id', how='left'
)

# 百分位打分：R 越小越好，F/M 越大越好
rfm['R_score'] = pd.qcut(rfm['recency'].rank(method='first'), q=4, labels=[4, 3, 2, 1]).astype(int)
rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int)
rfm['M_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int)
rfm['RFM_score'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']


def segment_customer(row):
    r, f, m = row['R_score'], row['F_score'], row['M_score']
    if r >= 3 and f >= 3 and m >= 3:
        return '重要价值客户'
    if r >= 3 and f < 3 and m >= 3:
        return '重要发展客户'
    if r < 3 and f >= 3 and m >= 3:
        return '重要保持客户'
    if r < 3 and f < 3 and m >= 3:
        return '重要挽留客户'
    if r >= 3 and f >= 3 and m < 3:
        return '一般价值客户'
    if r >= 3 and f < 3 and m < 3:
        return '一般发展客户'
    if r < 3 and f >= 3 and m < 3:
        return '一般保持客户'
    return '一般挽留客户'


rfm['customer_segment'] = rfm.apply(segment_customer, axis=1)

segment_summary = (
    rfm.groupby('customer_segment')
    .agg(
        客户数=('customer_unique_id', 'count'),
        人均消费=('monetary', 'mean'),
        人均订单=('frequency', 'mean'),
        平均最近购买天数=('recency', 'mean'),
    )
    .sort_values('人均消费', ascending=False)
    .reset_index()
)
print('\n  --- RFM 分群结果 ---')
print(segment_summary.to_string(index=False))

rfm_path = os.path.join(ADV_OUTPUT_DIR, 'rfm_customers.csv')
rfm.to_csv(rfm_path, index=False, encoding='utf-8-sig')
segment_summary.to_csv(os.path.join(ADV_OUTPUT_DIR, 'rfm_segment_summary.csv'), index=False, encoding='utf-8-sig')
print(f'  saved: {rfm_path}')

# =============================================================================
# 3. 同期群（Cohort）留存分析
# =============================================================================
print('\n[3/8] 同期群留存分析...')

cohort_data = valid_orders[['customer_unique_id', 'order_purchase_timestamp']].copy()
cohort_data['cohort_month'] = cohort_data.groupby('customer_unique_id')['order_purchase_timestamp'].transform('min').dt.strftime('%Y-%m')
cohort_data['order_month'] = cohort_data['order_purchase_timestamp'].dt.strftime('%Y-%m')
cohort_data['min_ts'] = cohort_data.groupby('customer_unique_id')['order_purchase_timestamp'].transform('min')
cohort_data['month_index'] = (
    (cohort_data['order_purchase_timestamp'].dt.year - cohort_data['min_ts'].dt.year) * 12
    + (cohort_data['order_purchase_timestamp'].dt.month - cohort_data['min_ts'].dt.month)
)

cohort_size = cohort_data.groupby('cohort_month')['customer_unique_id'].nunique()
cohort_active = (
    cohort_data.groupby(['cohort_month', 'month_index'])['customer_unique_id']
    .nunique().reset_index()
)
cohort_active['cohort_size'] = cohort_active['cohort_month'].map(cohort_size)
cohort_active['retention_rate'] = (cohort_active['customer_unique_id'] / cohort_active['cohort_size'] * 100).round(2)
cohort_pivot = cohort_active.pivot_table(
    index='cohort_month', columns='month_index', values='retention_rate', aggfunc='mean'
).reset_index()

print('  --- 留存率矩阵（%）---')
print(cohort_pivot.head(20).to_string(index=False))
cohort_pivot.to_csv(os.path.join(ADV_OUTPUT_DIR, 'cohort_retention.csv'), index=False, encoding='utf-8-sig')

# =============================================================================
# 4. 商品品类关联规则（购物篮分析）
# =============================================================================
print('\n[4/8] 商品品类关联规则...')

items_with_cat = valid_items.merge(
    products[['product_id', 'product_category_name_english']], on='product_id', how='left'
)
# 同一订单内去重品类
basket = (
    items_with_cat.dropna(subset=['product_category_name_english'])
    .groupby('order_id')['product_category_name_english']
    .apply(lambda x: list(dict.fromkeys(x)))
    .reset_index()
)
basket['n_categories'] = basket['product_category_name_english'].apply(len)
multi_basket = basket[basket['n_categories'] >= 2]
print(f'  包含多品类的订单数: {len(multi_basket):,} / {len(basket):,}')

# 统计单品类出现次数（支持度分母）
category_counts = Counter()
for cats in basket['product_category_name_english']:
    category_counts.update(set(cats))
total_baskets = len(basket)

# 统计品类对共现次数
pair_counts = Counter()
for cats in multi_basket['product_category_name_english']:
    for a, b in combinations(set(cats), 2):
        pair_counts[(a, b)] += 1

rules = []
for (a, b), cnt in pair_counts.items():
    if cnt < 20:  # 过滤低支持度噪声
        continue
    support = cnt / total_baskets
    confidence_ab = cnt / category_counts[a]
    confidence_ba = cnt / category_counts[b]
    lift = cnt * total_baskets / (category_counts[a] * category_counts[b])
    rules.append({
        '品类A': a,
        '品类B': b,
        '共现次数': cnt,
        '支持度': round(support, 6),
        '置信度(A→B)': round(confidence_ab, 4),
        '置信度(B→A)': round(confidence_ba, 4),
        '提升度': round(lift, 4),
    })

association_rules = pd.DataFrame(rules).sort_values('提升度', ascending=False)
print(f'  生成关联规则数: {len(association_rules):,}')
if not association_rules.empty:
    print(association_rules.head(10).to_string(index=False))
association_rules.to_csv(os.path.join(ADV_OUTPUT_DIR, 'association_rules.csv'), index=False, encoding='utf-8-sig')

# =============================================================================
# 5. 月度销售趋势预测
# =============================================================================
print('\n[5/8] 月度销售趋势预测...')

orders['order_year_month'] = orders['order_purchase_timestamp'].dt.strftime('%Y-%m')
valid_orders['order_year_month'] = valid_orders['order_purchase_timestamp'].dt.strftime('%Y-%m')
monthly_sales = (
    valid_orders.groupby('order_year_month')['payment_value']
    .sum().reset_index().sort_values('order_year_month')
)
monthly_sales['moving_avg_3'] = monthly_sales['payment_value'].rolling(3).mean()
monthly_sales['ewm_alpha_03'] = monthly_sales['payment_value'].ewm(alpha=0.3, adjust=False).mean()
monthly_sales.columns = ['月份', '实际营收', '3月移动平均', '指数平滑']
print('  --- 月度营收与预测 ---')
print(monthly_sales.round(2).to_string(index=False))
monthly_sales.to_csv(os.path.join(ADV_OUTPUT_DIR, 'sales_forecast.csv'), index=False, encoding='utf-8-sig')

# 简易下月预测（最近3个月均值）
last3_avg = monthly_sales['实际营收'].tail(3).mean()
print(f'  下月营收简单预测（最近3月均值）: R$ {last3_avg:,.2f}')

# =============================================================================
# 6. 客户流失风险分层
# =============================================================================
print('\n[6/8] 客户流失风险分层...')


def recency_segment(days):
    if days <= 90:
        return '活跃客户'
    if days <= 180:
        return '沉默客户'
    if days <= 365:
        return '流失风险客户'
    return '已流失客户'


rfm['lifecycle_stage'] = rfm['recency'].apply(recency_segment)
lifecycle_summary = (
    rfm.groupby('lifecycle_stage')
    .agg(客户数=('customer_unique_id', 'count'), 人均消费=('monetary', 'mean'))
    .reindex(['活跃客户', '沉默客户', '流失风险客户', '已流失客户'])
    .reset_index()
)
print(lifecycle_summary.to_string(index=False))
lifecycle_summary.to_csv(os.path.join(ADV_OUTPUT_DIR, 'customer_lifecycle.csv'), index=False, encoding='utf-8-sig')

# =============================================================================
# 7. 客户生命周期价值（CLV）估算
# =============================================================================
print('\n[7/8] 客户生命周期价值估算...')

# 简化 CLV = 平均客单价 × 平均购买频次（按全部有效订单客户）
clv = rfm.copy()
clv['estimated_clv'] = clv['avg_order_value'] * clv['frequency']
clv_summary = (
    clv.groupby('customer_segment')
    .agg(客户数=('customer_unique_id', 'count'), 平均CLV=('estimated_clv', 'mean'))
    .sort_values('平均CLV', ascending=False)
    .reset_index()
)
print(clv_summary.to_string(index=False))
clv_summary.to_csv(os.path.join(ADV_OUTPUT_DIR, 'clv_by_segment.csv'), index=False, encoding='utf-8-sig')

# =============================================================================
# 8. 配送履约质量分析
# =============================================================================
print('\n[8/8] 配送履约质量分析...')

delivered = valid_orders[valid_orders['order_status'] == 'delivered'].copy()
delivery_summary = (
    delivered.groupby('customer_state')
    .agg(
        订单数=('order_id', 'count'),
        平均送达天数=('delivery_days', 'mean'),
        平均延迟天数=('delivery_delay_days', 'mean'),
        准时率=('is_on_time', 'mean'),
    )
    .reset_index()
)
delivery_summary['准时率(%)'] = (delivery_summary['准时率'] * 100).round(2)
delivery_summary = delivery_summary.sort_values('订单数', ascending=False)
print(delivery_summary.head(15).to_string(index=False))
delivery_summary.to_csv(os.path.join(ADV_OUTPUT_DIR, 'delivery_performance.csv'), index=False, encoding='utf-8-sig')

print('\n高级分析完成 ✅')
