import React from 'react';
import ReactDOM from 'react-dom';
import { act, Simulate } from 'react-dom/test-utils';
import DynamicRecordForm from './DynamicRecordForm';

const entity = { id: 'fixture', displayName: '测试', fields: [
  { id: 'name', name: 'name', displayName: '名称', type: 'text' },
  { id: 'note', name: 'note', displayName: '备注', type: 'text' }
] };
let root;
const mount = async props => { await act(async () => { ReactDOM.render(<DynamicRecordForm entity={entity} visible mode="edit" onCancel={() => {}} {...props} />, root); }); };
beforeEach(() => {
  root = document.createElement('div'); document.body.appendChild(root);
  window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
});
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); root.remove(); });
test('switching from edit to create clears the previous record values', async () => {
  await mount({ record: { name: '旧记录', note: '私有备注' } });
  expect(document.querySelector('input[id="name"]').value).toBe('旧记录');
  await mount({ mode: 'create', record: null });
  expect(document.querySelector('input[id="name"]').value).toBe('');
  expect(document.querySelector('input[id="note"]').value).toBe('');
});
test('a failed save keeps entered values for correction and retry', async () => {
  const onSubmit = jest.fn().mockResolvedValue(undefined);
  await mount({ record: { name: '重试内容' }, onSubmit });
  const button = [...document.querySelectorAll('button')].find(el => el.textContent.includes('保 存'));
  await act(async () => { button.click(); });
  expect(onSubmit).toHaveBeenCalledWith({ name: '重试内容' });
  expect(document.querySelector('input[id="name"]').value).toBe('重试内容');
});
