import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import '../components/AILFAboutPage.css';

const AboutPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentScenario, setCurrentScenario] = useState(0);
  const [scenarioFading, setScenarioFading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  const [scrollProgress, setScrollProgress] = useState(0);
  const [impactCounted, setImpactCounted] = useState(false);

  const heroRef = useRef<HTMLElement>(null);
  const scenariosRef = useRef<HTMLElement>(null);
  const flowRef = useRef<HTMLElement>(null);
  const impactRef = useRef<HTMLElement>(null);
  const useCasesRef = useRef<HTMLElement>(null);
  const capabilitiesRef = useRef<HTMLElement>(null);
  const trustRef = useRef<HTMLElement>(null);
  const stackRef = useRef<HTMLElement>(null);
  const faqRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLElement>(null);

  const scenarios = useMemo(
    () => [
      {
        id: 'no-fixed-ui',
        title: '无固定前端',
        subtitle: '业务说话，界面生长',
        description:
          '没有模板库的束缚，界面随意图变化。每次对话，都是一次针对当前业务的全新生成。',
        quote: '“我要一页用于票务对账的界面，重点看今天的销量。”',
        visual: '01',
        color: '#007aff'
      },
      {
        id: 'voice-to-ui',
        title: '语音/文本驱动',
        subtitle: '一句话直达可用界面',
        description:
          '自然语言表达需求，系统自动识别意图、字段与流程，并在数秒内构建可交互界面。',
        quote: '“帮我做一个工单筛选页，能按状态和优先级查。”',
        visual: '02',
        color: '#5ac8fa'
      },
      {
        id: 'policy-driven',
        title: '权限与规则驱动',
        subtitle: '数据与权限同步生效',
        description:
          '以业务规则为核心，权限、字段、流程在同一处配置，前端自动适配角色与组织结构。',
        quote: '“客服只能看到自己负责的工单。”',
        visual: '03',
        color: '#5ac8fa'
      },
      {
        id: 'workflow-native',
        title: '工作流原生',
        subtitle: '流程与界面一体',
        description:
          '审批、支付、出票等节点天然融合，界面跟随流程自动变化，信息可追溯。',
        quote: '“流程走到哪里，界面就给到哪里。”',
        visual: '04',
        color: '#0071e3'
      }
    ],
    []
  );

  useEffect(() => {
    setIsVisible(true);
  }, []);

  useEffect(() => {
    const container = document.querySelector('.about-page-container');
    if (!container) return;

    const observerOptions = {
      root: container,
      threshold: 0.2,
      rootMargin: '0px 0px -20% 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        const sectionId = entry.target.getAttribute('data-section');
        if (sectionId && entry.isIntersecting) {
          setVisibleSections((prev) => {
            const next = new Set(prev);
            next.add(sectionId);
            return next;
          });
        }
      });
    }, observerOptions);

    const sections = [
      { ref: heroRef, id: 'hero' },
      { ref: scenariosRef, id: 'scenarios' },
      { ref: flowRef, id: 'flow' },
      { ref: impactRef, id: 'impact' },
      { ref: useCasesRef, id: 'use-cases' },
      { ref: capabilitiesRef, id: 'capabilities' },
      { ref: trustRef, id: 'trust' },
      { ref: stackRef, id: 'stack' },
      { ref: faqRef, id: 'faq' },
      { ref: ctaRef, id: 'cta' }
    ];

    sections.forEach(({ ref, id }) => {
      if (ref.current) {
        ref.current.setAttribute('data-section', id);
        observer.observe(ref.current);
      }
    });

    const handleScroll = () => {
      sections.forEach(({ ref, id }) => {
        if (ref.current) {
          const rect = ref.current.getBoundingClientRect();
          const containerRect = container.getBoundingClientRect();
          const isSectionVisible =
            rect.top < containerRect.bottom * 0.8 && rect.bottom > containerRect.top;

          if (isSectionVisible) {
            setVisibleSections((prev) => {
              const next = new Set(prev);
              next.add(id);
              return next;
            });
          }
        }
      });
    };

    container.addEventListener('scroll', handleScroll);
    setTimeout(handleScroll, 400);

    // Scroll progress bar tracking
    const handleScrollProgress = () => {
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight - container.clientHeight;
      const progress = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
      setScrollProgress(Math.min(progress, 1));
    };

    container.addEventListener('scroll', handleScrollProgress);

    return () => {
      observer.disconnect();
      container.removeEventListener('scroll', handleScroll);
      container.removeEventListener('scroll', handleScrollProgress);
    };
  }, []);

  useEffect(() => {
    const switchScenario = () => {
      setScenarioFading(true);
      setTimeout(() => {
        setCurrentScenario((prev) => (prev + 1) % scenarios.length);
        setScenarioFading(false);
      }, 350);
    };
    const interval = setInterval(switchScenario, 5000);
    return () => clearInterval(interval);
  }, [scenarios.length]);

  const handleScenarioClick = useCallback((index: number) => {
    if (index === currentScenario) return;
    setScenarioFading(true);
    setTimeout(() => {
      setCurrentScenario(index);
      setScenarioFading(false);
    }, 350);
  }, [currentScenario]);

  // Trigger count-up animation when impact section enters view
  useEffect(() => {
    if (visibleSections.has('impact') && !impactCounted) {
      setImpactCounted(true);
    }
  }, [visibleSections, impactCounted]);

  return (
    <div className="about-page-container">
      <div className={`ailf-about-page ${isVisible ? 'visible' : ''}`}>
        {/* Scroll progress bar — Google Material informative motion */}
        <div
          className="scroll-progress-bar"
          style={{ transform: `scaleX(${scrollProgress})` }}
        />

        <button className="ailf-back-button" onClick={() => navigate('/')} aria-label="返回主页">
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
          </svg>
        </button>

        <section
          ref={heroRef}
          className={`ailf-hero ailf-section ${visibleSections.has('hero') ? 'animate-in' : ''}`}
        >
          <div className="container hero-grid">
            <div className="hero-copy">
              <span className="hero-badge">AILF 动态界面引擎</span>
              <h1 className="hero-title">
                让界面跟着业务生长，<br />
                每一句需求都能落地
              </h1>
              <p className="hero-subtitle">
                AILF 把“说清楚需求”变成“马上可用的界面”，让业务、流程、数据在同一处被理解与呈现。
              </p>
              <div className="hero-actions">
                <button className="primary-button" onClick={() => navigate('/')}>
                  回到主页
                </button>
                <button className="ghost-button" onClick={() => navigate('/config')}>
                  查看配置
                </button>
              </div>
              <div className="hero-highlights">
                <div>零固定模板</div>
                <div>多角色权限同步</div>
                <div>工作流自动生成</div>
                <div>全链路可追溯</div>
              </div>
            </div>
            <div className="hero-visual">
              <div className="hero-card hero-card-main">
                <div className="hero-card-title">指令 → 界面</div>
                <p>“我要买票，上海到成都，2月12日出发。”</p>
                <span className="hero-chip">实时生成</span>
              </div>
              <div className="hero-card hero-card-side">
                <div className="hero-card-title">流程节点</div>
                <ul>
                  <li>乘客验证</li>
                  <li>车次选择</li>
                  <li>支付出票</li>
                </ul>
              </div>
              <div className="hero-card hero-card-mini">
                <div className="hero-card-title">数据视图</div>
                <p>库存 / 订单 / 支付 状态实时联动</p>
              </div>
            </div>
          </div>
        </section>

        <section
          ref={scenariosRef}
          className={`ailf-scenarios ailf-section ${visibleSections.has('scenarios') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="section-header">
              <p className="section-eyebrow">场景化能力</p>
              <h2>不是模板，是每次都因你而生</h2>
              <p className="section-lead">从需求到界面，AILF 让每个业务场景都拥有自己的专属表达。</p>
            </div>

            <div className="scenario-panel">
              <div className="scenario-visual">
                <span className={`scenario-index ${scenarioFading ? 'scenario-fade-out' : 'scenario-fade-in'}`}>
                  {scenarios[currentScenario].visual}
                </span>
                <div className="scenario-glow" style={{ background: scenarios[currentScenario].color }} />
              </div>
              <div className={`scenario-content ${scenarioFading ? 'scenario-fade-out' : 'scenario-fade-in'}`}>
                <h3>{scenarios[currentScenario].title}</h3>
                <p className="scenario-subtitle">{scenarios[currentScenario].subtitle}</p>
                <p className="scenario-description">{scenarios[currentScenario].description}</p>
                <div className="scenario-quote">{scenarios[currentScenario].quote}</div>
              </div>
            </div>

            <div className="scenario-indicators">
              {scenarios.map((scenario, index) => (
                <button
                  key={scenario.id}
                  className={`indicator ${index === currentScenario ? 'active' : ''}`}
                  onClick={() => handleScenarioClick(index)}
                  aria-label={`切换到场景 ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </section>

        <section
          ref={flowRef}
          className={`ailf-flow ailf-section ${visibleSections.has('flow') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="section-header">
              <p className="section-eyebrow">流程一体化</p>
              <h2>三步完成“意图 → 界面”</h2>
              <p className="section-lead">表达需求、生成结构、同步业务流程，全链路一次贯通。</p>
            </div>

            <div className="flow-grid">
              <div className="flow-step">
                <span className="flow-index">01</span>
                <h3>意图表达</h3>
                <p>通过语音或文本描述需求，系统理解意图与核心字段。</p>
              </div>
              <div className="flow-step">
                <span className="flow-index">02</span>
                <h3>结构生成</h3>
                <p>AI 结合权限、API、字段规则构建页面结构与交互逻辑。</p>
              </div>
              <div className="flow-step">
                <span className="flow-index">03</span>
                <h3>界面落地</h3>
                <p>页面立即可用，流程节点同步联动，数据更新实时呈现。</p>
              </div>
            </div>
          </div>
        </section>

        <section
          ref={impactRef}
          className={`ailf-impact ailf-section ${visibleSections.has('impact') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="impact-grid">
              <div className="impact-copy">
                <p className="section-eyebrow">落地成效</p>
                <h2>从需求到落地，速度与一致性并存</h2>
                <p className="section-lead">
                  AILF 把业务的语言直接转换成界面与流程，让跨团队协作、权限控制、数据验证一步到位。
                </p>
                <div className="impact-list">
                  <div>一处配置，多端即用；界面结构、字段校验、权限策略同步生效。</div>
                  <div>流程节点可回溯，订单/支付/出票等关键动作自动留痕。</div>
                  <div>界面更新与数据更新同步完成，避免手工维护的漂移。</div>
                </div>
                <div className="impact-tags">
                  <span>票务出行</span>
                  <span>客服工单</span>
                  <span>库存管理</span>
                  <span>审批流程</span>
                  <span>数据看板</span>
                </div>
              </div>
              <div className="impact-cards">
                <div className="impact-card">
                  <p className={`impact-value ${impactCounted ? 'counting' : ''}`}>
                    <span className="count-number">2~5s</span>
                  </p>
                  <p className="impact-label">平均界面生成速度</p>
                  <p className="impact-note">自然语言输入后即可得到可用页面</p>
                </div>
                <div className="impact-card">
                  <p className={`impact-value ${impactCounted ? 'counting' : ''}`}>
                    <span className="count-number">7+</span>
                  </p>
                  <p className="impact-label">典型节点覆盖</p>
                  <p className="impact-note">验证、查询、支付、出票等流程一体化</p>
                </div>
                <div className="impact-card">
                  <p className={`impact-value ${impactCounted ? 'counting' : ''}`}>
                    <span className="count-number">99%</span>
                  </p>
                  <p className="impact-label">界面一致性</p>
                  <p className="impact-note">多角色、多端口体验统一且可控</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          ref={useCasesRef}
          className={`ailf-use-cases ailf-section ${visibleSections.has('use-cases') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="section-header">
              <p className="section-eyebrow">行业场景</p>
              <h2>把复杂业务拆成清晰可执行的界面</h2>
              <p className="section-lead">不同领域的规则、权限与流程，都能被统一成可用的操作界面。</p>
            </div>
            <div className="use-case-grid">
              <div className="use-case-card">
                <div className="use-case-tag">票务出行</div>
                <h3>查询、锁座、支付、出票一体化</h3>
                <p>从余票检索到出票确认，节点清晰、数据联动，降低人工协作成本。</p>
                <ul>
                  <li>车次/座位动态联动</li>
                  <li>订单与支付状态同步</li>
                  <li>出票记录自动归档</li>
                </ul>
              </div>
              <div className="use-case-card">
                <div className="use-case-tag">政务审批</div>
                <h3>分级审批与材料校验可配置</h3>
                <p>审批路径可视化，字段校验与材料上传规则全部可控。</p>
                <ul>
                  <li>多级审批节点配置</li>
                  <li>材料清单自动检查</li>
                  <li>流程状态可追溯</li>
                </ul>
              </div>
              <div className="use-case-card">
                <div className="use-case-tag">供应链管理</div>
                <h3>库存、采购、入库自动联动</h3>
                <p>把复杂的表格与流程变成清晰的操作界面，支持多角色协作。</p>
                <ul>
                  <li>库存阈值预警</li>
                  <li>采购单自动流转</li>
                  <li>多仓库权限隔离</li>
                </ul>
              </div>
              <div className="use-case-card">
                <div className="use-case-tag">客服工单</div>
                <h3>语音意图转工单，SLA 自动跟进</h3>
                <p>把分散的信息统一到可执行流程里，提升响应效率。</p>
                <ul>
                  <li>语音/文本意图识别</li>
                  <li>优先级与SLA规则</li>
                  <li>状态流转自动记录</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section
          ref={capabilitiesRef}
          className={`ailf-capabilities ailf-section ${visibleSections.has('capabilities') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="section-header">
              <p className="section-eyebrow">核心能力</p>
              <h2>为复杂业务准备的底层能力</h2>
              <p className="section-lead">从数据到流程，从权限到体验，能力环环相扣。</p>
            </div>

            <div className="capability-grid">
              <div className="capability-card">
                <h3>动态表单</h3>
                <p>字段随意图变化，校验、联动、默认值自动匹配业务规则。</p>
              </div>
              <div className="capability-card">
                <h3>多端适配</h3>
                <p>一套能力适配 PC、移动端与大屏展示，体验一致。</p>
              </div>
              <div className="capability-card">
                <h3>流程编排</h3>
                <p>节点、条件、分支可配置，界面与流程状态联动。</p>
              </div>
              <div className="capability-card">
                <h3>权限同步</h3>
                <p>角色、字段、数据范围在同一处配置，界面自动限制。</p>
              </div>
              <div className="capability-card">
                <h3>可观察性</h3>
                <p>调用链路、状态变化、接口响应可回溯，便于排障。</p>
              </div>
              <div className="capability-card">
                <h3>私有部署</h3>
                <p>支持本地化部署与数据隔离，满足企业合规要求。</p>
              </div>
            </div>
            <div className="capability-footer">
              <div>可配置字段校验 · 默认值 · 级联联动</div>
              <div>支持多租户、分组权限与审计日志</div>
              <div>界面结构可导出，支持快速复用</div>
            </div>
          </div>
        </section>

        <section
          ref={trustRef}
          className={`ailf-trust ailf-section ${visibleSections.has('trust') ? 'animate-in' : ''}`}
        >
          <div className="container trust-grid">
            <div>
              <p className="section-eyebrow">信任与安全</p>
              <h2>数据在你的掌控之内</h2>
              <p className="section-lead">
                业务数据在本地处理，权限与访问路径可控可审计，确保安全边界清晰可见。
              </p>
            </div>
            <div className="trust-cards">
              <div className="trust-card">
                <span>本地优先</span>
                <p>关键数据不离开你掌控的环境。</p>
              </div>
              <div className="trust-card">
                <span>权限隔离</span>
                <p>角色、字段、组织级别隔离到位。</p>
              </div>
              <div className="trust-card">
                <span>日志追踪</span>
                <p>每个动作、每次请求都有清晰记录。</p>
              </div>
            </div>
          </div>
        </section>

        <section
          ref={stackRef}
          className={`ailf-stack ailf-section ${visibleSections.has('stack') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="section-header">
              <p className="section-eyebrow">技术栈</p>
              <h2>可靠、可扩展、可演进</h2>
              <p className="section-lead">现代化技术组合，保障稳定性与持续迭代能力。</p>
            </div>

            <div className="stack-grid">
              <div className="stack-card">
                <h3>前端体验</h3>
                <ul>
                  <li>React + TypeScript</li>
                  <li>AMIS Schema 渲染</li>
                  <li>可视化主题系统</li>
                </ul>
              </div>
              <div className="stack-card">
                <h3>后端能力</h3>
                <ul>
                  <li>FastAPI 服务编排</li>
                  <li>动态路由与实体模型</li>
                  <li>工作流执行引擎</li>
                </ul>
              </div>
              <div className="stack-card">
                <h3>智能中枢</h3>
                <ul>
                  <li>意图识别与槽位填充</li>
                  <li>结构化数据映射</li>
                  <li>多模型协同生成</li>
                </ul>
              </div>
            </div>
            <div className="stack-note">
              <div>兼容主流数据库与对象存储</div>
              <div>支持 API 版本化与灰度发布</div>
              <div>可对接企业身份体系与单点登录</div>
            </div>
          </div>
        </section>

        <section
          ref={faqRef}
          className={`ailf-faq ailf-section ${visibleSections.has('faq') ? 'animate-in' : ''}`}
        >
          <div className="container">
            <div className="section-header">
              <p className="section-eyebrow">常见问题</p>
              <h2>你关心的，我们提前回答</h2>
              <p className="section-lead">从部署方式到权限策略，快速了解 AILF 如何落地。</p>
            </div>
            <div className="faq-grid">
              <div className="faq-item">
                <h3>需要重新开发前端吗？</h3>
                <p>不需要。配置 API 与权限规则后，界面会自动生成并保持一致。</p>
              </div>
              <div className="faq-item">
                <h3>复杂流程如何适配？</h3>
                <p>支持多节点、多条件分支与状态回溯，流程配置与界面生成一体化。</p>
              </div>
              <div className="faq-item">
                <h3>数据安全如何保障？</h3>
                <p>支持本地化部署与权限隔离，关键数据不离开你的基础设施。</p>
              </div>
              <div className="faq-item">
                <h3>能否接入现有系统？</h3>
                <p>支持多种 API 规范与身份体系，可与现有服务无缝对接。</p>
              </div>
            </div>
          </div>
        </section>

        <section
          ref={ctaRef}
          className={`ailf-cta ailf-section ${visibleSections.has('cta') ? 'animate-in' : ''}`}
        >
          <div className="container cta-card">
            <div>
              <h2>准备让界面自己生长了吗？</h2>
              <p>从一句话需求开始，进入你的下一代业务体验。</p>
            </div>
            <button className="primary-button" onClick={() => navigate('/')}>
              立即体验
            </button>
          </div>
        </section>

        <footer className="ailf-footer">
          <div className="container footer-content">
            <div>
              <p>© {new Date().getFullYear()} AILF Team</p>
              <p>Powered by workflow-first interface generation.</p>
            </div>
            <div className="footer-links">
              <button onClick={() => window.open('https://github.com/ailf-team/ailf', '_blank')}>
                GitHub
              </button>
              <button onClick={() => window.open('https://ailf.dev/docs', '_blank')}>
                文档
              </button>
              <button onClick={() => window.open('https://ailf.dev/support', '_blank')}>
                支持
              </button>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default AboutPage;
