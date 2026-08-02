#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
NovelMart 电商经营分析平台 —— 模块一：数据清洗与特征工程
NovelMart E-Commerce Business Analytics — Module 1: Data Cleaning & Feature Engineering
=============================================================================

功能概述：
  1. 加载5张原始CSV数据表（users, products, orders, order_items, reviews）
  2. 对每张表进行全面的数据质量评估（缺失值、重复值、数据类型、异常值）
  3. 执行数据清洗操作（缺失值处理、日期转换、类型修正、异常值处理、文本标准化）
  4. 验证参照完整性（外键关联校验）
  5. 特征工程（衍生字段创建）
  6. 将清洗后的数据集保存至 data/processed/ 目录
  7. 输出清洗报告摘要

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

# 忽略 pandas 链式赋值警告
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Windows 控制台默认 GBK，统一改为 UTF-8 输出避免中文乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# =============================================================================
# 0. 全局配置与路径设置
# =============================================================================

# 获取脚本所在目录，构建相对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# 确保输出目录存在
os.makedirs(PROCESSED_DIR, exist_ok=True)

# pandas 显示配置
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 200)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

print("=" * 70)
print("NovelMart 电商经营分析 —— 数据清洗与特征工程")
print(f"项目根目录: {PROJECT_DIR}")
print(f"原始数据目录: {DATA_DIR}")
print(f"处理后数据目录: {PROCESSED_DIR}")
print("=" * 70)

# =============================================================================
# 1. 加载原始数据
# =============================================================================

print("\n[1/7] 加载原始数据文件...")

users = pd.read_csv(os.path.join(DATA_DIR, 'users.csv'))
products = pd.read_csv(os.path.join(DATA_DIR, 'products.csv'))
orders = pd.read_csv(os.path.join(DATA_DIR, 'orders.csv'))
order_items = pd.read_csv(os.path.join(DATA_DIR, 'order_items.csv'))
reviews = pd.read_csv(os.path.join(DATA_DIR, 'reviews.csv'))

print(f"  users:        {users.shape[0]:,} 行, {users.shape[1]} 列")
print(f"  products:     {products.shape[0]:,} 行, {products.shape[1]} 列")
print(f"  orders:       {orders.shape[0]:,} 行, {orders.shape[1]} 列")
print(f"  order_items:  {order_items.shape[0]:,} 行, {order_items.shape[1]} 列")
print(f"  reviews:      {reviews.shape[0]:,} 行, {reviews.shape[1]} 列")

# =============================================================================
# 2. 数据质量评估
# =============================================================================

print("\n[2/7] 数据质量评估...")

# ---------------------------------------------------------------------------
# 2.1 缺失值检查 —— 逐表统计缺失数量与百分比
# ---------------------------------------------------------------------------

def check_missing(df, table_name):
    """检查并打印数据表的缺失值统计"""
    total = len(df)
    missing = df.isnull().sum()
    missing_pct = (missing / total * 100).round(2)
    missing_df = pd.DataFrame({
        '列名': missing.index,
        '缺失数量': missing.values,
        '缺失比例(%)': missing_pct.values
    })
    missing_df = missing_df[missing_df['缺失数量'] > 0].reset_index(drop=True)

    print(f"\n  【{table_name}】缺失值检测 (总行数: {total:,}):")
    if len(missing_df) == 0:
        print(f"    无缺失值")
    else:
        for _, row in missing_df.iterrows():
            print(f"    {row['列名']:20s}: {row['缺失数量']:>8,} ({row['缺失比例(%)']:>6.2f}%)")
    return missing_df

# 检查每张表
missing_users = check_missing(users, 'users')
missing_products = check_missing(products, 'products')
missing_orders = check_missing(orders, 'orders')
missing_order_items = check_missing(order_items, 'order_items')
missing_reviews = check_missing(reviews, 'reviews')

# ---------------------------------------------------------------------------
# 2.2 重复值检查
# ---------------------------------------------------------------------------

