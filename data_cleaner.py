# -*- coding: utf-8 -*-
"""
数据预处理模块
"""
import pandas as pd

DATA_DIR = './data'

def preprocess_data():
    """主处理函数"""
    print("开始数据预处理...")
    # 加载原始数据
    daily = pd.read_csv(f'{DATA_DIR}/stock_daily.csv', parse_dates=['日期'])
    valuation = pd.read_csv(f'{DATA_DIR}/valuation.csv', parse_dates=['trade_date'])

    daily.drop(columns="ts_code",inplace=True)
    # 1. 重命名列以统一格式
    daily.rename(columns={
        '日期': 'trade_date',
        '股票代码': 'ts_code',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount',
        '振幅': 'amplitude',
        '涨跌幅': 'pct_change',
        '涨跌额': 'change',
        '换手率': 'turnover'
    }, inplace=True)
    # 2. 合并数据集
    merged = pd.merge(daily, valuation, on=['ts_code', 'trade_date'], how='inner').sort_values(['trade_date', 'ts_code'])
    
    # 3. 处理异常值
    # 删除交易量、收盘价为空的记录
    merged = merged.dropna(subset=['volume', 'close'])


    # 缺失的PE/PB用当日均值填充
    industry_pe = merged.groupby('trade_date')['pe_ttm'].transform('median')
    merged['pe_ttm'] = merged['pe_ttm'].fillna(industry_pe)
    industry_pb = merged.groupby('trade_date')['pb'].transform('median')
    merged['pb'] = merged['pb'].fillna(industry_pb)

    # 剔除PE/PB为负或极大值
    merged = merged[(merged['pe_ttm'] > 0) & (merged['pe_ttm'] < 100)]
    merged = merged[(merged['pb'] > 0) & (merged['pb'] < 20)]

    # 4. 计算基础指标
    # 注意：AKShare不提供总股本数据，这里使用市值估算
    merged['market_cap'] = merged['close'] * merged['volume'] / merged['turnover'] * 100
    
    # 保存处理后的数据
    merged.to_csv(f'{DATA_DIR}/clean_data.csv', index=False)
    print("数据预处理完成！")
    print("="*50)

if __name__ == '__main__':
    preprocess_data()