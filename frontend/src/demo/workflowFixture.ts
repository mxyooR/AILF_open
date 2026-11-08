import type { APIRoute } from '../types/developer/route';
import type { WorkflowDefinition, WorkflowNode } from '../types/developer/workflowTypes';

const node = (id: string, type: WorkflowNode['type'], name: string, x: number, y: number, config: WorkflowNode['config'] = {}): WorkflowNode => ({
  id, type, name, description: name, position: { x, y }, config,
  parent_nodes: [], child_nodes: [], outputs: [],
  ai_instructions: { purpose: name, action: `执行${name}` }
});

/** Synthetic configuration only. The static demo never submits it to a backend. */
export function createDemoWorkflow(): WorkflowDefinition {
  const nodes = [
    node('start', 'start', '需求入口', 40, 90),
    node('lookup', 'api_call', '查询门诊时段', 230, 100, {
      api_id: 'demo_slots', api_endpoint: '/demo/slots', method: 'GET',
      parameters: { department: '${department}', period: '${period}' }, ui_mode: 'auto', context_fields: []
    }),
    node('decision', 'condition', '是否有号源', 460, 110),
    node('available', 'notification', '展示可选时段', 680, 95, { message: '已找到可选时段，请核对后继续。', type: 'success' }),
    node('unavailable', 'notification', '提示更换条件', 440, 340, { message: '当前条件暂无号源，可以更换时段再试。', type: 'info' }),
    node('end', 'end', '流程结束', 710, 335)
  ];
  nodes.find(n => n.id === 'lookup')!.outputs = [{ name: 'total', type: 'number', description: '匹配的时段数' }];
  const link = (source: string, target: string, description: string, expression?: string) => {
    nodes.find(n => n.id === source)!.child_nodes.push({ node_id: target, condition: { type: expression ? 'expression' : 'always', description, ...(expression ? { expression } : {}) } });
    nodes.find(n => n.id === target)!.parent_nodes.push(source);
  };
  link('start', 'lookup', '提取查询条件');
  link('lookup', 'decision', '返回查询结果');
  link('decision', 'available', '有可用时段', 'total > 0');
  link('decision', 'unavailable', '暂无可用时段', 'total == 0');
  link('available', 'end', '展示结果');
  link('unavailable', 'end', '返回提示');
  return {
    id: 'demo-clinic', name: '门诊时段查询', description: '用于体验节点、条件和连线编辑的合成示例', business_scenario: '门诊服务演示',
    user_intents: ['查询门诊时段'], trigger_keywords: ['门诊', '号源'],
    inputs: [
      { name: 'department', type: 'string', description: '科室', required: true, ai_prompt: '提取用户要查询的科室' },
      { name: 'period', type: 'string', description: '时段', required: true, ai_prompt: '提取上午或下午' }
    ], nodes
  };
}

export const demoWorkflowRoutes: APIRoute[] = [{
  id: 'demo-slots-route', api_id: 'demo_slots', name: '查询门诊时段（合成示例）', endpoint: '/demo/slots', method: 'GET',
  description: '展示查询节点的配置结构', auth_required: false, status: 'active',
  created_at: '2026-11-08T00:00:00Z', updated_at: '2026-11-08T00:00:00Z'
}];
