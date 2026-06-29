"""
Help Schema Service
使用 Jinja 模板渲染帮助 AMIS Schema（强依赖场景配置）。
"""
from typing import Dict, Any, Optional, List

from app.services.scenario_service import scenario_service
from app.services.schema_templates import TemplateLoader


def _format_tags(items: List[str]) -> str:
    tag_items = "".join(
        [
            (
                "<span style=\"display:inline-block;padding:6px 10px;"
                "background:#f5f7fa;border:1px solid #e5e7eb;border-radius:8px;"
                "color:#374151;font-size:12px;\">"
                f"{item}</span>"
            )
            for item in items
        ]
    )
    return (
        "<div style=\"display:flex;flex-wrap:wrap;gap:8px;\">"
        f"{tag_items}</div>"
    )


def _extract_api_names(apis: List[Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    seen = set()

    for api in apis or []:
        if not isinstance(api, dict):
            continue
        name = api.get("name") or api.get("description") or api.get("api_id") or api.get("id")
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        names.append(name)

    return names


def _error_schema(message: str) -> Dict[str, Any]:
    return {
        "type": "page",
        "title": "配置缺失",
        "body": {
            "type": "alert",
            "level": "warning",
            "body": message,
            "showIcon": True
        }
    }


def build_help_schema(command: str = "", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """构建帮助 AMIS Schema（强依赖场景配置）"""
    context = context or {}
    scenario_result = scenario_service.get_active_scenario()
    scenario = scenario_result.get("data", {}).get("scenario") if scenario_result.get("success") else None

    if not scenario:
        return _error_schema("未配置活跃场景，无法展示功能说明。请先在场景配置中补全信息。")

    example_instructions = scenario.config.example_instructions or []
    if not example_instructions:
        return _error_schema("场景未配置示例指令，无法生成帮助说明。请在场景配置中补全“示例指令”。")

    scenario_name = scenario.name
    scenario_desc = scenario.description or "—"
    business_domain = scenario.config.business_domain or "—"
    target_users = scenario.config.target_users or []

    target_users_text = "、".join(target_users) if target_users else "未设置"

    accessible_apis = context.get("accessible_apis", [])
    api_names = _extract_api_names(accessible_apis)[:10]
    if not api_names:
        key_features = scenario.config.key_features or []
        api_names = key_features[:10] if key_features else ["暂无可用权限"]

    features_html = _format_tags(api_names)
    example_text = "、".join(example_instructions)

    template_loader = TemplateLoader()
    return template_loader.render(
        "help_page.json.j2",
        scenario_name=scenario_name,
        business_domain=business_domain,
        target_users_text=target_users_text,
        scenario_desc=scenario_desc,
        features_html=features_html,
        example_text=example_text
    )
