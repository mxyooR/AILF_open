import type { WorkflowNode, ChildNode, NodeType } from '../../../types/developer/workflowTypes';

/** Workflow state owns fields/relationships. Butterfly supplies only live coordinates. */
export function snapshotWorkflowNodes(nodes: WorkflowNode[], canvasNodes: any[] = []): WorkflowNode[] {
  const positions = new Map(canvasNodes.map(node => [node.id, node]));
  return nodes.map(node => ({
    ...node,
    position: {
      x: Math.round(positions.get(node.id)?.left ?? node.position?.x ?? 0),
      y: Math.round(positions.get(node.id)?.top ?? node.position?.y ?? 0)
    },
    parent_nodes: [...(node.parent_nodes || [])],
    child_nodes: (node.child_nodes || []).map(child => ({ ...child, condition: { ...child.condition } }))
  }));
}
export function withoutWorkflowNode(nodes: WorkflowNode[], id: string): WorkflowNode[] {
  return nodes.filter(node => node.id !== id).map(node => ({
    ...node,
    parent_nodes: (node.parent_nodes || []).filter(parent => parent !== id),
    child_nodes: (node.child_nodes || []).filter(child => child.node_id !== id)
  }));
}
export function withoutWorkflowEdge(nodes: WorkflowNode[], source: string, target: string): WorkflowNode[] {
  return nodes.map(node => ({
    ...node,
    parent_nodes: node.id === target ? (node.parent_nodes || []).filter(id => id !== source) : node.parent_nodes,
    child_nodes: node.id === source ? (node.child_nodes || []).filter(child => child.node_id !== target) : node.child_nodes
  }));
}
export function withWorkflowEdge(nodes: WorkflowNode[], source: string, target: string, condition: ChildNode['condition']): WorkflowNode[] {
  return nodes.map(node => {
    if (node.id === source) {
      const children = node.child_nodes || [];
      return { ...node, child_nodes: children.some(child => child.node_id === target)
        ? children.map(child => child.node_id === target ? { ...child, condition } : child)
        : [...children, { node_id: target, condition }] };
    }
    if (node.id === target) return { ...node, parent_nodes: Array.from(new Set([...(node.parent_nodes || []), source])) };
    return node;
  });
}
export function nodeEndpoints(type: NodeType) {
  const input = { id: 'left', orientation: [-1, 0], pos: [0, 0.5], type: 'target' };
  const output = { id: 'right', orientation: [1, 0], pos: [0, 0.5], type: 'source' };
  if (type === 'start') return [output];
  if (type === 'end') return [input];
  if (type === 'condition') return [input, output, { id: 'bottom', orientation: [0, 1], pos: [0.5, 0], type: 'source' }];
  return [input, output];
}
