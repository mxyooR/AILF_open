# Celery Worker 代码包说明

该目录用于部署到分布式算力机器，仅包含代码，不包含模型权重文件。

## 目录结构
- `celery_worker/celery_app.py`：Worker 专用 Celery 应用
- `celery_worker/ai_tasks.py`：AI 推理任务定义
- `celery_worker/config.py`：Worker 独立配置（不依赖 `app.config`）
- `celery_worker/model/`：模型相关核心代码（已从 `backend/app/core/ai` 迁移）
- `celery_worker/start_celery_worker.ps1`：Worker 启动脚本
- `celery_worker/.env.example`：Worker 环境变量模板

## 启动方式（在项目根目录）
```powershell
conda activate ailf_env
powershell -ExecutionPolicy Bypass -File .\celery_worker\start_celery_worker.ps1
```
