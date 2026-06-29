# 日志系统说明

## 概述

AILF 后端使用统一的日志管理系统，支持控制台和文件日志输出。日志系统针对 Windows 环境进行了优化，解决了文件占用和写入失败的问题。

## 主要特性

### 1. Windows 兼容性优化

- **延迟文件打开**：使用 `delay=True` 参数，避免不必要的文件占用
- **按日期命名**：日志文件使用日期命名（如 `app_20260117.log`），避免文件轮转时的占用问题
- **自动降级**：如果文件日志失败，自动降级到控制台日志，确保应用正常运行
- **优雅关闭**：应用关闭时正确释放所有文件句柄

### 2. 日志轮转

- **按大小轮转**：单个日志文件最大 10MB
- **保留数量**：默认保留最近 5 个备份文件
- **自动清理**：启动时自动清理超过保留期限的旧日志

### 3. 多级别日志

- **应用日志**：`app_YYYYMMDD.log` - 记录所有级别的日志
- **错误日志**：`error_YYYYMMDD.log` - 仅记录 ERROR 及以上级别
- **访问日志**：`access_YYYYMMDD.log` - HTTP 请求访问日志（可选）

## 使用方法

### 基本使用

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("⚠️ 警告信息")
logger.error("❌ 错误信息")
```

### 配置日志级别

在 `.env` 文件中配置：

```env
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 是否启用文件日志
ENABLE_FILE_LOGGING=true

# 是否启用控制台日志
ENABLE_CONSOLE_LOGGING=true

# 日志目录（可选，默认为 backend/logs）
LOG_DIR=./logs
```

### 手动清理日志

运行清理脚本：

```bash
# 清理 7 天前的日志（默认）
python backend/scripts/cleanup_logs.py

# 清理 30 天前的日志
python backend/scripts/cleanup_logs.py --days 30

# 指定日志目录
python backend/scripts/cleanup_logs.py --log-dir /path/to/logs
```

在代码中清理：

```python
from app.core.logging_config import cleanup_old_logs

# 清理 7 天前的日志
cleanup_old_logs(days=7)
```

## 日志格式

### 文件日志格式（详细）

```
2026-01-17 10:30:45 | INFO     | app.services.user_service | user_service.py:123 | create_user() | 创建用户成功
```

包含：
- 时间戳
- 日志级别
- 模块名称
- 文件名和行号
- 函数名
- 日志消息

### 控制台日志格式（简洁）

```
INFO     | app.services.user_service | 创建用户成功
```

包含：
- 日志级别
- 模���名称
- 日志消息

## 日志规范

### Emoji 使用规范

**保留的重要 Emoji**：
- ✅ 成功操作
- ❌ 错误/失败
- ⚠️ 警告

**移除的装饰性 Emoji**：
- 🔥🎯📝🔍🔄📊🤖🚀📥📁🔧🧹🔗🗑️💾🎉👥🔑 等

### 日志级别使用

- **DEBUG**：详细的调试信息，仅在开发时使用
- **INFO**：重要的业务操作（创建、更新、删除等）
- **WARNING**：警告信息，不影响正常运行
- **ERROR**：错误信息，需要关注

### 示例

```python
# ✅ 好的日志
logger.info("用户登录成功: user_id=123")
logger.warning("⚠️ 数据库连接池接近上限")
logger.error("❌ 发送邮件失败: SMTP 连接超时")

# ❌ 避免的日志
logger.info("🎉🎉🎉 用户登录成功！！！")
logger.info("🔥 超级厉害的功能启动了")
```

## 故障排查

### 问题：日志文件无法写入

**原因**：Windows 下文件被占用

**解决方案**：
1. 系统会自动降级到控制台日志
2. 检查是否有其他进程占用日志文件
3. 重启应用，日志系统会创建新的日期文件

### 问题：日志文件过大

**解决方案**：
1. 日志会自动轮转（超过 10MB）
2. 手动运行清理脚本：`python backend/scripts/cleanup_logs.py`
3. 调整日志级别为 WARNING 或 ERROR

### 问题：找不到日志文件

**检查位置**：
- 默认位置：`backend/logs/`
- 文件名格式：`app_YYYYMMDD.log`、`error_YYYYMMDD.log`

## 性能优化

1. **延迟打开**：文件只在需要写入时才打开
2. **异步写入**：日志写入不阻塞主线程
3. **自动清理**：定期清理旧日志，避免磁盘占满
4. **级别过滤**：生产环境使用 INFO 或 WARNING 级别

## 最佳实践

1. **使用模块名称**：`logger = get_logger(__name__)`
2. **避免敏感信息**：不要记录密码、token 等敏感数据
3. **结构化日志**：使用清晰的格式，便于搜索和分析
4. **适当的级别**：根据重要性选择合适的日志级别
5. **定期清理**：设置定时任务清理旧日志
