# AILF API 概览文档

## 📋 概述

AILF (AI Language Frontend) 系统API概览，包含所有API端点的功能说明和分类。

## 🔐 认证模块 APIs

### 开发者认证
- `POST /api/v1/auth/developer` - 开发者密码认证，获取访问令牌
- `POST /api/v1/auth/developer/verify-token` - 验证开发者令牌有效性

## 📊 场景管理模块 APIs

### 场景配置管理
- `GET /api/v1/scenario` - 获取当前活跃的场景配置
- `POST /api/v1/scenario` - 创建或更新当前场景配置
- `POST /api/v1/scenario/from-template` - 从预设模板创建场景配置
- `POST /api/v1/scenario/validate` - 验证当前场景配置的有效性

## 🎯 模板管理模块 APIs

### 场景模板管理
- `GET /api/v1/templates` - 获取所有可用的场景模板
- `GET /api/v1/templates/{template_key}` - 获取特定模板的详细配置

## 🏗️ 业务实体建模模块 APIs

### 实体定义管理
- `POST /api/v1/entities` - 创建业务实体定义
- `GET /api/v1/entities` - 获取所有业务实体列表
- `GET /api/v1/entities/{entity_id}` - 获取特定实体详情
- `PUT /api/v1/entities/{entity_id}` - 更新实体定义
- `DELETE /api/v1/entities/{entity_id}` - 删除实体定义

### 实体数据管理
- `GET /api/v1/entities/{entity_id}/data` - 获取实体数据列表
- `POST /api/v1/entities/{entity_id}/data` - 创建实体数据记录
- `PUT /api/v1/entities/{entity_id}/data/{record_id}` - 更新实体数据记录
- `DELETE /api/v1/entities/{entity_id}/data/{record_id}` - 删除实体数据记录

### 实体关系管理
- `POST /api/v1/entities/{entity_id}/relationships` - 创建实体关系
- `GET /api/v1/entities/{entity_id}/relationships` - 获取实体关系列表
- `PUT /api/v1/relationships/{relationship_id}` - 更新实体关系
- `DELETE /api/v1/relationships/{relationship_id}` - 删除实体关系

## 🔄 工作流设计模块 APIs

### 工作流定义管理
- `POST /api/v1/workflow` - 创建工作流定义
- `GET /api/v1/workflow` - 获取所有工作流列表
- `GET /api/v1/workflow/{workflow_id}` - 获取特定工作流详情
- `PUT /api/v1/workflow/{workflow_id}` - 更新工作流定义
- `DELETE /api/v1/workflow/{workflow_id}` - 删除工作流定义

### 工作流执行管理
- `POST /api/v1/workflow/{workflow_id}/execute` - 执行工作流
- `GET /api/v1/workflow/instances` - 获取工作流实例列表
- `GET /api/v1/workflow/instances/{instance_id}` - 获取工作流实例详情
- `POST /api/v1/workflow/instances/{instance_id}/continue` - 继续执行工作流实例
- `POST /api/v1/workflow/instances/{instance_id}/cancel` - 取消工作流实例

### 工作流步骤管理
- `GET /api/v1/workflow/{workflow_id}/steps` - 获取工作流步骤列表
- `POST /api/v1/workflow/{workflow_id}/steps` - 添加工作流步骤
- `PUT /api/v1/workflow/steps/{step_id}` - 更新工作流步骤
- `DELETE /api/v1/workflow/steps/{step_id}` - 删除工作流步骤

## 📝 动态表单配置模块 APIs

### 表单定义管理
- `POST /api/v1/forms` - 创建动态表单配置
- `GET /api/v1/forms` - 获取所有表单配置
- `GET /api/v1/forms/{form_id}` - 获取特定表单配置
- `PUT /api/v1/forms/{form_id}` - 更新表单配置
- `DELETE /api/v1/forms/{form_id}` - 删除表单配置

### 表单渲染管理
- `GET /api/v1/forms/{form_id}/render` - 获取表单渲染配置（amis schema）
- `POST /api/v1/forms/{form_id}/submit` - 提交表单数据
- `GET /api/v1/forms/{form_id}/data/{record_id}` - 获取表单数据用于编辑
- `POST /api/v1/forms/validate` - 验证表单配置

