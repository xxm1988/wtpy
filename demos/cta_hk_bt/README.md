# 港股回测演示 - 腾讯控股DualThrust策略

本演示展示了如何使用Wondertrade量化框架进行港股回测，以腾讯控股(00700.HK)为例，使用富途OpenAPI作为数据源。

## 功能特点

- 支持港股市场数据接入
- 使用富途OpenAPI获取历史数据
- 针对港股交易特点优化的DualThrust策略
- 完整的回测分析和可视化

## 文件说明

- `runBT.py` - 主回测脚本
- `configbt.yaml` - 回测配置文件
- `logcfgbt.yaml` - 日志配置文件
- `README.md` - 说明文档

## 环境准备

### 1. 安装依赖

```bash
# 安装富途OpenAPI
pip install futu-api

# 安装分析工具（可选）
pip install pyfolio
```

### 2. 启动富途OpenD

1. 下载并安装富途牛牛客户端
2. 启动富途OpenD程序
3. 确保OpenD在127.0.0.1:11111端口运行

### 3. 数据准备

确保以下配置文件存在：
- `../common/hk_us_contracts.json` - 港美股合约信息
- `../common/hk_us_commodities.json` - 港美股品种信息
- `../common/hk_us_sessions.json` - 港美股交易时段
- `../common/fees_hk.json` - 港股佣金配置

## 运行回测

```bash
cd demos/cta_hk_bt
python runBT.py
```

## 策略参数

### DualThrustHK策略参数

- `code`: 股票代码 (HK.00700 - 腾讯控股)
- `period`: K线周期 (m5 - 5分钟)
- `days`: 历史数据天数 (30天)
- `k1`: 上轨系数 (0.7)
- `k2`: 下轨系数 (0.7)
- `max_pos`: 最大持仓股数 (1000股)
- `stop_loss`: 止损比例 (5%)

### 回测时间范围

- 开始时间: 2023年1月1日 09:30
- 结束时间: 2023年12月31日 16:00
- 初始资金: 500,000 港币

## 策略逻辑

### DualThrust指标计算

1. 计算前N天的最高价(HH)、最低价(LL)
2. 计算前N天的最高收盘价(HC)、最低收盘价(LC)
3. 计算波动范围: Range = Max(HH-LC, HC-LL)
4. 计算上下轨:
   - 上轨 = 开盘价 + K1 × Range
   - 下轨 = 开盘价 - K2 × Range

### 交易信号

- **买入信号**: 价格突破上轨且高于20日均线
- **卖出信号**: 价格跌破下轨且低于20日均线
- **止损**: 亏损超过5%时强制平仓

### 港股交易特点

- 每手100股
- 最小价格变动0.01港币
- 不支持做空（策略中已处理）
- 交易时间: 09:30-12:00, 13:00-16:00

## 回测结果

回测完成后，结果保存在 `./outputs_bt/dt_tencent/` 目录下：

- `funds.csv` - 资金曲线数据
- `trades.csv` - 交易记录
- `closes.csv` - 平仓记录
- `signals.csv` - 信号记录
- `summary.json` - 回测统计摘要

## 性能分析

### 使用WtBtAnalyst

```python
from wtpy.apps import WtBtAnalyst

analyst = WtBtAnalyst()
analyst.add_strategy('dt_tencent', folder='./outputs_bt/', 
                    init_capital=500000, rf=0.02, annual_trading_days=250)
analyst.run_new()
```

### 使用pyfolio（可选）

```python
def analyze_with_pyfolio(fund_filename, capital=500000):
    import pyfolio as pf
    import pandas as pd
    from datetime import datetime
    
    df = pd.read_csv(fund_filename)
    df['date'] = df['date'].apply(lambda x: datetime.strptime(str(x), '%Y%m%d'))
    df = df.set_index(df["date"])
    
    ay = df['dynbalance'] + capital
    rets = ay.pct_change().fillna(0).tz_localize('UTC')
    
    pf.create_full_tear_sheet(rets)
```

## 注意事项

1. **数据源**: 确保富途OpenD正常运行并有相应的数据权限
2. **交易权限**: 港股交易需要相应的市场权限
3. **网络连接**: 确保网络连接稳定，避免数据中断
4. **资金管理**: 合理设置初始资金和仓位大小
5. **风险控制**: 策略包含止损机制，但仍需注意风险管理

## 扩展功能

### 添加更多港股标的

在 `hk_us_contracts.json` 和 `hk_us_commodities.json` 中添加更多港股代码。

### 策略优化

- 调整DualThrust参数(k1, k2)
- 修改止损比例
- 添加更多技术指标过滤
- 实现多品种组合策略

### 实盘交易

将回测代码修改为实盘交易：
1. 使用 `WtEngine` 替代 `WtBtEngine`
2. 添加 `FutuParser` 和 `FutuExecuter`
3. 配置实盘交易参数

## 技术支持

如有问题，请参考：
- Wondertrade官方文档
- 富途OpenAPI文档
- 项目GitHub仓库