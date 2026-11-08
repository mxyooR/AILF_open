import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { render as renderAmis } from 'amis';
import { buildDemoSchema, handleDemoRequest, scenarios, ScenarioId } from '../demo/scenarios';
import './DemoPage.css';

const REPO = 'https://github.com/mxyooR/AILF_open';
const DemoPage: React.FC = () => {
  const [selected, setSelected] = useState<ScenarioId>('railway');
  const [active, setActive] = useState<ScenarioId>('railway');
  const [revision, setRevision] = useState(0);
  const [view, setView] = useState<'interface' | 'schema'>('interface');
  const [confirmed, setConfirmed] = useState('');
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
  function generate() { setActive(selected); setConfirmed(''); setView('interface'); setRevision(value => value + 1); }
  return (
    <div className="demo-page" id="demo-top">
      <a className="demo-skip" href="#playground">跳转到交互演示</a>
      <header className="demo-nav">
        <a className="demo-brand" href="#demo-top" aria-label="AILF 演示主页"><span className="demo-mark">a</span> AILF<span className="demo-edition">OPEN SOURCE</span></a>
        <nav aria-label="主导航"><a href="#playground">交互演示</a><a href="#architecture">系统设计</a><a href={REPO} target="_blank" rel="noreferrer">GitHub ↗</a>{process.env.REACT_APP_DEMO_ONLY === 'true' ? <a className="demo-nav-launch" href={`${REPO}/blob/master/docs/DEPLOYMENT.md`} target="_blank" rel="noreferrer">部署完整应用 ↗</a> : <Link className="demo-nav-launch" to="/">进入应用 ↗</Link>}</nav>
      </header>
      <main>
        <section className="demo-hero">
          <div className="demo-hero-copy">
            <p className="demo-eyebrow"><span /> LANGUAGE IN. INTERFACE OUT.</p>
            <h1>说出需求，<br />让<span>界面</span>接住。</h1>
            <p className="demo-lead">从自然语言到业务操作。把意图识别、动态表单与工作流连接起来，让每一个需求都有可交互的下一步。</p>
            <div className="demo-hero-actions"><a className="demo-primary" href="#playground">体验交互演示 <span>↓</span></a><a className="demo-text-link" href={`${REPO}#readme`} target="_blank" rel="noreferrer">阅读项目文档 ↗</a></div>
            <p className="demo-hero-note">无需登录 · 无需 GPU · 内置合成示例</p>
          </div>
          <div className="demo-flow-art" aria-label="需求转化为业务界面的示意图">
            <div className="demo-art-grid" />
            <div className="demo-art-prompt"><span className="demo-mini-label">YOU SAY</span><p>“帮我查一下北京到上海的高铁。”</p><span className="demo-art-cursor">↵</span></div>
            <div className="demo-art-connector"><span>意图 → 槽位 → Schema</span><i /></div>
            <div className="demo-art-interface"><div className="demo-art-title"><span>↗</span> 你的下一程<span className="demo-art-ready">READY</span></div><div className="demo-art-cities"><b>北京<small>BEIJING</small></b><span>→</span><b>上海<small>SHANGHAI</small></b></div><div className="demo-art-ticket"><span><b>G101</b><small>07:00 → 12:38</small></span><span className="demo-art-seat">二等座 · 有余票</span><strong>选择 →</strong></div></div>
            <span className="demo-art-caption">A UI THAT FOLLOWS YOUR INTENT.</span>
          </div>
        </section>
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
              {view === 'schema' ? <pre className="demo-schema" tabIndex={0} aria-label="生成的 AMIS Schema">{JSON.stringify(schema, null, 2)}</pre> : <div key={`${active}-${revision}`} className="demo-amis">{renderAmis(schema, {}, env)}</div>}
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
      <footer className="demo-footer"><div><b>AILF</b><span>AI Language Frontend</span></div><p>把需求变成可以操作的界面。</p><a href={`${REPO}/blob/master/LICENSE`} target="_blank" rel="noreferrer">Open source · MIT ↗</a></footer>
    </div>
  );
};
export default DemoPage;
