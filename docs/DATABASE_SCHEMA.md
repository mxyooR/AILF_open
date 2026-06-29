# AILF 数据库设计文档

## 📋 概述

AILF 项目使用 MySQL 数据库存储系统数据，采用 SQLAlchemy ORM 框架。数据库包含用户认证、权限管理、业务实体建模、工作流引擎、动态API路由等核心模块。

## 🗄️ 数据库信息

- **数据库类型**: MySQL
- **数据库名称**: `ailf_db`
- **字符集**: utf8mb4

---

## 📊 表结构总览

| 序号 | 表名 | 说明 |
|------|------|------|
| 1 | users | 用户表 |
| 2 | user_sessions | 用户会话表 |
| 3 | user_login_logs | 用户登录日志表 |
| 4 | user_roles | 用户角色关联表 |
| 5 | user_role_logs | 用户角色变更日志表 |
| 6 | roles | 角色表 |
| 7 | permissions | 权限表 |
| 8 | role_permissions | 角色权限关联表 |
| 9 | role_api_permissions | 角色API权限表 |
| 10 | role_level_configs | 角色等级配置表 |
| 11 | role_level_settings | 角色等级设置表 |
| 12 | scenarios | 业务场景表 |
| 13 | entities | 实体定义表 |
| 14 | entity_fields | 实体字段表 |
| 15 | entity_relationships | 实体关系表 |
| 16 | entity_records | 实体数据记录表 |
| 17 | workflows | 工作流定义表 |
| 18 | workflow_nodes | 工作流节点表 |
| 19 | api_routes | API路由定义表 |
| 20 | api_endpoints | API端点配置表 |
| 21 | api_route_parameters | API路由参数表 |
| 22 | api_route_responses | API响应配置表 |
| 23 | api_route_call_logs | API调用日志表 |
| 24 | configuration_status | 配置状态表 |
| 25 | permission_check_logs | 权限检查日志表 |

---

## 1️⃣ 用户认证模块

### 1.1 users - 用户表

存储系统用户信息。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | int | PRI | 主键，自增 |
| username | varchar(50) | UNI | 用户名，唯一 |
| email | varchar(100) | UNI | 邮箱，唯一 |
| password_hash | varchar(255) | | 密码哈希 |
| real_name | varchar(50) | | 真实姓名 |
| phone | varchar(20) | | 手机号 |
| role_id | varchar(50) | MUL | 角色ID |
| is_active | tinyint(1) | | 是否激活 |
| is_verified | tinyint(1) | | 是否验证 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |
| last_login | datetime | | 最后登录时间 |
| avatar_url | varchar(255) | | 头像URL |
| bio | text | | 个人简介 |
| settings | text | | 用户设置(JSON) |

### 1.2 user_sessions - 用户会话表

管理用户登录会话。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | int | PRI | 主键，自增 |
| user_id | int | MUL | 用户ID |
| token_hash | varchar(255) | | Token哈希 |
| ip_address | varchar(45) | | IP地址 |
| user_agent | text | | 用户代理 |
| created_at | datetime | | 创建时间 |
| expires_at | datetime | | 过期时间 |
| last_used | datetime | | 最后使用时间 |
| is_active | tinyint(1) | | 是否激活 |

### 1.3 user_login_logs - 用户登录日志表

记录用户登录历史。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | int | PRI | 主键，自增 |
| user_id | int | MUL | 用户ID |
| username | varchar(50) | | 用户名 |
| ip_address | varchar(45) | | IP地址 |
| user_agent | text | | 用户代理 |
| success | tinyint(1) | | 是否成功 |
| failure_reason | varchar(100) | | 失败原因 |
| login_time | datetime | | 登录时间 |

### 1.4 user_roles - 用户角色关联表

用户与角色的多对多关联。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| user_id | varchar(50) | PRI | 用户ID |
| role_id | varchar(50) | PRI | 角色ID |
| assigned_at | datetime | | 分配时间 |
| assigned_by | varchar(50) | | 分配人 |
| expires_at | datetime | | 过期时间 |

### 1.5 user_role_logs - 用户角色变更日志表

