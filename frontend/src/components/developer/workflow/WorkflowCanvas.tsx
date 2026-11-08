import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AutoComplete, Button, Drawer, Form, Input, message, Modal, Select, Spin } from 'antd';
import { Canvas } from 'butterfly-dag';
import type { WorkflowDefinition, WorkflowNode, NodeType, TransitionCondition } from '../../../types/developer/workflowTypes';
import { NodeTypeConfigs } from '../../../types/developer/workflowTypes';
import type { APIRoute } from '../../../types/developer/route';
import NodeEditor from './NodeEditor';
import NodePalette from './NodePalette';
import WorkflowButterflyNode from './WorkflowButterflyNode';
import WorkflowButterflyEdge from './WorkflowButterflyEdge';
import { nodeEndpoints, snapshotWorkflowNodes, withWorkflowEdge, withoutWorkflowEdge, withoutWorkflowNode } from './workflowGraph';
import './WorkflowCanvas.css';
import 'butterfly-dag/dist/index.css';

interface WorkflowCanvasProps {
  workflowId?: string;
  workflow?: WorkflowDefinition;
  readonly?: boolean;
  onSave?: (workflow: WorkflowDefinition) => void | Promise<void>;
  onNodeSelect?: (node: WorkflowNode | null) => void;
  /** Inject known routes to edit isolated fixtures without loading backend configuration. */
  availableRoutes?: APIRoute[];
}
interface SelectedEdge { edgeId?: string; source: string; target: string }
const edgeNodeId = (edge: any, side: 'source' | 'target'): string | undefined => {
  const candidate = edge?.[`${side}Node`] ?? edge?.[`${side}NodeId`] ?? edge?.options?.[`${side}Node`];
  return typeof candidate === 'string' ? candidate : candidate?.id ?? candidate?.nodeId;
};
const describeCondition = (condition: TransitionCondition) => condition.description || (
  condition.type === 'expression' ? condition.expression || '表达式条件' : condition.type === 'form_completed' ? '表单完成后执行' : '总是执行'
);

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({ workflowId, workflow, readonly = false, onSave, onNodeSelect, availableRoutes }) => {
  const rootRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<any>(null);
  const workflowRef = useRef<WorkflowDefinition | null>(workflow || null);
  const nodesRef = useRef<WorkflowNode[]>(workflow?.nodes || []);
  const eventRef = useRef<(event: any) => void>(() => {});
  const drawingRef = useRef(0);
  const pendingDrawRef = useRef<any>(null);
  const readonlyRef = useRef(readonly);
  readonlyRef.current = readonly;
  const [nodes, setNodes] = useState(nodesRef.current);
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [editorVisible, setEditorVisible] = useState(false);
  const [selectedEdge, setSelectedEdge] = useState<SelectedEdge | null>(null);
  const [edgeForm] = Form.useForm();

  const commitNodes = useCallback((next: WorkflowNode[]) => {
    nodesRef.current = next;
    if (workflowRef.current) workflowRef.current = { ...workflowRef.current, nodes: next };
    setNodes(next);
    // Update existing visuals without resetting the viewport or dragged positions.
    const canvas = canvasRef.current;
    canvas?.getDataMap().nodes.forEach((visual: any) => {
      const node = next.find(item => item.id === visual.id);
      if (!node) return;
      visual.options = { ...visual.options, nodeData: node, label: node.name, options: { ...visual.options?.options, nodeData: node, label: node.name, name: node.name } };
      const label = visual.dom?.querySelector('.node-label');
      if (label) label.textContent = node.name;
      const caption = visual.dom?.querySelector('.workflow-node-caption')?.textContent || NodeTypeConfigs[node.type].label;
      visual.dom?.setAttribute('aria-label', `${node.name}，${caption}节点`);
      visual.dom?.querySelector('.node-delete-btn')?.setAttribute('aria-label', `删除节点：${node.name}`);
    });
    canvas?.getDataMap().edges.forEach((edge: any) => {
      const source = next.find(node => node.id === edgeNodeId(edge, 'source'));
      const relation = source?.child_nodes?.find(child => child.node_id === edgeNodeId(edge, 'target'));
      if (relation) {
        const label = describeCondition(relation.condition);
        if (edge.label !== label) edge.updateLabel?.(label);
      }
    });
  }, []);
  const visualNode = (node: WorkflowNode) => ({
    id: node.id, left: node.position?.x ?? 100, top: node.position?.y ?? 100,
    Class: WorkflowButterflyNode, endpoints: nodeEndpoints(node.type),
    options: { label: node.name, name: node.name, nodeType: node.type, nodeData: node }
  });
  const drawWorkflow = useCallback((definition: WorkflowDefinition | null) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    workflowRef.current = definition;
    const next = definition?.nodes || [];
    nodesRef.current = next;
    setNodes(next); setSelectedNode(null); setEditorVisible(false); setSelectedEdge(null);
    const ids = new Set(next.map(node => node.id));
    const edges = next.flatMap(node => (node.child_nodes || []).filter(child => ids.has(child.node_id)).map((child, index) => ({
      id: JSON.stringify([node.id, child.node_id]), sourceNode: node.id, targetNode: child.node_id,
      source: node.type === 'condition' && index > 0 ? 'bottom' : 'right', target: 'left',
      type: 'endpoint', Class: WorkflowButterflyEdge, arrow: true, label: describeCondition(child.condition)
    })));
    // Serialize library draws ourselves; coalesce rapid external workflow changes.
    pendingDrawRef.current = { nodes: next.map(visualNode), edges };
    const flush = () => {
      if (canvasRef.current !== canvas) return;
      const data = pendingDrawRef.current;
      if (!data) {
        drawingRef.current = 0; setLoading(false);
        canvas.focusCenterWithAnimate?.({ animate: false });
        return;
      }
      pendingDrawRef.current = null;
      drawingRef.current = 1; setLoading(true);
      canvas.redraw(data, flush);
    };
    if (!drawingRef.current) flush();
  }, []);

  useEffect(() => {
    if (!rootRef.current) return;
    const root = rootRef.current;
    const canvas = new Canvas({
      root, draggable: !readonlyRef.current, linkable: !readonlyRef.current, disLinkable: !readonlyRef.current,
      zoomable: true, moveable: true,
      theme: { edge: { Class: WorkflowButterflyEdge, shapeType: 'AdvancedBezier', arrow: true }, endpoint: { position: ['Left', 'Right', 'Bottom'] } }
    });
    canvasRef.current = canvas;
    const listener = (event: any) => { if (!drawingRef.current && !readonlyRef.current) eventRef.current(event); };
    canvas.on('events', listener); setReady(true);
    return () => {
      canvas.off('events', listener); canvasRef.current = null; pendingDrawRef.current = null;
      const instance = canvas as any;
      instance.removeNodes?.(instance.getDataMap().nodes.map((node: any) => node.id), false, true);
      instance.destroy?.(); root.replaceChildren();
    };
  }, []);
  useEffect(() => {
    const canvas = canvasRef.current;
    canvas?.setDraggable(!readonly); canvas?.setLinkable(!readonly); canvas?.setDisLinkable(!readonly);
    if (readonly) { setEditorVisible(false); setSelectedEdge(null); }
  }, [readonly, ready]);
  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    setFetching(false);
    if (workflow) drawWorkflow(workflow);
    else if (workflowId && workflowId !== 'sample') {
      drawWorkflow(null);
      setFetching(true);
      import('../../../services/developer/workflowAPI').then(({ workflowAPI }) => workflowAPI.getWorkflowDetail(workflowId)).then(response => {
          if (cancelled) return;
          if (response.code === 200 && response.data?.workflow) drawWorkflow(response.data.workflow);
          else message.error(response.message || '加载工作流失败');
        }).catch(() => { if (!cancelled) message.error('加载工作流失败'); })
          .finally(() => { if (!cancelled) setFetching(false); });
    } else drawWorkflow(null);
    return () => { cancelled = true; };
  }, [workflow, workflowId, ready, drawWorkflow]);

  const removeNode = useCallback((id: string, alreadyRemoved = false) => {
    if (readonlyRef.current || !nodesRef.current.some(node => node.id === id)) return;
    // Commit first: removing a visual node also emits incident edge events.
    commitNodes(withoutWorkflowNode(nodesRef.current, id));
    if (!alreadyRemoved) canvasRef.current?.removeNode(id);
    setSelectedNode(current => current?.id === id ? null : current);
    setEditorVisible(false); setSelectedEdge(null); onNodeSelect?.(null);
  }, [commitNodes, onNodeSelect]);
  const removeEdge = (edge: any, alreadyRemoved = false) => {
    const source = edgeNodeId(edge, 'source'); const target = edgeNodeId(edge, 'target');
    if (!source || !target || readonlyRef.current) return;
    commitNodes(withoutWorkflowEdge(nodesRef.current, source, target));
    if (!alreadyRemoved) {
      const edges = [...(canvasRef.current?.getDataMap().edges || [])];
      edges.filter(item => edgeNodeId(item, 'source') === source && edgeNodeId(item, 'target') === target).forEach(item => canvasRef.current?.removeEdge(item.id));
    }
    setSelectedEdge(null);
  };
  const openEdge = (edge: any) => {
    const source = edgeNodeId(edge, 'source'); const target = edgeNodeId(edge, 'target');
    const relation = nodesRef.current.find(node => node.id === source)?.child_nodes?.find(child => child.node_id === target);
    if (!source || !target || !relation || readonlyRef.current) return;
    setSelectedEdge({ edgeId: edge.id, source, target });
    edgeForm.setFieldsValue({ condition_type: relation.condition.type, expression: relation.condition.expression || '', description: relation.condition.description || '' });
  };
  const connectEdge = (edge: any, condition: TransitionCondition = { type: 'always', description: '总是执行' }) => {
    const source = edgeNodeId(edge, 'source'); const target = edgeNodeId(edge, 'target');
    const sourceNode = nodesRef.current.find(node => node.id === source);
    const targetNode = nodesRef.current.find(node => node.id === target);
    if (!sourceNode || !targetNode || source === target || sourceNode.type === 'end' || targetNode.type === 'start') {
      canvasRef.current?.removeEdge(edge.id);
      message.warning('请从前一步的输出端连接到下一步的输入端'); return;
    }
    if (sourceNode.child_nodes?.some(child => child.node_id === target)) {
      const pair = canvasRef.current?.getDataMap().edges.filter((item: any) => edgeNodeId(item, 'source') === source && edgeNodeId(item, 'target') === target) || [];
      if (pair.length > 1) canvasRef.current.removeEdge(edge.id, true);
      return;
    }
    commitNodes(withWorkflowEdge(nodesRef.current, source!, target!, condition));
  };
  eventRef.current = (event: any) => {
    switch (event.type) {
      case 'node:click': {
        const node = nodesRef.current.find(item => item.id === event.node?.id) || null;
        setSelectedNode(node); onNodeSelect?.(node); break;
      }
      case 'canvas:click': setSelectedNode(null); onNodeSelect?.(null); break;
      case 'link:click': case 'edge:click': openEdge(event.edge || event.link); break;
      case 'link:connect': (event.links || [event.link || event.edge]).filter(Boolean).forEach((edge: any) => connectEdge(edge)); break;
      case 'link:delete': case 'link:disconnect': removeEdge(event.link || event.edge, true); break;
      case 'links:delete': (event.links || []).forEach((edge: any) => removeEdge(edge, true)); break;
      case 'link:reconnect': {
        const conditions = (event.delLinks || []).map((edge: any) => nodesRef.current.find(node => node.id === edgeNodeId(edge, 'source'))?.child_nodes?.find(child => child.node_id === edgeNodeId(edge, 'target'))?.condition);
        (event.delLinks || []).forEach((edge: any) => removeEdge(edge, true));
        (event.addLinks || []).forEach((edge: any, index: number) => connectEdge(edge, conditions[index])); break;
      }
      case 'nodes:delete': (event.nodes || []).forEach((node: any) => removeNode(node.id, true)); break;
    }
  };
  useEffect(() => {
    const root = rootRef.current;
    if (!root || readonly) return;
    const editNode = (event: Event) => {
      if (drawingRef.current) return;
      const node = nodesRef.current.find(item => item.id === (event as CustomEvent).detail.nodeId);
      if (node) { setSelectedNode(node); setEditorVisible(true); }
    };
    const deleteNode = (event: Event) => { if (!drawingRef.current) removeNode((event as CustomEvent).detail.nodeId); };
    const edgeEvent = (event: Event) => {
      if (drawingRef.current) return;
      const detail = (event as CustomEvent).detail;
      const edge = { id: detail.edgeId, sourceNode: detail.sourceNode, targetNode: detail.targetNode };
      if (event.type === 'edge-delete') removeEdge(edge); else openEdge(edge);
    };
    root.addEventListener('node-edit', editNode); root.addEventListener('node-delete', deleteNode);
    root.addEventListener('edge-click', edgeEvent); root.addEventListener('edge-delete', edgeEvent);
    return () => {
      root.removeEventListener('node-edit', editNode); root.removeEventListener('node-delete', deleteNode);
      root.removeEventListener('edge-click', edgeEvent); root.removeEventListener('edge-delete', edgeEvent);
    };
  }, [readonly, removeNode, edgeForm, commitNodes]);

  const addNode = (type: string, position?: { x: number; y: number }) => {
    const nodeType = type as NodeType;
    if (readonly || fetching || !NodeTypeConfigs[nodeType] || !canvasRef.current || drawingRef.current) return;
    if ((type === 'start' || type === 'end') && nodesRef.current.some(node => node.type === type)) return;
    const index = nodesRef.current.length;
    const node: WorkflowNode = {
      id: `${type}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: NodeTypeConfigs[nodeType].label, type: nodeType, description: '',
      position: position || { x: 80 + index % 4 * 180, y: 80 + Math.floor(index / 4) * 150 },
      parent_nodes: [], child_nodes: [], outputs: [], config: { ...NodeTypeConfigs[nodeType].defaultConfig }, ai_instructions: { purpose: '', action: '' }
    };
    canvasRef.current.addNode(visualNode(node)); commitNodes([...nodesRef.current, node]);
  };
  const saveNode = (updated: WorkflowNode) => {
    if (readonly || !nodesRef.current.some(node => node.id === updated.id)) return;
    commitNodes(nodesRef.current.map(node => node.id === updated.id ? { ...updated, position: node.position, parent_nodes: node.parent_nodes, child_nodes: node.child_nodes } : node));
    setEditorVisible(false); setSelectedNode(updated);
    message.success('节点已更新，请保存工作流以提交更改');
  };
  const saveWorkflow = async () => {
    if (!onSave || !workflowRef.current || readonly || saving || fetching || drawingRef.current) return;
    const next = snapshotWorkflowNodes(nodesRef.current, canvasRef.current?.getDataMap().nodes);
    const definition = { ...workflowRef.current, nodes: next,
      node_relationships: Object.fromEntries(next.map(node => [node.id, { parents: [...node.parent_nodes], children: node.child_nodes.map(child => child.node_id), conditions: node.child_nodes.map(child => ({ ...child.condition })) }])),
      metadata: { ...workflowRef.current.metadata, updated_at: new Date().toISOString() } };
    setSaving(true);
    try { await onSave(definition); }
    catch { message.error('保存工作流失败，请重试'); }
    finally { if (canvasRef.current) setSaving(false); }
  };
  const fields = useMemo(() => {
    const candidates = new Set((workflowRef.current?.inputs || []).map(input => input.name));
    nodes.forEach(node => {
      candidates.add(`${node.id}_result`); node.outputs?.forEach(output => candidates.add(output.name));
      Array.from(JSON.stringify(node.config || {}).matchAll(/\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g)).forEach(match => candidates.add(match[1]));
    });
    return Array.from(candidates).filter(Boolean).sort();
  }, [nodes]);
  const saveCondition = async () => {
    if (!selectedEdge || readonly) return;
    try {
      const values = await edgeForm.validateFields();
      const condition: TransitionCondition = { type: values.condition_type, description: (values.description || '').trim() };
      if (condition.type === 'expression') condition.expression = values.expression.trim();
      if (!condition.description) condition.description = describeCondition(condition);
      commitNodes(withWorkflowEdge(nodesRef.current, selectedEdge.source, selectedEdge.target, condition)); setSelectedEdge(null);
    } catch { /* Ant Form shows field validation errors. */ }
  };

  return <div className="workflow-canvas-container">
    {!readonly && <div className="workflow-sidebar">
      <NodePalette onNodeDrop={type => addNode(type)} loading={loading || fetching} existingNodes={nodes.map(node => ({ nodeType: node.type, id: node.id }))} />
      {onSave && <div className="workflow-actions"><Button type="primary" block loading={saving} disabled={loading || fetching || !ready || !workflowRef.current} onClick={saveWorkflow}>保存工作流</Button></div>}
      <p className="workflow-editor-help">拖动端点连接步骤，双击节点编辑属性，点击连线标签编辑条件。更改在保存后提交。</p>
    </div>}
    <div className="workflow-canvas-stage">
    <div ref={rootRef} className={`workflow-canvas ${readonly ? 'readonly' : ''}`} aria-label="工作流节点画布"
      onDragOver={event => { if (!readonly) { event.preventDefault(); event.dataTransfer.dropEffect = 'copy'; } }}
      onDrop={event => {
        event.preventDefault(); if (readonly || !canvasRef.current) return;
        const [x, y] = canvasRef.current.terminal2canvas([event.clientX, event.clientY]);
        addNode(event.dataTransfer.getData('application/workflow-node'), { x: Math.round(x), y: Math.round(y) });
      }} />
    <div className="workflow-viewport-tools">
      <Button size="small" onClick={() => canvasRef.current?.zoom(canvasRef.current.getZoom() / 1.2)} aria-label="缩小画布">−</Button>
      <Button size="small" onClick={() => canvasRef.current?.zoom(canvasRef.current.getZoom() * 1.2)} aria-label="放大画布">+</Button>
      <Button size="small" onClick={() => canvasRef.current?.focusCenterWithAnimate({ animate: false })}>居中显示</Button>
    </div>
    {(loading || fetching) && <div className="canvas-loading" role="status" aria-label="正在加载工作流"><Spin /></div>}
    </div>
    <Drawer title="编辑节点" placement="right" width="min(500px, 100vw)" open={editorVisible && !readonly} onClose={() => setEditorVisible(false)} destroyOnHidden>
      {selectedNode && <NodeEditor node={selectedNode} onSave={saveNode} onCancel={() => setEditorVisible(false)} availableRoutes={availableRoutes} />}
    </Drawer>
    <Modal title="编辑连线条件" open={!!selectedEdge && !readonly} onCancel={() => setSelectedEdge(null)} destroyOnHidden footer={[
      <Button key="delete" danger onClick={() => selectedEdge && removeEdge({ sourceNode: selectedEdge.source, targetNode: selectedEdge.target })}>删除连线</Button>,
      <Button key="cancel" onClick={() => setSelectedEdge(null)}>取消</Button>,
      <Button key="save" type="primary" onClick={saveCondition}>保存</Button>
    ]}>
      <Form form={edgeForm} layout="vertical">
        <Form.Item label="条件类型" name="condition_type" rules={[{ required: true }]}><Select options={[
          { label: '总是执行', value: 'always' }, { label: '表达式条件', value: 'expression' }
        ]} /></Form.Item>
        <Form.Item noStyle shouldUpdate={(previous, next) => previous.condition_type !== next.condition_type}>
          {({ getFieldValue }) => getFieldValue('condition_type') === 'expression' && <>
            <Form.Item label="字段候选"><Select showSearch placeholder="选择字段插入表达式" options={fields.map(value => ({ value, label: value }))} onSelect={value => edgeForm.setFieldValue('expression', `${value} == true`)} /></Form.Item>
            <Form.Item label="条件表达式" name="expression" extra="支持单字段比较：==、!=、>、<、>=、<=。例如 total > 0。" rules={[{ required: true, whitespace: true, message: '请输入条件表达式' }, { pattern: /^\s*\w+\s*(==|!=|>=|<=|>|<)\s*.+?\s*$/, message: '请使用单字段比较，例如 total > 0' }]}><AutoComplete options={fields.flatMap(field => [{ value: `${field} == true` }, { value: `${field} > 0` }])} placeholder="例如 verified == true" /></Form.Item>
          </>}
        </Form.Item>
        <Form.Item label="条件说明" name="description"><Input placeholder="显示在连线上的说明" /></Form.Item>
      </Form>
    </Modal>
  </div>;
};
export default WorkflowCanvas;
