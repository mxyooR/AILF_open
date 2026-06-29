# AMIS 知识库总结

## 📚 AMIS 框架概述

### 什么是 AMIS？
AMIS 是百度开源的一个**低代码前端框架**，通过 **JSON 配置**即可生成各类页面，无需编写前端代码。

### 核心特点
1. **低代码**: 使用 JSON 配置而非代码
2. **组件丰富**: 内置 120+ 组件
3. **开箱即用**: 无需学习前端技术栈
4. **长期稳定**: 配置不受前端技术更新影响
5. **可视化编辑**: 支持可视化页面编辑器

---

## 🎯 核心概念

### 1. Schema（配置）
AMIS 的基本配置结构：
```json
{
  "type": "组件类型",
  "属性1": "值1",
  "属性2": "值2"
}
```

**最简单的配置示例**：
```json
{
  "type": "page",
  "body": "Hello World!"
}
```

### 2. 组件树
通过嵌套的 JSON 结构构建页面：
```json
{
  "type": "page",
  "body": {
    "type": "form",
    "body": [
      {"type": "input-text", "name": "username"},
      {"type": "input-password", "name": "password"}
    ]
  }
}
```

### 3. 数据域与数据链
- **数据域**: 每个组件都有自己的数据存储区域
- **数据链**: 子组件可以访问父组件的数据
- **变量引用**: 使用 `${变量名}` 语法

### 4. 模板引擎
支持多种模板语法：
- 变量输出: `${username}`
- 条件判断: `${IF(age > 18, '成年', '未成年')}`
- 循环: `${ARRAYMAP(items, item => item.name)}`
- 过滤器: `${date | date:'YYYY-MM-DD'}`

### 5. 表达式系统
- 模板表达式: `${expression}`
- 公式表达式: `${= expression}`
- 条件表达式: `${IF(condition, true, false)}`
- 内置函数: IF, AND, OR, SUM, AVG, COUNT 等

### 6. 联动机制
- **显隐联动**: `visibleOn`, `hiddenOn`
- **禁用联动**: `disabledOn`
- **数据联动**: 一个组件变化影响另一个组件
- **选项联动**: 下拉框选项动态变化

### 7. 事件动作
通过 `onEvent` 监听事件，通过 `actions` 执行动作：
```json
{
  "type": "button",
  "label": "点击",
  "onEvent": {
    "click": {
      "actions": [
        {"actionType": "toast", "args": {"msg": "成功"}}
      ]
    }
  }
}
```

---

## 🧩 组件分类

### 布局组件（9个）
| 组件 | 类型 | 说明 |
|------|------|------|
| Page | page | 页面组件，必须的顶级节点 |
| Container | container | 通用容器 |
| Grid | grid | 水平分栏布局 |
| Flex | flex | Flex 弹性布局 |
| Panel | panel | 面板容器 |
| Tabs | tabs | 选项卡 |
| Divider | divider | 分割线 |
| Collapse | collapse | 折叠器 |
| Wrapper | wrapper | 简单包裹容器 |

### 表单组件（15+个）
| 组件 | 类型 | 说明 |
|------|------|------|
| Form | form | 表单容器 |
| InputText | input-text | 文本输入框 |
| InputNumber | input-number | 数字输入框 |
| InputEmail | input-email | 邮箱输入框 |
| InputPassword | input-password | 密码输入框 |
| Textarea | textarea | 多行文本 |
| Select | select | 下拉选择框 |
| Checkboxes | checkboxes | 复选框组 |
| Radios | radios | 单选框组 |
| Switch | switch | 开关 |
| InputDate | input-date | 日期选择器 |
| InputDatetime | input-datetime | 日期时间选择器 |
| InputDateRange | input-date-range | 日期范围 |
| InputFile | input-file | 文件上传 |
| InputImage | input-image | 图片上传 |

### 数据展示组件（7个）
| 组件 | 类型 | 说明 |
|------|------|------|
| CRUD | crud | 增删改查组件 |
| Table | table | 表格组件 |
| List | list | 列表组件 |
| Cards | cards | 卡片组件 |
| Chart | chart | 图表组件（ECharts） |
| Service | service | 功能型容器 |
| Pagination | pagination | 分页组件 |

### 功能组件（10个）
| 组件 | 类型 | 说明 |
|------|------|------|
| Action | action | 行为按钮 |
| Button | button | 普通按钮 |
| Dialog | dialog | 弹窗 |
| Drawer | drawer | 抽屉 |
| Toast | toast | 轻提示 |
| Alert | alert | 提示框 |
| Nav | nav | 导航菜单 |
| Wizard | wizard | 向导 |
| Carousel | carousel | 轮播图 |
| IFrame | iframe | 内嵌页面 |

---

## 💼 典型应用场景

### 1. 用户管理系统
**功能**: 用户列表、新增、编辑、删除、搜索、批量操作
**核心组件**: CRUD, Form, Dialog, Button

### 2. 数据仪表盘
**功能**: 统计卡片、图表展示、数据概览
**核心组件**: Grid, Panel, Chart, Service

### 3. 表单向导
**功能**: 多步骤表单、数据收集、步骤验证
**核心组件**: Wizard, Form, 各种输入组件

### 4. 复杂表单
**功能**: 多标签页、文件上传、富文本编辑
**核心组件**: Form, Tabs, InputImage, InputRichText

### 5. 数据列表
**功能**: 数据展示、排序、筛选、分页
**核心组件**: CRUD, Table, Filter, Pagination

---

## 🔑 关键特性

### 1. 表单功能
- **三种展示模式**: normal, horizontal, inline
- **完整校验系统**: 必填、格式、长度、正则等
- **数据初始化**: initApi 加载初始数据
- **提交处理**: api 提交数据，支持异步
- **联动控制**: 字段间相互影响

