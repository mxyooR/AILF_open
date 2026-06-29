"""
场景管理数据库模型
使用MySQL数据库存储
"""
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session

from app.core.database import Base, get_db_session
from app.schemas.scenario import Scenario, ScenarioType, ScenarioStatus, ScenarioConfig


class ScenarioDBModel(Base):
    """场景数据库表模型"""
    __tablename__ = "scenarios"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    type = Column(Enum(ScenarioType), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ScenarioStatus), nullable=False, default=ScenarioStatus.ACTIVE)
    template_key = Column(String(100), nullable=True)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def to_schema(self) -> Scenario:
        """转换为Pydantic模型"""
        # 处理空的配置，提供默认值
        config_data = self.config or {}
        if not config_data or not all(key in config_data for key in ['business_domain', 'target_users', 'key_features', 'example_instructions']):
            config_data = {
                'business_domain': config_data.get('business_domain', ''),
                'target_users': config_data.get('target_users', []),
                'key_features': config_data.get('key_features', []),
                'example_instructions': config_data.get('example_instructions', []),
                'custom_settings': config_data.get('custom_settings', {})
            }

        return Scenario(
            id=self.id,
            name=self.name,
            type=self.type,
            description=self.description or "",
            status=self.status,
            template_key=self.template_key,
            config=ScenarioConfig(**config_data),
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat()
        )


class ScenarioModel:
    """场景数据操作类"""
    
    def _generate_scenario_id(self) -> str:
        """生成场景ID"""
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        return f"scenario_{timestamp}"

    def get_active_scenario(self) -> Optional[Scenario]:
        """获取当前活跃的场景"""
        with get_db_session() as db:
            scenario_db = db.query(ScenarioDBModel).filter(
                ScenarioDBModel.status == ScenarioStatus.ACTIVE
            ).first()

            if scenario_db:
                return scenario_db.to_schema()
            return None
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """根据ID获取场景"""
        with get_db_session() as db:
            scenario_db = db.query(ScenarioDBModel).filter(
                ScenarioDBModel.id == scenario_id
            ).first()

            if scenario_db:
                return scenario_db.to_schema()
            return None
    
    def create_scenario(self, scenario_data: Dict[str, Any]) -> Scenario:
        """创建新场景"""
        with get_db_session() as db:
            # 生成场景ID
            scenario_id = self._generate_scenario_id()
            current_time = datetime.now(timezone.utc)

            # 如果创建新的活跃场景，将其他场景设为非活跃
            status = ScenarioStatus(scenario_data.get('status', ScenarioStatus.ACTIVE.value))
            if status == ScenarioStatus.ACTIVE:
                db.query(ScenarioDBModel).filter(
                    ScenarioDBModel.status == ScenarioStatus.ACTIVE
                ).update({
                    ScenarioDBModel.status: ScenarioStatus.INACTIVE,
                    ScenarioDBModel.updated_at: current_time
                })

            # 创建新场景
            new_scenario = ScenarioDBModel(
                id=scenario_id,
                name=scenario_data['name'],
                type=ScenarioType(scenario_data['type']),
                description=scenario_data.get('description', ''),
                status=status,
                template_key=scenario_data.get('template_key'),
                config=scenario_data['config'],
                created_at=current_time,
                updated_at=current_time
            )

            db.add(new_scenario)
            db.flush()  # 确保数据被写入，但不提交事务

            return new_scenario.to_schema()
    
    def update_scenario(self, scenario_id: str, update_data: Dict[str, Any]) -> Optional[Scenario]:
        """更新场景"""
        with get_db_session() as db:
            scenario_db = db.query(ScenarioDBModel).filter(
                ScenarioDBModel.id == scenario_id
            ).first()

            if not scenario_db:
                return None

            current_time = datetime.now(timezone.utc)

            # 更新字段
            if 'name' in update_data:
                scenario_db.name = update_data['name']
            if 'type' in update_data:
                scenario_db.type = ScenarioType(update_data['type'])
            if 'description' in update_data:
                scenario_db.description = update_data['description']
            if 'config' in update_data:
                scenario_db.config = update_data['config']
            if 'status' in update_data:
                new_status = ScenarioStatus(update_data['status'])
                # 如果设为活跃状态，将其他场景设为非活跃
                if new_status == ScenarioStatus.ACTIVE:
                    db.query(ScenarioDBModel).filter(
                        ScenarioDBModel.id != scenario_id,
                        ScenarioDBModel.status == ScenarioStatus.ACTIVE
                    ).update({
                        ScenarioDBModel.status: ScenarioStatus.INACTIVE,
                        ScenarioDBModel.updated_at: current_time
                    })
                scenario_db.status = new_status

            scenario_db.updated_at = current_time
            db.flush()

            return scenario_db.to_schema()
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """删除场景"""
        with get_db_session() as db:
            scenario_db = db.query(ScenarioDBModel).filter(
                ScenarioDBModel.id == scenario_id
            ).first()

            if scenario_db:
                db.delete(scenario_db)
                return True
            return False

    def list_scenarios(self, status: Optional[ScenarioStatus] = None) -> List[Scenario]:
        """列出场景"""
        with get_db_session() as db:
            query = db.query(ScenarioDBModel)

            if status:
                query = query.filter(ScenarioDBModel.status == status)

            scenarios_db = query.all()
            return [scenario.to_schema() for scenario in scenarios_db]

    def scenario_exists_by_name(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """检查场景名称是否已存在"""
        with get_db_session() as db:
            query = db.query(ScenarioDBModel).filter(ScenarioDBModel.name == name)

            if exclude_id:
                query = query.filter(ScenarioDBModel.id != exclude_id)

            return query.first() is not None


# 全局场景模型实例
scenario_model = ScenarioModel()
