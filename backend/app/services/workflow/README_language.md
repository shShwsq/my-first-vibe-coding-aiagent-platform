## 语言规范
节点分为一般节点和代码节点。一般节点用于处理逻辑，代码节点用于处理计算，如数学运算、字符串操作等。

代码用Python语法, 用{}包裹起来, 或用```包裹起来。
节点必须以分号结尾，包含"id"和"node"。

**节点换行规则**：
- 一般节点允许换行，以分号结尾
- 工作流执行时，节点中的换行符会被自动去除

**代码节点ID自动设置规则**：
- 每个节点之后最多允许跟随一个代码节点
- 如果节点后有代码节点，该代码节点会自动被视为一个独立的节点
- 代码节点的节点ID会自动设置为它前面节点的ID加上"_code"后缀
  - 例如：节点ID为1，其后的代码节点ID自动为"1_code"
  - 例如：节点ID为"start"，其后的代码节点ID自动为"start_code"
- 代码节点不需要显式声明"id"和"node"字段，系统会自动处理
- 允许`ctx.goto`跳转到代码节点
- 如果节点设置了`end`为`true`，则工作流直接结束，不执行后面的代码节点，除非有其它节点跳转到该节点的代码节点`_code`节点

## 保留字
- `ctx`：上下文对象
  - `ctx.set(name, value)`：设置变量的值。`name`表示变量名，`value`表示变量值。
  - `ctx.goto(*targets, max_loops=10) -> bool`：跳转到指定节点或多个节点。`targets`表示节点ID或节点name，多个节点ID或节点name之间用逗号隔开，同步执行所有节点。`max_loops`表示该步骤的执行次数上限，默认值为10，达到后返回 false 并忽略跳转。返回值：跳转成功返回 true，否则 false。
   - `ctx.final_return(result, history=True)`：返回最终结果。`history`表示是否添加到history，默认值为True。
  - `ctx.verbose_return(content, node_name=None)`：输出过程信息到前端。`content`表示要输出的内容，`node_name`表示节点名称（可选）。与节点的`verbose`参数功能类似，可在代码块中手动调用。
  - `ctx.get(name)`：获取变量的值。默认有input, history。
  - `ctx.output(*node_ids, join_mode="dict")`：获取节点的输出。`node_ids`为一个或多个节点ID（整数或字符串）。`join_mode`表示拼接方式，默认值为"dict"，返回字典，键名为节点ID；设置为"list"返回列表，每个元素为节点的输出；设置为"str"返回字符串，每个值之间用逗号隔开。
  - `ctx.http(url, method="GET", headers={}, body="")`：发送HTTP请求。`url`表示请求URL，`method`表示请求方法，`headers`表示请求头，`body`表示HTTP请求体。返回值：status，body, headers。此方法为异步方法，需在代码块中使用`await`调用。
  - `ctx.knowledgebase(baselist=None, query=None, file_paths=None)`：调用知识库检索。`baselist`表示知识库的名称列表（可选），`query`表示查询的关键词，`file_paths`表示上传文件的路径列表（可选）。如果同时指定了知识库和文件路径，会同时检索两者。返回包含`context`（检索到的上下文）、`sources`（知识库名称和文件名列表）、`error`的字典。此方法为异步方法，需在代码块中使用`await`调用。
  - `ctx.get_file_content(file_path, chunk_size=1000, chunk_overlap=200)`：获取文件的文本内容（分块列表）。`file_path`为文件路径，如果路径包含`files/`、`images/`或`chunks/`前缀（支持正斜杠或反斜杠），则在`backend/uploads`目录下查找；否则在`backend/workflow_files`目录下查找。`chunk_size`为分块大小（默认1000），`chunk_overlap`为分块重叠大小（默认200）。返回文本块列表，文件不存在或无法提取时返回空列表。
  - `ctx.call_agent(agent_id, agent_type=None, verbose_return=False, **kwargs)`：调用智能体。`agent_id`为智能体ID，`agent_type`为智能体类型（可选值为`"agent"`或`"workflow_agent"`，不指定则自动检测）。`verbose_return`为是否实时输出到前端，默认为`false`。`kwargs`支持`query`/`input_data`/`messages`等参数。此方法为异步方法，需在代码块中使用`await`调用。支持调用普通HTTP智能体（包括流式输出）和工作流智能体。
  - `ctx.call_model(model_id, messages, tools=None, enable_search=None, stream=False, output_format='text', timeout=60)`：调用大模型。`model_id`为模型配置ID（为None时使用默认模型），`messages`为消息列表（格式与大模型节点相同），`tools`为工具列表（可选），`enable_search`为是否启用搜索功能（可选），`stream`为是否流式输出，`output_format`为输出格式（`'text'`或`'json'`），`timeout`为超时时间（秒）。非流式返回文本内容或解析后的JSON对象，流式返回异步生成器。此方法为异步方法，需在代码块中使用`await`调用。
  - `ctx.call_tool(tool_name, **kwargs)`：调用代码工具。`tool_name`表示代码工具的函数名，`kwargs`表示传递给工具的参数。返回工具执行的结果。代码工具需在"代码工具"管理页面预先创建。
  - `ctx.wait_for_nodes(*node_ids)`：等待后台节点执行完成。`node_ids`为一个或多个节点ID。返回节点输出的字典。此方法为异步方法，需在代码块中使用`await`调用。
  - `ctx.save_file(content, filename=None, file_type=None)`：保存工作流生成的文件（图片、Excel等）到服务器。`content`支持bytes、base64字符串、matplotlib图表、pandas DataFrame、PIL图片等类型。`filename`为可选文件名，`file_type`为文件类型（如'png', 'xlsx', 'csv'）。返回文件的访问路径。
  - `ctx.save_chart(figure, filename=None, file_type="png")`：保存matplotlib图表的便捷方法。
  - `ctx.save_dataframe(df, filename=None, file_type="xlsx")`：保存pandas DataFrame的便捷方法。
  - `ctx.add_ui_element(element)`：动态添加UI元素。`element`为UI元素配置字典，支持添加按钮、图表、弹窗等。
  - `ctx.add_button(id, label, action, style=None)`：添加按钮。`id`为按钮ID，`label`为按钮文本，`action`为点击动作，支持：`{"type": "show_modal", "modal_id": "modal1"}`显示弹窗、`{"type": "close_modal", "modal_id": "modal1"}`关闭弹窗、`{"type": "download", "url": "path"}`下载文件、`{"type": "send_text", "text": "你好"}`发送指定文本到对话。`style`为可选样式配置。
  - `ctx.add_chart(id, chart_type, data, options=None,image_url=None)`：添加图表。`id`为图表ID，`chart_type`为图表类型（如'bar', 'line', 'pie'），`data`为图表数据，`options`为可选配置，`image_url`为可选图片URL。`image_url`为图表路径。
  - `ctx.add_modal(id, title, content, css=None, script=None)`：添加弹窗。`id`为弹窗ID，`title`为标题，`content`为内容（支持HTML），`css`为自定义样式，`script`为自定义脚本。
  - `ctx.set_layout(layout)`：设置UI布局配置。`layout`支持以下字段：
    - `direction`: 布局方向，"row"（横向）或 "column"（纵向），默认 "column"
    - `gap`: 元素间距，如 "16px"
    - `padding`: 内边距，如 "20px"
    - `align`: 对齐方式，"start", "center", "end", "stretch"
    - `justify`: 主轴对齐，"start", "center", "end", "space-between", "space-around"
    - `chart_width`: 图表默认宽度，如 "400px" 或 "100%"
    - `chart_height`: 图表默认高度，如 "300px"
  - `ctx.get_ui_elements()`：获取动态添加的UI元素和布局配置。
  - `ctx.clear_ui()`：清除所有动态添加的UI元素和布局配置。
- `memory`：长期存储的变量
  - `memory.set(name, value, is_editable, is_long)`：设置变量的值。`is_editable`表示用户是否可修改，默认值为false。`is_long`表示是否存储到永久记忆（跨会话保留），默认值为false。
  - `memory.get(name)`：获取变量的值。优先从永久记忆获取。
    - `memory.get("history")`：获取历史记录。包括当前用户消息。
- `logger`：日志对象，用于记录日志到控制台。`logger.info(msg)`：记录信息日志。`logger.error(msg)`：记录错误日志。`logger.warning(msg)`：记录警告日志。`logger.debug(msg)`：记录调试日志。`logger.critical(msg)`：记录严重错误日志。
- `workflow_logger`：工作流日志对象，用于记录日志到数据库。`workflow_logger.info(msg)`：记录信息日志。`workflow_logger.error(msg)`：记录错误日志。`workflow_logger.warning(msg)`：记录警告日志。`workflow_logger.debug(msg)`：记录调试日志。`workflow_logger.critical(msg)`：记录严重错误日志。

## 注释
- `//`：单行注释。
- `/*`：多行注释。

