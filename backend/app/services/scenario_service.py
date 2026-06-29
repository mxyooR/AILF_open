"""
场景管理服务
处理场景的CRUD操作、验证和模板创建的业务逻辑
"""
from typing import Optional, Dict, Any, List
from app.models.scenario import scenario_model
from app.schemas.scenario import (
    Scenario, ScenarioCreateRequest, ScenarioUpdateRequest,
    ScenarioValidateRequest, ScenarioFromTemplateRequest,
    ScenarioValidateSuccessData, ScenarioValidateFailData,
    ValidationChecks, ScenarioType, ScenarioStatus
)


class ScenarioService:
    """场景管理服务类"""
    
    def __init__(self):
        self.model = scenario_model
        # 预设模板配置
        self.templates = {
            "ecommerce_basic": {
                "name": "基础电商模板",
                "type": ScenarioType.ECOMMERCE,
                "description": "基础电子商务管理系统模板",
                "config": {
                    "business_domain": "电子商务",
                    "target_users": ["管理员", "销售人员"],
                    "key_features": ["商品管理", "订单处理", "用户管理"],
                    "example_instructions": ["查看今日订单", "新增商品：咖啡豆", "查询用户信息"],
                    "custom_settings": {
                        "support_multi_currency": False,
                        "default_language": "zh-CN",
                        "payment_methods": ["支付宝", "微信支付"]
                    }
                }
            },
            "restaurant_basic": {
                "name": "基础餐厅模板",
                "type": ScenarioType.RESTAURANT,
                "description": "基础餐厅管理系统模板",
                "config": {
                    "business_domain": "餐饮服务",
                    "target_users": ["店长", "服务员", "厨师"],
                    "key_features": ["菜品管理", "订单管理", "桌台管理"],
                    "example_instructions": ["查看当前订单", "新增菜单项：拿铁", "查询桌台状态"],
                    "custom_settings": {
                        "table_count": 10,
                        "support_takeout": True,
                        "support_delivery": False
                    }
                }
            },
            "hospital_basic": {
                "name": "基础医院模板",
                "type": ScenarioType.HOSPITAL,
                "description": "基础医院管理系统模板",
                "config": {
                    "business_domain": "医疗服务",
                    "target_users": ["医生", "护士", "管理员"],
                    "key_features": ["患者管理", "预约挂号", "病历管理"],
                    "example_instructions": ["查询患者信息", "预约挂号", "查看今日排班"],
                    "custom_settings": {
                        "departments": ["内科", "外科", "儿科"],
                        "support_online_booking": True
                    }
                }
            }
        }
    
    def get_active_scenario(self, include_details: bool = False) -> Dict[str, Any]:
        """获取当前活跃场景"""
        scenario = self.model.get_active_scenario()
        
        if not scenario:
            return {
                "success": False,
                "error": "no_active_scenario",
                "details": "系统中没有配置活跃的业务场景"
            }
        
        return {
            "success": True,
            "data": {"scenario": scenario}
        }
    
    def create_or_update_scenario(self, request: ScenarioCreateRequest) -> Dict[str, Any]:
        """创建或更新场景配置"""
        try:
            # 检查场景名称是否重复
            if self.model.scenario_exists_by_name(request.name):
                return {
                    "success": False,
                    "error": "duplicate_scenario",
                    "details": "场景名称已存在"
                }
        
            # 创建场景数据
            scenario_data = {
                "name": request.name,
                "type": request.type.value,
                "description": request.description or "",
                "config": request.config.model_dump(),
                "status": ScenarioStatus.ACTIVE.value
            }

            scenario = self.model.create_scenario(scenario_data)

            return {
                "success": True,
                "data": {"scenario": scenario},
                "created": True
            }

        except Exception as e:
            import traceback
            error_details = f"创建场景失败: {str(e)}\n{traceback.format_exc()}"
            return {
                "success": False,
                "error": "creation_failed",
                "details": error_details
            }
    
    def get_scenario_by_id(self, scenario_id: str) -> Dict[str, Any]:
        """根据ID获取场景"""
        scenario = self.model.get_scenario_by_id(scenario_id)
        
        if not scenario:
            return {
                "success": False,
                "error": "scenario_not_found",
                "details": "指定的场景ID不存在"
            }
        
        return {
            "success": True,
            "data": {"scenario": scenario}
        }
    
    def validate_scenario(self, request: ScenarioValidateRequest) -> Dict[str, Any]:
        """验证场景配置"""
        scenario = self.model.get_scenario_by_id(request.scenario_id)
        
        if not scenario:
            return {
                "success": False,
                "error": "scenario_not_found",
                "details": "指定的场景ID不存在"
            }
        
        # 执行验证检查
        validation_result = self._perform_validation_checks(scenario, request)
        
        if validation_result["valid"]:
            return {
                "success": True,
                "data": ScenarioValidateSuccessData(**validation_result)
            }
        else:
            return {
                "success": False,
                "data": ScenarioValidateFailData(**validation_result)
            }
    
    def create_from_template(self, request: ScenarioFromTemplateRequest) -> Dict[str, Any]:
        """从模板创建场景"""
        # 检查模板是否存在
        if request.template_key not in self.templates:
            return {
                "success": False,
                "error": "template_not_found",
                "details": "指定的模板不存在"
            }
        
        # 检查场景名称是否重复
        if self.model.scenario_exists_by_name(request.name):
            return {
                "success": False,
                "error": "duplicate_scenario",
                "details": "场景名称已存在"
            }
        
        # 获取模板配置
        template = self.templates[request.template_key]
        
        # 合并自定义配置
        config = template["config"].copy()
        if request.customizations:
            config["custom_settings"].update(request.customizations)
        
        # 创建场景数据
        scenario_data = {
            "name": request.name,
            "type": template["type"].value,
            "description": request.description or template["description"],
            "template_key": request.template_key,
            "config": config,
            "status": ScenarioStatus.ACTIVE.value
        }
        
        try:
            scenario = self.model.create_scenario(scenario_data)
            return {
                "success": True,
                "data": {"scenario": scenario},
                "created": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"从模板创建场景失败: {str(e)}"
            }
    
    def _perform_validation_checks(self, scenario: Scenario, request: ScenarioValidateRequest) -> Dict[str, Any]:
        """执行验证检查"""
        errors = []
        warnings = []
        suggestions = []
        
        # 基础信息检查
        basic_info_status = "passed"
        if not scenario.name or len(scenario.name.strip()) == 0:
            errors.append("场景名称不能为空")
            basic_info_status = "failed"
        
        if not scenario.config.business_domain:
            errors.append("业务领域不能为空")
            basic_info_status = "failed"
        
        if not scenario.config.target_users:
            errors.append("目标用户群体不能为空")
            basic_info_status = "failed"
        
        if not scenario.config.key_features:
            errors.append("关键功能列表不能为空")
            basic_info_status = "failed"

        if not scenario.config.example_instructions:
            errors.append("示例指令不能为空")
            basic_info_status = "failed"
        
        # 实体检查（模拟）
        entities_status = "passed"
        if request.check_dependencies:
            # 这里可以添加实际的实体依赖检查逻辑
            suggestions.append("建议添加更多实体定义以完善业务模型")
        
        # 工作流检查（模拟）
        workflows_status = "passed"
        if request.check_completeness:
            # 这里可以添加实际的工作流完整性检查逻辑
            suggestions.append("考虑优化工作流步骤")
        
        # 表单检查（模拟）
        forms_status = "passed"
        warnings.append("部分表单字段未配置验证规则")
        
        # 权限检查（模拟）
        permissions_status = "passed"
        
        # 构建验证结果
        checks = ValidationChecks(
            basic_info=basic_info_status,
            entities=entities_status,
            workflows=workflows_status,
            forms=forms_status,
            permissions=permissions_status
        )
        
        return {
            "valid": len(errors) == 0,
            "scenario_id": scenario.id,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """获取可用模板列表"""
        return [
            {
                "key": key,
                "name": template["name"],
                "type": template["type"].value,
                "description": template["description"]
            }
            for key, template in self.templates.items()
        ]


# 全局场景服务实例
scenario_service = ScenarioService()
