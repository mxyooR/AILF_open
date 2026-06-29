# train_ticket.py - 火车票场景定义 V3
# 简化版：删除 user_input 节点，所有输入在 api_call 节点的表单中完成

TRAIN_TICKET_SCENE = {
    "domain": "train_ticket",
    "apis": [
        {
            "id": "api_station_search",
            "path": "/api/trains/stations",
            "method": "GET",
            "desc": "搜索车站",
            "instruction_variants": ["搜索车站", "查车站", "找车站", "车站在哪", "喂，这车站叫啥", "帮我找车站", "车站怎么搜", "查一下车站"],
            "request": [
                {"name": "keyword", "type": "string", "label": "车站关键词", "required": True}
            ],
            "response": [
                {"name": "stations", "type": "array", "desc": "车站列表"}
            ]
        },
        {
            "id": "api_train_list",
            "path": "/api/trains",
            "method": "GET",
            "desc": "查询车次余票",
            "instruction_variants": ["查询车次余票", "查车次", "有票吗", "余票查询", "喂，还有票吗", "帮我查查车次", "车次有哪些", "查一下票"],
            "request": [
                {"name": "from_station", "type": "string", "label": "出发地", "required": True},
                {"name": "to_station", "type": "string", "label": "目的地", "required": True},
                {"name": "date", "type": "date", "label": "出发日期", "required": True},
                {"name": "train_type", "type": "string", "label": "车次类型(G/D/C/K等)", "required": False}
            ],
            "response": [
                {"name": "trains", "type": "array", "desc": "车次列表"}
            ]
        },
        {
            "id": "api_train_detail",
            "path": "/api/trains/{train_no}",
            "method": "GET",
            "desc": "查询车次详情",
            "instruction_variants": ["查询车次详情", "车次详情", "这车次怎么样", "车次信息", "喂，这车几点到", "帮我看看车次", "车次时刻表", "途径哪些站"],
            "request": [
                {"name": "train_no", "type": "string", "label": "车次号", "required": True},
                {"name": "date", "type": "date", "label": "日期", "required": True}
            ],
            "response": [
                {"name": "stations", "type": "array", "desc": "途径站点"},
                {"name": "timetable", "type": "array", "desc": "时刻表"}
            ]
        },
        {
            "id": "api_passenger_list",
            "path": "/api/ticket/passengers",
            "method": "GET",
            "desc": "查询常用乘车人",
            "instruction_variants": ["查询常用乘车人", "乘车人列表", "我的乘车人", "常用联系人", "喂，我有哪些乘车人", "帮我看看乘车人", "乘车人有谁", "联系人列表"],
            "request": [],
            "response": [
                {"name": "passengers", "type": "array", "desc": "乘车人列表"}
            ]
        },
        {
            "id": "api_passenger_add",
            "path": "/api/ticket/passengers",
            "method": "POST",
            "desc": "添加乘车人",
            "instruction_variants": ["添加乘车人", "新增乘车人", "添加联系人", "加个乘车人", "喂，我要添加乘车人", "帮我加个乘车人", "添加怎么弄", "新增联系人"],
            "request": [
                {"name": "name", "type": "string", "label": "姓名", "required": True},
                {"name": "id_card", "type": "string", "label": "身份证号", "required": True},
                {"name": "phone", "type": "string", "label": "手机号", "required": True},
                {"name": "passenger_type", "type": "string", "label": "乘客类型", "required": True}
            ],
            "response": [
                {"name": "passenger_id", "type": "string", "desc": "乘车人ID"}
            ]
        },
        # ========== 购票流程专用 API ==========
        {
            "id": "api_passenger_verify",
            "workflow_only": True,
            "path": "/api/v1/passengers/verify",
            "method": "POST",
            "desc": "验证乘客身份",
            "instruction_variants": ["验证乘客身份", "身份验证", "验证身份", "确认乘客", "喂，怎么验证身份", "帮我验证一下", "身份怎么确认", "验证乘客"],
            "request": [
                {"name": "name", "type": "string", "label": "姓名", "required": True},
                {"name": "id_card", "type": "string", "label": "身份证号", "required": True},
                {"name": "phone", "type": "string", "label": "手机号", "required": True},
                {"name": "passenger_type", "type": "string", "label": "乘客类型", "required": True}
            ],
            "response": [
                {"name": "passenger_id", "type": "string", "desc": "乘客ID"},
                {"name": "passenger_name", "type": "string", "desc": "乘客姓名"},
                {"name": "id_card", "type": "string", "desc": "身份证号"}
            ]
        },
        {
            "id": "api_create_ticket",
            "workflow_only": True,
            "path": "/api/v1/orders",
            "method": "POST",
            "desc": "创建购票订单",
            "instruction_variants": ["创建购票订单", "创建订单", "提交订单", "下单", "喂，我要买票", "帮我下单", "订单怎么创建", "买票"],
            "request": [
                {"name": "train_number", "type": "string", "label": "车次号", "required": True},
                {"name": "departure_date", "type": "date", "label": "出发日期", "required": True},
                {"name": "passenger_id", "type": "string", "label": "乘客ID", "required": True},
                {"name": "seat_type", "type": "string", "label": "席别", "required": True},
                {"name": "selected_seat", "type": "string", "label": "选中座位", "required": False}
            ],
            "response": [
                {"name": "order_id", "type": "string", "desc": "订单ID"},
                {"name": "total_amount", "type": "float", "desc": "订单总额"},
                {"name": "expire_time", "type": "string", "desc": "支付截止时间"}
            ]
        },
        {
            "id": "api_order_query",
            "path": "/api/ticket/orders/{order_id}",
            "method": "GET",
            "desc": "查询订单详情",
            "instruction_variants": ["查询订单详情", "订单详情", "我的订单", "订单信息", "喂，我的订单呢", "帮我查查订单", "订单怎么样了", "查看订单"],
            "request": [
                {"name": "order_id", "type": "string", "label": "订单ID", "required": True}
            ],
            "response": [
                {"name": "order", "type": "object", "desc": "订单详情"},
                {"name": "status", "type": "string", "desc": "订单状态"},
                {"name": "tickets", "type": "array", "desc": "车票列表"}
            ]
        },
        {
            "id": "api_order_list",
            "path": "/api/ticket/orders",
            "method": "GET",
            "desc": "查询订单列表",
            "instruction_variants": ["查询订单列表", "订单列表", "我的所有订单", "订单记录", "喂，我买过哪些票", "帮我看看订单", "订单历史", "所有订单"],
            "request": [
                {"name": "status", "type": "string", "label": "订单状态", "required": False},
                {"name": "start_date", "type": "date", "label": "开始日期", "required": False},
                {"name": "end_date", "type": "date", "label": "结束日期", "required": False}
            ],
            "response": [
                {"name": "orders", "type": "array", "desc": "订单列表"}
            ]
        },
        {
            "id": "api_payment",
            "workflow_only": True,
            "path": "/api/v1/payments",
            "method": "POST",
            "desc": "支付订单",
            "instruction_variants": ["支付订单", "付款", "支付", "我要付款", "喂，怎么付钱", "帮我支付", "付款怎么弄", "支付一下"],
            "request": [
                {"name": "order_id", "type": "string", "label": "订单ID", "required": True},
                {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}
            ],
            "response": [
                {"name": "payment_success", "type": "boolean", "desc": "支付是否成功"},
                {"name": "payment_id", "type": "string", "desc": "支付流水号"}
            ]
        },
        # ========== 退票流程专用 API ==========
        {
            "id": "api_ticket_validate",
            "workflow_only": True,
            "path": "/api/v1/tickets/{ticket_id}",
            "method": "GET",
            "desc": "验证车票信息",
            "instruction_variants": ["验证车票信息", "验证车票", "查验车票", "核对车票", "喂，这票是真的吗", "帮我验证车票", "车票怎么验证", "核实车票"],
            "request": [
                {"name": "ticket_id", "type": "string", "label": "车票号", "required": True},
                {"name": "passenger_id_card", "type": "string", "label": "身份证号", "required": True}
            ],
            "response": [
                {"name": "ticket_id", "type": "string", "desc": "车票号"},
                {"name": "ticket_info", "type": "object", "desc": "车票信息"},
                {"name": "original_amount", "type": "float", "desc": "原票价"}
            ]
        },
        {
            "id": "api_refund_policy",
            "workflow_only": True,
            "path": "/api/v1/tickets/{ticket_id}/refund-policy",
            "method": "GET",
            "desc": "查询退票政策",
            "instruction_variants": ["查询退票政策", "退票政策", "退票规则", "能退多少", "喂，退票怎么算", "帮我看看退票政策", "退票扣多少", "退票规定"],
            "request": [
                {"name": "ticket_id", "type": "string", "label": "车票号", "required": True}
            ],
            "response": [
                {"name": "can_refund", "type": "boolean", "desc": "是否可以退票"},
                {"name": "refund_rate", "type": "float", "desc": "退票费率"},
                {"name": "policy_description", "type": "string", "desc": "政策说明"}
            ]
        },
        {
            "id": "api_refund_calculate",
            "workflow_only": True,
            "path": "/api/v1/tickets/{ticket_id}/refund-calculate",
            "method": "POST",
            "desc": "计算退款金额",
            "instruction_variants": ["计算退款金额", "退款多少", "能退多少钱", "退款金额", "喂，退票能退多少", "帮我算算退款", "退款怎么算", "算一下退款"],
            "request": [
                {"name": "ticket_id", "type": "string", "label": "车票号", "required": True}
            ],
            "response": [
                {"name": "refund_fee", "type": "float", "desc": "手续费"},
                {"name": "refund_amount", "type": "float", "desc": "实际退款金额"}
            ]
        },
        {
            "id": "api_refund_confirm",
            "workflow_only": True,
            "path": "/api/v1/tickets/{ticket_id}/refund-confirm",
            "method": "POST",
            "desc": "确认退票",
            "instruction_variants": ["确认退票", "退票确认", "确认退", "我确认退票", "喂，确认退票", "帮我确认", "退票确定", "确认一下"],
            "request": [
                {"name": "ticket_id", "type": "string", "label": "车票号", "required": True},
                {"name": "confirm_refund", "type": "boolean", "label": "确认退票", "required": True},
                {"name": "refund_reason", "type": "string", "label": "退票原因", "required": True}
            ],
            "response": [
                {"name": "confirm_refund", "type": "boolean", "desc": "是否确认退票"}
            ]
        },
        {
            "id": "api_ticket_cancel",
            "workflow_only": True,
            "path": "/api/v1/tickets/{ticket_id}/refund",
            "method": "POST",
            "desc": "执行退票",
            "instruction_variants": ["执行退票", "退票", "取消车票", "退掉", "喂，我要退票", "帮我退票", "退票怎么办", "取消订单"],
            "request": [
                {"name": "ticket_id", "type": "string", "label": "车票号", "required": True},
                {"name": "refund_reason", "type": "string", "label": "退票原因", "required": True},
                {"name": "refund_amount", "type": "float", "label": "退款金额", "required": True}
            ],
            "response": [
                {"name": "refund_id", "type": "string", "desc": "退款记录ID"},
                {"name": "refund_status", "type": "string", "desc": "退款状态"}
            ]
        },
        # ========== 改签流程专用 API ==========
        {
            "id": "api_ticket_change",
            "workflow_only": True,
            "path": "/api/ticket/orders/{order_id}/change",
            "method": "POST",
            "desc": "改签",
            "instruction_variants": ["改签", "换票", "改车次", "改时间", "喂，我要改签", "帮我改签", "改签怎么办", "换个车次"],
            "request": [
                {"name": "order_id", "type": "string", "label": "订单ID", "required": True},
                {"name": "ticket_id", "type": "string", "label": "车票ID", "required": True},
                {"name": "new_train_no", "type": "string", "label": "新车次号", "required": True},
                {"name": "new_date", "type": "date", "label": "新日期", "required": True},
                {"name": "new_seat_type", "type": "string", "label": "新席别", "required": True}
            ],
            "response": [
                {"name": "new_ticket_id", "type": "string", "desc": "新车票ID"},
                {"name": "price_diff", "type": "float", "desc": "差价"}
            ]
        },
        {
            "id": "api_seat_select",
            "path": "/api/v1/trains/{train_number}/seats",
            "method": "GET",
            "desc": "查询可选席别和座位",
            "instruction_variants": ["查询可选席别和座位", "选座位", "查座位", "有什么座位", "喂，还有座吗", "帮我选座", "座位怎么选", "查一下座位"],
            "request": [
                {"name": "train_number", "type": "string", "label": "车次号", "required": True},
                {"name": "departure_date", "type": "date", "label": "日期", "required": True}
            ],
            "response": [
                {"name": "available_seats", "type": "array", "desc": "可选座位列表（按席别分组）"},
                {"name": "seat_type", "type": "string", "desc": "选中的席别"},
                {"name": "selected_seat", "type": "string", "desc": "选中的座位"},
                {"name": "seat_price", "type": "float", "desc": "座位票价"}
            ]
        },
        {
            "id": "api_ticket_price",
            "path": "/api/ticket/price",
            "method": "GET",
            "desc": "查询票价",
            "instruction_variants": ["查询票价", "票价多少", "多少钱", "价格", "喂，这票多少钱", "帮我查查票价", "票价怎么算", "查一下价格"],
            "request": [
                {"name": "train_no", "type": "string", "label": "车次号", "required": True},
                {"name": "from_station", "type": "string", "label": "出发站", "required": True},
                {"name": "to_station", "type": "string", "label": "到达站", "required": True}
            ],
            "response": [
                {"name": "prices", "type": "array", "desc": "各席别票价"}
            ]
        },
        {
            "id": "api_delay_info",
            "path": "/api/trains/{train_no}/delay",
            "method": "GET",
            "desc": "查询晚点信息",
            "instruction_variants": ["查询晚点信息", "晚点了吗", "车晚点没", "延误信息", "喂，车晚点了吗", "帮我查查晚点", "晚点多久", "有没有延误"],
            "request": [
                {"name": "train_no", "type": "string", "label": "车次号", "required": True},
                {"name": "date", "type": "date", "label": "日期", "required": True}
            ],
            "response": [
                {"name": "is_delayed", "type": "boolean", "desc": "是否晚点"},
                {"name": "delay_minutes", "type": "integer", "desc": "晚点分钟数"},
                {"name": "reason", "type": "string", "desc": "晚点原因"}
            ]
        },
        # ========== 管理员统计 API ==========
        {"id": "api_admin_ticket_stats", "path": "/api/v1/trains/admin/ticket/stats", "method": "GET", "desc": "查询售票统计", "name": "售票统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询售票统计", "售票统计", "售票数据", "票务统计", "喂，今天卖了多少票", "帮我看看售票", "售票情况", "票卖得怎么样"], "request": [{"name": "date_range", "type": "string", "label": "日期范围", "required": False}], "response": [{"name": "today_sales", "type": "integer", "desc": "今日售票"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_route_analysis", "path": "/api/v1/trains/admin/route/analysis", "method": "GET", "desc": "查询线路分析", "name": "线路分析", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询线路分析", "线路分析", "线路数据", "客流分析", "喂，哪条线路人多", "帮我看看线路", "线路情况", "客流量怎么样"], "request": [], "response": [{"name": "routes", "type": "array", "desc": "线路"}, {"name": "passengers", "type": "array", "desc": "客流量"}]},
        {"id": "api_admin_passenger_trend", "path": "/api/v1/trains/admin/passenger/trend", "method": "GET", "desc": "查询客流趋势", "name": "客流趋势", "response_type": "chart", "chart_type": "line",
         "instruction_variants": ["查询客流趋势", "客流趋势", "客流数据", "乘客趋势", "喂，客流怎么样", "帮我看看客流", "客流变化", "乘客多不多"], "request": [{"name": "days", "type": "integer", "label": "天数", "required": False}], "response": [{"name": "dates", "type": "array", "desc": "日期"}, {"name": "passengers", "type": "array", "desc": "客流量"}]}
    ],
    "workflows": [
        # ========== 购票流程（调整：乘客验证 → 查询车次 → 选择席别座位 → 创建订单 → 支付 → 出票通知） ==========
        {
            "id": "workflow_book_ticket",
            "name": "购票流程",
            "description": "完整的在线购票业务流程，包括乘客验证、车次查询、席别选择、订单创建、支付处理和出票通知",
            "business_scenario": "train_ticket",
            "status": "active",
            "instruction_variants": ["购票流程", "买票", "购票", "订票", "喂，我要买票", "帮我买票", "买票怎么办", "订火车票"],
            "user_intents": ["买票", "购票", "订票", "火车票", "买火车票", "预订火车票"],
            "trigger_keywords": ["买票", "购票", "订票", "火车票", "预订"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始购票流程"}},
                {
                    "id": "passenger_verification",
                    "name": "乘客身份验证",
                    "type": "api_call",
                    "description": "验证乘客身份信息",
                    "config": {
                        "api_id": "api_passenger_verify",
                        "api_endpoint": "/api/v1/passengers/verify",
                        "method": "POST",
                        "parameters": {
                            "name": "${name}",
                            "id_card": "${id_card}",
                            "phone": "${phone}",
                            "passenger_type": "${passenger_type}"
                        }
                    },
                    "outputs": [
                        {"name": "passenger_id", "type": "string", "description": "乘客ID"},
                        {"name": "passenger_name", "type": "string", "description": "乘客姓名"},
                        {"name": "id_card", "type": "string", "description": "身份证号"}
                    ],
                    "ai_instructions": {"user_message": "请填写乘客信息进行身份验证", "action": "验证乘客身份"}
                },
                {
                    "id": "train_query",
                    "name": "查询车次",
                    "type": "api_call",
                    "description": "查询可选车次列表",
                    "config": {
                        "api_id": "api_train_list",
                        "api_endpoint": "/api/trains",
                        "method": "GET",
                        "parameters": {
                            "from_station": "${from_station}",
                            "to_station": "${to_station}",
                            "date": "${departure_date}"
                        }
                    },
                    "outputs": [
                        {"name": "trains", "type": "array", "description": "可选车次列表"},
                        {"name": "train_number", "type": "string", "description": "选中的车次号"}
                    ],
                    "ai_instructions": {"user_message": "请输入出发地、目的地和日期查询车次", "action": "查询车次"}
                },
                {
                    "id": "seat_selection",
                    "name": "选择席别座位",
                    "type": "api_call",
                    "description": "查询并选择席别和座位",
                    "config": {
                        "api_id": "api_seat_select",
                        "api_endpoint": "/api/v1/trains/{train_number}/seats",
                        "method": "GET",
                        "parameters": {
                            "train_number": "${train_number}",
                            "departure_date": "${departure_date}"
                        }
                    },
                    "outputs": [
                        {"name": "available_seats", "type": "array", "description": "可选座位列表"},
                        {"name": "seat_type", "type": "string", "description": "选中的席别"},
                        {"name": "selected_seat", "type": "string", "description": "选中的座位"},
                        {"name": "seat_price", "type": "float", "description": "座位票价"}
                    ],
                    "ai_instructions": {"user_message": "请选择席别和座位", "action": "选择座位"}
                },
                {
                    "id": "order_creation",
                    "name": "创建订单",
                    "type": "api_call",
                    "description": "创建购票订单",
                    "config": {
                        "api_id": "api_create_ticket",
                        "api_endpoint": "/api/v1/orders",
                        "method": "POST",
                        "parameters": {
                            "train_number": "${train_number}",
                            "departure_date": "${departure_date}",
                            "passenger_id": "${passenger_id}",
                            "seat_type": "${seat_type}",
                            "selected_seat": "${selected_seat}"
                        }
                    },
                    "outputs": [
                        {"name": "order_id", "type": "string", "description": "订单号"},
                        {"name": "total_amount", "type": "float", "description": "订单总额"},
                        {"name": "expire_time", "type": "string", "description": "支付截止时间"}
                    ],
                    "ai_instructions": {"user_message": "正在创建订单", "action": "创建订单"}
                },
                {
                    "id": "payment_processing",
                    "name": "支付处理",
                    "type": "api_call",
                    "description": "处理订单支付",
                    "config": {
                        "api_id": "api_payment",
                        "api_endpoint": "/api/v1/payments",
                        "method": "POST",
                        "parameters": {
                            "order_id": "${order_id}",
                            "payment_method": "${payment_method}"
                        }
                    },
                    "outputs": [
                        {"name": "payment_success", "type": "boolean", "description": "支付是否成功"},
                        {"name": "payment_id", "type": "string", "description": "支付流水号"}
                    ],
                    "ai_instructions": {"user_message": "请选择支付方式完成支付", "action": "完成支付"}
                },
                {
                    "id": "ticket_notification",
                    "name": "出票通知",
                    "type": "notification",
                    "description": "发送出票成功通知",
                    "config": {
                        "message_template": "购票成功！订单号：${order_id}，车次：${train_number}，席别：${seat_type}，座位：${selected_seat}，请在发车前取票。"
                    },
                    "outputs": [
                        {"name": "ticket_number", "type": "string", "description": "车票号"}
                    ],
                    "ai_instructions": {"user_message": "购票成功", "action": "发送出票通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "购票完成"}}
            ],
            "edges": [
                {"source": "start", "target": "passenger_verification"},
                {"source": "passenger_verification", "target": "train_query"},
                {"source": "train_query", "target": "seat_selection"},
                {"source": "seat_selection", "target": "order_creation"},
                {"source": "order_creation", "target": "payment_processing"},
                {"source": "payment_processing", "target": "ticket_notification"},
                {"source": "ticket_notification", "target": "end"}
            ]
        },
        # ========== 退票流程（与后端 template 对齐：车票验证 → 政策检查 → 金额计算 → 确认 → 处理 → 通知） ==========
        {
            "id": "workflow_refund",
            "name": "退票流程",
            "description": "完整的车票退票业务流程，包括车票验证、退票政策检查、退款金额计算、用户确认、退款处理和通知",
            "business_scenario": "train_ticket",
            "status": "active",
            "instruction_variants": ["退票流程", "退票", "退火车票", "取消订单", "喂，我要退票", "帮我退票", "退票怎么办", "不想坐了"],
            "user_intents": ["退票", "退火车票", "取消订单", "不想坐了", "退款"],
            "trigger_keywords": ["退票", "退", "取消", "退款"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始退票流程"}},
                {
                    "id": "ticket_validation",
                    "name": "车票验证",
                    "type": "api_call",
                    "description": "验证车票信息",
                    "config": {
                        "api_id": "api_ticket_validate",
                        "api_endpoint": "/api/v1/tickets/{ticket_id}",
                        "method": "GET",
                        "parameters": {
                            "ticket_id": "${ticket_id}",
                            "passenger_id_card": "${passenger_id_card}"
                        }
                    },
                    "outputs": [
                        {"name": "ticket_id", "type": "string", "description": "车票号"},
                        {"name": "ticket_info", "type": "object", "description": "车票信息"},
                        {"name": "original_amount", "type": "float", "description": "原票价"}
                    ],
                    "ai_instructions": {"user_message": "请输入车票号和身份证号验证车票", "action": "验证车票"}
                },
                {
                    "id": "refund_policy_check",
                    "name": "退票政策检查",
                    "type": "api_call",
                    "description": "检查退票政策",
                    "config": {
                        "api_id": "api_refund_policy",
                        "api_endpoint": "/api/v1/tickets/{ticket_id}/refund-policy",
                        "method": "GET",
                        "parameters": {
                            "ticket_id": "${ticket_id}"
                        }
                    },
                    "outputs": [
                        {"name": "can_refund", "type": "boolean", "description": "是否可以退票"},
                        {"name": "refund_rate", "type": "float", "description": "退票费率"},
                        {"name": "policy_description", "type": "string", "description": "政策说明"}
                    ],
                    "ai_instructions": {"user_message": "正在检查退票政策", "action": "检查退票政策"}
                },
                {
                    "id": "refund_amount_calculation",
                    "name": "退款金额计算",
                    "type": "api_call",
                    "description": "计算退款金额",
                    "config": {
                        "api_id": "api_refund_calculate",
                        "api_endpoint": "/api/v1/tickets/{ticket_id}/refund-calculate",
                        "method": "POST",
                        "parameters": {
                            "ticket_id": "${ticket_id}"
                        }
                    },
                    "outputs": [
                        {"name": "refund_fee", "type": "float", "description": "手续费"},
                        {"name": "refund_amount", "type": "float", "description": "实际退款金额"}
                    ],
                    "ai_instructions": {"user_message": "正在计算退款金额", "action": "计算退款金额"}
                },
                {
                    "id": "refund_confirmation",
                    "name": "退款确认",
                    "type": "api_call",
                    "description": "用户确认退票",
                    "config": {
                        "api_id": "api_refund_confirm",
                        "api_endpoint": "/api/v1/tickets/{ticket_id}/refund-confirm",
                        "method": "POST",
                        "parameters": {
                            "ticket_id": "${ticket_id}",
                            "confirm_refund": "${confirm_refund}",
                            "refund_reason": "${refund_reason}"
                        }
                    },
                    "outputs": [
                        {"name": "confirm_refund", "type": "boolean", "description": "是否确认退票"}
                    ],
                    "ai_instructions": {"user_message": "请确认退票信息并填写退票原因", "action": "确认退票"}
                },
                {
                    "id": "refund_processing",
                    "name": "退款处理",
                    "type": "api_call",
                    "description": "处理退款",
                    "config": {
                        "api_id": "api_ticket_cancel",
                        "api_endpoint": "/api/v1/tickets/{ticket_id}/refund",
                        "method": "POST",
                        "parameters": {
                            "ticket_id": "${ticket_id}",
                            "refund_reason": "${refund_reason}",
                            "refund_amount": "${refund_amount}"
                        }
                    },
                    "outputs": [
                        {"name": "refund_id", "type": "string", "description": "退款记录ID"},
                        {"name": "refund_status", "type": "string", "description": "退款状态"}
                    ],
                    "ai_instructions": {"user_message": "正在处理退款", "action": "处理退款"}
                },
                {
                    "id": "refund_notification",
                    "name": "退款通知",
                    "type": "notification",
                    "description": "发送退款成功通知",
                    "config": {
                        "message_template": "退票成功！退款金额：${refund_amount}元，手续费：${refund_fee}元，预计3-5个工作日到账。"
                    },
                    "outputs": [],
                    "ai_instructions": {"user_message": "退票成功", "action": "发送退款通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退票完成"}}
            ],
            "edges": [
                {"source": "start", "target": "ticket_validation"},
                {"source": "ticket_validation", "target": "refund_policy_check"},
                {"source": "refund_policy_check", "target": "refund_amount_calculation"},
                {"source": "refund_amount_calculation", "target": "refund_confirmation"},
                {"source": "refund_confirmation", "target": "refund_processing"},
                {"source": "refund_processing", "target": "refund_notification"},
                {"source": "refund_notification", "target": "end"}
            ]
        },
        # ========== 改签流程 ==========
        {
            "id": "workflow_change_ticket",
            "name": "改签流程",
            "description": "办理火车票改签",
            "business_scenario": "train_ticket",
            "status": "active",
            "instruction_variants": ["改签流程", "改签", "换票", "改车次", "喂，我要改签", "帮我改签", "改签怎么办", "换个时间"],
            "user_intents": ["改签", "换票", "改时间", "改车次"],
            "trigger_keywords": ["改签", "换票", "改时间"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始改签流程"}},
                {
                    "id": "n_change",
                    "name": "执行改签",
                    "type": "api_call",
                    "description": "填写改签信息并提交",
                    "config": {
                        "api_id": "api_ticket_change",
                        "api_endpoint": "/api/ticket/orders/{order_id}/change",
                        "method": "POST",
                        "parameters": {
                            "order_id": "${order_id}",
                            "ticket_id": "${ticket_id}",
                            "new_train_no": "${new_train_no}",
                            "new_date": "${new_date}",
                            "new_seat_type": "${new_seat_type}"
                        }
                    },
                    "outputs": [{"name": "new_ticket_id", "type": "string"}, {"name": "price_diff", "type": "float"}],
                    "ai_instructions": {"user_message": "请填写改签信息", "action": "执行改签"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "改签完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_change"},
                {"source": "n_change", "target": "end"}
            ]
        },
        # ========== 订单查询流程 ==========
        {
            "id": "workflow_order_query",
            "name": "订单查询",
            "description": "查询火车票订单",
            "business_scenario": "train_ticket",
            "status": "active",
            "instruction_variants": ["订单查询", "查订单", "我的订单", "订单列表", "喂，我的订单呢", "帮我查查订单", "订单怎么查", "查看订单"],
            "user_intents": ["查订单", "我的订单", "订单查询"],
            "trigger_keywords": ["查订单", "订单", "查看订单"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始订单查询"}},
                {
                    "id": "n_query",
                    "name": "查询订单",
                    "type": "api_call",
                    "description": "查询订单列表",
                    "config": {
                        "api_id": "api_order_list",
                        "api_endpoint": "/api/ticket/orders",
                        "method": "GET",
                        "parameters": {
                            "status": "${status}"
                        }
                    },
                    "outputs": [{"name": "orders", "type": "array"}],
                    "ai_instructions": {"user_message": "请选择查询条件", "action": "查询订单"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "查询完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "end"}
            ]
        }
    ]
}
