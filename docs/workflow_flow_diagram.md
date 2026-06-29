# AILF 工作流处理流程图

## 概述

AILF 系统有两个主要的 API 端点来处理用户请求：
1. `/api/v1/ai/command` - 处理用户的语音/文本命令
2. `/api/v1/workflow/state` - 处理工作流状态转换

## 核心工作流程（用户点击下一步）

当 AI 生成一个工作流界面后，用户点击"下一步"按钮的完整流程：

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端(AMIS)
    participant B as 后端
    participant AI as AI模型
    participant S as 会话服务

    U->>F: 1. 说"我要买火车票"
    F->>B: 2. POST /api/v1/ai/command
    B->>AI: 3. 生成工作流入口界面
    AI-->>B: 4. 返回 AMIS Schema (含 workflow_id, node_id)
    B->>S: 5. 创建工作流会话
    B-->>F: 6. 返回 AMIS Schema
    F->>F: 7. 渲染表单界面
    
    U->>F: 8. 填写表单，点击"下一步"
    F->>B: 9. POST /api/v1/workflow/state<br/>{workflow_id, node_id, action, ...表单数据}
    B->>S: 10. 更新会话数据
    B->>S: 11. 计算下一步节点 (get_next_step)
    B->>AI: 12. 生成下一步界面
    AI-->>B: 13. 返回下一步 AMIS Schema
    B->>S: 14. 更新会话到下一步
    B-->>F: 15. 返回新的 AMIS Schema
    F->>F: 16. 渲染新界面
    
    Note over U,S: 重复步骤 8-16 直到工作流结束
```

## 流程图

### 1. 整体架构流程

```mermaid
flowchart TB
    subgraph 用户交互
        A[用户输入命令/语音]
        B[用户提交工作流表单]
    end
    
    subgraph API层
        C["/api/v1/ai/command"]
        D["/api/v1/workflow/state"]
    end
    
    subgraph 服务层
        E[ai_service_simple]
        F[workflow_session_service]
        G[workflow_service]
        H[ai_amis_service]
    end
    
    subgraph AI模型层
        I[graph_ai_model_service]
    end
    
    A --> C
    B --> D
    C --> E
    D --> F
    D --> G
    D --> H
    E --> F
    E --> G
    E --> H
    H --> I
```

### 2. `/api/v1/ai/command` 详细流程

```mermaid
flowchart TD
    A[接收用户命令] --> B{用户是否登录?}
    
    B -->|否| C[生成登录界面]
    C --> Z[返回 AMIS Schema]
    
    B -->|是| D{是否是工作流推进命令?}
    
    D -->|是| E[_handle_workflow_continue]
    E --> F{用户是否有活跃会话?}
    
    F -->|否| G[按普通命令处理]
    F -->|是| H[获取当前会话]
    
    H --> I[提取表单数据]
    I --> J[更新会话数据]
    J --> K[计算下一步 get_next_step]
    
    K --> L{下一步是什么?}
    L -->|end| M[结束会话,返回完成界面]
    L -->|节点ID| N[更新会话到下一步]
    
    N --> O[生成下一步界面]
    O --> Z
    M --> Z
    
    D -->|否| G
    G --> P[获取可访问API和工作流]
    P --> Q[构建数据集格式输入]
    Q --> R[调用 AI 生成 Schema]
    R --> S[检查是否需要创建工作流会话]
    S --> Z
