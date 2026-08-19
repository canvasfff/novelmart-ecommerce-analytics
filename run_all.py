#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Olist 电商经营分析平台 —— 一键运行脚本

依次执行：
  1. 数据清洗与特征工程
  2. 探索性数据分析 (EDA)
  3. 高级分析（RFM/同期群/关联/预测）
  4. 数据可视化

用法：
  python run_all.py
"""

import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Windows 控制台默认 GBK，统一改为 UTF-8 输出避免中文乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPTS = [
    'python/01_data_cleaning.py',
    'python/02_exploratory_analysis.py',
    'python/03_advanced_analysis.py',
    'python/04_visualizations.py',
]


def main():
    print('=' * 70)
    print('Olist 电商经营分析平台 —— 一键运行')
    print('=' * 70)
    for script in SCRIPTS:
        path = os.path.join(PROJECT_DIR, script)
        print(f'\n>>> 运行 {script}')
        code = subprocess.call([sys.executable, path])
        if code != 0:
            print(f'!!! 脚本执行失败: {script} (exit={code})')
            sys.exit(code)
    print('\n全部完成 ✅')


if __name__ == '__main__':
    main()
