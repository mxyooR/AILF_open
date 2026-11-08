import React from 'react';
import ReactDOM from 'react-dom';
import { act, Simulate } from 'react-dom/test-utils';
import { message } from 'antd';
import NodeEditor from './NodeEditor';
import { routeAPI } from '../../../services/developer/routeAPI';

jest.mock('antd', () => ({ ...jest.requireActual('antd'), message: { error: jest.fn() } }));
jest.mock('../../../services/developer/routeAPI', () => ({ routeAPI: { getRoutes: jest.fn() } }));

let root;
const fixture = (type, config) => ({
  id: 'notice', name: '通知', description: '显示流程结果', type, config,
  position: { x: 0, y: 0 }, parent_nodes: [], child_nodes: [], outputs: [],
  ai_instructions: { purpose: '显示结果', action: '向用户显示消息' }
});
beforeEach(() => {
  jest.useFakeTimers();
  window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
  root = document.createElement('div'); document.body.appendChild(root);
  jest.clearAllMocks();
});
afterEach(async () => {
  await act(async () => { jest.runOnlyPendingTimers(); });
  act(() => { ReactDOM.unmountComponentAtNode(root); }); root.remove();
  jest.clearAllTimers(); jest.useRealTimers();
});
const save = async () => {
  const button = [...root.querySelectorAll('button')].find(el => el.textContent.includes('保存'));
  await act(async () => { button.click(); });
};

test('preserves the configured notification severity when saving without changing it', async () => {
  const onSave = jest.fn();
  act(() => { ReactDOM.render(<NodeEditor node={fixture('notification', { message: '已完成', type: 'success' })} onSave={onSave} onCancel={() => {}} />, root); });
  expect(root.querySelector('.ant-select-selection-item').textContent).toBe('成功');
  await save();
  expect(onSave.mock.calls[0][0].config).toMatchObject({ message: '已完成', type: 'success' });
});

test('isolated API editor uses injected routes and reports invalid JSON without saving', async () => {
  const onSave = jest.fn();
  const node = fixture('api_call', { api_id: 'lookup', api_endpoint: '/demo/lookup', method: 'GET', parameters: {} });
  const routes = [{ id: 'lookup-route', api_id: 'lookup', name: '查询', method: 'GET', endpoint: '/demo/lookup' }];
  act(() => { ReactDOM.render(<NodeEditor node={node} availableRoutes={routes} onSave={onSave} onCancel={() => {}} />, root); });
  expect(routeAPI.getRoutes).not.toHaveBeenCalled();
  const parameters = root.querySelector('#parameters');
  act(() => { Simulate.change(parameters, { target: { value: '{invalid' } }); });
  await save();
  expect(onSave).not.toHaveBeenCalled();
  expect(message.error).toHaveBeenCalledWith('请求参数必须是有效的 JSON');
});
