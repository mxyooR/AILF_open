/** @jest-environment node */
import { apiClient } from './apiClient';
import DynamicAPIService from './dynamicAPI';

const originalFetch = global.fetch;
const originalHeaders = global.Headers;
// Jest 27 的 Node 沙箱不提供浏览器 Headers；替身只实现被测传输层需要的标准行为。
class FixtureHeaders {
  constructor(values = {}) { this.values = Object.fromEntries(Object.entries(values).map(([key, value]) => [key.toLowerCase(), value])); }
  has(key) { return key.toLowerCase() in this.values; }
  get(key) { return this.values[key.toLowerCase()] ?? null; }
  set(key, value) { this.values[key.toLowerCase()] = value; }
}
beforeEach(() => {
  global.fetch = jest.fn();
  global.Headers = FixtureHeaders;
  apiClient.setDeveloperToken('fixture-developer');
  apiClient.setUserToken(null);
});
afterEach(() => { global.fetch = originalFetch; global.Headers = originalHeaders; apiClient.setDeveloperToken(null); });

function respond(status, payload) {
  global.fetch.mockResolvedValue({ status, ok: status >= 200 && status < 300, text: async () => payload === undefined ? '' : JSON.stringify(payload) });
}

test('PATCH uses PATCH and preserves body, query values and explicit authentication', async () => {
  respond(200, { code: 200, message: '成功', data: { count: 0 } });
  const result = await DynamicAPIService.callDynamicAPI({
    method: 'PATCH', endpoint: '/api/v1/fixture', data: { count: 0 }, params: { enabled: false },
    headers: { Authorization: 'Bearer fixture-user', 'X-Fixture': 'test' }, timeout: 100,
  });
  expect(result.success).toBe(true);
  const [url, options] = global.fetch.mock.calls[0];
  expect(url).toContain('/api/v1/fixture?enabled=false');
  expect(options.method).toBe('PATCH');
  expect(JSON.parse(options.body)).toEqual({ count: 0 });
  expect(options.headers.get('Authorization')).toBe('Bearer fixture-user');
  expect(options.headers.get('X-Fixture')).toBe('test');
});

test('HTTP 200 business failures are reported as failed route tests', async () => {
  respond(200, { code: 409, message: '订单状态冲突', data: null });
  const result = await DynamicAPIService.callDynamicAPI({ method: 'POST', endpoint: '/api/v1/fixture' });
  expect(result.success).toBe(false);
  expect(result.error).toBe('订单状态冲突');
});

test('DELETE with an empty 204 response succeeds', async () => {
  respond(204);
  const result = await DynamicAPIService.callDynamicAPI({ method: 'DELETE', endpoint: '/api/v1/fixture' });
  expect(result.success).toBe(true);
  expect(result.statusCode).toBe(204);
});

test('personal notification requests use the user token when a developer is also logged in', async () => {
  respond(200, { code: 200, data: { items: [] } });
  apiClient.setUserToken('fixture-user');
  await apiClient.get('/api/v1/notifications');
  expect(global.fetch.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer fixture-user');
  apiClient.setUserToken(null);
  await apiClient.get('/api/v1/notifications');
  expect(global.fetch.mock.calls[1][1].headers.has('Authorization')).toBe(false);
});

test('API errors preserve HTTP status and explicit user authentication never refreshes a developer token', async () => {
  respond(403, { code: 403, message: '无权访问', data: null });
  const result = await DynamicAPIService.callDynamicAPI({ method: 'GET', endpoint: '/api/v1/fixture', headers: { Authorization: 'Bearer fixture-user' } });
  expect(result.success).toBe(false);
  expect(result.statusCode).toBe(403);
  expect(global.fetch).toHaveBeenCalledTimes(1);
});

test.each([
  { code: 409, message: '记录冲突' },
  { status: 1, msg: '删除失败' },
  { code: 200, success: false, message: '保存失败' }
])('shared client rejects HTTP 200 business failures before callers update the UI: %j', async payload => {
  respond(200, payload);
  await expect(apiClient.post('/api/v1/notifications/fixture/read')).rejects.toThrow(payload.message || payload.msg);
});

test('upload with HTTP 200 and a business error is reported as failed', async () => {
  const originalFormData = global.FormData;
  global.FormData = class { append() {} };
  global.fetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({ code: 409, message: '文件类型不支持' }) });
  try {
    const result = await DynamicAPIService.uploadFile('/api/v1/fixture/upload', {});
    expect(result.success).toBe(false);
    expect(result.error).toBe('文件类型不支持');
  } finally { global.FormData = originalFormData; }
});
