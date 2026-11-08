import { appConfigAPI } from './appConfig';
import { tokenManager } from './common/tokenManager';

jest.mock('./common/tokenManager', () => ({ tokenManager: { isAuthenticated: jest.fn(() => true), getToken: jest.fn(() => 'fixture-developer') } }));
const originalFetch = global.fetch;
beforeEach(() => {
  global.fetch = jest.fn(); jest.clearAllMocks();
  tokenManager.isAuthenticated.mockReturnValue(true);
  tokenManager.getToken.mockReturnValue('fixture-developer');
});
afterEach(() => { global.fetch = originalFetch; });
const reply = (payload, ok = true) => global.fetch.mockResolvedValue({ ok, json: async () => payload });

test.each([
  [{ detail: '服务暂不可用' }, false, '服务暂不可用'],
  [{ code: 409, message: '配置冲突' }, true, '配置冲突'],
  [{ code: 200, data: null }, true, '应用配置格式不正确'],
  [{ code: 200, data: { title: 'AILF', subtitle: null } }, true, '应用配置格式不正确'],
])('invalid app configuration is rejected so the page retains its defaults: %j', async (payload, ok, error) => {
  reply(payload, ok);
  await expect(appConfigAPI.getAppConfig()).rejects.toThrow(error);
});

test('valid configuration without an optional background retains the default style', async () => {
  reply({ code: 200, data: { title: '测试应用', subtitle: '' } });
  await expect(appConfigAPI.getAppConfig()).resolves.toEqual({ title: '测试应用', subtitle: '', backgroundStyle: 'mesh' });
});

test('HTTP 200 business failure never reports a configuration save as successful', async () => {
  reply({ code: 409, message: '保存冲突', data: null });
  await expect(appConfigAPI.updateAppConfig({ title: '测试', subtitle: '' })).rejects.toThrow('保存冲突');
  expect(global.fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer fixture-developer');
  expect(tokenManager.isAuthenticated).toHaveBeenCalled();
});
