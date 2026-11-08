# 异步命令 API

完整应用将自然语言命令交给有界编排运行时，模型调用由独立 Celery Worker 执行。演示页使用本地请求处理器，不调用本 API。

## 提交

`POST /api/v1/command/async`

```json
{
  "command": "查询北京到上海的高铁",
  "context": {}
}
```

按业务需要附带用户或开发者 `Authorization: Bearer …`。服务端从认证信息构建权限上下文；任务查询凭据只允许查询结果，不能授予业务操作权限。

接收成功返回 HTTP 202：

```json
{
  "code": 202,
  "message": "异步任务已提交",
  "data": {
    "task_id": "<task-id>",
    "poll_token": "<per-task-credential>",
    "status": "PENDING",
    "poll_url": "/api/v1/command/async/<task-id>"
  },
  "meta": {"timestamp": 0}
}
```

占位符和时间戳仅说明结构。`poll_token` 只在提交时返回，应保存在请求生命周期内的内存中。不要写入 URL、日志、分析埋点或公开截图。

## 查询

`GET /api/v1/command/async/{task_id}`，请求头包含 `X-Task-Token: <per-task-credential>`。

返回 HTTP 200，状态位于 `data.status`：

| 状态 | 含义 | 附加字段 |
| --- | --- | --- |
| `PENDING` | 等待编排槽位 | `message` |
| `STARTED` | 正在编排和等待模型 | `message` |
| `SUCCESS` | 结束轮询，可渲染结果 | `result`，包含 `amis_schema` 等生成结果 |
| `FAILURE` | 结束轮询，提示用户重试 | `error`，通用失败、超时或关闭说明 |

前端默认每 1200 毫秒查询一次，最长等待 600 秒。终态应停止轮询。需要重新提交时，由用户明确发起；提交接口没有提供业务幂等保证。

## 错误与兼容性

| HTTP 状态 | 含义 |
| --- | --- |
| 404 | 任务不存在、已过期、已从本地缓存淘汰，或查询凭据缺失 / 不正确；统一响应避免暴露任务是否存在 |
| 429 | 本进程未完成任务达到容量上限 |
| 503 | 运行时正在关闭，无法接受新任务 |
| 500 | 提交或查询服务异常；响应不返回原始异常细节 |

旧客户端仅凭 `task_id` 轮询会收到 404，必须同时升级前后端。状态从最后一次迁移开始默认保留 3600 秒，轮询不会续期；Redis 故障时本地结果可能因容量限制提前淘汰。

命令并发和容量是单进程限制；Redis 共享状态不提供进程重启后的任务重放。编排超时不会强制撤销已派发的模型作业。配置项与部署边界见[部署指南](DEPLOYMENT.md)，机制与源码见[架构设计](ARCHITECTURE.md)。
