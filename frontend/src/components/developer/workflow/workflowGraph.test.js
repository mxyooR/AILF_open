/** @jest-environment node */
import { withWorkflowEdge } from './workflowGraph';

test('editing a branch condition preserves branch order and the opposite branch', () => {
  const condition = { type: 'expression', expression: 'decision_result == true', description: '可预约' };
  const other = { type: 'expression', expression: 'decision_result == false', description: '无号源' };
  const nodes = [
    { id: 'decision', child_nodes: [{ node_id: 'yes', condition }, { node_id: 'no', condition: other }] },
    { id: 'yes', parent_nodes: ['decision'] }, { id: 'no', parent_nodes: ['decision'] }
  ];
  const updated = withWorkflowEdge(nodes, 'decision', 'yes', { ...condition, description: '已更新' });
  expect(updated[0].child_nodes.map(child => child.node_id)).toEqual(['yes', 'no']);
  expect(updated[0].child_nodes[1].condition).toEqual(other);
  expect(updated[1].parent_nodes).toEqual(['decision']);
  expect(nodes[0].child_nodes[0].condition.description).toBe('可预约');
});
