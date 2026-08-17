#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
NovelMart 电商经营分析平台 —— 模块三：高级分析
NovelMart E-Commerce Business Analytics — Module 3: Advanced Analytics
=============================================================================

功能概述：
  1. 客户细分 —— RFM 分析与 K-means 聚类 / 百分位分段
  2. 商品关联分析 —— 购物篮分析（共现矩阵、Lift 提升度）
  3. 同期群分析 —— 按注册月份的用户留存矩阵
  4. 销售预测 —— 移动平均与简单指数平滑预测
  5. 流失分析 —— 90天无订单用户识别与会员等级流失率
  6. 价格-销量相关性分析 —— 价格与销量的分品类相关性
  7. 导出所有分析结果
  8. 打印综合发现报告

注：本脚本专注于数值分析与统计计算，不生成图表。

适用环境：Python 3.8+, pandas, numpy
作者：Cavsin
日期：2026-07
=============================================================================
"""

import os
import sys
import warnings
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from itertools import combinations

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
ADV_OUTPUT_DIR = os.path.join(PROCESSED_DIR, 'advanced_results')
os.makedirs(ADV_OUTPUT_DIR, exist_ok=True)

# 业务口径：有效订单 = 已付款且未取消/未退款
VALID_ORDER_STATUSES = ['已完成', '待发货', '已发货']

pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 240)
pd.set_option('display.float_format', lambda x: '%.4f' % x)

print("=" * 70)
print("NovelMart 电商经营分析 —— 高级分析模块")
print("=" * 70)

# =============================================================================
# 1. 加载数据
# =============================================================================

print("\n[1/7] 加载数据...")

def load_data(name):
    """优先加载清洗后 parquet，其次 csv，最后原始 csv"""
    for ext, reader in [('_cleaned.parquet', pd.read_parquet),
                         ('_cleaned.csv', pd.read_csv),
                         ('.csv', pd.read_csv)]:
        path = os.path.join(PROCESSED_DIR if 'cleaned' in ext else DATA_DIR,
                            f'{name}{ext}')
        if os.path.exists(path):
            print(f"  {name}: {path}")
            df = reader(path)
            # 统一处理日期列
            for col in df.columns:
                if 'date' in col.lower() and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass
            return df
    raise FileNotFoundError(f"Cannot find data for {name}")

users = load_data('users')
products = load_data('products')
orders = load_data('orders')
order_items = load_data('order_items')
reviews = load_data('reviews')

print(f"  加载完成: users={len(users):,}, products={len(products):,}, "
      f"orders={len(orders):,}, order_items={len(order_items):,}, "
      f"reviews={len(reviews):,}")

# 所有高级分析统一使用有效订单口径
valid_orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
valid_order_ids = set(valid_orders['order_id'])
valid_order_items = order_items[order_items['order_id'].isin(valid_order_ids)].copy()
print(f"  有效订单: {len(valid_orders):,} 条, 有效订单明细: {len(valid_order_items):,} 条")

# =============================================================================
# 2. 客户细分 —— RFM 分析
# =============================================================================

print("\n[2/7] 客户细分 —— RFM 分析...")

# ---------------------------------------------------------------------------
# 2.1 计算 RFM 指标
# ---------------------------------------------------------------------------

# 设定参考日期为有效订单中最后一天 + 1天（用于计算 Recency）
reference_date = valid_orders['order_date'].max() + timedelta(days=1)
print(f"  RFM 参考日期: {reference_date.date()}")

# 按用户聚合计算 RFM（仅有效订单，避免取消/退款/未支付订单污染消费频次与金额）
rfm = valid_orders.groupby('user_id').agg(
    # Recency: 最近一次购买距今多少天（越小越好）
    recency=('order_date', lambda x: (reference_date - x.max()).days),
    # Frequency: 购买频次（订单数）
    frequency=('order_id', 'count'),
    # Monetary: 总消费金额
    monetary=('actual_amount', 'sum')
).reset_index()

# 合并用户信息
rfm = rfm.merge(users[['user_id', 'membership_level', 'province', 'age', 'registration_date']],
                on='user_id', how='left')

print(f"  RFM 计算完成，覆盖 {len(rfm):,} 个用户")
print(f"  Recency:  min={rfm['recency'].min()}, max={rfm['recency'].max()}, "
      f"median={rfm['recency'].median():.0f}")
print(f"  Frequency: min={rfm['frequency'].min()}, max={rfm['frequency'].max()}, "
      f"median={rfm['frequency'].median():.0f}")
print(f"  Monetary:  min={rfm['monetary'].min():.0f}, max={rfm['monetary'].max():.0f}, "
      f"median={rfm['monetary'].median():.0f}")

# ---------------------------------------------------------------------------
# 2.2 百分位法 RFM 分段
# 注：本脚本采用百分位打分；sql/03_crud_queries.sql 的 RFM 采用规则阈值打分，
#     两套方法论结果不同，属有意设计（分别演示两种打分思路）。
# ---------------------------------------------------------------------------

# 对每个维度按四分位数打分：1=最差, 2, 3, 4=最好
# Recency：值越小越好 → 反转打分（天数少=分数高）
# 注意：先用 rank 消除并列值，避免 qcut 因分位边界重复而抛 "Bin edges must be unique"
rfm['R_score'] = pd.qcut(rfm['recency'].rank(method='first'), q=4, labels=[4, 3, 2, 1]).astype(int)
rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int)
rfm['M_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int)

# RFM 综合分数
rfm['RFM_score'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']

# ---------------------------------------------------------------------------
# 2.3 客户分层
# ---------------------------------------------------------------------------

def segment_customer(row):
    """
    基于 RFM 分数组合进行客户分层。
    参考分层策略：
    - 重要价值客户：R高 F高 M高
    - 重要发展客户：R高 F低 M高
    - 重要保持客户：R低 F高 M高
    - 重要挽留客户：R低 F低 M高
    - 一般价值客户：R高 F高 M低
    - 一般发展客户：R高 F低 M低
    - 一般保持客户：R低 F高 M低
    - 一般挽留客户：R低 F低 M低
    """
    r, f, m = row['R_score'], row['F_score'], row['M_score']
    if r >= 3 and f >= 3 and m >= 3:
        return '重要价值客户'
    elif r >= 3 and f < 3 and m >= 3:
        return '重要发展客户'
    elif r < 3 and f >= 3 and m >= 3:
        return '重要保持客户'
    elif r < 3 and f < 3 and m >= 3:
        return '重要挽留客户'
    elif r >= 3 and f >= 3 and m < 3:
        return '一般价值客户'
    elif r >= 3 and f < 3 and m < 3:
        return '一般发展客户'
    elif r < 3 and f >= 3 and m < 3:
        return '一般保持客户'
    else:
        return '一般挽留客户'

rfm['customer_segment'] = rfm.apply(segment_customer, axis=1)

# ---------------------------------------------------------------------------
# 2.4 各细分群体画像
# ---------------------------------------------------------------------------

print("\n  --- 客户细分群体画像 ---")
segment_profile = rfm.groupby('customer_segment').agg(
    用户数=('user_id', 'count'),
    用户占比=('user_id', lambda x: f'{len(x)/len(rfm)*100:.1f}%'),
    平均Recency天数=('recency', 'mean'),
    平均购买频次=('frequency', 'mean'),
    平均消费金额=('monetary', 'mean'),
    总消费金额=('monetary', 'sum'),
    平均年龄=('age', 'mean'),
).round(2)

# 按用户数降序排列
segment_order = ['重要价值客户', '重要发展客户', '重要保持客户', '重要挽留客户',
                 '一般价值客户', '一般发展客户', '一般保持客户', '一般挽留客户']
segment_profile = segment_profile.reindex(
    [s for s in segment_order if s in segment_profile.index])

print(segment_profile.to_string())

# 输出各细分群体的会员等级分布
print(f"\n  --- 各细分群体会员等级交叉分布 ---")
segment_membership = pd.crosstab(rfm['customer_segment'], rfm['membership_level'])
print(segment_membership.to_string())

# ---------------------------------------------------------------------------
# 2.5 尝试 K-means 聚类（如果 sklearn 可用）
# ---------------------------------------------------------------------------

print(f"\n  --- K-means 聚类 ---")
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    # 标准化 RFM 值
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm[['recency', 'frequency', 'monetary']])

    # 使用肘部法则确定最佳 K 值（简化版：固定 K=4）
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm['kmeans_cluster'] = kmeans.fit_predict(rfm_scaled)

    # 分析每个聚类的 RFM 均值
    cluster_analysis = rfm.groupby('kmeans_cluster').agg(
        用户数=('user_id', 'count'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        avg_monetary=('monetary', 'mean')
    ).round(2)
    cluster_analysis['用户占比(%)'] = (cluster_analysis['用户数'] /
                                  cluster_analysis['用户数'].sum() * 100).round(1)
    print(cluster_analysis.to_string())

    # 为聚类命名：按平均消费金额排序分配价值标签（保证标签唯一），
    # 长期未购买（recency 显著偏高）的簇单独标注为「流失风险群体」
    cluster_names = {}
    rank_names = ['高价值群体', '潜力发展群体', '一般消费群体', '低消费群体']
    monetary_order = cluster_analysis['avg_monetary'].sort_values(ascending=False).index
    for rank, c in enumerate(monetary_order):
        avg_r = cluster_analysis.loc[c, 'avg_recency']
        if avg_r > rfm['recency'].median() * 2:
            cluster_names[c] = '流失风险群体'
        else:
            cluster_names[c] = rank_names[min(rank, len(rank_names) - 1)]

    rfm['cluster_name'] = rfm['kmeans_cluster'].map(cluster_names)
    print(f"\n  聚类命名: {cluster_names}")

except ImportError:
    print("  sklearn 不可用，跳过 K-means 聚类（使用百分位分段结果）")
    rfm['kmeans_cluster'] = -1
    rfm['cluster_name'] = 'N/A'
except Exception as e:
    print(f"  K-means 聚类失败: {e}")
    rfm['kmeans_cluster'] = -1
    rfm['cluster_name'] = 'N/A'

# 保存 RFM 结果
rfm.to_csv(os.path.join(ADV_OUTPUT_DIR, 'rfm_segmentation.csv'),
           index=False, encoding='utf-8-sig')
print(f"\n  RFM 客户细分结果已保存 (rfm_segmentation.csv)")

# =============================================================================
# 3. 商品关联分析 —— 购物篮分析
# =============================================================================

print("\n[3/7] 商品关联分析 —— 购物篮分析...")

# ---------------------------------------------------------------------------
# 3.1 构建订单-商品共现矩阵
# ---------------------------------------------------------------------------

# 按子类别级别做关联分析（类目级别更有业务意义，也避免商品级别过于稀疏）
print("  以子类别级别进行关联分析...")

# 获取每个订单包含的子类别集合（仅有效订单）
order_subcategories = valid_order_items.merge(
    products[['product_id', 'subcategory']],
    on='product_id', how='inner'
)[['order_id', 'subcategory']].drop_duplicates()

# 构建交易篮字典
baskets = order_subcategories.groupby('order_id')['subcategory'].apply(set).to_dict()
print(f"  共 {len(baskets):,} 个有效订单购物篮")

# 只保留购买商品数 >= 2 的订单（单商品订单不产生关联）
multi_item_baskets = {k: v for k, v in baskets.items() if len(v) >= 2}
print(f"  其中 {len(multi_item_baskets):,} 个订单包含 >= 2 种子类别商品")

# 获取所有子类别列表
all_subcats = sorted(set().union(*baskets.values()))
subcat_to_idx = {s: i for i, s in enumerate(all_subcats)}
n_subcats = len(all_subcats)

# ---------------------------------------------------------------------------
# 3.2 计算共现频率与 Lift
# ---------------------------------------------------------------------------

# 统计单个子类别出现次数
item_count = Counter()
for basket in multi_item_baskets.values():
    for item in basket:
        item_count[item] += 1

# 统计子类别对共现次数
pair_count = Counter()
for basket in multi_item_baskets.values():
    items = sorted(basket)
    for a, b in combinations(items, 2):
        pair_count[(a, b)] += 1

total_baskets = len(multi_item_baskets)

# 计算 Lift
association_results = []
for (a, b), co_count in pair_count.most_common(200):  # Top 200 对
    support_ab = co_count / total_baskets
    support_a = item_count[a] / total_baskets
    support_b = item_count[b] / total_baskets

    if support_a > 0 and support_b > 0:
        lift = support_ab / (support_a * support_b)
    else:
        lift = 0

    confidence_a_to_b = co_count / item_count[a] if item_count[a] > 0 else 0
    confidence_b_to_a = co_count / item_count[b] if item_count[b] > 0 else 0

    association_results.append({
        '子类别A': a,
        '子类别B': b,
        '共现次数': co_count,
        '支持度(support)': round(support_ab, 6),
        '置信度(A→B)': round(confidence_a_to_b, 4),
        '置信度(B→A)': round(confidence_b_to_a, 4),
        '提升度(Lift)': round(lift, 4),
        'A单独频次': item_count[a],
        'B单独频次': item_count[b],
    })

association_df = pd.DataFrame(association_results)
association_df = association_df.sort_values('提升度(Lift)', ascending=False)

print(f"\n  --- Top 20 最强关联子类别对 (按 Lift) ---")
print(association_df.head(20)[['子类别A', '子类别B', '共现次数', '支持度(support)',
                                 '置信度(A→B)', '提升度(Lift)']].to_string(index=False))

# 统计 Lift 分布
print(f"\n  Lift 分布统计:")
print(f"    Lift > 5:  {(association_df['提升度(Lift)'] > 5).sum()} 对")
print(f"    Lift > 3:  {(association_df['提升度(Lift)'] > 3).sum()} 对")
print(f"    Lift > 1:  {(association_df['提升度(Lift)'] > 1).sum()} 对")
print(f"    Lift <= 1: {(association_df['提升度(Lift)'] <= 1).sum()} 对")
print(f"    平均 Lift: {association_df['提升度(Lift)'].mean():.4f}")

# ---------------------------------------------------------------------------
# 3.3 构建共现矩阵（用于查看关联热力数据）
# ---------------------------------------------------------------------------

print(f"\n  --- 构建 Top 20 子类别的共现矩阵 ---")
top_subcats = [s for s, _ in item_count.most_common(20)]
co_matrix = pd.DataFrame(0, index=top_subcats, columns=top_subcats)

for (a, b), cnt in pair_count.items():
    if a in top_subcats and b in top_subcats:
        co_matrix.loc[a, b] = cnt
        co_matrix.loc[b, a] = cnt

print(f"  共现矩阵尺寸: {co_matrix.shape}")
print(f"  总非零共现对数: {(co_matrix.values > 0).sum() - len(top_subcats)}")  # 减去对角线

# 保存关联分析结果
association_df.to_csv(os.path.join(ADV_OUTPUT_DIR, 'product_association.csv'),
                      index=False, encoding='utf-8-sig')
co_matrix.to_csv(os.path.join(ADV_OUTPUT_DIR, 'cooccurrence_matrix.csv'),
                 encoding='utf-8-sig')
print(f"  商品关联分析结果已保存")

# =============================================================================
# 4. 同期群分析 —— 用户留存
# =============================================================================

print("\n[4/7] 同期群分析 —— 用户留存...")

# ---------------------------------------------------------------------------
# 4.1 为每个用户分配注册同期群
# ---------------------------------------------------------------------------

# 用户注册年月
if 'registration_date' in users.columns:
    users['cohort_month'] = users['registration_date'].dt.to_period('M')
else:
    # 回退方案：用首单日期
    first_order = valid_orders.groupby('user_id')['order_date'].min().reset_index()
    first_order.columns = ['user_id', 'first_order_date']
    first_order['cohort_month'] = first_order['first_order_date'].dt.to_period('M')
    users = users.merge(first_order[['user_id', 'cohort_month']], on='user_id', how='left')

print(f"  用户同期群分布:")
cohort_sizes = users.groupby('cohort_month')['user_id'].nunique().sort_index()
for period, size in cohort_sizes.tail(10).items():
    print(f"    {period}: {size:>6,} 用户")

# ---------------------------------------------------------------------------
# 4.2 构建“注册后第 N 个月”留存矩阵
# ---------------------------------------------------------------------------

# 只使用有效订单与用户同期群关联
orders_with_cohort = valid_orders.merge(
    users[['user_id', 'cohort_month']],
    on='user_id', how='inner'
)

# 为订单添加订单月份和“相对注册月偏移”
orders_with_cohort['order_month'] = orders_with_cohort['order_date'].dt.to_period('M')
orders_with_cohort['period_offset'] = (
    orders_with_cohort['order_month'] - orders_with_cohort['cohort_month']
).apply(lambda x: x.n)
# 只保留注册当月及之后的订单
orders_with_cohort = orders_with_cohort[orders_with_cohort['period_offset'] >= 0]

# 展示最近 12 个注册月份（更符合业务阅读习惯）
recent_cohorts = cohort_sizes.tail(12).index
orders_with_cohort = orders_with_cohort[orders_with_cohort['cohort_month'].isin(recent_cohorts)]

# 计算每个同期群在“注册后第 N 个月”的活跃用户数
cohort_activity = orders_with_cohort.groupby(
    ['cohort_month', 'period_offset']
)['user_id'].nunique().unstack(fill_value=0)

# 构建留存率矩阵：活跃用户数 / 同期群注册用户总数 * 100
retention_matrix = cohort_activity.copy()
for cohort in retention_matrix.index:
    cohort_size = cohort_sizes.get(cohort, 1)
    if cohort_size > 0:
        retention_matrix.loc[cohort] = (retention_matrix.loc[cohort] / cohort_size * 100).round(2)

print(f"\n  --- 用户留存率矩阵 (%, 注册后第 N 月) ---")
print(retention_matrix.to_string())

# 计算各期平均留存率（跨同期群）
avg_retention_by_period = retention_matrix.mean(axis=0)
print(f"\n  --- 各时期平均留存率 ---")
for period, rate in avg_retention_by_period.head(12).items():
    print(f"    注册后第{period}月: {rate:.1f}%")

# 首月留存率 = 注册后第 1 个月（period_offset = 1）
if 1 in retention_matrix.columns:
    first_month_retention = retention_matrix[1].mean()
    print(f"\n  首月平均留存率: {first_month_retention:.1f}%")

# 保存留存矩阵
retention_matrix.to_csv(os.path.join(ADV_OUTPUT_DIR, 'cohort_retention_matrix.csv'),
                        encoding='utf-8-sig')
cohort_activity.to_csv(os.path.join(ADV_OUTPUT_DIR, 'cohort_activity_matrix.csv'),
                       encoding='utf-8-sig')
print(f"\n  同期群分析结果已保存")

# =============================================================================
# 5. 销售预测
# =============================================================================

print("\n[5/7] 销售预测...")

# ---------------------------------------------------------------------------
# 5.1 准备月度销售时间序列
# ---------------------------------------------------------------------------

# 统一使用 order_year_month（只统计有效订单）
if 'order_year_month' not in valid_orders.columns:
    valid_orders['order_year_month'] = valid_orders['order_date'].dt.strftime('%Y-%m')

monthly_sales = valid_orders.groupby('order_year_month').agg(
    营收=('actual_amount', 'sum'),
    订单数=('order_id', 'count')
).sort_index()
monthly_sales.index.name = '月份'

# 确保无缺失月份（填充为NaN以便后续处理）
# 对于离散的月份数据，直接使用现有数据

revenue_series = monthly_sales['营收']
n_months = len(revenue_series)

print(f"  月度数据点: {n_months} 个月")
print(f"  营收范围: {revenue_series.min():,.0f} ~ {revenue_series.max():,.0f}")
print(f"  最近3个月营收: {revenue_series.tail(3).to_dict()}")

# ---------------------------------------------------------------------------
# 5.2 移动平均与指数平滑（作为描述性指标）
# ---------------------------------------------------------------------------

def simple_moving_average(series, window=3):
    """计算简单移动平均"""
    return series.rolling(window=window, min_periods=1).mean()

def weighted_moving_average(series, window=3):
    """计算加权移动平均（越近权重越高）"""
    weights = np.arange(1, window + 1)
    return series.rolling(window=window, min_periods=1).apply(
        lambda x: np.dot(x, weights[:len(x)][-len(x):]) / weights[:len(x)].sum(),
        raw=True
    )

# 计算不同窗口的移动平均
revenue_sma3 = simple_moving_average(revenue_series, window=3)
revenue_sma6 = simple_moving_average(revenue_series, window=6)
revenue_wma3 = weighted_moving_average(revenue_series, window=3)

def simple_exponential_smoothing(series, alpha=0.3):
    """简单指数平滑"""
    result = [series.iloc[0]]
    for i in range(1, len(series)):
        result.append(alpha * series.iloc[i] + (1 - alpha) * result[-1])
    return pd.Series(result, index=series.index)

ses_forecast = simple_exponential_smoothing(revenue_series, alpha=0.3)

# ---------------------------------------------------------------------------
# 5.3 预测：使用最近 6 个月做线性趋势外推（保守基线，避免指数外推爆炸）
# ---------------------------------------------------------------------------

forecast_horizon = 3  # 预测未来3个月

def linear_forecast(series, horizon=3, window=6):
    """基于最近 window 个月做一元线性回归外推。数据不足时回退到最近 3 个月均值。"""
    train = series.tail(window)
    if len(train) < 3:
        baseline = series.tail(3).mean()
        return [baseline] * horizon
    x = np.arange(len(train))
    A = np.vstack([x, np.ones(len(x))]).T
    slope, intercept = np.linalg.lstsq(A, train.values, rcond=None)[0]
    if not np.isfinite(slope) or slope < 0:
        # 趋势为负或不可用时，使用最近值/均值，避免给出负营收预测
        baseline = series.tail(3).mean()
        return [baseline] * horizon
    # 外推时从训练集最后一个点的下一期开始
    last_x = len(train) - 1
    return [slope * (last_x + i) + intercept for i in range(1, horizon + 1)]

forecast_values = linear_forecast(revenue_series, horizon=forecast_horizon, window=6)
forecast_df = pd.DataFrame([{
    '预测月份': f'未来第{i}月',
    '预测营收': round(forecast_values[i-1], 2),
    '预测方法': '最近6个月线性趋势外推' if len(revenue_series) >= 6 else '最近3个月均值基线'
} for i in range(1, forecast_horizon + 1)])

print(f"\n  --- 销售预测 (未来{forecast_horizon}个月) ---")
print(f"  预测方法: 最近6个月线性趋势外推（保守基线，非指数外推）")
print(forecast_df.to_string(index=False))

# 回测：用前 N-3 个月训练线性模型，预测最后 3 个月
if n_months >= 9:
    train = revenue_series.iloc[:-3]
    test = revenue_series.iloc[-3:]
    pred = linear_forecast(train, horizon=3, window=min(6, len(train)))
    mape_lin = np.mean(np.abs((test.values - np.array(pred)) / test.values)) * 100
    mae_lin = np.mean(np.abs(test.values - np.array(pred)))
    print(f"\n  回测 MAE (线性基线): {mae_lin:,.0f}")
    print(f"  回测 MAPE (线性基线): {mape_lin:.1f}%")

# 保存预测结果
monthly_sales['SMA_3'] = revenue_sma3.round(2)
monthly_sales['SMA_6'] = revenue_sma6.round(2)
monthly_sales['WMA_3'] = revenue_wma3.round(2)
monthly_sales['SES_0.3'] = ses_forecast.round(2)
monthly_sales.to_csv(os.path.join(ADV_OUTPUT_DIR, 'sales_forecast_data.csv'),
                     encoding='utf-8-sig')
forecast_df.to_csv(os.path.join(ADV_OUTPUT_DIR, 'sales_forecast_prediction.csv'),
                   index=False, encoding='utf-8-sig')
print(f"  销售预测结果已保存")

# =============================================================================
# 6. 流失分析
# =============================================================================

print("\n[6/7] 流失分析...")

# ---------------------------------------------------------------------------
# 6.1 识别流失风险用户
# ---------------------------------------------------------------------------

# 定义流失：90天内无任何有效订单（已付款且未取消/未退款）
churn_threshold_days = 90
latest_order_date = valid_orders['order_date'].max()

# 计算每个用户的最后有效下单日期
user_last_order = valid_orders.groupby('user_id')['order_date'].max().reset_index()
user_last_order['days_since_last_order'] = (
    latest_order_date - user_last_order['order_date']
).dt.days

# 标记流失风险
user_last_order['is_at_risk'] = user_last_order['days_since_last_order'] > churn_threshold_days
user_last_order['is_churned'] = user_last_order['days_since_last_order'] > 180  # 180天视为已流失

# 合并用户信息
user_last_order = user_last_order.merge(
    users[['user_id', 'membership_level', 'province', 'registration_date',
           'total_orders', 'total_spent']],
    on='user_id', how='left'
)

at_risk_count = user_last_order['is_at_risk'].sum()
churned_count = user_last_order['is_churned'].sum()
active_count = len(user_last_order) - at_risk_count

print(f"  总用户数(有订单): {len(user_last_order):,}")
print(f"  活跃用户 (<= {churn_threshold_days}天): {active_count:,} ({active_count/len(user_last_order)*100:.1f}%)")
print(f"  流失风险 (>{churn_threshold_days}天): {at_risk_count:,} ({at_risk_count/len(user_last_order)*100:.1f}%)")
print(f"  已流失 (>{180}天): {churned_count:,} ({churned_count/len(user_last_order)*100:.1f}%)")

# 重新计算：总用户中从未下有效订单的
users_with_orders = set(valid_orders['user_id'].unique())
all_user_ids = set(users['user_id'])
never_ordered = all_user_ids - users_with_orders
print(f"  从未下单用户: {len(never_ordered):,} ({len(never_ordered)/len(all_user_ids)*100:.1f}%)")

# ---------------------------------------------------------------------------
# 6.2 按会员等级分析流失率
# ---------------------------------------------------------------------------

membership_churn = user_last_order.groupby('membership_level').agg(
    用户数=('user_id', 'count'),
    流失风险数=('is_at_risk', 'sum'),
    已流失数=('is_churned', 'sum'),
    平均最后下单天数=('days_since_last_order', 'mean'),
    中位最后下单天数=('days_since_last_order', 'median'),
    平均累计消费=('total_spent', 'mean')
).round(2)

membership_churn['流失风险率(%)'] = (membership_churn['流失风险数'] /
                              membership_churn['用户数'] * 100).round(1)
membership_churn['已流失率(%)'] = (membership_churn['已流失数'] /
                             membership_churn['用户数'] * 100).round(1)

print(f"\n  --- 各会员等级流失分析 ---")
print(membership_churn.to_string())

# ---------------------------------------------------------------------------
# 6.3 流失风险用户特征分析
# ---------------------------------------------------------------------------

at_risk_users = user_last_order[user_last_order['is_at_risk']]
print(f"\n  --- 流失风险用户特征 ---")
print(f"  平均累计消费: {at_risk_users['total_spent'].mean():,.0f} (vs 整体均值: {user_last_order['total_spent'].mean():,.0f})")
print(f"  平均历史订单数: {at_risk_users['total_orders'].mean():.1f} (vs 整体均值: {user_last_order['total_orders'].mean():.1f})")
print(f"  平均未购买天数: {at_risk_users['days_since_last_order'].mean():.0f}")

# 按省份的流失风险
province_churn = at_risk_users.groupby('province').size().sort_values(ascending=False).head(10)
province_total = user_last_order.groupby('province').size()
province_churn_rate = (province_churn / province_total * 100).round(1).sort_values(ascending=False).head(10)
print(f"\n  Top 10 流失风险省份:")
for province, rate in province_churn_rate.items():
    print(f"    {province}: {rate}% ({province_churn.get(province, 0)}/{province_total.get(province, 0)})")

# 保存流失分析结果
user_last_order.to_csv(os.path.join(ADV_OUTPUT_DIR, 'churn_analysis_users.csv'),
                       index=False, encoding='utf-8-sig')
membership_churn.to_csv(os.path.join(ADV_OUTPUT_DIR, 'churn_by_membership.csv'),
                        encoding='utf-8-sig')
print(f"\n  流失分析结果已保存")

# =============================================================================
# 7. 价格-销量相关性分析
# =============================================================================

print("\n[7/7] 价格-销量相关性分析（辅助定价参考）...")

# ---------------------------------------------------------------------------
# 7.1 按品类的价格-销量关系
# ---------------------------------------------------------------------------

# 计算每个商品的总销量和均价
# line_total 仅在执行过 01_data_cleaning.py 后存在；缺失时（回退到原始数据）按相同公式现场计算
if 'line_total' not in order_items.columns:
    order_items['line_total'] = (order_items['quantity'] * order_items['unit_price'] *
                                 (1 - order_items['discount'].fillna(0))).round(2)

# price_tier 仅在执行过 01_data_cleaning.py 后存在；缺失时回退到原始数据，跳过价格层级分析
prod_cols = ['product_id', 'category', 'subcategory', 'price']
has_price_tier = 'price_tier' in products.columns
if has_price_tier:
    prod_cols.append('price_tier')

product_performance = valid_order_items.merge(
    products[prod_cols],
    on='product_id', how='inner'
)

agg_dict = {
    '总销量': ('quantity', 'sum'),
    '平均成交单价': ('unit_price', 'mean'),
    '标价': ('price', 'first'),
    '订单数': ('order_id', 'nunique'),
    '营收': ('line_total', 'sum'),
}
if has_price_tier:
    agg_dict['价格层级'] = ('price_tier', 'first')

category_elasticity = product_performance.groupby(['category', 'product_id']).agg(
    **agg_dict
).reset_index()

# ---------------------------------------------------------------------------
# 7.2 各品类的价格-销量相关系数
# ---------------------------------------------------------------------------

print(f"\n  --- 各品类价格-销量相关系数 ---")
elasticity_results = []
for cat in category_elasticity['category'].unique():
    cat_data = category_elasticity[category_elasticity['category'] == cat]
    if len(cat_data) >= 10:  # 至少10个商品
        # Pearson 相关系数
        pearson_corr = cat_data['标价'].corr(cat_data['总销量'])
        # Spearman 秩相关系数（对非线性关系更稳健）
        spearman_corr = cat_data['标价'].corr(cat_data['总销量'], method='spearman')

        # 简单线性回归：销量 ~ 价格
        x = cat_data['标价'].values
        y = cat_data['总销量'].values
        avg_price = cat_data['标价'].mean()
        avg_quantity = cat_data['总销量'].mean()
        if len(x) >= 2 and np.std(x) > 0:
            # numpy 最小二乘拟合
            A = np.vstack([x, np.ones(len(x))]).T
            slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]

            # 在均价处计算弹性 (弹性 = (dQ/dP) * (P/Q))
            point_elasticity = slope * (avg_price / avg_quantity) if avg_quantity > 0 else np.nan
        else:
            slope, intercept, point_elasticity = np.nan, np.nan, np.nan

        elasticity_results.append({
            '品类': cat,
            '商品数': len(cat_data),
            '平均价格': round(avg_price, 2),
            '平均销量': round(avg_quantity, 1),
            'Pearson_r': round(pearson_corr, 4),
            'Spearman_rho': round(spearman_corr, 4),
            '价格系数(斜率)': round(slope, 6),
            '截距': round(intercept, 2),
            '点弹性(均值处)': round(point_elasticity, 4) if not np.isnan(point_elasticity) else 'N/A',
        })

elasticity_df = pd.DataFrame(elasticity_results)
elasticity_df = elasticity_df.sort_values('Pearson_r')
print(elasticity_df.to_string(index=False))

# 解读弹性
print(f"\n  --- 价格-销量相关性解读 ---")
for _, row in elasticity_df.iterrows():
    pearson = row['Pearson_r']
    if pearson < -0.3:
        interpretation = '价格与销量负相关较强（降价可能带来更高销量，需实验验证）'
    elif pearson < -0.1:
        interpretation = '价格与销量呈弱负相关（价格对销量有一定影响）'
    elif pearson < 0.1:
        interpretation = '价格与销量相关性不显著（价格与销量无明显关系）'
    else:
        interpretation = '价格与销量呈正相关（高价反而高销量，可能为品质信号或数据噪声）'
    print(f"  {row['品类']:<10s}: r={pearson:+.4f} — {interpretation}")

# ---------------------------------------------------------------------------
# 7.3 按价格层级的销量分析
# ---------------------------------------------------------------------------

if has_price_tier and '价格层级' in category_elasticity.columns:
    price_tier_sales = category_elasticity.groupby('价格层级').agg(
        商品数=('product_id', 'nunique'),
        总销量=('总销量', 'sum'),
        平均单品销量=('总销量', 'mean'),
        总营收=('营收', 'sum'),
        平均单价=('标价', 'mean')
    ).round(2)

    print(f"\n  --- 各价格层级销量表现 ---")
    print(price_tier_sales.to_string())

    price_tier_sales.to_csv(os.path.join(ADV_OUTPUT_DIR, 'price_tier_performance.csv'),
                            encoding='utf-8-sig')
else:
    print(f"\n  --- 各价格层级销量表现 (跳过: 未执行清洗，无 price_tier 列) ---")

# 保存价格-销量相关性结果（文件名保持兼容，但含义是相关性分析）
elasticity_df.to_csv(os.path.join(ADV_OUTPUT_DIR, 'price_elasticity.csv'),
                     index=False, encoding='utf-8-sig')
print(f"\n  价格-销量相关性分析结果已保存")

# =============================================================================
# 8. 综合发现报告
# =============================================================================

print("\n" + "=" * 70)
print("高级分析综合发现报告")
print("=" * 70)

report = []

# --- RFM 发现 ---
segment_counts = rfm['customer_segment'].value_counts()
vip_count = segment_counts.get('重要价值客户', 0) + segment_counts.get('重要发展客户', 0) + \
            segment_counts.get('重要保持客户', 0)
report.append("=" * 60)
report.append("一、客户细分（RFM分析）")
report.append("=" * 60)
report.append(f"  1. 高价值用户群体（重要价值+重要发展+重要保持）共 {vip_count:,} 人，"
              f"占活跃用户 {vip_count/len(rfm)*100:.1f}%")
report.append(f"  2. 需要挽留的用户（重要挽留+一般挽留）共 "
              f"{segment_counts.get('重要挽留客户', 0) + segment_counts.get('一般挽留客户', 0):,} 人")

# 找到价值最高的群体
seg_avg = rfm.groupby('customer_segment')['monetary'].mean()
best_seg = seg_avg.idxmax()
report.append(f"  3. 人均消费最高的细分群体为「{best_seg}」，"
              f"人均消费 {seg_avg.max():,.0f} 元")
report.append(f"  4. 建议：对「重要发展客户」加强促销引导、对「重要挽留客户」发放专属优惠券")

# --- 关联分析发现 ---
report.append(f"\n{'='*60}")
report.append("二、商品关联分析")
report.append("=" * 60)
if len(association_df) > 0:
    top_pair = association_df.iloc[0]
    # 注意：不要使用 ↔ 等非 GBK 字符，Windows 控制台(GBK)下 print 会抛 UnicodeEncodeError
    report.append(f"  1. 最强关联子类别对：「{top_pair['子类别A']}」与「{top_pair['子类别B']}」"
                  f"(Lift={top_pair['提升度(Lift)']:.2f})")
    report.append(f"  2. 共发现 {(association_df['提升度(Lift)'] > 1).sum()} 对有效关联（Lift > 1）")

    # 当前模拟数据中 Lift 普遍接近 1，说明不存在强关联，只作方法演示，不直接推荐捆绑
    strong_pairs = association_df[association_df['提升度(Lift)'] > 3].head(5)
    if len(strong_pairs) > 0:
        report.append(f"  3. 推荐捆绑销售组合（Lift>3）：")
        for _, pair in strong_pairs.iterrows():
            report.append(f"     - {pair['子类别A']} + {pair['子类别B']} "
                          f"(共现{pair['共现次数']}次, Lift={pair['提升度(Lift)']:.2f})")
    else:
        report.append(f"  3. 当前数据中未发现 Lift>3 的强关联组合，"
                      f"关联规则仅作为方法演示，不建议直接用于捆绑销售。")
report.append(f"  4. 建议：后续可引入更细粒度商品/真实行为数据后再评估推荐模块价值")

# --- 同期群发现 ---
report.append(f"\n{'='*60}")
report.append("三、同期群分析")
report.append("=" * 60)
if 1 in retention_matrix.columns:
    first_mon_ret = retention_matrix[1].mean()
    report.append(f"  1. 注册后首月平均留存率: {first_mon_ret:.1f}%")
    # 计算留存率衰减
    if 3 in retention_matrix.columns:
        third_mon_ret = retention_matrix[3].mean()
        decay = (1 - third_mon_ret / first_mon_ret) * 100 if first_mon_ret > 0 else 0
        report.append(f"  2. 注册后第3月平均留存率: {third_mon_ret:.1f}%，"
                      f"较首月衰减 {decay:.1f}%")
report.append(f"  3. 建议：优化新用户首单体验（新人专享价、首单免邮），提升早期留存")

# --- 销售预测发现 ---
report.append(f"\n{'='*60}")
report.append("四、销售预测")
report.append("=" * 60)
report.append(f"  1. 预计未来3个月营收（线性趋势基线）：")
for _, row in forecast_df.iterrows():
    report.append(f"     - {row['预测月份']}: {row['预测营收']:,.0f} 元")
if n_months >= 9 and 'mape_lin' in dir():
    report.append(f"  2. 模型回测 MAPE: {mape_lin:.1f}%（线性基线）")
report.append(f"  3. 建议：结合节假日和促销季节调整预测值")

# --- 流失分析发现 ---
report.append(f"\n{'='*60}")
report.append("五、流失分析")
report.append("=" * 60)
report.append(f"  1. 当前有 {at_risk_count:,} 名用户存在流失风险（>{churn_threshold_days}天未购买），"
              f"占有下单用户 {at_risk_count/len(user_last_order)*100:.1f}%")
report.append(f"  2. 已流失用户（>180天）: {churned_count:,} 人 ({churned_count/len(user_last_order)*100:.1f}%)")
if len(membership_churn) > 0:
    highest_churn = membership_churn['流失风险率(%)'].idxmax()
    highest_churn_rate = membership_churn.loc[highest_churn, '流失风险率(%)']
    report.append(f"  3. 流失风险最高的会员等级: {highest_churn} ({highest_churn_rate}%)")
report.append(f"  4. 建议：对90天未购买用户推送「回归优惠券」，对180天用户发送「我们想念你」EDM")

# --- 价格-销量相关性发现 ---
report.append(f"\n{'='*60}")
report.append("六、价格-销量相关性分析")
report.append("=" * 60)
if len(elasticity_df) > 0:
    most_elastic = elasticity_df.loc[elasticity_df['Pearson_r'].idxmin()]
    report.append(f"  1. 价格-销量负相关最强的品类: {most_elastic['品类']} "
                  f"(r={most_elastic['Pearson_r']:.4f})，价格越高销量越低")
    least_elastic = elasticity_df.loc[elasticity_df['Pearson_r'].idxmax()]
    report.append(f"  2. 价格-销量相关性最弱的品类: {least_elastic['品类']} "
                  f"(r={least_elastic['Pearson_r']:.4f})，价格对销量解释力有限")
report.append(f"  3. 注意：这是截面相关性而非因果价格弹性，"
              f"定价决策需结合实验（A/B测试）进一步验证。")

report.append(f"\n{'='*60}")
report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"分析结果文件位置: {ADV_OUTPUT_DIR}")
report.append(f"{'='*60}")

# 打印报告
for line in report:
    print(line)

# 保存报告到文件
report_path = os.path.join(ADV_OUTPUT_DIR, 'advanced_analysis_report.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
print(f"\n综合发现报告已保存至: {report_path}")

# 汇总所有输出文件
print(f"\n{'='*70}")
print(f"高级分析完成！输出文件列表:")
for f in sorted(os.listdir(ADV_OUTPUT_DIR)):
    fpath = os.path.join(ADV_OUTPUT_DIR, f)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"  {f} ({size_kb:,.1f} KB)")
print(f"{'='*70}")
