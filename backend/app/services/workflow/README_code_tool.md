# 代码工具 (Code Tool)

代码工具是一种可复用的 Python 函数，可以在工作流中通过 `ctx.call_tool()` 调用。

## 基本概念

### 什么是代码工具？

代码工具是一个 Python 函数，具有以下特点：
- 函数名必须与工具名称一致
- 可以接收参数并返回结果
- 在工作流中执行时可以访问 `ctx` 对象

### 工具属性

| 属性 | 说明 |
|------|------|
| `name` | 函数名，用于调用时的标识符（如 `my_tool`） |
| `display_name` | 显示名称，用于界面展示 |
| `description` | 工具描述 |
| `code` | Python 代码 |
| `parameters` | 参数定义（JSON Schema 格式） |
| `return_type` | 返回值类型 |
| `is_active` | 是否启用 |

## 代码规范

### 函数定义

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

### 可用的全局对象

在工作流中调用代码工具时，可以使用以下全局对象：

| 对象 | 说明 |
|------|------|
| `ctx` | 工作流上下文对象，提供数据存储、文件保存等功能 |
| `__builtins__` | Python 内置函数 |

### ctx 对象方法

| 方法 | 说明 |
|------|------|
| `ctx.get(name)` | 获取上下文变量 |
| `ctx.set(name, value)` | 设置上下文变量 |
| `ctx.save_file(content, filename, file_type)` | 保存文件到服务器 |
| `ctx.save_chart(figure, filename, file_type)` | 保存 matplotlib 图表 |
| `ctx.save_dataframe(df, filename, file_type)` | 保存 pandas DataFrame |
| `ctx.add_button(id, label, action, style)` | 添加 UI 按钮 |
| `ctx.add_chart(id, chart_type, data, options)` | 添加 UI 图表 |
| `ctx.add_modal(id, title, content)` | 添加 UI 弹窗 |
| `ctx.set_layout(layout)` | 设置 UI 布局 |

## 示例

### 示例1：JSON 生成 Excel 并保存

```python
def json_to_excel(data: str, filename="export"):
    """
    将 JSON 数据转换为 Excel 文件并保存
    
    参数:
        data: JSON 数据字符串，可以是字典列表字符串或字典字符串
            - 字典列表字符串: '[{"name": "张三", "age": 25}, {"name": "李四", "age": 30}]'
            - 字典字符串: '{"headers": ["name", "age"], "rows": [["张三", 25], ["李四", 30]]}'
        filename: 文件名（不含扩展名），默认 "export"
    
    返回:
        dict: 包含文件路径和状态信息
            - success: 是否成功
            - file_path: 文件相对路径
            - rows: 数据行数
    """
    import json
    import pandas as pd
    
    # 解析 JSON 字符串
    try:
        parsed_data = json.loads(data)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON 解析失败: {str(e)}"}
    
    # 处理不同格式的输入数据
    if isinstance(parsed_data, list):
        # 字典列表格式
        df = pd.DataFrame(parsed_data)
    elif isinstance(parsed_data, dict):
        if "headers" in parsed_data and "rows" in parsed_data:
            # headers + rows 格式
            df = pd.DataFrame(parsed_data["rows"], columns=parsed_data["headers"])
        else:
            # 单个字典转为 DataFrame
            df = pd.DataFrame([parsed_data])
    else:
        return {"success": False, "error": "不支持的数据格式"}
    
    # 保存为 Excel 文件（filename 不需要包含扩展名）
    file_path = ctx.save_dataframe(df, filename, "xlsx")
    
    return {
        "success": True,
        "file_path": file_path,
        "rows": len(df),
        "columns": list(df.columns)
    }
```

**在工作流中调用：**

```python
import json

# 准备数据
sales_data = [
    {"product": "产品A", "quantity": 100, "price": 50.0},
    {"product": "产品B", "quantity": 200, "price": 30.0},
    {"product": "产品C", "quantity": 150, "price": 40.0}
]

# 转换为 JSON 字符串
json_str = json.dumps(sales_data, ensure_ascii=False)

# 调用工具
result = await ctx.call_tool("json_to_excel", data=json_str, filename="sales_report")

# 获取文件路径
if result.get("success"):
    file_path = result["file_path"]
    # 输出: 2026/04/26/sales_report.xlsx
else:
    logger.error(f"工具调用失败: {result.get('error')}")
```

### 示例2：生成图表并保存

```python
def create_bar_chart(labels, values, title="图表", filename="chart"):
    """
    创建柱状图并保存
    
    参数:
        labels: X 轴标签列表
        values: Y 轴值列表
        title: 图表标题
        filename: 文件名
    
    返回:
        dict: 包含文件路径
    """
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([str(l) for l in labels], values)
    ax.set_title(title)
    ax.set_xlabel('类别')
    ax.set_ylabel('数值')
    
    # 保存图表
    file_path = ctx.save_chart(fig, f"{filename}.png", "png")
    plt.close(fig)
    
    return {
        "success": True,
        "file_path": file_path
    }
```

