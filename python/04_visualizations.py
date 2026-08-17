#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NovelMart E-Commerce Business Analytics — Visualization Script
Generates 12 high-quality charts and analytical data exports.
All paths are relative to this script's location.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd

# Windows 控制台默认 GBK，统一改为 UTF-8 输出避免中文乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Matplotlib setup: non-interactive backend + Chinese font support ──────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
from scipy.stats import gaussian_kde

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# ── Paths (relative to this script) ───────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
CHART_DIR = os.path.join(PROJECT_DIR, 'charts')
os.makedirs(CHART_DIR, exist_ok=True)

# 业务口径：有效订单 = 已付款且未取消/未退款
VALID_ORDER_STATUSES = ['已完成', '待发货', '已发货']

# ── Color palette (dataviz-validated categorical palette, light mode) ─────────
CAT_PALETTE = [
    '#2a78d6',  # slot 1 — blue
    '#eb6834',  # slot 2 — orange
    '#1baf7a',  # slot 3 — aqua
    '#eda100',  # slot 4 — yellow
    '#e87ba4',  # slot 5 — magenta
    '#008300',  # slot 6 — green
    '#4a3aa7',  # slot 7 — violet
    '#e34948',  # slot 8 — red
]

# Sequential blue ramp (light→dark)
BLUE_RAMP = [
    '#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef',
    '#6da7ec', '#5598e7', '#3987e5', '#2a78d6',
    '#256abf', '#1c5cab', '#184f95', '#104281',
]

# Chart chrome
SURFACE = '#fcfcfb'
GRIDLINE = '#e1e0d9'
BASELINE = '#c3c2b7'
TEXT_PRIMARY = '#0b0b0b'
TEXT_SECONDARY = '#52514e'
TEXT_MUTED = '#898781'

# Global style
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


# ═══════════════════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_data():
    """Load all CSV files and return a dict of DataFrames.
    优先加载清洗后数据 (data/processed/)，缺失时回退到原始数据，
    与 02/03 脚本的加载策略保持一致。"""
    print('Loading data files...')
    dfs = {}

    date_cols = {'orders': ['order_date'], 'reviews': ['review_date']}
    for name in ['users', 'products', 'orders', 'order_items', 'reviews']:
        cleaned_path = os.path.join(PROCESSED_DIR, f'{name}_cleaned.csv')
        raw_path = os.path.join(DATA_DIR, f'{name}.csv')
        path = cleaned_path if os.path.exists(cleaned_path) else raw_path
        kwargs = {'encoding': 'utf-8-sig'}
        if name in date_cols:
            kwargs['parse_dates'] = date_cols[name]
        dfs[name] = pd.read_csv(path, **kwargs)
        src = 'cleaned' if path == cleaned_path else 'raw'
        print(f'  {name}: {len(dfs[name]):,} rows ({src})')
    return dfs


# ═══════════════════════════════════════════════════════════════════════════════
# Chart Helper
# ═══════════════════════════════════════════════════════════════════════════════

_chart_counter = 0


def save_chart(fig, name):
    """Save figure to charts/ directory and close."""
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor=SURFACE, edgecolor='none')
    plt.close(fig)
    global _chart_counter
    _chart_counter += 1
    print(f'  [{_chart_counter}/12] Saved: {name}')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 1: Monthly Revenue Trend
# ═══════════════════════════════════════════════════════════════════════════════

