#!/usr/bin/env python3
"""
第十一部分：AI交互模块简化测试
测试AI核心功能，不依赖后端服务
"""
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    
    try:
        from app.core.ai.amis_knowledge import amis_knowledge, AmisComponentType
        print("✅ amis知识库导入成功")
        
        from app.core.ai.amis_validator import amis_validator
        print("✅ amis校验器导入成功")
        
        from app.core.ai.prompt_templates import prompt_manager, PromptType
        print("✅ 提示词模板导入成功")
        
        from backend.app.services.ai_service_new import ai_service
        print("✅ AI服务导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {str(e)}")
        return False

def test_amis_knowledge():
    """测试amis知识库"""
    print("\n=== 测试amis知识库 ===")
    
    try:
        from app.core.ai.amis_knowledge import amis_knowledge, AmisComponentType
        
        # 测试组件模板
        page_template = amis_knowledge.get_component_template(AmisComponentType.PAGE, "basic")
        assert page_template.get("type") == "page", "页面模板类型错误"
        print("✅ 页面模板测试通过")
        
        # 测试表单项配置
        text_config = amis_knowledge.get_form_item_config("string", "username", "用户名", required=True)
        assert text_config.get("type") == "input-text", "文本输入类型错误"
        assert text_config.get("required") == True, "必填配置错误"
        print("✅ 表单项配置测试通过")
        
        # 测试CRUD列配置
        column_config = amis_knowledge.get_crud_column_config("created_at", "创建时间", "datetime")
        assert column_config.get("type") == "datetime", "日期时间列类型错误"
        print("✅ CRUD列配置测试通过")
        
        # 测试最佳实践
        practices = amis_knowledge.get_best_practices("form_design")
        assert isinstance(practices, list), "最佳实践应该是列表"
        assert len(practices) > 0, "应该有最佳实践建议"
        print(f"✅ 最佳实践测试通过 ({len(practices)} 条建议)")
        
        return True
        
    except Exception as e:
        print(f"❌ amis知识库测试失败: {str(e)}")
        return False

def test_amis_validator():
    """测试amis校验器"""
    print("\n=== 测试amis校验器 ===")
    
    try:
        from app.core.ai.amis_validator import amis_validator
        
        # 测试有效schema
        valid_schema = {
            "type": "page",
            "title": "测试页面",
            "body": [
                {
                    "type": "crud",
                    "api": "/api/test",
                    "columns": [
                        {"name": "id", "label": "ID"},
                        {"name": "name", "label": "名称"}
                    ]
                }
            ]
        }
        
        result = amis_validator.validate(valid_schema)
        assert result.is_valid, "有效schema应该通过校验"
        print("✅ 有效schema校验通过")
        
        # 测试无效schema
        invalid_schema = {
            "type": "crud"
            # 缺少必需的api字段
        }
        
        result = amis_validator.validate(invalid_schema)
        assert not result.is_valid, "无效schema应该校验失败"
        assert len(result.errors) > 0, "应该有错误信息"
        print(f"✅ 无效schema校验失败 ({len(result.errors)} 个错误)")
        
        return True
        
    except Exception as e:
        print(f"❌ amis校验器测试失败: {str(e)}")
        return False

def test_prompt_templates():
    """测试提示词模板"""
    print("\n=== 测试提示词模板 ===")
    
    try:
        from app.core.ai.prompt_templates import prompt_manager, PromptType
        
        # 测试意图分析模板
        messages = prompt_manager.get_messages(
            PromptType.INTENT_ANALYSIS,
            command="显示用户列表",
            context="{}"
        )
        
        assert isinstance(messages, list), "消息应该是列表"
        assert len(messages) > 0, "应该有消息内容"
        assert all("role" in msg and "content" in msg for msg in messages), "消息格式错误"
        print(f"✅ 意图分析模板测试通过 ({len(messages)} 条消息)")
        
        # 测试amis schema生成模板
        messages = prompt_manager.get_messages(
            PromptType.AMIS_SCHEMA_GENERATION,
            intent='{"intent_type": "data_query", "entity": "user"}',
            entities='[]',
            scenario_config='{}',
            api_endpoints='{}'
        )
        
        assert isinstance(messages, list), "消息应该是列表"
        assert len(messages) > 0, "应该有消息内容"
        print(f"✅ amis schema生成模板测试通过 ({len(messages)} 条消息)")
        
        return True
        
    except Exception as e:
        print(f"❌ 提示词模板测试失败: {str(e)}")
        return False

def test_ai_service_basic():
    """测试AI服务基础功能"""
    print("\n=== 测试AI服务基础功能 ===")
    
    try:
        from backend.app.services.ai_service_new import ai_service
        
        # 测试服务实例化
        assert ai_service is not None, "AI服务实例不应该为空"
        print("✅ AI服务实例化成功")
        
        # 测试schema校验方法
        test_schema = {
            "type": "page",
            "title": "测试",
            "body": []
        }
        
        validation_result = ai_service._validate_amis_schema(test_schema)
        assert validation_result is not None, "校验结果不应该为空"
        assert hasattr(validation_result, 'is_valid'), "校验结果应该有is_valid属性"
        print("✅ schema校验方法测试通过")
        
        # 测试实体字段生成
        fields = ai_service._get_default_entity_fields("user")
        assert isinstance(fields, list), "字段应该是列表"
        assert len(fields) > 0, "应该有默认字段"
        print(f"✅ 实体字段生成测试通过 ({len(fields)} 个字段)")
        
        return True
        
    except Exception as e:
        print(f"❌ AI服务基础功能测试失败: {str(e)}")
        return False

def test_component_coverage():
    """测试组件覆盖度"""
    print("\n=== 测试组件覆盖度 ===")
    
    try:
        from app.core.ai.amis_knowledge import AmisComponentType, AmisFormItemType
        
        # 测试组件类型数量
        component_count = len(list(AmisComponentType))
        print(f"支持的组件类型: {component_count} 种")
        assert component_count >= 50, f"组件类型数量不足，当前: {component_count}"
        
        # 测试表单项类型数量
        form_item_count = len(list(AmisFormItemType))
        print(f"支持的表单项类型: {form_item_count} 种")
        assert form_item_count >= 30, f"表单项类型数量不足，当前: {form_item_count}"
        
        # 测试关键组件类型
        key_components = [
            AmisComponentType.PAGE,
            AmisComponentType.FORM,
            AmisComponentType.CRUD,
            AmisComponentType.TABLE,
            AmisComponentType.DIALOG,
            AmisComponentType.DRAWER
        ]
        
        for component in key_components:
            assert component.value, f"关键组件 {component.name} 值为空"
        
        print("✅ 关键组件类型测试通过")
        
        # 测试关键表单项类型
        key_form_items = [
            AmisFormItemType.INPUT_TEXT,
            AmisFormItemType.SELECT,
            AmisFormItemType.TEXTAREA,
            AmisFormItemType.INPUT_DATE,
            AmisFormItemType.SWITCH
        ]
        
        for form_item in key_form_items:
            assert form_item.value, f"关键表单项 {form_item.name} 值为空"
        
        print("✅ 关键表单项类型测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件覆盖度测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始AI交互模块简化测试...")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("amis知识库", test_amis_knowledge),
        ("amis校验器", test_amis_validator),
        ("提示词模板", test_prompt_templates),
        ("AI服务基础功能", test_ai_service_basic),
        ("组件覆盖度", test_component_coverage)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！AI交互模块核心功能正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
