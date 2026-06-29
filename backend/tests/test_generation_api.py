"""
代码生成API测试
测试代码生成相关的API端点
"""
import pytest
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.generation_service import generation_service

# 配置pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_get_scenario_config():
    """测试获取场景配置"""
    print("🔧 测试获取场景配置...")
    
    try:
        config = await generation_service._get_scenario_config()
        
        assert config is not None, "场景配置不应为空"
        assert "entities" in config, "配置应包含entities字段"
        assert "apis" in config, "配置应包含apis字段"
        
        print("✅ 场景配置获取成功")
        print(f"实体数量: {len(config.get('entities', []))}")
        print(f"API数量: {len(config.get('apis', []))}")
        
    except Exception as e:
        print(f"❌ 场景配置获取失败: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_database_generation():
    """测试数据库生成功能"""
    print("🔧 测试数据库生成功能...")
    
    try:
        # 获取场景配置
        scenario_config = await generation_service._get_scenario_config()
        assert scenario_config is not None, "场景配置不应为空"
        
        # 生成数据库结构
        result = await generation_service.generate_database_structure(
            scenario_config=scenario_config,
            output_dir="/tmp/test_db_generation"
        )
        
        assert result["success"] == True, f"数据库生成应该成功: {result.get('error', '')}"
        assert "generated_tables" in result, "结果应包含generated_tables"
        assert len(result["generated_tables"]) > 0, "应该生成至少一个表"
        
        print("✅ 数据库生成成功")
        print(f"生成表数量: {len(result['generated_tables'])}")
        print(f"输出目录: {result['output_directory']}")
        
    except Exception as e:
        print(f"❌ 数据库生成失败: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_api_generation():
    """测试API生成功能"""
    print("🔧 测试API生成功能...")
    
    try:
        # 获取场景配置
        scenario_config = await generation_service._get_scenario_config()
        assert scenario_config is not None, "场景配置不应为空"
        
        # 生成API代码
        result = await generation_service.generate_api_code(
            scenario_config=scenario_config,
            output_dir="/tmp/test_api_generation"
        )
        
        assert result["success"] == True, f"API生成应该成功: {result.get('error', '')}"
        assert "generated_files" in result, "结果应包含generated_files"
        assert len(result["generated_files"]) > 0, "应该生成至少一个文件"
        
        print("✅ API生成成功")
        print(f"生成文件数量: {len(result['generated_files'])}")
        
    except Exception as e:
        print(f"❌ API生成失败: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_generation_status():
    """测试生成状态查询"""
    print("🔧 测试生成状态查询...")
    
    try:
        # 查询所有生成状态
        result = await generation_service.get_generation_status()
        
        assert result["success"] == True, f"状态查询应该成功: {result.get('error', '')}"
        assert "generations" in result, "结果应包含generations"
        
        print("✅ 生成状态查询成功")
        print(f"生成任务数量: {len(result.get('generations', []))}")
        
    except Exception as e:
        print(f"❌ 生成状态查询失败: {str(e)}")
        raise


@pytest.mark.asyncio
async def test_system_activation():
    """测试系统激活功能"""
    print("🔧 测试系统激活功能...")
    
    try:
        # 测试激活功能（使用模拟的generation_id）
        result = await generation_service.activate_generated_system(
            generation_id="test_generation_123"
        )
        
        # 由于没有实际的生成文件，这里应该返回失败
        assert result["success"] == False, "没有实际文件时应该返回失败"
        assert result["error"] == "generation_not_found", "应该返回generation_not_found错误"
        
        print("✅ 系统激活测试通过（预期失败）")
        print(f"错误信息: {result.get('details', '')}")
        
    except Exception as e:
        print(f"❌ 系统激活测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    # 直接运行测试
    async def run_tests():
        print("🚀 开始代码生成API测试...\n")
        
        await test_get_scenario_config()
        print()
        
        await test_database_generation()
        print()
        
        await test_api_generation()
        print()
        
        await test_generation_status()
        print()
        
        await test_system_activation()
        print()
        
        print("🎉 所有测试完成！")
    
    asyncio.run(run_tests())