### 2. CRUD 功能
- **数据加载**: api 接口获取数据
- **搜索过滤**: filter 配置搜索表单
- **批量操作**: bulkActions 批量处理
- **单条操作**: 编辑、删除、查看等
- **分页**: 自动分页处理
- **排序**: 列排序功能
- **导出**: 支持 CSV、Excel 导出

### 3. 数据交互
- **初始化接口**: initApi
- **提交接口**: api
- **异步接口**: asyncApi
- **轮询**: interval 定时刷新
- **WebSocket**: ws 实时通信

### 4. 动作类型
- **ajax**: 发送请求
- **dialog**: 打开弹窗
- **drawer**: 打开抽屉
- **toast**: 显示提示
- **reload**: 刷新组件
- **link**: 页面跳转
- **submit**: 提交表单
- **reset**: 重置表单

---

## 📊 数据格式

### API 请求格式
```json
{
  "method": "get|post|put|delete",
  "url": "/api/endpoint",
  "data": {},
  "headers": {}
}
```

### API 响应格式
```json
{
  "status": 0,
  "msg": "success",
  "data": {}
}
```

### CRUD 数据格式
```json
{
  "status": 0,
  "msg": "success",
  "data": {
    "items": [],
    "total": 100
  }
}
```

---

## 🎨 样式定制

### 1. CSS 类名
通过 `className` 属性添加自定义类名

### 2. 内联样式
通过 `style` 属性添加内联样式

### 3. CSS 变量
通过 `cssVars` 自定义 CSS 变量：
```json
{
  "cssVars": {
    "--primary-color": "#007bff"
  }
}
```

### 4. 工具类
AMIS 提供了丰富的工具类：
- 边距: m-t, m-r, m-b, m-l, p-t, p-r, p-b, p-l
- 对齐: text-center, text-right, text-left
- 颜色: text-primary, text-success, bg-primary 等

---

## 🚀 最佳实践

### 1. 组件选择
- 简单展示用 `tpl`
- 数据列表用 `crud` 或 `table`
- 表单用 `form`
- 布局用 `grid` 或 `flex`
- 容器用 `panel` 或 `container`

### 2. 数据管理
- 使用 `initApi` 初始化数据
- 使用数据域共享数据
- 使用 `source` 动态加载选项
- 使用数据映射转换数据

### 3. 交互设计
- 使用 `dialog` 处理复杂操作
- 使用 `drawer` 展示详情
- 使用 `toast` 反馈操作结果
- 使用 `confirmText` 确认危险操作

### 4. 性能优化
- 使用 `loadDataOnce` 一次性加载
- 使用 `silentPolling` 静默轮询
- 使用 `defer` 延迟加载
- 合理使用 `initFetch`

---

## 📝 常用代码片段

### 登录表单
```json
{
  "type": "form",
  "api": "/api/login",
  "body": [
    {"type": "input-text", "name": "username", "label": "用户名", "required": true},
    {"type": "input-password", "name": "password", "label": "密码", "required": true}
  ]
}
```

### 用户列表
```json
{
  "type": "crud",
  "api": "/api/users",
  "columns": [
    {"name": "id", "label": "ID"},
    {"name": "name", "label": "姓名"},
    {"name": "email", "label": "邮箱"}
  ]
}
```

### 统计卡片
```json
{
  "type": "grid",
  "columns": [
    {
      "body": {
        "type": "panel",
        "body": {
          "type": "tpl",
          "tpl": "<h2>${count}</h2><p>总数</p>"
        }
      }
    }
  ]
}
```

---

## 🎓 学习资源

### 官方资源
- [AMIS 官方文档](https://aisuda.bce.baidu.com/amis/zh-CN/docs/index)
- [AMIS GitHub](https://github.com/baidu/amis)
- [可视化编辑器](https://aisuda.github.io/amis-editor-demo/)

### 本知识库
- `core_concepts.py`: 核心概念
- `components_*.py`: 各类组件详解
- `examples.py`: 完整示例
- `dataset_builder.py`: 数据集生成

---

## ✅ 知识点检查清单

### 基础概念
- [x] 理解 AMIS 是什么
- [x] 掌握 Schema 配置结构
- [x] 理解组件树概念
- [x] 掌握数据域和数据链
- [x] 理解模板引擎
- [x] 掌握表达式系统

### 组件使用
- [x] 掌握 Page 组件
- [x] 掌握 Form 组件及各种输入控件
- [x] 掌握 CRUD 组件
- [x] 掌握 Table 组件
- [x] 掌握 Dialog/Drawer 组件
- [x] 掌握布局组件（Grid, Flex）

### 高级功能
- [x] 掌握事件动作系统
- [x] 掌握组件联动
- [x] 掌握数据映射
- [x] 掌握 API 交互
- [x] 掌握表单校验
- [x] 掌握样式定制

### 实战应用
- [x] 能创建用户管理系统
- [x] 能创建数据仪表盘
- [x] 能创建复杂表单
- [x] 能创建多步骤向导
- [x] 能处理数据交互
- [x] 能实现组件联动

---

## 🎯 总结

AMIS 是一个功能强大的低代码框架，通过 JSON 配置即可快速构建各类中后台页面。其核心优势在于：

1. **简单易用**: 无需前端知识，JSON 配置即可
2. **功能完整**: 120+ 组件覆盖各种场景
3. **稳定可靠**: 百度内部 6 年实战验证
4. **持续更新**: 不断优化和新增功能
5. **灵活扩展**: 支持自定义组件

适用于各类中后台管理系统、数据展示平台、表单密集型应用等场景。

---

**知识库版本**: 1.0.0  
**最后更新**: 2024  
**维护者**: AILF Team
