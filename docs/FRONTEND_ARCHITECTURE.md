# AILF 前端架构文档

## 📋 概述

AILF前端架构分为两个核心部分：
1. **开发者配置界面** - 用于业务场景配置的管理后台
2. **最终用户界面** - 基于amis schema的动态生成界面

## 🏗️ 整体架构

```
AILF Frontend
├── Developer Config Panel (开发者配置界面)
│   ├── 认证系统
│   ├── 七步骤配置流程
│   └── 可视化设计器
└── End User Interface (最终用户界面)
    ├── AI语音交互
    ├── 动态amis页面
    ├── 实时数据展示
    └── 工作流执行界面
```

## 🔧 开发者配置界面架构

### 技术栈
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **状态管理**: React Context + useState/useReducer
- **路由**: React Router 6
- **HTTP客户端**: Axios
- **可视化**: React Flow (工作流) + AntV G6 (关系图) + Formily (表单)

### 目录结构
```
frontend/src/
├── components/
│   ├── developer/                 # 开发者配置组件
│   │   ├── auth/                 # 认证相关
│   │   │   ├── AuthPanel.tsx
│   │   │   └── TokenVerifier.tsx
│   │   ├── scenario/             # 场景配置
│   │   │   ├── ScenarioConfigPanel.tsx
│   │   │   ├── TemplateSelector.tsx
│   │   │   └── ScenarioValidator.tsx
│   │   ├── entity/               # 实体建模
│   │   │   ├── EntityModeler.tsx
│   │   │   ├── EntityCanvas.tsx
│   │   │   ├── EntityEditor.tsx
│   │   │   ├── FieldEditor.tsx
│   │   │   └── RelationshipEditor.tsx
│   │   ├── workflow/             # 工作流设计
│   │   │   ├── WorkflowDesigner.tsx
│   │   │   ├── WorkflowCanvas.tsx
│   │   │   ├── StepPalette.tsx
│   │   │   ├── StepEditor.tsx
│   │   │   └── ConditionEditor.tsx
│   │   ├── form/                 # 表单配置
│   │   │   ├── FormDesigner.tsx
│   │   │   ├── FormCanvas.tsx
│   │   │   ├── FieldPalette.tsx
│   │   │   ├── FieldEditor.tsx
│   │   │   └── FormPreview.tsx
│   │   ├── api/                  # API配置
│   │   │   ├── ApiRoutePanel.tsx
│   │   │   ├── ApiEditor.tsx
│   │   │   └── ApiTester.tsx
│   │   ├── role/                 # 角色管理
│   │   │   ├── RoleManagementPanel.tsx
│   │   │   ├── RoleEditor.tsx
│   │   │   └── PermissionMatrix.tsx
│   │   ├── permission/           # 权限配置
│   │   │   ├── PermissionPanel.tsx
│   │   │   ├── PermissionEditor.tsx
│   │   │   └── PermissionVisualizer.tsx

│   └── enduser/                  # 最终用户组件
│       ├── AIInterface.tsx       # AI交互界面
│       ├── VoiceInput.tsx        # 语音输入
│       ├── AmisRenderer.tsx      # amis渲染器
│       └── WorkflowExecutor.tsx  # 工作流执行器
├── pages/
│   ├── DeveloperConfig.tsx       # 开发者配置主页
│   ├── EntityModeling.tsx        # 实体建模页面
│   ├── WorkflowDesign.tsx        # 工作流设计页面
│   ├── FormDesign.tsx            # 表单设计页面
│   └── EndUserApp.tsx            # 最终用户应用
├── hooks/
│   ├── useAuth.ts                # 认证钩子
│   ├── useScenario.ts            # 场景管理钩子
│   ├── useEntity.ts              # 实体管理钩子
│   ├── useWorkflow.ts            # 工作流管理钩子
│   ├── useForm.ts                # 表单管理钩子
│   └── useAmis.ts                # amis集成钩子
├── services/
│   ├── api.ts                    # API服务
│   ├── auth.ts                   # 认证服务
│   ├── scenario.ts               # 场景服务
│   ├── entity.ts                 # 实体服务
│   ├── workflow.ts               # 工作流服务
│   ├── form.ts                   # 表单服务
│   └── amis.ts                   # amis服务
├── types/
│   ├── auth.ts                   # 认证类型定义
│   ├── scenario.ts               # 场景类型定义
│   ├── entity.ts                 # 实体类型定义
│   ├── workflow.ts               # 工作流类型定义
│   ├── form.ts                   # 表单类型定义
│   └── amis.ts                   # amis类型定义
└── utils/
    ├── validation.ts             # 验证工具
    ├── schema-generator.ts       # schema生成工具
    └── amis-helper.ts            # amis辅助工具
```