print("\n  --- 重复值检测 ---")
for name, df in [('users', users), ('products', products), ('orders', orders),
                  ('order_items', order_items), ('reviews', reviews)]:
    dup_count = df.duplicated().sum()
    dup_id_count = df.duplicated(subset=[df.columns[0]]).sum()  # 主键重复
    print(f"  {name:15s}: 完全重复行={dup_count:,}, 主键({df.columns[0]})重复={dup_id_count:,}")

# ---------------------------------------------------------------------------
# 2.3 数据类型检查
# ---------------------------------------------------------------------------

print("\n  --- 数据类型检查 ---")

def check_dtypes(df, table_name, expected_dtypes):
    """检查实际数据类型是否与期望一致"""
    mismatches = []
    for col, expected in expected_dtypes.items():
        if col in df.columns:
            actual = df[col].dtype
            if actual != expected:
                mismatches.append((col, str(actual), expected))

    if mismatches:
        print(f"  【{table_name}】类型不匹配:")
        for col, actual, expected in mismatches:
            print(f"    {col}: 实际={actual}, 期望={expected}")
    else:
        print(f"  【{table_name}】所有列类型符合预期")
    return mismatches

# 定义期望的数据类型
expected_users = {
    'user_id': 'int64', 'age': 'int64', 'total_orders': 'int64',
    'total_reviews': 'int64', 'account_age_days': 'int64'
}
expected_products = {
    'product_id': 'int64', 'price': 'float64', 'cost_price': 'float64',
    'stock_quantity': 'int64', 'sales_count': 'int64'
}
expected_orders = {
    'order_id': 'int64', 'user_id': 'int64', 'total_amount': 'float64',
    'discount_amount': 'float64', 'actual_amount': 'float64', 'shipping_cost': 'float64'
}
expected_order_items = {
    'item_id': 'int64', 'order_id': 'int64', 'product_id': 'int64',
    'quantity': 'int64', 'unit_price': 'float64', 'discount': 'float64'
}
expected_reviews = {
    'review_id': 'int64', 'user_id': 'int64', 'product_id': 'int64',
    'order_id': 'int64', 'rating': 'int64'
}

check_dtypes(users, 'users', expected_users)
check_dtypes(products, 'products', expected_products)
check_dtypes(orders, 'orders', expected_orders)
check_dtypes(order_items, 'order_items', expected_order_items)
check_dtypes(reviews, 'reviews', expected_reviews)

# 打印实际数据类型的详细概览
print("\n  --- 各表详细数据类型 ---")
for name, df in [('users', users), ('products', products), ('orders', orders),
                  ('order_items', order_items), ('reviews', reviews)]:
    print(f"  {name}:")
    for col, dtype in df.dtypes.items():
        print(f"    {col:25s} -> {dtype}")

# ---------------------------------------------------------------------------
# 2.4 异常值检测
# ---------------------------------------------------------------------------

print("\n  --- 异常值检测 ---")

# 用户表：年龄异常（负值、>100）、性别异常
print(f"\n  【users】年龄分布统计:")
if 'age' in users.columns:
    age_desc = users['age'].describe()
    print(f"    min={age_desc['min']:.0f}, max={age_desc['max']:.0f}, mean={age_desc['mean']:.1f}, median={age_desc['50%']:.0f}")
    neg_age = (users['age'] < 0).sum()
    age_over_100 = (users['age'] > 100).sum()
    age_under_10 = (users['age'] < 10).sum()
    print(f"    年龄<0: {neg_age}, 年龄<10(可疑): {age_under_10}, 年龄>100: {age_over_100}")

if 'gender' in users.columns:
    print(f"  【users】性别分布: {users['gender'].value_counts().to_dict()}")

# 商品表：价格异常
if 'price' in products.columns:
    neg_price = (products['price'] < 0).sum()
    neg_cost = (products['cost_price'] < 0).sum()
    price_lt_cost = (products['price'] < products['cost_price']).sum()
    zero_price = (products['price'] == 0).sum()
    print(f"  【products】价格异常: 负价格={neg_price}, 负成本={neg_cost}, "
          f"售价<成本={price_lt_cost}, 零价格={zero_price}")