**在工作流中调用：**

```python
result = await ctx.call_tool(
    "create_bar_chart",
    labels=["一月", "二月", "三月"],
    values=[100, 200, 150],
    title="月度销售",
    filename="monthly_sales"
)

# 添加到 UI
ctx.add_chart("sales_chart", "bar", {
    "labels": ["一月", "二月", "三月"],
    "datasets": [{"data": [100, 200, 150]}]
}, {"title": {"text": "月度销售"}})
```

### 示例3：数据处理工具

```python
def process_data(input_data, operation="sum"):
    """
    数据处理工具
    
    参数:
        input_data: 输入数据列表
        operation: 操作类型 (sum, avg, max, min)
    
    返回:
        dict: 处理结果
    """
    if not input_data:
        return {"success": False, "error": "输入数据为空"}
    
    operations = {
        "sum": sum,
        "avg": lambda x: sum(x) / len(x),
        "max": max,
        "min": min
    }
    
    if operation not in operations:
        return {"success": False, "error": f"不支持的操作: {operation}"}
    
    result = operations[operation](input_data)
    
    return {
        "success": True,
        "operation": operation,
        "result": result,
        "count": len(input_data)
    }
```

### 示例4：生成报告并下载

```python
def generate_report(title, sections, filename="report"):
    """
    生成包含数据和图表的报告
    
    参数:
        title: 报告标题
        sections: 报告章节列表，每个章节包含:
            - name: 章节名称
            - type: 类型 (text, table, chart)
            - data: 数据
        filename: 文件名
    
    返回:
        dict: 报告文件路径
    """
    import pandas as pd
    from io import BytesIO
    
    # 创建 Excel writer
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 添加摘要页
        summary_data = {"章节": [s["name"] for s in sections], "类型": [s["type"] for s in sections]}
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="摘要", index=False)
        
        # 添加各章节数据
        for i, section in enumerate(sections):
            sheet_name = f"章节{i+1}"[:31]  # Excel sheet 名称限制
            
            if section["type"] == "table":
                df = pd.DataFrame(section["data"])
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            elif section["type"] == "text":
                pd.DataFrame({"内容": [section["data"]]}).to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    
    # 保存文件
    file_path = ctx.save_file(output.getvalue(), f"{filename}.xlsx", "xlsx")
    
    # 添加下载按钮到 UI
    ctx.add_button("download_report", "下载报告", {
        "type": "download",
        "url": file_path,
        "filename": f"{title}.xlsx"
    })
    
    return {
        "success": True,
        "file_path": file_path,
        "sections": len(sections)
    }
```

**在工作流中调用：**

```python
report_data = {
    "title": "销售分析报告",
    "sections": [
        {
            "name": "销售概况",
            "type": "table",
            "data": [
                {"月份": "一月", "销售额": 10000, "增长率": 0.05},
                {"月份": "二月", "销售额": 12000, "增长率": 0.20},
                {"月份": "三月", "销售额": 15000, "增长率": 0.25}
            ]
        },
        {
            "name": "分析结论",
            "type": "text",
            "data": "本季度销售表现良好，整体增长趋势明显。"
        }
    ]
}

result = await ctx.call_tool("generate_report", **report_data)
```

## 参数定义

代码工具的参数使用 JSON Schema 格式定义：

```json
{
    "type": "object",
    "properties": {
        "data": {
            "type": "array",
            "description": "输入数据列表"
        },
        "filename": {
            "type": "string",
            "description": "输出文件名",
            "default": "export"
        }
    },
    "required": ["data"]
}
```

## 注意事项

1. **函数名必须与工具名称一致**：如果工具名称是 `my_tool`，则代码中必须定义 `def my_tool(...):`

2. **返回值建议使用字典**：便于包含状态信息和错误处理

3. **异常处理**：建议在工具内部处理异常并返回错误信息，而不是抛出异常

4. **文件保存**：使用 `ctx.save_file()` 等方法保存文件，返回的路径可直接用于前端下载

5. **前端测试**：在前端直接测试运行代码工具时，`ctx` 是空操作对象，方法调用不会执行实际操作

## 调用方式

### 在工作流代码中调用

```python
# 基本调用
result = await ctx.call_tool("tool_name", param1=value1, param2=value2)

# 带错误处理
result = await ctx.call_tool("json_to_excel", data=my_data)
if result.get("success"):
    file_path = result["file_path"]
else:
    logger.error(f"工具调用失败: {result.get('error')}")
```

### 在 UI 节点中使用下载

```python
# 工具返回文件路径后，在 UI 中添加下载按钮
result = await ctx.call_tool("json_to_excel", data=sales_data, filename="sales")

ctx.add_button("download_btn", "下载 Excel", {
    "type": "download",
    "url": result["file_path"],
    "filename": "销售数据.xlsx"
})
```
