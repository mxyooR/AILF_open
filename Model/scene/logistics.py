# logistics.py - 物流场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

LOGISTICS_SCENE = {
    "domain": "logistics",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_express_query", "path": "/api/logistics/express/{tracking_no}", "method": "GET", "desc": "查询快递",
         "instruction_variants": ["查询快递", "查快递", "快递到哪了", "物流查询", "帮我查快递", "快递单号查询", "物流轨迹", "快递状态"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}],
         "response": [{"name": "status", "type": "string", "desc": "物流状态"}, {"name": "traces", "type": "array", "desc": "物流轨迹"}, {"name": "estimated_time", "type": "string", "desc": "预计送达时间"}]},
        {"id": "api_express_price", "path": "/api/logistics/price", "method": "GET", "desc": "查询运费",
         "instruction_variants": ["查询运费", "运费多少", "快递费用", "帮我算运费", "寄件运费", "运费查询", "寄快递多少钱", "运费预估"],
         "request": [{"name": "from_city", "type": "string", "label": "寄件城市", "required": True}, {"name": "to_city", "type": "string", "label": "收件城市", "required": True}, {"name": "weight", "type": "float", "label": "重量", "required": True}, {"name": "service_type", "type": "string", "label": "服务类型", "required": False}],
         "response": [{"name": "price", "type": "float", "desc": "运费"}, {"name": "estimated_days", "type": "integer", "desc": "预计天数"}]},
        {"id": "api_address_list", "path": "/api/logistics/addresses", "method": "GET", "desc": "查询常用地址",
         "instruction_variants": ["查询常用地址", "地址簿", "我的地址", "收寄地址", "帮我看地址", "常用地址列表", "地址列表", "寄件地址"],
         "request": [{"name": "type", "type": "string", "label": "地址类型", "required": False}],
         "response": [{"name": "addresses", "type": "array", "desc": "地址列表"}]},
        {"id": "api_sender_verify", "workflow_only": True, "path": "/api/logistics/sender/verify", "method": "POST", "desc": "寄件人验证",
         "instruction_variants": ["寄件人验证", "验证寄件人", "寄件身份核验", "确认寄件人信息", "帮我验证寄件人", "寄件人怎么验证", "核验寄件人", "寄件人身份确认"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "phone", "type": "string", "label": "电话", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": False}],
         "response": [{"name": "sender_id", "type": "string", "desc": "寄件人ID"}, {"name": "verified", "type": "boolean", "desc": "是否验证通过"}]},
        {"id": "api_express_create", "workflow_only": True, "path": "/api/logistics/express", "method": "POST", "desc": "寄快递",
         "instruction_variants": ["寄快递", "创建快递单", "我要寄件", "帮我寄快递", "下快递单", "寄件下单", "发快递", "寄件"],
         "request": [{"name": "sender_id", "type": "string", "label": "寄件人ID", "required": True}, {"name": "sender_address", "type": "string", "label": "寄件地址", "required": True}, {"name": "receiver_name", "type": "string", "label": "收件人姓名", "required": True}, {"name": "receiver_phone", "type": "string", "label": "收件人电话", "required": True}, {"name": "receiver_address", "type": "string", "label": "收件地址", "required": True}, {"name": "weight", "type": "float", "label": "重量(kg)", "required": True}, {"name": "service_type", "type": "string", "label": "服务类型", "required": False}, {"name": "insured_value", "type": "float", "label": "保价金额", "required": False}],
         "response": [{"name": "tracking_no", "type": "string", "desc": "快递单号"}, {"name": "price", "type": "float", "desc": "运费"}]},
        {"id": "api_express_pay", "workflow_only": True, "path": "/api/logistics/express/{tracking_no}/pay", "method": "POST", "desc": "快递支付",
         "instruction_variants": ["快递支付", "运费支付", "我要付款", "帮我付运费", "快递怎么付款", "支付运费", "订单付款", "寄件付款"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "payment_id", "type": "string", "desc": "支付流水号"}]},
        {"id": "api_pickup_time_slots", "path": "/api/logistics/pickup/slots", "method": "GET", "desc": "查询取件时间段",
         "instruction_variants": ["查询取件时间段", "取件时间", "上门取件时间", "取件时段查询", "帮我查取件时间", "有哪些取件时间", "取件时间段", "取件时间选择"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": True}],
         "response": [{"name": "slots", "type": "array", "desc": "可选时间段"}]},
        {"id": "api_pickup_book", "workflow_only": True, "path": "/api/logistics/pickup", "method": "POST", "desc": "预约上门取件",
         "instruction_variants": ["预约上门取件", "预约取件", "叫快递上门", "帮我预约取件", "上门取件", "取件预约", "预约快递员", "上门取件预约"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "pickup_date", "type": "date", "label": "取件日期", "required": True}, {"name": "pickup_slot", "type": "string", "label": "取件时段", "required": True}],
         "response": [{"name": "pickup_id", "type": "string", "desc": "取件单号"}, {"name": "courier_phone", "type": "string", "desc": "快递员电话"}]},
        {"id": "api_delivery_sign", "workflow_only": True, "path": "/api/logistics/sign", "method": "POST", "desc": "确认签收",
         "instruction_variants": ["确认签收", "签收确认", "快递签收", "帮我确认签收", "已签收", "确认收货", "签收一下", "签收快递"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "sign_code", "type": "string", "label": "签收码", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_complaint_create", "workflow_only": True, "path": "/api/logistics/complaints", "method": "POST", "desc": "投诉建议",
         "instruction_variants": ["投诉建议", "我要投诉", "提交投诉", "帮我投诉", "快递投诉", "投诉快递", "投诉处理", "提交投诉单"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "type", "type": "string", "label": "投诉类型", "required": True}, {"name": "content", "type": "string", "label": "投诉内容", "required": True}],
         "response": [{"name": "complaint_id", "type": "string", "desc": "投诉单号"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_order_list", "workflow_only": True, "path": "/api/logistics/admin/orders", "method": "GET", "desc": "查询订单列表（管理员）",
         "instruction_variants": ["查询订单列表", "查看订单列表", "订单管理", "订单列表", "帮我查订单", "快递订单", "订单情况", "待处理订单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "date", "type": "date", "label": "日期", "required": False}],
         "response": [{"name": "orders", "type": "array", "desc": "订单列表"}, {"name": "pending_pickup", "type": "integer", "desc": "待取件数"}, {"name": "in_transit", "type": "integer", "desc": "运输中数"}]},
        {"id": "api_admin_order_detail", "workflow_only": True, "path": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "desc": "查询订单详情（管理员）",
         "instruction_variants": ["查询订单详情", "订单详情", "查看订单", "订单信息", "帮我看订单详情", "订单内容", "快递订单详情", "查询订单信息"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}],
         "response": [{"name": "order", "type": "object", "desc": "订单详情"}, {"name": "sender", "type": "object", "desc": "寄件人信息"}, {"name": "receiver", "type": "object", "desc": "收件人信息"}]},
        {"id": "api_admin_courier_list", "workflow_only": True, "path": "/api/logistics/admin/couriers", "method": "GET", "desc": "查询快递员列表",
         "instruction_variants": ["查询快递员列表", "快递员列表", "配送员列表", "帮我查快递员", "可用快递员", "快递员情况", "骑手列表", "快递员查询"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "area", "type": "string", "label": "区域", "required": False}],
         "response": [{"name": "couriers", "type": "array", "desc": "快递员列表"}, {"name": "available_count", "type": "integer", "desc": "可用人数"}]},
        {"id": "api_admin_dispatch", "workflow_only": True, "path": "/api/logistics/admin/dispatch", "method": "POST", "desc": "派单",
         "instruction_variants": ["派单", "派件", "分配任务", "派单给快递员", "帮我派单", "安排取件", "分配快递员", "派送任务"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "courier_id", "type": "string", "label": "快递员ID", "required": True}, {"name": "task_type", "type": "string", "label": "任务类型", "required": True}],
         "response": [{"name": "dispatch_id", "type": "string", "desc": "派单ID"}, {"name": "courier_name", "type": "string", "desc": "快递员姓名"}]},
        {"id": "api_admin_pickup_confirm", "workflow_only": True, "path": "/api/logistics/admin/pickup/{pickup_id}/confirm", "method": "POST", "desc": "确认取件",
         "instruction_variants": ["确认取件", "取件确认", "快递员取件确认", "帮我确认取件", "已取件", "取件核实", "取件确认一下", "确认收件"],
         "request": [{"name": "pickup_id", "type": "string", "label": "取件单号", "required": True}, {"name": "actual_weight", "type": "float", "label": "实际重量", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "price_diff", "type": "float", "desc": "运费差额"}]},
        {"id": "api_admin_transit_update", "workflow_only": True, "path": "/api/logistics/admin/transit", "method": "POST", "desc": "更新运输状态",
         "instruction_variants": ["更新运输状态", "更新物流状态", "物流状态更新", "帮我更新状态", "运输状态变更", "更新物流", "改物流状态", "更新当前位置"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "status", "type": "string", "label": "状态", "required": True}, {"name": "location", "type": "string", "label": "当前位置", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_delivery_assign", "workflow_only": True, "path": "/api/logistics/admin/delivery/assign", "method": "POST", "desc": "分配派送",
         "instruction_variants": ["分配派送", "安排派送", "派送分配", "帮我分配派送", "派送员安排", "分配送件", "安排配送", "派送任务"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "courier_id", "type": "string", "label": "快递员ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "estimated_time", "type": "string", "desc": "预计送达时间"}]},
        {"id": "api_admin_delivery_complete", "workflow_only": True, "path": "/api/logistics/admin/delivery/{tracking_no}/complete", "method": "POST", "desc": "完成派送",
         "instruction_variants": ["完成派送", "派送完成", "配送完成", "帮我完成派送", "签收完成", "完成配送", "派送结束", "送达完成"],
         "request": [{"name": "tracking_no", "type": "string", "label": "快递单号", "required": True}, {"name": "sign_type", "type": "string", "label": "签收方式", "required": True}, {"name": "sign_photo", "type": "string", "label": "签收照片", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "sign_time", "type": "datetime", "desc": "签收时间"}]},
        {"id": "api_admin_complaint_list", "workflow_only": True, "path": "/api/logistics/admin/complaints", "method": "GET", "desc": "查询投诉列表",
         "instruction_variants": ["查询投诉列表", "投诉列表", "待处理投诉", "帮我看投诉", "投诉管理", "投诉记录", "投诉情况", "投诉清单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "complaints", "type": "array", "desc": "投诉列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数量"}]},
        {"id": "api_admin_complaint_handle", "workflow_only": True, "path": "/api/logistics/admin/complaints/{complaint_id}/handle", "method": "POST", "desc": "处理投诉",
         "instruction_variants": ["处理投诉", "投诉处理", "处理客户投诉", "帮我处理投诉", "处理投诉单", "投诉处理流程", "投诉解决", "处理投诉申请"],
         "request": [{"name": "complaint_id", "type": "string", "label": "投诉单号", "required": True}, {"name": "action", "type": "string", "label": "处理动作", "required": True}, {"name": "result", "type": "string", "label": "处理结果", "required": True}, {"name": "compensation", "type": "float", "label": "赔偿金额", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        # ========== 管理员统计 API ==========
        {"id": "api_admin_delivery_stats", "path": "/api/logistics/admin/stats", "method": "GET", "desc": "查询配送统计", "name": "配送统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询配送统计", "配送统计", "今日配送量", "配送数据", "帮我看配送统计", "配送报表", "配送趋势", "配送情况"],
         "request": [], "response": [{"name": "today_count", "type": "integer", "desc": "今日配送"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_courier_performance", "path": "/api/logistics/admin/courier/performance", "method": "GET", "desc": "查询快递员绩效", "name": "快递员绩效", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询快递员绩效", "快递员绩效", "配送员绩效", "帮我看快递员绩效", "骑手绩效", "快递员表现", "绩效统计", "快递员数据"],
         "request": [], "response": [{"name": "couriers", "type": "array", "desc": "快递员"}, {"name": "deliveries", "type": "array", "desc": "配送量"}]},
        {"id": "api_admin_area_analysis", "path": "/api/logistics/admin/area/analysis", "method": "GET", "desc": "查询区域分析", "name": "区域分析", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询区域分析", "区域分析", "区域订单分布", "帮我看区域数据", "区域占比", "区域订单统计", "区域情况", "区域分析报表"],
         "request": [], "response": [{"name": "areas", "type": "array", "desc": "区域"}, {"name": "orders", "type": "array", "desc": "订单量"}]},
    ],

    "workflows": [
        # ========== 用户：完整寄件流程（7步：查询运费 → 身份验证 → 填写信息 → 创建订单 → 支付 → 预约取件 → 通知） ==========
        {
            "id": "workflow_full_send",
            "name": "完整寄件流程",
            "description": "完整的寄快递流程，包括运费查询、身份验证、订单创建、支付和预约取件",
            "instruction_variants": ["完整寄件流程", "寄快递流程", "我要寄快递", "帮我寄件", "寄件全流程", "寄快递怎么走", "寄件流程走一下", "寄件从下单到取件"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["寄快递", "寄件", "发快递"],
            "trigger_keywords": ["寄快递", "寄件", "发快递"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始寄件"}},
                {
                    "id": "n_query_price",
                    "name": "查询运费",
                    "type": "api_call",
                    "description": "查询预估运费",
                    "config": {"api_id": "api_express_price", "api_endpoint": "/api/logistics/price", "method": "GET", "parameters": {"from_city": "${from_city}", "to_city": "${to_city}", "weight": "${weight}", "service_type": "${service_type}"}},
                    "outputs": [{"name": "price", "type": "float", "description": "运费"}, {"name": "estimated_days", "type": "integer", "description": "预计天数"}],
                    "ai_instructions": {"user_message": "请输入寄件城市、收件城市和重量", "action": "查询运费"}
                },
                {
                    "id": "n_verify",
                    "name": "寄件人验证",
                    "type": "api_call",
                    "description": "验证寄件人身份",
                    "config": {"api_id": "api_sender_verify", "api_endpoint": "/api/logistics/sender/verify", "method": "POST", "parameters": {"name": "${sender_name}", "phone": "${sender_phone}", "id_card": "${sender_id_card}"}},
                    "outputs": [{"name": "sender_id", "type": "string", "description": "寄件人ID"}, {"name": "verified", "type": "boolean", "description": "是否验证通过"}],
                    "ai_instructions": {"user_message": "请填写寄件人信息进行验证", "action": "寄件人验证"}
                },
                {
                    "id": "n_create",
                    "name": "创建寄件订单",
                    "type": "api_call",
                    "description": "填写收件信息并创建订单",
                    "config": {"api_id": "api_express_create", "api_endpoint": "/api/logistics/express", "method": "POST", "parameters": {"sender_id": "${sender_id}", "sender_address": "${sender_address}", "receiver_name": "${receiver_name}", "receiver_phone": "${receiver_phone}", "receiver_address": "${receiver_address}", "weight": "${weight}", "service_type": "${service_type}", "insured_value": "${insured_value}"}},
                    "outputs": [{"name": "tracking_no", "type": "string", "description": "快递单号"}, {"name": "price", "type": "float", "description": "运费"}],
                    "ai_instructions": {"user_message": "请填写收件人信息", "action": "创建寄件订单"}
                },
                {
                    "id": "n_pay",
                    "name": "支付运费",
                    "type": "api_call",
                    "description": "支付快递运费",
                    "config": {"api_id": "api_express_pay", "api_endpoint": "/api/logistics/express/{tracking_no}/pay", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "payment_id", "type": "string", "description": "支付流水号"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "支付运费"}
                },
                {
                    "id": "n_pickup_slots",
                    "name": "查询取件时段",
                    "type": "api_call",
                    "description": "查询可选的取件时段",
                    "config": {"api_id": "api_pickup_time_slots", "api_endpoint": "/api/logistics/pickup/slots", "method": "GET", "parameters": {"date": "${pickup_date}"}},
                    "outputs": [{"name": "slots", "type": "array", "description": "可选时间段"}, {"name": "pickup_slot", "type": "string", "description": "选中时段"}],
                    "ai_instructions": {"user_message": "请选择取件日期", "action": "查询取件时段"}
                },
                {
                    "id": "n_pickup",
                    "name": "预约取件",
                    "type": "api_call",
                    "description": "预约上门取件",
                    "config": {"api_id": "api_pickup_book", "api_endpoint": "/api/logistics/pickup", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "pickup_date": "${pickup_date}", "pickup_slot": "${pickup_slot}"}},
                    "outputs": [{"name": "pickup_id", "type": "string", "description": "取件单号"}, {"name": "courier_phone", "type": "string", "description": "快递员电话"}],
                    "ai_instructions": {"user_message": "请选择取件时段", "action": "预约取件"}
                },
                {
                    "id": "n_notify",
                    "name": "寄件通知",
                    "type": "notification",
                    "description": "发送寄件成功通知",
                    "config": {"message_template": "寄件成功！快递单号：${tracking_no}，运费：${price}元，预计${estimated_days}天送达，快递员电话：${courier_phone}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "寄件成功", "action": "发送寄件通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "寄件完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query_price"},
                {"source": "n_query_price", "target": "n_verify"},
                {"source": "n_verify", "target": "n_create"},
                {"source": "n_create", "target": "n_pay"},
                {"source": "n_pay", "target": "n_pickup_slots"},
                {"source": "n_pickup_slots", "target": "n_pickup"},
                {"source": "n_pickup", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：快递查询签收流程（4步：查询快递 → 确认状态 → 签收 → 通知） ==========
        {
            "id": "workflow_query_sign",
            "name": "快递查询签收流程",
            "description": "查询快递状态并签收",
            "instruction_variants": ["快递查询签收流程", "查快递并签收", "我要查快递", "帮我查快递", "签收流程", "查快递流程", "快递状态查询", "查快递到签收"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["查快递", "签收", "收快递"],
            "trigger_keywords": ["查快递", "签收", "收快递"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始查询签收"}},
                {
                    "id": "n_query",
                    "name": "查询快递",
                    "type": "api_call",
                    "description": "查询快递状态",
                    "config": {"api_id": "api_express_query", "api_endpoint": "/api/logistics/express/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "status", "type": "string", "description": "物流状态"}, {"name": "traces", "type": "array", "description": "物流轨迹"}, {"name": "estimated_time", "type": "string", "description": "预计送达时间"}],
                    "ai_instructions": {"user_message": "请输入快递单号", "action": "查询快递"}
                },
                {
                    "id": "n_sign",
                    "name": "确认签收",
                    "type": "api_call",
                    "description": "确认签收快递",
                    "config": {"api_id": "api_delivery_sign", "api_endpoint": "/api/logistics/sign", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "sign_code": "${sign_code}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请确认签收", "action": "确认签收"}
                },
                {
                    "id": "n_notify",
                    "name": "签收通知",
                    "type": "notification",
                    "description": "发送签收成功通知",
                    "config": {"message_template": "签收成功！快递单号：${tracking_no}已签收。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "签收成功", "action": "发送签收通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "签收完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "n_sign"},
                {"source": "n_sign", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：投诉建议流程（4步：查询快递 → 填写投诉 → 提交 → 通知） ==========
        {
            "id": "workflow_complaint",
            "name": "投诉建议流程",
            "description": "快递投诉建议流程",
            "instruction_variants": ["投诉建议流程", "我要投诉", "快递投诉流程", "帮我投诉", "提交投诉流程", "投诉处理流程", "投诉快递", "投诉建议"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["投诉", "建议", "快递投诉"],
            "trigger_keywords": ["投诉", "建议", "快递投诉"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始投诉"}},
                {
                    "id": "n_query",
                    "name": "查询快递",
                    "type": "api_call",
                    "description": "查询要投诉的快递",
                    "config": {"api_id": "api_express_query", "api_endpoint": "/api/logistics/express/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "status", "type": "string", "description": "物流状态"}, {"name": "tracking_no", "type": "string", "description": "快递单号"}],
                    "ai_instructions": {"user_message": "请输入要投诉的快递单号", "action": "查询快递"}
                },
                {
                    "id": "n_complaint",
                    "name": "提交投诉",
                    "type": "api_call",
                    "description": "填写并提交投诉",
                    "config": {"api_id": "api_complaint_create", "api_endpoint": "/api/logistics/complaints", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "type": "${type}", "content": "${content}"}},
                    "outputs": [{"name": "complaint_id", "type": "string", "description": "投诉单号"}],
                    "ai_instructions": {"user_message": "请选择投诉类型并填写投诉内容", "action": "提交投诉"}
                },
                {
                    "id": "n_notify",
                    "name": "投诉提交通知",
                    "type": "notification",
                    "description": "发送投诉提交成功通知",
                    "config": {"message_template": "投诉已提交！投诉单号：${complaint_id}，我们将在24小时内处理。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "投诉已提交", "action": "发送投诉通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "投诉完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "n_complaint"},
                {"source": "n_complaint", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：派单流程（6步：查询待派订单 → 查看订单详情 → 查询可用快递员 → 派单 → 通知快递员 → 更新状态） ==========
        {
            "id": "workflow_admin_dispatch",
            "name": "管理员派单流程",
            "description": "管理员将新订单派给快递员取件",
            "instruction_variants": ["派单流程", "管理员派单", "分配订单流程", "指派快递员", "派单给快递员", "派件流程", "派单处理", "派单操作"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["派单", "分配订单", "指派快递员"],
            "trigger_keywords": ["派单", "分配订单", "指派快递员"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始派单"}},
                {
                    "id": "n_order_list",
                    "name": "查询待派订单",
                    "type": "api_call",
                    "description": "查询待派送的订单列表",
                    "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/logistics/admin/orders", "method": "GET", "parameters": {"status": "pending_dispatch"}},
                    "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}, {"name": "pending_pickup", "type": "integer", "description": "待取件数"}],
                    "ai_instructions": {"user_message": "查询待派送订单", "action": "查询待派订单"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看订单详情",
                    "type": "api_call",
                    "description": "查看选中订单的详细信息",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "sender", "type": "object", "description": "寄件人信息"}, {"name": "receiver", "type": "object", "description": "收件人信息"}],
                    "ai_instructions": {"user_message": "请选择要派送的订单", "action": "查看订单详情"}
                },
                {
                    "id": "n_courier_list",
                    "name": "查询可用快递员",
                    "type": "api_call",
                    "description": "查询该区域可用的快递员",
                    "config": {"api_id": "api_admin_courier_list", "api_endpoint": "/api/logistics/admin/couriers", "method": "GET", "parameters": {"status": "available", "area": "${sender_area}"}},
                    "outputs": [{"name": "couriers", "type": "array", "description": "快递员列表"}, {"name": "available_count", "type": "integer", "description": "可用人数"}],
                    "ai_instructions": {"user_message": "查询可用快递员", "action": "查询可用快递员"}
                },
                {
                    "id": "n_dispatch",
                    "name": "派单",
                    "type": "api_call",
                    "description": "将订单派给选中的快递员",
                    "config": {"api_id": "api_admin_dispatch", "api_endpoint": "/api/logistics/admin/dispatch", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "courier_id": "${courier_id}", "task_type": "pickup"}},
                    "outputs": [{"name": "dispatch_id", "type": "string", "description": "派单ID"}, {"name": "courier_name", "type": "string", "description": "快递员姓名"}],
                    "ai_instructions": {"user_message": "请选择快递员进行派单", "action": "派单"}
                },
                {
                    "id": "n_notify",
                    "name": "派单通知",
                    "type": "notification",
                    "description": "通知快递员新任务",
                    "config": {"message_template": "派单成功！订单${tracking_no}已派给${courier_name}，派单ID：${dispatch_id}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "派单成功", "action": "发送派单通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "派单完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_order_list"},
                {"source": "n_order_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_courier_list"},
                {"source": "n_courier_list", "target": "n_dispatch"},
                {"source": "n_dispatch", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：取件确认流程（5步：查询取件任务 → 查看订单详情 → 确认取件 → 更新运输状态 → 通知） ==========
        {
            "id": "workflow_admin_pickup_confirm",
            "name": "管理员取件确认流程",
            "description": "快递员取件后管理员确认并更新状态",
            "instruction_variants": ["取件确认流程", "管理员确认取件", "揽收确认流程", "取件完成确认", "确认取件操作", "取件确认处理", "揽收确认", "取件确认"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["确认取件", "取件完成", "揽收确认"],
            "trigger_keywords": ["确认取件", "取件完成", "揽收确认"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始取件确认"}},
                {
                    "id": "n_order_list",
                    "name": "查询待确认取件",
                    "type": "api_call",
                    "description": "查询待确认取件的订单",
                    "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/logistics/admin/orders", "method": "GET", "parameters": {"status": "pending_pickup_confirm"}},
                    "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}],
                    "ai_instructions": {"user_message": "查询待确认取件订单", "action": "查询待确认取件"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看订单详情",
                    "type": "api_call",
                    "description": "查看订单详细信息",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "pickup_id", "type": "string", "description": "取件单号"}],
                    "ai_instructions": {"user_message": "请选择要确认的订单", "action": "查看订单详情"}
                },
                {
                    "id": "n_pickup_confirm",
                    "name": "确认取件",
                    "type": "api_call",
                    "description": "确认取件并录入实际重量",
                    "config": {"api_id": "api_admin_pickup_confirm", "api_endpoint": "/api/logistics/admin/pickup/{pickup_id}/confirm", "method": "POST", "parameters": {"pickup_id": "${pickup_id}", "actual_weight": "${actual_weight}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "price_diff", "type": "float", "description": "运费差额"}],
                    "ai_instructions": {"user_message": "请输入实际重量确认取件", "action": "确认取件"}
                },
                {
                    "id": "n_transit_update",
                    "name": "更新运输状态",
                    "type": "api_call",
                    "description": "更新为运输中状态",
                    "config": {"api_id": "api_admin_transit_update", "api_endpoint": "/api/logistics/admin/transit", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "status": "in_transit", "location": "${current_location}", "remark": "已揽收，运输中"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "更新运输状态", "action": "更新运输状态"}
                },
                {
                    "id": "n_notify",
                    "name": "取件确认通知",
                    "type": "notification",
                    "description": "发送取件确认通知",
                    "config": {"message_template": "取件确认成功！订单${tracking_no}已揽收，实际重量${actual_weight}kg，运费差额${price_diff}元。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "取件确认成功", "action": "发送取件确认通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "取件确认完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_order_list"},
                {"source": "n_order_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_pickup_confirm"},
                {"source": "n_pickup_confirm", "target": "n_transit_update"},
                {"source": "n_transit_update", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：派送流程（6步：查询到站快递 → 查看详情 → 查询派送员 → 分配派送 → 完成派送 → 通知） ==========
        {
            "id": "workflow_admin_delivery",
            "name": "管理员派送流程",
            "description": "快递到站后分配派送员进行派送",
            "instruction_variants": ["派送流程", "管理员派送", "分配送件流程", "安排派送", "派送分配流程", "派送处理", "安排送货流程", "派送操作"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["派送", "分配派送", "安排送货"],
            "trigger_keywords": ["派送", "分配派送", "安排送货"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始派送"}},
                {
                    "id": "n_order_list",
                    "name": "查询到站快递",
                    "type": "api_call",
                    "description": "查询已到站待派送的快递",
                    "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/logistics/admin/orders", "method": "GET", "parameters": {"status": "arrived"}},
                    "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}],
                    "ai_instructions": {"user_message": "查询到站快递", "action": "查询到站快递"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看快递详情",
                    "type": "api_call",
                    "description": "查看快递详细信息",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "receiver", "type": "object", "description": "收件人信息"}],
                    "ai_instructions": {"user_message": "请选择要派送的快递", "action": "查看快递详情"}
                },
                {
                    "id": "n_courier_list",
                    "name": "查询派送员",
                    "type": "api_call",
                    "description": "查询可用的派送员",
                    "config": {"api_id": "api_admin_courier_list", "api_endpoint": "/api/logistics/admin/couriers", "method": "GET", "parameters": {"status": "available", "area": "${receiver_area}"}},
                    "outputs": [{"name": "couriers", "type": "array", "description": "快递员列表"}],
                    "ai_instructions": {"user_message": "查询可用派送员", "action": "查询派送员"}
                },
                {
                    "id": "n_assign",
                    "name": "分配派送",
                    "type": "api_call",
                    "description": "将快递分配给派送员",
                    "config": {"api_id": "api_admin_delivery_assign", "api_endpoint": "/api/logistics/admin/delivery/assign", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "courier_id": "${courier_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "estimated_time", "type": "string", "description": "预计送达时间"}],
                    "ai_instructions": {"user_message": "请选择派送员", "action": "分配派送"}
                },
                {
                    "id": "n_notify",
                    "name": "派送通知",
                    "type": "notification",
                    "description": "发送派送分配通知",
                    "config": {"message_template": "派送分配成功！订单${tracking_no}已分配派送，预计${estimated_time}送达。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "派送分配成功", "action": "发送派送通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "派送分配完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_order_list"},
                {"source": "n_order_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_courier_list"},
                {"source": "n_courier_list", "target": "n_assign"},
                {"source": "n_assign", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：签收确认流程（5步：查询派送中快递 → 查看详情 → 完成派送 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_sign_confirm",
            "name": "管理员签收确认流程",
            "description": "确认快递已签收并完成派送",
            "instruction_variants": ["签收确认流程", "管理员签收确认", "完成派送流程", "确认送达流程", "签收完成确认", "签收处理流程", "确认签收", "派送完成确认"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["签收确认", "完成派送", "确认送达"],
            "trigger_keywords": ["签收确认", "完成派送", "确认送达"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始签收确认"}},
                {
                    "id": "n_order_list",
                    "name": "查询派送中快递",
                    "type": "api_call",
                    "description": "查询正在派送的快递",
                    "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/logistics/admin/orders", "method": "GET", "parameters": {"status": "delivering"}},
                    "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}],
                    "ai_instructions": {"user_message": "查询派送中快递", "action": "查询派送中快递"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看快递详情",
                    "type": "api_call",
                    "description": "查看快递详细信息",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}],
                    "ai_instructions": {"user_message": "请选择要确认签收的快递", "action": "查看快递详情"}
                },
                {
                    "id": "n_complete",
                    "name": "完成派送",
                    "type": "api_call",
                    "description": "确认派送完成",
                    "config": {"api_id": "api_admin_delivery_complete", "api_endpoint": "/api/logistics/admin/delivery/{tracking_no}/complete", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "sign_type": "${sign_type}", "sign_photo": "${sign_photo}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "sign_time", "type": "datetime", "description": "签收时间"}],
                    "ai_instructions": {"user_message": "请选择签收方式并上传签收照片", "action": "完成派送"}
                },
                {
                    "id": "n_notify",
                    "name": "签收完成通知",
                    "type": "notification",
                    "description": "发送签收完成通知",
                    "config": {"message_template": "签收确认成功！订单${tracking_no}已于${sign_time}签收完成。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "签收确认成功", "action": "发送签收完成通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "签收确认完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_order_list"},
                {"source": "n_order_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_complete"},
                {"source": "n_complete", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：投诉处理流程（6步：查询投诉列表 → 查看投诉详情 → 查看订单详情 → 处理投诉 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_complaint_handle",
            "name": "管理员投诉处理流程",
            "description": "处理用户投诉并给出处理结果",
            "instruction_variants": ["投诉处理流程", "管理员处理投诉", "处理投诉流程", "解决投诉流程", "投诉处理操作", "处理用户投诉", "投诉处理流程走一下", "投诉处理"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["处理投诉", "投诉处理", "解决投诉"],
            "trigger_keywords": ["处理投诉", "投诉处理", "解决投诉"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理投诉"}},
                {
                    "id": "n_complaint_list",
                    "name": "查询投诉列表",
                    "type": "api_call",
                    "description": "查询待处理的投诉",
                    "config": {"api_id": "api_admin_complaint_list", "api_endpoint": "/api/logistics/admin/complaints", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "complaints", "type": "array", "description": "投诉列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数量"}],
                    "ai_instructions": {"user_message": "查询待处理投诉", "action": "查询投诉列表"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看关联订单",
                    "type": "api_call",
                    "description": "查看投诉关联的订单详情",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "complaint_id", "type": "string", "description": "投诉单号"}],
                    "ai_instructions": {"user_message": "请选择要处理的投诉", "action": "查看关联订单"}
                },
                {
                    "id": "n_handle",
                    "name": "处理投诉",
                    "type": "api_call",
                    "description": "处理投诉并给出结果",
                    "config": {"api_id": "api_admin_complaint_handle", "api_endpoint": "/api/logistics/admin/complaints/{complaint_id}/handle", "method": "POST", "parameters": {"complaint_id": "${complaint_id}", "action": "${handle_action}", "result": "${handle_result}", "compensation": "${compensation}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择处理方式并填写处理结果", "action": "处理投诉"}
                },
                {
                    "id": "n_notify",
                    "name": "处理结果通知",
                    "type": "notification",
                    "description": "发送投诉处理结果通知",
                    "config": {"message_template": "投诉处理完成！投诉单号${complaint_id}，处理结果：${handle_result}，赔偿金额：${compensation}元。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "投诉处理完成", "action": "发送处理结果通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "投诉处理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_complaint_list"},
                {"source": "n_complaint_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_handle"},
                {"source": "n_handle", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：运输状态更新流程（4步：查询运输中快递 → 查看详情 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_transit_update",
            "name": "管理员运输状态更新流程",
            "description": "更新快递运输状态和位置",
            "instruction_variants": ["运输状态更新流程", "更新物流状态流程", "管理员更新状态", "更新运输状态", "物流位置更新", "运输状态变更流程", "更新物流位置", "状态更新流程"],
            "business_scenario": "logistics",
            "status": "active",
            "user_intents": ["更新状态", "运输更新", "位置更新"],
            "trigger_keywords": ["更新状态", "运输更新", "位置更新"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始更新状态"}},
                {
                    "id": "n_order_list",
                    "name": "查询运输中快递",
                    "type": "api_call",
                    "description": "查询运输中的快递",
                    "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/logistics/admin/orders", "method": "GET", "parameters": {"status": "in_transit"}},
                    "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}, {"name": "in_transit", "type": "integer", "description": "运输中数"}],
                    "ai_instructions": {"user_message": "查询运输中快递", "action": "查询运输中快递"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看快递详情",
                    "type": "api_call",
                    "description": "查看快递详细信息",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/logistics/admin/orders/{tracking_no}", "method": "GET", "parameters": {"tracking_no": "${tracking_no}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}],
                    "ai_instructions": {"user_message": "请选择要更新的快递", "action": "查看快递详情"}
                },
                {
                    "id": "n_update",
                    "name": "更新运输状态",
                    "type": "api_call",
                    "description": "更新快递运输状态",
                    "config": {"api_id": "api_admin_transit_update", "api_endpoint": "/api/logistics/admin/transit", "method": "POST", "parameters": {"tracking_no": "${tracking_no}", "status": "${new_status}", "location": "${current_location}", "remark": "${remark}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请输入新状态和当前位置", "action": "更新运输状态"}
                },
                {
                    "id": "n_notify",
                    "name": "状态更新通知",
                    "type": "notification",
                    "description": "发送状态更新通知",
                    "config": {"message_template": "状态更新成功！订单${tracking_no}当前位置：${current_location}，状态：${new_status}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "状态更新成功", "action": "发送状态更新通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "状态更新完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_order_list"},
                {"source": "n_order_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_update"},
                {"source": "n_update", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