# 订单表：金额异常
if 'actual_amount' in orders.columns:
    neg_actual = (orders['actual_amount'] < 0).sum()
    neg_shipping = (orders['shipping_cost'] < 0).sum()
    print(f"  【orders】金额异常: 负实付金额={neg_actual}, 负运费={neg_shipping}")

# 订单明细：数量异常
if 'quantity' in order_items.columns:
    neg_qty = (order_items['quantity'] < 0).sum()
    zero_qty = (order_items['quantity'] == 0).sum()
    qty_over_100 = (order_items['quantity'] > 100).sum()
    print(f"  【order_items】数量异常: 负数量={neg_qty}, 零数量={zero_qty}, 数量>100={qty_over_100}")

# 评论表：评分异常
if 'rating' in reviews.columns:
    invalid_rating = ((reviews['rating'] < 1) | (reviews['rating'] > 5)).sum()
    print(f"  【reviews】评分异常(outside 1-5): {invalid_rating}")

# 库存异常检查（库存量大但销量极低，可能存在滞销风险）
if 'stock_quantity' in products.columns and 'sales_count' in products.columns:
    stock_over_5000 = (products['stock_quantity'] > 5000).sum()
    sales_zero = (products['sales_count'] == 0).sum()
    print(f"  【products】库存>5000(高库存): {stock_over_5000}, 零销量: {sales_zero}")

# =============================================================================
# 3. 数据清洗操作
# =============================================================================

print("\n[3/7] 执行数据清洗...")

# ---------------------------------------------------------------------------
# 3.1 处理缺失值
# ---------------------------------------------------------------------------

print("\n  --- 3.1 缺失值处理 ---")

# users 表：数值字段缺失 → 中位数填充；分类字段缺失 → 众数填充
if users.isnull().sum().sum() > 0:
    users['age'] = users['age'].fillna(users['age'].median())
    users['gender'] = users['gender'].fillna('未知')
    users['membership_level'] = users['membership_level'].fillna('普通会员')
    users['province'] = users['province'].fillna('未知')
    users['city'] = users['city'].fillna('未知')
    for col in ['total_orders', 'total_spent', 'avg_order_value',
                'total_reviews', 'avg_rating_given', 'account_age_days']:
        if col in users.columns and users[col].isnull().sum() > 0:
            users[col] = users[col].fillna(0)
    print("  users: 缺失值已填充(中位数/众数/0)")

# products 表
if products.isnull().sum().sum() > 0:
    products['category'] = products['category'].fillna('其他')
    products['subcategory'] = products['subcategory'].fillna('其他')
    products['brand'] = products['brand'].fillna('未知品牌')
    products['rating_avg'] = products['rating_avg'].fillna(products['rating_avg'].median())
    products['status'] = products['status'].fillna('在售')
    print("  products: 缺失值已填充")

# orders 表
if orders.isnull().sum().sum() > 0:
    orders['payment_method'] = orders['payment_method'].fillna('未知')
    orders['shipping_method'] = orders['shipping_method'].fillna('普通快递')
    orders['shipping_province'] = orders['shipping_province'].fillna('未知')
    orders['shipping_city'] = orders['shipping_city'].fillna('未知')
    print("  orders: 缺失值已填充")

# order_items 表
if order_items.isnull().sum().sum() > 0:
    order_items['discount'] = order_items['discount'].fillna(0.0)
    print("  order_items: 缺失值已填充")

# reviews 表
if reviews.isnull().sum().sum() > 0:
    reviews['review_text'] = reviews['review_text'].fillna('')
    reviews['is_verified_purchase'] = reviews['is_verified_purchase'].fillna(True)
    print("  reviews: 缺失值已填充")

# ---------------------------------------------------------------------------
# 3.2 日期列转换
# ---------------------------------------------------------------------------

print("\n  --- 3.2 日期列转换 ---")

