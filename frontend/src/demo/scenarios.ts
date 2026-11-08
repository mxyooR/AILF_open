/** Synthetic public fixtures. No model, account, storage or business API is used. */
export type ScenarioId = 'railway' | 'commerce' | 'hospital';
type DemoRow = { id: string; name: string; detail: string; price: number; status: string };
export type DemoScenario = {
  id: ScenarioId; label: string; prompt: string; intent: string; workflow: string[];
  fields: { name: string; label: string; value: string; options: string[] }[];
  rows: DemoRow[]; action: string;
};

export const scenarios: DemoScenario[] = [
  {
    id: 'railway', label: '铁路出行', prompt: '帮我查一下北京到上海的高铁，选择二等座。',
    intent: 'train_ticket_booking', workflow: ['查询车次', '选择车次', '确认行程'],
    fields: [
      { name: 'departure', label: '出发地', value: '北京', options: ['北京', '杭州'] },
      { name: 'destination', label: '目的地', value: '上海', options: ['上海', '南京'] },
      { name: 'seat', label: '席别', value: '二等座', options: ['二等座', '一等座'] }
    ],
    rows: [
      { id: 'G101', name: 'G101 · 07:00 — 12:38', detail: '北京南 → 上海虹桥', price: 553, status: '有余票' },
      { id: 'G103', name: 'G103 · 07:38 — 13:18', detail: '北京南 → 上海虹桥', price: 553, status: '有余票' },
      { id: 'G105', name: 'G105 · 08:05 — 13:48', detail: '北京南 → 上海虹桥', price: 553, status: '有余票' }
    ], action: '选择车次'
  },
  {
    id: 'commerce', label: '商品检索', prompt: '我想找一副无线耳机，看看有哪些在售商品。',
    intent: 'product_search', workflow: ['筛选商品', '查看结果', '确认选择'],
    fields: [
      { name: 'category', label: '商品分类', value: '无线耳机', options: ['无线耳机', '便携音箱'] },
      { name: 'sort', label: '排序', value: '价格升序', options: ['价格升序', '价格降序'] },
      { name: 'availability', label: '库存', value: '在售', options: ['在售'] }
    ],
    rows: [
      { id: 'DEMO-P01', name: 'Air Lite 无线耳机', detail: '轻巧入耳 · 24 小时续航', price: 199, status: '在售' },
      { id: 'DEMO-P02', name: 'Studio 无线耳机', detail: '主动降噪 · 通透模式', price: 399, status: '在售' },
      { id: 'DEMO-P03', name: 'Studio Pro 无线耳机', detail: '空间音频 · 无线充电', price: 699, status: '在售' }
    ], action: '选择商品'
  },
  {
    id: 'hospital', label: '门诊预约', prompt: '帮我看看综合门诊的可预约时段。',
    intent: 'outpatient_appointment', workflow: ['选择科室', '查询时段', '确认预约'],
    fields: [
      { name: 'department', label: '科室', value: '综合门诊', options: ['综合门诊', '口腔门诊'] },
      { name: 'period', label: '时段', value: '上午', options: ['上午', '下午'] },
      { name: 'type', label: '门诊类型', value: '普通门诊', options: ['普通门诊'] }
    ],
    rows: [
      { id: 'DEMO-A01', name: '09:00 — 09:30', detail: '综合门诊 · A 诊室', price: 20, status: '可预约' },
      { id: 'DEMO-A02', name: '10:00 — 10:30', detail: '综合门诊 · B 诊室', price: 20, status: '可预约' },
      { id: 'DEMO-A03', name: '11:00 — 11:30', detail: '综合门诊 · A 诊室', price: 20, status: '可预约' }
    ], action: '选择时段'
  }
];

/** Selects a supported preset; this public playground does not run model inference. */
export function matchDemoScenario(command: string): ScenarioId | null {
  const keywords: [ScenarioId, RegExp][] = [
    ['railway', /高铁|火车|车次|车票|买票|铁路/i],
    ['commerce', /耳机|音箱|商品|购物|电商/i],
    ['hospital', /门诊|医院|挂号|科室|预约|看病/i]
  ];
  return keywords.find(([, pattern]) => pattern.test(command.trim()))?.[0] || null;
}

export function queryDemo(scenario: DemoScenario, values: Record<string, unknown> = {}): DemoRow[] {
  const fields = Object.fromEntries(scenario.fields.map(field => [field.name, values[field.name] || field.value]));
  const rows = scenario.rows.map((row, index) => {
    if (scenario.id === 'railway') return { ...row, detail: `${fields.departure} → ${fields.destination}`, price: fields.seat === '一等座' ? 933 : 553 };
    if (scenario.id === 'commerce') return { ...row, name: fields.category === '便携音箱' ? ['Pocket 便携音箱', 'Room 便携音箱', 'Room Pro 便携音箱'][index] : row.name };
    return { ...row, name: fields.period === '下午' ? ['14:00 — 14:30', '15:00 — 15:30', '16:00 — 16:30'][index] : row.name, detail: `${fields.department} · ${index === 1 ? 'B' : 'A'} 诊室` };
  });
  return fields.sort === '价格降序' ? rows.sort((a, b) => b.price - a.price) : rows;
}

export function buildDemoSchema(scenario: DemoScenario) {
  return {
    type: 'page', body: {
      type: 'form', title: '', wrapWithPanel: false,
      api: { method: 'post', url: `demo://query/${scenario.id}` },
      data: { ...Object.fromEntries(scenario.fields.map(field => [field.name, field.value])), items: queryDemo(scenario) },
      body: [
        { type: 'grid', columns: scenario.fields.map(field => ({ md: 4, body: { type: 'select', name: field.name, label: field.label, options: field.options, required: true, clearable: false } })) },
        { type: 'button', label: '查询示例数据', actionType: 'submit', level: 'primary', className: 'm-b-lg' },
        { type: 'table', source: '${items}', columns: [
          { name: 'name', label: '名称 / 时段' }, { name: 'detail', label: '详情' },
          { name: 'price', label: '价格（元）', type: 'number' }, { name: 'status', label: '状态' },
          { type: 'operation', label: '操作', buttons: [{ type: 'button', label: scenario.action, level: 'link', actionType: 'ajax', api: { method: 'post', url: `demo://confirm/${scenario.id}`, data: { id: '${id}' } } }] }
        ] }
      ], actions: []
    }
  };
}

/** Explicit local transport. Unknown URLs are rejected without a network fallback. */
export async function handleDemoRequest(scenario: DemoScenario, api: { url: string; data?: Record<string, unknown> }, onConfirm: (id: string) => void) {
  if (api.url === `demo://query/${scenario.id}`) return { status: 200, data: { status: 0, msg: '', data: { items: queryDemo(scenario, api.data) } } };
  if (api.url === `demo://confirm/${scenario.id}`) {
    const row = scenario.rows.find(item => item.id === api.data?.id);
    if (!row) throw new Error('请选择有效的示例条目');
    onConfirm(row.id);
    return { status: 200, data: { status: 0, msg: '已完成本地演示选择', data: {} } };
  }
  throw new Error('演示页面仅支持本地示例操作');
}
