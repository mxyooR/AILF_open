import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import WorkflowDesignStep from './WorkflowDesignStep';
import { workflowAPI } from '../../../services/developer/workflowAPI';

jest.mock('../../../hooks/developer/useDeveloperAuth', () => ({ useDeveloperAuth: () => ({ authState: { isAuthenticated: true, token: 'fixture-developer' } }) }));
jest.mock('../../../services/common/apiClient', () => ({ apiClient: { getDeveloperToken: () => 'fixture-developer' } }));
jest.mock('../../../services/developer/workflowAPI', () => ({ workflowAPI: { getWorkflowsList: jest.fn(), getWorkflowDetail: jest.fn(), updateWorkflow: jest.fn() } }));
jest.mock('../workflow/WorkflowCanvas', () => props => <div data-testid="canvas">{props.workflow.name}<button onClick={() => { void props.onSave({ ...props.workflow, name: '保存后的名称' }).catch(() => {}); }}>保存设计fixture</button></div>);
jest.mock('antd', () => ({ ...jest.requireActual('antd'), message: { success: jest.fn(), error: jest.fn() } }));
const flow = id => ({ id, name: id, description: '描述', business_scenario: 'test', status: 'DRAFT', nodes: [], inputs: [], trigger_keywords: [], user_intents: [] });
let root;
beforeEach(() => {
  jest.clearAllMocks();
  delete window.apiClient;
  window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
  root = document.createElement('div'); document.body.appendChild(root);
  workflowAPI.getWorkflowsList.mockResolvedValue({ code: 200, data: { workflows: [flow('first'), flow('second')] } });
  workflowAPI.getWorkflowDetail.mockImplementation(async id => ({ code: 200, data: { workflow: flow(id) } }));
  workflowAPI.updateWorkflow.mockImplementation(async (id, request) => ({ code: 200, data: { workflow: { ...flow(id), ...request } } }));
});
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); root.remove(); });
const mount = async () => { await act(async () => ReactDOM.render(<WorkflowDesignStep />, root)); };
const card = name => [...root.querySelectorAll('.workflow-card')].find(el => el.textContent.includes(name));
test('production loads details without a window debug client and saves a draft without activating it', async () => {
  await mount();
  await act(async () => { card('first').click(); });
  expect(workflowAPI.getWorkflowDetail).toHaveBeenCalledWith('first');
  expect(root.querySelector('[data-testid="canvas"]').textContent).toContain('first');
  await act(async () => { root.querySelector('[data-testid="canvas"] button').click(); });
  expect(workflowAPI.updateWorkflow).toHaveBeenCalledWith('first', expect.objectContaining({ name: '保存后的名称', nodes: [] }));
  expect(workflowAPI.updateWorkflow.mock.calls[0][1]).not.toHaveProperty('status');
});
test('rapid selection cannot save first workflow nodes under the second workflow id', async () => {
  const pending = {};
  workflowAPI.getWorkflowDetail.mockImplementation(id => new Promise(resolve => { pending[id] = resolve; }));
  await mount();
  act(() => { card('first').click(); card('second').click(); });
  await act(async () => { pending.second({ code: 200, data: { workflow: flow('second') } }); });
  await act(async () => { pending.first({ code: 200, data: { workflow: flow('first') } }); });
  expect(root.querySelector('[data-testid="canvas"]').textContent).toContain('second');
  await act(async () => { root.querySelector('[data-testid="canvas"] button').click(); });
  expect(workflowAPI.updateWorkflow.mock.calls[0][0]).toBe('second');
});
test('a failed list shows the server error and retry, without fabricated example workflows', async () => {
  workflowAPI.getWorkflowsList.mockRejectedValue(new Error('读取配置失败fixture'));
  await mount();
  expect(root.textContent).toContain('读取配置失败fixture');
  expect(root.textContent.replace(/\s/g, '')).toContain('重试');
  expect(root.querySelectorAll('.workflow-card')).toHaveLength(0);
});
