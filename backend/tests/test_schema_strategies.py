"""
测试 Schema 生成策略

测试所有节点类型和展示方式
"""
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.amis_schema_generator import amis_schema_generator


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(test_name, schema):
    """打印测试结果"""
    print(f"\n✅ {test_name}")
    print(f"Schema 类型: {schema.get('type')}")
    if 'body' in schema:
        body = schema['body']
        if isinstance(body, dict):
            print(f"Body 类型: {body.get('type')}")
        elif isinstance(body, list):
            print(f"Body 组件数: {len(body)}")
    print(f"JSON 长度: {len(json.dumps(schema))} 字符")


def test_workflow_entry():
    """测试工作流入口表单"""
    print_section("测试 1: 工作流入口表单")
    
    workflow = {
        "id": "workflow_test",
        "name": "测试工作流"
    }
    
    first_node = {
        "id": "node_1",
        "type": "api_call",
        "description": "填写订单信息",
        "config": {
            "parameters": {
                "order_id": "${order_id}",
                "customer_name": "${customer_name}"
            }
        },
        "ai_instructions": {
            "user_message": "请填写订单信息"
        }
    }
    
    schema = amis_schema_generator.generate_workflow_entry_form(
        workflow=workflow,
        first_node=first_node
    )
    
    print_result("工作流入口表单", schema)
    assert schema["type"] == "page"
    assert schema["workflow_id"] == "workflow_test"
    assert schema["current_node_id"] == "node_1"


def test_start_node():
    """测试 Start 节点"""
    print_section("测试 2: Start 节点")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {"id": "start", "type": "start"}
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("Start 节点", schema)
    assert schema["type"] == "page"
    assert "正在启动" in schema["body"]["body"]


def test_end_node():
    """测试 End 节点"""
    print_section("测试 3: End 节点")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "end",
        "type": "end",
        "ai_instructions": {
            "action": "订单已成功创建"
        }
    }
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("End 节点", schema)
    assert schema["type"] == "page"
    assert schema["body"]["type"] == "result"
    assert schema["body"]["status"] == "success"


def test_condition_node():
    """测试 Condition 节点"""
    print_section("测试 4: Condition 节点")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {"id": "cond_1", "type": "condition"}
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("Condition 节点", schema)
    assert schema["type"] == "page"
    assert "处理中" in schema["body"]["body"]


def test_notification_node():
    """测试 Notification 节点"""
    print_section("测试 5: Notification 节点")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "notif_1",
        "type": "notification",
        "config": {
            "message_template": "您的订单 ${order_id} 已提交"
        }
    }
    
    context_data = {"order_id": "ORD123456"}
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node,
        context_data=context_data
    )
    
    print_result("Notification 节点", schema)
    assert schema["type"] == "page"
    assert "ORD123456" in schema["body"][0]["body"]


def test_api_call_get_table():
    """测试 API Call GET - Table 展示"""
    print_section("测试 6: API Call GET - Table 展示")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "api_1",
        "type": "api_call",
        "description": "查询订单列表",  # 包含"列表"关键词
        "config": {
            "method": "GET",
            "api_endpoint": "/api/orders"
        },
        "outputs": [
            {
                "name": "orders",
                "type": "array",
                "items": {
                    "properties": {
                        "order_id": {"type": "string", "description": "订单号"},
                        "status": {"type": "string", "description": "状态"}
                    }
                }
            }
        ]
    }
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("API Call GET - Table", schema)
    assert schema["type"] == "page"
    # 检查是否包含 table 组件
    body_str = json.dumps(schema["body"])
    assert "table" in body_str


def test_api_call_get_cards():
    """测试 API Call GET - Cards 展示"""
    print_section("测试 7: API Call GET - Cards 展示")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "api_2",
        "type": "api_call",
        "description": "查询商品卡片",  # 包含"卡片"关键词
        "config": {
            "method": "GET",
            "api_endpoint": "/api/products",
            "display_type": "cards"  # 显式指定
        },
        "outputs": [
            {
                "name": "products",
                "type": "array",
                "items": {
                    "properties": {
                        "id": {"type": "string", "description": "商品ID"},
                        "name": {"type": "string", "description": "商品名称"},
                        "price": {"type": "number", "description": "价格"}
                    }
                }
            }
        ]
    }
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("API Call GET - Cards", schema)
    assert schema["type"] == "page"
    # 检查是否包含 cards 组件
    body_str = json.dumps(schema["body"])
    assert "cards" in body_str


def test_api_call_get_service():
    """测试 API Call GET - Service 展示（默认）"""
    print_section("测试 8: API Call GET - Service 展示")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "api_3",
        "type": "api_call",
        "description": "查询用户信息",
        "config": {
            "method": "GET",
            "api_endpoint": "/api/user/info"
        },
        "outputs": [
            {"name": "name", "type": "string", "description": "姓名"},
            {"name": "email", "type": "string", "description": "邮箱"}
        ]
    }
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("API Call GET - Service", schema)
    assert schema["type"] == "page"
    # 检查是否包含 service 组件
    body_str = json.dumps(schema["body"])
    assert "service" in body_str


