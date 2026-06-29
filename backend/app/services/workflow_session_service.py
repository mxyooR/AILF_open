"""
工作流会话管理服务（Redis 优先 + 内存兜底）
跟踪用户当前在哪个工作流的哪个步骤

说明：
- 优先写入 Redis（支持跨进程/重启保留，按 TTL 过期）
- Redis 不可用时自动回退到内存存储
"""
from app.core.logging_config import get_logger
from typing import Dict, Any, Optional
from datetime import datetime
import json
from app.config import settings

logger = get_logger(__name__)


class WorkflowSession:
    """工作流会话"""
    
    def __init__(self, user_id: str, workflow_id: str, workflow_data: Dict[str, Any]):
        self.user_id = user_id
        self.workflow_id = workflow_id
        self.workflow_data = workflow_data
        self.current_step = "start"
        self.step_data = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = "active"  # active, completed, cancelled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            "workflow_data": self.workflow_data,
            "current_step": self.current_step,
            "step_data": self.step_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowSession':
        session = cls(
            user_id=data["user_id"],
            workflow_id=data["workflow_id"],
            workflow_data=data["workflow_data"]
        )
        session.current_step = data.get("current_step", "start")
        session.step_data = data.get("step_data", {})
        session.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        session.updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        session.status = data.get("status", "active")
        return session