记录用户角色变更历史。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| user_id | varchar(50) | | 用户ID |
| role_id | varchar(50) | MUL | 角色ID |
| operation | varchar(20) | | 操作类型 |
| operator_id | varchar(50) | | 操作人ID |
| operator_name | varchar(100) | | 操作人姓名 |
| reason | text | | 变更原因 |
| expires_at | datetime | | 过期时间 |
| operation_metadata | json | | 操作元数据 |
| created_at | datetime | | 创建时间 |

---

## 2️⃣ 权限管理模块

### 2.1 roles - 角色表

定义系统角色。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| name | varchar(100) | | 角色名称 |
| code | varchar(50) | UNI | 角色代码，唯一 |
| description | text | | 角色描述 |
| status | varchar(20) | | 状态 |
| role_metadata | json | | 角色元数据 |
| user_count | int | | 用户数量 |
| permission_count | int | | 权限数量 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |
| created_by | varchar(50) | | 创建人 |
| updated_by | varchar(50) | | 更新人 |

### 2.2 permissions - 权限表

定义系统权限。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| name | varchar(100) | UNI | 权限名称，唯一 |
| description | text | | 权限描述 |
| resource | varchar(50) | | 资源类型 |
| action | varchar(50) | | 操作类型 |
| is_system | tinyint(1) | | 是否系统权限 |
| is_active | tinyint(1) | | 是否激活 |
| permission_metadata | json | | 权限元数据 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 2.3 role_permissions - 角色权限关联表

角色与权限的多对多关联。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| role_id | varchar(50) | PRI | 角色ID |
| permission_id | varchar(50) | PRI | 权限ID |
| granted_at | datetime | | 授权时间 |
| granted_by | varchar(50) | | 授权人 |

### 2.4 role_api_permissions - 角色API权限表

细粒度的API访问权限控制。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| role_id | varchar(50) | MUL | 角色ID |
| api_id | varchar(50) | MUL | API ID |
| permission_name | varchar(100) | | 权限名称 |
| is_granted | tinyint(1) | | 是否授权 |
| conditions | json | | 授权条件 |
| granted_by | varchar(50) | | 授权人 |
| granted_at | datetime | | 授权时间 |
| expires_at | datetime | | 过期时间 |
| permission_metadata | json | | 权限元数据 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 2.5 role_level_configs - 角色等级配置表

定义角色等级体系。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | int | PRI | 主键，自增 |
| level | int | UNI | 等级值 |
| name | varchar(100) | | 等级名称 |
| description | text | | 等级描述 |
| color | varchar(20) | | 等级颜色 |
| permissions | json | | 等级权限 |
| is_active | tinyint(1) | | 是否激活 |
| sort_order | int | | 排序顺序 |
| display_icon | varchar(50) | | 显示图标 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |
| created_by | varchar(50) | | 创建人 |
| updated_by | varchar(50) | | 更新人 |

### 2.6 role_level_settings - 角色等级设置表

角色等级系统的全局设置。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | int | PRI | 主键，自增 |
| max_level | int | | 最大等级 |
| min_level | int | | 最小等级 |
| default_level | int | | 默认等级 |
| level_naming_pattern | varchar(100) | | 等级命名模式 |
| allow_custom_levels | tinyint(1) | | 允许自定义等级 |
| auto_assign_permissions | tinyint(1) | | 自动分配权限 |
| extra_config | json | | 额外配置 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |
| updated_by | varchar(50) | | 更新人 |

### 2.7 permission_check_logs - 权限检查日志表

记录权限检查历史。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| user_id | varchar(50) | | 用户ID |
| permission | varchar(100) | | 权限标识 |
| resource | varchar(50) | | 资源类型 |
| result | varchar(20) | | 检查结果 |
| ip_address | varchar(50) | | IP地址 |
| user_agent | text | | 用户代理 |
| request_path | varchar(500) | | 请求路径 |
| request_method | varchar(10) | | 请求方法 |
| error_message | text | | 错误信息 |
| created_at | datetime | | 创建时间 |

---

## 3️⃣ 业务场景模块

### 3.1 scenarios - 业务场景表

定义和管理业务场景配置。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| name | varchar(200) | MUL | 场景名称 |
| type | enum | MUL | 场景类型(ECOMMERCE/HOSPITAL/RESTAURANT/EDUCATION/LOGISTICS/FINANCE/CUSTOM) |
| description | text | | 场景描述 |
| status | enum | MUL | 状态(ACTIVE/INACTIVE/DRAFT/ARCHIVED) |
| template_key | varchar(100) | | 模板键 |
| config | json | | 场景配置 |
| created_at | datetime | MUL | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 3.2 configuration_status - 配置状态表

