"""
API路由管理模块数据库模型
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RouteStatus(enum.Enum):
    """路由状态枚举"""
    ACTIVE = "active"      # 激活
    INACTIVE = "inactive"  # 停用


class HandlerType(enum.Enum):
    """Handler type enum."""
    ENTITY_CRUD = "entity_crud"
    CUSTOM_FUNCTION = "custom_function"
    PROXY = "proxy"
    WORKFLOW = "workflow"
    STATIC_DATA = "static_data"
    SCRIPT = "script"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    IMAGE_DISPLAY = "image_display"
    MEDIA_STREAMING = "media_streaming"

class ParameterLocation(enum.Enum):
    """参数位置枚举"""
    QUERY = "query"    # 查询参数
    PATH = "path"      # 路径参数
    HEADER = "header"  # 请求头参数
    BODY = "body"      # 请求体参数


class APIRouteDBModel(Base):
    """API路由数据库模型"""
    __tablename__ = "api_routes"
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="路由ID")
    api_id = Column(String(100), unique=True, nullable=False, comment="API标识符")
    name = Column(String(200), nullable=False, comment="路由名称")
    endpoint = Column(String(500), nullable=False, comment="API端点")
    method = Column(String(10), nullable=False, comment="HTTP方法")
    description = Column(Text, comment="路由描述")
    
    # 配置信息
    auth_required = Column(Boolean, default=True, comment="是否需要认证")
    permission_config = Column(JSON, comment="权限配置")
    status = Column(SQLEnum(RouteStatus), default=RouteStatus.ACTIVE, comment="路由状态")
    
    # 处理器配置
    handler_type = Column(String(50), nullable=False, comment="处理器类型")
    handler_config = Column(JSON, comment="处理器配置")
    
    # 参数和响应配置
    parameters_config = Column(JSON, comment="参数配置")
    responses_config = Column(JSON, comment="响应配置")
    dynamic_rules_config = Column(JSON, comment="动态响应规则配置")
    
    # 统计信息
    call_count = Column(Integer, default=0, comment="调用次数")
    last_called = Column(DateTime, comment="最后调用时间")
    avg_response_time = Column(Integer, default=0, comment="平均响应时间(ms)")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )


class APIRouteParameterDBModel(Base):
    """API路由参数数据库模型"""
    __tablename__ = "api_route_parameters"
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="参数ID")
    route_id = Column(String(50), nullable=False, comment="路由ID")
    name = Column(String(100), nullable=False, comment="参数名称")
    type = Column(String(50), nullable=False, comment="参数类型")
    location = Column(SQLEnum(ParameterLocation), nullable=False, comment="参数位置")
    required = Column(Boolean, default=False, comment="是否必填")
    description = Column(Text, comment="参数描述")
    
    # 验证配置
    validation_config = Column(JSON, comment="验证配置")
    default_value = Column(Text, comment="默认值")
    
    # 排序
    order_index = Column(Integer, default=0, comment="排序索引")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )


class APIRouteResponseDBModel(Base):
    """API路由响应数据库模型"""
    __tablename__ = "api_route_responses"
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="响应ID")
    route_id = Column(String(50), nullable=False, comment="路由ID")
    status_code = Column(String(10), nullable=False, comment="状态码")
    description = Column(Text, comment="响应描述")
    
    # 响应配置
    schema_config = Column(JSON, comment="响应Schema配置")
    headers_config = Column(JSON, comment="响应头配置")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )


class APIRouteCallLogDBModel(Base):
    """API路由调用日志数据库模型"""
    __tablename__ = "api_route_call_logs"
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="日志ID")
    route_id = Column(String(50), nullable=False, comment="路由ID")
    
    # 请求信息
    request_method = Column(String(10), comment="请求方法")
    request_path = Column(String(500), comment="请求路径")
    request_params = Column(JSON, comment="请求参数")
    request_headers = Column(JSON, comment="请求头")
    request_body = Column(Text, comment="请求体")
    
    # 响应信息
    response_status = Column(Integer, comment="响应状态码")
    response_time = Column(Integer, comment="响应时间(ms)")
    response_size = Column(Integer, comment="响应大小(bytes)")
    
    # 客户端信息
    client_ip = Column(String(50), comment="客户端IP")
    user_agent = Column(Text, comment="用户代理")
    user_id = Column(String(50), comment="用户ID")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 索引
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
