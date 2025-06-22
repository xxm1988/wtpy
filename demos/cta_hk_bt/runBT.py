#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯控股回测演示
使用富途OpenAPI数据源进行港股回测
"""

from wtpy import WtBtEngine, EngineType
from wtpy.apps import WtBtAnalyst

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../Strategies'))
from DualThrustHK import StraDualThrustHK

def analyze_with_pyfolio(fund_filename: str, capital: float = 500000):
    """
    使用pyfolio进行回测结果分析
    
    Args:
        fund_filename: 资金曲线文件路径
        capital: 初始资金
    """
    try:
        import pyfolio as pf
        import pandas as pd
        from datetime import datetime
        import matplotlib.pyplot as plt

        # 读取每日资金
        df = pd.read_csv(fund_filename)
        df['date'] = df['date'].apply(lambda x: datetime.strptime(str(x), '%Y%m%d'))
        df = df.set_index(df["date"])

        # 将资金转换成收益率
        ay = df['dynbalance'] + capital
        rets = ay.pct_change().fillna(0).tz_localize('UTC')

        # 调用pyfolio进行分析
        pf.create_full_tear_sheet(rets)

        # 如果在jupyter，不需要执行该语句
        plt.show()
    except ImportError:
        print("请安装pyfolio: pip install pyfolio")

if __name__ == "__main__":
    # 创建一个运行环境，并加入策略
    engine = WtBtEngine(EngineType.ET_CTA)
    config_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(config_dir, "configbt.yaml")
    engine.init(config_dir, config_file)
    
    # 配置回测时间范围（港股交易时间）
    # 2023年1月1日到2025年12月31日
    engine.configBacktest(202301010930, 202512311600)
    #engine.configBTStorage(mode="csv", path="../storage/")

    # 添加富途数据加载器
    from wtpy.futu import FutuDataLoader
    futu_loader = FutuDataLoader(host='127.0.0.1', port=11111)
    if futu_loader.init():
        # 设置数据加载器，bAutoTrans=False表示不自动转换数据格式
        engine.set_extended_data_loader(futu_loader, bAutoTrans=False)
        print("富途数据加载器初始化成功")
    else:
        print("富途数据加载器初始化失败，请检查富途OpenD服务")
        exit(1)
    
    engine.commitBTConfig()

    # 创建腾讯控股DualThrust策略实例
    straInfo = StraDualThrustHK(
        name='dt_tencent',      # 策略实例名称
        code='HK.00700',       # 腾讯控股代码
        barCnt=50000,          # 要拉取的K线条数
        period='m1',           # 使用5分钟K线
        days=30,               # 算法引用的历史数据条数
        k1=0.7,                # 上边界系数
        k2=0.7,                # 下边界系数
        max_pos=1000,          # 最大持仓股数
        stop_loss=0.05         # 止损比例5%
    )
    engine.set_cta_strategy(straInfo)

    try:
        # 运行回测
        print("开始运行回测...")
        print(f"回测标的: 腾讯控股 (HK.00700)")
        print(f"回测时间: 2023-01-01 09:30 至 2025-12-31 16:00")
        print(f"策略参数: days={straInfo.days}, k1={straInfo.k1}, k2={straInfo.k2}")
        
        engine.run_backtest()
        print("回测运行完成！")

        # 分析回测结果
        print("开始分析回测结果...")
        analyst = WtBtAnalyst()
        analyst.add_strategy('dt_tencent', folder='./outputs_bt/', init_capital=500000, rf=0.02, annual_trading_days=250)
        analyst.run_new()
        print("回测结果分析完成！")

        # 使用pyfolio进行详细分析（可选）
        # analyze_with_pyfolio('./outputs_bt/dt_tencent/funds.csv', 500000)

        # 输出回测完成信息
        print("\n=== 腾讯控股回测完成！ ===")
        print("回测结果保存在 ./outputs_bt/dt_tencent/ 目录下")
        print("可以查看以下文件：")
        print("- funds.csv: 资金曲线")
        print("- trades.csv: 交易记录")
        print("- closes.csv: 平仓记录")
        print("- signals.csv: 信号记录")
        
    finally:
        # 确保关闭富途连接
        print("\n正在关闭富途数据连接...")
        futu_loader.close()
        print("富途数据连接已关闭")