## 一般节点参数说明
- 节点公共参数：
  - "id": 节点的ID，必须为"start"或整数。
  - "name": 节点的名称（开始节点为智能体的名称）, optional, default none。
  - "node": 节点的类型。
  - "next": 下一个节点的ID或节点name，必须为整数或字符串，多个节点ID或节点name之间用逗号隔开,optional, default none。如果没有next, 则默认顺序执行下面的内容（可能是节点或代码）；如果没有next且下面没有其他节点, 则默认返回最终结果。
  - "async": 是否后台执行, optional, default false, 可选值为true或false。
  - "wait": 是否等待某个节点的输出，optional, default [], 可选值为节点ID数组。wait 可等待异步节点，引擎内部轮询或通过回调机制获取结果。
  - "max_loops"：执行次数上限, optional, default 10, 可选值为1到100之间的整数。
  - "verbose"：是否作为过程输出, optional, default false, 可选值为true或false。
  - "history"：是否添加到memory的history, optional, 非结束节点默认值为 false, 结束节点默认值为 true, 可选值为true或false。
  - "timeout"：超时时间, optional, default 60, 可选值为1到300之间的整数。
  - "end"：是否为最后一个节点, optional, default false, 可选值为true或false。设置为true时会自动设置final_return并终止工作流。

