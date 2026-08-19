#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Olist 电商经营分析平台 —— 公共配置与工具模块
Common paths, business rules and loading utilities.

所有 Python 脚本共用此模块，保证路径、业务口径和表名一致。
"""

import os
import sys

import pandas as pd

# ── 路径 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
EDA_DIR = os.path.join(PROCESSED_DIR, 'eda_results')
ADV_DIR = os.path.join(PROCESSED_DIR, 'advanced_results')
CHART_DIR = os.path.join(PROJECT_DIR, 'charts')
DOCS_DIR = os.path.join(PROJECT_DIR, 'docs')

# 原始数据文件名
RAW_FILES = {
    'customers': 'olist_customers_dataset.csv',
    'geolocation': 'olist_geolocation_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'order_reviews': 'olist_order_reviews_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'category_translation': 'product_category_name_translation.csv',
}

# 清洗/分析后输出文件名
PROCESSED_FILES = {
    'customers': 'customers.csv',
    'customers_agg': 'customers_agg.csv',
    'sellers': 'sellers.csv',
    'products': 'products.csv',
    'orders': 'orders.csv',
    'order_items': 'order_items.csv',
    'payments': 'payments.csv',
    'reviews': 'reviews.csv',
    'geolocation_zip': 'geolocation_zip.csv',
    'category_translation': 'category_translation.csv',
}

# ── 业务口径 ──────────────────────────────────────────────────────────────────
# Olist 订单状态：
#   delivered/shipped/invoiced/processing/created/approved 表示已形成有效交易；
#   canceled/unavailable 不计入营收、复购、RFM 等经营指标。
VALID_ORDER_STATUSES = [
    'delivered', 'shipped', 'invoiced', 'processing', 'created', 'approved'
]

ORDER_STATUS_CN = {
    'delivered': '已送达',
    'shipped': '已发货',
    'invoiced': '已开票',
    'processing': '处理中',
    'created': '已创建',
    'approved': '已批准',
    'canceled': '已取消',
    'unavailable': '不可用',
}

PAYMENT_TYPE_CN = {
    'credit_card': '信用卡',
    'boleto': '银行单据',
    'voucher': '优惠券',
    'debit_card': '借记卡',
    'not_defined': '未定义',
}

# ── 输出编码与显示 ────────────────────────────────────────────────────────────
CSV_ENCODING = 'utf-8-sig'


def ensure_dirs():
    """确保所有输出目录存在。"""
    for d in [PROCESSED_DIR, EDA_DIR, ADV_DIR, CHART_DIR]:
        os.makedirs(d, exist_ok=True)


def configure_console():
    """Windows 控制台默认 GBK，统一改为 UTF-8 输出避免中文乱码。"""
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def load_raw(name):
    """从 data/raw 读取 Olist 原始 CSV。"""
    path = os.path.join(RAW_DIR, RAW_FILES[name])
    return pd.read_csv(path, encoding='utf-8')


def load_processed(name):
    """从 data/processed 读取清洗后的 CSV。"""
    path = os.path.join(PROCESSED_DIR, PROCESSED_FILES[name])
    return pd.read_csv(path, encoding='utf-8-sig')


def save_processed(df, name):
    """保存清洗/聚合后的 CSV 到 data/processed。"""
    path = os.path.join(PROCESSED_DIR, PROCESSED_FILES[name])
    df.to_csv(path, index=False, encoding=CSV_ENCODING)
    print(f'  saved: {path}')


def to_datetime_columns(df, cols):
    """将指定列统一转为 datetime。"""
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df