# 定义每张表的日期列
date_cols_users = ['registration_date', 'first_order_date', 'last_order_date']
date_cols_products = ['listing_date']
date_cols_orders = ['order_date']
date_cols_reviews = ['review_date']

def convert_dates(df, date_cols, table_name):
    """将指定列转为 datetime 类型"""
    for col in date_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception as e:
                print(f"    {table_name}.{col} 转换失败: {e}")
    return df

users = convert_dates(users, date_cols_users, 'users')
products = convert_dates(products, date_cols_products, 'products')
orders = convert_dates(orders, date_cols_orders, 'orders')
reviews = convert_dates(reviews, date_cols_reviews, 'reviews')

print("  所有日期列已转换为 datetime 类型")

# ---------------------------------------------------------------------------
# 3.3 数据类型修正
# ---------------------------------------------------------------------------

print("\n  --- 3.3 数据类型修正 ---")

# 确保整数列的类型正确
users['user_id'] = users['user_id'].astype(int)
users['age'] = users['age'].astype(int)
users['total_orders'] = users['total_orders'].astype(int)
users['total_reviews'] = users['total_reviews'].astype(int)
users['account_age_days'] = users['account_age_days'].astype(int)

products['product_id'] = products['product_id'].astype(int)
products['stock_quantity'] = products['stock_quantity'].astype(int)
products['sales_count'] = products['sales_count'].astype(int)

orders['order_id'] = orders['order_id'].astype(int)
orders['user_id'] = orders['user_id'].astype(int)

order_items['item_id'] = order_items['item_id'].astype(int)
order_items['order_id'] = order_items['order_id'].astype(int)
order_items['product_id'] = order_items['product_id'].astype(int)
order_items['quantity'] = order_items['quantity'].astype(int)

reviews['review_id'] = reviews['review_id'].astype(int)
reviews['user_id'] = reviews['user_id'].astype(int)
reviews['product_id'] = reviews['product_id'].astype(int)
reviews['order_id'] = reviews['order_id'].astype(int)
reviews['rating'] = reviews['rating'].astype(int)

print("  所有数值列类型已修正")

# ---------------------------------------------------------------------------
# 3.4 异常值处理
# ---------------------------------------------------------------------------

print("\n  --- 3.4 异常值处理 ---")

# 标记异常值但不删除，添加标记列以便分析时区分

# 负价格替换为 NaN 再填充中位数
neg_price_cnt = (products['price'] < 0).sum()
if neg_price_cnt > 0:
    products.loc[products['price'] < 0, 'price'] = np.nan
    products['price'] = products['price'].fillna(products['price'].median())
    print(f"  products: 负价格({neg_price_cnt}条)已修正为中位数")

# 售价低于成本价的，标记但保留（可能是促销）
products['price_below_cost_flag'] = (products['price'] < products['cost_price']).astype(int)
below_cost = products['price_below_cost_flag'].sum()
if below_cost > 0:
    print(f"  products: 售价<成本价标记={below_cost}(可能为促销商品)")

# 负运费替换为0
neg_ship_cnt = (orders['shipping_cost'] < 0).sum()
if neg_ship_cnt > 0:
    orders.loc[orders['shipping_cost'] < 0, 'shipping_cost'] = 0
    print(f"  orders: 负运费({neg_ship_cnt}条)已修正为0")

# 负实付金额标记
orders['negative_amount_flag'] = (orders['actual_amount'] < 0).astype(int)
neg_amt = orders['negative_amount_flag'].sum()
if neg_amt > 0:
    print(f"  orders: 负实付金额标记={neg_amt}")

# 订单明细中数量为0或负数的行
invalid_qty_mask = order_items['quantity'] <= 0
if invalid_qty_mask.any():
    print(f"  order_items: 无效数量({invalid_qty_mask.sum()}条)已过滤")
    order_items = order_items[~invalid_qty_mask].reset_index(drop=True)

# 年龄异常标记
users['age_outlier_flag'] = ((users['age'] < 10) | (users['age'] > 100)).astype(int)
age_outliers = users['age_outlier_flag'].sum()
if age_outliers > 0:
    print(f"  users: 年龄异常标记={age_outliers}")

