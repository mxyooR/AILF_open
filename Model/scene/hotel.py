# hotel.py - 酒店场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

HOTEL_SCENE = {
    "domain": "hotel",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_hotel_search", "path": "/api/hotels/search", "method": "GET", "desc": "搜索酒店",
         "instruction_variants": ["搜索酒店", "查找酒店", "我想订酒店", "附近有哪些酒店", "帮我找个酒店", "酒店怎么搜", "给我查一下酒店", "查酒店列表"],
         "request": [{"name": "city", "type": "string", "label": "城市", "required": True}, {"name": "check_in", "type": "date", "label": "入住日期", "required": True}, {"name": "check_out", "type": "date", "label": "离店日期", "required": True}, {"name": "star", "type": "integer", "label": "星级", "required": False}],
         "response": [{"name": "hotels", "type": "array", "desc": "酒店列表"}, {"name": "hotel_id", "type": "string", "desc": "酒店ID"}, {"name": "hotel_name", "type": "string", "desc": "酒店名称"}]},
        {"id": "api_hotel_detail", "path": "/api/hotels/{hotel_id}", "method": "GET", "desc": "查询酒店详情",
         "instruction_variants": ["查询酒店详情", "查看酒店信息", "酒店详情", "看看这家酒店", "这家酒店怎么样", "帮我看酒店介绍", "酒店设施有哪些", "酒店评分多少"],
         "request": [{"name": "hotel_id", "type": "string", "label": "酒店ID", "required": True}],
         "response": [{"name": "hotel", "type": "object", "desc": "酒店详情"}, {"name": "facilities", "type": "array", "desc": "设施列表"}, {"name": "rating", "type": "float", "desc": "评分"}]},
        {"id": "api_room_list", "path": "/api/hotels/{hotel_id}/rooms", "method": "GET", "desc": "查询房型",
         "instruction_variants": ["查询房型", "查看房型", "有哪些房型", "房型列表", "这家酒店有什么房", "帮我看看房间", "房型价格", "可订房型有哪些"],
         "request": [{"name": "hotel_id", "type": "string", "label": "酒店ID", "required": True}, {"name": "check_in", "type": "date", "label": "入住日期", "required": False}, {"name": "check_out", "type": "date", "label": "离店日期", "required": False}],
         "response": [{"name": "rooms", "type": "array", "desc": "房型列表"}, {"name": "room_type", "type": "string", "desc": "房型"}, {"name": "price", "type": "float", "desc": "价格"}]},
        {"id": "api_room_detail", "path": "/api/hotels/{hotel_id}/rooms/{room_type}", "method": "GET", "desc": "查询房型详情",
         "instruction_variants": ["查询房型详情", "房型详情", "查看房间信息", "这个房型怎么样", "房型设施有哪些", "帮我看房型细节", "房型剩余多少", "这间房有啥设施"],
         "request": [{"name": "hotel_id", "type": "string", "label": "酒店ID", "required": True}, {"name": "room_type", "type": "string", "label": "房型", "required": True}],
         "response": [{"name": "room", "type": "object", "desc": "房型详情"}, {"name": "available_count", "type": "integer", "desc": "可用数量"}, {"name": "amenities", "type": "array", "desc": "房间设施"}]},
        {"id": "api_guest_verify", "workflow_only": True, "path": "/api/hotels/guests/verify", "method": "POST", "desc": "入住人身份验证",
         "instruction_variants": ["入住人身份验证", "验证入住人", "身份核验", "确认入住人信息", "帮我验证身份", "入住人怎么验证", "核验一下住客", "住客身份确认"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "phone", "type": "string", "label": "手机号", "required": True}],
         "response": [{"name": "guest_id", "type": "string", "desc": "入住人ID"}, {"name": "guest_name", "type": "string", "desc": "入住人姓名"}, {"name": "verified", "type": "boolean", "desc": "是否验证通过"}]},
        {"id": "api_booking_preview", "workflow_only": True, "path": "/api/hotels/bookings/preview", "method": "POST", "desc": "预订预览",
         "instruction_variants": ["预订预览", "看看价格", "先算下房费", "预订前估价", "帮我算一下总价", "价格预览", "住几晚多少钱", "订房费用是多少"],
         "request": [{"name": "hotel_id", "type": "string", "label": "酒店ID", "required": True}, {"name": "room_type", "type": "string", "label": "房型", "required": True}, {"name": "check_in", "type": "date", "label": "入住日期", "required": True}, {"name": "check_out", "type": "date", "label": "离店日期", "required": True}, {"name": "room_count", "type": "integer", "label": "房间数", "required": True}],
         "response": [{"name": "room_price", "type": "float", "desc": "房费"}, {"name": "service_fee", "type": "float", "desc": "服务费"}, {"name": "total_price", "type": "float", "desc": "总价"}, {"name": "nights", "type": "integer", "desc": "入住晚数"}]},
        {"id": "api_booking_create", "workflow_only": True, "path": "/api/hotels/bookings", "method": "POST", "desc": "预订酒店",
         "instruction_variants": ["预订酒店", "下单订房", "我要订酒店", "帮我订房", "创建预订", "预订一下", "订这家酒店", "订房下单"],
         "request": [{"name": "hotel_id", "type": "string", "label": "酒店ID", "required": True}, {"name": "room_type", "type": "string", "label": "房型", "required": True}, {"name": "check_in", "type": "date", "label": "入住日期", "required": True}, {"name": "check_out", "type": "date", "label": "离店日期", "required": True}, {"name": "room_count", "type": "integer", "label": "房间数", "required": True}, {"name": "guest_id", "type": "string", "label": "入住人ID", "required": True}, {"name": "special_request", "type": "string", "label": "特殊要求", "required": False}],
         "response": [{"name": "booking_id", "type": "string", "desc": "订单号"}, {"name": "total_price", "type": "float", "desc": "总价"}]},
        {"id": "api_booking_pay", "workflow_only": True, "path": "/api/hotels/bookings/{booking_id}/pay", "method": "POST", "desc": "预订支付",
         "instruction_variants": ["预订支付", "支付订单", "付房费", "我要付款", "帮我付款", "订房怎么付钱", "订单付款", "支付预订费用"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "payment_id", "type": "string", "desc": "支付流水号"}]},
        {"id": "api_booking_query", "path": "/api/hotels/bookings/{booking_id}", "method": "GET", "desc": "查询订单",
         "instruction_variants": ["查询订单", "查看预订", "我的订单", "订单详情", "帮我查订单", "预订记录怎么看", "查询预订信息", "订单状态"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "booking", "type": "object", "desc": "订单详情"}, {"name": "status", "type": "string", "desc": "订单状态"}, {"name": "hotel_name", "type": "string", "desc": "酒店名称"}]},
        {"id": "api_booking_list", "path": "/api/hotels/bookings", "method": "GET", "desc": "查询订单列表",
         "instruction_variants": ["查询订单列表", "我的订单列表", "预订记录", "全部订单", "帮我看看订单", "订单列表", "有哪些预订", "查看所有订单"],
         "request": [{"name": "status", "type": "string", "label": "订单状态", "required": False}],
         "response": [{"name": "bookings", "type": "array", "desc": "订单列表"}]},
        {"id": "api_booking_cancel_check", "workflow_only": True, "path": "/api/hotels/bookings/{booking_id}/cancel/check", "method": "GET", "desc": "取消预检查",
         "instruction_variants": ["取消预检查", "能不能取消订单", "取消规则看看", "取消会退多少钱", "先看看能不能退", "取消前检查", "帮我查取消条件", "取消政策"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "can_cancel", "type": "boolean", "desc": "是否可取消"}, {"name": "refund_amount", "type": "float", "desc": "可退金额"}, {"name": "cancel_policy", "type": "string", "desc": "取消政策"}]},
        {"id": "api_booking_cancel", "workflow_only": True, "path": "/api/hotels/bookings/{booking_id}/cancel", "method": "POST", "desc": "取消订单",
         "instruction_variants": ["取消订单", "退订", "我要取消预订", "帮我退房", "取消这笔订单", "订单怎么取消", "退订酒店", "取消预订"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}, {"name": "reason", "type": "string", "label": "取消原因", "required": False}],
         "response": [{"name": "refund_amount", "type": "float", "desc": "退款金额"}, {"name": "refund_status", "type": "string", "desc": "退款状态"}]},
        {"id": "api_checkin", "workflow_only": True, "path": "/api/hotels/checkin", "method": "POST", "desc": "办理入住",
         "instruction_variants": ["办理入住", "我要入住", "入住办理", "帮我办入住", "到店入住", "入住手续", "办理check in", "入住登记"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}],
         "response": [{"name": "room_number", "type": "string", "desc": "房间号"}, {"name": "wifi_password", "type": "string", "desc": "WiFi密码"}]},
        {"id": "api_checkout", "workflow_only": True, "path": "/api/hotels/checkout", "method": "POST", "desc": "办理退房",
         "instruction_variants": ["办理退房", "我要退房", "退房手续", "帮我办理退房", "离店退房", "退房结账", "check out", "退房"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "total_amount", "type": "float", "desc": "总费用"}, {"name": "extra_charges", "type": "float", "desc": "额外消费"}]},
        {"id": "api_service_request", "workflow_only": True, "path": "/api/hotels/services", "method": "POST", "desc": "客房服务请求",
         "instruction_variants": ["客房服务请求", "叫客房服务", "我要送东西", "帮我叫服务", "客房服务", "房间需要服务", "申请客房服务", "给房间叫人"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}, {"name": "service_type", "type": "string", "label": "服务类型", "required": True}, {"name": "description", "type": "string", "label": "描述", "required": False}],
         "response": [{"name": "request_id", "type": "string", "desc": "请求单号"}, {"name": "estimated_time", "type": "string", "desc": "预计时间"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_booking_list", "workflow_only": True, "path": "/api/hotels/admin/bookings", "method": "GET", "desc": "查询预订列表（管理员）",
         "instruction_variants": ["查询预订列表", "查看预订列表", "今天有哪些预订", "预订管理", "帮我查预订", "预订清单", "待处理预订", "预订情况"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "bookings", "type": "array", "desc": "预订列表"}, {"name": "today_checkin", "type": "integer", "desc": "今日入住数"}, {"name": "today_checkout", "type": "integer", "desc": "今日退房数"}]},
        {"id": "api_admin_booking_detail", "workflow_only": True, "path": "/api/hotels/admin/bookings/{booking_id}", "method": "GET", "desc": "查询预订详情（管理员）",
         "instruction_variants": ["查询预订详情", "查看订单详情", "预订详情", "订单信息", "帮我看预订", "查这笔预订", "订单详情查看", "预订内容"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "booking", "type": "object", "desc": "预订详情"}, {"name": "guest", "type": "object", "desc": "入住人信息"}, {"name": "payment", "type": "object", "desc": "支付信息"}]},
        {"id": "api_admin_room_list", "workflow_only": True, "path": "/api/hotels/admin/rooms", "method": "GET", "desc": "查询房间列表（管理员）",
         "instruction_variants": ["查询房间列表", "房间列表", "查看房态", "现在有哪些房", "空房有哪些", "帮我查房间", "房间情况", "房态查询"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "floor", "type": "integer", "label": "楼层", "required": False}],
         "response": [{"name": "rooms", "type": "array", "desc": "房间列表"}, {"name": "available_count", "type": "integer", "desc": "可用房间数"}, {"name": "occupied_count", "type": "integer", "desc": "已入住数"}]},
        {"id": "api_admin_room_assign", "workflow_only": True, "path": "/api/hotels/admin/rooms/assign", "method": "POST", "desc": "分配房间",
         "instruction_variants": ["分配房间", "给客人排房", "安排房号", "派房", "帮我分配房间", "指定房间", "分配房号", "安排入住房间"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}, {"name": "room_number", "type": "string", "label": "房间号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "room_number", "type": "string", "desc": "房间号"}]},
        {"id": "api_admin_checkin_process", "workflow_only": True, "path": "/api/hotels/admin/checkin", "method": "POST", "desc": "办理入住（管理员）",
         "instruction_variants": ["办理入住(管理员)", "前台办理入住", "入住登记", "帮客人办入住", "前台入住", "开房办理", "办理入住手续", "办理入住房卡"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}, {"name": "room_number", "type": "string", "label": "房间号", "required": True}, {"name": "deposit", "type": "float", "label": "押金", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "key_card", "type": "string", "desc": "房卡号"}]},
        {"id": "api_admin_checkout_process", "workflow_only": True, "path": "/api/hotels/admin/checkout", "method": "POST", "desc": "办理退房（管理员）",
         "instruction_variants": ["办理退房(管理员)", "前台退房", "结账退房", "帮客人退房", "办理退房手续", "退房结算", "退房办理", "客人退房"],
         "request": [{"name": "booking_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "total_amount", "type": "float", "desc": "总费用"}, {"name": "extra_charges", "type": "float", "desc": "额外消费"}, {"name": "refund_deposit", "type": "float", "desc": "退还押金"}]},
        {"id": "api_admin_room_clean", "workflow_only": True, "path": "/api/hotels/admin/rooms/{room_number}/clean", "method": "POST", "desc": "房间清洁",
         "instruction_variants": ["房间清洁", "安排打扫", "派保洁", "清洁房间", "帮我安排清洁", "房间需要打扫", "安排保洁", "打扫房间"],
         "request": [{"name": "room_number", "type": "string", "label": "房间号", "required": True}, {"name": "clean_type", "type": "string", "label": "清洁类型", "required": True}],
         "response": [{"name": "task_id", "type": "string", "desc": "任务ID"}, {"name": "assigned_staff", "type": "string", "desc": "分配员工"}]},
        {"id": "api_admin_room_inspect", "workflow_only": True, "path": "/api/hotels/admin/rooms/{room_number}/inspect", "method": "POST", "desc": "房间检查",
         "instruction_variants": ["房间检查", "检查房间", "房间验收", "帮我查房", "检查清洁情况", "验房", "房间巡检", "房态检查"],
         "request": [{"name": "room_number", "type": "string", "label": "房间号", "required": True}, {"name": "items", "type": "array", "label": "检查项目", "required": False}],
         "response": [{"name": "passed", "type": "boolean", "desc": "是否通过"}, {"name": "issues", "type": "array", "desc": "问题列表"}]},
        {"id": "api_admin_room_status_update", "workflow_only": True, "path": "/api/hotels/admin/rooms/{room_number}/status", "method": "PUT", "desc": "更新房间状态",
         "instruction_variants": ["更新房间状态", "修改房态", "房间状态更新", "把房态改一下", "设置房间状态", "房态变更", "更新房态", "改房间状态"],
         "request": [{"name": "room_number", "type": "string", "label": "房间号", "required": True}, {"name": "status", "type": "string", "label": "状态", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_service_list", "workflow_only": True, "path": "/api/hotels/admin/services", "method": "GET", "desc": "查询服务请求列表",
         "instruction_variants": ["查询服务请求列表", "客房服务列表", "服务请求", "待处理服务", "帮我查服务请求", "服务工单列表", "请求列表", "服务订单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "requests", "type": "array", "desc": "请求列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数量"}]},
        {"id": "api_admin_service_handle", "workflow_only": True, "path": "/api/hotels/admin/services/{request_id}/handle", "method": "POST", "desc": "处理服务请求",
         "instruction_variants": ["处理服务请求", "处理客房服务", "处理工单", "帮我处理服务", "服务请求处理", "完成服务请求", "处理服务订单", "服务处理"],
         "request": [{"name": "request_id", "type": "string", "label": "请求单号", "required": True}, {"name": "action", "type": "string", "label": "处理动作", "required": True}, {"name": "comment", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_price_list", "workflow_only": True, "path": "/api/hotels/admin/prices", "method": "GET", "desc": "查询房价列表",
         "instruction_variants": ["查询房价列表", "房价列表", "查看房价", "房价查询", "帮我查房价", "当前房价", "价格清单", "房价情况"],
         "request": [{"name": "room_type", "type": "string", "label": "房型", "required": False}],
         "response": [{"name": "prices", "type": "array", "desc": "房价列表"}]},
        {"id": "api_admin_price_update", "workflow_only": True, "path": "/api/hotels/admin/prices", "method": "PUT", "desc": "更新房价",
         "instruction_variants": ["更新房价", "调整房价", "修改价格", "改房价", "帮我调价", "设置新房价", "房价更新", "调价"],
         "request": [{"name": "room_type", "type": "string", "label": "房型", "required": True}, {"name": "date_from", "type": "date", "label": "开始日期", "required": True}, {"name": "date_to", "type": "date", "label": "结束日期", "required": True}, {"name": "price", "type": "float", "label": "价格", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        # ========== 管理员统计 API ==========
        {"id": "api_admin_occupancy", "path": "/api/hotels/admin/occupancy", "method": "GET", "desc": "查询入住率", "name": "入住率统计", "response_type": "chart", "chart_type": "line",
         "instruction_variants": ["查询入住率", "入住率统计", "今天入住率", "住客入住率", "帮我看入住率", "房间入住情况", "入住率曲线", "入住率数据"],
         "request": [], "response": [{"name": "dates", "type": "array", "desc": "日期"}, {"name": "rates", "type": "array", "desc": "入住率"}]},
        {"id": "api_admin_revenue_stats", "path": "/api/hotels/admin/revenue/stats", "method": "GET", "desc": "查询营收统计", "name": "营收统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询营收统计", "营收统计", "收入情况", "今日营收", "帮我看营收", "营收报表", "营业收入统计", "营收趋势"],
         "request": [], "response": [{"name": "today_revenue", "type": "float", "desc": "今日营收"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_room_type_stats", "path": "/api/hotels/admin/room/stats", "method": "GET", "desc": "查询房型统计", "name": "房型统计", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询房型统计", "房型统计", "房型预订情况", "各房型占比", "帮我看房型数据", "房型分析", "房型分布", "房型预订占比"],
         "request": [], "response": [{"name": "room_types", "type": "array", "desc": "房型"}, {"name": "bookings", "type": "array", "desc": "预订数"}]},
    ],

    "workflows": [
        # ========== 用户：完整预订流程（8步：搜索酒店 → 查看详情 → 选择房型 → 身份验证 → 预览价格 → 创建订单 → 支付 → 通知） ==========
        {
            "id": "workflow_full_booking",
            "name": "完整预订流程",
            "description": "完整的酒店预订流程，包括搜索酒店、查看详情、选择房型、身份验证、价格预览、创建订单和支付",
            "instruction_variants": ["完整订房流程", "订酒店流程", "我要订酒店", "帮我订房", "酒店预订流程", "订房全流程", "订酒店怎么弄", "订房从搜索到支付"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["订酒店", "预订酒店", "住酒店", "订房"],
            "trigger_keywords": ["订酒店", "预订酒店", "住酒店", "订房"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始预订"}},
                {
                    "id": "n_search",
                    "name": "搜索酒店",
                    "type": "api_call",
                    "description": "搜索符合条件的酒店",
                    "config": {"api_id": "api_hotel_search", "api_endpoint": "/api/hotels/search", "method": "GET", "parameters": {"city": "${city}", "check_in": "${check_in}", "check_out": "${check_out}", "star": "${star}"}},
                    "outputs": [{"name": "hotels", "type": "array", "description": "酒店列表"}, {"name": "hotel_id", "type": "string", "description": "酒店ID"}, {"name": "hotel_name", "type": "string", "description": "酒店名称"}],
                    "ai_instructions": {"user_message": "请输入城市、入住日期和离店日期", "action": "搜索酒店"}
                },
                {
                    "id": "n_hotel_detail",
                    "name": "查看酒店详情",
                    "type": "api_call",
                    "description": "查看酒店详细信息",
                    "config": {"api_id": "api_hotel_detail", "api_endpoint": "/api/hotels/{hotel_id}", "method": "GET", "parameters": {"hotel_id": "${hotel_id}"}},
                    "outputs": [{"name": "hotel", "type": "object", "description": "酒店详情"}, {"name": "facilities", "type": "array", "description": "设施列表"}, {"name": "rating", "type": "float", "description": "评分"}],
                    "ai_instructions": {"user_message": "请选择要查看的酒店", "action": "查看酒店详情"}
                },
                {
                    "id": "n_select_room",
                    "name": "选择房型",
                    "type": "api_call",
                    "description": "查看并选择房型",
                    "config": {"api_id": "api_room_list", "api_endpoint": "/api/hotels/{hotel_id}/rooms", "method": "GET", "parameters": {"hotel_id": "${hotel_id}", "check_in": "${check_in}", "check_out": "${check_out}"}},
                    "outputs": [{"name": "rooms", "type": "array", "description": "房型列表"}, {"name": "room_type", "type": "string", "description": "房型"}, {"name": "price", "type": "float", "description": "价格"}],
                    "ai_instructions": {"user_message": "请选择房型", "action": "选择房型"}
                },
                {
                    "id": "n_verify",
                    "name": "入住人验证",
                    "type": "api_call",
                    "description": "验证入住人身份",
                    "config": {"api_id": "api_guest_verify", "api_endpoint": "/api/hotels/guests/verify", "method": "POST", "parameters": {"name": "${guest_name}", "id_card": "${guest_id_card}", "phone": "${guest_phone}"}},
                    "outputs": [{"name": "guest_id", "type": "string", "description": "入住人ID"}, {"name": "guest_name", "type": "string", "description": "入住人姓名"}, {"name": "verified", "type": "boolean", "description": "是否验证通过"}],
                    "ai_instructions": {"user_message": "请填写入住人信息", "action": "入住人验证"}
                },
                {
                    "id": "n_preview",
                    "name": "预览价格",
                    "type": "api_call",
                    "description": "预览订单价格",
                    "config": {"api_id": "api_booking_preview", "api_endpoint": "/api/hotels/bookings/preview", "method": "POST", "parameters": {"hotel_id": "${hotel_id}", "room_type": "${room_type}", "check_in": "${check_in}", "check_out": "${check_out}", "room_count": "${room_count}"}},
                    "outputs": [{"name": "room_price", "type": "float", "description": "房费"}, {"name": "service_fee", "type": "float", "description": "服务费"}, {"name": "total_price", "type": "float", "description": "总价"}, {"name": "nights", "type": "integer", "description": "入住晚数"}],
                    "ai_instructions": {"user_message": "正在计算价格", "action": "预览价格"}
                },
                {
                    "id": "n_book",
                    "name": "创建订单",
                    "type": "api_call",
                    "description": "创建预订订单",
                    "config": {"api_id": "api_booking_create", "api_endpoint": "/api/hotels/bookings", "method": "POST", "parameters": {"hotel_id": "${hotel_id}", "room_type": "${room_type}", "check_in": "${check_in}", "check_out": "${check_out}", "room_count": "${room_count}", "guest_id": "${guest_id}", "special_request": "${special_request}"}},
                    "outputs": [{"name": "booking_id", "type": "string", "description": "订单号"}, {"name": "total_price", "type": "float", "description": "总价"}],
                    "ai_instructions": {"user_message": "请确认订单信息", "action": "创建订单"}
                },
                {
                    "id": "n_pay",
                    "name": "订单支付",
                    "type": "api_call",
                    "description": "支付订单",
                    "config": {"api_id": "api_booking_pay", "api_endpoint": "/api/hotels/bookings/{booking_id}/pay", "method": "POST", "parameters": {"booking_id": "${booking_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "payment_id", "type": "string", "description": "支付流水号"}],
                    "ai_instructions": {"user_message": "请选择支付方式完成支付", "action": "订单支付"}
                },
                {
                    "id": "n_notify",
                    "name": "预订通知",
                    "type": "notification",
                    "description": "发送预订成功通知",
                    "config": {"message_template": "预订成功！订单号：${booking_id}，酒店：${hotel_name}，房型：${room_type}，入住${nights}晚，总价：${total_price}元，请按时入住。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "预订成功", "action": "发送预订通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "预订完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_search"},
                {"source": "n_search", "target": "n_hotel_detail"},
                {"source": "n_hotel_detail", "target": "n_select_room"},
                {"source": "n_select_room", "target": "n_verify"},
                {"source": "n_verify", "target": "n_preview"},
                {"source": "n_preview", "target": "n_book"},
                {"source": "n_book", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：取消预订流程（5步：查询订单 → 取消检查 → 确认取消 → 退款 → 通知） ==========
        {
            "id": "workflow_cancel_booking",
            "name": "取消预订流程",
            "description": "取消酒店预订流程，包括订单查询、取消政策检查和退款",
            "instruction_variants": ["取消预订流程", "退订流程", "我要退订", "帮我取消订单", "退订酒店流程", "取消订房", "如何退订", "退房取消流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["取消订单", "退订", "取消预订"],
            "trigger_keywords": ["取消订单", "退订", "取消预订"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始取消预订"}},
                {
                    "id": "n_query",
                    "name": "查询订单",
                    "type": "api_call",
                    "description": "查询要取消的订单",
                    "config": {"api_id": "api_booking_query", "api_endpoint": "/api/hotels/bookings/{booking_id}", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "booking", "type": "object", "description": "订单详情"}, {"name": "status", "type": "string", "description": "订单状态"}, {"name": "hotel_name", "type": "string", "description": "酒店名称"}],
                    "ai_instructions": {"user_message": "请输入要取消的订单号", "action": "查询订单"}
                },
                {
                    "id": "n_check",
                    "name": "取消检查",
                    "type": "api_call",
                    "description": "检查取消政策和可退金额",
                    "config": {"api_id": "api_booking_cancel_check", "api_endpoint": "/api/hotels/bookings/{booking_id}/cancel/check", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "can_cancel", "type": "boolean", "description": "是否可取消"}, {"name": "refund_amount", "type": "float", "description": "可退金额"}, {"name": "cancel_policy", "type": "string", "description": "取消政策"}],
                    "ai_instructions": {"user_message": "正在检查取消政策", "action": "取消检查"}
                },
                {
                    "id": "n_cancel",
                    "name": "确认取消",
                    "type": "api_call",
                    "description": "确认取消订单",
                    "config": {"api_id": "api_booking_cancel", "api_endpoint": "/api/hotels/bookings/{booking_id}/cancel", "method": "POST", "parameters": {"booking_id": "${booking_id}", "reason": "${reason}"}},
                    "outputs": [{"name": "refund_amount", "type": "float", "description": "退款金额"}, {"name": "refund_status", "type": "string", "description": "退款状态"}],
                    "ai_instructions": {"user_message": "请确认取消并填写原因", "action": "确认取消"}
                },
                {
                    "id": "n_notify",
                    "name": "取消通知",
                    "type": "notification",
                    "description": "发送取消成功通知",
                    "config": {"message_template": "预订已取消！订单号：${booking_id}，退款金额：${refund_amount}元，预计3-5个工作日到账。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "取消成功", "action": "发送取消通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "取消预订完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "n_check"},
                {"source": "n_check", "target": "n_cancel"},
                {"source": "n_cancel", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：入住流程（4步：查询订单 → 身份验证 → 办理入住 → 通知） ==========
        {
            "id": "workflow_checkin",
            "name": "入住流程",
            "description": "办理酒店入住流程",
            "instruction_variants": ["入住流程", "办理入住流程", "我要办理入住", "帮我办入住", "酒店入住流程", "check in流程", "入住手续流程", "到店入住流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["入住", "check in", "办理入住"],
            "trigger_keywords": ["入住", "check in", "办理入住"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始入住"}},
                {
                    "id": "n_query",
                    "name": "查询订单",
                    "type": "api_call",
                    "description": "查询预订订单",
                    "config": {"api_id": "api_booking_query", "api_endpoint": "/api/hotels/bookings/{booking_id}", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "booking", "type": "object", "description": "订单详情"}, {"name": "status", "type": "string", "description": "订单状态"}, {"name": "hotel_name", "type": "string", "description": "酒店名称"}],
                    "ai_instructions": {"user_message": "请输入预订订单号", "action": "查询订单"}
                },
                {
                    "id": "n_checkin",
                    "name": "办理入住",
                    "type": "api_call",
                    "description": "办理入住手续",
                    "config": {"api_id": "api_checkin", "api_endpoint": "/api/hotels/checkin", "method": "POST", "parameters": {"booking_id": "${booking_id}", "id_card": "${id_card}"}},
                    "outputs": [{"name": "room_number", "type": "string", "description": "房间号"}, {"name": "wifi_password", "type": "string", "description": "WiFi密码"}],
                    "ai_instructions": {"user_message": "请提供身份证办理入住", "action": "办理入住"}
                },
                {
                    "id": "n_notify",
                    "name": "入住通知",
                    "type": "notification",
                    "description": "发送入住成功通知",
                    "config": {"message_template": "入住成功！房间号：${room_number}，WiFi密码：${wifi_password}，祝您入住愉快！"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "入住成功", "action": "发送入住通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "入住完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "n_checkin"},
                {"source": "n_checkin", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：退房流程（4步：查询订单 → 办理退房 → 结算 → 通知） ==========
        {
            "id": "workflow_checkout",
            "name": "退房流程",
            "description": "办理酒店退房流程",
            "instruction_variants": ["退房流程", "办理退房流程", "我要退房", "帮我退房", "酒店退房流程", "check out流程", "退房结账流程", "离店退房流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["退房", "check out", "办理退房"],
            "trigger_keywords": ["退房", "check out", "办理退房"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始退房"}},
                {
                    "id": "n_query",
                    "name": "查询订单",
                    "type": "api_call",
                    "description": "查询入住订单",
                    "config": {"api_id": "api_booking_query", "api_endpoint": "/api/hotels/bookings/{booking_id}", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "booking", "type": "object", "description": "订单详情"}, {"name": "status", "type": "string", "description": "订单状态"}],
                    "ai_instructions": {"user_message": "请输入订单号", "action": "查询订单"}
                },
                {
                    "id": "n_checkout",
                    "name": "办理退房",
                    "type": "api_call",
                    "description": "办理退房手续",
                    "config": {"api_id": "api_checkout", "api_endpoint": "/api/hotels/checkout", "method": "POST", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "total_amount", "type": "float", "description": "总费用"}, {"name": "extra_charges", "type": "float", "description": "额外消费"}],
                    "ai_instructions": {"user_message": "正在办理退房", "action": "办理退房"}
                },
                {
                    "id": "n_notify",
                    "name": "退房通知",
                    "type": "notification",
                    "description": "发送退房成功通知",
                    "config": {"message_template": "退房成功！总费用：${total_amount}元，额外消费：${extra_charges}元，感谢您的入住！"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "退房成功", "action": "发送退房通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退房完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "n_checkout"},
                {"source": "n_checkout", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：入住办理流程（6步：查询预订 → 查看详情 → 分配房间 → 办理入住 → 发放房卡 → 通知） ==========
        {
            "id": "workflow_admin_checkin",
            "name": "入住办理流程",
            "description": "管理员办理客人入住流程，包括预订查询、房间分配和入住办理",
            "instruction_variants": ["前台入住流程", "管理员办理入住", "前台帮客人入住", "办理入住(前台)", "入住接待流程", "前台开房流程", "入住房卡办理", "前台入住流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["办理入住", "客人入住", "前台入住"],
            "trigger_keywords": ["办理入住", "客人入住"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始办理入住"}},
                {
                    "id": "n_booking_list",
                    "name": "查询今日预订",
                    "type": "api_call",
                    "description": "查询今日待入住的预订",
                    "config": {"api_id": "api_admin_booking_list", "api_endpoint": "/api/hotels/admin/bookings", "method": "GET", "parameters": {"date": "${date}", "status": "confirmed"}},
                    "outputs": [{"name": "bookings", "type": "array", "description": "预订列表"}, {"name": "today_checkin", "type": "integer", "description": "今日入住数"}],
                    "ai_instructions": {"user_message": "正在查询今日待入住预订", "action": "查询今日预订"}
                },
                {
                    "id": "n_booking_detail",
                    "name": "查看预订详情",
                    "type": "api_call",
                    "description": "查看预订详细信息",
                    "config": {"api_id": "api_admin_booking_detail", "api_endpoint": "/api/hotels/admin/bookings/{booking_id}", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "booking", "type": "object", "description": "预订详情"}, {"name": "guest", "type": "object", "description": "入住人信息"}],
                    "ai_instructions": {"user_message": "请选择要办理入住的预订", "action": "查看预订详情"}
                },
                {
                    "id": "n_room_list",
                    "name": "查询可用房间",
                    "type": "api_call",
                    "description": "查询可分配的房间",
                    "config": {"api_id": "api_admin_room_list", "api_endpoint": "/api/hotels/admin/rooms", "method": "GET", "parameters": {"status": "available"}},
                    "outputs": [{"name": "rooms", "type": "array", "description": "房间列表"}, {"name": "available_count", "type": "integer", "description": "可用房间数"}],
                    "ai_instructions": {"user_message": "正在查询可用房间", "action": "查询可用房间"}
                },
                {
                    "id": "n_assign",
                    "name": "分配房间",
                    "type": "api_call",
                    "description": "为客人分配房间",
                    "config": {"api_id": "api_admin_room_assign", "api_endpoint": "/api/hotels/admin/rooms/assign", "method": "POST", "parameters": {"booking_id": "${booking_id}", "room_number": "${room_number}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "room_number", "type": "string", "description": "房间号"}],
                    "ai_instructions": {"user_message": "请选择要分配的房间", "action": "分配房间"}
                },
                {
                    "id": "n_checkin",
                    "name": "办理入住",
                    "type": "api_call",
                    "description": "办理入住手续",
                    "config": {"api_id": "api_admin_checkin_process", "api_endpoint": "/api/hotels/admin/checkin", "method": "POST", "parameters": {"booking_id": "${booking_id}", "room_number": "${room_number}", "deposit": "${deposit}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "key_card", "type": "string", "description": "房卡号"}],
                    "ai_instructions": {"user_message": "请输入押金金额", "action": "办理入住"}
                },
                {
                    "id": "n_notify",
                    "name": "入住完成通知",
                    "type": "notification",
                    "description": "发送入住完成通知",
                    "config": {"message_template": "入住办理完成！房间号：${room_number}，房卡号：${key_card}，已通知客人。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "入住办理完成", "action": "发送入住通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "入住办理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_booking_list"},
                {"source": "n_booking_list", "target": "n_booking_detail"},
                {"source": "n_booking_detail", "target": "n_room_list"},
                {"source": "n_room_list", "target": "n_assign"},
                {"source": "n_assign", "target": "n_checkin"},
                {"source": "n_checkin", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：退房办理流程（5步：查询入住 → 查看详情 → 办理退房 → 结算 → 通知） ==========
        {
            "id": "workflow_admin_checkout",
            "name": "退房办理流程",
            "description": "管理员办理客人退房流程，包括入住查询、退房办理和费用结算",
            "instruction_variants": ["前台退房流程", "管理员办理退房", "前台结账退房", "办理退房(前台)", "退房结算流程", "前台退房办理", "客人退房处理", "退房接待流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["办理退房", "客人退房", "前台退房"],
            "trigger_keywords": ["办理退房", "客人退房"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始办理退房"}},
                {
                    "id": "n_booking_list",
                    "name": "查询今日退房",
                    "type": "api_call",
                    "description": "查询今日待退房的订单",
                    "config": {"api_id": "api_admin_booking_list", "api_endpoint": "/api/hotels/admin/bookings", "method": "GET", "parameters": {"date": "${date}", "status": "checked_in"}},
                    "outputs": [{"name": "bookings", "type": "array", "description": "预订列表"}, {"name": "today_checkout", "type": "integer", "description": "今日退房数"}],
                    "ai_instructions": {"user_message": "正在查询今日待退房订单", "action": "查询今日退房"}
                },
                {
                    "id": "n_booking_detail",
                    "name": "查看订单详情",
                    "type": "api_call",
                    "description": "查看订单详细信息",
                    "config": {"api_id": "api_admin_booking_detail", "api_endpoint": "/api/hotels/admin/bookings/{booking_id}", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "booking", "type": "object", "description": "订单详情"}, {"name": "guest", "type": "object", "description": "入住人信息"}],
                    "ai_instructions": {"user_message": "请选择要办理退房的订单", "action": "查看订单详情"}
                },
                {
                    "id": "n_checkout",
                    "name": "办理退房",
                    "type": "api_call",
                    "description": "办理退房手续并结算",
                    "config": {"api_id": "api_admin_checkout_process", "api_endpoint": "/api/hotels/admin/checkout", "method": "POST", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "total_amount", "type": "float", "description": "总费用"}, {"name": "extra_charges", "type": "float", "description": "额外消费"}, {"name": "refund_deposit", "type": "float", "description": "退还押金"}],
                    "ai_instructions": {"user_message": "正在办理退房", "action": "办理退房"}
                },
                {
                    "id": "n_notify",
                    "name": "退房完成通知",
                    "type": "notification",
                    "description": "发送退房完成通知",
                    "config": {"message_template": "退房办理完成！总费用：${total_amount}元，额外消费：${extra_charges}元，退还押金：${refund_deposit}元。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "退房办理完成", "action": "发送退房通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退房办理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_booking_list"},
                {"source": "n_booking_list", "target": "n_booking_detail"},
                {"source": "n_booking_detail", "target": "n_checkout"},
                {"source": "n_checkout", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：房间清洁检查流程（5步：查询待清洁 → 分配清洁 → 清洁完成 → 检查 → 更新状态） ==========
        {
            "id": "workflow_admin_room_clean",
            "name": "房间清洁检查流程",
            "description": "管理员房间清洁和检查流程",
            "instruction_variants": ["房间清洁流程", "打扫房间流程", "安排保洁流程", "房间清洁检查", "清洁验房流程", "房间打扫流程", "保洁流程", "房间清洁处理"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["房间清洁", "打扫房间", "清洁检查"],
            "trigger_keywords": ["房间清洁", "打扫房间"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始房间清洁"}},
                {
                    "id": "n_room_list",
                    "name": "查询待清洁房间",
                    "type": "api_call",
                    "description": "查询待清洁的房间列表",
                    "config": {"api_id": "api_admin_room_list", "api_endpoint": "/api/hotels/admin/rooms", "method": "GET", "parameters": {"status": "dirty"}},
                    "outputs": [{"name": "rooms", "type": "array", "description": "房间列表"}],
                    "ai_instructions": {"user_message": "正在查询待清洁房间", "action": "查询待清洁房间"}
                },
                {
                    "id": "n_clean",
                    "name": "分配清洁任务",
                    "type": "api_call",
                    "description": "分配房间清洁任务",
                    "config": {"api_id": "api_admin_room_clean", "api_endpoint": "/api/hotels/admin/rooms/{room_number}/clean", "method": "POST", "parameters": {"room_number": "${room_number}", "clean_type": "${clean_type}"}},
                    "outputs": [{"name": "task_id", "type": "string", "description": "任务ID"}, {"name": "assigned_staff", "type": "string", "description": "分配员工"}],
                    "ai_instructions": {"user_message": "请选择房间和清洁类型", "action": "分配清洁任务"}
                },
                {
                    "id": "n_inspect",
                    "name": "房间检查",
                    "type": "api_call",
                    "description": "检查清洁后的房间",
                    "config": {"api_id": "api_admin_room_inspect", "api_endpoint": "/api/hotels/admin/rooms/{room_number}/inspect", "method": "POST", "parameters": {"room_number": "${room_number}"}},
                    "outputs": [{"name": "passed", "type": "boolean", "description": "是否通过"}, {"name": "issues", "type": "array", "description": "问题列表"}],
                    "ai_instructions": {"user_message": "正在检查房间", "action": "房间检查"}
                },
                {
                    "id": "n_update_status",
                    "name": "更新房间状态",
                    "type": "api_call",
                    "description": "更新房间状态为可用",
                    "config": {"api_id": "api_admin_room_status_update", "api_endpoint": "/api/hotels/admin/rooms/{room_number}/status", "method": "PUT", "parameters": {"room_number": "${room_number}", "status": "available"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "正在更新房间状态", "action": "更新房间状态"}
                },
                {
                    "id": "n_notify",
                    "name": "清洁完成通知",
                    "type": "notification",
                    "description": "发送清洁完成通知",
                    "config": {"message_template": "房间清洁完成！房间号：${room_number}，检查通过，已更新为可用状态。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "清洁完成", "action": "发送清洁通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "房间清洁完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_room_list"},
                {"source": "n_room_list", "target": "n_clean"},
                {"source": "n_clean", "target": "n_inspect"},
                {"source": "n_inspect", "target": "n_update_status"},
                {"source": "n_update_status", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：客房服务处理流程（4步：查询请求 → 处理请求 → 完成 → 通知） ==========
        {
            "id": "workflow_admin_service_handle",
            "name": "客房服务处理流程",
            "description": "管理员处理客房服务请求",
            "instruction_variants": ["客房服务处理流程", "处理服务请求流程", "服务工单处理", "客房服务处理", "处理客房服务流程", "服务请求处理流程", "处理服务单", "客房服务处理流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["处理服务", "客房服务", "服务请求"],
            "trigger_keywords": ["处理服务", "客房服务"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理服务"}},
                {
                    "id": "n_service_list",
                    "name": "查询服务请求",
                    "type": "api_call",
                    "description": "查询待处理的服务请求",
                    "config": {"api_id": "api_admin_service_list", "api_endpoint": "/api/hotels/admin/services", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "requests", "type": "array", "description": "请求列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数量"}],
                    "ai_instructions": {"user_message": "正在查询待处理的服务请求", "action": "查询服务请求"}
                },
                {
                    "id": "n_handle",
                    "name": "处理请求",
                    "type": "api_call",
                    "description": "处理服务请求",
                    "config": {"api_id": "api_admin_service_handle", "api_endpoint": "/api/hotels/admin/services/{request_id}/handle", "method": "POST", "parameters": {"request_id": "${request_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择处理动作", "action": "处理请求"}
                },
                {
                    "id": "n_notify",
                    "name": "处理完成通知",
                    "type": "notification",
                    "description": "发送处理完成通知",
                    "config": {"message_template": "服务请求已处理！请求单号：${request_id}，已通知客人。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "处理完成", "action": "发送处理通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "服务处理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_service_list"},
                {"source": "n_service_list", "target": "n_handle"},
                {"source": "n_handle", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：房价调整流程（4步：查询房价 → 调整价格 → 确认 → 通知） ==========
        {
            "id": "workflow_admin_price_adjust",
            "name": "房价调整流程",
            "description": "管理员调整房间价格",
            "instruction_variants": ["房价调整流程", "调价流程", "修改房价流程", "更新房价流程", "房价管理流程", "调整价格", "房价变更流程", "调价申请流程"],
            "business_scenario": "hotel",
            "status": "active",
            "user_intents": ["调整房价", "修改价格", "房价管理"],
            "trigger_keywords": ["调整房价", "修改价格"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始调整房价"}},
                {
                    "id": "n_price_list",
                    "name": "查询当前房价",
                    "type": "api_call",
                    "description": "查询当前房价列表",
                    "config": {"api_id": "api_admin_price_list", "api_endpoint": "/api/hotels/admin/prices", "method": "GET", "parameters": {"room_type": "${room_type}"}},
                    "outputs": [{"name": "prices", "type": "array", "description": "房价列表"}],
                    "ai_instructions": {"user_message": "请选择房型查询当前房价", "action": "查询当前房价"}
                },
                {
                    "id": "n_update",
                    "name": "更新房价",
                    "type": "api_call",
                    "description": "更新房间价格",
                    "config": {"api_id": "api_admin_price_update", "api_endpoint": "/api/hotels/admin/prices", "method": "PUT", "parameters": {"room_type": "${room_type}", "date_from": "${date_from}", "date_to": "${date_to}", "price": "${price}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请输入新价格和生效日期范围", "action": "更新房价"}
                },
                {
                    "id": "n_notify",
                    "name": "调整完成通知",
                    "type": "notification",
                    "description": "发送房价调整完成通知",
                    "config": {"message_template": "房价调整完成！房型：${room_type}，新价格：${price}元，生效日期：${date_from}至${date_to}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "调整完成", "action": "发送调整通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "房价调整完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_price_list"},
                {"source": "n_price_list", "target": "n_update"},
                {"source": "n_update", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
