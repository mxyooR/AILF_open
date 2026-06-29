"""AILF Backend 启动入口

所有配置从 .env 文件读取，详见 .env 文件注释
"""
import sys
import os

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=False)

# 添加 app 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    print(f"🚀 启动服务器 | DEBUG={settings.DEBUG} | LOG_LEVEL={settings.LOG_LEVEL}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_excludes=["logs", "*.log", "__pycache__"] if settings.DEBUG else None,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.ENABLE_ACCESS_LOG
    )
