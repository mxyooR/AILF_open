"""
测试两轮对话的 Slot-Filling 架构

验证：
1. 第一轮：AI 选择 API/Workflow
2. 第二轮：AI 输出槽位值 JSON（不是完整 AMIS）
3. 规则生成器生成最终的 AMIS Schema
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.core.ai.pure_llm_model_service import pure_llm_model_service


async def test_api_selection():
    """测试 API 选择的两轮对话"""
    print("=" * 80)
    print("测试 API 选择的两轮对话（Slot-Filling）")
    print("=" * 80)
    
    # 模拟候选资源
    candidate_apis = [
        {
            "api_id": "api_order_list",
            "endpoint": "/api/shop/orders",
            "method": "GET",
            "description": "查询订单列表",
            "desc": "查询订单列表",
            "request": [
                {"name": "status", "type": "string", "label": "订单状态"},
                {"name": "date_from", "type": "date", "label": "开始日期"}
            ]
        }
    ]
    
    candidate_workflows = []
    
    print("\n测试用例: '查询订单'")
    print("-" * 80)
    
    result = await pure_llm_model_service.generate_two_round_async(
        user_instruction="查询订单",
        candidate_apis=candidate_apis,
        candidate_workflows=candidate_workflows,
        domain="ecommerce",
        validate_endpoints=False
    )
    
    print(f"\n✅ 结果:")
    print(f"   - valid: {result.get('valid')}")
    print(f"   - selection type: {result.get('selection', {}).get('type')}")
    print(f"   - selection name: {result.get('selection', {}).get('name')}")
    
    if result.get('slot_values'):
        print(f"\n✅ 槽位值:")
        for key, value in result['slot_values'].items():
            print(f"   - {key}: {value}")
    
    if result.get('validated_json'):
        schema = result['validated_json']
        print(f"\n✅ 最终 AMIS Schema:")
        print(f"   - type: {schema.get('type')}")
        print(f"   - title: {schema.get('title')}")
        if schema.get('body'):
            print(f"   - body.type: {schema['body'].get('type')}")
            if schema['body'].get('type') == 'form':
                print(f"   - body.api.url: {schema['body'].get('api', {}).get('url')}")


async def test_workflow_selection():
    """测试 Workflow 选择的两轮对话"""
    print("\n" + "=" * 80)
    print("测试 Workflow 选择的两轮对话（Slot-Filling）")
    print("=" * 80)
    
    # 模拟候选资源
    candidate_apis = []
    
    candidate_workflows = [
        {
            "workflow_id": "workflow_checkout",
            "name": "完整购物流程",
            "description": "从购物车到支付的完整流程",
            "nodes": [
                {
                    "id": "node_1",
                    "type": "api_call",
                    "name": "查看购物车",
                    "config": {
                        "parameters": {
                            "user_id": "${user_id}",
                            "cart_id": "${cart_id}"
                        }
                    }
                }
            ]
        }
    ]
    
    print("\n测试用例: '我要购物'")
    print("-" * 80)
    
    result = await pure_llm_model_service.generate_two_round_async(
        user_instruction="我要购物",
        candidate_apis=candidate_apis,
        candidate_workflows=candidate_workflows,
        domain="ecommerce",
        validate_endpoints=False
    )
    
    print(f"\n✅ 结果:")
    print(f"   - valid: {result.get('valid')}")
    print(f"   - selection type: {result.get('selection', {}).get('type')}")
    print(f"   - selection name: {result.get('selection', {}).get('name')}")
    
    if result.get('slot_values'):
        print(f"\n✅ 槽位值:")
        for key, value in result['slot_values'].items():
            print(f"   - {key}: {value}")
    
    if result.get('validated_json'):
        schema = result['validated_json']
        print(f"\n✅ 最终 AMIS Schema:")
        print(f"   - type: {schema.get('type')}")
        print(f"   - title: {schema.get('title')}")
        if schema.get('body'):
            print(f"   - body.type: {schema['body'].get('type')}")


async def test_slot_values_format():
    """测试槽位值格式"""
    print("\n" + "=" * 80)
    print("测试槽位值格式")
    print("=" * 80)
    
    # 测试默认槽位值生成
    slots = ["page_title", "user_message", "submit_button_text", "field_label_order_id"]
    selected_item = {
        "name": "查询订单列表",
        "description": "查询订单列表"
    }
    
    default_values = pure_llm_model_service._get_default_slot_values(
        slots, selected_item, "API"
    )
    
    print("\n默认槽位值:")
    for key, value in default_values.items():
        print(f"   - {key}: {value}")
    
    # 验证格式
    assert "page_title" in default_values, "应该包含 page_title"
    assert "user_message" in default_values, "应该包含 user_message"
    assert "submit_button_text" in default_values, "应该包含 submit_button_text"
    assert "field_label_order_id" in default_values, "应该包含 field_label_order_id"
    
    print("\n✅ 所有格式验证通过")


if __name__ == "__main__":
    # 检查模型是否加载
    if not pure_llm_model_service.is_loaded:
        print("⚠️ LLM 模型未加载，只测试格式")
        asyncio.run(test_slot_values_format())
    else:
        print("✅ LLM 模型已加载，运行完整测试")
        asyncio.run(test_api_selection())
        asyncio.run(test_workflow_selection())
        asyncio.run(test_slot_values_format())
