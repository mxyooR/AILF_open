"""
配置完成状态模型
跟踪七步配置的完成状态
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import json
from typing import Dict, Any, Optional


class ConfigurationStatus(Base):
    """配置完成状态模型"""
    __tablename__ = "configuration_status"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(50), unique=True, index=True, comment="场景ID")
    
    # 七个步骤的完成状态
    step1_auth_completed = Column(Boolean, default=False, comment="步骤1：开发者认证")
    step2_scenario_completed = Column(Boolean, default=False, comment="步骤2：场景配置")
    step3_template_completed = Column(Boolean, default=False, comment="步骤3：模板选择")
    step4_entity_completed = Column(Boolean, default=False, comment="步骤4：实体建模")
    step5_api_completed = Column(Boolean, default=False, comment="步骤5：API路由管理")
    step6_workflow_completed = Column(Boolean, default=False, comment="步骤6：工作流设计")
    step7_role_completed = Column(Boolean, default=False, comment="步骤7：角色管理")
    
    # 整体完成状态
    all_steps_completed = Column(Boolean, default=False, comment="所有步骤是否完成")
    
    # 完成时间记录
    step1_completed_at = Column(DateTime, nullable=True, comment="步骤1完成时间")
    step2_completed_at = Column(DateTime, nullable=True, comment="步骤2完成时间")
    step3_completed_at = Column(DateTime, nullable=True, comment="步骤3完成时间")
    step4_completed_at = Column(DateTime, nullable=True, comment="步骤4完成时间")
    step5_completed_at = Column(DateTime, nullable=True, comment="步骤5完成时间")
    step6_completed_at = Column(DateTime, nullable=True, comment="步骤6完成时间")
    step7_completed_at = Column(DateTime, nullable=True, comment="步骤7完成时间")
    all_completed_at = Column(DateTime, nullable=True, comment="全部完成时间")
    
    # 额外信息
    completion_details = Column(Text, nullable=True, comment="完成详情JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.completion_details = json.dumps({})
    
    def get_completion_summary(self) -> Dict[str, Any]:
        """获取完成状态摘要"""
        return {
            "scenario_id": self.scenario_id,
            "steps": {
                "step1_auth": {
                    "completed": self.step1_auth_completed,
                    "completed_at": self.step1_completed_at.isoformat() if self.step1_completed_at else None
                },
                "step2_scenario": {
                    "completed": self.step2_scenario_completed,
                    "completed_at": self.step2_completed_at.isoformat() if self.step2_completed_at else None
                },
                "step3_template": {
                    "completed": self.step3_template_completed,
                    "completed_at": self.step3_completed_at.isoformat() if self.step3_completed_at else None
                },
                "step4_entity": {
                    "completed": self.step4_entity_completed,
                    "completed_at": self.step4_completed_at.isoformat() if self.step4_completed_at else None
                },
                "step5_api": {
                    "completed": self.step5_api_completed,
                    "completed_at": self.step5_completed_at.isoformat() if self.step5_completed_at else None
                },
                "step6_workflow": {
                    "completed": self.step6_workflow_completed,
                    "completed_at": self.step6_completed_at.isoformat() if self.step6_completed_at else None
                },
                "step7_role": {
                    "completed": self.step7_role_completed,
                    "completed_at": self.step7_completed_at.isoformat() if self.step7_completed_at else None
                }
            },
            "all_completed": self.all_steps_completed,
            "all_completed_at": self.all_completed_at.isoformat() if self.all_completed_at else None,
            "completed_count": self.get_completed_count(),
            "total_steps": 7,
            "completion_percentage": round((self.get_completed_count() / 7) * 100, 1)
        }
    
    def get_completed_count(self) -> int:
        """获取已完成步骤数量"""
        steps = [
            self.step1_auth_completed,
            self.step2_scenario_completed,
            self.step3_template_completed,
            self.step4_entity_completed,
            self.step5_api_completed,
            self.step6_workflow_completed,
            self.step7_role_completed
        ]
        return sum(1 for step in steps if step)
    
    def update_step_completion(self, step_number: int, completed: bool = True, details: Optional[Dict[str, Any]] = None):
        """更新指定步骤的完成状态"""
        from datetime import datetime
        
        current_time = datetime.now() if completed else None
        
        # 更新对应步骤的状态
        if step_number == 1:
            self.step1_auth_completed = completed
            self.step1_completed_at = current_time
        elif step_number == 2:
            self.step2_scenario_completed = completed
            self.step2_completed_at = current_time
        elif step_number == 3:
            self.step3_template_completed = completed
            self.step3_completed_at = current_time
        elif step_number == 4:
            self.step4_entity_completed = completed
            self.step4_completed_at = current_time
        elif step_number == 5:
            self.step5_api_completed = completed
            self.step5_completed_at = current_time
        elif step_number == 6:
            self.step6_workflow_completed = completed
            self.step6_completed_at = current_time
        elif step_number == 7:
            self.step7_role_completed = completed
            self.step7_completed_at = current_time
        
        # 更新详情
        if details:
            try:
                current_details = json.loads(self.completion_details or "{}")
                current_details[f"step{step_number}"] = details
                self.completion_details = json.dumps(current_details)
            except:
                self.completion_details = json.dumps({f"step{step_number}": details})
        
        # 检查是否所有步骤都完成
        self._update_all_completed_status()
    
    def _update_all_completed_status(self):
        """更新整体完成状态"""
        all_completed = all([
            self.step1_auth_completed,
            self.step2_scenario_completed,
            self.step3_template_completed,
            self.step4_entity_completed,
            self.step5_api_completed,
            self.step6_workflow_completed,
            self.step7_role_completed
        ])
        
        if all_completed and not self.all_steps_completed:
            # 首次完成所有步骤
            from datetime import datetime
            self.all_steps_completed = True
            self.all_completed_at = datetime.now()
        elif not all_completed and self.all_steps_completed:
            # 有步骤被取消完成
            self.all_steps_completed = False
            self.all_completed_at = None
    
    def reset_all_steps(self):
        """重置所有步骤状态"""
        self.step1_auth_completed = False
        self.step2_scenario_completed = False
        self.step3_template_completed = False
        self.step4_entity_completed = False
        self.step5_api_completed = False
        self.step6_workflow_completed = False
        self.step7_role_completed = False
        
        self.step1_completed_at = None
        self.step2_completed_at = None
        self.step3_completed_at = None
        self.step4_completed_at = None
        self.step5_completed_at = None
        self.step6_completed_at = None
        self.step7_completed_at = None
        
        self.all_steps_completed = False
        self.all_completed_at = None
        self.completion_details = json.dumps({})
    
    def __repr__(self):
        return f"<ConfigurationStatus(scenario_id='{self.scenario_id}', completed={self.get_completed_count()}/7)>"