class WorkflowSessionService:
    """工作流会话管理服务（Redis 优先 + 内存兜底）"""
    
    def __init__(self):
        # 内存兜底存储
        self._memory: Dict[str, WorkflowSession] = {}
        self._redis = None
        self._redis_enabled = False
        self._init_redis()
        if self._redis_enabled:
            logger.info("工作流会话服务已初始化(Redis + 内存兜底)")
        else:
            logger.warning("工作流会话服务已初始化(仅内存，Redis 不可用)")

    def _init_redis(self) -> None:
        """初始化 Redis 客户端。"""
        try:
            import redis  # type: ignore

            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            self._redis.ping()
            self._redis_enabled = True
        except Exception as e:
            self._redis = None
            self._redis_enabled = False
            logger.warning(f"Redis 初始化失败，将使用内存会话: {e}")

    def _session_key(self, user_id: str) -> str:
        return f"wf:session:{user_id}"

    def _save_session(self, session: WorkflowSession) -> None:
        """保存会话（Redis 优先，内存兜底）。"""
        # 无论如何都更新内存副本，保证 Redis 抖动时仍可继续
        self._memory[session.user_id] = session

        if not self._redis_enabled or not self._redis:
            return

        try:
            payload = json.dumps(session.to_dict(), ensure_ascii=False, default=str)
            self._redis.setex(
                self._session_key(session.user_id),
                settings.REDIS_SESSION_TTL,
                payload
            )
        except Exception as e:
            logger.warning(f"写入 Redis 会话失败，已回退内存: user={session.user_id}, error={e}")

    def _load_session(self, user_id: str) -> Optional[WorkflowSession]:
        """加载会话（Redis 优先，失败回退内存）。"""
        if self._redis_enabled and self._redis:
            try:
                raw = self._redis.get(self._session_key(user_id))
                if raw:
                    data = json.loads(raw)
                    session = WorkflowSession.from_dict(data)
                    # 同步到内存，减少后续反序列化开销
                    self._memory[user_id] = session
                    return session
            except Exception as e:
                logger.warning(f"读取 Redis 会话失败，回退内存: user={user_id}, error={e}")

        return self._memory.get(user_id)
    
    def create_session(self, user_id: str, workflow_id: str, workflow_data: Dict[str, Any]) -> WorkflowSession:
        """创建新的工作流会话"""
        try:
            # 如果用户已有活跃会话，先结束它
            existing = self.get_active_session(user_id)
            if existing:
                logger.info(f"结束用户 {user_id} 的现有会话: {existing.workflow_id}")
                self.end_session(user_id, "cancelled")
            
            session = WorkflowSession(user_id, workflow_id, workflow_data)
            
            # 存储会话（Redis 优先）
            self._save_session(session)
            
            logger.info(f"✅ 创建工作流会话: user={user_id}, workflow={workflow_id}")
            return session
            
        except Exception as e:
            logger.error(f"❌ 创建工作流会话失败: {str(e)}")
            raise
    
    def get_active_session(self, user_id: str) -> Optional[WorkflowSession]:
        """获取用户的活跃会话"""
        try:
            session = self._load_session(user_id)
            if session and session.status == "active":
                return session
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取活跃会话失败: {str(e)}")
            return None
    
    def update_session_step(self, user_id: str, workflow_id: str, new_step: str, step_data: Dict[str, Any] = None) -> bool:
        """更新会话的当前步骤并累积表单数据"""
        try:
            session = self.get_active_session(user_id)
            if not session or session.workflow_id != workflow_id:
                logger.warning(f"会话不存在: user={user_id}, workflow={workflow_id}")
                return False
            
            old_step = session.current_step
            session.current_step = new_step
            
            # 累积表单数据（关键：使用 update 而不是替换）
            if step_data:
                normalized_step_data = dict(step_data)

                logger.debug(f"Session: 累积表单数据 {list(normalized_step_data.keys())}")
                session.step_data.update(normalized_step_data)
                logger.debug(f"Session: 累积后数据 {list(session.step_data.keys())}")
            
            session.updated_at = datetime.now()
            self._save_session(session)
            
            logger.info(f"Session: 更新步骤 {user_id} {old_step}->{new_step}")
            return True
            
        except Exception as e:
            logger.error(f"Session: 更新步骤失败 {str(e)}")
            return False
    
    def end_session(self, user_id: str, status: str = "completed") -> bool:
        """结束用户的活跃会话"""
        try:
            session = self.get_active_session(user_id)
            if not session:
                return False
            
            session.status = status
            session.updated_at = datetime.now()
            self._save_session(session)
            
            logger.info(f"✅ 结束工作流会话: user={user_id}, status={status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 结束会话失败: {str(e)}")
            return False
    
    def get_current_step_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户当前步骤信息"""
        try:
            session = self.get_active_session(user_id)
            if not session:
                return None
            
            workflow_data = session.workflow_data
            current_step = session.current_step
            
            # 查找当前步骤的节点信息
            nodes = workflow_data.get("nodes", [])
            current_node = None
            
            for node in nodes:
                if node.get("id") == current_step:
                    current_node = node
                    break
            
            return {
                "session": session.to_dict(),
                "current_node": current_node,
                "workflow_name": workflow_data.get("name", "未知工作流"),
                "step_data": session.step_data
            }
            
        except Exception as e:
            logger.error(f"❌ 获取当前步骤信息失败: {str(e)}")
            return None
    
    def get_next_step(self, user_id: str, current_data: Dict[str, Any] = None) -> Optional[str]:
        """获取下一个步骤（支持条件分支）"""
        try:
            session = self.get_active_session(user_id)
            if not session:
                logger.warning(f"用户{user_id}没有活跃的工作流会话")
                return None
            
            workflow_data = session.workflow_data
            current_step = session.current_step
            
            # 查找当前步骤的节点
            nodes = workflow_data.get("nodes", [])
            current_node = None
            
            for node in nodes:
                if node.get("id") == current_step:
                    current_node = node
                    break
            
            if not current_node:
                # 当前节点不存在，可能是动态生成的或是起始节点
                logger.info(f"节点{current_step}未预定义，返回下一个逻辑步骤")
                # 简单逻辑：按 nodes 顺序找下一个
                for i, node in enumerate(nodes):
                    if i > 0:  # 跳过 start
                        return node.get("id", "end")
                return "end"
            
            logger.debug(f"当前节点: {current_node.get('name')} ({current_node.get('id')})")
            
            # 获取子节点（优先使用 child_nodes，它支持条件分支）
            child_nodes = current_node.get("child_nodes", [])
            
            if child_nodes:
                logger.debug(f"发现{len(child_nodes)}个子节点，开始评估条件")
                # 有条件分支，需要评估每个条件
                for i, child in enumerate(child_nodes):
                    condition = child.get("condition")
                    target_node_id = child.get("node_id")
                    
                    logger.debug(f"  分支{i+1}: 目标节点={target_node_id}, 条件={condition}")
                    
                    # 评估条件
                    if self._evaluate_condition(condition, current_data, session.step_data):
                        logger.info(f"  ✅ 条件满足，选择节点: {target_node_id}")
                        return target_node_id if target_node_id else "end"
                    else:
                        logger.info(f"  ❌ 条件不满足")
                
                # 如果没有条件满足，返回第一个无条件分支或结束
                for child in child_nodes:
                    if not child.get("condition"):
                        logger.info(f"  ⚠️ 使用默认分支: {child.get('node_id')}")
                        return child.get("node_id", "end")
                
                logger.warning("⚠️ 所有条件都不满足且无默认分支，工作流结束")
                return "end"
            
            # 没有 child_nodes，尝试使用 nextSteps（简单的线性流程）
            next_steps = current_node.get("nextSteps", [])
            if next_steps:
                logger.info(f"📊 使用 nextSteps，下一步: {next_steps[0]}")
                return next_steps[0] if next_steps else "end"
            
            # 没有任何下一步定义
            logger.info("📊 节点没有定义下一步，工作流结束")
            return "end"
            
        except Exception as e:
            logger.error(f"❌ 获取下一步骤失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None


    def _evaluate_condition(self, condition: Optional[Dict[str, Any]], current_data: Dict[str, Any], accumulated_data: Dict[str, Any]) -> bool:
        """评估条件表达式（安全版本）
        
        Args:
            condition: 条件定义，支持以下格式：
                - {"type": "always"} - 总是满足
                - {"type": "never"} - 永不满足
                - {"type": "expression", "expression": "field == value"} - 表达式条件
                - {"field": "age", "operator": ">", "value": 18} - 字段比较
            current_data: 当前步骤提交的数据
            accumulated_data: 累积的所有步骤数据
        
        Returns:
            bool: 条件是否满足
        
        安全特性：
            - 数值转换失败时返回 False 并记录警告
            - 缺失字段时优雅处理
            - 所有异常都被捕获并返回 False
        """
        try:
            # 如果没有条件，默认为 True（无条件分支）
            if not condition:
                return True
            
            # 合并数据源（当前数据优先）
            current_data = current_data or {}
            accumulated_data = accumulated_data or {}
            all_data = {**accumulated_data, **current_data}
            
            # 支持 type 字段的简化条件格式
            condition_type = condition.get("type")
            if condition_type:
                if condition_type == "always":
                    logger.info(f"  ✅ 条件类型为 'always'，直接满足")
                    return True
                elif condition_type == "never":
                    logger.info(f"  ❌ 条件类型为 'never'，直接不满足")
                    return False
                elif condition_type == "expression":
                    # 🔥 处理 expression 类型条件
                    expression = condition.get("expression", "")
                    if not expression:
                        logger.warning(f"⚠️ expression 条件缺少 expression 字段: {condition}")
                        return False
                    return self._evaluate_expression(expression, all_data)
            
            # 获取条件字段
            field = condition.get("field")
            operator = condition.get("operator")
            expected_value = condition.get("value")
            
            # 如果没有 field 和 operator，条件定义不完整
            if not field and not operator:
                logger.warning(f"⚠️ 条件定义不完整 (无 field/operator): {condition}")
                return False
            
            # 获取实际值（安全处理缺失字段）
            actual_value = all_data.get(field)
            
            logger.info(f"  📝 条件评估: {field} {operator} {expected_value}, 实际值: {actual_value}")
            
            # 评估不同的操作符
            if operator == "==":
                return actual_value == expected_value
            elif operator == "!=":
                return actual_value != expected_value
            elif operator in (">", "<", ">=", "<="):
                # 安全的数值比较
                return self._safe_numeric_compare(field, actual_value, operator, expected_value)
            elif operator == "in":
                # 安全处理：如果 expected_value 不是可迭代对象，返回 False
                if expected_value is None:
                    return False
                try:
                    return actual_value in expected_value
                except TypeError:
                    logger.warning(f"⚠️ 'in' 操作符的 expected_value 不可迭代: {expected_value}")
                    return False
            elif operator == "not_in":
                if expected_value is None:
                    return True
                try:
                    return actual_value not in expected_value
                except TypeError:
                    logger.warning(f"⚠️ 'not_in' 操作符的 expected_value 不可迭代: {expected_value}")
                    return True
            elif operator == "contains":
                # 安全处理：如果 actual_value 为 None，返回 False
                if actual_value is None:
                    return False
                return expected_value in str(actual_value)
            elif operator == "exists":
                return field in all_data
            elif operator == "not_exists":
                return field not in all_data
            elif operator == "is_empty":
                return not actual_value or actual_value == "" or actual_value == []
            elif operator == "is_not_empty":
                return actual_value and actual_value != "" and actual_value != []
            else:
                logger.warning(f"⚠️ 不支持的操作符: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 条件评估失败: {str(e)}")
            logger.error(f"   条件: {condition}")
            logger.error(f"   当前数据: {current_data}")
            logger.error(f"   累积数据: {accumulated_data}")
            return False
    
    def _safe_numeric_compare(self, field: str, actual_value: Any, operator: str, expected_value: Any) -> bool:
        """
        安全的数值比较
        
        Args:
            field: 字段名（用于日志）
            actual_value: 实际值
            operator: 比较操作符 (>, <, >=, <=)
            expected_value: 期望值
        
        Returns:
            bool: 比较结果，转换失败时返回 False
        """
        try:
            # 处理 None 值
            if actual_value is None:
                logger.warning(f"⚠️ 数值比较失败: field={field} 的值为 None")
                return False
            
            # 尝试转换为浮点数
            try:
                actual_num = float(actual_value)
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"⚠️ 数值转换失败: field={field}, actual_value={actual_value!r}, "
                    f"type={type(actual_value).__name__}, error={e}"
                )
                return False
            
            try:
                expected_num = float(expected_value)
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"⚠️ 数值转换失败: expected_value={expected_value!r}, "
                    f"type={type(expected_value).__name__}, error={e}"
                )
                return False
            
            # 执行比较
            if operator == ">":
                return actual_num > expected_num
            elif operator == "<":
                return actual_num < expected_num
            elif operator == ">=":
                return actual_num >= expected_num
            elif operator == "<=":
                return actual_num <= expected_num
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ 数值比较异常: {str(e)}")
            return False

    def _evaluate_expression(self, expression: str, data: Dict[str, Any]) -> bool:
        """
        评估表达式条件（安全版本）
        
        支持的表达式格式：
        - "field == value"
        - "field != value"
        - "field == true" / "field == false"
        - "field > 100"
        - "field < 100"
        - "field >= 100"
        - "field <= 100"
        
        Args:
            expression: 表达式字符串，如 "confirm_refund == true"
            data: 数据字典
        
        Returns:
            bool: 表达式是否为真
        """
        import re
        
        try:
            logger.debug(f"  评估表达式: {expression}")
            logger.debug(f"  可用数据: {list(data.keys())}")
            
            # 解析表达式：支持 ==, !=, >, <, >=, <=
            # 匹配模式：field operator value
            pattern = r'^\s*(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+?)\s*$'
            match = re.match(pattern, expression)
            
            if not match:
                logger.warning(f"⚠️ 无法解析表达式: {expression}")
                return False
            
            field = match.group(1)
            operator = match.group(2)
            expected_str = match.group(3).strip()
            
            # 获取实际值
            actual_value = data.get(field)
            
            logger.debug(f"  字段={field}, 操作符={operator}, 期望值={expected_str}, 实际值={actual_value}")
            
            # 解析期望值
            expected_value = self._parse_expression_value(expected_str)
            
            # 如果实际值不存在，尝试从 api_response.data 中读取（兼容常见API返回结构）
            if actual_value is None:
                api_response = data.get("api_response")
                if isinstance(api_response, dict):
                    api_data = api_response.get("data")
                    if isinstance(api_data, dict) and field in api_data:
                        actual_value = api_data.get(field)
                        logger.debug(f"  字段{field}来自api_response.data: {actual_value}")

            # 如果实际值仍不存在，条件不满足
            if actual_value is None:
                logger.debug(f"  字段{field}不存在于数据中，条件不满足")
                return False
            
            # 执行比较
            result = self._compare_values(actual_value, operator, expected_value)
            logger.debug(f"  {'✅' if result else '❌'} 表达式结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 表达式评估失败: {expression}, 错误={str(e)}")
            return False
    
    def _parse_expression_value(self, value_str: str) -> Any:
        """
        解析表达式中的值
        
        Args:
            value_str: 值字符串
        
        Returns:
            解析后的值（bool, int, float, str, None）
        """
        # 去除引号
        value_str = value_str.strip().strip('"').strip("'")
        
        # null 值
        if value_str.lower() == 'null' or value_str.lower() == 'none':
            return None
        
        # 布尔值
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # 数字
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        # 字符串
        return value_str
    
    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """
        比较两个值
        
        Args:
            actual: 实际值
            operator: 操作符
            expected: 期望值
        
        Returns:
            比较结果
        """
        try:
            # 类型转换：如果期望值是布尔，尝试将实际值转为布尔
            if isinstance(expected, bool):
                if isinstance(actual, str):
                    actual = actual.lower() in ('true', '1', 'yes')
                elif isinstance(actual, (int, float)):
                    actual = bool(actual)
            
            # 类型转换：如果期望值是数字，尝试将实际值转为数字
            elif isinstance(expected, (int, float)) and isinstance(actual, str):
                try:
                    actual = float(actual) if '.' in actual else int(actual)
                except ValueError:
                    pass
            
            # 执行比较
            if operator == '==':
                return actual == expected
            elif operator == '!=':
                return actual != expected
            elif operator == '>':
                return float(actual) > float(expected)
            elif operator == '<':
                return float(actual) < float(expected)
            elif operator == '>=':
                return float(actual) >= float(expected)
            elif operator == '<=':
                return float(actual) <= float(expected)
            else:
                logger.warning(f"⚠️ 不支持的操作符: {operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ 值比较失败: actual={actual}, operator={operator}, expected={expected}, error={e}")
            return False


# 创建全局实例
workflow_session_service = WorkflowSessionService()