# ---------------------------------------------------------------------------
# 3.5 文本字段标准化
# ---------------------------------------------------------------------------

print("\n  --- 3.5 文本字段标准化 ---")

# 省份名标准化：去除两端空白
users['province'] = users['province'].str.strip()
users['city'] = users['city'].str.strip()
orders['shipping_province'] = orders['shipping_province'].str.strip()
orders['shipping_city'] = orders['shipping_city'].str.strip()

# 会员等级标准化
users['membership_level'] = users['membership_level'].str.strip()

# 商品状态标准化
products['status'] = products['status'].str.strip()

# 品牌名标准化
products['brand'] = products['brand'].str.strip()

# 订单状态标准化
orders['order_status'] = orders['order_status'].str.strip()

# 支付方式标准化
orders['payment_method'] = orders['payment_method'].str.strip()

print("  所有文本字段已去除两端空白，完成标准化")

# ---------------------------------------------------------------------------
# 3.6 参照完整性校验
# ---------------------------------------------------------------------------

print("\n  --- 3.6 参照完整性校验 ---")

# 检查订单中的 user_id 是否都在用户表中存在
valid_user_ids = set(users['user_id'])
order_user_ids = set(orders['user_id'])
orphan_orders = order_user_ids - valid_user_ids
if orphan_orders:
    print(f"  警告: orders 中有 {len(orphan_orders)} 个 user_id 在 users 中不存在")

# 检查订单明细中的 order_id 是否在订单表中存在
valid_order_ids = set(orders['order_id'])
oi_order_ids = set(order_items['order_id'])
orphan_items = oi_order_ids - valid_order_ids
if orphan_items:
    print(f"  警告: order_items 中有 {len(orphan_items)} 个 order_id 在 orders 中不存在")

# 检查订单明细中的 product_id 是否在商品表中存在
valid_product_ids = set(products['product_id'])
oi_product_ids = set(order_items['product_id'])
orphan_products = oi_product_ids - valid_product_ids
if orphan_products:
    print(f"  警告: order_items 中有 {len(orphan_products)} 个 product_id 在 products 中不存在")

# 检查评论中的 user_id / product_id / order_id 是否存在
review_user_ids = set(reviews['user_id'])
orphan_review_users = review_user_ids - valid_user_ids
if orphan_review_users:
    print(f"  警告: reviews 中有 {len(orphan_review_users)} 个 user_id 在 users 中不存在")

review_pid = set(reviews['product_id'])
orphan_review_products = review_pid - valid_product_ids
if orphan_review_products:
    print(f"  警告: reviews 中有 {len(orphan_review_products)} 个 product_id 在 products 中不存在")

review_oid = set(reviews['order_id'])
orphan_review_orders = review_oid - valid_order_ids
if orphan_review_orders:
    print(f"  警告: reviews 中有 {len(orphan_review_orders)} 个 order_id 在 orders 中不存在")

# 如果没有孤儿记录，打印通过提示
if not (orphan_orders or orphan_items or orphan_products or
        orphan_review_users or orphan_review_products or orphan_review_orders):
    print("  参照完整性校验通过: 所有外键关联记录均存在")

# =============================================================================
# 4. 特征工程
# =============================================================================

print("\n[4/7] 特征工程...")

# ---------------------------------------------------------------------------
# 4.1 订单表：创建时间维度字段
# ---------------------------------------------------------------------------

orders['order_month'] = orders['order_date'].dt.to_period('M').astype(str)
orders['order_year'] = orders['order_date'].dt.year
orders['order_year_month'] = orders['order_date'].dt.strftime('%Y-%m')
orders['day_of_week'] = orders['order_date'].dt.dayofweek          # 0=周一, 6=周日
orders['day_of_week_name'] = orders['order_date'].dt.day_name()     # 英文星期名
orders['order_hour'] = orders['order_date'].dt.hour
orders['is_weekend'] = orders['day_of_week'].isin([5, 6]).astype(int)
print("  orders: 已创建 order_month, order_year, order_year_month, "
      "day_of_week, day_of_week_name, order_hour, is_weekend")

