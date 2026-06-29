# Contributing to AILF

感谢您对 AILF (AI Language Frontend) 的兴趣！我们欢迎各种形式的贡献，包括但不限于提交 bug 报告、功能建议、文档改进和代码贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
  - [报告 Bug](#报告-bug)
  - [建议功能](#建议功能)
  - [提交代码](#提交代码)
  - [改进文档](#改进文档)
- [开发环境](#开发环境)
  - [前置要求](#前置要求)
  - [本地搭建](#本地搭建)
- [代码规范](#代码规范)
  - [Python 后端](#python-后端)
  - [TypeScript/React 前端](#typescriptreact-前端)
- [提交规范](#提交规范)
- [PR 流程](#pr-流程)
- [项目结构](#项目结构)

---

## 行为准则

- 保持尊重、友善的交流氛围
- 欢迎不同经验水平的贡献者
- 建设性的反馈优先于批评
- 关注技术本身，避免人身攻击

## 如何贡献

### 报告 Bug

如果发现了 Bug，请通过 GitHub Issues 提交，并包含以下信息：

1. **清晰的标题** — 简要描述问题
2. **环境信息** — OS、Python 版本、Node.js 版本、浏览器等
3. **复现步骤** — 详细的操作步骤
4. **预期行为** — 你认为应该发生什么
5. **实际行为** — 实际发生了什么
6. **日志/截图** — 相关的错误日志或界面截图

### 建议功能

我们欢迎功能建议！请在提交前：

1. 先搜索 Issues，确认是否已有类似建议
2. 清楚地描述功能的价值和使用场景
3. 如果可能，提供设计思路或实现方案

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 改进文档

文档改进是非常有价值的贡献。你可以在 `docs/` 目录下找到所有文档。欢迎修正错别字、补充示例、完善 API 说明等。

## 开发环境

### 前置要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| pnpm | 8+ | 前端包管理器 |
| Redis | 6+ | Celery 消息队列 & 缓存 |
| MySQL | 8.0+ | 业务数据存储 |

### 本地搭建

请参考 [README_zh.md](README_zh.md) 或 [README.md](README.md) 中的"手动安装"部分。

**快速回顾：**

```bash
# 1. 克隆仓库
git clone https://github.com/mxyooR/AILF.git
cd AILF

# 2. 创建 Python 环境
conda create -n ailf_env python=3.11
conda activate ailf_env

# 3. 安装后端依赖
cd backend
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 5. 初始化数据库
python scripts/init_db.py

# 6. 安装前端依赖
cd ../frontend
pnpm install

# 7. 启动后端（终端1）
cd ../backend
python main.py

# 8. 启动前端（终端2）
cd ../frontend
pnpm dev
```

## 代码规范

### Python 后端

- 遵循 **PEP 8** 编码规范
- 使用类型注解 (type hints)
- 函数/方法需要 docstring (中英文皆可)
- 命名规范：
  - 类名: `PascalCase`
  - 函数/变量: `snake_case`
  - 常量: `UPPER_CASE`
  - 私有成员: 前缀下划线 `_private_method`
- 导入顺序：标准库 → 第三方库 → 本地模块

**示例：**

```python
import os
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate
from app.services.user_service import UserService


router = APIRouter()


@router.post("/users")
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
) -> dict:
    """创建新用户"""
    service = UserService(db)
    user = service.create(request)
    return {"id": user.id, "username": user.username}
```

### TypeScript/React 前端

- 使用 **TypeScript**，避免 `any` 类型
- 组件文件名使用 `PascalCase` (如 `UserProfile.tsx`)
- 工具函数使用 `camelCase` (如 `formatDate.ts`)
- 使用 React Hooks 替代 class 组件
- Props 接口声明在文件顶部或独立类型文件

**组件结构：**

```tsx
interface UserProfileProps {
  userId: string;
  onUpdate?: () => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ userId, onUpdate }) => {
  // 组件逻辑
  return <div>...</div>;
};

export default UserProfile;
```

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]
```

**类型 (type):**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式调整 |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖 |

**示例：**

```
feat(ai): add streaming response for intent recognition
fix(workflow): handle empty node list gracefully
docs(api): update entity module API documentation
refactor(auth): extract JWT validation to middleware
```

## PR 流程

1. **确保测试通过**：`cd backend && python -m pytest tests/`
2. **保持小 PR**：一个 PR 只解决一个问题
3. **描述清楚**：说明为什么改、怎么改、测试情况
4. **代码审查**：至少一个人 review 后才能合并
5. **保持提交历史清晰**：必要时 rebase

**PR 模板：**

```markdown
## 描述
[简要描述改动内容]

## 类型
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor

## 测试
- [ ] 单元测试已通过
- [ ] 手动测试已完成

## 相关问题
Closes #[issue_number]
```

## 项目结构

```
AILF/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/       # API 路由
│   │   ├── core/         # 核心模块
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── services/     # 业务逻辑
│   │   └── templates/    # 业务模板
│   ├── scripts/          # 运维脚本
│   └── tests/            # 测试用例
├── frontend/             # React + AMIS 前端
├── celery_worker/        # 推理 Worker
├── Model/                # 训练相关
├── docs/                 # 文档
└── docker-compose.yml    # Docker 编排
```

## 许可证

通过提交贡献，您同意您的贡献将在 [MIT 许可证](LICENSE) 下授权。
