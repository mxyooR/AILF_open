import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import AppleRibbonBackground from '../components/AppleRibbonBackground';
import SiriOrb from '../components/SiriOrb';
import { matchDemoScenario, ScenarioId } from './scenarios';
import './DemoSiri.css';

const REPO = 'https://github.com/mxyooR/AILF_open';
type Props = { onSelectScenario: (id: ScenarioId) => void };
type Recognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type SpeechBrowser = { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };

/** Reuses the application's original visual components with a local demo transport. */
export default function DemoSiri({ onSelectScenario }: Props) {
  const [command, setCommand] = useState('');
  const [notice, setNotice] = useState('');
  const [listening, setListening] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<Recognition | null>(null);

  useEffect(() => () => {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.onresult = recognition.onend = recognition.onerror = null;
      recognition.abort();
    }
  }, []);

  function openScenario(id: ScenarioId, text: string) {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.onresult = recognition.onend = recognition.onerror = null;
      recognition.abort();
      recognitionRef.current = null;
    }
    setListening(false);
    setNotice('');
    setCommand(text);
    onSelectScenario(id);
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const id = matchDemoScenario(command);
    if (!id) {
      setNotice('可以试试“查询高铁”“查找耳机”或“预约门诊”。当前演示支持这三种场景。');
      return;
    }
    openScenario(id, command.trim());
  }

  function toggleSpeech() {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const browser = window as unknown as SpeechBrowser;
    const SpeechAPI = browser.SpeechRecognition || browser.webkitSpeechRecognition;
    if (!SpeechAPI) {
      setNotice('当前浏览器不支持语音识别，可以输入文字或点击下方示例。');
      inputRef.current?.focus();
      return;
    }
    const recognition = new SpeechAPI();
    recognitionRef.current?.abort();
    recognitionRef.current = recognition;
    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.onresult = event => {
      if (recognitionRef.current !== recognition) return;
      setCommand(Array.from(event.results, result => result[0]?.transcript || '').join(''));
    };
    recognition.onend = () => {
      if (recognitionRef.current !== recognition) return;
      setListening(false);
      inputRef.current?.focus();
    };
    recognition.onerror = event => {
      if (recognitionRef.current !== recognition) return;
      setListening(false);
      if (event.error === 'aborted') return;
      setNotice(event.error === 'not-allowed' || event.error === 'service-not-allowed'
        ? '麦克风未获授权，可以输入文字或直接选择示例。'
        : '暂时无法识别语音，可以输入文字或直接选择示例。');
    };
    setNotice('');
    try { recognition.start(); setListening(true); }
    catch { setListening(false); setNotice('语音暂时不可用，请使用文字输入。'); }
  }

  return (
    <section className="demo-siri" aria-label="Siri 风格交互演示">
      <AppleRibbonBackground />
      <header className="demo-siri-nav">
        <a className="demo-siri-brand" href="#demo-top">AILF <span>OPEN SOURCE</span></a>
        <nav aria-label="演示导航"><a href="#playground">示例工作台 ↓</a><a href="#workflow">工作流节点 ↓</a><a href={REPO} target="_blank" rel="noreferrer">GitHub ↗</a>{process.env.REACT_APP_DEMO_ONLY === 'true' ? <a className="demo-siri-nav-app" href={`${REPO}/blob/master/docs/DEPLOYMENT.md`} target="_blank" rel="noreferrer">部署完整应用 ↗</a> : <Link className="demo-siri-nav-app" to="/">进入应用 ↗</Link>}</nav>
      </header>
      <div className="demo-siri-content">
        <div className="demo-siri-heading"><h1>AILF</h1><p>AI Language Frontend</p></div>
        <div className="demo-siri-conversation">
          <h2>{listening ? '我在听。' : '智能化业务管理平台'}</h2>
          <p>{listening ? '说完后，点击发送进入示例界面。' : '点击光球，告诉我你需要什么界面。'}</p>
          <form className="demo-siri-input" onSubmit={submit}>
            <label className="demo-visually-hidden" htmlFor="demo-siri-command">输入业务需求</label>
            <input id="demo-siri-command" ref={inputRef} value={command} onChange={event => { setCommand(event.target.value); setNotice(''); }} placeholder="也可以输入：帮我查一下北京到上海的高铁" maxLength={300} autoComplete="off" />
            <button type="submit" disabled={!command.trim()} aria-label="发送需求"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 14 5-5 5 5M12 9v11" /></svg></button>
          </form>
          <div className="demo-siri-examples" role="group" aria-label="快速体验场景">
            <button type="button" onClick={() => openScenario('railway', '帮我查一下北京到上海的高铁')}>查询高铁 <span>↗</span></button>
            <button type="button" onClick={() => openScenario('commerce', '我想找一副无线耳机')}>查找耳机 <span>↗</span></button>
            <button type="button" onClick={() => openScenario('hospital', '帮我看看门诊的可预约时段')}>预约门诊 <span>↗</span></button>
          </div>
          <div className="demo-siri-notice" role="status">{notice}</div>
        </div>
        <div className="demo-siri-voice">
          <SiriOrb isListening={listening} onClick={toggleSpeech} ariaLabel={listening ? '停止语音输入' : '开始语音输入'} />
          <p>{listening ? '正在聆听 · 点击光球结束' : '点击开始语音 · 由浏览器识别服务处理'}</p>
        </div>
      </div>
      <footer className="demo-siri-foot"><span><i /> 内置场景 · 合成数据 · 无需登录</span><a href="#playground">探索示例工作台 <span>↓</span></a></footer>
    </section>
  );
}
