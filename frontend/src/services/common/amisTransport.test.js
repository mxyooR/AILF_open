import { buildAmisRequest, canApplyWorkflowResponse, normalizeAmisResponse } from './amisTransport';

test('GET carries false, zero and filter values in the query instead of a request body', () => {
  const config = buildAmisRequest({ url: '/api/v1/query', method: 'GET', data: { enabled: false, page: 0, city: '上海' } }, {});
  expect(config.params).toEqual({ enabled: false, page: 0, city: '上海' });
  expect(config.data).toBeUndefined();
});

test('write requests keep query parameters separate from form data', () => {
  const config = buildAmisRequest({ url: '/api/v1/items', method: 'PATCH', data: { amount: 0 }, params: { dry_run: false } }, {});
  expect(config.method).toBe('patch');
  expect(config.params).toEqual({ dry_run: false });
  expect(config.data).toEqual({ amount: 0 });
});

test.each([
  { status: 1, msg: '保存失败', data: { type: 'page' } },
  { code: 409, message: '记录冲突' },
  { code: 200, success: false, message: '操作失败' },
  { status: 'invalid', msg: '状态错误' },
])('business errors never become successful workflow transitions: %j', payload => {
  expect(normalizeAmisResponse(payload).status).not.toBe(0);
});

test('a completion page is still a successful response and preserves the final result', () => {
  const payload = { status: 0, msg: '工作流已完成', data: { type: 'page', body: '订单结果' } };
  expect(normalizeAmisResponse(payload)).toEqual({ status: 0, msg: '工作流已完成', data: payload });
});

test('responses from a previous interface, instance or step cannot replace the current form', () => {
  const schema = { instance_id: 'instance-2', current_node_id: 'edit-2' };
  expect(canApplyWorkflowResponse(schema, schema, { instance_id: 'instance-2', node_id: 'edit-2' })).toBe(true);
  expect(canApplyWorkflowResponse(schema, { ...schema }, { instance_id: 'instance-2', node_id: 'edit-2' })).toBe(false);
  expect(canApplyWorkflowResponse(schema, schema, { instance_id: 'instance-1', node_id: 'edit-2' })).toBe(false);
  expect(canApplyWorkflowResponse(schema, schema, { instance_id: 'instance-2', node_id: 'edit-1' })).toBe(false);
});
