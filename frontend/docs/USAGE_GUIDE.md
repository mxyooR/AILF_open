# AILF前端Token管理系统使用指南

## 🚀 快速开始

### 1. 访问开发者配置页面

访问 `http://localhost:3000/config` 进入开发者配置页面。

### 2. 开发者认证

1. 在第一步"开发者认证"中输入开发者密码
2. 密码: `AILF_DEV_2024_SECURE`
3. 可选择"记住登录状态"以保持认证
4. 点击"开始配置"完成认证

### 3. 步骤导航

认证成功后，您可以：
- 按顺序完成各个配置步骤
- 点击左侧步骤列表快速跳转（仅限已启用的步骤）
- 查看步骤完成进度

## 🔐 认证机制说明

### Token管理
- **自动存储**: Token自动保存到浏览器本地存储
- **自动刷新**: Token即将过期时（提前5分钟）自动刷新
- **状态同步**: 认证状态在所有组件间实时同步
- **安全清理**: 无效或过期的token自动清除

### 权限控制
- **第1步**: 开发者认证 - 总是可访问
- **第2-8步**: 需要先完成认证，且按顺序完成前置步骤

## 🛠️ 测试功能

### 访问测试页面
访问 `http://localhost:3000/test/token` 查看Token管理器测试页面。

### 测试功能包括
- **开发者认证**: 测试认证流程
- **Token验证**: 验证当前token有效性
- **状态监控**: 实时查看认证状态和token信息
- **自动刷新**: 观察token自动刷新机制

## 🔧 开发者指南

### 使用TokenManager

```typescript
import { tokenManager } from '../services/common/tokenManager';

// 检查认证状态
const isAuthenticated = tokenManager.isAuthenticated();

// 获取token信息
const tokenInfo = tokenManager.getTokenInfo();

// 监听状态变化
tokenManager.addListener((isAuthenticated) => {
  console.log('认证状态:', isAuthenticated);
});
```

### 使用认证Hook

```typescript
import { useDeveloperAuth } from '../hooks/developer/useDeveloperAuth';

const MyComponent = () => {
  const { authState, authenticate, logout } = useDeveloperAuth();
  
  // 认证状态: authState.isAuthenticated
  // 执行认证: authenticate({ password, rememberMe })
  // 退出登录: logout()
};
```

### 保护组件

```typescript
import AuthGuard from '../components/developer/auth/AuthGuard';

<AuthGuard onAuthRequired={() => navigate('/config')}>
  <ProtectedComponent />
</AuthGuard>
```

## 🚨 常见问题

### Q: Token过期了怎么办？
A: 系统会自动尝试刷新token。如果刷新失败，会自动清除过期token并提示重新认证。

### Q: 页面刷新后需要重新登录吗？
A: 不需要。Token会自动从本地存储恢复，除非已过期。

### Q: 如何查看当前认证状态？
A: 可以访问测试页面 `/test/token` 查看详细的认证状态信息。

### Q: 为什么某些步骤无法访问？
A: 请确保：
1. 已完成开发者认证
2. 按顺序完成了前置步骤
3. 当前步骤已启用（非开发中状态）

## 📱 移动端支持

当前系统主要针对桌面端设计，移动端访问可能存在样式适配问题。建议使用桌面浏览器进行开发者配置。

## 🔄 更新日志

### v2.0.0 (2024-01-20)
- ✅ 实现统一Token管理系统
- ✅ 添加严格的步骤访问控制
- ✅ 支持自动token刷新
- ✅ 优化用户体验和错误处理

### v1.x
- 基础认证功能
- 简单的步骤导航



**文档版本**: v2.0.0
**最后更新**: 2024-01-20
