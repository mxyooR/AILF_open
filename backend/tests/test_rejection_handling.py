"""
测试拒绝样本的后端处理逻辑

验证：
1. AI 输出 "REJECT" 时，后端直接生成拒绝 AMIS Schema
2. 拒绝 Schema 包含可用操作建议
3. 不再让 AI 生成完整的拒绝 AMIS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.core.ai.pure_llm_model_service import pure_llm_model_service


async def test_reject_handling():
    """测试拒绝处理逻辑"""
    print("=" * 80)
    print("测试拒绝样本的后端处理逻辑")
    print("=" * 80)
    
    # 模拟候选资源
    candidate_apis = [
        {
            "api_id": "api_order_list",
            "endpoint": "/api/shop/orders",
            "method": "GET",
            "description": "查询订单列表",
            "desc": "查询订单列表"
        },
        {
            "api_id": "api_product_search",
            "endpoint": "/api/shop/search",
            "method": "GET",
            "description": "搜索商品",
            "desc": "搜索商品"
        }
    ]
    
    candidate_workflows = [
        {
            "workflow_id": "workflow_checkout",
            "name": "完整购物流程",
            "description": "从购物车到支付的完整流程",
            "nodes": []
        }
    ]
    
    # 测试用例 1：无关指令（应该输出 REJECT）
    print("\n" + "=" * 80)
    print("测试用例 1: 无关指令 - '今天天气怎么样'")
    print("=" * 80)
    
    result = await pure_llm_model_service.generate_two_round_async(
        user_instruction="今天天气怎么样",
        candidate_apis=candidate_apis,
        candidate_workflows=candidate_workflows,
        domain="ecommerce",
        validate_endpoints=False
    )
    
    print(f"\n✅ 结果:")
    print(f"   - valid: {result.get('valid')}")
    print(f"   - selection type: {result.get('selection', {}).get('type')}")
    
    if result.get('validated_json'):
        schema = result['validated_json']
        print(f"   - schema type: {schema.get('type')}")
        print(f"   - schema title: {schema.get('title')}")
        if schema.get('body'):
            print(f"   - body type: {schema['body'].get('type')}")
            print(f"   - body level: {schema['body'].get('level')}")
            body_text = schema['body'].get('body', '')
            print(f"   - body message (前100字符): {body_text[:100]}...")
            
            # 检查是否包含可用操作建议
            if "您可以尝试以下操作" in body_text:
                print(f"   ✅ 包含可用操作建议")
            else:
                print(f"   ⚠️ 未包含可用操作建议")
    
    # 测试用例 2：领域不匹配的指令
    print("\n" + "=" * 80)
    print("测试用例 2: 领域不匹配 - '预约挂号'（医疗领域指令，但候选是电商）")
    print("=" * 80)
    
    result2 = await pure_llm_model_service.generate_two_round_async(
        user_instruction="预约挂号",
        candidate_apis=candidate_apis,
        candidate_workflows=candidate_workflows,
        domain="ecommerce",
        validate_endpoints=False
    )
    
    print(f"\n✅ 结果:")
    print(f"   - valid: {result2.get('valid')}")
    print(f"   - selection type: {result2.get('selection', {}).get('type')}")
    
    if result2.get('validated_json'):
        schema = result2['validated_json']
        print(f"   - schema type: {schema.get('type')}")
        print(f"   - schema title: {schema.get('title')}")
        if schema.get('body'):
            body_text = schema['body'].get('body', '')
            print(f"   - body message (前100字符): {body_text[:100]}...")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


async def test_reject_schema_format():
    """测试拒绝 Schema 的格式"""
    print("\n" + "=" * 80)
    print("测试拒绝 Schema 格式")
    print("=" * 80)
    
    # 测试不带可用操作
    schema1 = pure_llm_model_service._create_rejection_schema("今天天气怎么样")
    print("\n不带可用操作:")
    print(f"   - title: {schema1.get('title')}")
    print(f"   - body.level: {schema1.get('body', {}).get('level')}")
    print(f"   - body.body: {schema1.get('body', {}).get('body')}")
    
    # 测试带可用操作
    available_actions = ["查询订单列表", "搜索商品", "完整购物流程"]
    schema2 = pure_llm_model_service._create_rejection_schema(
        "今天天气怎么样",
        available_actions=available_actions
    )
    print("\n带可用操作:")
    print(f"   - title: {schema2.get('title')}")
    print(f"   - body.level: {schema2.get('body', {}).get('level')}")
    body_text = schema2.get('body', {}).get('body', '')
    print(f"   - body.body (前200字符): {body_text[:200]}...")
    
    # 验证格式
    assert schema2.get('type') == 'page', "Schema type 应该是 'page'"
    assert schema2.get('title') == '无法处理', "Title 应该是 '无法处理'"
    assert schema2.get('body', {}).get('type') == 'alert', "Body type 应该是 'alert'"
    assert schema2.get('body', {}).get('level') == 'warning', "Level 应该是 'warning'"
    assert '您可以尝试以下操作' in body_text, "应该包含可用操作建议"
    assert '查询订单列表' in body_text, "应该包含第一个可用操作"
    
    print("\n✅ 所有格式验证通过")


if __name__ == "__main__":
    # 检查模型是否加载
    if not pure_llm_model_service.is_loaded:
        print("⚠️ LLM 模型未加载，跳过需要模型的测试")
        print("\n只测试 Schema 格式...")
        asyncio.run(test_reject_schema_format())
    else:
        print("✅ LLM 模型已加载，运行完整测试")
        asyncio.run(test_reject_handling())
        asyncio.run(test_reject_schema_format())
