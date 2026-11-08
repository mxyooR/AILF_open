# 部署与运行

先选择运行范围：只体验界面用 `/demo`；运行真实自然语言推理，需要应用、数据库、消息队列、计算环境和模型权重。

## 仅运行交互演示

需要 Node.js 20+、pnpm 10.13.1。

```bash
git clone https://github.com/mxyooR/AILF_open.git
cd AILF_open
pnpm install --frozen-lockfile
pnpm dev
```

打开 http://localhost:3000/demo。已有环境可以复用，无需重复安装。此模式无需 `.env`、数据库或模型。

Docker 方式：

```bash
docker compose -f docker-compose.demo.yml up --build -d
```

## GitHub Pages 在线演示

本仓库的静态演示发布到 **https://mxyooR.github.io/AILF_open/**。CI 在主分支提交后先运行内容扫描、离线测试和前端检查，再上传构建产物并由 GitHub Actions 发布 Pages。

演示构建设置 `REACT_APP_DEMO_ONLY=true` 与 `PUBLIC_URL=/AILF_open`。前者只展示演示入口并将内部导航留在内存中，后者设置静态资源前缀，因此访问仓库子路径、页内锚点和刷新均不依赖服务器路由回退。默认 `pnpm build` 保持完整应用模式。

自行部署同类项目时，在仓库 Settings → Pages 中选择 **GitHub Actions** 作为来源，并按仓库名设置 `PUBLIC_URL`。站点只包含前端静态文件，不上传 `.env`、模型或数据库，也不提供真实业务推理。

## 完整应用：Docker

需要 Docker Compose v2。推理 Worker 还需要 NVIDIA GPU、驱动与 NVIDIA Container Toolkit；模型采用量化加载，实际显存需求应根据权重和上下文长度测量。

```bash
python scripts/setup_env.py
docker compose up --build -d
docker compose ps
```

配置脚本仅创建不存在的根目录 `.env`，生成独立随机凭据且不输出明文。`.env` 被 Git 和 Docker 构建上下文忽略。Compose 要求配置数据库和认证凭据，不提供固定密码回退。

访问地址：

| 地址 | 用途 |
| --- | --- |
| http://localhost:3000/demo | 浏览器内演示 |
| http://localhost:3000 | 完整应用 |
| http://localhost:3000/config | 开发者业务配置 |
| http://localhost:5000/docs | 当前代码生成的 API 文档 |

开发者密码由本地 `.env` 中的 `DEVELOPER_PASSWORD` 提供。默认不创建公开测试账号；业务用户通过注册或开发者面板创建。数据服务端口和应用端口默认绑定本机地址。

MySQL 使用专用应用用户。应用启动会创建或调整表结构，请只连接用于该部署的数据库。已有数据卷不会因更改 `.env` 自动修改数据库密码。

## 模型与 Worker

Git 中不包含基础模型、LoRA 或 embedding 的权重文件。目录中的适配器配置不能替代权重。准备以下本地文件：

| 目录 / 配置 | 内容 |
| --- | --- |
| `Qwen/Qwen3-4B` / `LOCAL_MODEL_BASE_PATH` | 完整的 Qwen3-4B 模型与 tokenizer |
| `Model/checkpoint_epoch_2` / `LOCAL_MODEL_LORA_PATH` | 与训练数据和基础模型兼容的 LoRA 权重与适配器配置 |
| `Model/bge-small-zh-v1.5` / `EMBEDDING_MODEL_PATH` | 完整的 BGE embedding 模型 |

