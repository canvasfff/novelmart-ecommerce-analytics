#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
NovelMart 电商经营分析平台 —— 模块二：探索性数据分析（EDA）
NovelMart E-Commerce Business Analytics — Module 2: Exploratory Data Analysis
=============================================================================

功能概述：
  1. 加载清洗后的数据（或自动回退到原始数据）
  2. 单变量分析 —— 各字段的分布特征
  3. 双变量分析 —— 字段间的关系探索
  4. 时间序列分析 —— 按月的趋势变化
  5. Top-N 分析 —— 最佳表现的产品/城市/品牌
  6. 统计摘要表输出
  7. 导出分析结果为 CSV
  8. 打印关键发现

注：本脚本专注于数值分析与统计计算，不生成图表（图表另行处理）。

适用环境：Python 3.8+, pandas, numpy
作者：Cavsin
日期：2026-07
=============================================================================
"""

import os
import sys
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

# Windows 控制台默认 GBK，统一改为 UTF-8 输出避免中文乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# =============================================================================
# 0. 路径与配置
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
EDA_OUTPUT_DIR = os.path.join(PROCESSED_DIR, 'eda_results')
os.makedirs(EDA_OUTPUT_DIR, exist_ok=True)

# 业务口径：有效订单 = 已付款且未取消/未退款
# 所有营收、销售额、复购、RFM、留存等指标都应基于该口径
VALID_ORDER_STATUSES = ['已完成', '待发货', '已发货']

pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 220)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

print("=" * 70)
print("NovelMart 电商经营分析 —— 探索性数据分析 (EDA)")
print("=" * 70)

# =============================================================================
# 1. 加载数据
# =============================================================================

print("\n[1/8] 加载数据...")

def load_preferred_file(filename_stem):
    """
    优先加载清洗后的 parquet，其次清洗后的 csv，最后回退到原始 csv。
    """
    parquet_path = os.path.join(PROCESSED_DIR, f'{filename_stem}_cleaned.parquet')
    csv_path = os.path.join(PROCESSED_DIR, f'{filename_stem}_cleaned.csv')
    raw_path = os.path.join(DATA_DIR, f'{filename_stem}.csv')

    if os.path.exists(parquet_path):
        print(f"  {filename_stem}: 加载 Parquet (清洗后)")
        return pd.read_parquet(parquet_path)
    elif os.path.exists(csv_path):
        print(f"  {filename_stem}: 加载 CSV (清洗后)")
        return pd.read_csv(csv_path)
    else:
        print(f"  {filename_stem}: 加载原始 CSV (未清洗)")
        return pd.read_csv(raw_path)

users = load_preferred_file('users')
products = load_preferred_file('products')
orders = load_preferred_file('orders')
order_items = load_preferred_file('order_items')
reviews = load_preferred_file('reviews')

# 如果日期列不是 datetime，转换它们
for col in ['registration_date', 'first_order_date', 'last_order_date']:
    if col in users.columns and not pd.api.types.is_datetime64_any_dtype(users[col]):
        users[col] = pd.to_datetime(users[col], errors='coerce')

for col in ['order_date']:
    if col in orders.columns and not pd.api.types.is_datetime64_any_dtype(orders[col]):
        orders[col] = pd.to_datetime(orders[col], errors='coerce')

for col in ['review_date']:
    if col in reviews.columns and not pd.api.types.is_datetime64_any_dtype(reviews[col]):
        reviews[col] = pd.to_datetime(reviews[col], errors='coerce')

for col in ['listing_date']:
    if col in products.columns and not pd.api.types.is_datetime64_any_dtype(products[col]):
        products[col] = pd.to_datetime(products[col], errors='coerce')

print(f"  加载完成: users={len(users):,}, products={len(products):,}, "
      f"orders={len(orders):,}, order_items={len(order_items):,}, "
      f"reviews={len(reviews):,}")

# line_total 仅在清洗后存在；缺失时（回退到原始数据）按相同公式现场计算
if 'line_total' not in order_items.columns:
    order_items['line_total'] = (order_items['quantity'] * order_items['unit_price'] *
                                 (1 - order_items['discount'].fillna(0))).round(2)

# 创建合并视图，方便后续分析
# 清洗后的列（age_group / price_tier）仅在执行过 01_data_cleaning.py 后存在，
# 缺失时回退到原始数据，保证脚本可直接运行（后续用到这些列的位置均有 isin 守卫）
user_merge_cols = ['user_id', 'membership_level', 'age', 'gender', 'province', 'city']
if 'age_group' in users.columns:
    user_merge_cols.append('age_group')

# 将订单与用户信息合并
orders_with_users = orders.merge(
    users[user_merge_cols],
    on='user_id', how='left', suffixes=('', '_user')
)
# 消费类分析只统计有效订单
orders_with_users_valid = orders_with_users[orders_with_users['order_status'].isin(VALID_ORDER_STATUSES)].copy()
valid_orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
# 将订单明细与订单和商品信息合并
product_merge_cols = ['product_id', 'product_name', 'category', 'subcategory', 'brand', 'price']
if 'price_tier' in products.columns:
    product_merge_cols.append('price_tier')
order_items_full = order_items.merge(
    orders[['order_id', 'user_id', 'order_date', 'order_status']],
    on='order_id', how='left'
).merge(
    products[product_merge_cols],
    on='product_id', how='left'
)

# 销售/营收类分析只保留有效订单，避免把未支付、取消、退款订单计入
order_items_full = order_items_full[order_items_full['order_status'].isin(VALID_ORDER_STATUSES)].copy()

print("  已构建分析用合并数据集")

# =============================================================================
# 2. 单变量分析 (Univariate Analysis)
# =============================================================================

print("\n[2/8] 单变量分析...")

# ---------------------------------------------------------------------------
# 2.1 用户年龄分布
# ---------------------------------------------------------------------------

print("\n  --- 2.1 用户年龄分布 ---")
age_stats = users['age'].describe()
print(f"  count={age_stats['count']:.0f}, mean={age_stats['mean']:.2f}, "
      f"std={age_stats['std']:.2f}")
print(f"  min={age_stats['min']:.0f}, 25%={age_stats['25%']:.0f}, "
      f"median={age_stats['50%']:.0f}, 75%={age_stats['75%']:.0f}, "
      f"max={age_stats['max']:.0f}")
print(f"  偏度(skewness)={users['age'].skew():.2f}, 峰度(kurtosis)={users['age'].kurtosis():.2f}")

# 年龄分组分布
if 'age_group' in users.columns:
    age_group_dist = users['age_group'].value_counts().sort_index()
    print(f"  年龄分组分布:")
    for grp, cnt in age_group_dist.items():
        print(f"    {grp}: {cnt:,} ({cnt/len(users)*100:.1f}%)")

# ---------------------------------------------------------------------------
# 2.2 商品价格按品类分布
# ---------------------------------------------------------------------------

print("\n  --- 2.2 商品价格按品类分布 ---")
category_price_stats = products.groupby('category')['price'].agg([
    'count', 'mean', 'std', 'min',
    lambda x: x.quantile(0.25),
    'median',
    lambda x: x.quantile(0.75),
    'max'
]).round(2)
category_price_stats.columns = ['商品数', '均价', '标准差', '最低价', 'P25', '中位数', 'P75', '最高价']
print(category_price_stats.to_string())

# 价格层级分布
if 'price_tier' in products.columns:
    tier_dist = products['price_tier'].value_counts().sort_index()
    print(f"\n  价格层级分布:")
    for tier, cnt in tier_dist.items():
        print(f"    {tier}: {cnt:,} ({cnt/len(products)*100:.1f}%)")

# ---------------------------------------------------------------------------
# 2.3 订单状态分布
# ---------------------------------------------------------------------------

print("\n  --- 2.3 订单状态分布 ---")
status_dist = orders['order_status'].value_counts()
print(f"  订单状态分布:")
for status, cnt in status_dist.items():
    print(f"    {status}: {cnt:,} ({cnt/len(orders)*100:.1f}%)")

# 支付方式分布
pay_dist = orders['payment_method'].value_counts()
print(f"\n  支付方式分布:")
for method, cnt in pay_dist.items():
    print(f"    {method}: {cnt:,} ({cnt/len(orders)*100:.1f}%)")

# ---------------------------------------------------------------------------
# 2.4 评分分布
# ---------------------------------------------------------------------------

print("\n  --- 2.4 评分分布 ---")
rating_dist = reviews['rating'].value_counts().sort_index()
print(f"  评论评分分布:")
for rating, cnt in rating_dist.items():
    bar = '#' * int(cnt / len(reviews) * 100)
    print(f"    {rating}星: {cnt:>8,} ({cnt/len(reviews)*100:>5.1f}%) {bar}")

avg_rating = reviews['rating'].mean()
print(f"  平均评分: {avg_rating:.2f}")
print(f"  好评率(4-5星): {((reviews['rating'] >= 4).sum() / len(reviews) * 100):.1f}%")
print(f"  差评率(1-2星): {((reviews['rating'] <= 2).sum() / len(reviews) * 100):.1f}%")

# 商品平均评分分布
print(f"\n  商品平均评分统计:")
print(f"  mean={products['rating_avg'].mean():.2f}, median={products['rating_avg'].median():.2f}, "
      f"std={products['rating_avg'].std():.2f}")

# =============================================================================
# 3. 双变量分析 (Bivariate Analysis)
# =============================================================================

print("\n[3/8] 双变量分析...")

# ---------------------------------------------------------------------------
# 3.1 各会员等级平均消费
# ---------------------------------------------------------------------------

print("\n  --- 3.1 各会员等级平均消费 ---")
membership_spending = orders_with_users_valid.groupby('membership_level').agg(
    订单数=('order_id', 'count'),
    平均客单价=('actual_amount', 'mean'),
    总消费中位数=('actual_amount', 'median'),
    总消费额=('actual_amount', 'sum')
).round(2)
membership_spending['订单占比(%)'] = (membership_spending['订单数'] /
                                membership_spending['订单数'].sum() * 100).round(1)
print(membership_spending.to_string())

# 各会员等级用户数
user_membership = users.groupby('membership_level').agg(
    用户数=('user_id', 'count'),
    平均年龄=('age', 'mean'),
    人均累计消费=('total_spent', 'mean')
).round(2)
user_membership['用户占比(%)'] = (user_membership['用户数'] /
                             user_membership['用户数'].sum() * 100).round(1)
print(f"\n  各会员等级用户统计:")
print(user_membership.to_string())

# ---------------------------------------------------------------------------
# 3.2 各省份平均消费
# ---------------------------------------------------------------------------

print("\n  --- 3.2 各省份消费统计 (Top 15) ---")
province_spending = orders_with_users_valid.groupby('shipping_province').agg(
    订单数=('order_id', 'count'),
    平均订单金额=('actual_amount', 'mean'),
    总消费额=('actual_amount', 'sum')
).round(2)
province_spending = province_spending.sort_values('总消费额', ascending=False).head(15)
print(province_spending.to_string())

# ---------------------------------------------------------------------------
# 3.3 各品类商品销售情况
# ---------------------------------------------------------------------------

print("\n  --- 3.3 各品类商品销售 ---")
category_sales = order_items_full.groupby('category').agg(
    销售商品数=('product_id', 'nunique'),
    销售件数=('quantity', 'sum'),
    销售额=('line_total', 'sum'),
    平均单价=('unit_price', 'mean')
).round(2)
category_sales['销售额占比(%)'] = (category_sales['销售额'] /
                             category_sales['销售额'].sum() * 100).round(1)
category_sales = category_sales.sort_values('销售额', ascending=False)
print(category_sales.to_string())

# 各品类销量 Top 子类别
print(f"\n  各品类 Top 3 子类别 (按销售额):")
for cat in category_sales.index[:5]:
    subcat = order_items_full[order_items_full['category'] == cat].groupby('subcategory')['line_total'].sum().sort_values(ascending=False).head(3)
    print(f"    [{cat}]")
    for sc, val in subcat.items():
        print(f"      {sc}: {val:,.0f}")

# ---------------------------------------------------------------------------
# 3.4 评分与价格的相关性
# ---------------------------------------------------------------------------

print("\n  --- 3.4 评分与价格相关性 ---")
if 'rating_avg' in products.columns and 'price' in products.columns:
    price_rating_corr = products[['price', 'rating_avg', 'sales_count']].corr()
    print("  相关性矩阵:")
    print(f"  价格 vs 平均评分:  {price_rating_corr.loc['price', 'rating_avg']:.4f}")
    print(f"  价格 vs 销量:      {price_rating_corr.loc['price', 'sales_count']:.4f}")
    print(f"  评分 vs 销量:      {price_rating_corr.loc['rating_avg', 'sales_count']:.4f}")

# 按价格层级统计平均评分
if 'price_tier' in products.columns:
    tier_rating = products.groupby('price_tier')['rating_avg'].agg(['mean', 'std', 'count']).round(3)
    print(f"\n  各价格层级平均评分:")
    print(tier_rating.to_string())

# ---------------------------------------------------------------------------
# 3.5 星期几的订单分布
# ---------------------------------------------------------------------------

print("\n  --- 3.5 订单按星期分布 ---")
if 'day_of_week' in orders.columns:
    day_order_stats = valid_orders.groupby('day_of_week').agg(
        订单数=('order_id', 'count'),
        平均金额=('actual_amount', 'mean'),
        总金额=('actual_amount', 'sum')
    ).round(2)
    day_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
    day_order_stats.index = day_order_stats.index.map(day_names)
    print(day_order_stats.to_string())

# 周末 vs 工作日
if 'is_weekend' in orders.columns:
    weekend_stats = valid_orders.groupby('is_weekend').agg(
        订单数=('order_id', 'count'),
        平均金额=('actual_amount', 'mean')
    ).round(2)
    weekend_stats.index = ['工作日', '周末']
    print(f"\n  工作日 vs 周末:")
    print(weekend_stats.to_string())

# =============================================================================
# 4. 时间序列分析 (Time Series Analysis)
# =============================================================================

print("\n[4/8] 时间序列分析...")

# 用于时间序列的辅助字段
if 'order_year_month' not in orders.columns:
    orders['order_year_month'] = orders['order_date'].dt.strftime('%Y-%m')
if 'order_month' not in orders.columns:
    orders['order_month'] = orders['order_date'].dt.to_period('M').astype(str)

# ---------------------------------------------------------------------------
# 4.1 月度营收趋势
# ---------------------------------------------------------------------------

print("\n  --- 4.1 月度营收趋势 ---")
monthly_revenue = valid_orders.groupby('order_year_month').agg(
    订单数=('order_id', 'count'),
    总营收=('actual_amount', 'sum'),
    平均客单价=('actual_amount', 'mean'),
    总折扣额=('discount_amount', 'sum')
).round(2)
monthly_revenue = monthly_revenue.sort_index()
monthly_revenue['环比增长率(%)'] = monthly_revenue['总营收'].pct_change() * 100
monthly_revenue['环比增长率(%)'] = monthly_revenue['环比增长率(%)'].round(1)

print(f"  共 {len(monthly_revenue)} 个月")
print(f"  月度营收统计: mean={monthly_revenue['总营收'].mean():,.0f}, "
      f"std={monthly_revenue['总营收'].std():,.0f}")
print(f"  最高月份: {monthly_revenue['总营收'].idxmax()} ({monthly_revenue['总营收'].max():,.0f})")
print(f"  最低月份: {monthly_revenue['总营收'].idxmin()} ({monthly_revenue['总营收'].min():,.0f})")
print(f"\n  月度明细 (最近12个月):")
print(monthly_revenue.tail(12).to_string())

# ---------------------------------------------------------------------------
# 4.2 月度订单量趋势
# ---------------------------------------------------------------------------

print("\n  --- 4.2 月度订单量趋势 ---")
monthly_orders = valid_orders.groupby('order_year_month').size()
monthly_orders = monthly_orders.sort_index()
if len(monthly_orders) > 1:
    mom_change = monthly_orders.pct_change() * 100
    print(f"  平均环比变化率: {mom_change.mean():.1f}%")
    print(f"  最大增长: {mom_change.idxmax()} ({mom_change.max():.1f}%)")
    print(f"  最大下降: {mom_change.idxmin()} ({mom_change.min():.1f}%)")

# ---------------------------------------------------------------------------
# 4.3 月度新用户注册趋势
# ---------------------------------------------------------------------------

print("\n  --- 4.3 月度新用户注册趋势 ---")
if 'registration_date' in users.columns:
    users['reg_year_month'] = users['registration_date'].dt.strftime('%Y-%m')
    monthly_new_users = users.groupby('reg_year_month').size().sort_index()
    print(f"  总注册月份: {len(monthly_new_users)}")
    print(f"  月均注册: {monthly_new_users.mean():.0f}")
    print(f"  高峰月份: {monthly_new_users.idxmax()} ({monthly_new_users.max():,})")
    print(f"\n  最近12个月注册趋势:")
    recent_users = monthly_new_users.tail(12)
    for month, cnt in recent_users.items():
        print(f"    {month}: {cnt:>6,}")

# ---------------------------------------------------------------------------
# 4.4 月度评论数趋势
# ---------------------------------------------------------------------------

print("\n  --- 4.4 月度评论数趋势 ---")
if 'review_date' in reviews.columns:
    reviews['review_year_month'] = reviews['review_date'].dt.strftime('%Y-%m')
    monthly_reviews = reviews.groupby('review_year_month').agg(
        评论数=('review_id', 'count'),
        平均评分=('rating', 'mean')
    ).round(3).sort_index()
    print(f"  月均评论数: {monthly_reviews['评论数'].mean():.0f}")
    print(f"  月度平均评分范围: {monthly_reviews['平均评分'].min():.2f} - {monthly_reviews['平均评分'].max():.2f}")

# =============================================================================
# 5. Top-N 分析
# =============================================================================

print("\n[5/8] Top-N 分析...")

# ---------------------------------------------------------------------------
# 5.1 Top 10 畅销商品（按销量）
# ---------------------------------------------------------------------------

print("\n  --- 5.1 Top 10 畅销商品 (按销量) ---")
product_sales = order_items_full.groupby(['product_id', 'product_name', 'category', 'brand']).agg(
    销售数量=('quantity', 'sum'),
    销售额=('line_total', 'sum'),
    订单数=('order_id', 'nunique')
).round(2).sort_values('销售数量', ascending=False).head(10).reset_index()

for i, row in product_sales.iterrows():
    print(f"  {i+1:>2}. {row['product_name'][:30]:<32s} "
          f"销量:{row['销售数量']:>6.0f}  销售额:{row['销售额']:>12,.0f}  "
          f"[{row['category']}/{row['brand']}]")

# ---------------------------------------------------------------------------
# 5.2 Top 10 最高营收商品
# ---------------------------------------------------------------------------

print("\n  --- 5.2 Top 10 最高营收商品 ---")
product_revenue = order_items_full.groupby(['product_id', 'product_name', 'category', 'brand']).agg(
    销售额=('line_total', 'sum'),
    销售数量=('quantity', 'sum'),
    订单数=('order_id', 'nunique')
).round(2).sort_values('销售额', ascending=False).head(10).reset_index()

for i, row in product_revenue.iterrows():
    print(f"  {i+1:>2}. {row['product_name'][:30]:<32s} "
          f"营收:{row['销售额']:>12,.0f}  销量:{row['销售数量']:>6.0f}  "
          f"[{row['category']}/{row['brand']}]")

# ---------------------------------------------------------------------------
# 5.3 Top 10 城市（按订单数）
# ---------------------------------------------------------------------------

print("\n  --- 5.3 Top 10 城市 (按订单数) ---")
city_orders = valid_orders.groupby(['shipping_province', 'shipping_city']).agg(
    订单数=('order_id', 'count'),
    总消费=('actual_amount', 'sum'),
    平均消费=('actual_amount', 'mean'),
    用户数=('user_id', 'nunique')
).round(2).sort_values('订单数', ascending=False).head(10).reset_index()

for i, row in city_orders.iterrows():
    print(f"  {i+1:>2}. {row['shipping_province']}{row['shipping_city']:<10s}  "
          f"订单:{row['订单数']:>5.0f}  总消费:{row['总消费']:>14,.0f}  "
          f"用户:{row['用户数']:>5.0f}")

# ---------------------------------------------------------------------------
# 5.4 Top 10 品牌（按销售额）
# ---------------------------------------------------------------------------

print("\n  --- 5.4 Top 10 品牌 (按销售额) ---")
brand_sales = order_items_full.groupby('brand').agg(
    销售额=('line_total', 'sum'),
    销量=('quantity', 'sum'),
    商品数=('product_id', 'nunique')
).round(2).sort_values('销售额', ascending=False).head(10).reset_index()

for i, row in brand_sales.iterrows():
    print(f"  {i+1:>2}. {row['brand']:<20s}  "
          f"销售额:{row['销售额']:>12,.0f}  销量:{row['销量']:>6.0f}  "
          f"商品数:{row['商品数']:>4.0f}")

# ---------------------------------------------------------------------------
# 5.5 Top 10 用户（按累计消费）
# ---------------------------------------------------------------------------

print("\n  --- 5.5 Top 10 高价值用户 (按累计消费) ---")
top_users = users.nlargest(10, 'total_spent')[
    ['user_id', 'username', 'membership_level', 'province', 'city',
     'total_spent', 'total_orders', 'avg_order_value']
]
for i, row in top_users.iterrows():
    print(f"  {i+1:>2}. {row['username']:<16s}  "
          f"{row['membership_level']:<8s}  "
          f"累计消费:{row['total_spent']:>12,.0f}  "
          f"订单数:{row['total_orders']:>4.0f}  "
          f"[{row['province']}/{row['city']}]")

# =============================================================================
# 6. 统计摘要表
# =============================================================================

print("\n[6/8] 统计摘要表...")

# 整体业务概览（营收/客单价/复购统一使用有效订单口径）
total_revenue = valid_orders['actual_amount'].sum()
total_orders = len(valid_orders)
total_users = len(users)
total_products = len(products)
total_reviews_count = len(reviews)
avg_order_value = valid_orders['actual_amount'].mean()
avg_user_spend = users['total_spent'].mean()
repeat_rate = (users['total_orders'] > 1).sum() / total_users * 100

summary = pd.DataFrame({
    '指标': ['总营收(元)', '总订单数', '总用户数', '总商品数', '总评论数',
             '平均客单价(元)', '用户人均消费(元)', '复购率(%)',
             '订单含评论率(%)'],
    '数值': [
        f'{total_revenue:,.0f}',
        f'{total_orders:,}',
        f'{total_users:,}',
        f'{total_products:,}',
        f'{total_reviews_count:,}',
        f'{avg_order_value:,.2f}',
        f'{avg_user_spend:,.2f}',
        f'{repeat_rate:.1f}%',
        f'{total_reviews_count / total_orders * 100:.1f}%'
    ]
})

print("\n  === 电商业务核心指标概览 ===")
for _, row in summary.iterrows():
    print(f"  {row['指标']:<20s}: {row['数值']:>15s}")

# =============================================================================
# 7. 导出分析结果
# =============================================================================

print("\n[7/8] 导出分析结果...")

# 导出各类分析结果到 CSV
export_tasks = [
    ('age_group_distribution', age_group_dist.reset_index(name='用户数').rename(columns={'index': '年龄分组'}) if 'age_group_dist' in dir() else None),
    ('category_price_stats', category_price_stats.reset_index()),
    ('order_status_dist', status_dist.reset_index(name='订单数').rename(columns={'index': '状态'})),
    ('rating_dist', rating_dist.reset_index(name='评论数').rename(columns={'index': '评分'})),
    ('membership_spending', membership_spending.reset_index()),
    ('province_spending_top15', province_spending.reset_index()),
    ('category_sales', category_sales.reset_index()),
    ('monthly_revenue', monthly_revenue.reset_index()),
    ('top10_products_by_sales', product_sales),
    ('top10_products_by_revenue', product_revenue),
    ('top10_cities_by_orders', city_orders),
    ('top10_brands_by_sales', brand_sales),
    ('top10_users_by_spent', top_users),
    ('business_summary', summary),
]

exported_count = 0
for filename, df in export_tasks:
    if df is not None and not df.empty:
        filepath = os.path.join(EDA_OUTPUT_DIR, f'{filename}.csv')
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        exported_count += 1

print(f"  已导出 {exported_count} 个分析结果文件至 {EDA_OUTPUT_DIR}/")

# 同时导出一个综合性的 Excel 文件（如果安装了 openpyxl）
try:
    excel_path = os.path.join(EDA_OUTPUT_DIR, 'eda_summary_report.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for filename, df in export_tasks:
            if df is not None and not df.empty:
                # Excel sheet name 限制 31 个字符
                sheet_name = filename[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"  综合 Excel 报告已保存至: {excel_path}")
except Exception as e:
    print(f"  Excel 导出跳过 ({e})")

# =============================================================================
# 8. 关键发现总结
# =============================================================================

print("\n[8/8] ========== 关键发现总结 ==========")

findings = []

# 发现1：用户年龄集中度
median_age = users['age'].median()
findings.append(f"1. 用户画像: 用户年龄中位数为 {median_age:.0f} 岁，"
                f"主要集中在 {users['age'].quantile(0.25):.0f}-{users['age'].quantile(0.75):.0f} 岁区间")

# 发现2：最高营收品类
top_cat = category_sales.index[0]
top_cat_pct = category_sales.iloc[0]['销售额占比(%)']
findings.append(f"2. 品类表现: 最高营收品类为「{top_cat}」，"
                f"占总销售额 {top_cat_pct:.1f}%")

# 发现3：会员价值
if len(membership_spending) > 1:
    best_member = membership_spending['平均客单价'].idxmax()
    best_avg = membership_spending.loc[best_member, '平均客单价']
    worst_member = membership_spending['平均客单价'].idxmin()
    worst_avg = membership_spending.loc[worst_member, '平均客单价']
    ratio = best_avg / worst_avg if worst_avg > 0 else float('inf')
    findings.append(f"3. 会员价值差异: 「{best_member}」平均客单价({best_avg:,.0f})"
                    f"是「{worst_member}」({worst_avg:,.0f})的 {ratio:.1f} 倍")

# 发现4：评分分布
findings.append(f"4. 用户满意度: 商品平均评分 {avg_rating:.2f}/5.0，"
                f"好评率(4-5星) {(reviews['rating'] >= 4).sum() / len(reviews) * 100:.1f}%")

# 发现5：价格-评分关系
if 'price_rating_corr' in dir():
    pr = price_rating_corr.loc['price', 'rating_avg']
    direction = '正' if pr > 0 else '负'
    findings.append(f"5. 价格质量关系: 价格与评分的相关系数为 {pr:.4f}，"
                    f"呈微弱{direction}相关关系")

# 发现6：复购率
findings.append(f"6. 用户黏性: 复购率(>1单用户占比)为 {repeat_rate:.1f}%，"
                f"用户人均消费 {avg_user_spend:,.0f} 元")

# 发现7：时间趋势
if len(monthly_revenue) > 2:
    recent_trend = monthly_revenue.tail(3)
    trend_direction = '上升' if recent_trend['总营收'].is_monotonic_increasing else \
                      '下降' if recent_trend['总营收'].is_monotonic_decreasing else '波动'
    findings.append(f"7. 近期营收趋势: 最近3个月呈{trend_direction}态势，"
                    f"最近一月营收为 {recent_trend.iloc[-1]['总营收']:,.0f} 元")

# 发现8：品牌集中度
top3_brands = brand_sales.head(3)
top3_pct = top3_brands['销售额'].sum() / brand_sales['销售额'].sum() * 100
findings.append(f"8. 品牌集中度: Top 3 品牌贡献了 {top3_pct:.1f}% 的销售额，"
                f"品牌依赖程度{'高' if top3_pct > 50 else '中等' if top3_pct > 30 else '低'}")

# 发现9：星期效应
if 'day_of_week' in orders.columns:
    weekday_avg = valid_orders[valid_orders['day_of_week'].isin([0,1,2,3,4])]['actual_amount'].mean()
    weekend_avg = valid_orders[valid_orders['day_of_week'].isin([5,6])]['actual_amount'].mean()
    findings.append(f"9. 时间效应: 工作日平均客单价 {weekday_avg:,.0f} vs "
                    f"周末 {weekend_avg:,.0f}，"
                    f"周末{'更高' if weekend_avg > weekday_avg else '更低'}")

# 打印发现
for f in findings:
    print(f"  {f}")

print(f"\n{'='*70}")
print("探索性数据分析完成！结果已保存至 data/processed/eda_results/")
print(f"{'='*70}")

# 保存发现到文件
findings_path = os.path.join(EDA_OUTPUT_DIR, 'key_findings.txt')
with open(findings_path, 'w', encoding='utf-8') as f:
    f.write(f"电商数据探索性分析 —— 关键发现\n")
    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"{'='*60}\n\n")
    for finding in findings:
        f.write(finding + '\n')
print(f"\n关键发现已保存至: {findings_path}")
