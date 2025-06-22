import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from wtpy.ExtModuleDefs import BaseExtDataLoader
import logging

try:
    from futu import *
except ImportError:
    print("请安装富途OpenAPI: pip install futu-api")
    raise

class FutuDataLoader(BaseExtDataLoader):
    """
    富途OpenAPI历史数据加载器
    支持港股和美股历史数据加载
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 11111):
        """
        初始化富途数据加载器
        
        Args:
            host: 富途OpenD服务器地址
            port: 富途OpenD服务器端口
        """
        super().__init__()
        self.__host__ = host
        self.__port__ = port
        self.__quote_ctx__ = None
        self.__logger__ = logging.getLogger("FutuDataLoader")
        
    def init(self):
        """
        初始化数据加载器
        """
        try:
            self.__quote_ctx__ = OpenQuoteContext(host=self.__host__, port=self.__port__)
            
            # 简单测试连接是否成功建立
            self.__logger__.info(f"富途数据加载器连接成功: {self.__host__}:{self.__port__}")
            print(f"富途数据加载器连接成功: {self.__host__}:{self.__port__}")
            return True
                
        except Exception as e:
            self.__logger__.error(f"初始化富途数据加载器失败: {e}")
            return False
            
    def load_bars(self, code: str, period: str, start_date: str, end_date: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """
        加载K线数据
        
        Args:
            code: 股票代码，如 HK.00700
            period: 周期，支持 '1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            count: 最大条数
            
        Returns:
            K线数据DataFrame
        """
        if not self.__quote_ctx__:
            self.__logger__.error("数据加载器未初始化")
            return None
            
        try:
            # 转换周期格式
            ktype = self._convert_period(period)
            if not ktype:
                self.__logger__.error(f"不支持的周期格式: {period}")
                return None
                
            # 加载历史K线
            print(f"正在从富途API获取K线数据: {code}, 周期: {period}, 时间范围: {start_date} 至 {end_date}")
            self.__logger__.info(f"请求K线数据: {code}, 周期: {period}, 时间范围: {start_date} 至 {end_date}")
            
            ret, data, page_req_key = self.__quote_ctx__.request_history_kline(
                code=code,
                start=start_date,
                end=end_date,
                ktype=ktype,
                autype=AuType.QFQ,  # 前复权
                max_count=count
            )
            
            if ret != RET_OK:
                error_msg = f"加载K线数据失败: {code}, 错误: {data}"
                self.__logger__.error(error_msg)
                print(error_msg)
                return None
                
            if data.empty:
                warning_msg = f"没有K线数据: {code}"
                self.__logger__.warning(warning_msg)
                print(warning_msg)
                return None
                
            # 转换为wtpy格式
            df = self._convert_to_wtpy_format(data)
            success_msg = f"成功加载K线数据: {code}, 周期: {period}, 条数: {len(df)}"
            self.__logger__.info(success_msg)
            print(success_msg)
            return df
            
        except Exception as e:
            self.__logger__.error(f"加载K线数据时发生错误: {e}")
            return None
            
    def load_ticks(self, code: str, date: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """
        加载Tick数据
        
        Args:
            code: 股票代码
            date: 日期，格式 'YYYY-MM-DD'
            count: 最大条数
            
        Returns:
            Tick数据DataFrame
        """
        if not self.__quote_ctx__:
            self.__logger__.error("数据加载器未初始化")
            return None
            
        try:
            # 富途API获取分时数据
            ret, data = self.__quote_ctx__.get_rt_ticker(code, count)
            
            if ret != RET_OK:
                self.__logger__.error(f"加载Tick数据失败: {code}, 错误: {data}")
                return None
                
            if data.empty:
                self.__logger__.warning(f"没有Tick数据: {code}")
                return None
                
            # 转换为wtpy格式
            df = self._convert_ticks_to_wtpy_format(data)
            self.__logger__.info(f"成功加载Tick数据: {code}, 日期: {date}, 条数: {len(df)}")
            return df
            
        except Exception as e:
            self.__logger__.error(f"加载Tick数据时发生错误: {e}")
            return None
            
    def get_trading_calendar(self, market: str, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日历
        
        Args:
            market: 市场，'HK' 或 'US'
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表
        """
        if not self.__quote_ctx__:
            return []
            
        try:
            market_enum = Market.HK if market == 'HK' else Market.US
            ret, data = self.__quote_ctx__.get_trading_days(market_enum, start_date, end_date)
            
            if ret == RET_OK:
                return data['time'].tolist()
            else:
                self.__logger__.error(f"获取交易日历失败: {data}")
                return []
                
        except Exception as e:
            self.__logger__.error(f"获取交易日历时发生错误: {e}")
            return []
            
    def _convert_period(self, period: str) -> Optional[str]:
        """
        转换周期格式
        
        Args:
            period: wtpy周期格式
            
        Returns:
            富途周期格式
        """
        period_mapping = {
            'm1': KLType.K_1M,
            'm5': KLType.K_5M,
            'm15': KLType.K_15M,
            'm30': KLType.K_30M,
            'h1': KLType.K_60M,
            'd1': KLType.K_DAY,
            'w1': KLType.K_WEEK,
            'M1': KLType.K_MON,
            # 兼容其他格式
            '1m': KLType.K_1M,
            '5m': KLType.K_5M,
            '15m': KLType.K_15M,
            '30m': KLType.K_30M,
            '1h': KLType.K_60M,
            '1d': KLType.K_DAY,
            '1w': KLType.K_WEEK,
            '1M': KLType.K_MON
        }
        return period_mapping.get(period)
        
    def _convert_to_wtpy_format(self, futu_data: pd.DataFrame) -> pd.DataFrame:
        """
        将富途K线数据转换为wtpy格式
        
        Args:
            futu_data: 富途K线数据
            
        Returns:
            wtpy格式的K线数据
        """
        try:
            df = pd.DataFrame()
            
            # 时间转换
            time_dt = pd.to_datetime(futu_data['time_key'])
            df['time'] = time_dt.dt.strftime('%Y%m%d%H%M%S').astype('int64')
            df['date'] = time_dt.dt.strftime('%Y%m%d').astype('int32')
            
            # OHLCV数据
            df['open'] = futu_data['open'].astype(float)
            df['high'] = futu_data['high'].astype(float)
            df['low'] = futu_data['low'].astype(float)
            df['close'] = futu_data['close'].astype(float)
            df['volume'] = futu_data['volume'].astype(int)
            
            # 成交额
            if 'turnover' in futu_data.columns:
                df['turnover'] = futu_data['turnover'].astype(float)
            else:
                df['turnover'] = 0.0
                
            # 持仓量（股票没有，设为0）
            df['interest'] = 0
            
            return df.sort_values('time').reset_index(drop=True)
            
        except Exception as e:
            self.__logger__.error(f"转换K线数据格式时发生错误: {e}")
            return pd.DataFrame()
            
    def _convert_ticks_to_wtpy_format(self, futu_data: pd.DataFrame) -> pd.DataFrame:
        """
        将富途Tick数据转换为wtpy格式
        
        Args:
            futu_data: 富途Tick数据
            
        Returns:
            wtpy格式的Tick数据
        """
        try:
            df = pd.DataFrame()
            
            # 时间转换
            time_dt = pd.to_datetime(futu_data['time'])
            df['time'] = time_dt.dt.strftime('%Y%m%d%H%M%S').astype('int64')
            df['date'] = time_dt.dt.strftime('%Y%m%d').astype('int32')
            
            # 价格数据
            df['price'] = futu_data['price'].astype(float)
            df['volume'] = futu_data['volume'].astype(int)
            df['turnover'] = futu_data['turnover'].astype(float) if 'turnover' in futu_data.columns else 0.0
            
            # 买卖方向
            df['direction'] = futu_data['direction'] if 'direction' in futu_data.columns else 0
            
            return df.sort_values('time').reset_index(drop=True)
            
        except Exception as e:
            self.__logger__.error(f"转换Tick数据格式时发生错误: {e}")
            return pd.DataFrame()
            
    def load_final_his_bars(self, stdCode: str, period: str, feeder) -> bool:
        """
        加载最终历史K线（回测、实盘）
        该接口用于加载外部处理好的复权数据、主力合约数据
        
        Args:
            stdCode: 合约代码，格式如HK.00700
            period: 周期，m1/m5/d1等
            feeder: 回调函数，feed_raw_bars(bars:POINTER(WTSBarStruct), count:int)
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.__logger__.info(f"开始加载最终历史K线: {stdCode}, 周期: {period}")
            
            # 计算时间范围（默认加载最近2年数据）
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
            
            # 加载K线数据
            df = self.load_bars(stdCode, period, start_date, end_date, count=10000)
            if df is None or df.empty:
                self.__logger__.warning(f"未获取到K线数据: {stdCode}")
                return False
                
            # 转换为WTSBarStruct格式并调用feeder
            bars_data = self._convert_to_wts_bars(df)
            if bars_data is not None:
                count = len(df)
                feeder(bars_data, count)
                self.__logger__.info(f"成功加载最终历史K线: {stdCode}, 条数: {count}")
                return True
            else:
                self.__logger__.warning(f"转换K线数据失败: {stdCode}")
                return False
                
        except Exception as e:
            self.__logger__.error(f"加载最终历史K线时发生错误: {e}")
            return False
            
    def load_raw_his_bars(self, stdCode: str, period: str, feeder) -> bool:
        """
        加载未加工的历史K线（回测、实盘）
        该接口用于加载原始的K线数据，如未复权数据和分月合约数据
        
        Args:
            stdCode: 合约代码，格式如HK.00700
            period: 周期，m1/m5/d1等
            feeder: 回调函数，feed_raw_bars(bars:POINTER(WTSBarStruct), count:int)
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.__logger__.info(f"开始加载原始历史K线: {stdCode}, 周期: {period}")
            
            # 对于港股，原始数据和最终数据相同（富途已处理复权）
            return self.load_final_his_bars(stdCode, period, feeder)
                
        except Exception as e:
            self.__logger__.error(f"加载原始历史K线时发生错误: {e}")
            return False
            
    def load_his_ticks(self, stdCode: str, uDate: int, feeder) -> bool:
        """
        加载历史Tick数据（只在回测有效，实盘只提供当日落地的）
        
        Args:
            stdCode: 合约代码，格式如HK.00700
            uDate: 日期，格式如20231201
            feeder: 回调函数，feed_raw_ticks(ticks:POINTER(WTSTickStruct), count:int)
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.__logger__.info(f"开始加载历史Tick数据: {stdCode}, 日期: {uDate}")
            
            # 将日期格式转换为YYYY-MM-DD
            date_str = f"{uDate//10000:04d}-{(uDate//100)%100:02d}-{uDate%100:02d}"
            
            # 加载Tick数据
            df = self.load_ticks(stdCode, date_str)
            if df is None or df.empty:
                self.__logger__.warning(f"未获取到Tick数据: {stdCode}, 日期: {date_str}")
                return False
                
            # 转换为WTSTickStruct格式并调用feeder
            ticks_data = self._convert_to_wts_ticks(df)
            if ticks_data and len(ticks_data) > 0:
                feeder(ticks_data, len(ticks_data))
                self.__logger__.info(f"成功加载历史Tick数据: {stdCode}, 条数: {len(ticks_data)}")
                return True
            else:
                self.__logger__.warning(f"转换Tick数据失败: {stdCode}")
                return False
                
        except Exception as e:
            self.__logger__.error(f"加载历史Tick数据时发生错误: {e}")
            return False
            
    def load_adj_factors(self, stdCode: str = "", feeder = None) -> bool:
        """
        加载复权因子
        
        Args:
            stdCode: 合约代码，格式如HK.00700，如果为空则加载全部除权数据
            feeder: 回调函数，feed_adj_factors(stdCode:str, dates:list, factors:list)
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.__logger__.info(f"开始加载复权因子: {stdCode}")
            
            # 富途API暂不直接提供复权因子接口，这里返回False
            # 实际的复权处理已在load_bars中通过AuType.QFQ参数处理
            self.__logger__.warning("富途API暂不支持直接获取复权因子，复权处理已在K线数据中完成")
            return False
                
        except Exception as e:
            self.__logger__.error(f"加载复权因子时发生错误: {e}")
            return False
            
    def _convert_to_wts_bars(self, df: pd.DataFrame):
        """
        将DataFrame转换为WTSBarStruct格式
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            WTSBarStruct数组
        """
        try:
            from wtpy.WtCoreDefs import WTSBarStruct
            from ctypes import POINTER
            
            if df.empty:
                return None
                
            # 创建WTSBarStruct数组
            BUFFER = WTSBarStruct * len(df)
            buffer = BUFFER()
            
            # 填充数据
            for i, row in df.iterrows():
                bar = buffer[i]
                bar.date = int(row['date'])
                bar.time = int(row['time'])
                bar.open = float(row['open'])
                bar.high = float(row['high'])
                bar.low = float(row['low'])
                bar.close = float(row['close'])
                bar.vol = float(row['volume'])
                bar.money = float(row.get('turnover', 0.0))
                bar.hold = float(row.get('interest', 0.0))
                bar.settle = 0.0
                bar.diff = 0.0
                bar.reserve = 0
                
            return buffer
            
        except Exception as e:
            self.__logger__.error(f"转换WTSBarStruct时发生错误: {e}")
            return None
        
    def _convert_to_wts_ticks(self, df: pd.DataFrame):
        """
        将DataFrame转换为WTSTickStruct格式
        
        Args:
            df: Tick数据DataFrame
            
        Returns:
            转换后的数据结构
        """
        # 这里需要根据wtpy的具体数据结构进行转换
        # 暂时返回DataFrame，实际使用时可能需要进一步转换
        return df.to_dict('records')
        
    def close(self):
        """
        关闭连接
        """
        if self.__quote_ctx__:
            try:
                self.__quote_ctx__.close()
                self.__logger__.info("富途数据加载器连接已关闭")
            except Exception as e:
                self.__logger__.error(f"关闭连接时发生错误: {e}")
                
    def __del__(self):
        """
        析构函数
        """
        self.close()