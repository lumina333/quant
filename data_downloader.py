# -*- coding: utf-8 -*-
"""
简化版数据下载模块 - 使用AKShare
（减少数据量，便于快速熟悉流程）
"""
import os
from csv import excel

import pandas as pd
import akshare as ak
from config import START_DATE, END_DATE, STOCK_UNIVERSE

# 创建数据存储目录
DATA_DIR = './data'
os.makedirs(DATA_DIR, exist_ok=True)


def download_index_constituents():
    print("下载指数成分股...")
    # 获取沪深300成分股
    try:
        df = ak.index_stock_cons_sina(symbol=STOCK_UNIVERSE)

        # 仅保留前20只股票（减少数据量）
        df = df.head(20)

        df.to_csv(f'{DATA_DIR}/index_constituents.csv', index=False)
        print(f"成分股数量: {len(df)}")
    except Exception as e:
        print(f"下载指数成分股失败: {e}")


def download_stock_daily():
    print("下载日线行情数据...")
    # 获取成分股列表
    try:
        constituents = pd.read_csv(f'{DATA_DIR}/index_constituents.csv')
        stock_list = constituents['code'].tolist()

        all_data = []
        for i, stock in enumerate(stock_list):
            # 获取个股日线数据
            df = ak.stock_zh_a_hist(
                symbol= str(stock),
                period="daily",
                start_date=START_DATE,
                end_date=END_DATE,
                adjust="qfq"  # 前复权
            )
            df['ts_code'] = stock
            all_data.append(df)
            print(f"已下载 {stock} 的日线数据")
            # 合并保存
            if all_data:
                pd.concat(all_data).to_csv(f'{DATA_DIR}/stock_daily.csv', index=False)
                print(f"日线数据保存完成，共 {len(all_data)} 只股票")
            else:
                print("未下载到任何日线数据")

    except Exception as e:
        print(f"下载日线行情数据失败: {e}")


def download_valuation_data():
    print("下载估值数据...")
    # 获取成分股列表
    constituents = pd.read_csv(f'{DATA_DIR}/index_constituents.csv')
    stock_list = constituents['code'].tolist()

    all_data = []
    for stock in stock_list:
        try:
            stock_str = str(stock)
            # 获取个股估值指标（使用乐咕乐股数据）
            df = ak.stock_a_indicator_lg(stock_str)

            # 确保日期列是datetime类型
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 将START_DATE和END_DATE转换为datetime类型
            start_date_dt = pd.to_datetime(START_DATE, format='%Y%m%d')
            end_date_dt = pd.to_datetime(END_DATE, format='%Y%m%d')

            # 仅保留从START_DATE到END_DATE之间的数据
            df = df[(df['trade_date'] >= start_date_dt) & (df['trade_date'] <= end_date_dt)]

            df['ts_code'] = stock_str
            all_data.append(df)
            print(f"已下载 {stock_str} 的估值数据")
        except Exception as e:
            print(f"下载 {stock_str} 估值数据失败: {str(e)}")

    # 合并保存
    if all_data:
        pd.concat(all_data).to_csv(f'{DATA_DIR}/valuation.csv', index=False)
        print(f"估值数据保存完成，共 {len(all_data)} 只股票")
    else:
        print("未下载到任何估值数据")


def download_benchmark_data():
    print("下载基准指数数据...")
    # 获取沪深300指数数据
    df = ak.stock_zh_index_daily(symbol="sh000300")

    # 确保日期列是datetime类型
    df['date'] = pd.to_datetime(df['date'])

    # 将START_DATE和END_DATE转换为datetime类型
    start_date_dt = pd.to_datetime(START_DATE, format='%Y%m%d')
    end_date_dt = pd.to_datetime(END_DATE, format='%Y%m%d')

    # 仅保留从START_DATE开始的数据
    df = df[(df['date'] >= start_date_dt) & (df['date'] <= end_date_dt)]

    df.to_csv(f'{DATA_DIR}/benchmark.csv', index=False)
    print("基准指数数据保存完成")


def download_all_data():
    """主函数：执行所有下载任务"""
    print("开始下载数据...")
    download_index_constituents()
    download_stock_daily()
    download_valuation_data()
    download_benchmark_data()
    print("数据下载完成！")


if __name__ == '__main__':
    download_all_data()