def chart_monthly_revenue(orders):
    """Line chart of actual_amount summed by month (only valid orders)."""
    df = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
    df['month'] = df['order_date'].dt.to_period('M')
    monthly = df.groupby('month')['actual_amount'].sum().reset_index()
    monthly['month_str'] = monthly['month'].astype(str)
    monthly = monthly.sort_values('month')

    # Export CSV
    csv_out = monthly[['month_str', 'actual_amount']].copy()
    csv_out.columns = ['月份', '实付金额']
    csv_out.to_csv(os.path.join(CHART_DIR, 'monthly_revenue.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(12, 5))
    x = range(len(monthly))
    y = monthly['actual_amount'].values / 1e6  # millions

    ax.plot(x, y, color=CAT_PALETTE[0], linewidth=2, marker='o',
            markersize=6, markerfacecolor=CAT_PALETTE[0],
            markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    ax.fill_between(x, 0, y, color=CAT_PALETTE[0], alpha=0.08)

    ax.set_xticks(x)
    ax.set_xticklabels(monthly['month_str'].values, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('营收金额（百万元）')
    ax.set_title('月度营收趋势')
    ax.grid(axis='y', color=GRIDLINE, linewidth=0.5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))
    ax.set_xlim(-0.5, len(x) - 0.5)

    # Label first and last points
    for idx in [0, -1]:
        ax.annotate(f'{y[idx]:.2f}M',
                    xy=(x[idx], y[idx]),
                    xytext=(0, 10 if idx == -1 else -14),
                    textcoords='offset points',
                    fontsize=8, color=TEXT_SECONDARY, ha='center')

    fig.tight_layout()
    save_chart(fig, 'chart1_monthly_revenue.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 2: Category Sales Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def chart_category_sales(order_items, products, orders):
    """Horizontal bar chart: sales by category, sorted descending (valid orders only)."""
    # 只保留有效订单，避免把未支付/取消/退款订单的明细计入销售额
    valid_order_ids = set(orders.loc[orders['order_status'].isin(VALID_ORDER_STATUSES), 'order_id'])
    order_items = order_items[order_items['order_id'].isin(valid_order_ids)]
    # Merge order_items with products to get category
    merged = order_items.merge(products[['product_id', 'category']], on='product_id', how='left')
    # 与 EDA (02) 中 line_total = quantity*unit_price*(1-discount) 的口径保持一致
    merged['sale_amount'] = merged['quantity'] * merged['unit_price'] * (1 - merged['discount'].fillna(0))
    cat_sales = merged.groupby('category')['sale_amount'].sum().sort_values(ascending=True)

    # Export CSV
    csv_out = cat_sales.reset_index()
    csv_out.columns = ['商品大类', '销售额']
    csv_out = csv_out.sort_values('销售额', ascending=False)
    csv_out.to_csv(os.path.join(CHART_DIR, 'category_sales.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(10, 5))
    n = len(cat_sales)
    y_pos = range(n)
    values = cat_sales.values / 1e6  # millions

    # Single color for one-measure bars (categories identified by labels, not color)
    bars = ax.barh(y_pos, values, height=0.6, color=CAT_PALETTE[0],
                   edgecolor='none', zorder=3)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(cat_sales.index, fontsize=10)
    ax.set_xlabel('销售额（百万元）')
    ax.set_title('商品大类销售分布')
    ax.grid(axis='x', color=GRIDLINE, linewidth=0.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))
    ax.set_xlim(0, values.max() * 1.12)

    # Direct label at bar end for each
    for i, v in enumerate(values):
        ax.text(v + values.max() * 0.01, i, f'{v:.2f}M',
                va='center', fontsize=8, color=TEXT_SECONDARY)

    fig.tight_layout()
    save_chart(fig, 'chart2_category_sales.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 3: Membership Level Spending (grouped bar)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_membership_spending(users):
    """Grouped bar chart: avg spending by membership_level and gender."""
    df = users[users['gender'].isin(['男', '女'])]  # exclude 未知
    grouped = df.groupby(['membership_level', 'gender'])['total_spent'].mean().unstack()

    # Ensure consistent order
    level_order = ['普通会员', '银卡会员', '金卡会员', '钻石会员']
    grouped = grouped.reindex(level_order)
    gender_cols = ['男', '女']
    grouped = grouped[[c for c in gender_cols if c in grouped.columns]]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(grouped))
    width = 0.32
    gap = 0.04  # surface gap between adjacent bars

    for i, gender in enumerate(grouped.columns):
        offset = (i - len(grouped.columns) / 2 + 0.5) * (width + gap)
        vals = grouped[gender].values / 1e4  # ten-thousands
        color = CAT_PALETTE[i]
        bars = ax.bar(x + offset, vals, width, label=gender,
                      color=color, edgecolor='none', zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(grouped.index, fontsize=10)
    ax.set_ylabel('平均累计消费（万元）')
    ax.set_title('不同会员等级与性别的平均消费')
    ax.legend(frameon=True, loc='upper left')
    ax.grid(axis='y', color=GRIDLINE, linewidth=0.5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}万'))

    fig.tight_layout()
    save_chart(fig, 'chart3_membership_spending.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 4: Rating Distribution (pie chart)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_rating_distribution(reviews):
    """Pie chart of review rating distribution (1-5)."""
    rating_counts = reviews['rating'].value_counts().sort_index()
    labels = [f'{r}星' for r in rating_counts.index]
    sizes = rating_counts.values
    total = sizes.sum()
    pct = [f'{s/total*100:.1f}%' for s in sizes]

    # Explode 5-star slice
    explode = [0.0] * len(sizes)
    if 5 in rating_counts.index:
        idx = list(rating_counts.index).index(5)
        explode[idx] = 0.08

    colors = [CAT_PALETTE[i] for i in range(len(sizes))]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=None, colors=colors,
        autopct='%1.1f%%', startangle=140,
        pctdistance=0.78,
        wedgeprops={'linewidth': 2, 'edgecolor': SURFACE}
    )

    for at in autotexts:
        at.set_fontsize(10)
        at.set_color(TEXT_PRIMARY)

    # Custom legend
    legend_labels = [f'{l}  ({pct[i]})' for i, l in enumerate(labels)]
    ax.legend(wedges, legend_labels, title='评分分布',
              loc='center left', bbox_to_anchor=(0.92, 0.5),
              frameon=True, fontsize=9)

    ax.set_title('评论评分分布', y=0.98)
    fig.tight_layout()
    save_chart(fig, 'chart4_rating_distribution.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 5: Top 10 Products by Sales
# ═══════════════════════════════════════════════════════════════════════════════

def chart_top_products(products):
    """Horizontal bar chart of top 10 products by sales_count."""
    top10 = products.nlargest(10, 'sales_count')[['product_name', 'sales_count']]
    top10 = top10.iloc[::-1]  # reverse for horizontal bar (largest on top)

    # Truncate names to 20 chars
    names = top10['product_name'].apply(lambda s: s[:18] + '…' if len(s) > 20 else s[:20])

    # Export CSV
    csv_out = products.nlargest(10, 'sales_count')[
        ['product_name', 'category', 'sales_count', 'price', 'rating_avg']
    ]
    csv_out.columns = ['商品名称', '大类', '销量', '单价', '平均评分']
    csv_out.to_csv(os.path.join(CHART_DIR, 'top_products.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(10, 5))
    y_pos = range(len(top10))
    values = top10['sales_count'].values / 1e4  # ten-thousands

    bars = ax.barh(y_pos, values, height=0.6, color=CAT_PALETTE[0],
                   edgecolor='none', zorder=3)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel('销量（万件）')
    ax.set_title('商品销量 Top 10')
    ax.grid(axis='x', color=GRIDLINE, linewidth=0.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}万'))
    ax.set_xlim(0, values.max() * 1.12)

    for i, v in enumerate(values):
        ax.text(v + values.max() * 0.01, i, f'{v:.2f}万',
                va='center', fontsize=8, color=TEXT_SECONDARY)

    fig.tight_layout()
    save_chart(fig, 'chart5_top_products.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 6: User Age Distribution (histogram + KDE)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_age_distribution(users):
    """Histogram of user age with KDE overlay, mean and median lines."""
    ages = users['age'].dropna()
    age_mean = ages.mean()
    age_median = ages.median()

    fig, ax = plt.subplots(figsize=(10, 5))

    # Histogram
    counts, bins, patches = ax.hist(
        ages, bins=35, density=True, alpha=0.35,
        color=CAT_PALETTE[0], edgecolor=SURFACE, linewidth=0.5, zorder=2
    )

    # KDE
    kde = gaussian_kde(ages, bw_method=0.3)
    x_smooth = np.linspace(ages.min(), ages.max(), 300)
    y_smooth = kde(x_smooth)
    ax.plot(x_smooth, y_smooth, color=CAT_PALETTE[1], linewidth=2, zorder=4,
            label='密度曲线')

    # Mean and median lines
    ax.axvline(age_mean, color=CAT_PALETTE[7], linewidth=1.5, linestyle='--',
               label=f'均值: {age_mean:.1f}岁', zorder=5)
    ax.axvline(age_median, color=CAT_PALETTE[3], linewidth=1.5, linestyle=':',
               label=f'中位数: {age_median:.0f}岁', zorder=5)

    ax.set_xlabel('年龄（岁）')
    ax.set_ylabel('密度')
    ax.set_title('用户年龄分布')
    ax.legend(frameon=True, fontsize=9)
    ax.grid(axis='y', color=GRIDLINE, linewidth=0.5)
    ax.set_xlim(ages.min() - 2, ages.max() + 2)

    fig.tight_layout()
    save_chart(fig, 'chart6_age_distribution.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 7: Payment Method Share (donut chart)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_payment_method(orders):
    """Donut chart of payment method distribution (valid orders only)."""
    pay_counts = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)]['payment_method'].value_counts()
    total = pay_counts.sum()

    labels = pay_counts.index.tolist()
    sizes = pay_counts.values
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts = ax.pie(
        sizes, labels=None, colors=colors, startangle=140,
        wedgeprops={'linewidth': 2, 'edgecolor': SURFACE, 'width': 0.45}
    )

    # Legend with count and percentage
    legend_labels = [
        f'{l}\n  {s:,}笔 ({s/total*100:.1f}%)'
        for l, s in zip(labels, sizes)
    ]
    ax.legend(wedges, legend_labels, title='支付方式',
              loc='center left', bbox_to_anchor=(0.92, 0.5),
              frameon=True, fontsize=8)

    # Center label
    ax.text(0, 0, f'总订单\n{total:,}笔', ha='center', va='center',
            fontsize=12, fontweight='bold', color=TEXT_PRIMARY)
    ax.set_title('支付方式分布', y=0.98)
    fig.tight_layout()
    save_chart(fig, 'chart7_payment_method.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 8: Province Sales Heatmap Data (CSV export)
# ═══════════════════════════════════════════════════════════════════════════════

def export_province_sales(orders):
    """Aggregate sales by province and export as CSV for Tableau (valid orders only)."""
    orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)]
    province_sales = orders.groupby('shipping_province').agg(
        order_count=('order_id', 'count'),
        total_revenue=('actual_amount', 'sum'),
        avg_order_value=('actual_amount', 'mean'),
    ).reset_index()
    province_sales.columns = ['省份', '订单数', '总营收', '平均客单价']
    province_sales = province_sales.sort_values('总营收', ascending=False)

    csv_path = os.path.join(CHART_DIR, 'province_sales.csv')
    province_sales.to_csv(csv_path, index=False, encoding='utf-8-sig')
    global _chart_counter
    _chart_counter += 1
    print(f'  [{_chart_counter}/12] Exported: province_sales.csv ({len(province_sales)} provinces)')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 9: Order Status Breakdown
# ═══════════════════════════════════════════════════════════════════════════════

def chart_order_status(orders):
    """Horizontal bar chart of order status with count labels."""
    status_counts = orders['order_status'].value_counts()
    # Sort by count ascending for horizontal bar
    status_counts = status_counts.sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y_pos = range(len(status_counts))
    values = status_counts.values / 1e4  # ten-thousands
    n = len(status_counts)

    # Assign color by count rank (larger = darker blue)
    bar_colors = [CAT_PALETTE[0]] * n  # single color — one measure

    bars = ax.barh(y_pos, values, height=0.6, color=bar_colors,
                   edgecolor='none', zorder=3)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(status_counts.index, fontsize=10)
    ax.set_xlabel('订单数量（万）')
    ax.set_title('订单状态分布')
    ax.grid(axis='x', color=GRIDLINE, linewidth=0.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}万'))
    ax.set_xlim(0, values.max() * 1.15)

    for i, (label, v) in enumerate(zip(status_counts.index, status_counts.values)):
        ax.text(values[i] + values.max() * 0.01, i,
                f'{v:,} ({v/status_counts.sum()*100:.1f}%)',
                va='center', fontsize=8, color=TEXT_SECONDARY)

    fig.tight_layout()
    save_chart(fig, 'chart9_order_status.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 10: Price vs Rating Scatter
# ═══════════════════════════════════════════════════════════════════════════════

def chart_price_rating_scatter(products):
    """Scatter plot: price vs rating_avg, colored by category."""
    # Sample 2000 products (or all if fewer)
    df = products.dropna(subset=['price', 'rating_avg'])
    n_sample = min(2000, len(df))
    df_sample = df.sample(n=n_sample, random_state=42)

    categories = df_sample['category'].unique()
    # Map categories to fixed palette slots (color follows entity)
    cat_color_map = {}
    for i, cat in enumerate(categories):
        cat_color_map[cat] = CAT_PALETTE[i % len(CAT_PALETTE)]

    fig, ax = plt.subplots(figsize=(10, 6))

    for cat in categories:
        subset = df_sample[df_sample['category'] == cat]
        ax.scatter(subset['price'], subset['rating_avg'],
                   c=cat_color_map[cat], label=cat,
                   alpha=0.55, s=18, edgecolors='none', zorder=2)

    # Trend line (linear regression on full sample)
    from numpy.polynomial.polynomial import polyfit
    x_vals = df_sample['price'].values
    y_vals = df_sample['rating_avg'].values
    # Fit degree 1 polynomial
    coeffs = polyfit(x_vals, y_vals, 1)
    x_trend = np.linspace(x_vals.min(), x_vals.max(), 200)
    y_trend = coeffs[0] + coeffs[1] * x_trend
    ax.plot(x_trend, y_trend, color=TEXT_PRIMARY, linewidth=1.5,
            linestyle='--', zorder=5, label='趋势线')

    ax.set_xlabel('价格（元）')
    ax.set_ylabel('平均评分')
    ax.set_title('商品价格与评分关系')
    ax.legend(frameon=True, fontsize=8, ncol=2, loc='lower right')
    ax.grid(color=GRIDLINE, linewidth=0.5)

    # Format x-axis with comma separators
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))

    fig.tight_layout()
    save_chart(fig, 'chart10_price_rating_scatter.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 11: Top 10 Cities Revenue
# ═══════════════════════════════════════════════════════════════════════════════

def chart_top_cities(orders):
    """Bar chart of top 10 cities by total revenue (valid orders only)."""
    orders = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)]
    city_rev = orders.groupby('shipping_city')['actual_amount'].sum().nlargest(10)
    city_rev = city_rev.sort_values()  # ascending for display

    fig, ax = plt.subplots(figsize=(10, 5))
    y_pos = range(len(city_rev))
    values = city_rev.values / 1e6

    bars = ax.barh(y_pos, values, height=0.6, color=CAT_PALETTE[0],
                   edgecolor='none', zorder=3)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(city_rev.index, fontsize=10)
    ax.set_xlabel('营收（百万元）')
    ax.set_title('城市营收 Top 10')
    ax.grid(axis='x', color=GRIDLINE, linewidth=0.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))
    ax.set_xlim(0, values.max() * 1.12)

    for i, v in enumerate(values):
        ax.text(v + values.max() * 0.01, i, f'{v:.2f}M',
                va='center', fontsize=8, color=TEXT_SECONDARY)

    fig.tight_layout()
    save_chart(fig, 'chart11_top_cities.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 12: Weekly Order Pattern
# ═══════════════════════════════════════════════════════════════════════════════

def chart_weekly_pattern(orders):
    """Bar chart of order count by day of week (Monday-Sunday, valid orders only)."""
    df = orders[orders['order_status'].isin(VALID_ORDER_STATUSES)].copy()
    df['day_of_week'] = df['order_date'].dt.dayofweek  # 0=Monday, 6=Sunday
    day_counts = df['day_of_week'].value_counts().sort_index()

    day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    x_labels = [day_names[i] for i in day_counts.index]
    values = day_counts.values / 1e4

    fig, ax = plt.subplots(figsize=(9, 4.5))

    bars = ax.bar(range(len(day_counts)), values, width=0.55,
                  color=CAT_PALETTE[0], edgecolor='none', zorder=3)

    ax.set_xticks(range(len(day_counts)))
    ax.set_xticklabels(x_labels, fontsize=10)
    ax.set_ylabel('订单量（万）')
    ax.set_title('周订单规律')
    ax.grid(axis='y', color=GRIDLINE, linewidth=0.5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}万'))

    # Value labels on top of each bar
    for i, v in enumerate(values):
        ax.text(i, v + values.max() * 0.015, f'{v:.2f}万',
                ha='center', fontsize=9, color=TEXT_SECONDARY)

    ax.set_xlim(-0.5, len(day_counts) - 0.5)
    ax.set_ylim(0, values.max() * 1.12)

    fig.tight_layout()
    save_chart(fig, 'chart12_weekly_pattern.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print('=' * 60)
    print('E-Commerce Data Visualization')
    print(f'Output directory: {CHART_DIR}')
    print('=' * 60)

    data = load_data()

    print('\nGenerating charts...')

    # 1: Monthly Revenue Trend
    chart_monthly_revenue(data['orders'])

    # 2: Category Sales Distribution
    chart_category_sales(data['order_items'], data['products'], data['orders'])

    # 3: Membership Level Spending
    chart_membership_spending(data['users'])

    # 4: Rating Distribution (pie)
    chart_rating_distribution(data['reviews'])

    # 5: Top 10 Products by Sales
    chart_top_products(data['products'])

    # 6: User Age Distribution (histogram + KDE)
    chart_age_distribution(data['users'])

    # 7: Payment Method Share (donut)
    chart_payment_method(data['orders'])

    # 8: Province Sales Data Export (CSV)
    export_province_sales(data['orders'])

    # 9: Order Status Breakdown
    chart_order_status(data['orders'])

    # 10: Price vs Rating Scatter
    chart_price_rating_scatter(data['products'])

    # 11: Top 10 Cities Revenue
    chart_top_cities(data['orders'])

    # 12: Weekly Order Pattern
    chart_weekly_pattern(data['orders'])

    print(f'\nDone! {_chart_counter} outputs saved to {CHART_DIR}')


if __name__ == '__main__':
    main()
