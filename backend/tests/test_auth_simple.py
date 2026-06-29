"""
开发者认证测试
"""
import requests
import json


def test_developer_auth():
    """测试开发者认证"""
    base_url = "http://localhost:5000"
    
    print("测试开发者认证...")
    
    # 测试获取开发者令牌
    auth_data = {
        "password": "AILF_DEV_2024_SECURE"  # 从config.py中的默认密码
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/developer",
            json=auth_data,
            timeout=10
        )
        
        print(f"认证响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 开发者认证成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 提取token
            token = data.get('data', {}).get('token')
            if token:
                print(f"🔑 Token: {token}")
                return token
            else:
                print("❌ 响应中没有找到token")
                return None
        else:
            print(f"❌ 认证失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {str(e)}")
        return None


def test_with_token(token: str):
    """使用token测试API访问"""
    base_url = "http://localhost:5000"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n使用token测试API访问...")
    
    try:
        # 测试获取路由列表
        response = requests.get(
            f"{base_url}/api/routes",
            headers=headers,
            timeout=10
        )
        
        print(f"API路由列表响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API路由列表访问成功")
            print(f"路由数量: {len(data.get('data', {}).get('routes', []))}")
            return True
        else:
            print(f"❌ API访问失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("开发者认证和API访问测试")
    print("=" * 50)
    
    # 先测试认证
    token = test_developer_auth()
    
    if token:
        # 使用获取的token测试API访问
        success = test_with_token(token)
        
        if success:
            print("\n🎉 认证和API访问测试通过!")
            print(f"✅ 可以使用token: {token}")
        else:
            print("\n❌ API访问测试失败")
    else:
        print("\n❌ 认证测试失败，无法继续")


if __name__ == "__main__":
    main()