基础模型来源：[Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B)、[bge-small-zh-v1.5](https://huggingface.co/BAAI/bge-small-zh-v1.5)。下载与使用遵循各自许可。LoRA 可按 [Model 说明](../Model/README.md)训练；本仓库不提供外部权重下载承诺。

```bash
docker compose --profile inference up --build -d worker
docker compose logs -f worker
```

模型目录以只读卷挂载，不复制进镜像。后端只安装 HTTP 编排依赖，模型依赖在独立 Worker 环境安装。

## 手动运行完整应用

推荐 Python 3.11 / 3.12，另需 MySQL 8、Redis 7。已有 Conda 环境可以直接使用。下列命令从仓库根目录执行。

```bash
python scripts/setup_env.py
pip install -r backend/requirements.txt
python backend/main.py
```

启动前，在 MySQL 中为独立库创建有建表权限的应用用户，并根据本机实际环境修改 `.env`。不要将文档中的测试命令指向有重要业务数据的数据库。

另一个终端运行 `pnpm dev`。在准备模型权重和匹配 CUDA 的 PyTorch 后，单独运行 Worker：

```bash
pip install -r celery_worker/requirements.txt
python -m celery -A celery_worker.celery_app:celery_app worker --loglevel=info --pool=solo --concurrency=1 -Q ai_inference
```

Worker 必须从仓库根目录运行。Windows 也可使用 `celery_worker/start_celery_worker.ps1`。基础模型与 LoRA 路径默认相对项目目录；自定义路径建议使用绝对路径。

## 配置约定

后端配置优先级：进程环境变量 → `backend/.env` → 根目录 `.env`。Worker 配置优先级：进程环境变量 → `celery_worker/.env` → 根目录 `.env` → `backend/.env`。

| 变量 | 用途 |
| --- | --- |
| `JWT_SECRET_KEY` | 至少 32 字符；进程间共享的 JWT 签名密钥 |
| `DEVELOPER_PASSWORD` | 至少 12 字符；开发者配置认证 |
| `DB_PASSWORD` | 至少 12 字符；应用数据库密码 |
| `MYSQL_ROOT_PASSWORD` | Compose 数据库管理员密码，独立于应用密码 |
| `DEBUG` | 默认 `false`，本地调试可显式开启 |
| `SEED_DEMO_USERS` | 默认 `false`；若开启，还需设置 `DEMO_USER_PASSWORD` |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | 后端与推理 Worker 使用同一 Redis 队列 |
| `AI_COMMAND_MAX_CONCURRENT` / `AI_COMMAND_MAX_PENDING` | 单进程活跃编排数 / 未完成任务总量，默认 2 / 64；满载返回 429 |
| `AI_COMMAND_TIMEOUT_SECONDS` | 排队与执行的等待上限，默认 540 秒 |
| `AI_COMMAND_CACHE_SIZE` / `REDIS_AI_TASK_TTL` | 本地状态条数 / 状态 TTL，默认 1024 / 3600 秒 |

后端拒绝缺失、过短和指定格式的占位认证凭据。更完整的可选配置见 `backend/.env.example` 与 `celery_worker/.env.example`。

命令运行时要求 `cache >= pending >= concurrent >= 1` 且 `TTL > timeout > 0`。状态 TTL 从最近一次状态更新计算，轮询不续期。查询必须携带提交时返回的 `poll_token`，详见[异步 API 约定](ASYNC_COMMANDS.md)。前端与后端应一起升级，旧的仅凭 `task_id` 查询方式不再受支持。

这些限制按后端进程计算，不是集群限流。Redis 回退状态只存在当前进程；重启不自动恢复编排，也不会因编排超时撤销已派发的 GPU 作业。默认 Docker Worker 以单进程顺序消费模型队列，调整计算并行度前应测量显存和真实请求负载。

## 验证与已知限制

离线测试、前端构建和 Compose 配置检查的实际结果见[验证记录](VALIDATION.md)。它们不替代 GPU 模型加载、完整业务流程、容器镜像构建或并发测试。

- 演示使用本地合成数据，不执行真实支付、出票或预约。
- 原型保留部分旧依赖版本和历史集成脚本，公开部署前应单独完成依赖升级、隔离、TLS、限流和集成验证。
- 现有本地启动脚本含 Conda / Redis 的环境约定，不作为跨平台的一键部署入口。
- 不建议运行 `pytest backend/tests/` 作为离线检查，旧脚本可能连接服务或修改数据。
