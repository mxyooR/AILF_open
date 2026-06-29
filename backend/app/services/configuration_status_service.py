"""
配置状态管理服务
管理和检查七步配置的完成状态
"""
from app.core.logging_config import get_logger
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db_session
from app.models.configuration_status import ConfigurationStatus
from app.config import settings

logger = get_logger(__name__)


class ConfigurationStatusService:
    """配置状态管理服务"""
    
    def __init__(self):
        self.default_scenario_id = "default"  # 默认场景ID
    
    def get_or_create_status(self, scenario_id: str = None) -> Optional[ConfigurationStatus]:
        """获取或创建配置状态"""
        if not scenario_id:
            scenario_id = self.default_scenario_id
            
        try:
            with get_db_session() as db:
                # 尝试获取现有状态
                status = db.query(ConfigurationStatus).filter(
                    ConfigurationStatus.scenario_id == scenario_id
                ).first()
                
                if not status:
                    # 创建新的状态记录
                    status = ConfigurationStatus(scenario_id=scenario_id)
                    db.add(status)
                    db.commit()
                    db.refresh(status)
                    logger.info(f"创建新的配置状态记录: {scenario_id}")
                
                return status
                
        except SQLAlchemyError as e:
            logger.error(f"获取或创建配置状态失败: {str(e)}")
            return None
    
    def update_step_completion(self, step_number: int, completed: bool = True, 
                             scenario_id: str = None, details: Optional[Dict[str, Any]] = None) -> bool:
        """更新步骤完成状态"""
        if not scenario_id:
            scenario_id = self.default_scenario_id
            
        if step_number < 1 or step_number > 7:
            logger.error(f"无效的步骤编号: {step_number}")
            return False
            
        try:
            with get_db_session() as db:
                status = db.query(ConfigurationStatus).filter(
                    ConfigurationStatus.scenario_id == scenario_id
                ).first()
                
                if not status:
                    status = ConfigurationStatus(scenario_id=scenario_id)
                    db.add(status)
                
                # 更新步骤状态
                status.update_step_completion(step_number, completed, details)
                
                db.commit()
                db.refresh(status)
                
                logger.info(f"更新步骤 {step_number} 完成状态: {completed}, 场景: {scenario_id}")
                
                # 如果所有步骤都完成了，记录日志
                if status.all_steps_completed:
                    logger.info(f"🎉 所有配置步骤已完成! 场景: {scenario_id}")
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"更新步骤完成状态失败: {str(e)}")
            return False
    
    def is_configuration_completed(self, scenario_id: str = None) -> bool:
        """检查配置是否完成"""
        # 优先检查环境变量设置
        if settings.CONFIGURATION_COMPLETED:
            logger.debug("环境变量 CONFIGURATION_COMPLETED=true，跳过配置检查")
            return True

        if not scenario_id:
            scenario_id = self.default_scenario_id

        try:
            with get_db_session() as db:
                status = db.query(ConfigurationStatus).filter(
                    ConfigurationStatus.scenario_id == scenario_id
                ).first()

                if not status:
                    return False

                return status.all_steps_completed

        except SQLAlchemyError as e:
            logger.error(f"检查配置完成状态失败: {str(e)}")
            return False
    
    def get_configuration_status(self, scenario_id: str = None) -> Optional[Dict[str, Any]]:
        """获取配置状态详情"""
        if not scenario_id:
            scenario_id = self.default_scenario_id

        # 如果环境变量设置为已完成，返回全部完成的状态
        logger.debug(f"检查环境变量 CONFIGURATION_COMPLETED: {settings.CONFIGURATION_COMPLETED}")
        if settings.CONFIGURATION_COMPLETED:
            logger.debug("环境变量 CONFIGURATION_COMPLETED=true，返回全部完成状态")
            from datetime import datetime
            current_time = datetime.now().isoformat()
            return {
                "scenario_id": scenario_id,
                "steps": {
                    f"step{i}": {"completed": True, "completed_at": current_time}
                    for i in range(1, 8)
                },
                "all_completed": True,
                "all_completed_at": current_time,
                "completed_count": 7,
                "total_steps": 7,
                "completion_percentage": 100.0
            }

        logger.debug("环境变量 CONFIGURATION_COMPLETED=false，使用数据库状态")

        try:
            with get_db_session() as db:
                status = db.query(ConfigurationStatus).filter(
                    ConfigurationStatus.scenario_id == scenario_id
                ).first()

                if not status:
                    # 返回默认状态
                    return {
                        "scenario_id": scenario_id,
                        "steps": {
                            f"step{i}": {"completed": False, "completed_at": None}
                            for i in range(1, 8)
                        },
                        "all_completed": False,
                        "all_completed_at": None,
                        "completed_count": 0,
                        "total_steps": 7,
                        "completion_percentage": 0.0
                    }

                return status.get_completion_summary()

        except SQLAlchemyError as e:
            logger.error(f"获取配置状态失败: {str(e)}")
            return None
    
    def get_incomplete_steps(self, scenario_id: str = None) -> List[int]:
        """获取未完成的步骤列表"""
        if not scenario_id:
            scenario_id = self.default_scenario_id
            
        try:
            with get_db_session() as db:
                status = db.query(ConfigurationStatus).filter(
                    ConfigurationStatus.scenario_id == scenario_id
                ).first()
                
                if not status:
                    return list(range(1, 8))  # 所有步骤都未完成
                
                incomplete_steps = []
                steps = [
                    status.step1_auth_completed,
                    status.step2_scenario_completed,
                    status.step3_template_completed,
                    status.step4_entity_completed,
                    status.step5_api_completed,
                    status.step6_workflow_completed,
                    status.step7_role_completed
                ]
                
                for i, completed in enumerate(steps, 1):
                    if not completed:
                        incomplete_steps.append(i)
                
                return incomplete_steps
                
        except SQLAlchemyError as e:
            logger.error(f"获取未完成步骤失败: {str(e)}")
            return list(range(1, 8))
    
    def reset_configuration(self, scenario_id: str = None) -> bool:
        """重置配置状态"""
        if not scenario_id:
            scenario_id = self.default_scenario_id
            
        try:
            with get_db_session() as db:
                status = db.query(ConfigurationStatus).filter(
                    ConfigurationStatus.scenario_id == scenario_id
                ).first()
                
                if status:
                    status.reset_all_steps()
                    db.commit()
                    logger.info(f"重置配置状态: {scenario_id}")
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"重置配置状态失败: {str(e)}")
            return False
    
    def get_step_name(self, step_number: int) -> str:
        """获取步骤名称"""
        step_names = {
            1: "开发者认证",
            2: "场景配置", 
            3: "模板选择",
            4: "实体建模",
            5: "API路由管理",
            6: "工作流设计",
            7: "角色管理"
        }
        return step_names.get(step_number, f"步骤{step_number}")
    
    def validate_access_permission(self, scenario_id: str = None) -> Dict[str, Any]:
        """验证访问权限（是否完成配置）"""
        if not scenario_id:
            scenario_id = self.default_scenario_id
            
        is_completed = self.is_configuration_completed(scenario_id)
        
        if is_completed:
            return {
                "allowed": True,
                "message": "配置已完成，可以使用所有功能",
                "status": "completed"
            }
        else:
            incomplete_steps = self.get_incomplete_steps(scenario_id)
            step_names = [self.get_step_name(step) for step in incomplete_steps]
            
            return {
                "allowed": False,
                "message": f"配置未完成，请先完成以下步骤：{', '.join(step_names)}",
                "status": "incomplete",
                "incomplete_steps": incomplete_steps,
                "incomplete_step_names": step_names
            }


# 创建全局实例
configuration_status_service = ConfigurationStatusService()
