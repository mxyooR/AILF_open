import { UserTokenManager, userTokenManager } from './userTokenManager';

const originalFetch = global.fetch;
const login = (token, id = 1, expires = 3600) => ({ access_token: token, expires_in: expires,
  token_type: 'bearer', user: { id, username: 'fixture', role: { id: 'role', name: '测试角色', permissions: ['data:read'] } },
  permissions: { apis: [], features: [] } });
let manager;
beforeEach(() => {
  jest.useFakeTimers(); localStorage.clear();
  manager = new UserTokenManager({ storageKey: 'fixture_token', userInfoKey: 'fixture_user', autoRefresh: false });
  global.fetch = jest.fn();
});
afterEach(() => { manager.destroy(); userTokenManager.destroy(); global.fetch = originalFetch; jest.clearAllTimers(); jest.useRealTimers(); localStorage.clear(); });
test('a late refresh cannot resurrect a logged out session', async () => {
  let resolve;
  global.fetch.mockImplementation(() => new Promise(done => { resolve = done; }));
  manager.setToken(login('old'));
  const pending = manager.refreshToken();
  manager.clearToken();
  resolve({ ok: true, status: 200, json: async () => ({ code: 200, data: { access_token: 'late', expires_in: 3600 } }) });
  await pending;
  expect(manager.getToken()).toBeNull();
});
test('an old refresh failure cannot log out a newly signed in account', async () => {
  let resolve;
  global.fetch.mockImplementation(() => new Promise(done => { resolve = done; }));
  manager.setToken(login('old'));
  const pending = manager.refreshToken();
  manager.setToken(login('new', 2));
  resolve({ ok: false, status: 401, json: async () => ({ code: 401 }) });
  await pending;
  expect(manager.getToken()).toBe('new');
  expect(manager.getUserInfo().id).toBe(2);
});
test('concurrent refreshes share one request and update all observers', async () => {
  let resolve;
  global.fetch.mockImplementation(() => new Promise(done => { resolve = done; }));
  manager.setToken(login('old'));
  const listener = jest.fn(); manager.addListener(listener);
  const first = manager.refreshToken(), second = manager.refreshToken();
  expect(global.fetch).toHaveBeenCalledTimes(1);
  resolve({ ok: true, status: 200, json: async () => ({ code: 200, data: { access_token: 'new', expires_in: 3600 } }) });
  await Promise.all([first, second]);
  expect(manager.getToken()).toBe('new');
  expect(listener).toHaveBeenCalledWith(true, expect.objectContaining({ id: 1 }));
});
test('profile refresh preserves same-role permissions and broadcasts the new display name', () => {
  manager.setToken(login('session'));
  const listener = jest.fn(); manager.addListener(listener);
  manager.updateUserInfo({ id: 1, username: 'fixture', real_name: '新名字', role: { id: 'role', name: '新角色名' } });
  expect(manager.hasPermission('data', 'read')).toBe(true);
  expect(listener).toHaveBeenCalledWith(true, expect.objectContaining({ real_name: '新名字' }));
});
test('short token lifetimes schedule a delay rather than recursively refreshing', () => {
  manager.destroy();
  manager = new UserTokenManager({ autoRefresh: true });
  manager.setToken(login('short', 1, 60));
  expect(global.fetch).not.toHaveBeenCalled();
  expect(jest.getTimerCount()).toBe(1);
});
