import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import WorkflowCanvas from './WorkflowCanvas';
import WorkflowButterflyNode from './WorkflowButterflyNode';
import { workflowAPI } from '../../../services/developer/workflowAPI';

const mockCanvases = [];
jest.mock('antd', () => ({ ...jest.requireActual('antd'), message: { success: jest.fn(), error: jest.fn(), warning: jest.fn() } }));
jest.mock('../../../services/developer/workflowAPI', () => ({ workflowAPI: { getWorkflowDetail: jest.fn() } }));
jest.mock('butterfly-dag', () => ({
  Canvas: class {
    constructor({ root }) {
      this.root = root;
      this.nodes = [];
      this.edges = [];
      this.handlers = {};
      this.destroy = jest.fn(() => root.replaceChildren());
      this.on = (name, callback) => { this.handlers[name] = callback; };
      this.off = jest.fn();
      this.getDataMap = () => ({ nodes: this.nodes, edges: this.edges });
      this.getNode = id => this.nodes.find(node => node.id === id);
      this.addNode = data => {
        const dom = global.document.createElement('div');
        dom.innerHTML = '<span class="node-label"></span>';
        dom.querySelector('span').textContent = data.options.label;
        root.appendChild(dom);
        const node = { ...data, options: data, dom };
        this.nodes.push(node);
        return node;
      };
      this.removeNode = id => {
        this.getNode(id)?.dom.remove();
        this.nodes = this.nodes.filter(node => node.id !== id);
        this.edges = this.edges.filter(edge => edge.sourceNode !== id && edge.targetNode !== id);
      };
      this.removeNodes = ids => ids.forEach(id => this.removeNode(id));
      this.removeEdge = (id, silent) => {
        const links = this.edges.filter(edge => edge.id === id);
        this.edges = this.edges.filter(edge => edge.id !== id);
        if (!silent) this.handlers.events?.({ type: 'links:delete', links });
      };
      this.addEdge = data => { this.edges.push({ ...data, updateLabel: jest.fn() }); };
      this.draw = (data, callback) => {
        data.nodes.forEach(this.addNode);
        data.edges.forEach(this.addEdge);
        callback?.();
      };
      this.redraw = jest.fn((data, callback) => {
        this.nodes.forEach(node => node.dom.remove());
        this.nodes = []; this.edges = [];
        this.draw(data, callback);
      });
      this.setDraggable = jest.fn(); this.setLinkable = jest.fn(); this.setDisLinkable = jest.fn();
      this.terminal2canvas = ([x, y]) => [x / 2, y / 2];
      mockCanvases.push(this);
    }
  },
  Node: class {}, Edge: class {}
}));
jest.mock('./NodePalette', () => ({ onNodeDrop }) => <button onClick={() => onNodeDrop('notification', { x: 200, y: 100 })}>添加通知</button>);
jest.mock('./NodeEditor', () => ({ node, onSave }) => <button onClick={() => onSave({ ...node, name: '已修改', config: { message: '新消息', type: 'success' } })}>提交节点</button>);

