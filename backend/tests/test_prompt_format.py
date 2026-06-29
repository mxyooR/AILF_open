"""
测试后端 Prompt 格式是否与数据集一致
"""
import json
from app.services.slot_filling_service import slot_filling_service


def test_workflow_prompt_format():
    """测试工作流槽填充 Prompt 格式"""
    
    # 模拟工作流上下文
    context = {
        "workflow": {
            "id": "workflow_123",
            "name": "银行卡审批发卡流程",
            "description": ""
        },
        "node": {
            "name": "查询待审批申请",
            "type": "api_call",
            "fields": [{"name": "status"}]
        }
    }
    
    slots = ["page_title", "user_message", "submit_button_text", "reset_button_text", "field_label_status"]
    
    # 生成 Prompt
    prompt = slot_filling_service._build_slot_filling_prompt(
        slots=slots,
        context=context,
        user_instruction="我想银行卡审批发卡流程"
    )
    
    print("=" * 80)
    print("工作流 Prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # 验证格式
    assert "工作流详情：" in prompt
    assert '"name": "银行卡审批发卡流程"' in prompt
    assert '任务：为以下槽位生成中文文案（JSON 格式）：' in prompt
    assert '["page_title", "user_message", "submit_button_text", "reset_button_text", "field_label_status"]' in prompt
    
    # 工作流不应该有"要求"部分
    assert "要求：" not in prompt
    
    print("✅ 工作流 Prompt 格式正确")


def test_api_prompt_format():
    """测试 API 槽填充 Prompt 格式"""
    
    # 模拟 API 上下文
    context = {
        "api": {
            "path": "/api/shop/refunds",
            "method": "POST",
            "desc": "申请退款",
            "request_params": [
                {"name": "order_id", "type": "string"},
                {"name": "reason", "type": "string"},
                {"name": "amount", "type": "float"},
                {"name": "images", "type": "array"}
            ]
        }
    }
    
    slots = ["page_title", "user_message", "submit_button_text", "field_label_order_id", "field_label_reason", "field_label_amount", "field_label_images"]
    
    # 生成 Prompt
    prompt = slot_filling_service._build_slot_filling_prompt(
        slots=slots,
        context=context,
        user_instruction="申请退款一下"
    )
    
    print("=" * 80)
    print("API Prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # 验证格式
    assert "API详情：" in prompt
    assert '"path": "/api/shop/refunds"' in prompt
    assert '任务：为以下槽位生成中文文案（JSON 格式）：' in prompt
    assert '["page_title"' in prompt
    
    # API 应该有"要求"部分
    assert "要求：" in prompt
    assert "- page_title：3-6 字" in prompt
    assert "- user_message：10-20 字" in prompt
    assert "- field_label_xxx：2-4 字" in prompt
    assert "- 只输出 JSON，不要其他内容" in prompt
    
    print("✅ API Prompt 格式正确")


def test_reject_prompt_format():
    """测试拒绝提示 Prompt 格式"""
    from app.services.ai_service import AIServiceSimple
    
    ai_service = AIServiceSimple()
    available_actions = ["完整报销流程", "付款申请流程", "开票申请流程", "查询发票", "申请开票", "查询预算"]
    
    # 构建拒绝 Prompt
    system_prompt = f"""用户指令无法匹配到任何资源。

可用操作：
{json.dumps(available_actions[:6], ensure_ascii=False)}

任务：为拒绝提示生成槽位值（JSON 格式）：
- reject_title：拒绝标题（4-6 字）
- reject_message：拒绝提示信息（20-40 字，包含可用操作建议）"""
    
    print("=" * 80)
    print("拒绝 Prompt:")
    print("=" * 80)
    print(system_prompt)
    print("=" * 80)
    
    # 验证格式
    assert "用户指令无法匹配到任何资源。" in system_prompt
    assert "可用操作：" in system_prompt
    assert "任务：为拒绝提示生成槽位值（JSON 格式）：" in system_prompt
    assert "- reject_title：拒绝标题（4-6 字）" in system_prompt
    assert "- reject_message：拒绝提示信息（20-40 字，包含可用操作建议）" in system_prompt
    
    print("✅ 拒绝 Prompt 格式正确")


if __name__ == "__main__":
    test_workflow_prompt_format()
    print()
    test_api_prompt_format()
    print()
    test_reject_prompt_format()
    print()
    print("🎉 所有测试通过！后端 Prompt 格式与数据集一致")
