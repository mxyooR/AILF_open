# Celery 部署说明（主后端单机 + 推理机可扩展）

## 1. 目标架构
- 主机：运行 FastAPI 后端（`python main.py`）+ Redis（Broker/Result Backend）
- 推理机：运行 Celery Worker（可 1 台，也可多台，仅执行推理任务）
- 前端：只访问主后端，不直接访问推理机

当前支持两种模式：
- 本地单推理机：主机同时跑后端和 1 个 Worker
- 企业扩展：多台局域网推理机共同消费同一队列

## 2. 必要配置
在 `backend/.env` 中确认：

```env
CELERY_BROKER_URL=redis://<redis-host>:6379/1
CELERY_RESULT_BACKEND=redis://<redis-host>:6379/1
CELERY_AI_QUEUE=ai_inference
```

在 `celery_worker/.env` 中确认 Worker 参数：

```env
CELERY_WORKER_POOL=solo
CELERY_WORKER_CONCURRENCY=1
```

说明：如果是局域网多机，所有 Worker 的 Broker/Backend 必须指向主机 Redis。

## 3. Worker 代码位置（新）
- Worker 独立代码目录：`celery_worker`
- 其中模型相关核心代码已迁移至：`celery_worker/model`
- 主后端仅负责投递任务与查询结果，不再绑定 Worker 任务实现

## 4. 本地单推理机部署（你当前场景）
### 步骤 A：启动主后端
```powershell
conda activate ailf_env
cd backend
python main.py
```

### 步骤 B：启动 Celery Worker
```powershell
conda activate ailf_env
powershell -ExecutionPolicy Bypass -File .\celery_worker\start_celery_worker.ps1
```

### 步骤 C：验证 Worker 可用
```powershell
cd backend
conda run -n ailf_env python scripts/check_celery_worker.py
```

输出包含 `celery_ping_ok` 即表示可消费任务。

## 5. Worker 代码目录
- Worker 运行脚本：`celery_worker/start_celery_worker.ps1`
- Worker 独立配置：`celery_worker/config.py`
- Worker 环境变量模板：`celery_worker/.env.example`

## 6. 企业多推理机扩展
在每台推理机上：
1. 部署同版本代码和模型
2. 配置同一个 `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`
3. 启动 Worker（队列保持 `ai_inference`）

多台 Worker 同时消费同一队列即可自动分摊推理压力，无需改主后端。

## 7. 当前状态边界
- 已接入异步接口：`/api/v1/command/async` + 查询接口
- 主后端负责业务编排与任务状态管理，不加载本地模型
- Worker 仅提供推理任务：`app.tasks.ai.invoke` / `app.tasks.ai.ping`
