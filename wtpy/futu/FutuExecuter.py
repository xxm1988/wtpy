import threading
import time
from typing import Dict, Optional
from wtpy import BaseExtExecuter
import logging

try:
    from futu import *
except ImportError:
    print("请安装富途OpenAPI: pip install futu-api")
    raise

class FutuExecuter(BaseExtExecuter):
    """
    富途OpenAPI交易执行器
    支持港股和美股交易执行
    """
    
    def __init__(self, id: str, scale: float = 1.0, host: str = '127.0.0.1', port: int = 11111, 
                 unlock_pwd: str = '', is_simulate: bool = True):
        """
        初始化富途交易执行器
        
        Args:
            id: 执行器ID
            scale: 数量放大倍数
            host: 富途OpenD服务器地址
            port: 富途OpenD服务器端口
            unlock_pwd: 交易密码
            is_simulate: 是否为模拟交易
        """
        super().__init__(id, scale)
        self.__host__ = host
        self.__port__ = port
        self.__unlock_pwd__ = unlock_pwd
        self.__is_simulate__ = is_simulate
        self.__trade_ctx__ = None
        self.__is_connected__ = False
        self.__current_positions__: Dict[str, float] = {}
        self.__logger__ = logging.getLogger(f"FutuExecuter_{id}")
        
    def init(self):
        """
        初始化执行器
        """
        try:
            # 创建交易上下文
            if self.__is_simulate__:
                self.__trade_ctx__ = OpenSecTradeContext(
                    filter_trdmarket=TrdMarket.HK,  # 可以根据需要调整
                    host=self.__host__, 
                    port=self.__port__,
                    is_encrypt=False
                )
            else:
                self.__trade_ctx__ = OpenSecTradeContext(
                    filter_trdmarket=TrdMarket.HK,
                    host=self.__host__, 
                    port=self.__port__,
                    is_encrypt=True
                )
                
            # 解锁交易
            if self.__unlock_pwd__:
                ret, data = self.__trade_ctx__.unlock_trade(self.__unlock_pwd__)
                if ret != RET_OK:
                    self.__logger__.error(f"解锁交易失败: {data}")
                    return
                    
            # 获取账户信息
            ret, data = self.__trade_ctx__.get_acc_list()
            if ret == RET_OK:
                self.__is_connected__ = True
                self.__logger__.info(f"富途交易连接成功，账户列表: {data}")
                
                # 获取当前持仓
                self._update_positions()
            else:
                self.__logger__.error(f"获取账户列表失败: {data}")
                
        except Exception as e:
            self.__logger__.error(f"初始化富途交易执行器失败: {e}")
            self.__is_connected__ = False
            
    def set_position(self, stdCode: str, targetPos: float):
        """
        设置目标仓位
        
        Args:
            stdCode: 标准代码，如 HK.00700
            targetPos: 目标仓位
        """
        if not self.__is_connected__:
            self.__logger__.warning("未连接到富途交易服务，无法执行交易")
            return
            
        try:
            # 调用父类方法更新目标仓位
            super().set_position(stdCode, targetPos)
            
            # 获取当前仓位
            current_pos = self.__current_positions__.get(stdCode, 0.0)
            
            # 计算需要交易的数量
            diff = targetPos - current_pos
            
            if abs(diff) < 0.01:  # 忽略微小差异
                return
                
            # 执行交易
            if diff > 0:
                # 买入
                self._place_order(stdCode, abs(diff), TrdSide.BUY)
            else:
                # 卖出
                self._place_order(stdCode, abs(diff), TrdSide.SELL)
                
            self.__logger__.info(f"仓位调整: {stdCode}, 当前: {current_pos}, 目标: {targetPos}, 差异: {diff}")
            
        except Exception as e:
            self.__logger__.error(f"设置仓位时发生错误: {e}")
            
    def _place_order(self, code: str, qty: float, trd_side: TrdSide):
        """
        下单
        
        Args:
            code: 股票代码
            qty: 数量
            trd_side: 交易方向
        """
        try:
            # 获取当前价格
            quote_ctx = OpenQuoteContext(host=self.__host__, port=self.__port__)
            ret, data = quote_ctx.get_market_snapshot([code])
            quote_ctx.close()
            
            if ret != RET_OK:
                self.__logger__.error(f"获取价格失败: {code}, {data}")
                return
                
            if data.empty:
                self.__logger__.error(f"没有价格数据: {code}")
                return
                
            current_price = data.iloc[0]['last_price']
            
            # 计算下单价格（市价单使用当前价格）
            order_price = current_price
            
            # 下单
            ret, data = self.__trade_ctx__.place_order(
                price=order_price,
                qty=int(qty),
                code=code,
                trd_side=trd_side,
                order_type=OrderType.NORMAL,  # 普通订单
                trd_env=TrdEnv.SIMULATE if self.__is_simulate__ else TrdEnv.REAL
            )
            
            if ret == RET_OK:
                order_id = data['order_id'][0]
                self.__logger__.info(f"下单成功: {code}, 方向: {trd_side}, 数量: {qty}, 价格: {order_price}, 订单ID: {order_id}")
                
                # 更新本地仓位记录
                if trd_side == TrdSide.BUY:
                    self.__current_positions__[code] = self.__current_positions__.get(code, 0) + qty
                else:
                    self.__current_positions__[code] = self.__current_positions__.get(code, 0) - qty
            else:
                self.__logger__.error(f"下单失败: {code}, 错误: {data}")
                
        except Exception as e:
            self.__logger__.error(f"下单时发生错误: {e}")
            
    def _update_positions(self):
        """
        更新当前持仓信息
        """
        try:
            ret, data = self.__trade_ctx__.get_position_list(
                trd_env=TrdEnv.SIMULATE if self.__is_simulate__ else TrdEnv.REAL
            )
            
            if ret == RET_OK:
                self.__current_positions__.clear()
                for _, row in data.iterrows():
                    code = row['code']
                    qty = float(row['qty'])
                    self.__current_positions__[code] = qty
                    
                self.__logger__.info(f"持仓更新完成: {self.__current_positions__}")
            else:
                self.__logger__.error(f"获取持仓失败: {data}")
                
        except Exception as e:
            self.__logger__.error(f"更新持仓时发生错误: {e}")
            
    def get_position(self, code: str) -> float:
        """
        获取指定代码的当前仓位
        
        Args:
            code: 股票代码
            
        Returns:
            当前仓位数量
        """
        return self.__current_positions__.get(code, 0.0)
        
    def get_all_positions(self) -> Dict[str, float]:
        """
        获取所有持仓
        
        Returns:
            所有持仓字典
        """
        return self.__current_positions__.copy()
        
    def close(self):
        """
        关闭连接
        """
        if self.__trade_ctx__:
            try:
                self.__trade_ctx__.close()
                self.__is_connected__ = False
                self.__logger__.info("富途交易连接已关闭")
            except Exception as e:
                self.__logger__.error(f"关闭连接时发生错误: {e}")