const node = (id, type, children = [], parents = []) => ({
  id, type, name: id, description: '', position: { x: 0, y: 0 },
  parent_nodes: parents, child_nodes: children.map(node_id => ({ node_id, condition: { type: 'always', description: '总是执行' } })),
  config: {}, outputs: [], ai_instructions: { purpose: '', action: '' }
});
const fixture = () => ({ id: 'test', name: '本地测试', description: '', business_scenario: 'test', user_intents: [], trigger_keywords: [], inputs: [], nodes: [node('start', 'start', ['notice']), node('notice', 'notification', ['end'], ['start']), node('end', 'end', [], ['notice'])] });
let root;
const click = async text => {
  const button = [...document.querySelectorAll('button')].find(el => el.textContent.includes(text));
  expect(button).toBeDefined();
  await act(async () => { button.click(); });
};
const custom = (canvas, type, detail) => act(() => { canvas.nodes[0].dom.dispatchEvent(new CustomEvent(type, { bubbles: true, detail })); });
beforeEach(() => {
  jest.useFakeTimers();
  mockCanvases.length = 0;
  window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
  root = document.createElement('div'); document.body.appendChild(root);
  jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(() => {
  act(() => { ReactDOM.unmountComponentAtNode(root); }); root.remove();
  jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks();
});
const mount = (props = {}) => {
  act(() => { ReactDOM.render(<WorkflowCanvas workflow={fixture()} {...props} />, root); });
  act(() => jest.runOnlyPendingTimers());
  return mockCanvases[mockCanvases.length - 1];
};

test('keeps a live canvas when nodes change and retains zero coordinates', async () => {
  const canvas = mount();
  expect(canvas.destroy).not.toHaveBeenCalled();
  expect(canvas.nodes[0].left).toBe(0);
  await click('添加通知');
  expect(canvas.destroy).not.toHaveBeenCalled();
  expect(canvas.nodes).toHaveLength(4);
});

test('saves edited fields and live positions instead of stale canvas metadata', async () => {
  const onSave = jest.fn(); const canvas = mount({ onSave });
  custom(canvas, 'node-edit', { nodeId: 'notice', nodeType: 'notification' });
  act(() => jest.runOnlyPendingTimers());
  await click('提交节点');
  canvas.getNode('notice').left = 321;
  await click('保存工作流');
  const saved = onSave.mock.calls[0][0].nodes.find(n => n.id === 'notice');
  expect(saved).toMatchObject({ name: '已修改', position: { x: 321, y: 0 }, config: { message: '新消息' } });
  expect(canvas.getNode('notice').dom.textContent).toContain('已修改');
  expect(canvas.getNode('notice').dom.getAttribute('aria-label')).toContain('已修改');
});

test('deleting a node removes both incoming and outgoing relationships', async () => {
  const onSave = jest.fn(); const canvas = mount({ onSave });
  custom(canvas, 'node-delete', { nodeId: 'notice' });
  await click('保存工作流');
  const saved = onSave.mock.calls[0][0].nodes;
  expect(saved.map(n => n.id)).toEqual(['start', 'end']);
  expect(saved.every(n => n.parent_nodes.length === 0 && n.child_nodes.length === 0)).toBe(true);
});

test('only the owning editable canvas handles custom node events', () => {
  const workflow = fixture();
  act(() => { ReactDOM.render(<><WorkflowCanvas workflow={workflow} /><WorkflowCanvas workflow={workflow} readonly /></>, root); });
  act(() => jest.runOnlyPendingTimers());
  custom(mockCanvases[0], 'node-edit', { nodeId: 'notice', nodeType: 'notification' });
  act(() => jest.runOnlyPendingTimers());
  expect([...document.querySelectorAll('button')].filter(el => el.textContent === '提交节点')).toHaveLength(1);
});

test('disconnecting and reconnecting maintain both sides without duplicate links', async () => {
  const onSave = jest.fn(); const canvas = mount({ onSave });
  act(() => { canvas.removeEdge(JSON.stringify(['start', 'notice'])); });
  const edge = { id: 'new', sourceNode: { id: 'start' }, targetNode: { id: 'end' } };
  act(() => { canvas.edges.push(edge); canvas.handlers.events({ type: 'link:connect', links: [edge] }); });
  const duplicate = { ...edge, id: 'duplicate' };
  act(() => { canvas.edges.push(duplicate); canvas.handlers.events({ type: 'link:connect', links: [duplicate] }); });
  await click('保存工作流');
  const saved = onSave.mock.calls[0][0].nodes;
  expect(saved.find(n => n.id === 'start').child_nodes.map(n => n.node_id)).toEqual(['end']);
  expect(saved.find(n => n.id === 'notice').parent_nodes).toEqual([]);
  expect(saved.find(n => n.id === 'end').parent_nodes).toEqual(['notice', 'start']);
  expect(canvas.edges.filter(e => e.id === 'duplicate')).toHaveLength(0);
});

test('saves an intentionally empty graph without resurrecting canvas nodes', async () => {
  const onSave = jest.fn(); const canvas = mount({ onSave });
  ['start', 'notice', 'end'].forEach(nodeId => custom(canvas, 'node-delete', { nodeId }));
  canvas.nodes.push({ id: 'ghost', left: 10, top: 10, dom: document.createElement('div') });
  await click('保存工作流');
  expect(onSave.mock.calls[0][0].nodes).toEqual([]);
});

test('ignores an old API response after switching workflows', async () => {
  let resolveFirst; let resolveSecond;
  workflowAPI.getWorkflowDetail.mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve; }))
    .mockImplementationOnce(() => new Promise(resolve => { resolveSecond = resolve; }));
  const canvas = mount({ workflow: undefined, workflowId: 'first' });
  await act(async () => {});
  await act(async () => { ReactDOM.render(<WorkflowCanvas workflowId="second" />, root); });
  const second = { ...fixture(), id: 'second', nodes: [node('second-node', 'start')] };
  await act(async () => { resolveSecond({ code: 200, data: { workflow: second } }); });
  await act(async () => { resolveFirst({ code: 200, data: { workflow: fixture() } }); });
  expect(canvas.nodes.map(n => n.id)).toEqual(['second-node']);
});