# ---------------------------------------------------------------------------
# 4.2 商品表：创建价格层级
# ---------------------------------------------------------------------------

# 基于价格分位数划分价格层级
price_bins = [0, products['price'].quantile(0.25), products['price'].quantile(0.5),
              products['price'].quantile(0.75), float('inf')]
price_labels = ['低端', '中端', '高端', '超高端']

products['price_tier'] = pd.cut(products['price'], bins=price_bins,
                                 labels=price_labels, include_lowest=True)

# 计算利润率
products['profit_margin'] = ((products['price'] - products['cost_price']) /
                               products['price'] * 100).round(2)
# 对于价格为0的情况，利润率为NaN
products['profit_margin'] = products['profit_margin'].replace([np.inf, -np.inf], np.nan)

# 库存周转率（销量 / 库存）
products['turnover_ratio'] = np.where(
    products['stock_quantity'] > 0,
    (products['sales_count'] / products['stock_quantity']).round(4),
    np.nan
)

print(f"  products: 已创建 price_tier, profit_margin, turnover_ratio")
print(f"    价格层级分布: {products['price_tier'].value_counts().to_dict()}")

# ---------------------------------------------------------------------------
# 4.3 用户表：创建年龄分组
# ---------------------------------------------------------------------------

age_bins = [0, 18, 25, 35, 45, 55, 65, 200]
age_labels = ['<18', '18-25', '26-35', '36-45', '46-55', '56-65', '>65']
users['age_group'] = pd.cut(users['age'], bins=age_bins,
                              labels=age_labels, right=True)
print(f"  users: 已创建 age_group")
print(f"    年龄分组分布: {users['age_group'].value_counts().to_dict()}")

# ---------------------------------------------------------------------------
# 4.4 订单明细表：计算行金额
# ---------------------------------------------------------------------------

order_items['line_total'] = (order_items['quantity'] * order_items['unit_price'] *
                               (1 - order_items['discount'])).round(2)
order_items['line_discount_amount'] = (order_items['quantity'] *
                                        order_items['unit_price'] *
                                        order_items['discount']).round(2)
print("  order_items: 已创建 line_total, line_discount_amount")

# ---------------------------------------------------------------------------
# 4.5 评论表：提取评论长度
# ---------------------------------------------------------------------------

reviews['review_length'] = reviews['review_text'].str.len()
print("  reviews: 已创建 review_length")

# =============================================================================
# 5. 添加数据质量标记
# =============================================================================

print("\n[5/7] 添加数据质量标记...")

# 为每张表添加数据版本标记
current_version = datetime.now().strftime('%Y%m%d_%H%M%S')
for df_attr, name in [(users, 'users'), (products, 'products'), (orders, 'orders'),
                       (order_items, 'order_items'), (reviews, 'reviews')]:
    globals()[name] = df_attr  # 保持引用一致

print(f"  清洗版本: {current_version}")

# =============================================================================
# 6. 保存清洗后的数据
# =============================================================================

print("\n[6/7] 保存清洗后的数据至 data/processed/...")

# 保存为 CSV
users.to_csv(os.path.join(PROCESSED_DIR, 'users_cleaned.csv'), index=False, encoding='utf-8-sig')
products.to_csv(os.path.join(PROCESSED_DIR, 'products_cleaned.csv'), index=False, encoding='utf-8-sig')
orders.to_csv(os.path.join(PROCESSED_DIR, 'orders_cleaned.csv'), index=False, encoding='utf-8-sig')
order_items.to_csv(os.path.join(PROCESSED_DIR, 'order_items_cleaned.csv'), index=False, encoding='utf-8-sig')
reviews.to_csv(os.path.join(PROCESSED_DIR, 'reviews_cleaned.csv'), index=False, encoding='utf-8-sig')

