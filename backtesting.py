import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# 设置默认字体为英文
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'Verdana']
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 数据文件路径
DATA_DIR = './data'
PORTFOLIO_HOLDING_FILE = f'{DATA_DIR}/portfolio_holding.csv'
CLEAN_DATA_FILE = f'{DATA_DIR}/clean_data.csv'
BENCHMARK_FILE = f'{DATA_DIR}/benchmark.csv'

class FixedWeightStrategy(bt.Strategy):
    params = (
        ('commission', 0.0005),  # 默认交易佣金 0.05%
        ('portfolio_holding', None),  # 持仓数据作为参数传递
    )

    def __init__(self):
        # 创建持仓字典 {date: {symbol: weight}}
        self.holdings_dict = {}
        for _, row in self.p.portfolio_holding.iterrows():
            dt = row['trade_date'].date()
            symbol = str(row['ts_code'])
            weight = row['weight']
            
            if dt not in self.holdings_dict:
                self.holdings_dict[dt] = {}
                
            self.holdings_dict[dt][symbol] = weight

        # 创建数据映射 {symbol: data}
        self.data_map = {d._name: d for d in self.datas}
        
        # 添加基准数据引用
        self.benchmark = self.data_map['benchmark']
        
        # 记录交易日和净值
        self.date_index = []
        self.values = []
        self.benchmark_values = []

    def next(self):
        current_date = self.datetime.date(0)
        self.date_index.append(current_date)
        self.values.append(self.broker.getvalue())
        
        # 记录基准净值
        self.benchmark_values.append(self.benchmark.close[0])
        
        # 只在持仓变更日调整仓位
        if current_date not in self.holdings_dict:
            return
            
        daily_holdings = self.holdings_dict[current_date]
        total_value = self.broker.getvalue()
        
        # 清除不在当前持仓的股票
        for data in self.datas:
            if data == self.benchmark:
                continue
                
            symbol = data._name
            if symbol not in daily_holdings and self.getposition(data):
                self.close(data)
        
        # 按权重调整持仓
        for symbol, weight in daily_holdings.items():
            if symbol not in self.data_map:
                continue
                
            data = self.data_map[symbol]
            target_value = total_value * weight
            self.order_target_value(data, target_value)

    def stop(self):
        # 计算简单收益率
        initial_value = self.values[0] if self.values else 0
        final_value = self.values[-1] if self.values else 0
        
        # 计算基准收益率
        initial_benchmark = self.benchmark_values[0] if self.benchmark_values else 0
        final_benchmark = self.benchmark_values[-1] if self.benchmark_values else 0
        
        if initial_value > 0 and initial_benchmark > 0:
            total_return = (final_value / initial_value - 1) * 100
            benchmark_return = (final_benchmark / initial_benchmark - 1) * 100
            excess_return = total_return - benchmark_return
            
            print(f"\n===== Strategy Performance =====")
            print(f"Initial Capital: {initial_value:,.2f}")
            print(f"Final Capital: {final_value:,.2f}")
            print(f"Strategy Return: {total_return:.2f}%")
            print(f"Benchmark Return: {benchmark_return:.2f}%")
            print(f"Excess Return: {excess_return:.2f}%")
        else:
            print("Warning: Initial capital or benchmark value is zero, cannot calculate return")
        
        # 绘制并显示净值曲线
        self.plot_results()

    def plot_results(self):
        if not self.values or not self.benchmark_values:
            print("No data to plot")
            return
            
        # 归一化处理，使初始值都为100
        norm_strategy = [v / self.values[0] * 100 for v in self.values]
        norm_benchmark = [v / self.benchmark_values[0] * 100 for v in self.benchmark_values]
        
        plt.figure(figsize=(12, 8))
        
        # 绘制策略净值曲线
        plt.subplot(2, 1, 1)
        plt.plot(self.date_index, norm_strategy, 'b-', label='Strategy Value')
        plt.plot(self.date_index, norm_benchmark, 'r-', label='Benchmark Value')
        plt.title('Strategy vs Benchmark Performance')
        plt.ylabel('Normalized Value (Start=100)')
        plt.grid(True)
        plt.legend()
        
        # 绘制超额收益曲线
        plt.subplot(2, 1, 2)
        excess = [s - b for s, b in zip(norm_strategy, norm_benchmark)]
        plt.plot(self.date_index, excess, 'g-', label='Excess Return')
        plt.title('Excess Return Over Benchmark')
        plt.xlabel('Date')
        plt.ylabel('Excess Return (Points)')
        plt.grid(True)
        plt.legend()
        
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        
        plt.show()

# 主函数
def main():
    # 读取数据
    benchmark_df = pd.read_csv(BENCHMARK_FILE, parse_dates=['date']).rename(columns={'date': 'trade_date'})
    portfolio_holding = pd.read_csv(PORTFOLIO_HOLDING_FILE, parse_dates=['trade_date'])
    clean_data = pd.read_csv(CLEAN_DATA_FILE, parse_dates=['trade_date'])
    
    # 确保股票代码是字符串
    portfolio_holding['ts_code'] = portfolio_holding['ts_code'].astype(str)
    clean_data['ts_code'] = clean_data['ts_code'].astype(str)
    
    # 创建Cerebro引擎
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.set_cash(10000000)  # 设置初始资金1000万
    
    # 添加个体股票数据
    all_symbols = portfolio_holding['ts_code'].unique()
    
    for symbol in all_symbols:
        # 为每只股票创建单独的数据流
        df = clean_data[clean_data['ts_code'] == symbol].copy()
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        
        # 创建PandasData对象
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            name=symbol
        )
        cerebro.adddata(data)
    
    # 添加基准数据
    benchmark_df.set_index('trade_date', inplace=True)
    bench_data = bt.feeds.PandasData(
        dataname=benchmark_df,
        datetime=None,
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        name='benchmark'
    )
    cerebro.adddata(bench_data)
    
    # 添加策略并传递持仓数据
    cerebro.addstrategy(
        FixedWeightStrategy,
        portfolio_holding=portfolio_holding
    )
    
    # 运行回测
    print("===== Starting Backtest =====")
    cerebro.run()
    print("Backtest completed")

if __name__ == '__main__':
    main()