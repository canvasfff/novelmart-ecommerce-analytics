#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Olist 电商经营分析平台 —— 模块四：数据可视化
Olist E-Commerce Business Analytics — Module 4: Visualization
=============================================================================

功能概述：
  生成 12 张分析图表 + Tableau 数据导出 CSV。
  图表涵盖：销售趋势、品类、支付、评分、商品/卖家排行、
  客户分群、订单状态、配送时效、价格评分关系、周内下单规律。

适用环境：Python 3.8+, pandas, numpy, matplotlib, scipy
=============================================================================
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

import common

common.configure_console()
common.ensure_dirs()

from scipy.stats import gaussian_kde

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

VALID_ORDER_STATUSES = common.VALID_ORDER_STATUSES
CHART_DIR = common.CHART_DIR

# ── 配色 ──────────────────────────────────────────────────────────────────────
CAT_PALETTE = [
    '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4',
    '#008300', '#4a3aa7', '#e34948',
]
SURFACE = '#fcfcfb'
GRIDLINE = '#e1e0d9'
BASELINE = '#c3c2b7'
TEXT_PRIMARY = '#0b0b0b'
TEXT_SECONDARY = '#52514e'

plt.rcParams.update({
    'figure.facecolor': SURFACE,
    'axes.facecolor': SURFACE,
    'axes.edgecolor': BASELINE,
    'axes.linewidth': 0.8,
    'axes.labelcolor': TEXT_PRIMARY,
    'text.color': TEXT_PRIMARY,
    'xtick.color': TEXT_SECONDARY,
    'ytick.color': TEXT_SECONDARY,
    'grid.color': GRIDLINE,
    'grid.linewidth': 0.5,
    'grid.alpha': 1.0,
    'legend.edgecolor': BASELINE,
    'legend.framealpha': 0.95,
    'legend.fontsize': 9,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})


def load_data():
    """加载清洗后数据。"""
    print('Loading processed Olist data...')
    dfs = {
        'customers_agg': common.load_processed('customers_agg'),
        'products': common.load_processed('products'),
        'orders': common.load_processed('orders'),
        'order_items': common.load_processed('order_items'),
        'payments': common.load_processed('payments'),
        'reviews': common.load_processed('reviews'),
        'geolocation_zip': common.load_processed('geolocation_zip'),
    }
    for name in ['orders']:
        dfs[name] = common.to_datetime_columns(dfs[name], [
            'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
            'order_delivered_customer_date', 'order_estimated_delivery_date',
        ])
    dfs['reviews'] = common.to_datetime_columns(dfs['reviews'], ['review_creation_date', 'review_answer_timestamp'])
    return dfs


_chart_counter = 0


def save_chart(fig, name):
    global _chart_counter
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor=SURFACE, edgecolor='none')
    plt.close(fig)
    _chart_counter += 1
    print(f'  [{_chart_counter}/12] Saved: {name}')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 1: Monthly Revenue Trend
# ═══════════════════════════════════════════════════════════════════════════════

