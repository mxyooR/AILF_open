# Dataset Generation Project

用于生成 **GNN + LLM 联合训练** 的高质量 JSONL 数据集。

## 项目结构

```
Model/script/
├── __init__.py              # 包初始化
├── scene_loader.py          # 场景加载器 - 加载所有业务场景定义
├── amis_generator.py        # AMIS Schema 生成器 - 生成符合AMIS标准的JSON
├── graph_builder.py         # 图谱上下文构建器 - 构建混合候选池
├── dataset_generator.py     # 主数据集生成器
└── README.md               # 本文档
```

## 核心特性

### 1. 混合图谱 (Mixed Graph Context)

每个样本的 `graph_input.nodes` 包含：
- **1 个正样本**: API 或 Workflow 入口
- **2-3 个同域干扰项**: 同业务下的其他 API/工作流
- **2-3 个跨域干扰项**: 来自其他业务域的 API/工作流
- **1-2 个噪声干扰项**: 游戏、社交等无关领域

### 2. JSONL 格式 (OpenAI Compatible)

每行包含两个顶级字段：

```json
{
  "messages": [
    {"role": "system", "content": "基于图谱上下文生成 Amis JSON。"},
    {"role": "user", "content": "指令：我要挂号\n当前状态：Global_Routing"},
    {"role": "assistant", "content": "{\"type\": \"page\", ...}"}
  ],
  "graph_input": {
    "nodes": [
      {"id": "wf_registration", "type": "workflow", "desc": "门诊挂号流程", "domain": "medical"},
      {"id": "api_dept_list", "type": "api", "desc": "查询科室列表", "domain": "medical"},
      {"id": "api_skin", "type": "api", "desc": "购买皮肤", "domain": "gaming"}
    ],
    "edges": []
  }
}
```

### 3. 任务类型分布

- **Global Routing (40%)**: 全局路由选择，选择正确的 API 或 Workflow
- **Workflow Input (40%)**: 工作流输入阶段，填写表单字段
- **Workflow Execute (20%)**: 工作流执行阶段，API 调用

### 4. 数据来源

- **业务场景**: 从 `Model/scene/` 加载 7 个核心业务域
  - medical (医疗)
  - finance (财务)
  - ecommerce (电商)
  - train_ticket (火车票)
  - logistics (物流)
  - hrm (人力资源)
  - education (教育)

- **AMIS 标准**: 从 `Model/amis/` 获取 AMIS 组件和格式规范

- **噪声域**: gaming (游戏), social (社交), smarthome (智能家居)

## 使用方法

### 1. 安装依赖

```bash
# 无额外依赖，仅需 Python 3.7+
```

### 2. 生成数据集

```bash
cd Model/script
python dataset_generator.py
```

### 3. 自定义参数

编辑 `dataset_generator.py` 中的参数：

```python
generator = DatasetGenerator(output_path="dataset_final.jsonl")
generator.generate_dataset(total_samples=600)  # 修改样本数量
```

### 4. 调整任务分布

修改 `DatasetGenerator` 类中的 `task_distribution`：

```python
self.task_distribution = {
    "global_routing": 0.40,      # 全局路由 40%
    "workflow_input": 0.40,      # 工作流输入 40%
    "workflow_execute": 0.20     # 工作流执行 20%
}
```

## 输出格式

生成的 `dataset_final.jsonl` 文件包含约 600 条样本，每行一个 JSON 对象。

### 示例样本

#### 1. Global Routing 样本

```json
{
  "messages": [
    {"role": "system", "content": "基于图谱上下文生成 Amis JSON。"},
    {"role": "user", "content": "指令：我要报销\n当前状态：Global_Routing"},
    {"role": "assistant", "content": "{\"type\":\"page\",\"title\":\"费用报销\",\"body\":{\"type\":\"form\",...}}"}
  ],
  "graph_input": {
    "nodes": [
      {"id": "wf_claim", "type": "workflow", "desc": "提交费用报销申请", "domain": "finance"},
      {"id": "api_budget", "type": "api", "desc": "查询预算详情", "domain": "finance"},
      {"id": "wf_registration", "type": "workflow", "desc": "门诊挂号流程", "domain": "medical"},
      {"id": "api_skin", "type": "api", "desc": "购买皮肤", "domain": "gaming"}
    ],
    "edges": []
  }
}
```

#### 2. Workflow Input 样本

```json
{
  "messages": [
    {"role": "system", "content": "基于图谱上下文生成 Amis JSON。"},
    {"role": "user", "content": "指令：门诊挂号流程 - 填写患者信息\n当前状态：Workflow_Input\n工作流ID：wf_registration"},
    {"role": "assistant", "content": "{\"type\":\"page\",\"body\":[{\"type\":\"form\",\"body\":[...]}]}"}
  ],
  "graph_input": {
    "nodes": [
      {"id": "wf_registration_node_n_patient_info", "type": "workflow_node", "desc": "填写患者信息", "domain": "medical"},
      {"id": "wf_registration_node_n_patient_info_field_patient_name", "type": "field", "name": "patient_name", "label": "患者姓名", "field_type": "string", "required": true},
      {"id": "wf_registration_node_n_patient_info_field_patient_id_card", "type": "field", "name": "patient_id_card", "label": "身份证号", "field_type": "string", "required": true}
    ],
    "edges": [
      {"source": "wf_registration_node_n_patient_info", "target": "wf_registration_node_n_patient_info_field_patient_name", "relation": "has_field"},
      {"source": "wf_registration_node_n_patient_info", "target": "wf_registration_node_n_patient_info_field_patient_id_card", "relation": "has_field"}
    ]
  }
}
```

## 数据质量保证

### 1. 图谱混合性
- ✅ 每个样本包含多种类型的节点（API + Workflow）
- ✅ 包含同域和跨域干扰项
- ✅ 包含噪声域干扰项

### 2. AMIS 标准符合性
- ✅ 所有 `assistant` 响应都是有效的 AMIS JSON Schema
- ✅ 使用正确的组件类型（page, form, input-text, select 等）
- ✅ 包含必要的属性（type, name, label, required 等）

### 3. 逻辑一致性
- ✅ `assistant` 的响应与 `graph_input` 中的正样本匹配
- ✅ 不生成图中不存在的节点内容
- ✅ 字段节点与父节点通过边连接

## 统计信息示例

```
=== 数据集统计 ===

任务类型分布:
  Global_Routing: 240 (40.0%)
  Workflow_Input: 240 (40.0%)
  Workflow_Execute: 120 (20.0%)

域分布 (节点级别):
  education: 523
  ecommerce: 531
  finance: 518
  gaming: 89
  hrm: 527
  logistics: 519
  medical: 534
  social: 45
  smarthome: 31
  train_ticket: 528

平均节点数: 7.2
平均边数: 1.8
```

## 扩展说明

### 添加新场景

1. 在 `Model/scene/` 下创建新的场景文件
2. 在 `scene_loader.py` 中导入并注册
3. 重新运行生成器

### 自定义 AMIS 组件

修改 `amis_generator.py` 中的生成方法，添加新的组件类型或样式。

### 调整图谱结构

修改 `graph_builder.py` 中的构建逻辑，调整节点数量或边的关系。

## 注意事项

1. **压缩 JSON**: `assistant` 的响应必须是压缩的 JSON 字符串（无换行和多余空格）
2. **中文支持**: 使用 `ensure_ascii=False` 保证中文正确输出
3. **随机性**: 每次运行生成的数据集略有不同，使用 `random.seed()` 可固定随机种子
4. **内存占用**: 600 条样本约占用 2-3 MB 内存

## License

MIT
