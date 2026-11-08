# 后端工作流与数据库修复

工作流入口、步骤执行和动态实体 API 共用同一套会话与字段转换规则。代码中的中文注释说明了保存顺序、实例冲突、条件选择、类型转换和 DDL 的处理原因。

## 从表单到数据库

用户命中工作流后，入口从开始节点的实际连线确定。入口表单与后续表单都带有实例 ID 和节点 ID；重新开始会创建新实例，旧表单提交会被拒绝。

提交时先取得该用户的执行锁，再校验实例和当前节点。写接口在表单模式下等待 `submit`，执行成功才合并输出并推进步骤；HTTP 200 中的业务错误也会阻止推进。条件、自动 API 和通知可以连续执行，遇到表单停止等待，自动循环会报错。

动态实体 API 和实体管理接口共用字段转换、默认值、验证和编码。记录写入与计数更新在同一事务中执行；SQL 参数不会混入未声明的工作流上下文字段。

| 代码入口 | 主要职责 |
| --- | --- |
| [workflow_graph.py](../backend/app/services/workflow_graph.py) | 校验连线、重建父节点、检查可达性 |
| [workflow_session_service.py](../backend/app/services/workflow_session_service.py) | 当前会话、实例快照、TTL、版本比较和执行锁 |
| [workflow_execution_service.py](../backend/app/services/workflow_execution_service.py) | 当前步骤、业务 API、分支、通知及等待界面 |
| [workflow_context.py](../backend/app/services/workflow_context.py) | 嵌套变量、响应解析和表单实例绑定 |
| [entity_storage.py](../backend/app/services/entity_storage.py) | 字段转换、默认值、JSON 编解码与 SQL 类型 |
| [entity_service.py](../backend/app/services/entity_service.py) | 实体定义、物理表变更和业务记录事务 |
| [dynamic_router.py](../backend/app/core/dynamic_router.py) | 已配置业务 API 的实际请求处理 |

## 工作流配置规则

- 草稿可以保留尚未连完的图；启用时必须有一个开始节点、至少一个结束节点，所有节点都能从入口到达并能通往终点。
- `child_nodes` 是连线的权威字段，顺序决定条件匹配顺序。默认分支应放在条件分支之后。只有缺少该字段时才导入旧 `nextSteps`；明确的空列表不会恢复旧连线。
- 参数支持 `${enabled}`、`${lookup_result.items[0].id}`。纯变量保留布尔、数字、数组和对象类型，避免 `False`、`0` 被转成文本或丢掉。
- 条件表达式支持单字段比较，例如 `lookup_result.total > 0`；它不执行 JavaScript 或 Python 代码。保留 `form_completed` 和旧 `config.conditions` 的兼容。
- 写接口只有明确设置 `ui_mode=auto` 才自动执行。普通表单写接口需要提交；旧 `user_input` 节点仍能生成交互表单。
- 通知按实例和节点去重。用户重新开始同一工作流后，可以再次收到该实例对应的通知。

## 实体结构与数据

实体保存先检查并应用物理表变更，再更新配置定义。建表或改表失败时返回失败，不留下声称保存成功的新定义。

`False`、`0`、空列表都是有效默认值。创建和更新使用相同转换规则，多选字段按 JSON 存储，带时区的日期时间转为 UTC。唯一性检查使用当前事务；记录计数通过 SQL 原子更新。

有数据的列不自动转换或收窄类型。移除字段保留旧列与历史值，必要时释放旧列的必填约束，使后续新记录仍可写入。MySQL 使用 8.0.13 及以上版本支持的表达式默认值和 DDL。

工作流实例来自 Redis 会话快照，保存期限由 `REDIS_SESSION_TTL` 决定。Redis 不可用时使用有容量限制的本地缓存；尚未同步的数据不能跨进程共享，也不会在进程重启后恢复。实例历史不是永久 SQL 归档。

## 验证方式

默认回归只使用内存 SQLite、合成登录令牌、模型输出和 Redis 替身。HTTP 测试通过 ASGI 在同一进程执行真实工作流与动态 API，不启动业务服务，也不读取本地 `.env`。

```bash
python -m unittest discover -s backend/tests/regression -v
```

复用已有 Python 环境即可运行，不需要在本机安装新依赖。不要直接执行整个历史 `backend/tests/`，其中包含依赖实际服务或写业务数据的脚本。

[后端 CI](../.github/workflows/backend-regressions.yml)另提供临时 MySQL 8 和 Redis 7 服务。MySQL 测试只接受 `ailf_regression_` 前缀的本机测试库；Redis 测试只操作随机测试用户和实例键，不使用 `FLUSHDB`。这些服务与业务库分开。

已验证的本地范围包括表单提交到动态 API 的落库链路；模型意图与槽位使用替身，完整 GPU、Celery 作业和真实业务配置仍需单独验收。
