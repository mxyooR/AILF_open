import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import { useCommandRequest } from './useCommandRequest';

let state;
let root;
function Fixture() { state = useCommandRequest(); return <span>{String(state.isProcessing)}</span>; }
beforeEach(() => { root = document.createElement('div'); act(() => ReactDOM.render(<Fixture />, root)); });
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); });
test('two submissions before React renders create only one request', () => {
  let first, second;
  act(() => { first = state.beginRequest(); second = state.beginRequest(); });
  expect(first).toBeTruthy();
  expect(second).toBeNull();
  expect(state.isProcessing).toBe(true);
});
test('closing invalidates the old request and its finally cannot unlock a newer one', () => {
  let old, current;
  act(() => { old = state.beginRequest(); });
  act(() => { state.cancelRequest(); current = state.beginRequest(); });
  expect(old.controller.signal.aborted).toBe(true);
  expect(state.isCurrentRequest(old)).toBe(false);
  act(() => state.finishRequest(old));
  expect(state.isCurrentRequest(current)).toBe(true);
  expect(state.isProcessing).toBe(true);
  act(() => state.finishRequest(current));
  expect(state.isProcessing).toBe(false);
});
test('navigation aborts polling and invalidates late responses', () => {
  let request;
  act(() => { request = state.beginRequest(); });
  act(() => ReactDOM.unmountComponentAtNode(root));
  expect(request.controller.signal.aborted).toBe(true);
  expect(state.isCurrentRequest(request)).toBe(false);
});
