import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from config import END_DATE

DATA_DIR = Path('./data')


def calculate_factors():
    """
    计算指定结束日期的三大因子（简化版）

    参数:
    end_date: 因子计算的结束日期（字符串或datetime）
    """
    # 转换日期格式
    end_date = pd.to_datetime(END_DATE)

    print(f"计算截止到 {end_date.strftime('%Y-%m-%d')} 的因子值")

    # 加载数据
    df = pd.read_csv(f'{DATA_DIR}/clean_data.csv', parse_dates=['trade_date'])

    # 价值因子：处理异常PE值
    df['value'] = np.where(df['pe_ttm'] <= 0, np.nan, 1 / df['pe_ttm'])

    # 按股票代码分组计算
    grouped = df.groupby('ts_code')['close']
    # 动量因子
    df['momentum'] = np.log(df['close'] / grouped.shift(periods=10))
    # 低波动因子
    df['low_vol'] = -grouped.pct_change().rolling(window=10, min_periods=10).std()

    df = df.dropna(subset=['value', 'momentum', 'low_vol'])
    result_df = df[['trade_date', 'ts_code', 'value', 'momentum', 'low_vol']]

    # 保存结果
    output_file = f'{DATA_DIR}/factor_data.csv'
    result_df.to_csv(output_file, index=False)

    print(f"因子计算完成！共计算 {len(result_df)} 组因子值")
    print(f"数据已保存至: {output_file}")

    return result_df


if __name__ == '__main__':
    calculate_factors()