/** @jest-environment node */
import { buildDemoSchema, handleDemoRequest, queryDemo, scenarios } from './scenarios';

test('changing a ticket search updates displayed route and fare without mutating fixtures', async () => {
  const scenario = scenarios[0];
  const result = await handleDemoRequest(scenario, { url: 'demo://query/railway', data: { departure: '杭州', destination: '南京', seat: '一等座' } }, jest.fn());
  expect(result.data.data.items[0]).toMatchObject({ detail: '杭州 → 南京', price: 933 });
  expect(scenario.rows[0].price).toBe(553);
});

test('product sorting and category changes affect the rendered results', () => {
  const result = queryDemo(scenarios[1], { category: '便携音箱', sort: '价格降序' });
  expect(result.map(item => item.price)).toEqual([699, 399, 199]);
  expect(result.every(item => item.name.includes('音箱'))).toBe(true);
});

test('appointment filters change the department and time', () => {
  expect(queryDemo(scenarios[2], { department: '口腔门诊', period: '下午' })[0]).toMatchObject({ name: '14:00 — 14:30', detail: '口腔门诊 · A 诊室' });
});

test('confirming an existing row completes only the local selection', async () => {
  const confirm = jest.fn();
  await handleDemoRequest(scenarios[0], { url: 'demo://confirm/railway', data: { id: 'G101' } }, confirm);
  expect(confirm).toHaveBeenCalledWith('G101');
});

test('invalid rows, cross-scenario endpoints and external URLs are rejected', async () => {
  const confirm = jest.fn();
  await expect(handleDemoRequest(scenarios[0], { url: 'demo://confirm/railway', data: { id: 'missing' } }, confirm)).rejects.toThrow();
  await expect(handleDemoRequest(scenarios[0], { url: 'demo://query/hospital' }, confirm)).rejects.toThrow();
  await expect(handleDemoRequest(scenarios[0], { url: 'https://example.com' }, confirm)).rejects.toThrow();
  expect(confirm).not.toHaveBeenCalled();
});

test.each(scenarios)('$id provides a serializable AMIS form using local endpoints', scenario => {
  const schema = JSON.parse(JSON.stringify(buildDemoSchema(scenario)));
  expect(schema.body.type).toBe('form');
  expect(schema.body.api.url).toBe(`demo://query/${scenario.id}`);
  expect(schema.body.data.items).toHaveLength(3);
});