跟踪系统配置步骤完成状态。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | int | PRI | 主键，自增 |
| scenario_id | varchar(50) | UNI | 场景ID |
| step1_auth_completed | tinyint(1) | | 步骤1：认证配置完成 |
| step2_scenario_completed | tinyint(1) | | 步骤2：场景配置完成 |
| step3_template_completed | tinyint(1) | | 步骤3：模板配置完成 |
| step4_entity_completed | tinyint(1) | | 步骤4：实体建模完成 |
| step5_api_completed | tinyint(1) | | 步骤5：API配置完成 |
| step6_workflow_completed | tinyint(1) | | 步骤6：工作流配置完成 |
| step7_role_completed | tinyint(1) | | 步骤7：角色配置完成 |
| all_steps_completed | tinyint(1) | | 所有步骤完成 |
| step1_completed_at | datetime | | 步骤1完成时间 |
| step2_completed_at | datetime | | 步骤2完成时间 |
| step3_completed_at | datetime | | 步骤3完成时间 |
| step4_completed_at | datetime | | 步骤4完成时间 |
| step5_completed_at | datetime | | 步骤5完成时间 |
| step6_completed_at | datetime | | 步骤6完成时间 |
| step7_completed_at | datetime | | 步骤7完成时间 |
| all_completed_at | datetime | | 全部完成时间 |
| completion_details | text | | 完成详情 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

---

## 4️⃣ 实体建模模块

### 4.1 entities - 实体定义表

定义业务实体（类似数据表结构）。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| scenario_id | varchar(50) | MUL | 场景ID |
| name | varchar(100) | UNI | 实体名称，唯一 |
| display_name | varchar(200) | | 显示名称 |
| description | text | | 实体描述 |
| icon | varchar(100) | | 图标 |
| status | varchar(20) | MUL | 状态 |
| field_count | int | | 字段数量 |
| record_count | int | | 记录数量 |
| created_at | timestamp | MUL | 创建时间 |
| updated_at | timestamp | | 更新时间 |
| is_role | tinyint(1) | | 是否为角色实体 |

### 4.2 entity_fields - 实体字段表

定义实体的字段结构。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| entity_id | varchar(50) | MUL | 实体ID |
| name | varchar(100) | MUL | 字段名称 |
| display_name | varchar(200) | | 显示名称 |
| type | varchar(50) | MUL | 字段类型 |
| required | tinyint(1) | | 是否必填 |
| unique_field | tinyint(1) | | 是否唯一 |
| default_value | text | | 默认值 |
| validation | json | | 验证规则 |
| options | json | | 选项列表 |
| sort_order | int | MUL | 排序顺序 |
| created_at | timestamp | | 创建时间 |
| updated_at | timestamp | | 更新时间 |
| aliases | json | | 字段别名(用于AI理解) |

### 4.3 entity_relationships - 实体关系表

定义实体之间的关系。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| name | varchar(100) | | 关系名称 |
| source_entity_id | varchar(50) | MUL | 源实体ID |
| target_entity_id | varchar(50) | MUL | 目标实体ID |
| type | varchar(50) | MUL | 关系类型 |
| foreign_key | varchar(100) | | 外键字段 |
| constraints | json | | 约束条件 |
| created_at | timestamp | | 创建时间 |
| updated_at | timestamp | | 更新时间 |

### 4.4 entity_records - 实体数据记录表

存储实体的业务数据记录。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| entity_id | varchar(50) | MUL | 实体ID |
| data | json | | 业务数据 |
| created_at | timestamp | MUL | 创建时间 |
| updated_at | timestamp | | 更新时间 |

---

## 5️⃣ 工作流模块

### 5.1 workflows - 工作流定义表

