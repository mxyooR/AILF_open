# 验证记录

验证日期：2026-11-08。本记录包括演示、开源内容清理、异步命令运行时、工作流编辑器，以及后端工作流与实体数据库修复。所有数字均为实际执行结果；此前前端检查和本次后端检查分别记录。

## 环境与执行范围

- Windows，Node.js 24.21.0，TypeScript 4.9.5，Python 3.12.11。
- 复用已有前端依赖和 Python 环境；前端源码副本、构建与日志位于原项目的本地验证目录，未为开源副本再次安装依赖。
- 原有 19 项后端离线测试不导入应用启动入口。新增回归在隔离 SQLite 中执行真实事务，通过 ASGI 导入并执行应用 HTTP 路由；启动初始化、模型和登录令牌使用替身，不读取本地 `.env`。
- 默认回归不连接业务 MySQL、Redis 或 GPU。单独的后端 CI 使用 Python 3.12、临时 MySQL 8 和 Redis 7；原有前端 CI 使用 Node.js 20，其他离线检查使用 Python 3.11。远端状态以 [GitHub Actions](https://github.com/mxyooR/AILF_open/actions) 为准。

## 已执行检查

| 检查 | 结果 | 覆盖内容 |
| --- | --- | --- |
| TypeScript `tsc --noEmit` | 通过 | 全量前端类型检查 |
| 前端 Jest | 5 个测试文件、32 项通过 | 场景与本地请求 10 项、异步命令 5 项、工作流画布 / 节点编辑 / 图关系回归 17 项 |
| 后端 `unittest` | 19 项通过 | 13 项运行时测试；6 项配置与凭据启动约定测试 |
| 后端工作流与实体回归 | 59 项通过，5 项集成测试默认跳过 | 两个仓库均执行；包含 HTTP 表单到动态 API 落库、旧实例拦截、类型与 DDL 规划、Redis 故障恢复 |
| 开源扫描器 `unittest` | 4 项通过 | 规则、值隐藏、禁止文件，以及工作区已清理但暂存区仍有凭据的情况 |
| 前端生产构建 | 完整应用与 Pages 演示模式均通过 | 使用 CRACO 构建，完整应用约 26.2 MiB；关闭 source map，保留旧代码的 ESLint、Autoprefixer、Browserslist 等警告 |
| 两份 Compose 配置 | `config --quiet` 通过 | 默认应用及独立前端演示；仅注入临时合成测试凭据 |
| 改动的 Python / JSON | 解析通过 | Python AST 解析、JSON 解析，不执行历史集成脚本 |
| Git 空白检查 | 通过 | `git diff --check` |

运行时测试包含：任务查询凭据隔离与摘要存储、并发和未完成任务容量限制、排队与执行超时、异常详情隐藏、上下文快照、关闭前尚未开始的任务、跨运行时共享结果、轮询不续期、完成结果优先淘汰、Redis 故障冷却、慢读与本地状态更新的竞争，以及配置边界。

新增后端回归验证工作流配置保留、真实入口和终点、表单提交及业务失败、并发重复提交、旧页面实例隔离、嵌套参数与通知、实体默认值与类型转换、事务回滚、物理表变更规划，以及 Redis 版本比较、TTL 和容量边界。新增代码中的中文注释说明数据流和处理顺序，详见[后端修复文档](BACKEND_RELIABILITY.md)。

## 浏览器交互

在生产构建的 `/demo` 页面，通过 Playwright 实际检查：

- 铁路：修改出发地和席别后查询，结果更新；选择 G101 后出现本地完成提示。
- 商品：修改排序后价格降序生效；选择商品出现完成提示。
- 门诊：切换下午时段后显示 14:00 起的结果；选择时段出现完成提示。
- Schema 视图可展开；三个场景均使用真实 AMIS 渲染器。
- 桌面宽度 1440 像素与手机视口 390 × 844 像素均可操作，手机页面无横向溢出。
- 上述演示操作未观察到页面未捕获异常或 `/api/` 请求。
- Siri 首页复用原有光球和极光组件；快捷示例、文字输入、弹窗条件查询、选择、Schema 与 Escape 返回均通过桌面 / 手机验证。
- 浏览器语音使用测试替身触发识别结果、结束、权限拒绝与不支持的分支，验证输入和回退行为；未调用真实麦克风或识别服务。

最终构建再次验证了三个场景的选择、Schema 视图和手机交互。README 中的[桌面截图](../screenshots/demo-desktop.png)与[手机截图](../screenshots/demo-mobile.png)来自本地合成演示。

另以 `PUBLIC_URL=/AILF_open`、`REACT_APP_DEMO_ONLY=true` 构建 Pages 模式，用静态文件服务复现仓库子路径。已验证资源无 404、页内锚点跳转与刷新、业务选择、Schema 视图和手机布局；该模式不加载后端入口，也未观察到 `/api/` 请求。

## 开源内容检查

本轮通过完整应用 `/config` 读取已有的购票、退票和改签工作流，打开改签画布与 API / 通知节点配置，验证实际详情加载与抽屉展示；未提交业务配置修改。真实首页、手机首页、场景配置、流程列表、画布与节点配置截图已单独记录。管理员账号、密码和 Token 不包含在截图中。

工作流编辑的自动回归覆盖画布生命周期、修改保存、合法零坐标、删除关系清理、空图保存、多画布隔离、连线去重与重连、出边顺序、过期异步响应、串行重绘、参数 JSON 提示与通知类型初始化。DOM 测试不依赖原生 Canvas；这不属于图形像素或后端执行测试。

当前文件扫描与提交前的实际暂存区扫描用于检查常见 provider key、签名 JWT、私钥、个人标识、绝对本地路径和禁止发布的文件类型。匹配值不会输出到扫描日志。旧的个人资料、账号状态与运行监控截图已从当前版本移除。

历史扫描发现原始提交中的两条过期 JWT，过期日期为 2025-07-30 与 2025-08-04。当前版本改为从本地环境读取测试 Token；包含这两条测试 Token 的原始提交仍保留，历史扫描仍会报告它们。详细边界见 [SECURITY.md](../SECURITY.md)。

## 未覆盖的验证

本次未执行完整 GPU 模型加载、真实 MySQL 业务读写、实际 Redis / Celery 故障演练、容器镜像构建、完整业务集成或并发压力测试。未测量模型准确率、P95 时延、吞吐量或任何相对提升。

命令并发限制属于单进程编排；内存状态不跨实例共享，进程重启不自动重放任务。等待超时不等于撤销已经派发的模型作业。这些边界及后续方向见[架构文档](ARCHITECTURE.md)。

## 复查命令

```bash
pnpm typecheck
pnpm test
pnpm build
python -m unittest discover -s backend/tests/unit -v
python -m unittest discover -s backend/tests/regression -v
python -m unittest discover -s scripts/tests -v
python scripts/check_public_repo.py
python scripts/check_public_repo.py --staged
git diff --check
docker compose config --quiet
docker compose -f docker-compose.demo.yml config --quiet
```

已有环境可以直接调用其中的 TypeScript / CRACO / Python 入口。Windows 隐藏目录下运行 CRA 测试时，如自动发现用例失败，可显式传入 `--testMatch '**/src/**/*.test.js'`。不要为离线验证直接运行整个旧 `backend/tests/`，其中有依赖服务或会写数据的脚本。
