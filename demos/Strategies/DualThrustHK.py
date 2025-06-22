#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
港股DualThrust策略
专门针对港股市场特点优化的DualThrust策略
支持腾讯控股等港股标的交易
"""

from wtpy import BaseCtaStrategy, CtaContext
import numpy as np
import talib

class StraDualThrustHK(BaseCtaStrategy):
    """
    港股DualThrust策略类
    针对港股市场的交易时间和特点进行优化
    """
    
    def __init__(self, name: str, code: str, barCnt: int, period: str, days: int, 
                 k1: float, k2: float, max_pos: int = 1000, stop_loss: float = 0.05):
        """
        初始化港股DualThrust策略
        
        Args:
            name: 策略名称
            code: 港股代码（如HK.00700）
            barCnt: K线数量
            period: K线周期
            days: 历史数据天数
            k1: 上轨系数
            k2: 下轨系数
            max_pos: 最大持仓手数
            stop_loss: 止损比例
        """
        BaseCtaStrategy.__init__(self, name)
        
        self.__days__ = days
        self.__k1__ = k1
        self.__k2__ = k2
        self.__period__ = period
        self.__bar_cnt__ = barCnt
        self.__code__ = code
        self.__max_pos__ = max_pos
        self.__stop_loss__ = stop_loss
        
        # 港股交易参数
        self.__lot_size__ = 100  # 港股每手股数
        self.__min_change__ = 0.01  # 最小价格变动
        
        # 策略状态变量
        self.__last_entry_price__ = 0.0
        self.__last_signal__ = 0
        
    @property
    def days(self):
        """获取历史数据天数"""
        return self.__days__
        
    @property
    def k1(self):
        """获取上轨系数"""
        return self.__k1__
        
    @property
    def k2(self):
        """获取下轨系数"""
        return self.__k2__
        
    @property
    def period(self):
        """获取K线周期"""
        return self.__period__
        
    @property
    def code(self):
        """获取交易代码"""
        return self.__code__
        
    @property
    def max_pos(self):
        """获取最大持仓"""
        return self.__max_pos__
        
    def on_init(self, context: CtaContext):
        """
        策略初始化
        
        Args:
            context: 策略上下文
        """
        code = self.__code__
        print(f"策略初始化开始: {code}")
        
        # 获取品种信息
        pInfo = context.stra_get_comminfo(code)
        if pInfo is not None:
            context.stra_log_text(f"品种信息: {pInfo}")
            print(f"品种信息: {pInfo}")
        else:
            print(f"无法获取品种信息: {code}")
            
        # 准备K线数据
        context.stra_prepare_bars(code, self.__period__, self.__bar_cnt__, isMain=True)
        print(f"准备K线数据: {code}, 周期: {self.__period__}, 条数: {self.__bar_cnt__}")
        
        # 准备K线数据，这是触发策略计算的关键
        context.stra_prepare_bars(code, self.__period__, self.__bar_cnt__, isMain=True)
        # 订阅tick数据
        context.stra_sub_ticks(code)
        print(f"订阅tick数据: {code}")
        
        context.stra_log_text(f"港股DualThrust策略初始化完成: {code}")
        print(f"港股DualThrust策略初始化完成: {code}")
        
        # 读取存储的数据
        self.__last_entry_price__ = context.user_load_data('last_entry_price', 0.0)
        self.__last_signal__ = context.user_load_data('last_signal', 0)
        
    def on_tick(self, context: CtaContext, stdCode: str, newTick: dict):
        """
        tick数据回调
        
        Args:
            context: 策略上下文
            stdCode: 标准代码
            newTick: tick数据
        """
        # 可以在这里添加tick级别的逻辑
        pass
    
    def on_calculate(self, context: CtaContext):
        """
        策略计算主函数
        
        Args:
            context: 策略上下文
        """
        code = self.__code__
        print(f"策略计算开始: {code}, 当前时间: {context.stra_get_date()}{context.stra_get_time()}")
        
        # 获取K线数据
        print(f"尝试获取K线数据: {code}, 周期: {self.__period__}, 天数: {self.__days__}")
        kline = context.stra_get_bars(code, self.__period__, self.__days__, isMain=True)
        
        if kline is None:
            print(f"无法获取K线数据: {code}")
            return
            
        print(f"获取到K线数据: {code}, 数据条数: {len(kline)}条")
        if len(kline) < self.__days__:
            print(f"K线数据不足: {code}, 需要{self.__days__}条，实际{len(kline)}条")
            return
            
        print(f"K线数据充足，开始计算指标: {code}")
        # 打印最近几条数据用于调试
        if len(kline) > 0:
            print(f"最新K线数据: 时间={kline.times[-1]}, 开盘={kline.opens[-1]}, 最高={kline.highs[-1]}, 最低={kline.lows[-1]}, 收盘={kline.closes[-1]}")
            
        # 计算技术指标
        closes = kline.closes[-self.__days__:]
        highs = kline.highs[-self.__days__:]
        lows = kline.lows[-self.__days__:]
        
        if len(closes) < self.__days__:
            return
            
        # 计算DualThrust指标
        hh = np.max(highs[:-1])  # 前N-1天的最高价
        ll = np.min(lows[:-1])   # 前N-1天的最低价
        hc = np.max(closes[:-1]) # 前N-1天的最高收盘价
        lc = np.min(closes[:-1]) # 前N-1天的最低收盘价
        
        # 计算波动范围
        range1 = hh - lc
        range2 = hc - ll
        range_val = max(range1, range2)
        
        # 计算上下轨
        current_open = kline.opens[-1]
        upper_band = current_open + self.__k1__ * range_val
        lower_band = current_open - self.__k2__ * range_val
        
        current_price = closes[-1]
        current_pos = context.stra_get_position(code)
        
        # 添加移动平均线过滤
        ma20 = talib.SMA(closes, timeperiod=20)[-1] if len(closes) >= 20 else current_price
        
        # 交易信号逻辑
        signal = 0
        
        # 多头信号：价格突破上轨且在均线之上
        if current_price > upper_band and current_price > ma20:
            signal = 1
            
        # 空头信号：价格跌破下轨且在均线之下
        elif current_price < lower_band and current_price < ma20:
            signal = -1
            
        # 止损逻辑
        if current_pos != 0 and self.__last_entry_price__ > 0:
            if current_pos > 0:  # 多头持仓
                if current_price < self.__last_entry_price__ * (1 - self.__stop_loss__):
                    signal = 0  # 止损平仓
                    context.stra_log_text(f"多头止损: 入场价{self.__last_entry_price__:.2f}, 当前价{current_price:.2f}")
            elif current_pos < 0:  # 空头持仓
                if current_price > self.__last_entry_price__ * (1 + self.__stop_loss__):
                    signal = 0  # 止损平仓
                    context.stra_log_text(f"空头止损: 入场价{self.__last_entry_price__:.2f}, 当前价{current_price:.2f}")
        
        # 执行交易
        target_pos = 0
        if signal == 1:  # 做多
            target_pos = self.__max_pos__
        elif signal == -1:  # 做空（港股不支持做空，这里仅作演示）
            target_pos = 0  # 港股市场通常不支持做空
        elif signal == 0:  # 平仓
            target_pos = 0
            
        # 执行交易逻辑
        if current_pos == 0:  # 无持仓
            if signal == 1:  # 做多信号
                lots = self.__max_pos__ // self.__lot_size__
                if lots > 0:
                    context.stra_enter_long(code, lots * self.__lot_size__, "enterlong")
                    self.__last_entry_price__ = current_price
                    context.stra_log_text(f"多头开仓: 价格{current_price:.2f}, 上轨{upper_band:.2f}, 数量{lots * self.__lot_size__}")
        elif current_pos > 0:  # 持有多头
            if signal == -1 or signal == 0:  # 平仓信号
                context.stra_exit_long(code, current_pos, "exitlong")
                context.stra_log_text(f"多头平仓: 价格{current_price:.2f}, 下轨{lower_band:.2f}, 数量{current_pos}")
                 
        # 保存状态（在有交易时）
        if signal != self.__last_signal__:
            context.user_save_data('last_entry_price', self.__last_entry_price__)
            context.user_save_data('last_signal', signal)
            self.__last_signal__ = signal
        
        # 输出调试信息
        if context.stra_get_date() % 100 == 0:  # 每100个周期输出一次
            context.stra_log_text(
                f"价格:{current_price:.2f}, 上轨:{upper_band:.2f}, 下轨:{lower_band:.2f}, "
                f"MA20:{ma20:.2f}, 持仓:{current_pos}, 信号:{signal}"
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
        # 可以在这里添加日终处理逻辑
        current_pos = context.stra_get_position(self.__code__)
        context.stra_log_text(f"交易日结束: {curTDate}, 当前持仓: {current_pos}")