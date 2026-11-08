import React, { useEffect, useMemo, useRef, useState } from 'react';
import { render as renderAmis } from 'amis';
import { buildDemoSchema, handleDemoRequest, scenarios, ScenarioId } from '../demo/scenarios';
import './DemoPage.css';
import DemoSiri from '../demo/DemoSiri';

const REPO = 'https://github.com/mxyooR/AILF_open';
const DemoPage: React.FC = () => {
  const [selected, setSelected] = useState<ScenarioId>('railway');
  const [active, setActive] = useState<ScenarioId>('railway');
  const [revision, setRevision] = useState(0);
  const [view, setView] = useState<'interface' | 'schema'>('interface');
  const [confirmed, setConfirmed] = useState('');
  const [siriResultOpen, setSiriResultOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const scenario = scenarios.find(item => item.id === active)!;
  const selectedScenario = scenarios.find(item => item.id === selected)!;
  const schema = useMemo(() => buildDemoSchema(scenario), [scenario]);
  const env = useMemo(() => ({
    fetcher: (api: { url: string; data?: Record<string, unknown> }) => handleDemoRequest(scenario, api, setConfirmed),
    theme: 'antd', session: `ailf-showcase-${active}-${revision}`
  }), [scenario, active, revision]);
  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'AILF · 从一句话，到可交互的业务界面';
    document.body.classList.add('demo-body');
    return () => { document.title = previousTitle; document.body.classList.remove('demo-body'); };
  }, []);
  useEffect(() => {
    if (!siriResultOpen) return;
    dialogRef.current?.showModal();
    const previousOverflow = document.body.style.overflow;
    const previousPriority = document.body.style.getPropertyPriority('overflow');
    document.body.style.setProperty('overflow', 'hidden', 'important');
    return () => { document.body.style.setProperty('overflow', previousOverflow, previousPriority); };
  }, [siriResultOpen]);
  function generate() { setActive(selected); setConfirmed(''); setView('interface'); setRevision(value => value + 1); }
  function openSiriScenario(id: ScenarioId) { setSelected(id); setActive(id); setConfirmed(''); setView('interface'); setRevision(value => value + 1); setSiriResultOpen(true); }
  function closeSiriResult() { dialogRef.current?.close(); setSiriResultOpen(false); }
  return (
    <div className="demo-page" id="demo-top">
      <a className="demo-skip" href="#playground">跳转到交互演示</a>
      <main>
        <DemoSiri onSelectScenario={openSiriScenario} />
        <div className="demo-stack-strip"><span>BUILT WITH</span><b>React + TypeScript</b><i /><b>AMIS</b><i /><b>FastAPI</b><i /><b>Celery + Redis</b><i /><b>Qwen3 + LoRA</b></div>
        <section id="playground" className="demo-playground">
          <div className="demo-section-heading"><div><p className="demo-eyebrow">01 / PLAYGROUND</p><h2>一句需求，一个操作入口。</h2></div><p>选择示例 → 生成界面 → 修改条件 → 完成选择</p></div>
          <div className="demo-workbench">
            <aside className="demo-command-panel">
              <span className="demo-mini-label">选择一句需求</span>
              <div className="demo-scenario-list" role="group" aria-label="业务场景">{scenarios.map((item, index) => <button key={item.id} className={`demo-scenario ${selected === item.id ? 'is-selected' : ''}`} aria-pressed={selected === item.id} onClick={() => setSelected(item.id)}><span>0{index + 1}</span><b>{item.label}</b><span>↗</span></button>)}</div>
              <div className="demo-prompt-card"><span className="demo-mini-label">EXAMPLE PROMPT</span><p>{selectedScenario.prompt}</p></div>
              <button className="demo-primary demo-generate" onClick={generate}>生成演示界面 <span>→</span></button>
              <p className="demo-local-note">此页使用预置意图与合成数据，在浏览器内运行。完整模式由模型推理生成 Schema。</p>
              <div className="demo-execution"><span className="demo-mini-label">当前流程</span>{scenario.workflow.map((step, index) => <div key={step}><span className={index < 2 || confirmed ? 'is-complete' : ''}>{index < 2 || confirmed ? '✓' : '3'}</span><p>{step}</p>{index === 2 && confirmed && <small>已完成</small>}</div>)}</div>
            </aside>
            <div className="demo-result-panel">
              <div className="demo-result-toolbar"><div><span className="demo-live-dot" />{scenario.label}<span className="demo-synthetic">合成数据</span></div><div className="demo-view-switch" role="group" aria-label="预览视图"><button aria-pressed={view === 'interface'} onClick={() => setView('interface')}>业务界面</button><button aria-pressed={view === 'schema'} onClick={() => setView('schema')}>Schema</button></div></div>
              <div className="demo-result-heading"><span className="demo-mini-label">GENERATED WORKSPACE</span><h3>{scenario.label}工作台</h3><p>条件可修改，结果可操作。所有操作仅在当前页面生效。</p></div>
              {confirmed && <div className="demo-confirmation" role="status"><span>✓</span><div><b>已完成演示选择 · {confirmed}</b><p>这是一条本地演示记录，可重新生成界面再次体验。</p></div><button onClick={generate}>重置</button></div>}
              {!siriResultOpen && (view === 'schema' ? <pre className="demo-schema" tabIndex={0} aria-label="生成的 AMIS Schema">{JSON.stringify(schema, null, 2)}</pre> : <div key={`${active}-${revision}`} className="demo-amis">{renderAmis(schema, {}, env)}</div>)}
              <div className="demo-result-footer"><code>intent: {scenario.intent}</code><span>AMIS Schema → React UI</span></div>
            </div>
          </div>
        </section>
        <section id="architecture" className="demo-architecture">
          <div className="demo-section-heading"><div><p className="demo-eyebrow">02 / UNDER THE INTERFACE</p><h2>让生成有依据，让执行有边界。</h2></div><a className="demo-text-link" href={`${REPO}/blob/master/docs/ARCHITECTURE.md`} target="_blank" rel="noreferrer">查看架构设计 ↗</a></div>
          <div className="demo-design-grid">
            <article><span>01 / UNDERSTAND</span><h3>先理解，再生成</h3><p>从业务图谱召回候选 API 与工作流，两轮推理完成意图选择和槽位提取，再由服务端组装界面。</p><code>BGE → Qwen3 + LoRA</code></article>
            <article><span>02 / ORCHESTRATE</span><h3>界面跟随流程</h3><p>开发者配置实体、路由与流程节点。工作流执行器推进状态，Schema 策略将当前步骤转为表单与结果视图。</p><code>Workflow → Schema → AMIS</code></article>
            <article><span>03 / EXECUTE</span><h3>服务端校验执行</h3><p>权限过滤候选，JWT 区分会话，动态路由在执行时校验访问。独立 Worker 通过 Celery 承载模型推理。</p><code>FastAPI → Redis → Worker</code></article>
          </div>
        </section>
      </main>
      {siriResultOpen && <dialog ref={dialogRef} className="demo-siri-dialog" aria-labelledby="demo-siri-result-title" onCancel={event => { event.preventDefault(); closeSiriResult(); }}>
        <header className="demo-siri-dialog-header"><div><h2 id="demo-siri-result-title">{scenario.label}工作台</h2><p>已为你打开内置示例，修改条件即可继续操作。</p></div><button type="button" className="demo-siri-close" onClick={closeSiriResult} aria-label="返回 Siri 界面">×</button></header>
        <div className="demo-result-toolbar"><div><span className="demo-live-dot" />本地演示<span className="demo-synthetic">合成数据</span></div><div className="demo-view-switch" role="group" aria-label="预览视图"><button aria-pressed={view === 'interface'} onClick={() => setView('interface')}>业务界面</button><button aria-pressed={view === 'schema'} onClick={() => setView('schema')}>Schema</button></div></div>
        {confirmed && <div className="demo-confirmation" role="status"><span>✓</span><div><b>已完成演示选择 · {confirmed}</b><p>仅记录当前页面的示例选择。</p></div><button onClick={generate}>重置</button></div>}
        {view === 'schema' ? <pre className="demo-schema" tabIndex={0} aria-label="生成的 AMIS Schema">{JSON.stringify(schema, null, 2)}</pre> : <div className="demo-amis" key={`siri-${active}-${revision}`}>{renderAmis(schema, {}, env)}</div>}
      </dialog>}
      <footer className="demo-footer"><div><b>AILF</b><span>AI Language Frontend</span></div><p>把需求变成可以操作的界面。</p><a href={`${REPO}/blob/master/LICENSE`} target="_blank" rel="noreferrer">Open source · MIT ↗</a></footer>
    </div>
  );
};
export default DemoPage;