定义业务工作流。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| name | varchar(200) | | 工作流名称 |
| description | text | | 工作流描述 |
| business_scenario | varchar(100) | | 业务场景 |
| status | enum | | 状态(draft/active/inactive/archived) |
| user_intents | json | | 用户意图列表 |
| trigger_keywords | json | | 触发关键词 |
| inputs | json | | 输入参数 |
| nodes | json | | 节点定义 |
| workflow_metadata | json | | 工作流元数据 |
| created_by | varchar(50) | | 创建人 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 5.2 workflow_nodes - 工作流节点表

定义工作流中的节点。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| workflow_id | varchar(50) | MUL | 工作流ID |
| node_id | varchar(50) | MUL | 节点ID |
| name | varchar(200) | | 节点名称 |
| type | enum | | 节点类型(start/api_call/user_input/condition/notification/end) |
| description | text | | 节点描述 |
| position_x | int | | X坐标 |
| position_y | int | | Y坐标 |
| parent_nodes | json | | 父节点列表 |
| child_nodes | json | | 子节点列表 |
| config | json | | 节点配置 |
| outputs | json | | 输出定义 |
| ai_instructions | json | | AI指令 |
| is_active | tinyint(1) | | 是否激活 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

---

## 6️⃣ 动态API模块

### 6.1 api_routes - API路由定义表

定义动态API路由。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| api_id | varchar(100) | UNI | API标识，唯一 |
| name | varchar(200) | | API名称 |
| endpoint | varchar(500) | | 端点路径 |
| method | varchar(10) | | HTTP方法 |
| description | text | | API描述 |
| auth_required | tinyint(1) | | 是否需要认证 |
| permission_config | json | | 权限配置 |
| status | enum | | 状态(ACTIVE/INACTIVE) |
| handler_type | enum | | 处理器类型 |
| handler_config | json | | 处理器配置 |
| parameters_config | json | | 参数配置 |
| responses_config | json | | 响应配置 |
| call_count | int | | 调用次数 |
| last_called | datetime | | 最后调用时间 |
| avg_response_time | int | | 平均响应时间(ms) |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |
| dynamic_rules_config | json | | 动态规则配置 |

**handler_type 枚举值说明**:
- `entity_crud`: 实体CRUD操作
- `custom_function`: 自定义函数
- `proxy`: 代理转发
- `workflow`: 工作流执行
- `static_data`: 静态数据
- `script`: 脚本执行
- `file_upload`: 文件上传
- `file_download`: 文件下载
- `image_display`: 图片显示
- `media_streaming`: 媒体流

### 6.2 api_endpoints - API端点配置表

配置API端点的详细信息。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| name | varchar(100) | | 端点名称 |
| endpoint | varchar(200) | | 端点路径 |
| method | varchar(10) | | HTTP方法 |
| resource | varchar(50) | | 资源类型 |
| action | varchar(50) | | 操作类型 |
| permission | varchar(100) | | 权限标识 |
| description | text | | 端点描述 |
| is_public | tinyint(1) | | 是否公开 |
| is_active | tinyint(1) | | 是否激活 |
| min_role_level | int | | 最低角色等级 |
| api_metadata | json | | API元数据 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 6.3 api_route_parameters - API路由参数表

定义API请求参数。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| route_id | varchar(50) | | 路由ID |
| name | varchar(100) | | 参数名称 |
| type | varchar(50) | | 参数类型 |
| location | enum | | 参数位置(QUERY/PATH/HEADER/BODY) |
| required | tinyint(1) | | 是否必填 |
| description | text | | 参数描述 |
| validation_config | json | | 验证配置 |
| default_value | text | | 默认值 |
| order_index | int | | 排序顺序 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 6.4 api_route_responses - API响应配置表

定义API响应格式。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| route_id | varchar(50) | | 路由ID |
| status_code | int | | HTTP状态码 |
| content_type | varchar(100) | | 内容类型 |
| schema | json | | 响应Schema |
| example | json | | 响应示例 |
| description | text | | 响应描述 |
| created_at | datetime | | 创建时间 |
| updated_at | datetime | | 更新时间 |

### 6.5 api_route_call_logs - API调用日志表

记录API调用历史。

