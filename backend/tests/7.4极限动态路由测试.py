"""
极限动态路由测试
测试大量路由的动态导入和删除，验证系统稳定性
"""
import requests
import json
import time
import threading
import concurrent.futures
from typing import List, Dict


def get_auth_token():
    """获取认证令牌"""
    response = requests.post(
        "http://localhost:5000/api/auth/developer",
        json={"password": "AILF_DEV_2024_SECURE"}
    )
    return response.json()["data"]["token"]


def create_test_route(index: int) -> Dict:
    """创建测试路由配置"""
    return {
        "api_id": f"extreme_test_{index}",
        "name": f"极限测试路由{index}",
        "endpoint": f"/api/extreme/test{index}",
        "method": "GET",
        "description": f"第{index}个极限测试路由",
        "auth_required": False,
        "handler": {
            "type": "static_data",
            "config": {
                "data": {
                    "route_index": index,
                    "message": f"这是动态路由{index}",
                    "timestamp": time.time()
                }
            }
        },
        "parameters": [],
        "responses": {"200": {"description": "成功"}}
    }


def register_route(headers: Dict, route_config: Dict) -> Dict:
    """注册单个路由"""
    try:
        response = requests.post("http://localhost:5000/api/routes/register", 
                               headers=headers, json=route_config, timeout=10)
        if response.status_code == 201:
            data = response.json()
            return {
                "success": True,
                "id": data["data"]["route"]["id"],
                "endpoint": route_config["endpoint"]
            }
        else:
            return {
                "success": False,
                "error": f"Status: {response.status_code}",
                "endpoint": route_config["endpoint"]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "endpoint": route_config["endpoint"]
        }


def delete_route(headers: Dict, route_id: str, endpoint: str) -> Dict:
    """删除单个路由"""
    try:
        response = requests.delete(f"http://localhost:5000/api/routes/{route_id}", 
                                 headers=headers, timeout=10)
        if response.status_code == 200:
            return {
                "success": True,
                "id": route_id,
                "endpoint": endpoint
            }
        else:
            return {
                "success": False,
                "error": f"Status: {response.status_code}",
                "id": route_id,
                "endpoint": endpoint
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "id": route_id,
            "endpoint": endpoint
        }


def test_route_access(endpoint: str) -> bool:
    """测试路由访问"""
    try:
        response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
        return response.status_code == 200
    except:
        return False


