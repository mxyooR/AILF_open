# AILF 后端架构文档

## 📋 概述

AILF后端采用FastAPI框架，提供RESTful API服务，支持动态业务场景配置、工作流执行和AI交互。

## 🏗️ 整体架构

```
AILF Backend
├── API Layer (API层)
│   ├── 认证路由
│   ├── 配置管理路由
│   ├── 业务实体路由
│   ├── 工作流路由
│   └── AI交互路由
├── Service Layer (服务层)
│   ├── 认证服务
│   ├── 场景管理服务
│   ├── 实体管理服务
│   ├── 工作流引擎
│   ├── 表单引擎
│   └── AI服务
├── Core Layer (核心层)
│   ├── 动态路由管理器
│   ├── 权限控制器
│   ├── 数据访问层
│   └── 缓存管理器
└── Data Layer (数据层)
    ├── SQLite数据库
    ├── JSON配置文件
    └── 生成代码文件
```

## 🔧 技术栈

- **框架**: FastAPI 0.104+
- **数据库**: SQLite + JSON文件存储
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT Token
- **AI集成**: 阿里云百炼API
- **任务队列**: Celery (可选)
- **缓存**: Redis (可选)
- **文件存储**: 本地文件系统

## 📁 目录结构

```
backend/
├── app/
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── api/                      # API路由层
│   │   ├── __init__.py
│   │   └── v1/                   # API版本1
│   │       ├── __init__.py
│   │       ├── auth.py           # 认证路由
│   │       ├── scenario.py       # 场景管理路由
│   │       ├── entities.py       # 实体管理路由
│   │       ├── workflows.py      # 工作流路由
│   │       ├── forms.py          # 表单路由
│   │       ├── routes.py         # 动态路由管理
│   │       ├── roles.py          # 角色管理路由
│   │       ├── permissions.py    # 权限管理路由

│   │       ├── ai.py             # AI交互路由
│   │       └── health.py         # 健康检查路由
│   ├── services/                 # 服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py       # 认证服务
│   │   ├── scenario_service.py   # 场景管理服务
│   │   ├── entity_service.py     # 实体管理服务
│   │   ├── workflow_service.py   # 工作流服务
│   │   ├── form_service.py       # 表单服务
│   │   ├── role_service.py       # 角色服务
│   │   ├── permission_service.py # 权限服务

│   │   └── ai_service.py         # AI服务
│   ├── core/                     # 核心层
│   │   ├── __init__.py
│   │   ├── auth/                 # 认证核心
│   │   │   ├── jwt_handler.py    # JWT处理
│   │   │   └── permissions.py    # 权限装饰器
│   │   ├── dynamic/              # 动态功能
│   │   │   ├── route_manager.py  # 动态路由管理器
│   │   │   ├── entity_manager.py # 实体管理器
│   │   │   ├── workflow_engine.py # 工作流引擎
│   │   │   └── form_engine.py    # 表单引擎

│   │   └── ai/                   # AI集成
│   │       ├── bailian_client.py # 百炼API客户端
│   │       ├── prompt_manager.py # 提示词管理
│   │       └── schema_generator.py # Schema生成器
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py               # 基础模型
│   │   ├── scenario.py           # 场景模型
│   │   ├── entity.py             # 实体模型
│   │   ├── workflow.py           # 工作流模型
│   │   ├── form.py               # 表单模型
│   │   ├── role.py               # 角色模型
│   │   └── permission.py         # 权限模型
│   ├── schemas/                  # Pydantic模式
│   │   ├── __init__.py
│   │   ├── auth.py               # 认证模式
│   │   ├── scenario.py           # 场景模式
│   │   ├── entity.py             # 实体模式
│   │   ├── workflow.py           # 工作流模式
│   │   ├── form.py               # 表单模式
│   │   └── common.py             # 通用模式
│   ├── database/                 # 数据库
│   │   ├── __init__.py
│   │   ├── connection.py         # 数据库连接
│   │   ├── migrations/           # 数据库迁移
│   │   └── seeds/                # 初始数据
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── file_utils.py         # 文件工具
│       ├── validation.py         # 验证工具
│       └── helpers.py            # 辅助函数
├── data/                         # 数据存储
│   ├── scenarios/                # 场景配置文件
│   ├── templates/                # 模板文件
│   ├── generated/                # 生成的代码
│   └── uploads/                  # 上传文件
├── tests/                        # 测试文件
├── requirements.txt              # 依赖包
└── Dockerfile                    # Docker配置
```

## 🔄 核心流程设计

### 1. 开发者配置流程

#### 场景配置流程
```python
# 场景服务流程
class ScenarioService:
    async def create_scenario(self, scenario_data: ScenarioCreate) -> Scenario:
        # 1. 验证场景配置
        validated_data = self.validate_scenario(scenario_data)
        
        # 2. 保存场景配置
        scenario = await self.save_scenario(validated_data)
        
        # 3. 初始化相关资源
        await self.initialize_scenario_resources(scenario)
        
        # 4. 触发后续流程
        await self.trigger_dependent_services(scenario)
        
        return scenario
```

#### 实体建模流程
```python
# 实体管理服务流程
class EntityService:
    async def create_entity(self, entity_data: EntityCreate) -> Entity:
        # 1. 验证实体定义
        validated_entity = self.validate_entity_definition(entity_data)
        
        # 2. 创建数据库表结构
        table_schema = await self.generate_table_schema(validated_entity)
        await self.create_database_table(table_schema)
        
        # 3. 生成API路由
        api_routes = await self.generate_entity_apis(validated_entity)
        await self.register_dynamic_routes(api_routes)
        
        # 4. 保存实体配置
        entity = await self.save_entity(validated_entity)
        
        return entity
```