```

### 3. `/api/v1/workflow/state` 详细流程

```mermaid
flowchart TD
    A[接收请求] --> B{workflow_id 和 node_id 是否存在?}
    
    B -->|否| C[返回 400 错误]
    
    B -->|是| D[提取表单数据]
    D --> E{用户是否有活跃会话?}
    
    E -->|否| F[获取工作流详情]
    F --> G[创建新会话]
    G --> H[设置 current_step 为 node_id]
    
    E -->|是| I{会话的 workflow_id 是否匹配?}
    I -->|否| F
    I -->|是| J[使用现有会话]
    
    H --> K[更新会话数据]
    J --> K
    
    K --> L[计算下一步 get_next_step]
    
    L --> M{下一步是什么?}
    M -->|None| N[返回 500 错误]
    M -->|end| O[结束会话,返回完成界面]
    M -->|节点ID| P[更新会话到下一步]
    
    P --> Q[获取用户可访问API]
    Q --> R[构建 AI 提示]
    R --> S[调用 AI 生成下一步界面]
    S --> T[返回 AMIS Schema]
    O --> T
```


### 4. 工作流会话管理流程

```mermaid
flowchart TD
    subgraph 会话生命周期
        A[创建会话] --> B[设置初始步骤]
        B --> C[用户提交表单]
        C --> D[更新会话数据]
        D --> E[计算下一步]
        E --> F{是否结束?}
        F -->|否| C
        F -->|是| G[结束会话]
    end
    
    subgraph get_next_step 逻辑
        H[获取当前节点] --> I{节点是否存在?}
        I -->|否| J[返回第一个节点或 end]
        I -->|是| K{是否有 child_nodes?}
        K -->|是| L[评估条件分支]
        L --> M{条件是否满足?}
        M -->|是| N[返回目标节点]
        M -->|否| O[检查下一个分支]
        O --> M
        K -->|否| P{是否有 nextSteps?}
        P -->|是| Q[返回第一个 nextStep]
        P -->|否| R[返回 end]
    end
```

## 数据流说明

### 请求数据格式

#### `/api/v1/ai/command` 请求
```json
{
    "command": "我要买火车票",
    "context": {
        "business_context": "railway_ticketing",
        "auto_progress": false
    }
}
```

#### `/api/v1/workflow/state` 请求
```json
{
    "workflow_id": "wf_ticket_booking",
    "node_id": "n_select_train",
    "action": "next",
    "departure": "北京",
    "destination": "上海",
    "date": "2025-01-15"
}
```

### 响应数据格式

```json
{
    "status": 0,
    "msg": "success",
    "data": {
        "type": "page",
        "title": "选择车次",
        "body": [
            {
                "type": "form",
                "api": {
                    "method": "POST",
                    "url": "/api/v1/workflow/state",
                    "data": {
                        "workflow_id": "wf_ticket_booking",
                        "node_id": "n_select_train"
                    }
                },
                "body": [...]
            }
        ]
    }
}
```

## AI 生成的表单配置

AI 生成的工作流表单会包含以下关键配置：

```json
{
  "type": "form",
  "title": "选择出发信息",
  "api": {
    "method": "post",
    "url": "/api/v1/workflow/state",
    "data": {
      "workflow_id": "wf_ticket_booking",
      "node_id": "n_select_train",
      "action": "next",
      "&": "$"
    }
  },
  "body": [...表单字段...],
  "actions": [
    {"type": "submit", "label": "下一步", "level": "primary"}
  ]
}
```

关键点：
- `"&": "$"` 是 AMIS 语法，表示把所有表单字段值合并到请求数据中
- `workflow_id` 和 `node_id` 用于后端定位当前工作流和节点
- `action` 指示操作类型（next/submit）

## 注意事项

1. **两个端点的职责不同**：
   - `/api/v1/ai/command`: 处理自然语言命令，可能触发工作流
   - `/api/v1/workflow/state`: 专门处理工作流状态转换（表单提交）

2. **会话管理**：
   - 每个用户同时只能有一个活跃的工作流会话
   - 创建新会话会自动结束旧会话

3. **条件分支**：
   - 支持多种操作符：==, !=, >, <, >=, <=, in, not_in, contains, exists, is_empty 等
   - 条件评估使用累积的表单数据

4. **AI 生成**：
   - 使用图增强大模型生成 AMIS Schema
   - 支持端点验证和修复
   - 必须正确生成 `workflow_id` 和 `node_id`
