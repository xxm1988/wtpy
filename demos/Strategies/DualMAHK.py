#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股双均线策略
当5日均线上穿10日均线时买入，下穿时卖出
"""

import numpy as np
import talib
from wtpy import BaseCtaStrategy, CtaContext

class DualMAHK(BaseCtaStrategy):
    """
    港股双均线策略
    
    策略逻辑：
    1. 计算5日和10日移动平均线
    2. 当5日均线上穿10日均线时买入
    3. 当5日均线下穿10日均线时卖出
    4. 包含基本的风险控制
    """
    
    def __init__(self, name: str, code: str, barCnt: int, period: str, ma_short: int = 5, ma_long: int = 10, max_pos: int = 1000, lot_size: int = 100):
        """
        策略初始化
        
        Args:
            name: 策略名称
            code: 交易代码，如HK.00700
            barCnt: K线数量
            period: K线周期
            ma_short: 短期均线周期，默认5
            ma_long: 长期均线周期，默认10
            max_pos: 最大持仓，默认1000股
            lot_size: 每手股数，港股通常为100股
        """
        BaseCtaStrategy.__init__(self, name)
        
        self.__code__ = code
        self.__bar_cnt__ = barCnt
        self.__period__ = period
        self.__ma_short__ = ma_short
        self.__ma_long__ = ma_long
        self.__max_pos__ = max_pos
        self.__lot_size__ = lot_size
        
        # 状态变量
        self.__last_ma_short__ = 0.0
        self.__last_ma_long__ = 0.0
        self.__last_signal__ = 0  # 0: 无信号, 1: 买入, -1: 卖出
        
    @property
    def code(self):
        """获取交易代码"""
        return self.__code__
        
    @property
    def ma_short(self):
        """获取短期均线周期"""
        return self.__ma_short__
        
    @property
    def ma_long(self):
        """获取长期均线周期"""
        return self.__ma_long__
        
    @property
    def max_pos(self):
        """获取最大持仓"""
        return self.__max_pos__
        
    def on_init(self, context: CtaContext):
        """
        策略初始化回调
        
        Args:
            context: 策略上下文
        """
        code = self.__code__
        print(f"=== 双均线策略初始化开始: {code} ===")
        print(f"策略参数: MA短期={self.__ma_short__}, MA长期={self.__ma_long__}")
        print(f"最大持仓: {self.__max_pos__}, 每手股数: {self.__lot_size__}")
        
        # 获取品种信息
        pInfo = context.stra_get_comminfo(code)
        print(f"品种信息: {pInfo}")
        
        # 准备K线数据，这是触发策略计算的关键
        print(f"准备K线数据: {code}, 周期: {self.__period__}, 条数: {self.__bar_cnt__}")
        context.stra_prepare_bars(code, self.__period__, self.__bar_cnt__, isMain=True)
        
        # 订阅K线事件，确保on_bar被调用
        context.stra_sub_bar_events(code, self.__period__)
        print(f"订阅K线事件: {code}, 周期: {self.__period__}")
        
        # 订阅tick数据
        context.stra_sub_ticks(code)
        print(f"订阅tick数据: {code}")
        
        # 获取并打印初始资金信息
        fund_data = context.stra_get_fund_data(0)  # 0-动态权益
        context.stra_log_text(f"初始资金: {fund_data}")
        
        print(f"=== 双均线策略初始化完成: {code} ===")
        
    def on_tick(self, context: CtaContext, stdCode: str, newTick):
        """
        tick数据回调
        
        Args:
            context: 策略上下文
            stdCode: 标准代码
            newTick: tick数据
        """
        # 可以在这里添加tick级别的逻辑
        pass
        
    def on_bar(self, context: CtaContext, stdCode: str, period: str, newBar: dict):
        """
        K线数据回调，这是策略的主要执行入口
        
        Args:
            context: 策略上下文
            stdCode: 标准代码
            period: K线周期
            newBar: 新的K线数据
        """
        print(f"*** on_bar被调用: {stdCode}, 周期: {period}, 时间: {context.stra_get_date()}{context.stra_get_time()} ***")
        
        if stdCode != self.__code__:
            print(f"代码不匹配，跳过: {stdCode} != {self.__code__}")
            return
            
        print(f"代码匹配，开始策略计算: {stdCode}")
        # 调用策略计算
        self.on_calculate(context)
        
    def on_calculate(self, context: CtaContext):
        """
        策略计算主函数
        
        Args:
            context: 策略上下文
        """
        code = self.__code__
        print(f"双均线策略计算开始: {code}, 当前时间: {context.stra_get_date()}{context.stra_get_time()}")
        
        # 获取日K线数据
        print(f"尝试获取K线数据: {code}, 周期: {self.__period__}, 条数: {self.__ma_long__ + 10}")
        kline = context.stra_get_bars(code, self.__period__, self.__ma_long__ + 10, isMain=True)
        
        if kline is None:
            print(f"无法获取K线数据: {code}")
            return
            
        print(f"获取到K线数据: {code}, 数据条数: {len(kline)}条")
        if len(kline) < self.__ma_long__ + 1:
            print(f"K线数据不足: {code}, 需要{self.__ma_long__ + 1}条，实际{len(kline)}条")
            return
            
        print(f"K线数据充足，开始计算均线: {code}")
        
        # 获取收盘价数据
        closes = kline.closes
        
        # 计算移动平均线
        ma_short_array = talib.SMA(closes, timeperiod=self.__ma_short__)
        ma_long_array = talib.SMA(closes, timeperiod=self.__ma_long__)
        
        # 获取最新的均线值
        current_ma_short = ma_short_array[-1]
        current_ma_long = ma_long_array[-1]
        prev_ma_short = ma_short_array[-2] if len(ma_short_array) >= 2 else 0
        prev_ma_long = ma_long_array[-2] if len(ma_long_array) >= 2 else 0
        
        # 检查均线数据有效性
        if np.isnan(current_ma_short) or np.isnan(current_ma_long):
            print(f"均线数据无效: {code}, MA{self.__ma_short__}={current_ma_short}, MA{self.__ma_long__}={current_ma_long}")
            return
            
        print(f"均线计算完成: {code}, MA{self.__ma_short__}={current_ma_short:.2f}, MA{self.__ma_long__}={current_ma_long:.2f}")
        
        # 获取当前价格和持仓
        current_price = closes[-1]
        current_pos = context.stra_get_position(code)
        
        # 判断均线交叉信号
        signal = 0
        
        # 金叉：短期均线上穿长期均线
        if (prev_ma_short <= prev_ma_long and current_ma_short > current_ma_long):
            signal = 1
            print(f"检测到金叉信号: {code}, MA{self.__ma_short__}({current_ma_short:.2f}) > MA{self.__ma_long__}({current_ma_long:.2f})")
            
        # 死叉：短期均线下穿长期均线
        elif (prev_ma_short >= prev_ma_long and current_ma_short < current_ma_long):
            signal = -1
            print(f"检测到死叉信号: {code}, MA{self.__ma_short__}({current_ma_short:.2f}) < MA{self.__ma_long__}({current_ma_long:.2f})")
            
        # 执行交易逻辑
        print(f"交易逻辑检查: current_pos={current_pos}, signal={signal}")
        
        if current_pos == 0:  # 无持仓
            if signal == 1:  # 金叉买入信号
                lots = self.__max_pos__ // self.__lot_size__
                print(f"计算买入数量: max_pos={self.__max_pos__}, lot_size={self.__lot_size__}, lots={lots}")
                if lots > 0:
                    print(f"准备执行买入操作...")
                    # 执行交易
                    context.stra_enter_long(code, lots * self.__lot_size__, "ma_cross_buy")
                    print(f"买入操作已执行: {code}, 数量{lots * self.__lot_size__}")
                    context.stra_log_text(f"金叉买入: {code}, 价格{current_price:.2f}, 数量{lots * self.__lot_size__}")
                    print(f"执行买入: {code}, 价格{current_price:.2f}, 数量{lots * self.__lot_size__}")
                    
                    # 验证持仓是否更新
                    new_pos = context.stra_get_position(code)
                    print(f"买入后持仓: {new_pos}")
                else:
                    print(f"买入数量为0，跳过交易: lots={lots}")
                    
        elif current_pos > 0:  # 持有多头
            if signal == -1:  # 死叉卖出信号
                print(f"当前持仓: {current_pos}, 准备卖出")
                print(f"准备执行卖出操作...")
                # 执行交易
                context.stra_exit_long(code, current_pos, "ma_cross_sell")
                print(f"卖出操作已执行: {code}, 数量{current_pos}")
                context.stra_log_text(f"死叉卖出: {code}, 价格{current_price:.2f}, 数量{current_pos}")
                print(f"执行卖出: {code}, 价格{current_price:.2f}, 数量{current_pos}")
                
                # 验证持仓是否更新
                new_pos = context.stra_get_position(code)
                print(f"卖出后持仓: {new_pos}")
        else:
            print(f"无交易条件满足: current_pos={current_pos}, signal={signal}")
                
        # 保存状态
        self.__last_ma_short__ = current_ma_short
        self.__last_ma_long__ = current_ma_long
        self.__last_signal__ = signal
        
        # 输出调试信息（每10个交易日输出一次）
        if context.stra_get_date() % 10 == 0:
            context.stra_log_text(
                f"价格:{current_price:.2f}, MA{self.__ma_short__}:{current_ma_short:.2f}, "
                f"MA{self.__ma_long__}:{current_ma_long:.2f}, 持仓:{current_pos}, 信号:{signal}"
            )
            
    def on_session_begin(self, context: CtaContext, curTDate: int):
        """
        交易日开始回调
        
        Args:
            context: 策略上下文
            curTDate: 当前交易日
        """
        context.stra_log_text(f"交易日开始: {curTDate}")
        
    def on_session_end(self, context: CtaContext, curTDate: int):
        """
        交易日结束回调
        
        Args:
            context: 策略上下文
            curTDate: 当前交易日
        """
        current_pos = context.stra_get_position(self.__code__)
        context.stra_log_text(f"交易日结束: {curTDate}, 当前持仓: {current_pos}")