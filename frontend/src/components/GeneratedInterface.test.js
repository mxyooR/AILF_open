import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import GeneratedInterface from './GeneratedInterface';

jest.mock('amis', () => ({ render: schema => <div><a href="/api/v1/orders">订单导航</a><img alt="fixture" src={schema.src || '/api/v1/files/serve/fixture.png'} /></div> }));
jest.mock('./SiriOrb', () => () => null);
jest.mock('../services/common/userTokenManager', () => ({ userTokenManager: { getToken: () => 'fixture-user' } }));
const originalFetch = global.fetch;
let root;
const props = { amisEnv: {}, onClose() {}, onToggleListening() {}, isListening: false };
beforeEach(() => {
  jest.useFakeTimers();
  global.fetch = jest.fn();
  URL.createObjectURL = jest.fn(() => 'blob:fixture');
  URL.revokeObjectURL = jest.fn();
  root = document.createElement('div'); document.body.appendChild(root);
});
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); root.remove(); global.fetch = originalFetch; jest.clearAllTimers(); jest.useRealTimers(); });
const mount = async (schema = { type: 'page' }) => {
  act(() => ReactDOM.render(<GeneratedInterface {...props} schema={schema} amisKey={1} />, root));
  await act(async () => { jest.advanceTimersByTime(100); });
};
test('navigation links stay navigable while protected images load with authentication', async () => {
  global.fetch.mockResolvedValue({ ok: true, blob: async () => new Blob(['fixture']) });
  await mount();
  expect(root.querySelector('a').getAttribute('href')).toBe('/api/v1/orders');
  expect(global.fetch).toHaveBeenCalledTimes(1);
  expect(global.fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer fixture-user');
  expect(root.querySelector('img').getAttribute('src')).toBe('blob:fixture');
});
test('closing aborts media requests and does not create late orphaned object URLs', async () => {
  let finish;
  global.fetch.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  await mount();
  const signal = global.fetch.mock.calls[0][1].signal;
  act(() => ReactDOM.unmountComponentAtNode(root));
  expect(signal.aborted).toBe(true);
  await act(async () => { finish({ ok: true, blob: async () => new Blob(['fixture']) }); });
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
test('closing releases existing media object URLs', async () => {
  global.fetch.mockResolvedValue({ ok: true, blob: async () => new Blob(['fixture']) });
  await mount();
  act(() => ReactDOM.unmountComponentAtNode(root));
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:fixture');
});
