"""
模板管理服务
处理模板查询、筛选和详情获取的业务逻辑
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.core.logging_config import get_logger
from app.schemas.template import (
    TemplateListItem, TemplateDetail, TemplatePreview, CategoryStats,
    TemplateCategory, TemplateDifficulty, TemplateConfig, ScenarioConfig,
    Entity, EntityField, FieldValidation, Workflow, WorkflowStep,
    Form, FormSection, API, Role, SetupGuide
)

logger = get_logger(__name__)


class TemplateService:
    """模板管理服务类"""

    def __init__(self):
        # 模板文件目录
        self.templates_dir = Path(__file__).parent.parent / "templates"
        # 缓存模板数据
        self._templates_cache = {}
        # 加载模板数据
        self._load_templates()

    def reload_templates(self):
        """重新加载模板数据"""
        self._load_templates()

    def _load_templates(self):
        """从JSON文件加载模板数据"""
        self.templates = {}

        # 确保模板目录存在
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            return

        # 遍历模板目录中的JSON文件
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)

                # 提取模板信息
                template_info = template_data.get("template_info", {})
                template_key = template_info.get("key", template_file.stem)

                # 转换分类和难度枚举
                category_str = template_info.get("category", "BUSINESS")
                difficulty_str = template_info.get("difficulty", "BEGINNER")

                try:
                    category = TemplateCategory[category_str]
                except KeyError:
                    category = TemplateCategory.BUSINESS

                try:
                    difficulty = TemplateDifficulty[difficulty_str]
                except KeyError:
                    difficulty = TemplateDifficulty.BEGINNER

                # 构建模板数据
                self.templates[template_key] = {
                    "key": template_key,
                    "name": template_info.get("name", template_key),
                    "description": template_info.get("description", ""),
                    "category": category,
                    "difficulty": difficulty,
                    "estimated_setup_time": template_info.get("estimated_setup_time", "30分钟"),
                    "version": template_info.get("version", "1.0.0"),
                    "author": template_info.get("author", "AILF Team"),
                    "license": template_info.get("license", "MIT"),
                    "features": template_info.get("features", []),
                    "tags": template_info.get("tags", []),
                    "created_at": template_info.get("created_at", "2024-01-01T00:00:00.000Z"),
                    "updated_at": template_info.get("updated_at", "2024-01-01T00:00:00.000Z"),
                    "preview": template_info.get("preview", {
                        "entities": 0,
                        "workflows": 0,
                        "forms": 0,
                        "apis": 0
                    })
                }

                # 缓存完整的模板数据
                self._templates_cache[template_key] = template_data

            except Exception as e:
                logger.warning(f"⚠️ 加载模板文件 {template_file} 失败: {str(e)}")
                continue

        # 如果没有加载到任何模板，记录警告
        if not self.templates:
            logger.warning("⚠️ 没有找到任何模板文件")
        
        # 分类映射
        self.category_names = {
            TemplateCategory.BUSINESS: "商业管理",
            TemplateCategory.HEALTHCARE: "医疗健康",
            TemplateCategory.EDUCATION: "教育培训",
            TemplateCategory.HOSPITALITY: "服务行业",
            TemplateCategory.FINANCE: "金融服务",
            TemplateCategory.LOGISTICS: "物流运输",
            TemplateCategory.GOVERNMENT: "政府机构",
            TemplateCategory.CUSTOM: "自定义"
        }
    
    def get_templates_list(self, category: Optional[str] = None, include_preview: bool = False) -> Dict[str, Any]:
        """
        获取模板列表
        
        Args:
            category: 分类筛选
            include_preview: 是否包含预览信息
            
        Returns:
            模板列表数据
        """
        try:
            # 筛选模板
            filtered_templates = []
            for template_data in self.templates.values():
                # 分类筛选
                if category and template_data["category"].value != category:
                    continue
                
                # 构建模板列表项
                template_item = TemplateListItem(
                    key=template_data["key"],
                    name=template_data["name"],
                    description=template_data["description"],
                    category=template_data["category"],
                    difficulty=template_data["difficulty"],
                    estimated_setup_time=template_data["estimated_setup_time"],
                    features=template_data["features"],
                    tags=template_data["tags"],
                    created_at=template_data["created_at"],
                    updated_at=template_data["updated_at"]
                )
                
                # 添加预览信息
                if include_preview and "preview" in template_data:
                    template_item.preview = TemplatePreview(**template_data["preview"])
                
                filtered_templates.append(template_item)
            
            # 统计分类
            categories = self._get_category_stats()
            
            return {
                "success": True,
                "data": {
                    "templates": filtered_templates,
                    "total": len(filtered_templates),
                    "categories": categories
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询模板列表失败: {str(e)}"
            }
    
    def get_template_detail(self, template_key: str) -> Dict[str, Any]:
        """
        获取模板详情
        
        Args:
            template_key: 模板标识符
            
        Returns:
            模板详情数据
        """
        if template_key not in self.templates:
            return {
                "success": False,
                "error": "template_not_found",
                "details": "指定的模板标识符不存在"
            }
        
        try:
            template_data = self.templates[template_key]
            
            # 构建详细配置（这里使用示例数据，实际应该从数据库获取）
            config = self._build_template_config(template_key)
            setup_guide = self._build_setup_guide(template_key)
            
            # 构建模板详情
            template_detail = TemplateDetail(
                key=template_data["key"],
                name=template_data["name"],
                description=template_data["description"],
                category=template_data["category"],
                difficulty=template_data["difficulty"],
                estimated_setup_time=template_data["estimated_setup_time"],
                version=template_data["version"],
                author=template_data["author"],
                license=template_data["license"],
                features=template_data["features"],
                tags=template_data["tags"],
                created_at=template_data["created_at"],
                updated_at=template_data["updated_at"],
                config=config,
                setup_guide=setup_guide
            )
            
            return {
                "success": True,
                "data": {"template": template_detail}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询模板详情失败: {str(e)}"
            }
    
    def _get_category_stats(self) -> List[CategoryStats]:
        """获取分类统计"""
        category_counts = {}
        
        for template_data in self.templates.values():
            category = template_data["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        
        categories = []
        for category, count in category_counts.items():
            categories.append(CategoryStats(
                key=category.value,
                name=self.category_names[category],
                count=count
            ))
        
        return categories

    def _build_template_config(self, template_key: str) -> TemplateConfig:
        """构建模板配置（示例数据）"""
        if template_key == "ecommerce_basic":
            return TemplateConfig(
                scenario=ScenarioConfig(
                    type="ecommerce",
                    business_domain="电子商务",
                    target_users=["管理员", "销售人员", "客服"],
                    key_features=["商品管理", "订单处理", "用户管理", "库存管理"],
                    example_instructions=["查看今日订单", "新增商品：咖啡豆", "查询用户信息"]
                ),
                entities=[
                    Entity(
                        name="product",
                        displayName="商品",
                        description="商品信息管理",
                        fields=[
                            EntityField(
                                name="name",
                                displayName="商品名称",
                                type="text",
                                required=True,
                                validation=FieldValidation(maxLength=100)
                            ),
                            EntityField(
                                name="price",
                                displayName="价格",
                                type="decimal",
                                required=True,
                                validation=FieldValidation(min=0, precision=2)
                            ),
                            EntityField(
                                name="stock",
                                displayName="库存",
                                type="number",
                                required=True,
                                defaultValue=0
                            ),
                            EntityField(
                                name="category",
                                displayName="分类",
                                type="select",
                                options=["电子产品", "服装", "食品", "图书"]
                            )
                        ]
                    ),
                    Entity(
                        name="order",
                        displayName="订单",
                        description="订单信息管理",
                        fields=[
                            EntityField(
                                name="order_no",
                                displayName="订单号",
                                type="text",
                                required=True,
                                unique=True
                            ),
                            EntityField(
                                name="customer_name",
                                displayName="客户姓名",
                                type="text",
                                required=True
                            ),
                            EntityField(
                                name="total_amount",
                                displayName="总金额",
                                type="decimal",
                                required=True
                            ),
                            EntityField(
                                name="status",
                                displayName="订单状态",
                                type="select",
                                options=["待付款", "已付款", "已发货", "已完成", "已取消"],
                                defaultValue="待付款"
                            )
                        ]
                    )
                ],
                workflows=[
                    Workflow(
                        name="订单处理流程",
                        description="从下单到完成的完整流程",
                        steps=[
                            WorkflowStep(name="创建订单", type="form", entity="order"),
                            WorkflowStep(name="支付确认", type="condition", condition="payment_status === 'success'"),
                            WorkflowStep(name="库存扣减", type="api_call", endpoint="/api/inventory/deduct"),
                            WorkflowStep(name="发货通知", type="notification", recipients=["customer", "warehouse"])
                        ]
                    )
                ],
                forms=[
                    Form(
                        name="商品录入表单",
                        entity="product",
                        layout="vertical",
                        sections=[
                            FormSection(title="基本信息", fields=["name", "category", "price", "stock"])
                        ]
                    ),
                    Form(
                        name="订单创建表单",
                        entity="order",
                        layout="horizontal",
                        sections=[
                            FormSection(title="订单信息", fields=["order_no", "customer_name", "total_amount"])
                        ]
                    )
                ],
                apis=[
                    API(path="/api/products", method="GET", description="获取商品列表"),
                    API(path="/api/products", method="POST", description="创建商品"),
                    API(path="/api/products/{id}", method="PUT", description="更新商品"),
                    API(path="/api/products/{id}", method="DELETE", description="删除商品"),
                    API(path="/api/orders", method="GET", description="获取订单列表"),
                    API(path="/api/orders", method="POST", description="创建订单"),
                    API(path="/api/orders/{id}", method="PUT", description="更新订单"),
                    API(path="/api/orders/{id}", method="DELETE", description="删除订单"),
                    API(path="/api/customers", method="GET", description="获取客户列表"),
                    API(path="/api/customers", method="POST", description="创建客户"),
                    API(path="/api/inventory", method="GET", description="获取库存信息"),
                    API(path="/api/inventory/deduct", method="POST", description="扣减库存")
                ],
                roles=[
                    Role(name="管理员", code="admin", level=10, permissions=["*"]),
                    Role(name="销售人员", code="sales", level=5, permissions=["products:read", "orders:*"])
                ]
            )
        else:
            # 其他模板的简化配置
            return TemplateConfig(
                scenario=ScenarioConfig(
                    type="custom",
                    business_domain="通用业务",
                    target_users=["管理员"],
                    key_features=["基础管理"],
                    example_instructions=["查看系统概览"]
                ),
                entities=[],
                workflows=[],
                forms=[],
                apis=[],
                roles=[]
            )

    def _build_setup_guide(self, template_key: str) -> SetupGuide:
        """构建设置指南"""
        if template_key == "ecommerce_basic":
            return SetupGuide(
                steps=[
                    "1. 选择此模板创建场景",
                    "2. 根据需要调整商品分类",
                    "3. 配置支付接口",
                    "4. 设置用户角色权限",
                    "5. 生成并部署系统"
                ],
                prerequisites=[
                    "了解基本的电商业务流程",
                    "准备商品分类数据"
                ],
                tips=[
                    "可以根据实际需求添加更多商品字段",
                    "建议先配置少量测试数据进行验证"
                ]
            )
        else:
            return SetupGuide(
                steps=["1. 选择此模板创建场景", "2. 根据需要调整配置", "3. 生成并部署系统"],
                prerequisites=["了解基本业务流程"],
                tips=["建议先进行测试验证"]
            )

    def apply_template(self, template_key: str, scenario_name: str, description: str = None, customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        应用模板到系统中，创建相应的实体、API、角色等配置
        应用前会清理相关的旧数据以避免冲突

        Args:
            template_key: 模板标识符
            scenario_name: 场景名称
            description: 场景描述
            customizations: 自定义配置

        Returns:
            应用结果
        """
        if template_key not in self.templates:
            return {
                "success": False,
                "error": "template_not_found",
                "details": "指定的模板标识符不存在"
            }

        try:
            # 获取完整的模板数据
            template_data = self._templates_cache.get(template_key)
            if not template_data:
                return {
                    "success": False,
                    "error": "template_data_not_found",
                    "details": "模板数据未找到"
                }

            # 清理相关的旧数据
            cleanup_result = self._cleanup_template_data(template_key, template_data)
            if not cleanup_result["success"]:
                return cleanup_result

            # 应用模板数据到数据库
            apply_result = self._apply_template_to_database(template_key, template_data, scenario_name, description)
            if not apply_result["success"]:
                return apply_result

            # 应用自定义配置
            if customizations:
                # 合并自定义配置到模板配置中
                if "entities" in customizations:
                    # 自定义实体配置
                    pass
                if "apis" in customizations:
                    # 自定义API配置
                    pass
                if "roles" in customizations:
                    # 自定义角色配置
                    pass

            # 创建应用结果
            scenario_data = template_data.get('scenario', {})
            applied_config = {
                "scenario": {
                    "name": scenario_name,
                    "description": description or scenario_data.get('description', f"基于{self.templates[template_key]['name']}模板创建"),
                    "type": scenario_data.get('type', 'CUSTOM'),
                    "business_domain": scenario_data.get('config', {}).get('business_domain', ''),
                    "target_users": scenario_data.get('config', {}).get('target_users', []),
                    "key_features": scenario_data.get('config', {}).get('key_features', []),
                    "example_instructions": scenario_data.get('config', {}).get('example_instructions', [])
                },
                "entities": template_data.get('entities', []),
                "workflows": template_data.get('workflows', []),
                "forms": template_data.get('forms', []),
                "api_routes": template_data.get('api_routes', []),
                "template_key": template_key,
                "applied_at": "2024-01-30T00:00:00.000Z",
                "cleanup_info": cleanup_result.get("cleanup_info", {}),
                "apply_info": apply_result.get("apply_info", {})
            }

            return {
                "success": True,
                "data": {
                    "applied_config": applied_config,
                    "template_info": {
                        "key": template_key,
                        "name": self.templates[template_key]["name"],
                        "version": self.templates[template_key].get("version", "1.0.0")
                    }
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": "apply_failed",
                "details": f"应用模板失败: {str(e)}"
            }

    def get_applied_template_data(self, template_key: str) -> Dict[str, Any]:
        """
        获取已应用模板的数据，用于后续配置步骤

        Args:
            template_key: 模板标识符

        Returns:
            模板数据
        """
        if template_key not in self.templates:
            return {
                "success": False,
                "error": "template_not_found",
                "details": "指定的模板标识符不存在"
            }

        try:
            # 从缓存中获取模板数据
            template_data = self._templates_cache.get(template_key)
            if not template_data:
                return {
                    "success": False,
                    "error": "template_data_not_found",
                    "details": "模板数据未找到"
                }

            return {
                "success": True,
                "data": {
                    "entities": template_data.get('entities', []),
                    "api_routes": template_data.get('api_routes', []),
                    "workflows": template_data.get('workflows', []),
                    "forms": template_data.get('forms', []),
                    "scenario": template_data.get('scenario', {})
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": "get_data_failed",
                "details": f"获取模板数据失败: {str(e)}"
            }

    def _cleanup_template_data(self, template_key: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理模板相关的旧数据，避免应用时的名称冲突 (使用ORM)

        Args:
            template_key: 模板标识符
            template_data: 完整的模板数据

        Returns:
            清理结果
        """
        try:
            from app.core.database import get_db_session
            from app.models.entity import EntityDBModel, EntityFieldDBModel
            from app.models.scenario import ScenarioDBModel
            from app.models.api_route import APIRouteDBModel
            from app.models.workflow import WorkflowDBModel
            from app.models.role import (
                RoleDBModel, PermissionDBModel, RolePermissionLogDBModel, UserRoleLogDBModel,
                role_permissions, user_roles
            )
            from app.models.user import User
            from sqlalchemy import text

            cleanup_info = {
                "deleted_entities": 0,
                "deleted_scenarios": 0,
                "deleted_api_routes": 0,
                "deleted_forms": 0,
                "deleted_workflows": 0,
                "deleted_roles": 0,
                "deleted_users": 0,
                "deleted_permissions": 0,
                "deleted_logs": 0,
                "cleanup_count": 0
            }

            with get_db_session() as db:
                # 1. 清理所有实体（应用新模板前清空所有旧实体）
                logger.info("开始清空所有实体...")
                existing_entities = db.query(EntityDBModel).all()
                if existing_entities:
                    logger.info(f"准备清理所有现有的 {len(existing_entities)} 个实体")
                    for entity in existing_entities:
                        # 删除实体对应的数据库表
                        try:
                            from app.services.entity_service import entity_service
                            table_name = f"entity_{entity_service._safe_table_name(entity.name)}"
                            entity_service._drop_entity_database_table(db, table_name)
                            logger.debug(f"  - 删除实体数据表: {table_name}")
                        except Exception as table_error:
                            logger.warning(f"  ⚠️ 删除实体数据表失败: {table_error}")
                    
                    # 使用ORM批量删除
                    db.query(EntityFieldDBModel).delete(synchronize_session=False)
                    num_deleted_entities = db.query(EntityDBModel).delete(synchronize_session=False)
                    cleanup_info["deleted_entities"] = num_deleted_entities
                    cleanup_info["cleanup_count"] += num_deleted_entities
                    logger.info(f"  ✅ 已通过ORM删除 {num_deleted_entities} 个实体及其字段")

                # 2. 完全清空所有用户、角色和权限相关数据
                logger.info("开始清空所有用户、角色和权限...")
                # 2.1 删除日志表，解除外键依赖
                num_deleted_role_perm_logs = db.query(RolePermissionLogDBModel).delete(synchronize_session=False)
                num_deleted_user_role_logs = db.query(UserRoleLogDBModel).delete(synchronize_session=False)
                total_logs = num_deleted_role_perm_logs + num_deleted_user_role_logs
                cleanup_info["deleted_logs"] = total_logs
                cleanup_info["cleanup_count"] += total_logs
                logger.info(f"  ✅ 已删除 {total_logs} 条相关日志")

                # 2.2 清空关联表
                db.execute(user_roles.delete())
                db.execute(role_permissions.delete())
                logger.info("  ✅ 已清空用户-角色和角色-权限关联表")
                
                # 2.3 删除主表记录
                num_deleted_users = db.query(User).delete(synchronize_session=False)
                cleanup_info["deleted_users"] = num_deleted_users
                cleanup_info["cleanup_count"] += num_deleted_users
                logger.info(f"  ✅ 已通过ORM删除 {num_deleted_users} 个用户")

                num_deleted_roles = db.query(RoleDBModel).delete(synchronize_session=False)
                cleanup_info["deleted_roles"] = num_deleted_roles
                cleanup_info["cleanup_count"] += num_deleted_roles
                logger.info(f"  ✅ 已通过ORM删除 {num_deleted_roles} 个角色")

                num_deleted_permissions = db.query(PermissionDBModel).delete(synchronize_session=False)
                cleanup_info["deleted_permissions"] = num_deleted_permissions
                cleanup_info["cleanup_count"] += num_deleted_permissions
                logger.info(f"  ✅ 已通过ORM删除 {num_deleted_permissions} 个权限")

                # 3. 清理所有现有的API路由
                logger.info("开始清空所有API路由...")
                num_deleted_routes = db.query(APIRouteDBModel).delete(synchronize_session=False)
                cleanup_info["deleted_api_routes"] = num_deleted_routes
                cleanup_info["cleanup_count"] += num_deleted_routes
                logger.info(f"  ✅ 已通过ORM删除 {num_deleted_routes} 个API路由")

                # 4. 表单功能已删除，跳过清理
                cleanup_info["deleted_forms"] = 0
                logger.debug("  表单功能已移除，跳过清理")

                # 5. 清理所有现有的工作流
                logger.info("开始清空所有工作流...")
                num_deleted_workflows = db.query(WorkflowDBModel).delete(synchronize_session=False)
                cleanup_info["deleted_workflows"] = num_deleted_workflows
                cleanup_info["cleanup_count"] += num_deleted_workflows
                logger.info(f"  ✅ 已通过ORM删除 {num_deleted_workflows} 个工作流")

                # 6. 清理同名场景
                logger.info("开始清空相关场景...")
                scenario_name_pattern = f"%{self.templates[template_key]['name']}%"
                num_deleted_scenarios = db.query(ScenarioDBModel).filter(
                    ScenarioDBModel.name.like(scenario_name_pattern)
                ).delete(synchronize_session=False)
                cleanup_info["deleted_scenarios"] = num_deleted_scenarios
                cleanup_info["cleanup_count"] += num_deleted_scenarios
                logger.info(f"  ✅ 已通过ORM删除 {num_deleted_scenarios} 个场景")

                # 统一提交所有清理操作
                logger.info(f"提交所有清理操作，共清理 {cleanup_info['cleanup_count']} 项")
                db.commit()
                logger.info("✅ 清理操作完成")

            return {
                "success": True,
                "cleanup_info": cleanup_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": "cleanup_failed",
                "details": f"清理旧数据失败: {str(e)}"
            }

    def _apply_template_to_database(self, template_key: str, template_data: Dict[str, Any], scenario_name: str, description: str = None) -> Dict[str, Any]:
        """
        将模板数据应用到数据库中

        Args:
            template_key: 模板标识符
            template_data: 模板数据
            scenario_name: 场景名称
            description: 场景描述

        Returns:
            应用结果
        """
        try:
            from app.core.database import get_db_session
            from app.models.entity import EntityDBModel, EntityFieldDBModel
            from app.models.scenario import ScenarioDBModel
            from app.models.api_route import APIRouteDBModel, RouteStatus, HandlerType
            from app.models.workflow import WorkflowDBModel
            from app.schemas.scenario import ScenarioType
            from app.models.role import PermissionDBModel
            from app.models.role import RoleDBModel
            import time

            apply_info = {
                "created_entities": [],
                "created_api_routes": [],
                "created_workflows": [],
                "created_roles": [],
                "updated_roles": [],
                "created_scenario": None,
                "apply_count": 0
            }

            with get_db_session() as db:
                # 创建实体（不再创建场景）
                entities_data = template_data.get('entities', [])
                role_entities_to_sync = []
                for entity_data in entities_data:
                    # 检查实体是否已存在
                    existing_entity = db.query(EntityDBModel).filter(EntityDBModel.name == entity_data.get('name')).first()
                    if existing_entity:
                        logger.debug(f"  - 实体 '{entity_data.get('display_name')}' (name: {entity_data.get('name')}) 已存在，检查并更新 is_role 状态")
                        # 即使实体存在，也要确保 is_role 状态与模板一致
                        is_role_in_template = entity_data.get('is_role', False)
                        if existing_entity.is_role != is_role_in_template:
                            existing_entity.is_role = is_role_in_template
                            logger.debug(f"    - 更新实体 '{existing_entity.display_name}' 的 is_role 状态为: {is_role_in_template}")
                        if is_role_in_template:
                            role_entities_to_sync.append(existing_entity)
                        continue

                    entity_id = f"entity_{int(time.time() * 1000)}_{len(apply_info['created_entities'])}"

                    entity = EntityDBModel(
                        id=entity_id,
                        name=entity_data.get('name'),
                        display_name=entity_data.get('display_name') or entity_data.get('displayName'),
                        description=entity_data.get('description'),
                        icon=entity_data.get('icon'),
                        status=entity_data.get('status', 'active'),
                        is_role=entity_data.get('is_role', False),  # 确保角色标识字段被正确设置
                        field_count=len(entity_data.get('fields', []))
                    )
                    db.add(entity)
                    
                    if entity.is_role:
                        role_entities_to_sync.append(entity)

                    db.flush()

                    logger.info(f"✅ 创建实体: {entity_data.get('display_name') or entity_data.get('displayName')} (is_role: {entity_data.get('is_role', False)})")

                    # 自动创建实体对应的数据库表
                    try:
                        # 转换字段格式以匹配EntityService的期望格式
                        fields_data = []
                        for field_data in entity_data.get('fields', []):
                            # 创建字段对象，转换模板格式到EntityService格式
                            from app.schemas.entity import EntityFieldCreateRequest, FieldType, FieldValidation

                            # 转换字段类型
                            field_type_str = field_data.get('type', 'text')
                            try:
                                field_type = FieldType(field_type_str)
                            except ValueError:
                                # 如果类型不匹配，默认使用text
                                field_type = FieldType.TEXT

                            # 转换验证规则
                            validation = None
                            if field_data.get('validation'):
                                validation = FieldValidation(**field_data['validation'])

                            # 兼容不同的字段格式：
                            # 1. 电商模板使用 display_name, unique_field, default_value
                            # 2. 医院模板使用 displayName, unique, defaultValue
                            display_name = field_data.get('displayName') or field_data.get('display_name')
                            unique = field_data.get('unique', False) or field_data.get('unique_field', False)
                            default_value = field_data.get('defaultValue') or field_data.get('default_value')

                            field_request = EntityFieldCreateRequest(
                                name=field_data.get('name'),
                                displayName=display_name,
                                type=field_type,
                                required=field_data.get('required', False),
                                unique=unique,
                                defaultValue=default_value,
                                validation=validation,
                                options=field_data.get('options')
                            )
                            fields_data.append(field_request)

                        # 调用EntityService的创建数据表方法（同步版本）
                        from app.services.entity_service import entity_service
                        entity_service._create_entity_database_table_sync(
                            entity_data.get('name'),
                            fields_data,
                            db
                        )
                        logger.info(f"✅ 为实体 '{entity_data.get('display_name')}' 自动创建了数据库表")

                    except Exception as table_error:
                        logger.warning(f"⚠️ 实体 '{entity_data.get('display_name')}' 的数据库表创建失败: {str(table_error)}")
                        import traceback
                        logger.debug(f"表创建错误详情: {traceback.format_exc()}")
                        # 继续执行，不因为表创建失败而中断实体创建

                    # 创建实体字段
                    fields_data = entity_data.get('fields', [])
                    for field_index, field_data in enumerate(fields_data):
                        field_id = f"field_{int(time.time() * 1000)}_{field_index}"

                        # 处理字段类型映射
                        field_type = field_data.get('type')
                        if field_type == 'textarea':
                            field_type = 'text'  # 将 textarea 映射为 text

                        field = EntityFieldDBModel(
                            id=field_id,
                            entity_id=entity_id,
                            name=field_data.get('name'),
                            display_name=field_data.get('displayName') or field_data.get('display_name'),
                            type=field_type,
                            required=field_data.get('required', False),
                            unique_field=field_data.get('unique') or field_data.get('unique_field', False),
                            default_value=field_data.get('defaultValue') or field_data.get('default_value'),
                            validation=field_data.get('validation'),
                            options=field_data.get('options'),
                            sort_order=field_data.get('sort_order', 0)
                        )
                        db.add(field)

                    apply_info["created_entities"].append({
                        "id": entity_id,
                        "name": entity_data.get('name'),
                        "display_name": entity_data.get('display_name') or entity_data.get('displayName')
                    })
                    apply_info["apply_count"] += 1

                # 3. 创建API路由并动态注册
                api_routes_data = template_data.get('api_routes', [])
                if api_routes_data:
                    logger.info(f"开始创建 {len(api_routes_data)} 个API路由")
                    
                    # 导入动态路由管理器
                    from app.core.dynamic_router import get_dynamic_router
                    
                    for route_data in api_routes_data:
                        route_id = f"route_{int(time.time() * 1000)}_{len(apply_info['created_api_routes'])}"

                        # 转换处理器类型 - 兼容两种格式:
                        # 格式1: handler: { type: ..., config: ... } (推荐格式)
                        # 格式2: handler_type: ..., handler_config: ... (旧格式)
                        if 'handler' in route_data and isinstance(route_data.get('handler'), dict):
                            # 新格式: handler: { type: ..., config: ... }
                            handler_type_str = route_data.get('handler', {}).get('type', 'ENTITY_CRUD')
                            handler_config_data = route_data.get('handler', {}).get('config', {})
                        else:
                            # 旧格式: handler_type, handler_config
                            handler_type_str = route_data.get('handler_type', 'ENTITY_CRUD')
                            handler_config_data = route_data.get('handler_config', {})
                        
                        try:
                            normalized = str(handler_type_str).strip().lower()
                            alias_map = {
                                "custom": "custom_function",
                                "custom_function": "custom_function",
                                "customfunc": "custom_function",
                                "static": "static_data",
                                "static_data": "static_data",
                                "entity": "entity_crud",
                                "crud": "entity_crud",
                            }
                            normalized = alias_map.get(normalized, normalized)
                            handler_type = HandlerType[normalized.upper()]
                        except (KeyError, AttributeError):
                            handler_type = HandlerType.ENTITY_CRUD

                        # 规范化端点为 /api/v1 前缀
                        raw_endpoint = route_data.get('endpoint') or ''
                        normalized_endpoint = raw_endpoint
                        try:
                            if isinstance(raw_endpoint, str):
                                if raw_endpoint.startswith('/api/vl/'):
                                    normalized_endpoint = '/api/v1' + raw_endpoint[7:]
                                elif raw_endpoint.startswith('/api/') and not raw_endpoint.startswith('/api/v1/'):
                                    normalized_endpoint = '/api/v1' + raw_endpoint[4:]
                        except Exception:
                            pass

                        # 获取参数和响应配置 - 兼容两种格式:
                        # 格式1: parameters, responses (推荐格式)
                        # 格式2: parameters_config, responses_config (旧格式)
                        parameters_data = route_data.get('parameters') or route_data.get('parameters_config', [])
                        responses_data = route_data.get('responses') or route_data.get('responses_config', {})

                        # 创建API路由
                        api_route = APIRouteDBModel(
                            id=route_id,
                            api_id=route_data.get('api_id'),
                            name=route_data.get('name'),
                            endpoint=normalized_endpoint,
                            method=route_data.get('method', 'GET'),
                            description=route_data.get('description'),
                            handler_type=handler_type.value,  # 使用枚举的字符串值
                            handler_config=handler_config_data,
                            auth_required=route_data.get('auth_required', False),
                            parameters_config=parameters_data,
                            responses_config=responses_data,
                            status=RouteStatus.ACTIVE,
                            call_count=0,
                            avg_response_time=0.0
                        )
                        db.add(api_route)
                        db.flush()
                        
                        # 打印调试信息
                        logger.info(f"✅ API路由创建: {route_data.get('api_id')} - handler_type: {handler_type.value}, handler_config: {handler_config_data}")

                        # 动态注册路由到FastAPI应用
                        try:
                            dynamic_router = get_dynamic_router()
                            route_config = {
                                "id": route_id,
                                "endpoint": normalized_endpoint,
                                "method": route_data.get('method', 'GET').upper(),
                                "handler_config": handler_config_data
                            }

                            # add_dynamic_route 会自动输出日志，这里不需要重复
                            if not dynamic_router.add_dynamic_route(route_config):
                                logger.warning(f"⚠️ 动态路由注册失败: {route_data.get('method', 'GET').upper()} {normalized_endpoint}")
                        except Exception as e:
                            logger.warning(f"⚠️ 动态路由注册异常: {e}")
                            # 动态路由添加失败不应该阻止模板应用，继续执行

                        apply_info["created_api_routes"].append({
                            "id": route_id,
                            "api_id": route_data.get('api_id'),
                            "name": route_data.get('name'),
                            "endpoint": normalized_endpoint,
                            "method": route_data.get('method', 'GET')
                        })
                        apply_info["apply_count"] += 1

                # 4. 创建工作流
                workflows_data = template_data.get('workflows', [])
                if workflows_data:
                    logger.info(f"开始创建 {len(workflows_data)} 个工作流")
                    
                    for workflow_data in workflows_data:
                        # 🔥 直接使用 workflow name 作为 workflow_id（语义化，与数据集一致）
                        workflow_name = workflow_data.get('name', 'unnamed')
                        workflow_id = workflow_name  # 直接用 name 作为 id
                        # 🔥 使用 display_name 作为显示名称，如果没有则使用 name
                        display_name = workflow_data.get('display_name', workflow_name)
                        
                        # 检查是否已存在同名工作流
                        existing = db.query(WorkflowDBModel).filter(WorkflowDBModel.id == workflow_id).first()
                        if existing:
                            logger.warning(f"⚠️ 工作流 {workflow_id} 已存在，跳过创建")
                            continue

                        # 创建工作流记录
                        workflow = WorkflowDBModel(
                            id=workflow_id,
                            name=display_name,  # 🔥 使用 display_name 作为显示名称
                            description=workflow_data.get('description'),
                            business_scenario=workflow_data.get('business_scenario', template_key),
                            status="ACTIVE",  # 设置为活跃状态
                            user_intents=workflow_data.get('user_intents', []),
                            trigger_keywords=workflow_data.get('trigger_keywords', []),
                            inputs=workflow_data.get('inputs', []),
                            nodes=workflow_data.get('nodes', []),
                            workflow_metadata=workflow_data.get('metadata', {}),
                            created_by="template_system"
                        )
                        db.add(workflow)
                        db.flush()

                        apply_info["created_workflows"].append({
                            "id": workflow_id,
                            "name": display_name,  # 🔥 使用 display_name
                            "business_scenario": workflow_data.get('business_scenario', template_key),
                            "node_count": len(workflow_data.get('nodes', []))
                        })
                        apply_info["apply_count"] += 1
                        logger.info(f"✅ 工作流创建成功: {display_name} ({workflow_id})")

                # 7. 在当前事务中同步角色实体为角色记录 (移到commit之前)
                logger.info("在当前事务中同步角色实体...")
                try:
                    from app.services.dynamic_user_service import DynamicUserService
                    user_service = DynamicUserService()
                    # 传入当前的db session和需要同步的实体列表
                    role_sync_result = user_service.sync_entity_roles(db=db, role_entities=role_entities_to_sync)

                    if role_sync_result.get("success"):
                        created_dynamic_roles = role_sync_result.get("created_roles", [])
                        updated_dynamic_roles = role_sync_result.get("updated_roles", [])

                        # 将动态创建的角色信息合并到 apply_info 中
                        apply_info["created_roles"].extend(created_dynamic_roles)
                        apply_info["updated_roles"].extend(updated_dynamic_roles)
                        apply_info["apply_count"] += len(created_dynamic_roles)

                        logger.info(f"✅ 动态角色同步完成: 创建 {len(created_dynamic_roles)} 个新角色, 更新 {len(updated_dynamic_roles)} 个角色")
                        for role in created_dynamic_roles:
                            logger.debug(f"  - 创建动态角色: {role['role_name']} (基于实体: {role['entity_name']})")
                    else:
                        logger.warning(f"⚠️ 角色同步失败: {role_sync_result}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ 角色同步异常: {e}")
                    import traceback
                    logger.debug(f"详细错误信息: {traceback.format_exc()}")
                    # 角色同步失败不应该阻止模板应用

                # 提交所有数据，包括实体、API、工作流和动态创建的角色
                db.commit()

                # 5. 角色已通过角色实体自动创建，无需从模板单独创建
                logger.debug("角色已通过角色实体自动创建，跳过模板角色创建步骤")

                # 6. 创建并分配权限
                logger.info("开始创建和分配权限...")
                all_template_permissions = []
                for route_info in apply_info["created_api_routes"]:
                    permission_name = f"{route_info['api_id']}:access"
                    permission = db.query(PermissionDBModel).filter(PermissionDBModel.name == permission_name).first()
                    if not permission:
                        permission_id = f"perm_{int(time.time() * 1000)}_{len(all_template_permissions)}"
                        permission = PermissionDBModel(
                            id=permission_id,
                            name=permission_name,
                            description=f"模板自动生成的权限: {route_info['name']}",
                            resource=route_info['api_id'].replace("_api", ""),
                            action="access"
                        )
                        db.add(permission)
                        logger.debug(f"  - 创建新权限: {permission_name}")
                        all_template_permissions.append(permission)
                db.commit() # 提交新创建的权限

                
                # 8. 将所有模板权限分配给所有同步的角色
                if all_template_permissions and (apply_info["created_roles"] or apply_info["updated_roles"]):
                    logger.info(f"开始将 {len(all_template_permissions)} 个权限分配给所有新创建和更新的角色...")
                    all_role_ids = [role['role_id'] for role in apply_info["created_roles"]] + [role['role_id'] for role in apply_info["updated_roles"]]
                    roles_to_update = db.query(RoleDBModel).filter(RoleDBModel.id.in_(all_role_ids)).all()

                    for role in roles_to_update:
                        logger.debug(f"  - 为角色 '{role.name}' 分配权限...")
                        for perm in all_template_permissions:
                            if perm not in role.permissions:
                                role.permissions.append(perm)
                    db.commit()
                    logger.info("✅ 权限分配完成")

            return {
                "success": True,
                "apply_info": apply_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": "apply_failed",
                "details": f"应用模板到数据库失败: {str(e)}"
            }

    def has_sample_data(self, template_key: str) -> Dict[str, Any]:
        """
        检查模板是否包含示例数据
        
        Args:
            template_key: 模板标识符
            
        Returns:
            包含示例数据信息的字典
        """
        if template_key not in self.templates:
            return {
                "success": False,
                "error": "template_not_found",
                "details": "指定的模板标识符不存在"
            }
        
        try:
            template_data = self._templates_cache.get(template_key)
            if not template_data:
                return {
                    "success": False,
                    "error": "template_data_not_found",
                    "details": "模板数据未找到"
                }
            
            entities = template_data.get('entities', [])
            entities_with_sample_data = []
            total_records = 0
            
            for entity in entities:
                sample_data = entity.get('sample_data', [])
                if sample_data:
                    entities_with_sample_data.append({
                        "name": entity.get('name'),
                        "display_name": entity.get('display_name'),
                        "record_count": len(sample_data)
                    })
                    total_records += len(sample_data)
            
            return {
                "success": True,
                "data": {
                    "has_sample_data": len(entities_with_sample_data) > 0,
                    "entity_count": len(entities_with_sample_data),
                    "total_records": total_records,
                    "entities": entities_with_sample_data
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "check_failed",
                "details": f"检查示例数据失败: {str(e)}"
            }

    def _get_entity_import_order(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根据实体依赖关系确定导入顺序
        
        Args:
            entities: 实体列表
            
        Returns:
            排序后的实体列表
        """
        # 定义实体导入优先级（数字越小越先导入）
        priority_map = {
            'station': 1,      # 车站无依赖
            'passenger': 2,    # 乘客无依赖
            'train': 3,        # 列车引用车站
            'seat': 4,         # 座位引用列车
            'ticket': 5,       # 车票引用列车、乘客、车站
            'order': 6,        # 订单引用乘客
            'payment': 7,      # 支付引用订单
            'refund': 8,       # 退款引用车票
            'change': 9,       # 改签引用车票
        }
        
        def get_priority(entity):
            name = entity.get('name', '')
            return priority_map.get(name, 100)  # 未知实体放最后
        
        return sorted(entities, key=get_priority)

    def import_sample_data(self, template_key: str) -> Dict[str, Any]:
        """
        导入模板的示例数据到数据库
        
        Args:
            template_key: 模板标识符
            
        Returns:
            导入结果
        """
        if template_key not in self.templates:
            return {
                "success": False,
                "error": "template_not_found",
                "details": "指定的模板标识符不存在"
            }
        
        try:
            from app.services.entity_service import entity_service
            
            template_data = self._templates_cache.get(template_key)
            if not template_data:
                return {
                    "success": False,
                    "error": "template_data_not_found",
                    "details": "模板数据未找到"
                }
            
            entities = template_data.get('entities', [])
            
            # 按依赖顺序排序实体
            sorted_entities = self._get_entity_import_order(entities)
            
            import_results = {
                "total_entities": 0,
                "imported_entities": 0,
                "total_records": 0,
                "success_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "entity_details": []
            }
            
            for entity in sorted_entities:
                entity_name = entity.get('name')
                sample_data = entity.get('sample_data', [])
                
                if not sample_data:
                    continue
                
                import_results["total_entities"] += 1
                
                # 获取实体ID
                entity_result = entity_service.get_entity_by_name(entity_name)
                if not entity_result.get('success'):
                    logger.warning(f"⚠️ 实体 '{entity_name}' 不存在，跳过示例数据导入")
                    import_results["entity_details"].append({
                        "entity_name": entity_name,
                        "display_name": entity.get('display_name'),
                        "total": len(sample_data),
                        "success": 0,
                        "skipped": len(sample_data),
                        "errors": [f"实体 '{entity_name}' 不存在"]
                    })
                    import_results["skipped_count"] += len(sample_data)
                    continue
                
                entity_id = entity_result['data']['entity'].id
                entity_detail = {
                    "entity_name": entity_name,
                    "display_name": entity.get('display_name'),
                    "total": len(sample_data),
                    "success": 0,
                    "skipped": 0,
                    "errors": []
                }
                
                logger.info(f"导入实体 '{entity.get('display_name')}' 的示例数据 ({len(sample_data)} 条)")
                
                for i, record in enumerate(sample_data):
                    import_results["total_records"] += 1
                    
                    try:
                        result = entity_service.create_entity_record(entity_id, record)
                        
                        if result.get('success'):
                            entity_detail["success"] += 1
                            import_results["success_count"] += 1
                        else:
                            error_msg = result.get('details', result.get('error', '未知错误'))
                            # 检查是否是唯一字段冲突
                            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                                entity_detail["skipped"] += 1
                                import_results["skipped_count"] += 1
                                logger.debug(f"  记录 {i+1} 跳过（唯一字段冲突）")
                            else:
                                entity_detail["errors"].append(f"记录 {i+1}: {error_msg}")
                                import_results["error_count"] += 1
                                logger.warning(f"  记录 {i+1} 导入失败: {error_msg}")
                    except Exception as e:
                        error_msg = str(e)
                        if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                            entity_detail["skipped"] += 1
                            import_results["skipped_count"] += 1
                        else:
                            entity_detail["errors"].append(f"记录 {i+1}: {error_msg}")
                            import_results["error_count"] += 1
                
                import_results["entity_details"].append(entity_detail)
                
                if entity_detail["success"] > 0:
                    import_results["imported_entities"] += 1
                    logger.info(f"  ✅ 成功导入 {entity_detail['success']}/{entity_detail['total']} 条记录")
            
            return {
                "success": True,
                "data": import_results
            }
            
        except Exception as e:
            import traceback
            logger.error(f"❌ 导入示例数据失败: {str(e)}")
            logger.debug(f"详细错误: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "import_failed",
                "details": f"导入示例数据失败: {str(e)}"
            }


# 全局模板服务实例
template_service = TemplateService()
