# 部署指南

## 项目结构

```
├── backend/           # FastAPI 后端
├── frontend/          # Vue 3 前端
├── nginx/             # Nginx 配置
├── docker-compose.yml # Docker 编排
└── .github/workflows/ # GitHub Actions
```

---

## 一、后端部署到阿里云轻量服务器

### 1. 服务器准备

1. 登录阿里云轻量应用服务器控制台
2. 确认服务器已预装 Docker 和 Docker Compose
3. 开放以下端口（防火墙规则）：
   - `80` - HTTP
   - `443` - HTTPS（如需）
   - `8000` - 后端 API（可选，Nginx 代理后可关闭）

### 2. 配置 PostgreSQL 数据库

1. 登录阿里云 RDS PostgreSQL 控制台
2. 创建数据库（如 `aiagent`）
3. 创建数据库用户并设置密码
4. 配置白名单，允许轻量服务器内网 IP 访问

### 3. 配置后端环境变量

在服务器上创建 `backend/.env` 文件：

```bash
# 数据库配置（替换为你的实际值）
DATABASE_URL=postgresql://用户名:密码@pgm-xxxxx.pg.rds.aliyuncs.com:5432/aiagent

# JWT 密钥（生产环境务必修改）
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=360

# CORS 配置（添加你的 GitHub Pages 域名）
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "https://你的用户名.github.io"]
```

**注意**：
- 密码中的特殊字符需要 URL 编码，如 `@` → `%40`, `#` → `%23`
- `CORS_ORIGINS` 必须包含前端 GitHub Pages 的完整域名

### 4. 上传代码到服务器

使用 `scp` 或 `git clone` 将代码上传到服务器：

```bash
# 方式1：使用 git clone
ssh root@你的服务器IP
cd /opt
git clone https://github.com/你的用户名/你的仓库.git
cd 你的仓库

# 方式2：使用 scp（本地执行）
scp -r ./backend root@你的服务器IP:/opt/aiagent/backend
scp docker-compose.yml root@你的服务器IP:/opt/aiagent/
scp -r nginx root@你的服务器IP:/opt/aiagent/nginx
```

### 5. 启动服务

```bash
cd /opt/aiagent

# 创建上传目录
mkdir -p backend/uploads

# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f backend
docker compose logs -f nginx
```

### 6. 验证部署

```bash
# 测试健康检查
curl http://localhost/health

# 测试 API
curl http://localhost/api/

# 查看容器状态
docker compose ps
```

### 7. 常用命令

```bash
# 重启服务
docker compose restart

# 更新代码后重新部署
git pull
docker compose up -d --build

# 停止服务
docker compose down

# 查看后端日志
docker compose logs -f backend

# 进入后端容器
docker compose exec backend bash
```

---

## 二、前端部署（支持 GitHub Pages 和 Vercel）

### 方案对比

| 特性 | GitHub Pages | Vercel |
|------|-------------|--------|
| 费用 | 免费 | 免费（Hobby 计划） |
| 国内访问 | 较慢 | 较快（有 CDN） |
| 自定义域名 | 支持 | 支持 |
| 自动 HTTPS | 支持 | 支持 |
| 部署速度 | 较慢 | 快 |
| 配置复杂度 | 低 | 低 |

### 通用配置

1. 打开 GitHub 仓库 → Settings → Secrets and variables → Actions
2. 添加以下 Secret：

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `VITE_API_BASE_URL` | `http://你的服务器IP` 或 `https://你的域名` | 后端 API 地址 |

### 方式 A：部署到 GitHub Pages

#### 1. 启用 GitHub Pages

1. 打开 GitHub 仓库 → Settings → Pages
2. Source 选择 **GitHub Actions**
3. 保存

#### 2. 触发部署

推送代码到 `main` 或 `master` 分支会自动触发部署：

```bash
git add .
git commit -m "deploy: update frontend"
git push origin main
```

#### 3. 手动选择部署平台

在 GitHub 仓库 → Actions → Deploy Frontend → Run workflow

选择部署目标：
- **github-pages** - 仅部署到 GitHub Pages
- **vercel** - 仅部署到 Vercel
- **both** - 同时部署到两个平台

部署完成后，访问 `https://你的用户名.github.io/仓库名` 即可。

### 方式 B：部署到 Vercel

#### 1. 创建 Vercel 项目

1. 登录 [Vercel](https://vercel.com)
2. 点击 **Add New Project**
3. 导入你的 GitHub 仓库
4. 配置：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. 添加环境变量：
   - `VITE_API_BASE_URL` = 你的后端 API 地址
6. 点击 **Deploy**

#### 2. 配置 GitHub Actions（可选）

如果需要通过 GitHub Actions 部署到 Vercel，添加以下 Secrets：

| Secret 名称 | 获取方式 |
|------------|----------|
| `VERCEL_TOKEN` | Vercel → Settings → Tokens → Create Token |
| `VERCEL_ORG_ID` | Vercel → Settings → General → Organization ID |
| `VERCEL_PROJECT_ID` | Vercel → Settings → General → Project ID |

添加 Variables：

| Variable 名称 | 值 |
|--------------|-----|
| `VERCEL_PROJECT_NAME` | 你的 Vercel 项目名称 |

#### 3. 触发部署

手动触发工作流并选择 `vercel` 或 `both` 即可。

---

## 三、CORS 配置说明

由于前端部署在外部平台，后端需要配置 CORS 允许跨域请求。

在 `backend/.env` 中：

```bash
# GitHub Pages
CORS_ORIGINS=["https://你的用户名.github.io"]

# Vercel
CORS_ORIGINS=["https://你的项目名.vercel.app"]

# 多个前端环境
CORS_ORIGINS=["http://localhost:3000", "https://你的用户名.github.io", "https://你的项目名.vercel.app"]
```

---

## 四、HTTPS 配置（可选）

如果需要 HTTPS，可以使用 Let's Encrypt 免费证书：

1. 在 `nginx/ssl/` 目录下放置证书文件：
   - `cert.pem` - 证书文件
   - `key.pem` - 私钥文件

2. 更新 `nginx/nginx.conf`，添加 HTTPS server 块：

```nginx
server {
    listen 443 ssl;
    server_name 你的域名;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location /api/ {
        proxy_pass http://backend/api/;
        # ... 其他配置同上
    }
}

server {
    listen 80;
    server_name 你的域名;
    return 301 https://$server_name$request_uri;
}
```

---

## 五、故障排查

### 后端无法连接数据库

```bash
# 检查数据库连接
docker compose exec backend python -c "from app.database import engine; print(engine.connect())"

# 检查白名单配置
# 确保阿里云 RDS 白名单包含服务器 IP
```

### 前端无法调用 API

1. 检查 `VITE_API_BASE_URL` 是否正确配置
2. 检查后端 CORS 配置是否包含前端域名
3. 浏览器开发者工具查看网络请求

### Docker 构建失败

```bash
# 清理缓存重新构建
docker compose build --no-cache

# 查看构建日志
docker compose build 2>&1 | tee build.log
```
