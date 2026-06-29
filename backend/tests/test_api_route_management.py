"""
API路由管理模块测试脚本
测试所有API路由管理功能，确保完全符合文档规范
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional


class APIRouteTestSuite:
    """API路由管理测试套件"""
    
    def __init__(self, base_url: str = "http://localhost:5000", token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXZlbG9wZXIiLCJ0eXBlIjoiZGV2ZWxvcGVyIiwiaWF0IjoxNzUzODU0NTM2LCJleHAiOjE3NTM4NTgxMzYsInVzZXJfdHlwZSI6ImRldmVsb3BlciJ9.2C3t1zaxdS9psFC8AP3SvTYzWf6ZeYORzFXFJn63lac"):
        """初始化测试套件"""
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        self.test_route_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """打印测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def assert_response(self, response: requests.Response, expected_code: int, test_name: str):
        """验证响应"""
        try:
            data = response.json() if response.content else {}
            if response.status_code == expected_code:
                self.log(f"✅ {test_name} - 响应状态码正确: {response.status_code}", "PASS")
                return data
            else:
                self.log(f"❌ {test_name} - 响应状态码错误: 期望 {expected_code}, 实际 {response.status_code}", "FAIL")
                self.log(f"响应内容: {data}", "ERROR")
                return None
        except Exception as e:
            self.log(f"❌ {test_name} - 响应解析失败: {str(e)}", "FAIL")
            return None
    
    def test_register_route(self) -> Optional[str]:
        """测试1: 动态注册新的API路由"""
        self.log("开始测试 - 动态注册API路由", "START")
        
        # 构造测试数据 - 商品创建API
        test_data = {
            "api_id": f"product_create_api_{int(time.time())}",
            "name": "商品创建API",
            "endpoint": f"/api/products/test_{int(time.time())}",
            "method": "POST",
            "description": "创建新的商品记录，支持商品基本信息和分类",
            "auth_required": True,
            "handler": {
                "type": "entity_crud",
                "config": {
                    "entity": "product",
                    "operation": "create",
                    "allowed_fields": ["name", "price", "description", "category_id", "brand_id"],
                    "validation_rules": {
                        "name": "required|max:100|unique:products,name",
                        "price": "required|numeric|min:0.01",
                        "category_id": "required|exists:categories,id"
                    },
                    "relations": ["category", "brand"],
                    "auto_timestamps": True
                }
            },
            "parameters": [
                {
                    "name": "name",
                    "type": "string",
                    "location": "body",
                    "required": True,
                    "description": "商品名称",
                    "validation": {
                        "max_length": 100,
                        "min_length": 2
                    }
                },
                {
                    "name": "price",
                    "type": "number",
                    "location": "body",
                    "required": True,
                    "description": "商品价格",
                    "validation": {
                        "min": 0.01,
                        "max": 999999.99
                    }
                },
                {
                    "name": "description",
                    "type": "string",
                    "location": "body",
                    "required": False,
                    "description": "商品描述"
                },
                {
                    "name": "category_id",
                    "type": "integer",
                    "location": "body",
                    "required": True,
                    "description": "商品分类ID"
                }
            ],
            "responses": {
                "201": {
                    "description": "商品创建成功",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 201},
                            "message": {"type": "string", "example": "商品创建成功"},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "product": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "price": {"type": "number"},
                                            "description": {"type": "string"},
                                            "category": {"type": "object"},
                                            "created_at": {"type": "string", "format": "datetime"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "400": {
                    "description": "请求参数验证失败",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 400},
                            "message": {"type": "string", "example": "参数验证失败"},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "error_type": {"type": "string"},
                                    "details": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "form_config": {
                "auto_generate": True,
                "layout": {
                    "type": "grid",
                    "columns": 2,
                    "spacing": 16
                },
                "sections": [
                    {
                        "title": "基本信息",
                        "fields": ["name", "category_id"]
                    },
                    {
                        "title": "详细信息",
                        "fields": ["price", "description"]
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/routes/register",
                headers=self.headers,
                json=test_data,
                timeout=30
            )
            
            data = self.assert_response(response, 201, "API路由注册")
            if data:
                # 验证响应格式
                required_fields = ['code', 'message', 'data', 'meta']
                for field in required_fields:
                    if field not in data:
                        self.log(f"❌ 响应缺少必需字段: {field}", "FAIL")
                        return None
                
                # 验证响应内容
                if data['code'] == 201 and data['message'] == "API路由注册成功":
                    route_data = data.get('data', {})
                    if 'route' in route_data:
                        route_id = route_data['route'].get('id')
                        self.log(f"✅ API路由注册成功，路由ID: {route_id}", "PASS")
                        self.test_route_id = route_id
                        return route_id
                    
            return None
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return None
    
    def test_get_routes_list(self):
        """测试2: 获取API路由列表"""
        self.log("开始测试 - 获取API路由列表", "START")
        
        try:
            # 测试基本列表查询
            response = requests.get(
                f"{self.base_url}/api/routes",
                headers=self.headers,
                timeout=30
            )
            
            data = self.assert_response(response, 200, "获取API路由列表")
            if data:
                # 验证分页信息
                route_data = data.get('data', {})
                if 'routes' in route_data and 'pagination' in route_data:
                    self.log(f"✅ 路由列表获取成功，共 {len(route_data['routes'])} 条记录", "PASS")
                    
                    # 测试筛选参数
                    filter_params = {
                        'status': 'active',
                        'method': 'POST',
                        'page': 1,
                        'limit': 10,
                        'include_stats': True,
                        'include_forms': True
                    }
                    
                    response = requests.get(
                        f"{self.base_url}/api/routes",
                        headers=self.headers,
                        params=filter_params,
                        timeout=30
                    )
                    
                    filter_data = self.assert_response(response, 200, "筛选API路由列表")
                    if filter_data:
                        self.log("✅ 路由列表筛选功能正常", "PASS")
                        return True
                        
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_get_route_detail(self):
        """测试3: 获取API路由详情"""
        if not self.test_route_id:
            self.log("❌ 跳过测试 - 没有可用的路由ID", "SKIP")
            return False
            
        self.log("开始测试 - 获取API路由详情", "START")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/routes/{self.test_route_id}",
                headers=self.headers,
                timeout=30
            )
            
            data = self.assert_response(response, 200, "获取API路由详情")
            if data:
                route = data.get('data', {}).get('route', {})
                if route.get('id') == self.test_route_id:
                    self.log("✅ API路由详情获取成功", "PASS")
                    return True
                    
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_update_route(self):
        """测试4: 更新API路由"""
        if not self.test_route_id:
            self.log("❌ 跳过测试 - 没有可用的路由ID", "SKIP")
            return False
            
        self.log("开始测试 - 更新API路由", "START")
        
        update_data = {
            "name": "商品创建API（已更新）",
            "description": "更新后的商品创建API描述",
            "auth_required": True
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/api/routes/{self.test_route_id}",
                headers=self.headers,
                json=update_data,
                timeout=30
            )
            
            data = self.assert_response(response, 200, "更新API路由")
            if data and data.get('code') == 200:
                self.log("✅ API路由更新成功", "PASS")
                return True
                
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_route_activation(self):
        """测试5: 路由激活/停用"""
        if not self.test_route_id:
            self.log("❌ 跳过测试 - 没有可用的路由ID", "SKIP")
            return False
            
        self.log("开始测试 - 路由激活功能", "START")
        
        try:
            # 测试激活路由
            response = requests.post(
                f"{self.base_url}/api/routes/{self.test_route_id}/activate",
                headers=self.headers,
                params={'health_check': True, 'warm_up': True},
                timeout=30
            )
            
            data = self.assert_response(response, 200, "激活API路由")
            if data and data.get('code') == 200:
                self.log("✅ API路由激活成功", "PASS")
                
                # 测试停用路由
                response = requests.post(
                    f"{self.base_url}/api/routes/{self.test_route_id}/deactivate",
                    headers=self.headers,
                    params={'graceful': True, 'timeout': 30},
                    timeout=30
                )
                
                deactivate_data = self.assert_response(response, 200, "停用API路由")
                if deactivate_data and deactivate_data.get('code') == 200:
                    self.log("✅ API路由停用成功", "PASS")
                    return True
                    
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_route_status(self):
        """测试6: 获取路由状态"""
        if not self.test_route_id:
            self.log("❌ 跳过测试 - 没有可用的路由ID", "SKIP")
            return False
            
        self.log("开始测试 - 获取路由状态", "START")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/routes/{self.test_route_id}/status",
                headers=self.headers,
                params={
                    'period': '24h',
                    'include_trends': True,
                    'include_errors': True
                },
                timeout=30
            )
            
            data = self.assert_response(response, 200, "获取路由状态")
            if data:
                status_data = data.get('data', {})
                if 'status' in status_data and 'statistics' in status_data:
                    self.log("✅ 路由状态信息获取成功", "PASS")
                    return True
                    
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_routes_health(self):
        """测试7: 健康检查"""
        self.log("开始测试 - 路由健康检查", "START")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/routes/health",
                headers=self.headers,
                params={
                    'detailed': True,
                    'include_inactive': False,
                    'format': 'json'
                },
                timeout=30
            )
            
            data = self.assert_response(response, 200, "路由健康检查")
            if data:
                health_data = data.get('data', {})
                if 'summary' in health_data and 'routes' in health_data:
                    self.log("✅ 路由健康检查完成", "PASS")
                    return True
                    
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_delete_route(self):
        """测试8: 删除API路由（清理测试数据）"""
        if not self.test_route_id:
            self.log("❌ 跳过测试 - 没有可用的路由ID", "SKIP")
            return False
            
        self.log("开始测试 - 删除API路由", "START")
        
        try:
            response = requests.delete(
                f"{self.base_url}/api/routes/{self.test_route_id}",
                headers=self.headers,
                params={
                    'force': True,
                    'backup': True,
                    'cascade': False
                },
                timeout=30
            )
            
            data = self.assert_response(response, 200, "删除API路由")
            if data and data.get('code') == 200:
                self.log("✅ API路由删除成功", "PASS")
                return True
                
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def test_error_scenarios(self):
        """测试9: 错误场景"""
        self.log("开始测试 - 错误场景处理", "START")
        
        # 测试路由冲突
        conflict_data = {
            "api_id": "conflict_test_api",
            "name": "冲突测试API",
            "endpoint": "/api/products",  # 使用已存在的端点
            "method": "POST",
            "handler": {
                "type": "static_data",
                "config": {"data": {"message": "test"}}
            },
            "responses": {
                "200": {
                    "description": "测试响应"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/routes/register",
                headers=self.headers,
                json=conflict_data,
                timeout=30
            )
            
            # 应该返回409冲突错误
            if response.status_code == 409:
                self.log("✅ 路由冲突检测正常", "PASS")
            else:
                self.log(f"❌ 路由冲突检测异常: {response.status_code}", "FAIL")
            
            # 测试无效路由ID
            response = requests.get(
                f"{self.base_url}/api/routes/invalid_route_id",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 404:
                self.log("✅ 无效路由ID处理正常", "PASS")
                return True
            else:
                self.log(f"❌ 无效路由ID处理异常: {response.status_code}", "FAIL")
                
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 请求失败: {str(e)}", "FAIL")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 60, "INFO")
        self.log("开始API路由管理模块完整测试", "START")
        self.log("=" * 60, "INFO")
        
        tests = [
            ("注册API路由", self.test_register_route),
            ("获取路由列表", self.test_get_routes_list),
            ("获取路由详情", self.test_get_route_detail),
            ("更新API路由", self.test_update_route),
            ("路由激活/停用", self.test_route_activation),
            ("获取路由状态", self.test_route_status),
            ("路由健康检查", self.test_routes_health),
            ("错误场景处理", self.test_error_scenarios),
            ("删除API路由", self.test_delete_route)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n{'=' * 50}", "INFO")
            self.log(f"执行测试: {test_name}", "INFO")
            self.log(f"{'=' * 50}", "INFO")
            
            result = test_func()
            if result:
                passed += 1
                
            time.sleep(1)  # 测试间隔
        
        self.log("\n" + "=" * 60, "INFO")
        self.log(f"测试完成 - 通过: {passed}/{total}", "SUMMARY")
        self.log("=" * 60, "INFO")
        
        if passed == total:
            self.log("🎉 所有测试通过！API路由管理模块功能完整", "SUCCESS")
        else:
            self.log(f"⚠️  有 {total - passed} 个测试失败", "WARNING")
        
        return passed == total


def main():
    """主函数"""
    # 检查后端服务是否运行
    try:
        response = requests.get("http://localhost:5000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
        else:
            print("❌ 后端服务响应异常")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到后端服务，请确保后端已启动")
        return
    
    # 运行测试
    test_suite = APIRouteTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
