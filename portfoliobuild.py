# -*- coding: utf-8 -*-
"""
组合构建模块（每7天调仓版）
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ------------------- 配置参数 -------------------
DATA_DIR = Path('./data')
FACTOR_FILE = DATA_DIR / 'factor_data.csv'  # 因子数据文件（ts_code, trade_date, value, momentum, low_vol）
PORTFOLIO_FILE = DATA_DIR / 'portfolio_holding.csv'  # 输出持仓文件（ts_code, trade_date, weight）
INITIAL_CAPITAL = 1e6  # 初始资金（可选，根据回测需求）
TOP_N = 5 # 每期持仓股票数量
REBALANCE_FREQ = '3D'  # 调仓频率（每7天）


# ------------------- 数据加载与时间范围确定 -------------------
def load_data():
    """
    加载因子数据，并动态获取数据的最小/最大交易日
    返回：因子数据DataFrame，最小日期，最大日期
    """
    # 加载因子数据
    df = pd.read_csv(FACTOR_FILE, parse_dates=['trade_date'])

    # 动态获取数据的最小和最大交易日（关键改进）
    min_date = df['trade_date'].min()
    max_date = df['trade_date'].max()
    print(f"因子数据时间范围：{min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")

    return df, min_date, max_date


# ------------------- 生成每7天调仓日 -------------------
def generate_rebalance_dates(min_date, max_date):
    """
    生成每7天的调仓日（仅保留数据中存在的交易日）
    参数：
        min_date: 数据最小日期（datetime）
        max_date: 数据最大日期（datetime）
    返回：
        调仓日列表（日期对象）
    """
    # 生成从min_date到max_date的每7天间隔的日期序列（包含首尾）
    raw_dates = pd.date_range(
        start=min_date,
        end=max_date,
        freq=REBALANCE_FREQ  # 调仓频率（每7天）
    )

    # 转换为日期对象（仅日期部分，无时间）
    raw_dates = [d.date() for d in raw_dates]

    # 筛选出因子数据中实际存在的交易日（避免处理无数据的日期）
    # 加载因子数据的trade_date列（仅日期部分）用于匹配
    factor_dates = pd.read_csv(FACTOR_FILE, parse_dates=['trade_date'])['trade_date'].dt.date.unique()
    valid_dates = [d for d in raw_dates if d in factor_dates]

    if not valid_dates:
        raise ValueError("无有效调仓日数据！请检查因子数据时间范围或调仓频率。")

    print(f"生成有效调仓日：{[d.strftime('%Y-%m-%d') for d in valid_dates[:5]]} ...（共 {len(valid_dates)} 个）")
    return valid_dates


# ------------------- 因子标准化与组合构建 -------------------
def build_portfolio_7d(factor_df, rebalance_dates, top_n=TOP_N):
    """
    每7天调仓的组合构建逻辑
    参数：
        factor_df: 因子数据（ts_code, trade_date, value, momentum, low_vol）
        rebalance_dates: 调仓日列表（日期对象）
        top_n: 每期持仓股票数量
    返回：
        持仓数据（ts_code, trade_date, weight）
    """
    # -------------------- 步骤1：筛选调仓日数据 --------------------
    # 提取factor_df的trade_date日期部分（用于匹配调仓日）
    factor_df = factor_df.copy()
    factor_df['trade_date_date'] = factor_df['trade_date'].dt.date

    # 筛选出属于调仓日的因子数据（确保调仓日有数据）
    rebalance_df = factor_df[factor_df['trade_date_date'].isin(rebalance_dates)].copy()
    if rebalance_df.empty:
        raise ValueError("调仓日无对应因子数据！请检查数据或调仓日生成逻辑。")

    # -------------------- 步骤2：按调仓日标准化因子（关键） --------------------
    # 对每个调仓日的因子值独立标准化（消除当日量纲差异）
    # 标准化公式：(因子值 - 当日因子均值) / 当日因子标准差（避免除零错误）
    factor_cols = ['value', 'momentum', 'low_vol']
    for col in factor_cols:
        rebalance_df[f'standardized_{col}'] = rebalance_df.groupby('trade_date')[col].transform(
            lambda x: (x - x.mean()) / x.std() if x.std() != 0 else 0  # 标准差为0时设为0
        )

    # -------------------- 步骤3：合成综合得分并筛选持仓 --------------------
    # 等权合成标准化因子（可调整为加权，如根据因子重要性赋权）
    rebalance_df['composite_score'] = rebalance_df[[f'standardized_{col}' for col in factor_cols]].sum(axis=1)

    # 按调仓日分组，筛选前TOP_N股票（综合得分降序）
    portfolios = []
    for trade_date, group in rebalance_df.groupby('trade_date'):
        # 跳过无有效因子的日期（如所有因子均为NaN）
        if group['composite_score'].isna().all():
            print(f"警告：{trade_date.strftime('%Y-%m-%d')} 无有效因子，跳过调仓！")
            continue

        # 筛选前TOP_N股票（综合得分最高的TOP_N只）
        top_stocks = group.nlargest(top_n, 'composite_score')

        # 等权分配权重（权重和为1）
        top_stocks['weight'] = 1 / top_n

        # 保留关键列（ts_code, trade_date, weight）
        portfolios.append(top_stocks[['ts_code', 'trade_date', 'weight']])

    # -------------------- 步骤4：合并持仓并保存 --------------------
    portfolio_df = pd.concat(portfolios, ignore_index=True)
    portfolio_df.to_csv(PORTFOLIO_FILE, index=False)
    print(f"组合构建完成！共 {len(portfolio_df)} 条持仓记录（{len(rebalance_dates)}个调仓日）")
    print(f"数据已保存至: {PORTFOLIO_FILE}")

    return portfolio_df


# ------------------- 主函数 -------------------
def main():
    # -------------------- 1. 加载数据并获取时间范围 --------------------
    factor_df, min_date, max_date = load_data()

    # -------------------- 2. 生成每7天调仓日（仅保留数据中存在的日期） --------------------
    rebalance_dates = generate_rebalance_dates(min_date, max_date)

    # -------------------- 3. 构建每7天调仓的组合 --------------------
    build_portfolio_7d(factor_df, rebalance_dates, top_n=TOP_N)


if __name__ == '__main__':
    main()