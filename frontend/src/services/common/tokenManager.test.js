import { TokenManager, tokenManager } from './tokenManager';
import { authAPI } from '../developer/authAPI';
jest.mock('../developer/authAPI', () => ({ authAPI: { setAuthToken: jest.fn(), refreshToken: jest.fn(), verifyToken: jest.fn() } }));
const login = token => ({ token, refresh_token: 'fixture-refresh', expires_at: new Date(Date.now() + 3600000).toISOString(), issued_at: new Date().toISOString(), expires_in: 3600, token_type: 'bearer' });
let manager;
beforeEach(() => { jest.useFakeTimers(); jest.clearAllMocks(); localStorage.clear(); sessionStorage.clear(); manager = new TokenManager({ storageKey: 'fixture_developer', autoRefresh: false }); });
afterEach(() => { manager.destroy(); tokenManager.destroy(); jest.clearAllTimers(); jest.useRealTimers(); localStorage.clear(); sessionStorage.clear(); });
test('developer logout cannot be undone by a late refresh', async () => {
  let finish;
  authAPI.refreshToken.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  manager.setToken(login('old'));
  const pending = manager.refreshToken();
  manager.clearToken();
  finish({ code: 200, data: login('late') });
  await pending;
  expect(manager.getToken()).toBeNull();
});
test('developer refresh uses one request and retains session-only storage', async () => {
  let finish;
  authAPI.refreshToken.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  manager.setToken(login('old'), { rememberMe: false });
  const first = manager.refreshToken(), second = manager.refreshToken();
  expect(authAPI.refreshToken).toHaveBeenCalledTimes(1);
  finish({ code: 200, data: login('new') });
  await Promise.all([first, second]);
  expect(manager.getToken()).toBe('new');
  expect(localStorage.getItem('fixture_developer')).toBeNull();
  expect(JSON.parse(sessionStorage.getItem('fixture_developer_session')).token).toBe('new');
});
test('an earlier refresh failure cannot clear a new developer session', async () => {
  let fail;
  authAPI.refreshToken.mockImplementation(() => new Promise((_, reject) => { fail = reject; }));
  manager.setToken(login('old'));
  const pending = manager.refreshToken();
  manager.setToken(login('new'));
  fail({ status: 401 });
  await pending;
  expect(manager.getToken()).toBe('new');
});

test.each(['invalid', 'error'])('late token verification cannot clear a newer developer session: %s', async result => {
  let finish, fail;
  authAPI.verifyToken.mockImplementation(() => new Promise((resolve, reject) => { finish = resolve; fail = reject; }));
  manager.setToken(login('old'));
  const pending = manager.verifyCurrentToken();
  manager.setToken(login('new'));
  if (result === 'invalid') finish({ code: 200, data: { valid: false } });
  else fail({ status: 401 });
  expect(await pending).toBe(false);
  expect(manager.getToken()).toBe('new');
});
test('temporary token verification failure retains a still valid local session', async () => {
  manager.setToken(login('valid'));
  authAPI.verifyToken.mockRejectedValue({ status: 503 });
  expect(await manager.verifyCurrentToken()).toBe(false);
  expect(manager.getToken()).toBe('valid');
});
