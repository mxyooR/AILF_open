import React, { useState } from 'react';
import WorkflowCanvas from '../components/developer/workflow/WorkflowCanvas';
import { createDemoWorkflow, demoWorkflowRoutes } from './workflowFixture';
import type { WorkflowDefinition } from '../types/developer/workflowTypes';
import './DemoWorkflow.css';

export default function DemoWorkflow() {
  const [workflow, setWorkflow] = useState(createDemoWorkflow);
  const [saved, setSaved] = useState<WorkflowDefinition | null>(null);
  const [showConfig, setShowConfig] = useState(false);
  const [readonly, setReadonly] = useState(false);
  return <div className="demo-workflow">
    <div className="demo-workflow-toolbar">
      <div><strong>门诊时段查询</strong><span>开发者配置视图 · 合成工作流</span></div>
      <div>
        <button aria-pressed={readonly} onClick={() => setReadonly(value => !value)}>{readonly ? '切换为编辑' : '切换为只读'}</button>
        <button onClick={() => { setWorkflow(saved ? JSON.parse(JSON.stringify(saved)) : createDemoWorkflow()); }}>重新加载已保存</button>
        <button onClick={() => { setWorkflow(createDemoWorkflow()); setSaved(null); setShowConfig(false); }}>恢复示例</button>
      </div>
    </div>
    <WorkflowCanvas workflow={workflow} readonly={readonly} availableRoutes={demoWorkflowRoutes} onSave={definition => { setSaved(definition); }} />
    <div className="demo-workflow-status" role="status">
      <span>{saved ? `已保存到当前页面：${saved.nodes.length} 个节点，${saved.nodes.reduce((count, node) => count + node.child_nodes.length, 0)} 条连线。` : '双击节点编辑配置，拖动端点连线，点击连线标签设置条件。'} 刷新页面后恢复示例。</span>
      {saved && <button aria-expanded={showConfig} onClick={() => setShowConfig(value => !value)}>{showConfig ? '收起配置' : '查看保存配置'}</button>}
    </div>
    {saved && showConfig && <pre className="demo-schema" tabIndex={0} aria-label="已保存的工作流配置">{JSON.stringify(saved, null, 2)}</pre>}
  </div>;
}