- 开始节点参数：
  - "id": 必须为"start"。
  - "node": 必须为"start"。
  - "name": 智能体的名称。
  - "params"：开始节点的参数, 直接添加到ctx中。
    - "name": 参数的名称。
    - "type": 参数的类型，可选值为：
      - `"str"`：字符串类型（默认值）
      - `"int"`：整数类型
      - `"float"`：浮点数类型
      - `"bool"`：布尔类型（支持 true/false/1/0/yes/no 等字符串自动转换）
      - `"list"`：列表类型（支持 JSON 数组字符串或逗号分隔的字符串）
      - `"dict"`：字典类型（支持 JSON 对象字符串）
      - `"df"`：DataFrame 类型（支持 JSON 对象/数组字符串，自动转换为 pandas DataFrame）
    - "default": 参数的默认值。optional, default none。
    - "description": 参数的描述。optional, default none。
    - 默认参数有："input_data": 用户输入的内容，"current_time": 当前时间。


- 大模型节点参数：
  - "id": 模型节点的ID，必须为整数。
  - "node": 必须为"model"。
  - "name": 模型节点的名称。
  - "model_id": 调用的模型ID，optional, 默认为用户的默认模型。
  - "messages"：模型节点的输入消息。
  - "tools"：模型节点的工具数组。
  - "enable_search"：是否启用搜索功能，optional, default null。
  - "stream"：是否流式输出。
  - "verbose"：是否实时输出到前端，optional, default true。当stream=true时，verbose=true表示实时流式输出到前端，verbose=false表示等待流式响应完成后返回完整内容。注意：如果该节点是最后一个节点（没有next且后面没有其他节点），会自动流式输出到前端，忽略verbose参数。
  - "output_format"：输出格式, optional, default "text", 可选值为"text"或"json"。


- 知识库节点参数：
  - "id": 知识库节点的ID，必须为整数。
  - "node": 必须为"knowledgebase"。
  - "name": 知识库节点的名称。
  - "baselist": 知识库的库列表。
  - "query": 知识库的查询关键词。
  - "output": 知识库的输出参数数组，默认为["context", "error", "sources"], 且目前只允许在"context", "error", "sources"中选择。

- 智能体节点参数：
  - "id": 智能体节点的ID，必须为整数。
  - "node": 必须为"agent"。
  - "name": 智能体节点的名称。
  - "agent_id": 调用的智能体ID，支持普通HTTP智能体和工作流智能体。
  - "agent_type": 调用的智能体的类型，可选，默认"workflow_agent"。支持"agent"和"workflow_agent"。
   - "params": 传递给智能体的参数，可选。格式为键值对字典，如`{"key1": "value1", "key2": "value2"}`。
  - "verbose_return": 是否实时输出到前端，可选，默认false。设为true时，智能体的返回结果会实时显示到前端（支持流式和非流式输出）。

