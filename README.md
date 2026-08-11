# my first vibe coding aiagent platform

**Version: 1.0.0**

一个基于 FastAPI + Vue 3 的 AI 智能体管理与测试平台，支持工作流编排、代码工具、知识库检索、智能体对话等功能。

## 功能特性

- **智能体管理**：支持 API 智能体和工作流智能体两种类型
- **工作流引擎**：纯代码编排工作流，支持节点和代码混合编程
- **代码工具**：可复用的 Python 函数工具，支持数据处理、图表生成、文件导出等
- **知识库系统**：支持 RAG 检索增强生成，多知识库管理
- **测试用例**：智能体测试用例管理与执行
- **实时对话**：支持流式输出的智能体对话界面
- **API 配置**：多模型 API 配置管理
- **用户认证**：JWT 用户认证系统

## 技术栈

### 后端
- **框架**：FastAPI 0.109.0
- **数据库**：PostgreSQL / MySQL
- **ORM**：SQLAlchemy 2.0
- **认证**：python-jose, passlib, bcrypt
- **文档处理**：PyPDF2, PyMuPDF, python-docx, openpyxl, python-pptx
- **AI 集成**：dashscope (通义千问), tiktoken
- **向量化**：pgvector
- **测试**：pytest, pytest-asyncio

### 前端
- **框架**：Vue 3.4
- **构建工具**：Vite 8.0
- **路由**：Vue Router 4.2
- **HTTP 客户端**：Axios 1.6
- **Markdown 渲染**：md-editor-v3 4.20

### 部署
- **容器化**：Docker + Docker Compose
- **反向代理**：Nginx
- **CI/CD**：GitHub Actions
- **部署平台**：阿里云轻量服务器 + RDS PostgreSQL
- **前端托管**：GitHub Pages / Vercel

## 项目结构

```
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── models/            # 数据库模型
│   │   ├── routers/           # API 路由
│   │   ├── schemas/           # Pydantic 数据模型
│   │   ├── services/          # 业务逻辑服务
│   │   │   └── workflow/      # 工作流引擎
│   │   ├── utils/             # 工具函数
│   │   ├── auth.py            # 认证模块
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── main.py            # 应用入口
│   │   └── websocket_manager.py # WebSocket 管理
│   ├── tests/                 # 测试用例
│   ├── requirements.txt       # Python 依赖
│   ├── Dockerfile             # Docker 配置
│   └── .env.example           # 环境变量示例
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   ├── views/             # 页面视图
│   │   ├── App.vue            # 根组件
│   │   └── main.js            # 应用入口
│   ├── package.json           # Node.js 依赖
│   ├── vite.config.js         # Vite 配置
│   └── vercel.json            # Vercel 部署配置
├── nginx/                      # Nginx 配置
│   └── nginx.conf
├── docker-compose.yml          # Docker 编排
├── .github/workflows/          # GitHub Actions 工作流
│   └── deploy-frontend.yml
├── DEPLOY.md                   # 详细部署指南
├── README_code_tool.md         # 代码工具文档（位于 backend/app/services/workflow/）
└── README_language.md          # 工作流语言规范（位于 backend/app/services/workflow/）
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- PostgreSQL 14+ 或 MySQL 8.0+
- Docker & Docker Compose（可选，用于容器化部署）

### 后端安装

1. 克隆项目并进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境并激活：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和其他参数
```

5. 启动开发服务器：
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问 `http://localhost:8000/docs` 查看 API 文档。

### 前端安装

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

访问 `http://localhost:5173` 查看前端界面。

### Docker 部署

使用 Docker Compose 一键启动后端和 Nginx：

```bash
# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 文件

# 构建并启动服务
docker compose up -d --build

# 查看日志
docker compose logs -f
```

详细部署指南请参考 [DEPLOY.md](DEPLOY.md)。

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 核心模块

### 工作流引擎

工作流引擎支持节点和代码混合编程，提供强大的流程编排能力。

- **节点类型**：开始节点、大模型节点、知识库节点、智能体节点、UI 节点
- **代码执行**：支持 Python 代码块，可访问上下文对象
- **流程控制**：条件分支、循环、异步执行、节点等待

详细语言规范请参考：[README_language.md](backend/app/services/workflow/README_language.md)

### 代码工具

代码工具是可复用的 Python 函数，可在工作流中通过 `ctx.call_tool()` 调用。

- **文件处理**：Excel 导出、CSV 处理、文档生成
- **数据可视化**：matplotlib 图表生成
- **数据处理**：JSON 转换、数据聚合、统计分析
- **UI 集成**：动态添加按钮、图表、弹窗

详细文档请参考：[README_code_tool.md](backend/app/services/workflow/README_code_tool.md)

### 知识库系统

支持 RAG（检索增强生成）的知识库管理系统：

- 多格式文档上传（PDF、Word、Excel、PPT、TXT）
- 文本分块与向量化存储
- 语义检索与上下文提取
- 多知识库管理

### 智能体管理

- **API 智能体**：基于 API 的传统智能体，直接调用大模型
- **工作流智能体**：基于纯代码编排的智能体，通过工作流语言定义流程逻辑
- **统一对话接口**：支持多种智能体类型的统一调用

### 测试系统

- 测试用例管理（文件夹组织）
- 测试用例执行与进度跟踪
- 测试结果查看与分析
- 测试图片管理

## 环境变量配置

### 后端环境变量 (.env)

```bash
# 应用配置
APP_NAME=AI Agent Platform
APP_VERSION=1.0.0

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/aiagent
# 或 MySQL
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/aiagent

# JWT 认证
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=360

# CORS 配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# 文件上传
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

### 前端环境变量 (.env)

```bash
# 后端 API 地址
VITE_API_BASE_URL=http://localhost:8000
```

## 开发指南

### 代码规范

- 后端遵循 PEP 8 规范
- 前端使用 Vue 3 Composition API
- 提交信息使用语义化提交

### 运行测试

```bash
# 后端测试
cd backend
pytest tests/

# 前端构建测试
cd frontend
npm run build
```

## 部署

### 生产环境部署

1. **后端部署**：阿里云轻量服务器 + Docker + RDS PostgreSQL
2. **前端部署**：GitHub Pages 或 Vercel
3. **反向代理**：Nginx（可选 HTTPS）
4. **CI/CD**：GitHub Actions 自动部署

详细部署步骤请参考 [DEPLOY.md](DEPLOY.md)。

### 部署架构

```
用户 → Nginx (80/443) → 前端静态文件
                    → 后端 API (8000) → PostgreSQL
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
