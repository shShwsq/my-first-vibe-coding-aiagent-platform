## 代码工具

代码工具是一种可复用的 Python 函数，可以在工作流中通过 `ctx.call_tool()` 调用。

### 基本概念

- 函数名必须与工具名称一致
- 可以接收参数并返回结果
- 在工作流中执行时可以访问 `ctx` 对象
  - `ctx`使用详见 [工作流语言](workflow-language.md)

### 代码规范

```python
def tool_name(param1, param2, ...):
    """
    工具函数
    
    参数:
        param1: 参数1说明
        param2: 参数2说明
    
    返回:
        返回值说明
    """
    # 函数逻辑
    return result
```

### 支持的库

代码工具支持以下常用 Python 库：

| 库 | 说明 |
|------|------|
| `numpy` | 数值计算 |
| `pandas` | 数据处理与分析 |
| `matplotlib` | 绘图库，支持中文显示 |
| `mplfinance` | 金融K线图绘制 |
| `tqsdk` | 天勤量化交易接口 |

### 示例

示例1：JSON 生成 Excel

```python
def json_to_excel(data: str, filename="export"):
    import json
    import pandas as pd
    
    parsed_data = json.loads(data)
    df = pd.DataFrame(parsed_data)
    file_path = ctx.save_dataframe(df, filename, "xlsx")
    
    return {
        "success": True,
        "file_path": file_path,
        "rows": len(df)
    }
```

示例2：绘制K线图

```python
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt


def plot_klines(df: pd.DataFrame,
                max_candles: int = 200,
                title: str = 'K线图',
                style: str = 'charles',
                volume: bool = True,
                filename: str = 'Kline') -> dict:
    """
    绘制K线图并保存（数据量超过 max_candles 时自动聚合降采样）

    Parameters
    ----------
    df : pd.DataFrame
        原始K线数据，必须包含字段:
        'datetime', 'open', 'high', 'low', 'close', 'volume'
    max_candles : int
        显示的最大K线根数，超出时按顺序分组聚合
    title : str
        图表标题
    style : str
        mplfinance 内置样式名称
    volume : bool
        是否绘制成交量副图
    filename : str
        保存文件名（不含扩展名）

    Returns
    -------
    dict : {"success": bool, "file_path": str}
    """

    # 提取并整理数据
    data = df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.sort_values('datetime', inplace=True)
    data.reset_index(drop=True, inplace=True)

    # ------------------------------------------------
    # 聚合降采样：将连续的多根K线合并为一根
    # Open  = 第一根开盘价
    # High  = 组内最高价
    # Low   = 组内最低价
    # Close = 最后一根收盘价
    # Volume= 组内成交量累加（求和）
    # ------------------------------------------------
    if len(data) > max_candles:
        total = len(data)
        # 每组包含的原始K线根数（向上取整，保证最终根数 ≤ max_candles）
        group_size = int(np.ceil(total / max_candles))
        # 生成组标签：0,0,... 1,1,... 按顺序分组
        groups = np.arange(total) // group_size

        data = data.groupby(groups).agg(
            datetime=('datetime', 'last'),  # 新K线时间取组内最后一根
            open=('open', 'first'),
            high=('high', 'max'),
            low=('low', 'min'),
            close=('close', 'last'),
            volume=('volume', 'sum')        # 累加成交量
        )
        data = data.sort_values('datetime').reset_index(drop=True)

    # 转换为 mplfinance 要求的列名与索引
    data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    data.set_index('Date', inplace=True)

    # 绘图
    fig, axes = mpf.plot(
        data,
        type='candle',
        style=style,
        title=title,
        volume=volume,
        figsize=(14, 7),
        panel_ratios=(3, 1) if volume else (1,),
        returnfig=True
    )

    # 保存图片
    file_path = f"{filename}.png"
    success = True
    try:
        if ctx is not None and hasattr(ctx, 'save_chart'):
            file_path = ctx.save_chart(fig, file_path, "png")
        else:
            success = False
    except Exception as e:
        success = False
        ctx.verbose_return(f"图片保存失败: {e}")
    finally:
        plt.close(fig)

    return {
        "success": success,
        "file_path": file_path
    }
```

### 调用方式

```python
result = await ctx.call_tool("工具名称", 参数1=值1, 参数2=值2, ...)
```

> **注意**：`call_tool`是异步方法，需要使用 `await` 调用。