- UI节点参数（UI节点的显示一定在最后）：
  - "id": UI节点的ID，必须为整数。
  - "node": 必须为"ui"。
  - "name": UI节点的名称。
  - "buttons": 按钮配置数组，每个按钮包含：
    - "id": 按钮ID，用于标识按钮。
    - "label": 按钮显示文本。
    - "action": 点击动作，支持以下类型：
      - `{"type": "show_modal", "modal_id": "弹窗ID"}`：点击显示指定弹窗。
      - `{"type": "close_modal", "modal_id": "弹窗ID"}`：点击关闭指定弹窗。
      - `{"type": "show_modal", "modal_id": "弹窗ID", "data": {...}}`：传递数据给弹窗。
      - `{"type": "download", "url": "文件路径或URL"}`：点击下载文件，url可以是相对路径（如`2026/04/26/file.png`）或完整URL。
      - `{"type": "download", "url": "文件路径", "filename": "自定义文件名.png"}`：下载时指定文件名。
      - `{"type": "send_text", "text": "你好"}`：点击发送指定文本到对话，相当于用户手动输入。
    - "style": 可选的按钮样式配置，如`{"background": "#4CAF50", "color": "white", "border_radius": "8px"}`。
  - "charts": 图表配置数组，每个图表包含：
    - "id": 图表ID，用于标识图表。
    - "type": 图表类型，支持：'bar'（柱状图）、'line'（折线图）、'pie'（饼图）、'doughnut'（环形图）、'radar'（雷达图）、'scatter'（散点图）。
    - "data": 图表数据，格式为`{"labels": ["标签1", "标签2"], "datasets": [{"label": "数据集名称", "data": [10, 20], "backgroundColor": "#颜色"}]}`。
    - "options": 可选的图表配置，如`{"title": {"display": true, "text": "图表标题"}, "scales": {"y": {"beginAtZero": true}}}`。
    - "image_url": 可选，图片URL，支持以下格式：
      - 相对路径：如`/workflow_files/2026/04/25/chart.png`（ctx.save_file()返回的路径）
      - 绝对URL：如`https://example.com/chart.png`
      - Base64字符串：纯base64编码，会自动添加`data:image/png;base64,`前缀
      - Data URL：如`data:image/png;base64,iVBORw0KGgo...`
    - "visible": 可选，是否显示图表，默认true。设为false时图表不在主界面显示，但仍可在弹窗中通过`{{chart:图表ID}}`引用。
  - "modals": 弹窗配置数组，每个弹窗包含：
    - "id": 弹窗ID，用于按钮关联。
    - "title": 弹窗标题。
    - "content": 弹窗内容，支持HTML格式。可包含图表占位符`{{chart:图表ID}}`来显示图表。
    - "css": 自定义CSS样式，会注入到弹窗中。
    - "script": 自定义JavaScript脚本，在弹窗打开时执行。可使用`modalData`变量获取传递的数据。
    - "width": 弹窗宽度，默认"600px"。
    - "height": 弹窗高度，默认"auto"。
    - "close_on_overlay": 点击遮罩层是否关闭弹窗，默认true。
  - "layout": 可选的布局配置：
    - "direction": 布局方向，"row"（横向）或 "column"（纵向），默认 "column"。
    - "gap": 元素间距，如 "16px"。
    - "padding": 内边距，如 "20px"。
    - "align": 交叉轴对齐方式，"start", "center", "end", "stretch"。
    - "justify": 主轴对齐方式，"start", "center", "end", "space-between", "space-around"。
    - "chart_width": 图表默认宽度，如 "400px" 或 "100%"。
    - "chart_height": 图表默认高度，如 "300px"。
    - "chart_direction": 图表排列方向，"row" 或 "column"。
    - "button_group": 按钮组配置，如 `{"align": "center"}`。
  - "show_in_modal": 可选，是否将整个UI显示在弹窗中，默认false。

## 示例
### 示例1 · 课程信息助手
```
"id": "start", "name": "课程信息助手", "node": "start", 
"params": [{"name": "input_data", "type": "text"}];
"id": 1, "name": "安全审核", "node": "model", 
"messages": [
{"role": "system", 
"content": "你是一个专业的安全审核助手，你需要根据用户输入的内容，判断是否符合安全规范。
如果符合，输出“合规”；如果不符合，输出“违规”。严格只输出“合规”或“违规”，不要输出任何解释，不要输出其它内容。"}, 
memory.get("history")
], "stream": false, "verbose": false, "output_format": "text";

{ 
    if ctx.output(1) == "合规":
        ctx.goto(2)
    elif ctx.output(1) == "违规":
        ctx.final_return("抱歉，暂时无法回答您的问题")
    else:
        ctx.goto(1, 2)  # 若次数超过2次，返回false, 继续执行下面的代码
        ctx.final_return("未知错误")
}

"id": 2, "node": "knowledgebase", 
"baselist": ["course_info"], "query": ctx.get("input_data"), "output": ["context", "error"], "next": 3;

{
    if ctx.output(2).error:
        ctx.final_return(ctx.output(2).error)
    elif ctx.output(2).context:
        ctx.verbose_return(memory.get("测试"))
        ctx.verbose_return('\n')
        ctx.verbose_return('')
        ctx.goto(3)
    else:
        ctx.final_return("抱歉，没有找到相关课程")
}

"id": 3, "node": "model", 
"messages": [
{"role": "system", 
"content": "你是一个专业的课程信息助手，你需要根据参考信息回答用户的问题。参考信息为：{ctx.output(2).context}"}, 
memory.get("history")
], "stream": true, "end": true;

```



