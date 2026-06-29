"""
统一日志管理配置模块
提供全局日志配置和日志记录器
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler
import platform


class LoggerConfig:
    """日志配置类"""
    
    # 日志级别映射
    LEVEL_MAP = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # 日志格式
    DETAILED_FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
    )
    
    SIMPLE_FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    CONSOLE_FORMAT = (
        "%(levelname)-8s | %(name)s | %(message)s"
    )
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        初始化日志配置
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录，默认为 backend/logs
            enable_file_logging: 是否启用文件日志
            enable_console_logging: 是否启用控制台日志
            max_bytes: 单个日志文件最大大小
            backup_count: 保留的日志文件数量
        """
        self.log_level = self.LEVEL_MAP.get(log_level.upper(), logging.INFO)
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.is_windows = platform.system() == 'Windows'
        
        # 设置日志目录
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            # 默认为 backend/logs
            backend_dir = Path(__file__).parent.parent.parent
            self.log_dir = backend_dir / "logs"
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理旧日志文件（保留最近 backup_count 天）
        self._cleanup_old_logs()
        
        # 日志文件路径 - 使用日期命名避免文件占用问题
        today = datetime.now().strftime("%Y%m%d")
        self.app_log_file = self.log_dir / f"app_{today}.log"
        self.error_log_file = self.log_dir / f"error_{today}.log"
        self.access_log_file = self.log_dir / f"access_{today}.log"
    
    def _cleanup_old_logs(self):
        """清理旧的日志文件"""
        try:
            import time
            current_time = time.time()
            # 保留天数（backup_count 天）
            retention_days = self.backup_count
            retention_seconds = retention_days * 24 * 60 * 60
            
            # 遍历日志目录
            for log_file in self.log_dir.glob("*.log*"):
                try:
                    # 获取文件修改时间
                    file_mtime = log_file.stat().st_mtime
                    # 如果文件超过保留期限，删除
                    if current_time - file_mtime > retention_seconds:
                        log_file.unlink()
                except Exception as e:
                    # 忽略单个文件删除失败
                    pass
        except Exception as e:
            # 清理失败不影响日志系统启动
            pass
    
    def setup_logger(
        self,
        logger_name: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """
        设置并返回日志记录器
        
        Args:
            logger_name: 日志记录器名称，默认为 root logger
            log_file: 自定义日志文件路径
            
        Returns:
            配置好的日志记录器
        """
        # 获取或创建 logger
        logger = logging.getLogger(logger_name)
        
        # 如果 logger 已经有 handlers，检查是否是我们配置的
        # 只有当 handlers 为空时才添加新的 handlers
        if logger.handlers:
            return logger
        
        logger.setLevel(self.log_level)
        
        # 添加控制台处理器
        if self.enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = logging.Formatter(
                self.CONSOLE_FORMAT,
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if self.enable_file_logging:
            # 应用日志（所有级别）
            if log_file:
                file_path = self.log_dir / log_file
            else:
                file_path = self.app_log_file
            
            file_handler_added = False
            error_handler_added = False
            
            try:
                # 使用 RotatingFileHandler 按大小分割日志（Windows 兼容性更好）
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                    delay=True  # 延迟打开文件，避免占用
                )
                file_handler.setLevel(self.log_level)
                file_formatter = logging.Formatter(
                    self.DETAILED_FORMAT,
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
                file_handler_added = True
            except Exception as e:
                sys.stderr.write(f"⚠️ 无法创建应用日志文件处理器: {e}\n")
            
            try:
                # 错误日志（仅 ERROR 及以上）
                error_handler = RotatingFileHandler(
                    self.error_log_file,
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                    delay=True  # 延迟打开文件，避免占用
                )
                error_handler.setLevel(logging.ERROR)
                error_formatter = logging.Formatter(
                    self.DETAILED_FORMAT,
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                error_handler.setFormatter(error_formatter)
                logger.addHandler(error_handler)
                error_handler_added = True
            except Exception as e:
                sys.stderr.write(f"⚠️ 无法创建错误日志文件处理器: {e}\n")
            
            # 如果文件日志完全失败，确保至少有控制台日志
            if not file_handler_added and not error_handler_added:
                sys.stderr.write("⚠️ 文件日志初始化失败，降级到仅控制台日志\n")
                if not self.enable_console_logging:
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(self.log_level)
                    console_formatter = logging.Formatter(
                        self.CONSOLE_FORMAT,
                        datefmt="%H:%M:%S"
                    )
                    console_handler.setFormatter(console_formatter)
                    logger.addHandler(console_handler)
        
        # 防止日志传播到父 logger
        logger.propagate = False
        
        return logger


class AILFLogger:
    """AILF 统一日志管理器"""
    
    _instance = None
    _config: Optional[LoggerConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(
        cls,
        log_level: str = None,
        log_dir: Optional[str] = None,
        enable_file_logging: bool = None,
        enable_console_logging: bool = True
    ):
        """
        初始化全局日志配置
        
        Args:
            log_level: 日志级别（默认从环境变量 LOG_LEVEL 读取）
            log_dir: 日志目录
            enable_file_logging: 是否启用文件日志（默认从环境变量读取）
            enable_console_logging: 是否启用控制台日志
        """
        # 从环境变量读取默认值，解决模块导入顺序问题
        if log_level is None:
            log_level = os.getenv("LOG_LEVEL", "INFO")
        if enable_file_logging is None:
            enable_file_logging = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
        cls._config = LoggerConfig(
            log_level=log_level,
            log_dir=log_dir,
            enable_file_logging=enable_file_logging,
            enable_console_logging=enable_console_logging
        )
        
        # 配置 root logger
        cls._config.setup_logger()
        
        # 配置第三方库的日志级别
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)  # 启用访问日志
        logging.getLogger("fastapi").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("transformers").setLevel(logging.WARNING)
        logging.getLogger("torch").setLevel(logging.WARNING)
        
        # 使用 stderr 输出初始化信息，避免循环依赖
        import sys
        sys.stderr.write(f"✅ 日志系统已初始化 | 级别: {log_level} | 目录: {cls._config.log_dir}\n")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称（通常使用 __name__）
            
        Returns:
            日志记录器
        """
        if cls._config is None:
            # 如果未初始化，从 Settings 读取配置进行自动初始化
            from app.config import settings
            cls.initialize(
                log_level=settings.LOG_LEVEL,
                log_dir=settings.LOG_DIR if settings.LOG_DIR else None,
                enable_file_logging=settings.ENABLE_FILE_LOGGING,
                enable_console_logging=settings.ENABLE_CONSOLE_LOGGING
            )
        
        return cls._config.setup_logger(name)
    
    @classmethod
    def shutdown(cls):
        """关闭所有日志处理器，释放文件句柄"""
        try:
            # 关闭所有 logger 的 handlers
            loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
            for logger in loggers:
                handlers = logger.handlers[:]
                for handler in handlers:
                    try:
                        handler.close()
                        logger.removeHandler(handler)
                    except:
                        pass
            
            # 关闭 logging 模块
            logging.shutdown()
        except Exception as e:
            sys.stderr.write(f"⚠️ 关闭日志系统时出错: {e}\n")


# 便捷函数
def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称，默认为调用模块的 __name__
        
    Returns:
        日志记录器
        
    Example:
        from app.core.logging_config import get_logger
        
        logger = get_logger(__name__)
        logger.info("这是一条信息日志")
        logger.error("这是一条错误日志")
    """
    return AILFLogger.get_logger(name or "ailf")


# 初始化全局日志配置（在导入时自动执行）
def init_logging(
    log_level: str = None,
    log_dir: Optional[str] = None,
    enable_file_logging: bool = None,
    enable_console_logging: bool = True
):
    """
    初始化日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录
        enable_file_logging: 是否启用文件日志
        enable_console_logging: 是否启用控制台日志
    """
    AILFLogger.initialize(
        log_level=log_level,
        log_dir=log_dir,
        enable_file_logging=enable_file_logging,
        enable_console_logging=enable_console_logging
    )


def shutdown_logging():
    """关闭日志系统，释放所有文件句柄"""
    AILFLogger.shutdown()


def cleanup_old_logs(log_dir: str = None, days: int = 7):
    """
    手动清理旧日志文件
    
    Args:
        log_dir: 日志目录，默认为 backend/logs
        days: 保留天数，默认 7 天
    """
    try:
        import time
        from pathlib import Path
        
        if log_dir:
            log_path = Path(log_dir)
        else:
            backend_dir = Path(__file__).parent.parent.parent
            log_path = backend_dir / "logs"
        
        if not log_path.exists():
            return
        
        current_time = time.time()
        retention_seconds = days * 24 * 60 * 60
        
        deleted_count = 0
        for log_file in log_path.glob("*.log*"):
            try:
                file_mtime = log_file.stat().st_mtime
                if current_time - file_mtime > retention_seconds:
                    log_file.unlink()
                    deleted_count += 1
            except Exception:
                pass
        
        if deleted_count > 0:
            sys.stderr.write(f"✅ 清理了 {deleted_count} 个旧日志文件\n")
    except Exception as e:
        sys.stderr.write(f"⚠️ 清理日志文件失败: {e}\n")

