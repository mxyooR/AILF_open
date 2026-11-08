import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import { useUserAuth } from './useUserAuth';
import { userTokenManager } from '../../services/common/userTokenManager';

const originalFetch = global.fetch;
let root, auth;
function Fixture() { auth = useUserAuth(); return null; }
beforeEach(() => { root = document.createElement('div'); global.fetch = jest.fn(); act(() => ReactDOM.render(<Fixture />, root)); });
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); userTokenManager.clearToken(); global.fetch = originalFetch; });
test('HTTP 201 registration is success rather than a false failure', async () => {
  global.fetch.mockResolvedValue({ ok: true, status: 201, json: async () => ({ code: 201, data: { user_id: 2 } }) });
  let result;
  await act(async () => { result = await auth.register({ username: 'fixture', password: 'fixture-only' }); });
  expect(result.success).toBe(true);
  expect(auth.authState.error).toBeNull();
});
test('logout immediately removes the local session without waiting for a slow backend', async () => {
  act(() => userTokenManager.setToken({ access_token: 'fixture-token', token_type: 'bearer', expires_in: 3600, user: { id: 1, username: 'fixture', role: { id: 'role' } }, permissions: { apis: [], features: [] } }));
  let finish;
  global.fetch.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  let pending;
  act(() => { pending = auth.logout(); });
  expect(userTokenManager.getToken()).toBeNull();
  expect(auth.authState.isAuthenticated).toBe(false);
  await act(async () => { finish({ ok: true }); await pending; });
});

test.each(['logout', 'unmount'])('late user login cannot restore the session after %s', async action => {
  let finish;
  global.fetch.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  let pending;
  act(() => { pending = auth.login({ username: 'fixture', password: 'fixture-only' }); });
  if (action === 'logout') await act(async () => { await auth.logout(); });
  else act(() => ReactDOM.unmountComponentAtNode(root));
  await act(async () => {
    finish({ ok: true, json: async () => ({ code: 200, data: { access_token: 'late', token_type: 'bearer', expires_in: 3600, user: { id: 1, username: 'fixture', role: { id: 'role' } }, permissions: { apis: [], features: [] } } }) });
    expect((await pending).success).toBe(false);
  });
  expect(userTokenManager.getToken()).toBeNull();
});
