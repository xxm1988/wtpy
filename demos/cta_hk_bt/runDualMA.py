#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股双均线策略回测脚本
回测腾讯控股最近2年的数据
"""

import sys
import os
from datetime import datetime, timedelta

# 添加wtpy路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from wtpy import WtBtEngine, EngineType
from wtpy.apps import WtBtAnalyst
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Strategies.DualMAHK import DualMAHK
from wtpy.futu import FutuDataLoader

def main():
    """
    主函数：运行双均线策略回测
    """
    print("=== 开始港股双均线策略回测 ===")
    
    # 初始化富途数据加载器
    print("初始化富途数据加载器...")
    futu_loader = FutuDataLoader(host='127.0.0.1', port=11111)
    if not futu_loader.init():
        print("富途数据加载器初始化失败！")
        return
    print("富途数据加载器初始化成功")
    
    try:
        # 创建回测引擎
        engine = WtBtEngine(EngineType.ET_CTA)
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(config_dir, "configbt.yaml")  # 使用基础配置文件
        engine.init(config_dir, config_file)
        
        # 配置回测时间范围（港股交易时间）
        engine.configBacktest(202301010930, 202506211600)
        
        # 设置外部数据加载器
        engine.set_extended_data_loader(futu_loader, bAutoTrans=False)
        
        engine.commitBTConfig()
        
        # 创建双均线策略实例
        strategy = DualMAHK(
            name='dual_ma_tencent',    # 策略实例名称
            code='HK.00700',          # 腾讯控股代码
            barCnt=50000,             # 要拉取的K线条数
            period='d',               # 使用日K线
            ma_short=5,               # 短期均线
            ma_long=10,               # 长期均线
            max_pos=1000,             # 最大持仓股数
            lot_size=100              # 每手股数
        )
        engine.set_cta_strategy(strategy)
        
        print("开始运行回测...")
        print(f"回测标的: 腾讯控股 (HK.00700)")
        print(f"回测时间: 2023-01-01 至 2025-06-21 (最近2年)")
        print(f"策略参数: MA短期={strategy.ma_short}, MA长期={strategy.ma_long}")
        
        # 运行回测
        engine.run_backtest()
        
        print("回测运行完成！")
        
        # 分析回测结果
        print("开始分析回测结果...")
        analyst = WtBtAnalyst()
        analyst.add_strategy('dual_ma_tencent', folder="./outputs_bt/", init_capital=1000000, rf=0.02, annual_trading_days=250)
        analyst.run_new()
        print("回测结果分析完成！")
        
        print("\n=== 腾讯控股双均线策略回测完成！ ===")
        print("回测结果保存在 ./outputs_bt/dual_ma_tencent/ 目录下")
        print("可以查看以下文件：")
        print("- funds.csv: 资金曲线")
        print("- trades.csv: 交易记录")
        print("- closes.csv: 平仓记录")
        print("- signals.csv: 信号记录")
        
    except Exception as e:
        print(f"回测过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 关闭富途数据连接
        print("\n正在关闭富途数据连接...")
        futu_loader.close()
        print("富途数据连接已关闭")

if __name__ == "__main__":
    main()