def test_api_call_post():
    """测试 API Call POST - Form 提交"""
    print_section("测试 9: API Call POST - Form 提交")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "api_4",
        "type": "api_call",
        "description": "提交订单",
        "config": {
            "method": "POST",
            "api_endpoint": "/api/orders",
            "parameters": {
                "product_id": "${product_id}",
                "quantity": "${quantity}"
            }
        }
    }
    
    context_data = {"product_id": "PROD123"}  # 已有上下文
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node,
        context_data=context_data
    )
    
    print_result("API Call POST - Form", schema)
    assert schema["type"] == "page"
    # 检查是否包含 form 组件
    body_str = json.dumps(schema["body"])
    assert "form" in body_str
    # 检查是否有隐藏字段（product_id 在上下文中）
    assert "hidden" in body_str


def test_chart_node():
    """测试 Chart 节点"""
    print_section("测试 10: Chart 节点")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "chart_1",
        "type": "api_call",
        "description": "销售统计分析",  # 包含"统计"关键词
        "config": {
            "method": "GET",
            "api_endpoint": "/api/stats/sales"
        },
        "outputs": [
            {
                "name": "sales_data",
                "type": "array",
                "description": "销售数据"
            }
        ]
    }
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node
    )
    
    print_result("Chart 节点", schema)
    assert schema["type"] == "page"
    # 检查是否包含 chart 组件
    body_str = json.dumps(schema["body"])
    assert "chart" in body_str


def test_direct_api_form():
    """测试直接 API 调用表单"""
    print_section("测试 11: 直接 API 调用表单")
    
    api = {
        "id": "api_test",
        "path": "/api/test",
        "method": "POST",
        "desc": "测试 API",
        "request": [
            {"name": "field1", "type": "string", "label": "字段1", "required": True},
            {"name": "field2", "type": "number", "label": "字段2", "required": False}
        ]
    }
    
    schema = amis_schema_generator.generate_direct_api_form(api)
    
    print_result("直接 API 表单", schema)
    assert schema["type"] == "page"
    assert schema["body"]["type"] == "form"
    assert len(schema["body"]["body"]) == 2


def test_rejection_response():
    """测试拒绝响应"""
    print_section("测试 12: 拒绝响应")
    
    schema = amis_schema_generator.generate_rejection_response(
        domain="general",
        instruction="今天天气怎么样",
        available_actions=["查询订单", "创建订单", "退款"]
    )
    
    print_result("拒绝响应", schema)
    assert schema["type"] == "page"
    assert schema["body"]["type"] == "alert"
    assert schema["body"]["level"] == "warning"
    assert "查询订单" in schema["body"]["body"]


def test_auto_inference():
    """测试自动推断展示类型"""
    print_section("测试 13: 自动推断展示类型")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    
    # 测试用例
    test_cases = [
        {
            "description": "查询订单列表",
            "expected": "table",
            "outputs": [{"name": "orders", "type": "array"}]
        },
        {
            "description": "商品展示",
            "expected": "cards",
            "outputs": [{"name": "products", "type": "array"}]
        },
        {
            "description": "用户信息",
            "expected": "service",
            "outputs": [{"name": "name", "type": "string"}]
        },
        {
            "description": "销售统计",
            "expected": "chart",
            "outputs": [{"name": "data", "type": "array"}]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        node = {
            "id": f"node_{i}",
            "type": "api_call",
            "description": case["description"],
            "config": {
                "method": "GET",
                "api_endpoint": f"/api/test{i}"
            },
            "outputs": case["outputs"]
        }
        
        schema = amis_schema_generator.generate_workflow_step_form(
            workflow=workflow,
            node=node
        )
        
        body_str = json.dumps(schema["body"]).lower()
        print(f"  {i}. {case['description']} → 推断为 {case['expected']}: ", end="")
        
        if case["expected"] in body_str:
            print("✅ 通过")
        else:
            print(f"⚠️ 未找到 {case['expected']}（可能被降级）")


def test_context_data_handling():
    """测试上下文数据处理"""
    print_section("测试 14: 上下文数据处理")
    
    workflow = {"id": "wf_1", "name": "测试工作流"}
    node = {
        "id": "node_1",
        "type": "api_call",
        "description": "确认订单",
        "config": {
            "method": "POST",
            "api_endpoint": "/api/orders/confirm",
            "parameters": {
                "order_id": "${order_id}",  # 在上下文中
                "payment_method": "${payment_method}"  # 不在上下文中
            }
        }
    }
    
    context_data = {"order_id": "ORD123456"}
    
    schema = amis_schema_generator.generate_workflow_step_form(
        workflow=workflow,
        node=node,
        context_data=context_data
    )
    
    print_result("上下文数据处理", schema)
    
    # 检查是否有隐藏字段（order_id）
    body_str = json.dumps(schema["body"])
    print("  - order_id 在上下文中 → 应该是隐藏字段")
    print("  - payment_method 不在上下文中 → 应该是输入字段")
    
    assert "hidden" in body_str
    assert "ORD123456" in body_str


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print("  Schema 生成策略测试套件")
    print("🚀" * 35)
    
    tests = [
        test_workflow_entry,
        test_start_node,
        test_end_node,
        test_condition_node,
        test_notification_node,
        test_api_call_get_table,
        test_api_call_get_cards,
        test_api_call_get_service,
        test_api_call_post,
        test_chart_node,
        test_direct_api_form,
        test_rejection_response,
        test_auto_inference,
        test_context_data_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 70)
    print(f"  测试完成: {passed} 通过, {failed} 失败")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！新架构工作正常！")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
