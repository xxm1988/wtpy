#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
港股实盘交易演示
使用富途OpenAPI进行腾讯控股实盘交易
"""

from wtpy import WtEngine, EngineType
from wtpy.futu import FutuParser, FutuExecuter

import sys
sys.path.append('../Strategies')
from DualThrustHK import StraDualThrustHK

def main():
    """
    主函数 - 启动港股实盘交易
    """
    # 创建实盘交易引擎
    engine = WtEngine(EngineType.ET_CTA)
    engine.init('../common/', 'config.yaml')
    
    # 添加富途行情解析器
    futu_parser = FutuParser(
        id="futu_parser",
        host="127.0.0.1",
        port=11111
    )
    engine.add_exetended_parser(futu_parser)
    
    # 添加富途交易执行器
    futu_executer = FutuExecuter(
        id="futu_executer",
        scale=1.0,
        host="127.0.0.1",
        port=11111,
        unlock_pwd="your_trade_password",  # 请替换为实际的交易密码
        is_simulate=True  # 设置为False进行真实交易
    )
    engine.add_exetended_executer(futu_executer)
    
    # 创建腾讯控股交易策略
    strategy = StraDualThrustHK(
        name='dt_tencent_live',
        code='HK.00700',
        barCnt=50,
        period='m5',
        days=30,
        k1=0.7,
        k2=0.7,
        max_pos=500,  # 实盘建议减少仓位
        stop_loss=0.03  # 实盘建议更严格的止损
    )
    engine.add_cta_strategy(strategy)
    
    # 启动引擎
    engine.run()
    
    print("港股实盘交易引擎已启动")
    print("按 Ctrl+C 停止交易")
    
    try:
        # 保持程序运行
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止交易引擎...")
        engine.release()
        print("交易引擎已停止")

if __name__ == "__main__":
    main()