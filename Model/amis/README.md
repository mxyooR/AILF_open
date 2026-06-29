# AMIS 知识库

这是一个完整的 AMIS 低代码框架知识库，用于构建训练数据集和知识表示。

## 📚 知识库结构

### 1. 核心概念 (core_concepts.py)
包含 AMIS 的基础概念和核心知识：
- **AmisIntroduction**: AMIS 框架介绍、优势、适用场景
- **SchemaBasics**: Schema 基础知识、配置结构
- **DataScopeAndChain**: 数据域与数据链
- **TemplateEngine**: 模板引擎和过滤器
- **DataMapping**: 数据映射机制
- **Expression**: 表达式系统
- **Linkage**: 组件联动
- **EventAction**: 事件动作系统
- **StyleSystem**: 样式系统

### 2. 布局组件 (components_layout.py)
包含所有布局相关的组件：
- **PageComponent**: 页面组件（顶级节点）
- **ContainerComponent**: 容器组件
- **GridComponent**: 水平分栏布局
- **FlexComponent**: Flex 弹性布局
- **PanelComponent**: 面板组件
- **TabsComponent**: 选项卡组件
- **DividerComponent**: 分割线
- **CollapseComponent**: 折叠器
- **WrapperComponent**: 包裹容器

### 3. 表单组件 (components_form.py)
包含所有表单输入相关的组件：
- **FormComponent**: 表单容器
- **InputTextComponent**: 文本输入框
- **InputNumberComponent**: 数字输入框
- **InputEmailComponent**: 邮箱输入框
- **InputPasswordComponent**: 密码输入框
- **TextareaComponent**: 多行文本
- **SelectComponent**: 下拉选择框
- **CheckboxesComponent**: 复选框组
- **RadiosComponent**: 单选框组
- **SwitchComponent**: 开关
- **DateComponent**: 日期选择器
- **DatetimeComponent**: 日期时间选择器
- **DateRangeComponent**: 日期范围选择器
- **FileComponent**: 文件上传
- **ImageComponent**: 图片上传
- **FormValidation**: 表单校验规则

### 4. 数据展示组件 (components_data.py)
包含所有数据展示相关的组件：
- **CRUDComponent**: 增删改查组件
- **TableComponent**: 表格组件
- **ListComponent**: 列表组件
- **CardsComponent**: 卡片组件
- **ChartComponent**: 图表组件（基于 ECharts）
- **ServiceComponent**: 功能型容器
- **PaginationComponent**: 分页组件

### 5. 功能组件 (components_functional.py)
包含所有功能性组件：
- **ActionComponent**: 行为按钮
- **ButtonComponent**: 普通按钮
- **DialogComponent**: 弹窗
- **DrawerComponent**: 抽屉
- **ToastComponent**: 轻提示
- **AlertComponent**: 提示框
- **NavComponent**: 导航菜单
- **WizardComponent**: 向导
- **CarouselComponent**: 轮播图
- **IFrameComponent**: 内嵌页面

### 6. 完整示例 (examples.py)
包含各种场景的完整配置示例：
- **UserManagementExample**: 用户管理系统
- **DashboardExample**: 数据仪表盘
- **FormWizardExample**: 多步骤注册表单
- **ComplexFormExample**: 复杂商品发布表单

### 7. 数据集构建器 (dataset_builder.py)
用于生成训练数据集：
- **generate_qa_pairs()**: 生成问答对数据集
- **generate_schema_tasks()**: 生成 Schema 生成任务
- **generate_component_examples()**: 生成组件示例
- **generate_training_samples()**: 生成训练样本
- **export_dataset()**: 导出完整数据集

## 🚀 使用方法

### 1. 查看核心概念
```python
from Model.amis.core_concepts import AMIS_CORE_CONCEPTS, get_concept_summary

# 获取概念摘要
summary = get_concept_summary()
print(summary)

# 访问具体概念
intro = AMIS_CORE_CONCEPTS['introduction']
print(intro.advantages)
```

### 2. 查看组件信息
```python
from Model.amis.components_layout import LAYOUT_COMPONENTS
from Model.amis.components_form import FORM_COMPONENTS
from Model.amis.components_data import DATA_COMPONENTS

# 获取 Page 组件信息
page = LAYOUT_COMPONENTS['page']
print(page.properties)
print(page.basic_example)

# 获取 Form 组件信息
form = FORM_COMPONENTS['form']
print(form.mode_types)
```

