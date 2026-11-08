import React from 'react';
import ReactDOM from 'react-dom';
import { act } from 'react-dom/test-utils';
import { useLocalVoice } from './useLocalVoice';

const mockTranscribe = jest.fn();
jest.mock('@xenova/transformers', () => ({ pipeline: jest.fn(async () => mockTranscribe), env: {} }));
let root, voice, recognition, recorder, stopped, finishRecording;
function Fixture() { voice = useLocalVoice(); return null; }
class Recognition {
  constructor() { recognition = this; }
  start() {}
  stop() { this.onend?.(); }
  abort() {}
}
class Recorder {
  static isTypeSupported() { return true; }
  constructor() { recorder = this; this.state = 'inactive'; }
  start() { this.state = 'recording'; }
  stop() {
    this.state = 'inactive';
    this.ondataavailable?.({ data: new Blob(['fixture']) });
    finishRecording = this.onstop?.();
  }
}
class AudioFixture {
  createAnalyser() { return { frequencyBinCount: 1, getByteFrequencyData: data => { data[0] = 0; } }; }
  createMediaStreamSource() { return { connect() {}, disconnect() {} }; }
  async decodeAudioData() { return { getChannelData: () => new Float32Array([0]) }; }
  async close() {}
}
beforeEach(() => {
  stopped = jest.fn();
  window.SpeechRecognition = Recognition;
  window.AudioContext = AudioFixture;
  global.MediaRecorder = Recorder;
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: jest.fn(async () => ({ getTracks: () => [{ stop: stopped }] })) } });
  Blob.prototype.arrayBuffer = async () => new ArrayBuffer(1);
  jest.spyOn(window, 'requestAnimationFrame').mockReturnValue(1);
  root = document.createElement('div');
  act(() => ReactDOM.render(<Fixture />, root));
});
afterEach(() => { act(() => ReactDOM.unmountComponentAtNode(root)); jest.restoreAllMocks(); });
test('silence or interim-only online speech never becomes a submitted instruction', async () => {
  await act(async () => { await voice.startListening(); });
  expect(voice.transcript).toBe('');
  act(() => recognition.onresult({ resultIndex: 0, results: [{ 0: { transcript: '临时结果' }, isFinal: false }] }));
  expect(voice.isListening).toBe(true);
  act(() => recognition.onend());
  expect(voice.transcript).toBe('');
  expect(voice.isListening).toBe(false);
});
test('only a final online speech result is kept after recognition ends', async () => {
  await act(async () => { await voice.startListening(); });
  act(() => { recognition.onresult({ resultIndex: 0, results: [{ 0: { transcript: '我要买票' }, isFinal: true }] }); recognition.onend(); });
  expect(voice.transcript).toBe('我要买票');
});
test('local transcription has separate busy state and never exposes status text as a command', async () => {
  act(() => recognition.onerror({ error: 'network' }));
  let complete;
  mockTranscribe.mockImplementation(() => new Promise(resolve => { complete = resolve; }));
  await act(async () => { await voice.startListening(); });
  expect(recorder.state).toBe('recording');
  await act(async () => { voice.stopListening(); });
  expect(voice.transcript).toBe('');
  expect(voice.isTranscribing).toBe(true);
  await act(async () => { complete({ text: '查询车次' }); await finishRecording; });
  expect(voice.isTranscribing).toBe(false);
  expect(voice.transcript).toBe('查询车次');
});
test('navigating away stops all microphone tracks', async () => {
  await act(async () => { await voice.startListening(); });
  act(() => ReactDOM.unmountComponentAtNode(root));
  expect(stopped).toHaveBeenCalledTimes(1);
});
test('closing during a pending permission request releases the late stream', async () => {
  let resolve;
  navigator.mediaDevices.getUserMedia.mockImplementation(() => new Promise(done => { resolve = done; }));
  let pending;
  act(() => { pending = voice.startListening(); });
  act(() => ReactDOM.unmountComponentAtNode(root));
  await act(async () => { resolve({ getTracks: () => [{ stop: stopped }] }); await pending; });
  expect(stopped).toHaveBeenCalledTimes(1);
});