### 八步骤配置流程

#### 1. 场景配置 (ScenarioConfigPanel)
```typescript
interface ScenarioStep {
  // 基本信息配置
  name: string;
  type: string;
  description: string;
  // 模板选择
  template?: string;
  // 自定义配置
  customizations?: Record<string, any>;
}
```

#### 2. 实体建模 (EntityModeler)
```typescript
interface EntityModelingStep {
  // 实体设计
  entities: BusinessEntity[];
  // 关系设计
  relationships: EntityRelationship[];
  // 可视化画布状态
  canvasState: {
    nodes: EntityNode[];
    edges: RelationshipEdge[];
  };
}
```

#### 3. 工作流设计 (WorkflowDesigner)
```typescript
interface WorkflowDesignStep {
  // 工作流定义
  workflows: WorkflowDefinition[];
  // 画布状态
  canvasState: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  };
  // 步骤配置
  stepConfigs: Record<string, StepConfig>;
}
```

#### 4. 表单配置 (FormDesigner)
```typescript
interface FormDesignStep {
  // 表单定义
  forms: DynamicForm[];
  // 字段配置
  fieldConfigs: FormFieldConfig[];
  // 布局配置
  layoutConfigs: FormLayoutConfig[];
}
```

#### 5-8. API/角色/权限/生成 (现有流程)

### 核心组件设计

#### EntityModeler 组件
```typescript
const EntityModeler: React.FC = () => {
  const [entities, setEntities] = useState<BusinessEntity[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [canvasNodes, setCanvasNodes] = useState<Node[]>([]);
  const [canvasEdges, setCanvasEdges] = useState<Edge[]>([]);

  // 实体CRUD操作
  const handleCreateEntity = (entity: BusinessEntity) => { /* ... */ };
  const handleUpdateEntity = (id: string, updates: Partial<BusinessEntity>) => { /* ... */ };
  const handleDeleteEntity = (id: string) => { /* ... */ };

  // 关系管理
  const handleCreateRelationship = (relationship: EntityRelationship) => { /* ... */ };
  const handleUpdateRelationship = (id: string, updates: Partial<EntityRelationship>) => { /* ... */ };

  // 画布交互
  const onNodesChange = useCallback((changes: NodeChange[]) => { /* ... */ }, []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => { /* ... */ }, []);

  return (
    <div className="entity-modeler">
      <EntityCanvas
        nodes={canvasNodes}
        edges={canvasEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeSelect={setSelectedEntity}
      />
      <EntityEditor
        entity={selectedEntity ? entities.find(e => e.id === selectedEntity) : null}
        onSave={handleUpdateEntity}
        onDelete={handleDeleteEntity}
      />
    </div>
  );
};
```

#### WorkflowDesigner 组件
```typescript
const WorkflowDesigner: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // React Flow 配置
  const nodeTypes = useMemo(() => ({
    start: StartNode,
    end: EndNode,
    form: FormNode,
    api: ApiNode,
    condition: ConditionNode,
    approval: ApprovalNode,
    notification: NotificationNode,
  }), []);

  return (
    <div className="workflow-designer">
      <StepPalette />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
      <StepEditor
        selectedNode={selectedNode}
        onUpdate={handleStepUpdate}
      />
    </div>
  );
};
```

## 🎨 最终用户界面架构

### amis Schema 生成流程

#### 1. 配置转换为Schema
```typescript
interface SchemaGenerator {
  // 实体转换为CRUD页面
  generateEntityCRUD(entity: BusinessEntity): AmisSchema;
  
  // 工作流转换为表单流程
  generateWorkflowForm(workflow: WorkflowDefinition): AmisSchema;
  
  // 表单配置转换为amis表单
  generateForm(form: DynamicForm): AmisSchema;
  
  // 完整页面生成
  generatePage(scenario: ScenarioConfig): AmisSchema;
}
```