### 示例2 · 使用代码工具
```
"id": "start", "name": "数据分析助手", "node": "start", 
"params": [{"name": "input_data", "type": "text"}];

{
    # 调用代码工具进行数据处理
    # 假设已创建名为 calculate_statistics 的代码工具
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = await ctx.call_tool("calculate_statistics", numbers=numbers)
    
    if result.get("error"):
        ctx.final_return(f"计算出错: {result['error']}")
    else:
        ctx.set("stats", result)
        ctx.goto(1)
}

"id": 1, "node": "model", 
"messages": [
{"role": "system", 
"content": "你是一个数据分析助手。用户提供了以下统计数据，请用简洁的语言解释这些数据的含义。"},
{"role": "user", "content": f"数据: {ctx.get('stats')}"}
], "stream": true, "end": true;
```

**代码工具示例 (calculate_statistics)**：
```python
def calculate_statistics(numbers: list) -> dict:
    """
    计算列表的统计信息
    
    参数:
        numbers: 数字列表
    
    返回:
        dict: 包含统计信息
    """
    if not numbers:
        return {"error": "列表不能为空"}
    
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "mean": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers)
    }
```

### 示例3 · UI节点 - 数据可视化仪表板
```
"id": "start", "name": "数据分析仪表板", "node": "start", 
"params": [{"name": "input_data", "type": "text"}];

{
    import matplotlib.pyplot as plt
    import io
    
    # 模拟数据分析
    data = {"产品A": 120, "产品B": 200, "产品C": 150, "产品D": 80}
    
    # 创建柱状图
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(data.keys(), data.values(), color=['#4CAF50', '#2196F3', '#FF9800', '#E91E63'])
    ax.set_title('产品销售数据')
    ax.set_ylabel('销量')
    
    # 保存图表
    chart_url = ctx.save_chart(fig, filename="sales_chart", file_type="png")
    plt.close()
    
    ctx.set("chart_url", chart_url)
    ctx.set("data", data)
    ctx.goto(1)
}

"id": 1, "node": "ui", "name": "数据仪表板",
"buttons": [
  {"id": "btn_detail", "label": "查看详情", "action": {"type": "show_modal", "modal_id": "detail_modal"}},
  {"id": "btn_export", "label": "导出数据", "action": {"type": "show_modal", "modal_id": "export_modal"}}
],
"charts": [
  {
    "id": "sales_chart",
    "type": "bar",
    "data": {"labels": ["产品A", "产品B", "产品C", "产品D"], "datasets": [{"label": "销量", "data": [120, 200, 150, 80], "backgroundColor": ["#4CAF50", "#2196F3", "#FF9800", "#E91E63"]}]},
    "options": {"title": {"display": true, "text": "产品销售数据"}, "scales": {"y": {"beginAtZero": true}}},
    "image_url": ctx.get("chart_url")
  }
],
"modals": [
  {
    "id": "detail_modal",
    "title": "详细数据",
    "content": "<div class='detail-content'><h3>销售详情</h3><p>产品A: 120件</p><p>产品B: 200件</p><p>产品C: 150件</p><p>产品D: 80件</p><div class='chart-container'>{{chart:sales_chart}}</div></div>",
    "css": ".detail-content { padding: 20px; } .detail-content h3 { color: #333; margin-bottom: 15px; } .chart-container { margin-top: 20px; }",
    "script": "console.log('弹窗打开，数据:', modalData);",
    "width": "800px"
  },
  {
    "id": "export_modal",
    "title": "导出选项",
    "content": "<div class='export-options'><p>选择导出格式：</p><button onclick='exportExcel()'>导出Excel</button><button onclick='exportPDF()'>导出PDF</button></div>",
    "css": ".export-options { padding: 20px; } .export-options button { margin: 10px 5px; padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; }",
    "script": "function exportExcel() { alert('导出Excel功能'); } function exportPDF() { alert('导出PDF功能'); }",
    "width": "400px"
  }
],
"layout": {"type": "vertical", "gap": "20px"};
```
