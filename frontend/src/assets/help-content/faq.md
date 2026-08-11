## 常见问题

### 模型API如何配置

- 在平台配置中添加模型 API 配置
- 模型名称可以自定义
- 模型代码为模型调用时的model=参数，可参考服务商文档
- 目前仅支持 OpenAI Responses, OpenAI Chat API 配置，其它方式正在开发中
- 示例：
```json
{
    "模型名称": "Qwen3.6 Flash",
    "模型代码": "qwen3.6-flash",
    "API URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "API KEY": "sk-1234567890abcdef1234567890abcdef"
}
```

### API智能体如何配置

- 在智能体管理中点击新建智能体按钮
- 智能体名称可自定义，API KEY 为智能体 API 认证密钥
- 填写调用参数示例后点击保存，后端会自动生成调用代码
- 生成后可在前端编辑调用代码并进行测试
- 调用参数示例的示例：
```bash
      curl --location --request POST 'https://aiagent.test.edu.cn/api/v1/general/agent_answer' \
      --header 'Content-Type: application/json' \
      --header 'Authorization: Bearer [token信息]' \
      --data '{
    "agent_id": 1,
    "messages": [
        {
            "role": "user",
            "content": "你好"
        }
    ]
}'
```



### 工作流执行错误

- 检查工作流代码语法是否正确
- 确认call_tool函数等是否正确调用
- 在工作流智能体编写界面测试运行，查看是否有错误信息
- debug，日志等功能正在开发中，后续会添加

### 代码工具调用失败

- 确认工具名称与函数名一致
- 检查参数是否匹配
- 在代码工具页面测试运行工具
