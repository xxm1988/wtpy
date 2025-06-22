import threading
import time
from typing import Dict, Set
from wtpy import BaseExtParser, WTSTickStruct
from ctypes import byref
import logging

try:
    from futu import *
except ImportError:
    print("请安装富途OpenAPI: pip install futu-api")
    raise

class FutuParser(BaseExtParser):
    """
    富途OpenAPI数据解析器
    支持港股和美股实时行情接收
    """
    
    def __init__(self, id: str, host: str = '127.0.0.1', port: int = 11111):
        """
        初始化富途数据解析器
        
        Args:
            id: 解析器ID
            host: 富途OpenD服务器地址
            port: 富途OpenD服务器端口
        """
        super().__init__(id)
        self.__host__ = host
        self.__port__ = port
        self.__quote_ctx__ = None
        self.__subscribed_codes__: Set[str] = set()
        self.__code_mapping__: Dict[str, str] = {}  # wtpy代码 -> 富途代码映射
        self.__is_connected__ = False
        self.__logger__ = logging.getLogger(f"FutuParser_{id}")
        
    def init(self, engine):
        """
        初始化解析器
        
        Args:
            engine: WtEngine实例
        """
        super().init(engine)
        self.__logger__.info(f"富途数据解析器 {self.id()} 初始化完成")
        
    def connect(self):
        """
        连接富途OpenD服务
        """
        try:
            self.__quote_ctx__ = OpenQuoteContext(host=self.__host__, port=self.__port__)
            
            # 设置行情回调
            self.__quote_ctx__.set_handler(StockQuoteHandlerBase(self._on_quote_callback))
            
            # 测试连接
            ret, data = self.__quote_ctx__.get_market_state([Market.HK, Market.US])
            if ret == RET_OK:
                self.__is_connected__ = True
                self.__logger__.info(f"富途OpenD连接成功: {self.__host__}:{self.__port__}")
                self.__logger__.info(f"市场状态: {data}")
            else:
                self.__logger__.error(f"获取市场状态失败: {data}")
                
        except Exception as e:
            self.__logger__.error(f"连接富途OpenD失败: {e}")
            self.__is_connected__ = False
            
    def disconnect(self):
        """
        断开连接
        """
        if self.__quote_ctx__:
            try:
                # 取消所有订阅
                for futu_code in self.__subscribed_codes__.copy():
                    self.__quote_ctx__.unsubscribe(futu_code, [SubType.QUOTE])
                    
                self.__quote_ctx__.close()
                self.__is_connected__ = False
                self.__logger__.info("富途OpenD连接已断开")
            except Exception as e:
                self.__logger__.error(f"断开连接时发生错误: {e}")
                
    def release(self):
        """
        释放资源
        """
        self.disconnect()
        self.__logger__.info("富途数据解析器资源已释放")
        
    def subscribe(self, fullCode: str):
        """
        订阅实时行情
        
        Args:
            fullCode: wtpy格式的合约代码，如 HK.00700 或 US.AAPL
        """
        if not self.__is_connected__:
            self.__logger__.warning("未连接到富途OpenD，无法订阅")
            return
            
        try:
            futu_code = self._convert_to_futu_code(fullCode)
            if not futu_code:
                self.__logger__.error(f"无法转换代码格式: {fullCode}")
                return
                
            ret, err_msg = self.__quote_ctx__.subscribe(futu_code, [SubType.QUOTE])
            if ret == RET_OK:
                self.__subscribed_codes__.add(futu_code)
                self.__code_mapping__[fullCode] = futu_code
                self.__logger__.info(f"订阅成功: {fullCode} -> {futu_code}")
            else:
                self.__logger__.error(f"订阅失败: {fullCode}, 错误: {err_msg}")
                
        except Exception as e:
            self.__logger__.error(f"订阅时发生错误: {e}")
            
    def unsubscribe(self, fullCode: str):
        """
        取消订阅
        
        Args:
            fullCode: wtpy格式的合约代码
        """
        if not self.__is_connected__:
            return
            
        try:
            if fullCode in self.__code_mapping__:
                futu_code = self.__code_mapping__[fullCode]
                ret, err_msg = self.__quote_ctx__.unsubscribe(futu_code, [SubType.QUOTE])
                if ret == RET_OK:
                    self.__subscribed_codes__.discard(futu_code)
                    del self.__code_mapping__[fullCode]
                    self.__logger__.info(f"取消订阅成功: {fullCode}")
                else:
                    self.__logger__.error(f"取消订阅失败: {fullCode}, 错误: {err_msg}")
                    
        except Exception as e:
            self.__logger__.error(f"取消订阅时发生错误: {e}")
            
    def _convert_to_futu_code(self, wtpy_code: str) -> str:
        """
        将wtpy格式代码转换为富途格式
        
        Args:
            wtpy_code: wtpy格式代码，如 HK.00700 或 US.AAPL
            
        Returns:
            富途格式代码，如 HK.00700 或 US.AAPL
        """
        # 富途和wtpy的代码格式基本一致，直接返回
        return wtpy_code
        
    def _convert_to_wtpy_code(self, futu_code: str) -> str:
        """
        将富途格式代码转换为wtpy格式
        
        Args:
            futu_code: 富途格式代码
            
        Returns:
            wtpy格式代码
        """
        # 查找映射表中的wtpy代码
        for wtpy_code, mapped_futu_code in self.__code_mapping__.items():
            if mapped_futu_code == futu_code:
                return wtpy_code
        return futu_code
        
    def _on_quote_callback(self, data):
        """
        行情数据回调函数
        
        Args:
            data: 富途行情数据
        """
        try:
            if data is None or data.empty:
                return
                
            for _, row in data.iterrows():
                # 创建wtpy tick结构
                tick = WTSTickStruct()
                
                # 转换代码格式
                wtpy_code = self._convert_to_wtpy_code(row['code'])
                code_parts = wtpy_code.split('.')
                if len(code_parts) >= 2:
                    tick.exchg = bytes(code_parts[0], encoding="UTF8")
                    tick.code = bytes(code_parts[1], encoding="UTF8")
                else:
                    continue
                    
                # 填充价格数据
                tick.price = float(row.get('last_price', 0))
                tick.open = float(row.get('open_price', 0))
                tick.high = float(row.get('high_price', 0))
                tick.low = float(row.get('low_price', 0))
                tick.settle = float(row.get('prev_close_price', 0))
                
                # 填充成交量和成交额
                tick.total_volume = int(row.get('volume', 0))
                tick.total_turnover = float(row.get('turnover', 0))
                
                # 填充买卖盘数据
                tick.bid_prices = [float(row.get('bid_price', 0))]
                tick.ask_prices = [float(row.get('ask_price', 0))]
                tick.bid_qty = [int(row.get('bid_vol', 0))]
                tick.ask_qty = [int(row.get('ask_vol', 0))]
                
                # 填充时间戳
                tick.action_date = int(time.strftime('%Y%m%d'))
                tick.action_time = int(time.strftime('%H%M%S')) * 1000
                tick.trading_date = tick.action_date
                
                # 推送到引擎
                if hasattr(self, '_BaseExtParser__engine__') and self._BaseExtParser__engine__:
                    self._BaseExtParser__engine__.push_quote_from_extended_parser(
                        self.id(), byref(tick), True
                    )
                    
        except Exception as e:
            self.__logger__.error(f"处理行情回调时发生错误: {e}")

class StockQuoteHandlerBase:
    """
    富途行情回调处理器基类
    """
    
    def __init__(self, callback_func):
        self.callback_func = callback_func
        
    def on_recv_rsp(self, rsp_pb):
        """
        接收行情推送
        """
        if self.callback_func:
            self.callback_func(rsp_pb)