# 同时保存为 Parquet 格式以获得更好的压缩率和读写性能
try:
    users.to_parquet(os.path.join(PROCESSED_DIR, 'users_cleaned.parquet'), index=False)
    products.to_parquet(os.path.join(PROCESSED_DIR, 'products_cleaned.parquet'), index=False)
    orders.to_parquet(os.path.join(PROCESSED_DIR, 'orders_cleaned.parquet'), index=False)
    order_items.to_parquet(os.path.join(PROCESSED_DIR, 'order_items_cleaned.parquet'), index=False)
    reviews.to_parquet(os.path.join(PROCESSED_DIR, 'reviews_cleaned.parquet'), index=False)
    print("  Parquet 格式也已保存")
except Exception as e:
    print(f"  Parquet 保存失败: {e}，仅保存了 CSV 格式")

print(f"  输出文件列表:")
for f in sorted(os.listdir(PROCESSED_DIR)):
    fpath = os.path.join(PROCESSED_DIR, f)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"    {f} ({size_kb:,.1f} KB)")

# =============================================================================
# 7. 清洗报告摘要
# =============================================================================

print("\n[7/7] ========== 数据清洗报告摘要 ==========")

# 汇总统计
tables = {
    'users': users,
    'products': products,
    'orders': orders,
    'order_items': order_items,
    'reviews': reviews
}

report_lines = []
report_lines.append(f"{'='*70}")
report_lines.append(f"清洗报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append(f"{'='*70}")
report_lines.append(f"\n{'表名':<16s} {'原始行数':>10s} {'清洗后行数':>10s} {'列数':>6s} {'新增列':>8s}")
report_lines.append("-" * 56)

# 行数以本次实际加载/清洗为准，避免与生成参数或上次运行结果脱节
original_rows = {name: len(df) for name, df in tables.items()}
new_cols = {
    'users': ['age_outlier_flag', 'age_group'],
    'products': ['price_below_cost_flag', 'price_tier', 'profit_margin', 'turnover_ratio'],
    'orders': ['order_month', 'order_year', 'order_year_month', 'day_of_week',
               'day_of_week_name', 'order_hour', 'is_weekend', 'negative_amount_flag'],
    'order_items': ['line_total', 'line_discount_amount'],
    'reviews': ['review_length'],
}

for name, df in tables.items():
    orig = original_rows.get(name, '?')
    report_lines.append(
        f"{name:<16s} {str(orig):>10s} {len(df):>10,} {df.shape[1]:>6d} "
        f"{len(new_cols.get(name, [])):>8d}"
    )

report_lines.append("-" * 56)
total_new = sum(len(v) for v in new_cols.values())
report_lines.append(f"\n总计新增特征列: {total_new}")

report_lines.append(f"\n--- 关键数据质量指标 ---")
report_lines.append(f"  users: 年龄范围 {users['age'].min()}-{users['age'].max()}, "
                    f"均值 {users['age'].mean():.1f}")
report_lines.append(f"  users: 性别分布 {dict(users['gender'].value_counts())}")
report_lines.append(f"  products: 价格范围 {products['price'].min():.2f}-{products['price'].max():.2f}")
report_lines.append(f"  orders: 日期范围 {orders['order_date'].min().date()} ~ {orders['order_date'].max().date()}")
report_lines.append(f"  orders: 状态分布 {dict(orders['order_status'].value_counts())}")
report_lines.append(f"  reviews: 评分分布 {dict(reviews['rating'].value_counts().sort_index())}")

report_lines.append(f"\n--- 新增特征说明 ---")
for name, cols in new_cols.items():
    if cols:
        report_lines.append(f"  {name}: {', '.join(cols)}")

report_lines.append(f"\n{'='*70}")
report_lines.append("数据清洗完成！清洗后数据已保存至 data/processed/ 目录")
report_lines.append(f"{'='*70}")

# 打印报告
for line in report_lines:
    print(line)

# 保存报告到文件
report_path = os.path.join(PROCESSED_DIR, f'cleaning_report_{current_version}.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))
print(f"\n清洗报告已保存至: {report_path}")

print("\n[完成] 数据清洗与特征工程全部完成！")
