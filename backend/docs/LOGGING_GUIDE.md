# AILF 统一日志管理使用指南

## 📋 概述

AILF 项目使用统一的日志管理系统，提供：
- ✅ 控制台日志输出
- ✅ 文件日志记录（自动轮转）
- ✅ 错误日志单独记录
- ✅ 灵活的日志级别配置
- ✅ 第三方库日志过滤

## 🚀 快速开始

### 1. 在代码中使用日志

```python
from app.core.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 2. 配置日志级别

在 `.env` 文件中配置：

```bash
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 日志目录（留空使用默认 backend/logs）
LOG_DIR=

# 是否启用文件日志
ENABLE_FILE_LOGGING=true

# 是否启用控制台日志
ENABLE_CONSOLE_LOGGING=true
```

## 📁 日志文件

日志文件默认保存在 `backend/logs/` 目录：

```
backend/logs/
├── app.log          # 应用日志（所有级别）
├── error.log        # 错误日志（仅 ERROR 及以上）
└── access.log       # 访问日志（预留）
```

### 日志轮转策略

- **单文件大小**: 10MB
- **保留文件数**: 5 个
- **自动轮转**: 文件达到大小限制时自动创建新文件
- **旧文件命名**: `app.log.1`, `app.log.2`, ...

## 🎨 日志格式

### 控制台格式（简洁）
```
INFO     | app.main | 🚀 AILF Backend 启动中...
```

### 文件格式（详细）
```
2024-12-06 19:30:00 | INFO     | app.main | main.py:74 | create_app() | 🚀 AILF Backend 启动中...
```

## 📝 使用示例

### 基础日志记录

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data):
    logger.info(f"开始处理数据: {len(data)} 条记录")
    
    try:
        # 处理逻辑
        result = do_something(data)
        logger.info(f"✅ 数据处理成功: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ 数据处理失败: {str(e)}", exc_info=True)
        raise
```

### 带上下文的日志

```python
logger.info(f"用户 {user_id} 执行操作: {action}")
logger.warning(f"API 调用超时: {api_url} (耗时: {elapsed}s)")
logger.error(f"数据库连接失败: {db_host}:{db_port}")
```

### 记录异常堆栈

```python
try:
    risky_operation()
except Exception as e:
    # exc_info=True 会自动记录完整的异常堆栈
    logger.error("操作失败", exc_info=True)
```

## 🔧 高级配置

### 自定义日志记录器

```python
from app.core.logging_config import AILFLogger

# 创建自定义日志记录器
custom_logger = AILFLogger.get_logger("my_module")
custom_logger.info("自定义模块日志")
```

### 动态修改日志级别

```python
import logging

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)  # 临时提升日志级别
```

### 禁用第三方库日志

默认已禁用以下库的详细日志：
- uvicorn
- fastapi
- sqlalchemy
- transformers
- torch

如需调整：

```python
import logging

# 启用 SQLAlchemy 详细日志
logging.getLogger("sqlalchemy").setLevel(logging.INFO)
```

## 🎯 最佳实践

### 1. 使用合适的日志级别

```python
# ✅ 正确
logger.debug("变量值: x=%d, y=%d", x, y)  # 调试信息
logger.info("用户登录成功: %s", username)  # 重要事件
logger.warning("缓存未命中，使用默认值")    # 警告
logger.error("API 调用失败: %s", error)    # 错误
logger.critical("数据库连接丢失！")         # 严重错误

# ❌ 错误
logger.info("x=%d, y=%d", x, y)  # 应该用 debug
logger.error("用户登录成功")      # 应该用 info
```

### 2. 避免敏感信息泄露

```python
# ❌ 错误 - 记录密码
logger.info(f"用户登录: {username}, 密码: {password}")

# ✅ 正确 - 隐藏敏感信息
logger.info(f"用户登录: {username}")
```

### 3. 使用结构化日志

```python
# ✅ 推荐 - 使用格式化字符串
logger.info("处理订单: order_id=%s, amount=%.2f", order_id, amount)

# ❌ 不推荐 - 字符串拼接
logger.info("处理订单: order_id=" + str(order_id) + ", amount=" + str(amount))
```

### 4. 记录关键业务事件

```python
# 用户操作
logger.info(f"👤 用户 {user_id} 登录成功")
logger.info(f"📝 用户 {user_id} 创建工作流: {workflow_name}")

# 系统事件
logger.info("🚀 AI 模型加载完成")
logger.warning("⚠️ 数据库连接池达到 80% 容量")
logger.error("❌ Redis 连接失败，切换到内存存储")
```

## 🐛 调试技巧

### 开发环境启用 DEBUG 日志

```bash
# .env
LOG_LEVEL=DEBUG
```

### 生产环境使用 INFO 或 WARNING

```bash
# .env
LOG_LEVEL=INFO
```

### 查看日志文件

```bash
# 实时查看应用日志
tail -f backend/logs/app.log

# 查看错误日志
tail -f backend/logs/error.log

# 搜索特定内容
grep "ERROR" backend/logs/app.log
```

## 📊 日志分析

### 统计错误数量

```bash
grep -c "ERROR" backend/logs/app.log
```

### 查找特定用户的操作

```bash
grep "user_id=123" backend/logs/app.log
```

### 分析性能问题

```bash
# 查找耗时操作
grep "耗时" backend/logs/app.log | sort -k5 -n
```

## 🔒 生产环境建议

1. **日志级别**: 使用 `INFO` 或 `WARNING`
2. **文件日志**: 必须启用
3. **日志轮转**: 保持默认配置（10MB, 5个文件）
4. **敏感信息**: 严格过滤密码、密钥等
5. **日志监控**: 配置日志聚合工具（如 ELK, Loki）

## 📚 相关文档

- [Python logging 官方文档](https://docs.python.org/3/library/logging.html)
- [日志最佳实践](https://docs.python-guide.org/writing/logging/)
- [FastAPI 日志配置](https://fastapi.tiangolo.com/tutorial/logging/)
