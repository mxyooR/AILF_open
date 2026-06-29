"""
AILF Backend FastAPI应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime

from app.config import settings
from app.core.logging_config import init_logging, get_logger
from app.api.v1.auth import router as auth_router
from app.api.v1.user_auth import router as user_auth_router
from app.api.v1.user_management import router as user_management_router
from app.api.v1.scenario import router as scenario_router
from app.api.v1.template import router as template_router
from app.api.v1.entity import router as entity_router
from app.api.v1.relationship import router as relationship_router
from app.api.v1.ai import router as ai_router


from app.api.v1.workflow import router as workflow_router
from app.api.v1.api_route import router as api_route_router
from app.api.v1.role import router as role_router
from app.api.v1.permission_control import router as permission_control_router
from app.api.v1.config import router as config_router
from app.api.v1.configuration_status import router as configuration_status_router
from app.api.v1.registration_config import router as registration_config_router
from app.api.v1.file_upload import router as file_upload_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.dynamic_response import router as dynamic_response_router
from app.api.v1.service_package import router as service_package_router
from app.core.dynamic_router import init_dynamic_router
from app.core.role_db_init import init_role_database
from app.core.permission_control_db_init import init_permission_control_database
from app.core.user_db_init import init_user_database
from app.core.database import init_database, db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger = get_logger(__name__)
    logger.info("[Lifespan] 主后端启动完成（不加载模型）")
    
    yield  # 应用运行中
    
    # Shutdown: 清理资源
    logger.info("[Lifespan] 应用关闭，清理资源...")
    
    # 关闭日志系统，释放文件句柄
    try:
        from app.core.logging_config import shutdown_logging
        shutdown_logging()
    except Exception as e:
        import sys
        sys.stderr.write(f"⚠️ 关闭日志系统失败: {e}\n")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""

    # 初始化日志系统
    init_logging(
        log_level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR if settings.LOG_DIR else None,
        enable_file_logging=settings.ENABLE_FILE_LOGGING,
        enable_console_logging=settings.ENABLE_CONSOLE_LOGGING
    )
    logger = get_logger(__name__)
    logger.info("AILF Backend 启动中...")

    # 初始化数据库
    if not init_database():
        logger.error("❌ 数据库初始化失败")
        raise RuntimeError("数据库初始化失败")
    logger.info("✅ 数据库初始化成功")

    app = FastAPI(
        lifespan=lifespan,  # 使用 lifespan 管理模型加载
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="AILF (AI Language Frontend) 后端API服务",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 请求日志中间件 - 根据配置决定是否启用
    if settings.ENABLE_ACCESS_LOG:
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            """记录所有 HTTP 请求"""
            import time
            import sys
            start_time = time.time()
            
            # 输出请求日志
            client_ip = request.client.host if request.client else "unknown"
            sys.stderr.write(f"{request.method} {request.url.path} from {client_ip}\n")
            sys.stderr.flush()
            
            response = await call_next(request)
            
            # 计算耗时并记录响应
            process_time = (time.time() - start_time) * 1000
            sys.stderr.write(f"{request.method} {request.url.path} -> {response.status_code} ({process_time:.2f}ms)\n")
            sys.stderr.flush()
            
            return response
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 初始化角色管理数据库
    logger.info("初始化角色管理数据库...")
    init_role_database()

    # 初始化权限控制数据库
    logger.info("初始化权限控制数据库...")
    init_permission_control_database()

    # 初始化用户认证数据库
    logger.info("初始化用户认证数据库...")
    init_user_database()

    # 注册路由 - 统一使用 /api/v1/ 前缀
    # 注意：具体路由必须在通配符路由之前注册，避免被拦截

    # 1. 先注册具体路由（避免被通配符路由拦截）
    app.include_router(workflow_router, prefix="/api/v1")
    app.include_router(role_router, prefix="/api/v1")
    app.include_router(permission_control_router, prefix="/api/v1")
    app.include_router(config_router, prefix="/api/v1")
    app.include_router(configuration_status_router, prefix="/api/v1")
    app.include_router(registration_config_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(user_auth_router, prefix="/api/v1")
    app.include_router(user_management_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    app.include_router(scenario_router, prefix="/api/v1")
    app.include_router(template_router, prefix="/api/v1")
    app.include_router(entity_router, prefix="/api/v1")
    app.include_router(relationship_router, prefix="/api/v1")
    app.include_router(ai_router, prefix="/api/v1")


    app.include_router(file_upload_router, prefix="/api/v1")
    app.include_router(dynamic_response_router, prefix="/api/v1")
    app.include_router(service_package_router, prefix="/api/v1")

    # 2. 最后注册通配符路由（避免拦截其他路由）
    app.include_router(api_route_router, prefix="/api/v1/routes")

    # 最后加载动态业务路由，确保固定系统 API 优先匹配
    init_dynamic_router(app)
    
    # 全局异常处理器
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器 - 使用统一响应格式"""
        from app.core.response import ResponseMeta
        import time
        
        # 如果detail已经是统一格式（包含code, message, data, meta），直接返回
        if isinstance(exc.detail, dict) and "meta" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # 否则包装成统一格式
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", "请求失败"),
                "data": exc.detail if isinstance(exc.detail, dict) else None,
                "meta": ResponseMeta().to_dict()
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """数据验证异常处理器 - 使用统一响应格式"""
        from app.core.response import ResponseMeta
        
        logger.warning(f"收到422验证错误: {request.method} {request.url}")
        logger.warning(f"验证错误详情: {exc.errors()}")
        
        # 避免重复读取请求体导致ClientDisconnect错误
        try:
            body = await request.body()
            logger.debug(f"请求体: {body}")
        except Exception as e:
            logger.debug(f"请求体读取失败: {str(e)}")

        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "数据验证失败",
                "data": {
                    "error": "validation_error",
                    "details": exc.errors(),
                    "suggestion": "请检查请求参数格式"
                },
                "meta": ResponseMeta().to_dict()
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器 - 使用统一响应格式"""
        from app.core.response import ResponseMeta
        import traceback
        
        error_details = f"{str(exc)}\n{traceback.format_exc()}" if settings.DEBUG else "服务器内部错误"
        logger.error(f"未捕获的异常: {error_details}")

        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "内部服务器错误",
                "data": {
                    "error": "internal_server_error",
                    "details": error_details
                },
                "meta": ResponseMeta().to_dict()
            }
        )
    
    # 健康检查接口
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """健康检查接口"""
        return {
            "code": 200,
            "message": "服务正常",
            "data": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": settings.VERSION
            }
        }

    @app.get("/health/database", tags=["健康检查"])
    async def database_health_check():
        """数据库健康检查端点"""
        import time
        health = db_manager.health_check()
        connection_info = db_manager.get_connection_info()

        return {
            "code": 200,
            "message": "数据库状态检查",
            "data": {
                "database": health,
                "connection_pool": connection_info,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            }
        }

    # 根路径
    @app.get("/", tags=["根路径"])
    async def root():
        """根路径接口"""
        return {
            "code": 200,
            "message": "AILF Backend API",
            "data": {
                "name": settings.APP_NAME,
                "version": settings.VERSION,
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    
    return app


# 创建应用实例
app = create_app()
