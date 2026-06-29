"""
测试复杂字段类型的支持
"""
import sys
sys.path.insert(0, 'E:/Programming/AILF/backend')

from app.services.amis_schema_generator import amis_schema_generator

def test_select_field():
    """测试下拉选择框"""
    field = {
        "name": "seat_type",
        "type": "select",
        "label": "座位类型",
        "required": True,
        "options": ["一等座", "二等座", "商务座", "无座"]
    }
    
    result = amis_schema_generator._convert_field_to_form_config(field)
    
    print("=" * 60)
    print("测试 select 字段")
    print("=" * 60)
    print(f"输入: {field}")
    print(f"输出: {result}")
    
    assert result["type"] == "select", f"类型错误: {result['type']}"
    assert "options" in result, "缺少 options"
    assert len(result["options"]) == 4, f"options 数量错误: {len(result['options'])}"
    assert result["options"][0]["label"] == "一等座", f"options 格式错误: {result['options'][0]}"
    print("✅ select 字段测试通过\n")

def test_file_upload_field():
    """测试文件上传"""
    field = {
        "name": "attachment",
        "type": "file",
        "label": "附件",
        "required": False
    }
    
    result = amis_schema_generator._convert_field_to_form_config(field)
    
    print("=" * 60)
    print("测试 file 字段")
    print("=" * 60)
    print(f"输入: {field}")
    print(f"输出: {result}")
    
    assert result["type"] == "input-file", f"类型错误: {result['type']}"
    assert "receiver" in result, "缺少 receiver"
    assert result["receiver"] == "/api/v1/upload", f"receiver 错误: {result['receiver']}"
    print("✅ file 字段测试通过\n")

def test_image_upload_field():
    """测试图片上传"""
    field = {
        "name": "avatar",
        "type": "image",
        "label": "头像",
        "required": False
    }
    
    result = amis_schema_generator._convert_field_to_form_config(field)
    
    print("=" * 60)
    print("测试 image 字段")
    print("=" * 60)
    print(f"输入: {field}")
    print(f"输出: {result}")
    
    assert result["type"] == "input-image", f"类型错误: {result['type']}"
    assert "receiver" in result, "缺少 receiver"
    assert "accept" in result, "缺少 accept"
    assert result["accept"] == "image/*", f"accept 错误: {result['accept']}"
    assert "limit" in result, "缺少 limit"
    print("✅ image 字段测试通过\n")

def test_date_field():
    """测试日期选择器"""
    field = {
        "name": "departure_date",
        "type": "date",
        "label": "出发日期",
        "required": True
    }
    
    result = amis_schema_generator._convert_field_to_form_config(field)
    
    print("=" * 60)
    print("测试 date 字段")
    print("=" * 60)
    print(f"输入: {field}")
    print(f"输出: {result}")
    
    assert result["type"] == "input-date", f"类型错误: {result['type']}"
    assert "format" in result, "缺少 format"
    assert result["format"] == "YYYY-MM-DD", f"format 错误: {result['format']}"
    print("✅ date 字段测试通过\n")

def test_datetime_field():
    """测试日期时间选择器"""
    field = {
        "name": "appointment_time",
        "type": "datetime",
        "label": "预约时间",
        "required": True
    }
    
    result = amis_schema_generator._convert_field_to_form_config(field)
    
    print("=" * 60)
    print("测试 datetime 字段")
    print("=" * 60)
    print(f"输入: {field}")
    print(f"输出: {result}")
    
    assert result["type"] == "input-datetime", f"类型错误: {result['type']}"
    assert "format" in result, "缺少 format"
    assert result["format"] == "YYYY-MM-DD HH:mm:ss", f"format 错误: {result['format']}"
    print("✅ datetime 字段测试通过\n")

def test_number_field():
    """测试数字输入"""
    field = {
        "name": "quantity",
        "type": "number",
        "label": "数量",
        "required": True,
        "min": 1,
        "max": 100,
        "step": 1
    }
    
    result = amis_schema_generator._convert_field_to_form_config(field)
    
    print("=" * 60)
    print("测试 number 字段")
    print("=" * 60)
    print(f"输入: {field}")
    print(f"输出: {result}")
    
    assert result["type"] == "input-number", f"类型错误: {result['type']}"
    assert "min" in result, "缺少 min"
    assert result["min"] == 1, f"min 错误: {result['min']}"
    assert "max" in result, "缺少 max"
    assert result["max"] == 100, f"max 错误: {result['max']}"
    print("✅ number 字段测试通过\n")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("开始测试复杂字段类型支持")
    print("=" * 60 + "\n")
    
    try:
        test_select_field()
        test_file_upload_field()
        test_image_upload_field()
        test_date_field()
        test_datetime_field()
        test_number_field()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