| 字段名 | 类型 | 键 | 说明 |
|--------|------|-----|------|
| id | varchar(50) | PRI | 主键 |
| route_id | varchar(50) | | 路由ID |
| request_method | varchar(10) | | 请求方法 |
| request_path | varchar(500) | | 请求路径 |
| request_params | json | | 请求参数 |
| request_headers | json | | 请求头 |
| request_body | text | | 请求体 |
| response_status | int | | 响应状态码 |
| response_time | int | | 响应时间(ms) |
| response_size | int | | 响应大小 |
| client_ip | varchar(50) | | 客户端IP |
| user_agent | text | | 用户代理 |
| user_id | varchar(50) | | 用户ID |
| created_at | datetime | | 创建时间 |

---

## 7️⃣ 业务数据表示例

以下表为火车售票系统的业务数据表示例，实际业务中会根据实体定义动态生成。

### 7.1 entity_train - 火车表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | varchar(36) | 主键(UUID) |
| train_number | varchar(255) | 车次号 |
| train_type | varchar(100) | 车型(默认:高速) |
| departure_station | varchar(255) | 出发站 |
| arrival_station | varchar(255) | 到达站 |
| departure_time | varchar(255) | 出发时间 |
| arrival_time | varchar(255) | 到达时间 |
| duration | int | 行程时长(分钟) |
| total_seats | int | 总座位数 |
| status | varchar(100) | 状态(默认:正常) |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### 7.2 entity_station - 车站表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | varchar(36) | 主键(UUID) |
| station_code | varchar(255) | 车站代码 |
| station_name | varchar(255) | 车站名称 |
| city | varchar(255) | 所在城市 |
| province | varchar(255) | 所在省份 |
| station_type | varchar(100) | 车站类型(默认:地级站) |
| platform_count | int | 站台数量(默认:2) |
| status | varchar(100) | 状态(默认:正常) |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### 7.3 entity_passenger - 乘客表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | varchar(36) | 主键(UUID) |
| name | varchar(255) | 乘客姓名 |
| id_card | varchar(255) | 身份证号 |
| phone | varchar(20) | 手机号 |
| passenger_type | varchar(100) | 乘客类型(默认:成人) |
| email | varchar(255) | 邮箱 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### 7.4 entity_order - 订单表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | varchar(36) | 主键(UUID) |
| order_number | varchar(255) | 订单号 |
| passenger_name | varchar(255) | 乘客姓名 |
| passenger_phone | varchar(20) | 乘客电话 |
| total_amount | int | 总金额(分) |
| ticket_count | int | 票数(默认:1) |
| payment_method | varchar(100) | 支付方式(默认:支付宝) |
| order_status | varchar(100) | 订单状态(默认:待支付) |
| create_time | datetime | 创建时间 |
| payment_time | datetime | 支付时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

---

## 🔗 表关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户认证模块                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  users ──────── user_roles ──────── roles                                    │
│    │                                        │                                │
│    ├──── user_sessions              role_permissions ──── permissions        │
│    ├──── user_login_logs            role_api_permissions                     │
│    └──── user_role_logs             role_level_configs                       │
│                                      role_level_settings                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              业务配置模块                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  scenarios ──── entities ──── entity_fields                                  │
│      │                │                                                      │
│      │                ├──── entity_relationships                             │
│      │                │                                                      │
│      │                └──── entity_records                                   │
│      │                                                                       │
│      └──── configuration_status                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              工作流模块                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  workflows ──── workflow_nodes                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              API路由模块                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  api_routes ──── api_endpoints                                               │
│      │               │                                                       │
│      ├──── api_route_parameters                                              │
│      ├──── api_route_responses                                               │
│      └──── api_route_call_logs                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 索引设计

主要索引字段：
- **唯一索引(UNI)**: username, email, api_id, station_code, station_name, order_number
- **普通索引(MUL)**: user_id, role_id, entity_id, scenario_id, workflow_id, route_id

---

## 🔐 安全说明

1. **密码存储**: 用户密码使用 bcrypt 进行哈希存储
2. **敏感日志**: 登录日志记录IP和User-Agent用于审计
3. **JWT认证**: 使用 HS256 算法签发访问令牌
4. **权限控制**: 基于RBAC模型的细粒度权限管理

---

## 📊 维护建议

1. **定期清理**: 建议定期清理 api_route_call_logs 和 user_login_logs 表
2. **数据备份**: 建议使用 MySQL 主从复制或定时备份
3. **性能监控**: 监控 avg_response_time 和 call_count 字段
4. **索引优化**: 根据实际查询模式添加复合索引