### 3. 查看完整示例
```python
from Model.amis.examples import AMIS_EXAMPLES, get_all_examples

# 获取用户管理示例
user_mgmt = AMIS_EXAMPLES['user_management']
print(user_mgmt.name)
print(user_mgmt.description)
print(user_mgmt.schema)

# 获取所有示例
all_examples = get_all_examples()
```

### 4. 生成数据集
```python
from Model.amis.dataset_builder import DatasetBuilder

# 创建数据集构建器
builder = DatasetBuilder()

# 生成问答对
qa_pairs = builder.generate_qa_pairs()
print(f"生成了 {len(qa_pairs)} 个问答对")

# 生成 Schema 任务
schema_tasks = builder.generate_schema_tasks()
print(f"生成了 {len(schema_tasks)} 个 Schema 任务")

# 导出完整数据集
dataset = builder.export_dataset("amis_dataset.json")

# 生成训练样本
training_samples = builder.generate_training_samples(100)
```

## 📊 数据集格式

### 问答对格式
```json
{
  "question": "什么是 amis？",
  "answer": "amis 是一个低代码前端框架..."
}
```

### Schema 任务格式
```json
{
  "instruction": "创建一个用户登录表单",
  "output": {
    "type": "page",
    "body": {
      "type": "form",
      ...
    }
  }
}
```

### 组件示例格式
```json
{
  "component": "input-text",
  "description": "文本输入框",
  "schema": {
    "type": "input-text",
    "name": "username",
    ...
  },
  "usage": "用于文本输入框的表单控件"
}
```

## 🎯 知识覆盖

### AMIS 核心知识点
- ✅ 框架介绍和优势
- ✅ Schema 配置结构
- ✅ 组件树和嵌套
- ✅ 数据域与数据链
- ✅ 模板引擎和表达式
- ✅ 数据映射机制
- ✅ 组件联动
- ✅ 事件动作系统
- ✅ 样式系统

### 组件覆盖（120+ 组件）
- ✅ 布局组件（9 个）
- ✅ 表单组件（15+ 个）
- ✅ 数据展示组件（7 个）
- ✅ 功能组件（10 个）

### 应用场景
- ✅ 用户管理系统
- ✅ 数据仪表盘
- ✅ 表单向导
- ✅ 复杂表单
- ✅ CRUD 应用
- ✅ 数据可视化

## 📝 数据集统计

通过 `dataset_builder.py` 可以生成：
- **问答对**: 30+ 个基础问答
- **Schema 任务**: 5+ 个完整页面生成任务
- **组件示例**: 8+ 个常用组件示例
- **训练样本**: 可生成任意数量的混合训练样本

## 🔧 扩展方法

### 添加新的问答对
在 `dataset_builder.py` 的 `generate_qa_pairs()` 方法中添加：
```python
qa_pairs.append({
    "question": "新问题",
    "answer": "新答案"
})
```

### 添加新的组件
1. 在对应的组件文件中创建新的 dataclass
2. 添加到导出字典中
3. 更新摘要函数

### 添加新的示例
在 `examples.py` 中创建新的示例类：
```python
@dataclass
class NewExample:
    name: str = "示例名称"
    description: str = "示例描述"
    schema: Dict[str, Any] = field(default_factory=lambda: {...})
```

## 📖 参考资源

- [AMIS 官方文档](https://aisuda.bce.baidu.com/amis/zh-CN/docs/index)
- [AMIS GitHub](https://github.com/baidu/amis)
- [AMIS 可视化编辑器](https://aisuda.github.io/amis-editor-demo/)

## 🎓 学习路径

1. **基础概念**: 从 `core_concepts.py` 开始，了解 AMIS 的基本概念
2. **组件学习**: 依次学习布局、表单、数据展示、功能组件
3. **实战示例**: 查看 `examples.py` 中的完整示例
4. **数据集构建**: 使用 `dataset_builder.py` 生成训练数据

## 💡 使用建议

- 用于 AI 模型训练：生成问答对和 Schema 生成任务
- 用于知识检索：快速查找组件属性和用法
- 用于代码生成：参考示例生成 AMIS 配置
- 用于文档生成：自动生成组件文档

## 📄 许可证

本知识库基于 AMIS 官方文档整理，仅用于学习和研究目的。
