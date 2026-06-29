# AILF 测试文件

这个目录包含AILF系统的所有测试文件。

## 测试文件说明

### AI功能测试
- `test_ai_integration.py` - AI集成测试
- `test_ai_apis.py` - AI API测试

### 代码生成测试  
- `test_generation_api.py` - 代码生成API测试
- `test_complete_generation.py` - 完整代码生成流程测试
- `test_simple_generation.py` - 简单代码生成测试

### 代码审查测试
- `test_code_review.py` - 代码审查功能测试
- `test_review_with_existing.py` - 使用已有项目的审查测试
- `test_approve_activate.py` - 审查批准和激活测试
- `test_fixed_issues.py` - 修复问题后的测试

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python tests/test_ai_integration.py
```

## 测试环境要求

1. 确保后端服务运行在 http://localhost:8000
2. 确保有有效的开发者token (dev_token.txt)
3. 确保AI服务配置正确