#### 工作流设计流程
```python
# 工作流引擎
class WorkflowEngine:
    async def create_workflow(self, workflow_data: WorkflowCreate) -> Workflow:
        # 1. 验证工作流定义
        validated_workflow = self.validate_workflow_definition(workflow_data)
        
        # 2. 编译工作流步骤
        compiled_steps = await self.compile_workflow_steps(validated_workflow.steps)
        
        # 3. 创建执行器
        executor = await self.create_workflow_executor(compiled_steps)
        
        # 4. 注册工作流处理器
        await self.register_workflow_handler(validated_workflow.id, executor)
        
        # 5. 保存工作流配置
        workflow = await self.save_workflow(validated_workflow)
        
        return workflow
```

### 2. AI交互流程

#### 智能命令处理
```python
# AI服务
class AIService:
    async def process_command(self, command: str, context: dict) -> AIResponse:
        # 1. 意图分析
        intent = await self.analyze_intent(command)

        # 2. 权限检查
        permissions = await self.check_user_permissions(context.user_id)

        # 3. 生成amis schema
        schema = await self.generate_amis_schema(intent, permissions)

        # 4. 返回响应
        return AIResponse(
            intent=intent,
            schema=schema,
            response_text=await self.generate_response_text(intent)
        )
```

### 3. 最终用户交互流程

#### AI命令处理流程
```python
# AI服务
class AIService:
    async def process_command(self, command: str, context: dict) -> AIResponse:
        # 1. 命令理解和意图识别
        intent = await self.analyze_command_intent(command)
        
        # 2. 获取相关场景配置
        scenario = await self.get_current_scenario(context)
        
        # 3. 生成amis schema
        schema = await self.generate_amis_schema(intent, scenario)
        
        # 4. 优化和验证schema
        optimized_schema = await self.optimize_schema(schema)
        
        # 5. 返回响应
        return AIResponse(
            schema=optimized_schema,
            response_text=await self.generate_response_text(intent)
        )
```

#### 工作流执行流程
```python
# 工作流执行引擎
class WorkflowExecutor:
    async def execute_workflow(self, workflow_id: str, input_data: dict) -> WorkflowInstance:
        # 1. 创建工作流实例
        instance = await self.create_workflow_instance(workflow_id, input_data)
        
        # 2. 执行工作流步骤
        current_step = await self.get_start_step(workflow_id)
        
        while current_step:
            # 执行当前步骤
            step_result = await self.execute_step(current_step, instance)
            
            # 更新实例状态
            await self.update_instance_state(instance, step_result)
            
            # 获取下一步骤
            current_step = await self.get_next_step(current_step, step_result)
        
        # 3. 完成工作流
        await self.complete_workflow_instance(instance)
        
        return instance
```

## 🔗 前后端对接设计

### 1. API接口规范

#### 统一响应格式
```python
class APIResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

#### 错误处理中间件
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": str(exc),
            "data": {"error": "internal_server_error"},
            "timestamp": datetime.now().isoformat()
        }
    )
```

### 2. 认证和权限

#### JWT认证中间件
```python
class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 提取和验证JWT token
            token = self.extract_token(scope)
            if token:
                user_info = await self.verify_token(token)
                scope["user"] = user_info
        
        await self.app(scope, receive, send)
```

#### 权限装饰器
```python
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查用户权限
            user = get_current_user()
            if not await check_user_permission(user, permission):
                raise HTTPException(status_code=403, detail="权限不足")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3. 动态路由管理

#### 路由注册器
```python
class DynamicRouteManager:
    def __init__(self, app: FastAPI):
        self.app = app
        self.registered_routes = {}
    
    async def register_route(self, route_config: RouteConfig):
        # 1. 验证路由配置
        validated_config = self.validate_route_config(route_config)
        
        # 2. 生成路由处理函数
        handler = await self.generate_route_handler(validated_config)
        
        # 3. 注册到FastAPI应用
        self.app.add_api_route(
            path=validated_config.endpoint,
            endpoint=handler,
            methods=[validated_config.method]
        )
        
        # 4. 记录注册信息
        self.registered_routes[route_config.route_id] = validated_config
```

### 4. 数据同步机制

#### WebSocket连接管理
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def broadcast_update(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)
```

## 🎯 核心特性实现

### 1. 高性能设计
- 异步IO处理
- 数据库连接池
- 缓存策略
- 批量操作优化

### 2. 可扩展架构
- 插件化设计
- 微服务支持
- 水平扩展能力
- 模块化组件

### 3. 安全保障
- JWT认证
- RBAC权限控制
- SQL注入防护
- XSS防护

### 4. 监控和日志
- 请求日志记录
- 性能监控
- 错误追踪
- 健康检查

### 5. 部署和运维
- Docker容器化
- 环境配置管理
- 数据库迁移
- 自动化部署

## 🔄 数据流架构

### 配置数据流
```
前端配置 → API验证 → 服务层处理 → 数据持久化 → 系统激活
```

### 用户请求流
```
用户请求 → 认证中间件 → 权限检查 → 动态路由 → 业务处理 → 响应返回
```

### AI交互流
```
语音输入 → 命令解析 → 意图识别 → Schema生成 → 前端渲染 → 用户交互
```

这个后端架构为AILF提供了完整的服务支持，从开发者配置到最终用户使用的全流程后端服务。
