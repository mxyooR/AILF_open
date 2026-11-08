# Contributing to AILF

感谢参与改进。报告问题时请附上运行方式、复现步骤和经过脱敏的日志。功能改动应说明对应的业务需求与验证方式。

## 运行与检查

依赖和启动步骤见[部署指南](docs/DEPLOYMENT.md)。已有本地环境可以直接复用。前端位于 `frontend/`，后端离线单元测试位于 `backend/tests/unit/`。

```bash
pnpm typecheck
pnpm test
pnpm build
python -m unittest discover -s backend/tests/unit -v
python -m unittest discover -s scripts/tests -v
python scripts/check_public_repo.py
```

CI 执行类型检查、演示测试、生产构建、离线配置 / 扫描器测试和当前公开文件扫描。GPU 推理及 MySQL / Redis 完整集成需要单独验证。

## 修改约定

- 说明当前行为、修改后的行为和验证结果。文档改动不应引入未经测量的准确率或性能数字。
- 保持演示与真实推理的区别清晰；演示数据使用显式的合成标记。
- 业务写入或配置迁移请使用独立测试库，提供恢复方式，不要对个人现有数据库运行集成脚本。
- 新增测试优先覆盖用户可见行为、输入边界和失败路径。
- 第三方代码、模型和素材保留来源与许可。

## 提交前

```bash
git diff --check
git add <reviewed-files>
python scripts/check_public_repo.py --staged
git diff --cached --stat
```

扫描器检查实际暂存内容，输出仅包含位置与规则名。`.gitignore` 不能保护已经被跟踪的文件；请一并审阅暂存内容和截图。不要提交 `.env`、真实 Token、数据库导出、上传文件、个人账号信息或模型权重。详细规则见[安全说明](SECURITY.md)。

建议使用 `feat:`、`fix:`、`docs:`、`test:` 或 `chore:` 提交前缀。PR 应围绕具体问题描述最终变化，并标明验证范围。