def test_extreme_dynamic_routing():
    """极限动态路由测试"""
    print("🔥 极限动态路由测试")
    print("=" * 80)
    print("测试大量路由的动态导入和删除，验证系统稳定性")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试参数
    ROUTE_COUNT = 50  # 测试50个路由
    CONCURRENT_WORKERS = 10  # 10个并发工作线程
    
    test_results = []
    registered_routes = []
    
    # 1. 批量注册路由
    print(f"\n1️⃣ 批量注册 {ROUTE_COUNT} 个路由")
    print("-" * 60)
    
    # 创建路由配置
    route_configs = [create_test_route(i) for i in range(1, ROUTE_COUNT + 1)]
    
    # 并发注册路由
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(register_route, headers, config) for config in route_configs]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    register_time = time.time() - start_time
    
    # 统计注册结果
    successful_registers = [r for r in results if r["success"]]
    failed_registers = [r for r in results if not r["success"]]
    
    registered_routes = successful_registers
    
    print(f"✅ 注册成功: {len(successful_registers)}/{ROUTE_COUNT}")
    print(f"❌ 注册失败: {len(failed_registers)}")
    print(f"⏱️ 注册耗时: {register_time:.2f}秒")
    print(f"📈 注册速度: {len(successful_registers)/register_time:.1f} 路由/秒")
    
    if len(successful_registers) >= ROUTE_COUNT * 0.9:  # 至少90%成功
        test_results.append(True)
    else:
        test_results.append(False)
    
    # 等待路由生效
    print("\n⏳ 等待路由生效...")
    time.sleep(5)
    
    # 2. 批量验证路由可访问性
    print(f"\n2️⃣ 批量验证 {len(registered_routes)} 个路由可访问性")
    print("-" * 60)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(test_route_access, route["endpoint"]) 
                  for route in registered_routes]
        access_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    access_time = time.time() - start_time
    
    successful_access = sum(access_results)
    
    print(f"✅ 访问成功: {successful_access}/{len(registered_routes)}")
    print(f"❌ 访问失败: {len(registered_routes) - successful_access}")
    print(f"⏱️ 访问耗时: {access_time:.2f}秒")
    print(f"📈 访问速度: {len(registered_routes)/access_time:.1f} 请求/秒")
    
    if successful_access >= len(registered_routes) * 0.9:  # 至少90%成功
        test_results.append(True)
    else:
        test_results.append(False)
    
    # 3. 随机访问压力测试
    print(f"\n3️⃣ 随机访问压力测试 (10秒)")
    print("-" * 60)
    
    import random
    
    def random_access_test():
        success_count = 0
        total_count = 0
        start_time = time.time()
        
        while time.time() - start_time < 10:  # 10秒测试
            if registered_routes:
                route = random.choice(registered_routes)
                if test_route_access(route["endpoint"]):
                    success_count += 1
                total_count += 1
                time.sleep(0.05)  # 50ms间隔
        
        return success_count, total_count
    
    # 启动多个并发压力测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(random_access_test) for _ in range(5)]
        stress_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_success = sum(r[0] for r in stress_results)
    total_requests = sum(r[1] for r in stress_results)
    success_rate = total_success / total_requests if total_requests > 0 else 0
    
    print(f"✅ 压力测试成功: {total_success}/{total_requests} ({success_rate:.1%})")
    print(f"📈 平均QPS: {total_requests/10:.1f}")
    
    if success_rate >= 0.85:  # 至少85%成功率
        test_results.append(True)
    else:
        test_results.append(False)
    
    # 4. 批量删除路由
    print(f"\n4️⃣ 批量删除 {len(registered_routes)} 个路由")
    print("-" * 60)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(delete_route, headers, route["id"], route["endpoint"]) 
                  for route in registered_routes]
        delete_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    delete_time = time.time() - start_time
    
    successful_deletes = [r for r in delete_results if r["success"]]
    failed_deletes = [r for r in delete_results if not r["success"]]
    
    print(f"✅ 删除成功: {len(successful_deletes)}/{len(registered_routes)}")
    print(f"❌ 删除失败: {len(failed_deletes)}")
    print(f"⏱️ 删除耗时: {delete_time:.2f}秒")
    print(f"📈 删除速度: {len(successful_deletes)/delete_time:.1f} 路由/秒")
    
    if len(successful_deletes) >= len(registered_routes) * 0.9:  # 至少90%成功
        test_results.append(True)
    else:
        test_results.append(False)
    
    # 等待删除生效
    print("\n⏳ 等待删除生效...")
    time.sleep(5)
    
    # 5. 验证删除后路由不可访问
    print(f"\n5️⃣ 验证删除后路由不可访问")
    print("-" * 60)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(test_route_access, route["endpoint"]) 
                  for route in successful_deletes]
        post_delete_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    verify_time = time.time() - start_time
    
    still_accessible = sum(post_delete_results)
    properly_deleted = len(post_delete_results) - still_accessible
    
    print(f"✅ 正确删除: {properly_deleted}/{len(successful_deletes)}")
    print(f"❌ 仍可访问: {still_accessible}")
    print(f"⏱️ 验证耗时: {verify_time:.2f}秒")
    
    if still_accessible <= len(successful_deletes) * 0.1:  # 最多10%仍可访问
        test_results.append(True)
    else:
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print("📊 极限动态路由测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    print(f"\n📈 性能统计:")
    print(f"  • 路由注册速度: {len(successful_registers)/register_time:.1f} 路由/秒")
    print(f"  • 路由访问速度: {len(registered_routes)/access_time:.1f} 请求/秒")
    print(f"  • 压力测试QPS: {total_requests/10:.1f}")
    print(f"  • 路由删除速度: {len(successful_deletes)/delete_time:.1f} 路由/秒")
    
    if passed == total:
        print("\n🎉 极限动态路由测试全部通过！")
        print("✅ 系统在高负载下稳定运行")
        print("✅ 大量路由动态管理正常")
        print("✅ 并发操作性能优秀")
    else:
        print(f"\n❌ 有 {total - passed} 个测试项失败")
        print("⚠️ 系统在极限条件下存在问题")
    
    return passed == total


if __name__ == "__main__":
    success = test_extreme_dynamic_routing()
    exit(0 if success else 1)
