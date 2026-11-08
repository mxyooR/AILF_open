"""兼容旧 user_input 节点，为只收集数据的步骤生成可提交的 AMIS 表单。"""
from copy import deepcopy
from .base import NodeStrategy


class UserInputStrategy(NodeStrategy):
    def can_handle(self, node):
        return node.get("type") == "user_input"

    def generate_schema(self, workflow, node, context_data=None, user_instruction="", slot_values=None):
        """优先复用旧 form_schema；未配置表单时从 inputs 创建基本输入控件。"""
        config = node.get("config") or {}
        configured = config.get("form_schema")
        if isinstance(configured, dict) and configured.get("type") == "form":
            form = deepcopy(configured)
        else:
            body = configured.get("body") if isinstance(configured, dict) else configured
            if not isinstance(body, (dict, list)):
                body = []
                for field in node.get("inputs") or []:
                    if not isinstance(field, dict) or not field.get("name"):
                        continue
                    component = {"number": "input-number", "integer": "input-number",
                                 "boolean": "switch", "date": "input-date", "datetime": "input-datetime"}
                    body.append({
                        "type": component.get(field.get("type"), "input-text"),
                        "name": field["name"], "label": field.get("label") or field.get("name"),
                        "required": bool(field.get("required", False)),
                    })
            form = {"type": "form", "body": deepcopy(body)}
        workflow_id = workflow.get("id") or workflow.get("workflow_id")
        # 该步骤只存会话数据，业务接口仍由后续 api_call 节点执行。
        form["api"] = self.build_workflow_api(workflow_id, node["id"], action="submit")
        form["api"]["data"]["&"] = "$$"
        form.setdefault("data", deepcopy(context_data or {}))
        form.setdefault("actions", [
            {"type": "reset", "label": "重置"},
            {"type": "submit", "label": (slot_values or {}).get("submit_button_text") or "下一步", "level": "primary"},
        ])
        return self.build_base_page(workflow, node, form)
