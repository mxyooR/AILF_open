import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import NotificationsPage from './NotificationsPage';
import apiClient from '../services/common/apiClient';
import { useUserAuth } from '../hooks/user/useUserAuth';

jest.mock('react-router-dom', () => ({ useNavigate: () => jest.fn() }));
jest.mock('../hooks/user/useUserAuth', () => ({ useUserAuth: jest.fn() }));
jest.mock('../services/common/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn(), delete: jest.fn() } }));
let root, auth;
const record = id => ({ id, title: '通知fixture' + id, content: '内容', status: '未读' });
const response = (items, page = 1, total = items.length) => ({ code: 200, data: { items, total, page, unread_count: total, has_prev: page > 1, has_next: page * 20 < total } });
const click = async label => {
  const button = [...root.querySelectorAll('button')].find(el => el.textContent === label);
  expect(button).toBeDefined();
  await act(async () => { button.click(); });
};
const render = async () => { await act(async () => ReactDOM.render(<NotificationsPage />, root)); };
beforeEach(() => {
  jest.resetAllMocks();
  auth = { isAuthenticated: true, user: { id: 1 } };
  useUserAuth.mockImplementation(() => ({ authState: auth }));
  root = document.createElement('div'); document.body.appendChild(root);
  apiClient.get.mockResolvedValue(response([record('one')]));
});
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); root.remove(); });
test('failed mark-read preserves the unread item and count', async () => {
  apiClient.post.mockRejectedValue(new Error('无权操作fixture'));
  await render(); await click('标记已读');
  expect(root.textContent).toContain('未读 1 条');
  expect(root.textContent).toContain('无权操作fixture');
  expect(root.textContent).toContain('标记已读');
});
test('deleting the last row on page two goes back to page one and reloads authoritative totals', async () => {
  apiClient.get.mockImplementation(async (_, options) => options.params.page === 2
    ? response([record('last')], 2, 21) : response([record('first')], 1, 21));
  await render(); await click('下一页');
  apiClient.delete.mockResolvedValue({ code: 200 });
  apiClient.get.mockResolvedValue(response([record('remaining')], 1, 20));
  await click('删除');
  expect(root.textContent).toContain('第 1 / 1 页');
  expect(root.textContent).toContain('共 20 条');
  expect(root.textContent).toContain('通知fixtureremaining');
});
test('switching accounts ignores a late list response from the previous account', async () => {
  let finishOld;
  apiClient.get.mockImplementationOnce(() => new Promise(resolve => { finishOld = resolve; }))
    .mockResolvedValue(response([record('new-user')]));
  await render();
  auth = { isAuthenticated: true, user: { id: 2 } };
  await render();
  await act(async () => { finishOld(response([record('old-user')])); });
  expect(root.textContent).toContain('new-user');
  expect(root.textContent).not.toContain('old-user');
});
test('the same notification cannot be marked read twice while a request is pending', async () => {
  let finish;
  apiClient.post.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  await render();
  const button = [...root.querySelectorAll('button')].find(el => el.textContent === '标记已读');
  act(() => { button.click(); button.click(); });
  expect(apiClient.post).toHaveBeenCalledTimes(1);
  await act(async () => { finish({ code: 200 }); });
});
