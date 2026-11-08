import { ensureFileResponse } from './fileResponse';
import DynamicAPIService from './dynamicAPI';

const response = (payload, type = 'application/json', ok = true) => ({
  ok, status: ok ? 200 : 404,
  headers: { get: name => name.toLowerCase() === 'content-type' ? type : null },
  clone: () => ({ json: async () => payload }),
});
test.each([
  { code: 409, message: '文件不可用' },
  { status: 1, msg: '生成失败' },
])('HTTP 200 file error is not accepted as a downloadable document: %j', async payload => {
  await expect(ensureFileResponse(response(payload))).rejects.toThrow(payload.message || payload.msg);
});
test('ordinary JSON files with domain status fields and binary documents can be downloaded', async () => {
  await expect(ensureFileResponse(response({ status: 'active', records: [] }))).resolves.toBeUndefined();
  await expect(ensureFileResponse(response(null, 'application/pdf'))).resolves.toBeUndefined();
});
test('HTTP errors retain the server explanation', async () => {
  await expect(ensureFileResponse(response({ detail: '文件不存在' }, 'application/problem+json', false))).rejects.toThrow('文件不存在');
});
test('failed downloads do not create a blob or trigger a browser download', async () => {
  const originalFetch = global.fetch;
  const reply = { ...response({ code: 409, message: '文件生成失败' }), blob: jest.fn() };
  global.fetch = jest.fn().mockResolvedValue(reply);
  try {
    await expect(DynamicAPIService.downloadFile('/api/v1/fixture/file', 'fixture.pdf')).resolves.toEqual({ success: false, error: '文件生成失败' });
    expect(reply.blob).not.toHaveBeenCalled();
  } finally { global.fetch = originalFetch; }
});