#### 2. 动态Schema示例
```typescript
// 商品管理页面Schema生成
const generateProductCRUDSchema = (productEntity: BusinessEntity): AmisSchema => {
  return {
    type: "page",
    title: "商品管理",
    body: [
      {
        type: "crud",
        api: "/api/entities/product/data",
        columns: productEntity.fields.map(field => ({
          name: field.name,
          label: field.displayName,
          type: getAmisFieldType(field.type)
        })),
        headerToolbar: [
          {
            type: "button",
            label: "新增商品",
            actionType: "dialog",
            dialog: {
              title: "新增商品",
              body: {
                type: "form",
                api: "POST:/api/entities/product/data",
                body: generateFormFields(productEntity.fields)
              }
            }
          }
        ]
      }
    ]
  };
};
```

### AI交互界面

#### VoiceInput 组件
```typescript
const VoiceInput: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  
  const startListening = () => {
    // 启动语音识别
    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.onresult = (event: any) => {
      const command = event.results[0][0].transcript;
      handleVoiceCommand(command);
    };
    recognition.start();
  };

  const handleVoiceCommand = async (command: string) => {
    try {
      const response = await api.post('/api/command', { command });
      const schema = response.data.data.schema;
      // 渲染动态界面
      renderAmisSchema(schema);
    } catch (error) {
      console.error('AI命令处理失败:', error);
    }
  };

  return (
    <div className="voice-input">
      <Button
        type="primary"
        shape="circle"
        size="large"
        icon={<AudioOutlined />}
        className={`voice-button ${isListening ? 'listening' : ''}`}
        onClick={startListening}
      />
      {transcript && (
        <div className="transcript">{transcript}</div>
      )}
    </div>
  );
};
```

### amis集成服务

#### AmisRenderer 组件
```typescript
const AmisRenderer: React.FC<{ schema: AmisSchema }> = ({ schema }) => {
  const amisEnv = useMemo(() => ({
    // API请求拦截
    fetcher: async (api: string, data?: any, options?: any) => {
      const response = await axios.request({
        url: api,
        method: options?.method || 'GET',
        data: data,
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });
      return {
        status: response.status,
        msg: response.data.message,
        data: response.data.data
      };
    },
    
    // 文件上传
    updateLocation: (location: string) => {
      window.history.pushState({}, '', location);
    },
    
    // 主题配置
    theme: 'cxd'
  }), []);

  return (
    <div className="amis-renderer">
      {render(schema, {}, amisEnv)}
    </div>
  );
};
```

## 🔄 前后端数据流

### 开发者配置流程
```
1. 前端配置 → POST /api/scenario → 后端保存配置
2. 前端实体设计 → POST /api/entities → 后端创建实体定义
3. 前端工作流设计 → POST /api/workflow → 后端创建工作流定义
4. 前端表单设计 → POST /api/forms → 后端创建表单配置
5. 前端代码生成 → POST /api/generate-complete → 后端生成完整系统
```

### 最终用户使用流程
```
1. 用户语音输入 → POST /api/command → AI处理 → 返回amis schema
2. 前端渲染schema → amis组件 → 动态界面
3. 用户操作界面 → API调用 → 后端处理 → 返回数据
4. 工作流触发 → POST /api/workflow/{id}/execute → 后端执行流程
```

## 🎯 关键特性

### 1. 响应式设计
- 支持桌面端和移动端
- 自适应布局
- 触摸友好的交互

### 2. 实时协作
- WebSocket连接
- 多用户同时配置
- 实时状态同步

### 3. 可视化设计
- 拖拽式操作
- 所见即所得
- 实时预览

### 4. 智能提示
- AI辅助配置
- 自动补全
- 错误提示

### 5. 性能优化
- 懒加载组件
- 虚拟滚动
- 缓存策略

这个前端架构为AILF提供了完整的开发者配置界面和最终用户界面，通过amis schema实现了配置驱动的动态界面生成。
