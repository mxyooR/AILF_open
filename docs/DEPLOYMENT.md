# AILF 部署文档

## 目录

- [方式一：Docker 部署（推荐）](#方式一docker-部署推荐)
- [方式二：手动安装](#方式二手动安装)
- [方式三：生产环境部署](#方式三生产环境部署)
- [环境变量参考](#环境变量参考)
- [服务验证](#服务验证)
- [常见部署问题](#常见部署问题)

---

## 方式一：Docker 部署（推荐）

最快的方式，一条命令启动所有服务。

### 前置要求

- Docker Engine 24+
- Docker Compose v2+

### 启动

```bash
# 1. 克隆仓库
git clone https://github.com/mxyooR/AILF.git
cd AILF

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

预期输出：

```
NAME                IMAGE               STATUS          PORTS
ailf-backend       ailf/backend        Up              0.0.0.0:5000->5000/tcp
ailf-frontend      ailf/frontend       Up              0.0.0.0:3000->3000/tcp
ailf-worker        ailf/worker         Up              5000/tcp
ailf-redis         redis:7-alpine      Up              0.0.0.0:6379->6379/tcp
ailf-mysql         mysql:8.0           Up              0.0.0.0:3306->3306/tcp
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 用户端 | http://localhost:3000 | 主应用界面 |
| 开发者面板 | http://localhost:3000/config | 配置实体、工作流 |
| API 文档 | http://localhost:5000/docs | 交互式 API 文档 |
| 健康检查 | http://localhost:5000/api/v1/health | 服务状态 |

### 自定义配置

通过环境变量文件覆盖默认配置：

```bash
# 创建 .env 文件（与 docker-compose.yml 同目录）
cat > .env << EOF
DB_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_key_at_least_32_chars
DEVELOPER_PASSWORD=your_developer_password
DEBUG=false
EOF

# 重新启动
docker-compose up -d
```

### 查看日志

```bash
# 所有服务日志
docker-compose logs -f

# 单个服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

---

## 方式二：手动安装

适用于开发环境或自定义部署。

### 前置依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| pnpm | 8+ | 前端包管理器 |
| Redis | 6+ | Celery 消息队列 & 缓存 |
| MySQL | 8.0+ | 业务数据存储 |
| Git | 2.0+ | 版本控制 |
| Conda | 最新版 | Python 环境管理（推荐） |

### 步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/mxyooR/AILF.git
cd AILF
```

#### 2. 创建 Python 环境

```bash
conda create -n ailf_env python=3.11
conda activate ailf_env
python --version
# 输出: Python 3.11.x
```

#### 3. 安装后端依赖

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} 安装成功')"
# 输出: FastAPI 0.104.x 安装成功
```

#### 4. 初始化数据库

确保 MySQL 服务已启动，然后：

```bash
cd backend
python scripts/init_db.py
```

预期输出：

```
[1/5] 正在创建数据库 'ailf_db'...
  ✅ 数据库 'ailf_db' 已就绪
[2/5] 正在清理已存在的数据库表...
  ✅ 已清理旧的数据库表结构
[3/5] 正在创建数据表...
  ✅ 已创建表: users, roles, permissions, entities, workflows ...
[4/5] 正在初始化默认数据...
  ✅ 角色管理数据初始化完成
  ✅ 用户数据初始化完成
[5/5] 正在验证数据库状态...
  ✅ 数据库连接正常
✅ 数据库初始化完成! 耗时: 3.21秒
```

#### 5. 安装前端依赖

```bash
cd frontend
pnpm install
pnpm --version
# 输出: 8.x.x
```

#### 6. 配置环境变量

编辑 `backend/.env`，至少修改以下配置：

```bash
# JWT 密钥（必须修改！）
JWT_SECRET_KEY=your-secret-key-at-least-32-chars

# 开发者密码（必须修改！）
DEVELOPER_PASSWORD=your-strong-password

# 数据库密码（必须修改！）
DB_PASSWORD=your-database-password

# LLM 配置（按实际情况填写）
LLM_API_KEY=your-api-key
LLM_BASE_URL=http://your-llm-server:8000/v1
```

编辑 `celery_worker/.env`：

```bash
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

#### 7. 启动服务

**终端 1 - 后端服务：**

```bash
cd backend
python main.py
# INFO:     Uvicorn running on http://0.0.0.0:5000
# INFO:     API documentation available at http://localhost:5000/docs
```

**终端 2 - 前端开发服务器：**

```bash
cd frontend
pnpm dev
# VITE v5.x.x  ready in 200 ms
# ➜  Local:   http://localhost:3000/
```

**终端 3 - Celery Worker：**

```bash
cd celery_worker

# Windows
powershell -File start_celery_worker.ps1

# Linux / macOS
celery -A celery_app.celery_app worker --loglevel=info

# [INFO] Celery worker 'celery@hostname' is ready
```

#### 8. 验证安装

```bash
curl http://localhost:5000/api/v1/health
# {"status": "healthy", "version": "1.0.0", ...}
```

#### 9. 一键启动脚本（Windows）

项目根目录提供了 `start_all_services.ps1`，可一键启动所有服务：

```powershell
# 默认使用 D:/redis 作为 Redis 目录
.\start_all_services.ps1

# 指定项目根目录和 Redis 目录
.\start_all_services.ps1 -ProjectRoot "C:\AILF" -RedisDir "C:\redis"
```

脚本会自动：
1. 启动 Redis 服务
2. 启动 FastAPI 后端（新窗口）
3. 启动前端开发服务器（新窗口）
4. 启动 Celery Worker（新窗口）

> **注意**：该脚本依赖 Conda 环境 `ailf_env`，请确保已创建环境并安装了所有依赖。

---

## 方式三：生产环境部署

### 使用 Docker Compose 生产部署

```bash
# 1. 创建生产环境配置
cp backend/.env.example backend/.env.production
# 编辑 backend/.env.production 填入生产配置

# 2. 构建并启动
docker-compose up -d --build

# 3. 查看日志
docker-compose logs -f
```

### 生产环境注意事项

1. **修改所有默认密码和密钥**
2. **关闭调试模式**：设置 `DEBUG=false`
3. **配置 HTTPS**：前端使用反向代理（Nginx）配置 SSL
4. **数据库备份**：定期备份 MySQL 数据
5. **日志管理**：配置日志轮转，避免磁盘写满
6. **Worker 扩展**：多台机器启动 Worker 消费同一队列即可水平扩展

### 反向代理配置示例（Nginx）

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 前端静态文件
    location / {
        proxy_pass http://127.0.0.1:3000;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 环境变量参考

### 后端环境变量 (`backend/.env`)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEBUG` | `true` | 调试模式 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `5000` | 监听端口 |
| `JWT_SECRET_KEY` | (自动生成) | JWT 签名密钥，至少 32 字符 |
| `JWT_EXPIRE_HOURS` | `24` | Token 过期时间 |
| `DEVELOPER_PASSWORD` | (自动生成) | 开发者面板密码 |
| `DB_HOST` | `localhost` | 数据库地址 |
| `DB_PORT` | `3306` | 数据库端口 |
| `DB_USER` | `root` | 数据库用户 |
| `DB_PASSWORD` | `123456` | 数据库密码 |
| `DB_NAME` | `ailf_db` | 数据库名称 |
| `REDIS_HOST` | `localhost` | Redis 地址 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | (空) | Redis 密码 |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery 消息队列 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CONFIGURATION_COMPLETED` | `false` | 是否跳过配置检查 |

### Worker 环境变量 (`celery_worker/.env`)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Broker 地址 |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | 结果后端 |
| `MODEL_PRELOAD_ON_WORKER_START` | `true` | 是否预加载模型 |
| `LOCAL_MODEL_BASE_PATH` | `Qwen/Qwen3-4B` | LLM 模型路径 |
| `LOCAL_MODEL_LORA_PATH` | `Model/checkpoint_epoch_2` | LoRA 权重路径 |
| `EMBEDDING_MODEL_PATH` | `Model/bge-small-zh-v1.5` | 嵌入模型路径 |
| `LLM_TEMPERATURE` | `0.3` | 生成温度 |

---

## 服务验证

### 健康检查端点

```bash
# 基础健康检查
curl http://localhost:5000/api/v1/health

# 数据库健康检查
curl http://localhost:5000/health/database
```

### 验证数据库

```bash
cd backend
python -c "
from app.core.database import db_manager
health = db_manager.health_check()
print(health)
"
```

### 验证 Worker

```bash
cd backend
python scripts/check_celery_worker.py
```

---

## 常见部署问题

### MySQL 连接失败

**现象**：后端启动时报 `Can't connect to MySQL server`

**解决**：

1. 确认 MySQL 服务已启动
2. 检查 `.env` 中的数据库配置是否正确
3. 确认 MySQL 用户有远程访问权限（Docker 部署时）

### Redis 连接失败

**现象**：Celery Worker 无法启动

**解决**：

1. 确认 Redis 服务已启动：`redis-cli ping` 应返回 `PONG`
2. 检查 Redis 配置中的绑定地址和密码

### 模型加载失败

**现象**：Worker 启动时模型加载失败

**解决**：

1. 确认模型文件已下载到正确路径
2. 检查 `LOCAL_MODEL_BASE_PATH` 和 `LOCAL_MODEL_LORA_PATH` 配置
3. GPU 显存不足时，尝试设置 `CELERY_WORKER_CONCURRENCY=1` 和 `CELERY_WORKER_POOL=solo`

### 前端 API 请求失败

**现象**：前端页面加载但 API 请求返回 502

**解决**：

1. 确认后端服务已启动
2. 检查前端代理配置（`craco.config.js` 中的 `proxy.target`）
3. CORS 配置：确认 `backend/app/config.py` 中的 `CORS_ORIGINS` 包含前端地址