test('coalesces external updates while an asynchronous redraw is in flight', async () => {
  const onSave = jest.fn(); const canvas = mount({ onSave });
  const draw = canvas.redraw.getMockImplementation(); const callbacks = [];
  canvas.redraw.mockImplementation((data, callback) => { callbacks.push(() => draw(data, callback)); });
  const render = id => {
    const workflow = { ...fixture(), id, nodes: [node(id, 'start')] };
    act(() => { ReactDOM.render(<WorkflowCanvas workflow={workflow} onSave={onSave} />, root); });
  };
  render('one'); render('two'); render('three');
  expect(callbacks).toHaveLength(1);
  act(() => { callbacks.shift()(); });
  expect(callbacks).toHaveLength(1);
  act(() => { callbacks.shift()(); });
  await click('保存工作流');
  expect(onSave.mock.calls[0][0].nodes.map(n => n.id)).toEqual(['three']);
  expect(canvas.nodes.map(n => n.id)).toEqual(['three']);
});

test.each(['api_call', 'condition', 'notification', 'end'])('renders %s using Butterfly nested draw options', type => {
  const visual = new WorkflowButterflyNode({});
  const dom = visual.draw({ id: 'node', left: 0, top: 0, options: { options: { nodeType: type, label: '节点名称' } } });
  expect(dom.dataset.nodeType).toBe(type);
  expect(dom.querySelector('.node-label').textContent).toBe('节点名称');
});

test('reconnecting retains the original condition and updates relationship summaries', async () => {
  const workflow = fixture();
  workflow.nodes[0].child_nodes[0].condition = { type: 'expression', expression: 'total > 0', description: '有结果' };
  const onSave = jest.fn(); const canvas = mount({ workflow, onSave });
  const oldEdge = canvas.edges[0];
  const newEdge = { id: 'reconnected', sourceNode: { id: 'start' }, targetNode: { id: 'end' } };
  act(() => {
    canvas.edges = canvas.edges.filter(edge => edge !== oldEdge); canvas.edges.push(newEdge);
    canvas.handlers.events({ type: 'link:reconnect', delLinks: [oldEdge], addLinks: [newEdge] });
  });
  await click('保存工作流');
  const saved = onSave.mock.calls[0][0];
  expect(saved.nodes[0].child_nodes[0]).toMatchObject({ node_id: 'end', condition: { expression: 'total > 0' } });
  expect(saved.node_relationships.start.children).toEqual(['end']);
  expect(saved.node_relationships.notice.parents).toEqual([]);
});

test('read-only canvas ignores mutations and coordinate conversion is used on drop', async () => {
  const workflow = fixture(); const onSave = jest.fn();
  const canvas = mount({ workflow, readonly: true, onSave });
  custom(canvas, 'node-delete', { nodeId: 'notice' });
  expect(canvas.nodes).toHaveLength(3);
  act(() => { ReactDOM.render(<WorkflowCanvas workflow={workflow} onSave={onSave} />, root); });
  const target = root.querySelector('.workflow-canvas');
  const event = new Event('drop', { bubbles: true });
  Object.assign(event, { clientX: 600, clientY: 400, dataTransfer: { getData: () => 'notification' } });
  act(() => { target.dispatchEvent(event); });
  await click('保存工作流');
  expect(onSave.mock.calls[0][0].nodes[3].position).toEqual({ x: 300, y: 200 });
});