### 表单字段管理
- `GET /api/v1/forms/{form_id}/fields` - 获取表单字段列表
- `POST /api/v1/forms/{form_id}/fields` - 添加表单字段
- `PUT /api/v1/forms/fields/{field_id}` - 更新表单字段
- `DELETE /api/v1/forms/fields/{field_id}` - 删除表单字段

## 🔗 动态API路由管理模块 APIs

### API路由管理
- `POST /api/v1/routes/register` - 动态注册新的API路由
- `GET /api/v1/routes` - 获取当前已注册的所有API路由
- `PUT /api/v1/routes/{route_id}` - 更新已注册的API路由
- `DELETE /api/v1/routes/{route_id}` - 删除已注册的API路由

### API路由状态管理
- `POST /api/v1/routes/{route_id}/activate` - 激活API路由
- `POST /api/v1/routes/{route_id}/deactivate` - 停用API路由
- `GET /api/v1/routes/{route_id}/status` - 获取API路由状态
- `GET /api/v1/routes/health` - 检查所有API路由健康状态

## 👥 角色管理模块 APIs

### 角色定义管理
- `POST /api/v1/roles` - 创建新的用户角色
- `GET /api/v1/roles` - 获取所有角色列表
- `GET /api/v1/roles/{role_id}` - 获取特定角色详情
- `PUT /api/v1/roles/{role_id}` - 更新角色信息
- `DELETE /api/v1/roles/{role_id}` - 删除角色

### 角色权限管理
- `GET /api/v1/roles/{role_id}/permissions` - 获取角色权限列表
- `POST /api/v1/roles/{role_id}/permissions` - 为角色分配权限
- `DELETE /api/v1/roles/{role_id}/permissions/{permission_id}` - 移除角色权限

## 🔒 权限访问控制模块 APIs

### 权限检查
- `POST /api/v1/permissions/check` - 检查用户是否有访问特定API的权限
- `GET /api/v1/permissions/user-apis` - 获取指定用户可以访问的API列表

### 权限配置管理
- `POST /api/v1/permissions/role-api` - 更新角色对特定API的访问权限
- `POST /api/v1/permissions/batch-update` - 批量更新多个角色的API权限
- `GET /api/v1/permissions/matrix` - 获取完整的权限矩阵
- `POST /api/v1/permissions/matrix` - 更新权限矩阵



## 🤖 AI交互模块 APIs

### AI命令处理
- `POST /api/v1/command` - 处理用户的语音/文本命令，生成动态界面
- `POST /api/v1/ai/analyze` - AI分析用户需求，推荐配置方案
- `POST /api/v1/ai/optimize` - AI优化现有配置
- `POST /api/v1/ai/generate-schema` - AI生成amis schema

### AI辅助配置
- `POST /api/v1/ai/suggest-entities` - AI推荐业务实体设计
- `POST /api/v1/ai/suggest-workflows` - AI推荐工作流设计
- `POST /api/v1/ai/suggest-forms` - AI推荐表单设计
- `POST /api/v1/ai/suggest-apis` - AI推荐API设计

## 🔧 系统健康检查 APIs

### 基础健康检查
- `GET /api/v1/health` - 检查系统健康状态

## 📝 API分类总结

### 核心配置APIs (开发者使用)
- 认证模块：2个API
- 场景管理：4个API
- 模板管理：2个API
- 实体建模：12个API
- 工作流设计：12个API
- 表单配置：10个API
- API路由管理：8个API
- 角色管理：8个API
- 权限控制：6个API

### 运行时APIs (最终用户使用)
- AI交互：7个API

### 系统管理APIs (运维使用)
- 系统健康检查：1个API

**总计：约72个API端点**

## 🎯 API使用流程

### 开发者配置流程
1. **认证** → 获取开发者令牌
2. **场景配置** → 创建/选择业务场景
3. **实体建模** → 设计业务数据结构
4. **工作流设计** → 配置业务流程
5. **表单配置** → 设计用户界面
6. **API配置** → 定义接口规范
7. **角色权限** → 配置访问控制

### 最终用户使用流程
1. **AI交互** → 语音/文本命令
2. **动态界面** → 自动生成的amis页面
3. **数据操作** → 通过生成的API进行CRUD
4. **工作流执行** → 按配置的流程处理业务

这个API概览为AILF系统提供了完整的功能支持，从开发者配置到最终用户使用的全流程覆盖。
