import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import { useDeveloperAuth } from './useDeveloperAuth';
import { authAPI } from '../../services/developer/authAPI';
import { tokenManager } from '../../services/common/tokenManager';

jest.mock('../../services/developer/authAPI', () => ({ authAPI: { setAuthToken: jest.fn(), authenticate: jest.fn(), logout: jest.fn() } }));
const login = token => ({ token, refresh_token: 'fixture-refresh', expires_at: new Date(Date.now() + 3600000).toISOString(), issued_at: new Date().toISOString(), expires_in: 3600, token_type: 'bearer' });
let root, auth;
function Fixture() { auth = useDeveloperAuth(); return null; }
beforeEach(() => { jest.useFakeTimers(); jest.clearAllMocks(); root = document.createElement('div'); act(() => ReactDOM.render(<Fixture />, root)); });
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); tokenManager.clearToken(); jest.clearAllTimers(); jest.useRealTimers(); });

test('slow developer logout clears immediately and cannot erase a subsequent login', async () => {
  act(() => tokenManager.setToken(login('old')));
  let finish;
  authAPI.logout.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  let pending;
  act(() => { pending = auth.logout(); });
  expect(auth.authState.isAuthenticated).toBe(false);
  expect(tokenManager.getToken()).toBeNull();
  expect(authAPI.logout).toHaveBeenCalledWith('old');
  act(() => tokenManager.setToken(login('new')));
  await act(async () => { finish(); await pending; });
  expect(tokenManager.getToken()).toBe('new');
  expect(auth.authState.isAuthenticated).toBe(true);
});

test.each(['logout', 'unmount'])('late authentication cannot restore the session after %s', async action => {
  let finish;
  authAPI.authenticate.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  let pending;
  act(() => { pending = auth.authenticate({ password: 'fixture-only', rememberMe: false }); });
  if (action === 'logout') await act(async () => { await auth.logout(); });
  else act(() => ReactDOM.unmountComponentAtNode(root));
  await act(async () => {
    finish({ code: 200, data: login('late') });
    expect((await pending).success).toBe(false);
  });
  expect(tokenManager.getToken()).toBeNull();
});