def chart_monthly_revenue(orders):
    df = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
    df['month'] = df['order_purchase_timestamp'].dt.to_period('M')
    monthly = df.groupby('month')['payment_value'].sum().reset_index()
    monthly['month_str'] = monthly['month'].astype(str)
    monthly = monthly.sort_values('month')

    csv_out = monthly[['month_str', 'payment_value']].copy()
    csv_out.columns = ['月份', '支付金额']
    csv_out.to_csv(os.path.join(CHART_DIR, 'monthly_revenue.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(12, 5))
    x = range(len(monthly))
    y = monthly['payment_value'].values / 1e5  # 十万 BRL
    ax.plot(x, y, color=CAT_PALETTE[0], linewidth=2, marker='o', markersize=5,
            markerfacecolor=CAT_PALETTE[0], markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    ax.fill_between(x, 0, y, color=CAT_PALETTE[0], alpha=0.08)
    ax.set_xticks(x)
    ax.set_xticklabels(monthly['month_str'].values, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('营收金额（十万 BRL）')
    ax.set_title('Olist 月度营收趋势')
    ax.grid(axis='y')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}'))
    ax.set_xlim(-0.5, len(x) - 0.5)
    fig.tight_layout()
    save_chart(fig, 'chart1_monthly_revenue.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 2: Category Sales Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_category_sales(order_items, products, orders):
    valid_order_ids = set(orders.loc[orders['order_status'].isin(VALID_ORDER_STATUSES), 'order_id'])
    items = order_items[order_items['order_id'].isin(valid_order_ids)]
    merged = items.merge(products[['product_id', 'product_category_name_english']], on='product_id', how='left')
    merged['sale_amount'] = merged['price'] + merged['freight_value']
    cat_sales = merged.groupby('product_category_name_english')['sale_amount'].sum().sort_values(ascending=True)

    csv_out = cat_sales.reset_index()
    csv_out.columns = ['品类', '销售额']
    csv_out.to_csv(os.path.join(CHART_DIR, 'category_sales.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(10, 8))
    y_pos = range(len(cat_sales))
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(cat_sales))]
    ax.barh(y_pos, cat_sales.values / 1e5, color=colors, edgecolor=SURFACE)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(cat_sales.index, fontsize=8)
    ax.set_xlabel('销售额（十万 BRL）')
    ax.set_title('各品类销售额分布')
    ax.grid(axis='x')
    fig.tight_layout()
    save_chart(fig, 'chart2_category_sales.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 3: Payment Method Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_payment_method(payments):
    pay_counts = payments['payment_type'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        pay_counts.values, labels=None, autopct='%.1f%%', startangle=90,
        colors=CAT_PALETTE, pctdistance=0.75, wedgeprops=dict(width=0.4, edgecolor=SURFACE)
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_color('white')
    ax.legend(wedges, [f'{k} ({v:,})' for k, v in pay_counts.items()],
              loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
    ax.set_title('支付方式分布')
    fig.tight_layout()
    save_chart(fig, 'chart3_payment_method.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 4: Review Score Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_rating_distribution(reviews):
    counts = reviews['review_score'].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(counts.index.astype(str), counts.values, color=CAT_PALETTE, edgecolor=SURFACE)
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1000, f'{v:,}', ha='center', fontsize=9, color=TEXT_SECONDARY)
    ax.set_xlabel('评分')
    ax.set_ylabel('评论数')
    ax.set_title('评论评分分布')
    ax.grid(axis='y')
    fig.tight_layout()
    save_chart(fig, 'chart4_rating_distribution.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 5: Top Products by Revenue
# ═══════════════════════════════════════════════════════════════════════════════

def chart_top_products(order_items, products, orders):
    valid_order_ids = set(orders.loc[orders['order_status'].isin(VALID_ORDER_STATUSES), 'order_id'])
    items = order_items[order_items['order_id'].isin(valid_order_ids)]
    merged = items.merge(products[['product_id', 'product_category_name_english']], on='product_id', how='left')
    merged['revenue'] = merged['price'] + merged['freight_value']
    top = merged.groupby(['product_id', 'product_category_name_english']).agg(
        销量=('order_item_id', 'count'), 销售额=('revenue', 'sum')
    ).nlargest(10, '销售额').reset_index()
    top['label'] = top['product_id'].str[:12] + '...'

    csv_out = top.copy()
    csv_out.to_csv(os.path.join(CHART_DIR, 'top_products.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top['label'][::-1], top['销售额'][::-1] / 1e4, color=CAT_PALETTE[0], edgecolor=SURFACE)
    ax.set_xlabel('销售额（万 BRL）')
    ax.set_title('Top10 商品销售额')
    ax.grid(axis='x')
    fig.tight_layout()
    save_chart(fig, 'chart5_top_products.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 6: Customer State Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_state_customers(customers_agg):
    state_counts = customers_agg['customer_state'].value_counts().head(15).sort_values()
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(state_counts.index, state_counts.values, color=CAT_PALETTE[1], edgecolor=SURFACE)
    ax.set_xlabel('客户数')
    ax.set_title('Top15 州客户分布')
    ax.grid(axis='x')
    fig.tight_layout()
    save_chart(fig, 'chart6_state_customers.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 7: RFM Segment Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_rfm_segments(rfm_path):
    rfm = pd.read_csv(rfm_path, encoding='utf-8-sig')
    seg_counts = rfm['customer_segment'].value_counts().reindex([
        '重要价值客户', '重要发展客户', '重要保持客户', '重要挽留客户',
        '一般价值客户', '一般发展客户', '一般保持客户', '一般挽留客户'
    ])
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(seg_counts))]
    bars = ax.bar(seg_counts.index, seg_counts.values, color=colors, edgecolor=SURFACE)
    for bar, v in zip(bars, seg_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 500, f'{v:,}', ha='center', fontsize=8)
    ax.set_xticks(range(len(seg_counts)))
    ax.set_xticklabels(seg_counts.index, rotation=30, ha='right', fontsize=8)
    ax.set_ylabel('客户数')
    ax.set_title('RFM 客户分群分布')
    ax.grid(axis='y')
    fig.tight_layout()
    save_chart(fig, 'chart7_rfm_segments.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 8: Order Status Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_order_status(orders):
    status_counts = orders['order_status'].value_counts()
    labels = [common.ORDER_STATUS_CN.get(s, s) for s in status_counts.index]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, status_counts.values, color=CAT_PALETTE, edgecolor=SURFACE)
    for bar, v in zip(bars, status_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 500, f'{v:,}', ha='center', fontsize=8)
    ax.set_ylabel('订单数')
    ax.set_title('订单状态分布')
    ax.grid(axis='y')
    fig.tight_layout()
    save_chart(fig, 'chart8_order_status.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 9: Delivery Days Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_delivery_days(orders):
    days = orders.loc[orders['delivery_days'].notna(), 'delivery_days']
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(days, bins=50, color=CAT_PALETTE[2], alpha=0.75, edgecolor=SURFACE)
    ax.axvline(days.mean(), color=CAT_PALETTE[7], linestyle='--', linewidth=1.5, label=f'均值: {days.mean():.1f} 天')
    ax.set_xlabel('送达时长（天）')
    ax.set_ylabel('订单数')
    ax.set_title('配送时效分布')
    ax.legend()
    ax.grid(axis='y')
    fig.tight_layout()
    save_chart(fig, 'chart9_delivery_days.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 10: Price vs Review Score
# ═══════════════════════════════════════════════════════════════════════════════

def chart_price_rating_scatter(products):
    df = products.dropna(subset=['avg_price', 'avg_review_score']).copy()
    df = df[df['quantity_sold'] > 0]
    df_sample = df.sample(min(3000, len(df)), random_state=42) if len(df) > 3000 else df

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, cat in enumerate(df_sample['product_category_name_english'].value_counts().head(8).index):
        sub = df_sample[df_sample['product_category_name_english'] == cat]
        ax.scatter(sub['avg_price'], sub['avg_review_score'], s=sub['quantity_sold'] / 10 + 3,
                   alpha=0.6, label=cat, color=CAT_PALETTE[i % len(CAT_PALETTE)], edgecolors='white', linewidths=0.3)
    ax.set_xlabel('商品平均售价（BRL）')
    ax.set_ylabel('平均评论评分')
    ax.set_title('商品价格 vs 评论评分')
    ax.legend(fontsize=7, loc='upper right', framealpha=0.9)
    ax.grid(True)
    fig.tight_layout()
    save_chart(fig, 'chart10_price_rating_scatter.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 11: Weekly Order Pattern
# ═══════════════════════════════════════════════════════════════════════════════

def chart_weekly_pattern(orders):
    valid = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
    valid['weekday'] = valid['order_purchase_timestamp'].dt.dayofweek
    wd_counts = valid['weekday'].value_counts().sort_index()
    labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(labels, wd_counts.values, color=CAT_PALETTE[4], marker='o', linewidth=2)
    for i, v in enumerate(wd_counts.values):
        ax.text(i, v + 300, f'{v:,}', ha='center', fontsize=8, color=TEXT_SECONDARY)
    ax.set_ylabel('订单数')
    ax.set_title('周内下单规律')
    ax.grid(axis='y')
    fig.tight_layout()
    save_chart(fig, 'chart11_weekly_pattern.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 12: Top Sellers by Revenue
# ═══════════════════════════════════════════════════════════════════════════════

def chart_top_sellers(order_items, orders):
    valid_order_ids = set(orders.loc[orders['order_status'].isin(VALID_ORDER_STATUSES), 'order_id'])
    items = order_items[order_items['order_id'].isin(valid_order_ids)]
    seller_rev = items.groupby('seller_id').agg(
        订单数=('order_id', 'nunique'), 销售额=('price', 'sum'), 运费=('freight_value', 'sum')
    ).reset_index()
    seller_rev['总销售额'] = seller_rev['销售额'] + seller_rev['运费']
    top = seller_rev.nlargest(10, '总销售额').sort_values('总销售额')
    top['label'] = top['seller_id'].str[:12] + '...'

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top['label'], top['总销售额'] / 1e4, color=CAT_PALETTE[3], edgecolor=SURFACE)
    ax.set_xlabel('销售额（万 BRL）')
    ax.set_title('Top10 卖家销售额')
    ax.grid(axis='x')
    fig.tight_layout()
    save_chart(fig, 'chart12_top_sellers.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Export province/state sales CSV for Tableau
# ═══════════════════════════════════════════════════════════════════════════════

def export_state_sales(orders):
    valid = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)]
    state_sales = valid.groupby('customer_state').agg(
        订单数=('order_id', 'count'),
        总营收=('payment_value', 'sum'),
        平均客单价=('payment_value', 'mean'),
    ).reset_index().sort_values('总营收', ascending=False)
    state_sales.columns = ['州', '订单数', '总营收', '平均客单价']
    state_sales.to_csv(os.path.join(CHART_DIR, 'state_sales.csv'), index=False, encoding='utf-8-sig')
    print('  Exported: state_sales.csv')


def main():
    print('=' * 70)
    print('Olist 电商经营分析 —— 数据可视化')
    print('=' * 70)
    dfs = load_data()

    chart_monthly_revenue(dfs['orders'])
    chart_category_sales(dfs['order_items'], dfs['products'], dfs['orders'])
    chart_payment_method(dfs['payments'])
    chart_rating_distribution(dfs['reviews'])
    chart_top_products(dfs['order_items'], dfs['products'], dfs['orders'])
    chart_state_customers(dfs['customers_agg'])
    chart_rfm_segments(os.path.join(common.ADV_DIR, 'rfm_customers.csv'))
    chart_order_status(dfs['orders'])
    chart_delivery_days(dfs['orders'])
    chart_price_rating_scatter(dfs['products'])
    chart_weekly_pattern(dfs['orders'])
    chart_top_sellers(dfs['order_items'], dfs['orders'])
    export_state_sales(dfs['orders'])
    print('\n可视化完成 ✅')


if __name__ == '__main__':
    main()
