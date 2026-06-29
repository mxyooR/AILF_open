# catering.py - 餐饮场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

CATERING_SCENE = {
    "domain": "catering",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_restaurant_list", "path": "/api/catering/restaurants", "method": "GET", "desc": "查询餐厅列表",
         "instruction_variants": ["查询餐厅列表", "查餐厅", "找餐厅", "附近有什么餐厅", "喂，哪里有餐厅", "帮我找餐厅", "餐厅在哪", "查一下餐厅"],
         "request": [{"name": "location", "type": "string", "label": "位置", "required": False}, {"name": "cuisine", "type": "string", "label": "菜系", "required": False}],
         "response": [{"name": "restaurants", "type": "array", "desc": "餐厅列表"}]},
        {"id": "api_restaurant_detail", "path": "/api/catering/restaurants/{restaurant_id}", "method": "GET", "desc": "查询餐厅详情",
         "instruction_variants": ["查询餐厅详情", "餐厅详情", "这餐厅怎么样", "餐厅信息", "喂，这餐厅好吗", "帮我看看餐厅", "餐厅评价", "餐厅介绍"],
         "request": [{"name": "restaurant_id", "type": "string", "label": "餐厅ID", "required": True}],
         "response": [{"name": "restaurant", "type": "object", "desc": "餐厅详情"}, {"name": "rating", "type": "float", "desc": "评分"}, {"name": "delivery_time", "type": "string", "desc": "配送时间"}]},
        {"id": "api_menu_list", "path": "/api/catering/restaurants/{restaurant_id}/menu", "method": "GET", "desc": "查询菜单",
         "instruction_variants": ["查询菜单", "看菜单", "有什么菜", "菜单", "喂，有啥好吃的", "帮我看看菜单", "菜单怎么样", "查一下菜"],
         "request": [{"name": "restaurant_id", "type": "string", "label": "餐厅ID", "required": True}],
         "response": [{"name": "dishes", "type": "array", "desc": "菜品列表"}, {"name": "categories", "type": "array", "desc": "分类"}]},
        {"id": "api_coupon_list", "path": "/api/catering/coupons", "method": "GET", "desc": "查询优惠券",
         "instruction_variants": ["查询优惠券", "优惠券", "有什么优惠", "折扣", "喂，有优惠吗", "帮我看看优惠券", "优惠券怎么领", "查一下优惠"],
         "request": [{"name": "restaurant_id", "type": "string", "label": "餐厅ID", "required": False}],
         "response": [{"name": "coupons", "type": "array", "desc": "优惠券列表"}]},
        {"id": "api_coupon_claim", "workflow_only": True, "path": "/api/catering/coupons/{coupon_id}/claim", "method": "POST", "desc": "领取优惠券",
         "instruction_variants": ["领取优惠券", "领优惠券", "领券", "抢券", "喂，我要领券", "帮我领优惠券", "优惠券怎么领", "领一张券"],
         "request": [{"name": "coupon_id", "type": "string", "label": "优惠券ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "user_coupon_id", "type": "string", "desc": "用户优惠券ID"}]},
        {"id": "api_order_create", "workflow_only": True, "path": "/api/catering/orders", "method": "POST", "desc": "创建订单",
         "instruction_variants": ["创建订单", "下单", "提交订单", "我要点餐", "喂，我要下单", "帮我下单", "下单怎么弄", "点餐"],
         "request": [{"name": "restaurant_id", "type": "string", "label": "餐厅ID", "required": True}, {"name": "items", "type": "array", "label": "菜品列表", "required": True}, {"name": "delivery_address", "type": "string", "label": "配送地址", "required": True}, {"name": "contact_phone", "type": "string", "label": "联系电话", "required": True}, {"name": "coupon_id", "type": "string", "label": "优惠券ID", "required": False}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "order_id", "type": "string", "desc": "订单ID"}, {"name": "total_amount", "type": "float", "desc": "总金额"}, {"name": "discount", "type": "float", "desc": "优惠金额"}]},
        {"id": "api_order_pay", "workflow_only": True, "path": "/api/catering/orders/{order_id}/pay", "method": "POST", "desc": "订单支付",
         "instruction_variants": ["订单支付", "支付", "付款", "我要付款", "喂，怎么付钱", "帮我支付", "支付怎么弄", "付钱"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "payment_id", "type": "string", "desc": "支付流水号"}]},
        {"id": "api_order_status", "path": "/api/catering/orders/{order_id}", "method": "GET", "desc": "查询订单状态",
         "instruction_variants": ["查询订单状态", "订单状态", "我的订单", "订单到哪了", "喂，订单怎么样了", "帮我查查订单", "订单进度", "查一下订单"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}],
         "response": [{"name": "status", "type": "string", "desc": "订单状态"}, {"name": "rider_info", "type": "object", "desc": "骑手信息"}, {"name": "estimated_time", "type": "string", "desc": "预计送达"}]},
        {"id": "api_order_cancel", "workflow_only": True, "path": "/api/catering/orders/{order_id}/cancel", "method": "POST", "desc": "取消订单",
         "instruction_variants": ["取消订单", "取消", "不要了", "退单", "喂，我要取消订单", "帮我取消", "取消怎么办", "不想要了"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "reason", "type": "string", "label": "取消原因", "required": False}],
         "response": [{"name": "refund_amount", "type": "float", "desc": "退款金额"}, {"name": "refund_status", "type": "string", "desc": "退款状态"}]},
        {"id": "api_table_slots", "path": "/api/catering/restaurants/{restaurant_id}/slots", "method": "GET", "desc": "查询可预订时段",
         "instruction_variants": ["查询可预订时段", "查时段", "什么时候有位", "预订时间", "喂，什么时候能订", "帮我查查时段", "时段怎么选", "查一下时间"],
         "request": [{"name": "restaurant_id", "type": "string", "label": "餐厅ID", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}],
         "response": [{"name": "slots", "type": "array", "desc": "可选时段"}, {"name": "tables", "type": "array", "desc": "可选桌位"}]},
        {"id": "api_table_reserve", "workflow_only": True, "path": "/api/catering/reservations", "method": "POST", "desc": "预订餐位",
         "instruction_variants": ["预订餐位", "订座", "预约", "订位", "喂，我要订座", "帮我预订", "预订怎么弄", "订个位子"],
         "request": [{"name": "restaurant_id", "type": "string", "label": "餐厅ID", "required": True}, {"name": "date", "type": "date", "label": "预订日期", "required": True}, {"name": "time", "type": "time", "label": "用餐时间", "required": True}, {"name": "guests", "type": "integer", "label": "用餐人数", "required": True}, {"name": "contact_name", "type": "string", "label": "联系人", "required": True}, {"name": "contact_phone", "type": "string", "label": "联系电话", "required": True}],
         "response": [{"name": "reservation_id", "type": "string", "desc": "预订ID"}, {"name": "table_no", "type": "string", "desc": "桌号"}]},
        {"id": "api_reservation_cancel", "workflow_only": True, "path": "/api/catering/reservations/{reservation_id}/cancel", "method": "POST", "desc": "取消预订",
         "instruction_variants": ["取消预订", "取消订座", "不去了", "取消", "喂，我要取消预订", "帮我取消", "取消怎么办", "不订了"],
         "request": [{"name": "reservation_id", "type": "string", "label": "预订ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_review_submit", "workflow_only": True, "path": "/api/catering/reviews", "method": "POST", "desc": "提交评价",
         "instruction_variants": ["提交评价", "评价", "写评价", "打分", "喂，我要评价", "帮我评价", "评价怎么写", "给个评分"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "rating", "type": "integer", "label": "评分", "required": True}, {"name": "comment", "type": "string", "label": "评价内容", "required": False}, {"name": "images", "type": "string", "label": "图片", "required": False}],
         "response": [{"name": "review_id", "type": "string", "desc": "评价ID"}, {"name": "points_earned", "type": "integer", "desc": "获得积分"}]},
        {"id": "api_complaint_submit", "workflow_only": True, "path": "/api/catering/complaints", "method": "POST", "desc": "投诉建议",
         "instruction_variants": ["投诉建议", "投诉", "反馈", "建议", "喂，我要投诉", "帮我投诉", "投诉怎么办", "提个意见"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "type", "type": "string", "label": "投诉类型", "required": True}, {"name": "content", "type": "string", "label": "投诉内容", "required": True}],
         "response": [{"name": "complaint_id", "type": "string", "desc": "投诉单号"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_order_list", "workflow_only": True, "path": "/api/catering/admin/orders", "method": "GET", "desc": "查询订单列表（管理员）",
         "instruction_variants": ["查询订单列表", "订单列表", "所有订单", "订单管理", "喂，有哪些订单", "帮我看看订单", "订单怎么样", "查一下订单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "date", "type": "date", "label": "日期", "required": False}],
         "response": [{"name": "orders", "type": "array", "desc": "订单列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_order_detail", "workflow_only": True, "path": "/api/catering/admin/orders/{order_id}", "method": "GET", "desc": "查询订单详情（管理员）",
         "instruction_variants": ["查询订单详情", "订单详情", "订单信息", "查看订单", "喂，这订单什么情况", "帮我看看详情", "订单详细信息", "查一下订单"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}],
         "response": [{"name": "order", "type": "object", "desc": "订单详情"}, {"name": "items", "type": "array", "desc": "菜品列表"}, {"name": "customer", "type": "object", "desc": "客户信息"}]},
        {"id": "api_admin_order_confirm", "workflow_only": True, "path": "/api/catering/admin/orders/{order_id}/confirm", "method": "POST", "desc": "确认订单",
         "instruction_variants": ["确认订单", "接单", "确认接单", "订单确认", "喂，我接单了", "帮我确认订单", "确认怎么弄", "接这个单"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "estimated_time", "type": "string", "label": "预计完成时间", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_order_ready", "workflow_only": True, "path": "/api/catering/admin/orders/{order_id}/ready", "method": "POST", "desc": "订单出餐",
         "instruction_variants": ["订单出餐", "出餐", "餐做好了", "可以配送了", "喂，餐好了", "帮我标记出餐", "出餐怎么弄", "餐已完成"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "rider_assigned", "type": "boolean", "desc": "是否已分配骑手"}]},
        {"id": "api_admin_rider_list", "workflow_only": True, "path": "/api/catering/admin/riders", "method": "GET", "desc": "查询骑手列表",
         "instruction_variants": ["查询骑手列表", "骑手列表", "有哪些骑手", "骑手管理", "喂，骑手在哪", "帮我看看骑手", "骑手怎么样", "查一下骑手"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "riders", "type": "array", "desc": "骑手列表"}, {"name": "available_count", "type": "integer", "desc": "可用人数"}]},
        {"id": "api_admin_rider_assign", "workflow_only": True, "path": "/api/catering/admin/orders/{order_id}/assign", "method": "POST", "desc": "分配骑手",
         "instruction_variants": ["分配骑手", "派单", "指派骑手", "安排配送", "喂，派个骑手", "帮我分配骑手", "分配怎么弄", "安排配送员"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "rider_id", "type": "string", "label": "骑手ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "rider_name", "type": "string", "desc": "骑手姓名"}]},
        {"id": "api_admin_order_complete", "workflow_only": True, "path": "/api/catering/admin/orders/{order_id}/complete", "method": "POST", "desc": "完成订单",
         "instruction_variants": ["完成订单", "订单完成", "已送达", "配送完成", "喂，订单送到了", "帮我标记完成", "完成怎么弄", "订单已完成"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_refund_list", "workflow_only": True, "path": "/api/catering/admin/refunds", "method": "GET", "desc": "查询退款列表",
         "instruction_variants": ["查询退款列表", "退款列表", "退款申请", "退款管理", "喂，有哪些退款", "帮我看看退款", "退款怎么样", "查一下退款"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "refunds", "type": "array", "desc": "退款列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_refund_process", "workflow_only": True, "path": "/api/catering/admin/refunds/{order_id}/process", "method": "POST", "desc": "处理退款",
         "instruction_variants": ["处理退款", "退款审核", "审批退款", "退款处理", "喂，我要处理退款", "帮我审核退款", "退款怎么处理", "审批一下"],
         "request": [{"name": "order_id", "type": "string", "label": "订单ID", "required": True}, {"name": "action", "type": "string", "label": "处理动作", "required": True}, {"name": "refund_amount", "type": "float", "label": "退款金额", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_reservation_list", "workflow_only": True, "path": "/api/catering/admin/reservations", "method": "GET", "desc": "查询预订列表（管理员）",
         "instruction_variants": ["查询预订列表", "预订列表", "预订管理", "订座列表", "喂，有哪些预订", "帮我看看预订", "预订怎么样", "查一下预订"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "reservations", "type": "array", "desc": "预订列表"}, {"name": "today_count", "type": "integer", "desc": "今日预订数"}]},
        {"id": "api_admin_reservation_checkin", "workflow_only": True, "path": "/api/catering/admin/reservations/{reservation_id}/checkin", "method": "POST", "desc": "预订签到",
         "instruction_variants": ["预订签到", "签到", "客人到了", "确认到店", "喂，客人来了", "帮我签到", "签到怎么弄", "确认签到"],
         "request": [{"name": "reservation_id", "type": "string", "label": "预订ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "table_no", "type": "string", "desc": "桌号"}]},
        {"id": "api_admin_complaint_list", "workflow_only": True, "path": "/api/catering/admin/complaints", "method": "GET", "desc": "查询投诉列表（管理员）",
         "instruction_variants": ["查询投诉列表", "投诉列表", "投诉管理", "客诉列表", "喂，有哪些投诉", "帮我看看投诉", "投诉怎么样", "查一下投诉"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "complaints", "type": "array", "desc": "投诉列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_complaint_handle", "workflow_only": True, "path": "/api/catering/admin/complaints/{complaint_id}/handle", "method": "POST", "desc": "处理投诉",
         "instruction_variants": ["处理投诉", "投诉处理", "解决投诉", "投诉回复", "喂，我要处理投诉", "帮我解决投诉", "投诉怎么处理", "回复一下"],
         "request": [{"name": "complaint_id", "type": "string", "label": "投诉单号", "required": True}, {"name": "result", "type": "string", "label": "处理结果", "required": True}, {"name": "compensation", "type": "float", "label": "赔偿金额", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},

        # ========== 管理员统计 API ==========
        {"id": "api_admin_revenue_stats", "path": "/api/catering/admin/stats/revenue", "method": "GET", "desc": "查询营业额统计", "name": "营业额统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询营业额统计", "营业额", "收入统计", "营收数据", "喂，今天赚了多少", "帮我看看营业额", "营业额怎么样", "查一下收入"],
         "request": [],
         "response": [{"name": "today_revenue", "type": "float", "desc": "今日营业额"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_dish_sales", "path": "/api/catering/admin/stats/dish", "method": "GET", "desc": "查询菜品销量", "name": "菜品销量", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询菜品销量", "菜品销量", "销量统计", "哪个菜卖得好", "喂，什么菜最火", "帮我看看销量", "销量怎么样", "查一下菜品"],
         "request": [],
         "response": [{"name": "dishes", "type": "array", "desc": "菜品"}, {"name": "sales", "type": "array", "desc": "销量"}]},
        {"id": "api_admin_order_stats", "path": "/api/catering/admin/stats/order", "method": "GET", "desc": "查询订单统计", "name": "订单统计", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询订单统计", "订单统计", "订单数据", "订单分布", "喂，订单情况怎么样", "帮我看看订单统计", "订单分析", "查一下订单"],
         "request": [],
         "response": [{"name": "status_distribution", "type": "array", "desc": "状态分布"}]},
    ],

    "workflows": [
        # ========== 用户：完整外卖点餐流程（7步：查询餐厅 → 查看详情 → 查询菜单 → 领取优惠券 → 创建订单 → 支付 → 通知） ==========
        {
            "id": "workflow_full_order",
            "name": "完整外卖点餐流程",
            "description": "完整的外卖点餐流程，包括选餐厅、点餐、优惠、支付",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["完整外卖点餐流程", "点外卖", "订餐", "外卖", "喂，我要点外卖", "帮我点餐", "点外卖怎么弄", "叫个外卖"],
            "user_intents": ["点外卖", "订餐", "外卖", "点餐", "叫外卖"],
            "trigger_keywords": ["点外卖", "订餐", "外卖", "点餐"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始外卖点餐"}},
                {
                    "id": "n_restaurant_list",
                    "name": "查询餐厅",
                    "type": "api_call",
                    "description": "查询附近餐厅",
                    "config": {"api_id": "api_restaurant_list", "api_endpoint": "/api/catering/restaurants", "method": "GET", "parameters": {"location": "${location}", "cuisine": "${cuisine}"}},
                    "outputs": [{"name": "restaurants", "type": "array", "description": "餐厅列表"}],
                    "ai_instructions": {"user_message": "请输入位置和菜系偏好", "action": "查询餐厅"}
                },
                {
                    "id": "n_restaurant_detail",
                    "name": "查看餐厅详情",
                    "type": "api_call",
                    "description": "查看餐厅详细信息",
                    "config": {"api_id": "api_restaurant_detail", "api_endpoint": "/api/catering/restaurants/{restaurant_id}", "method": "GET", "parameters": {"restaurant_id": "${restaurant_id}"}},
                    "outputs": [{"name": "restaurant", "type": "object", "description": "餐厅详情"}, {"name": "rating", "type": "float", "description": "评分"}],
                    "ai_instructions": {"user_message": "请选择餐厅", "action": "查看餐厅详情"}
                },
                {
                    "id": "n_menu",
                    "name": "查询菜单",
                    "type": "api_call",
                    "description": "查询餐厅菜单",
                    "config": {"api_id": "api_menu_list", "api_endpoint": "/api/catering/restaurants/{restaurant_id}/menu", "method": "GET", "parameters": {"restaurant_id": "${restaurant_id}"}},
                    "outputs": [{"name": "dishes", "type": "array", "description": "菜品列表"}],
                    "ai_instructions": {"user_message": "查看菜单", "action": "查询菜单"}
                },
                {
                    "id": "n_coupon",
                    "name": "查询优惠券",
                    "type": "api_call",
                    "description": "查询可用优惠券",
                    "config": {"api_id": "api_coupon_list", "api_endpoint": "/api/catering/coupons", "method": "GET", "parameters": {"restaurant_id": "${restaurant_id}"}},
                    "outputs": [{"name": "coupons", "type": "array", "description": "优惠券列表"}],
                    "ai_instructions": {"user_message": "查询优惠券", "action": "查询优惠券"}
                },
                {
                    "id": "n_create",
                    "name": "创建订单",
                    "type": "api_call",
                    "description": "选择菜品创建订单",
                    "config": {"api_id": "api_order_create", "api_endpoint": "/api/catering/orders", "method": "POST", "parameters": {"restaurant_id": "${restaurant_id}", "items": "${items}", "delivery_address": "${delivery_address}", "contact_phone": "${contact_phone}", "coupon_id": "${coupon_id}", "remark": "${remark}"}},
                    "outputs": [{"name": "order_id", "type": "string", "description": "订单ID"}, {"name": "total_amount", "type": "float", "description": "总金额"}, {"name": "discount", "type": "float", "description": "优惠金额"}],
                    "ai_instructions": {"user_message": "请选择菜品并填写配送信息", "action": "创建订单"}
                },
                {
                    "id": "n_pay",
                    "name": "支付订单",
                    "type": "api_call",
                    "description": "支付订单",
                    "config": {"api_id": "api_order_pay", "api_endpoint": "/api/catering/orders/{order_id}/pay", "method": "POST", "parameters": {"order_id": "${order_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "payment_id", "type": "string", "description": "支付流水号"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "支付订单"}
                },
                {
                    "id": "n_notify",
                    "name": "下单通知",
                    "type": "notification",
                    "description": "发送下单成功通知",
                    "config": {"message_template": "下单成功！订单号：${order_id}，总金额：${total_amount}元，优惠：${discount}元，请等待配送。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "下单成功", "action": "发送下单通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "点餐完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_restaurant_list"},
                {"source": "n_restaurant_list", "target": "n_restaurant_detail"},
                {"source": "n_restaurant_detail", "target": "n_menu"},
                {"source": "n_menu", "target": "n_coupon"},
                {"source": "n_coupon", "target": "n_create"},
                {"source": "n_create", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：餐位预订流程（6步：查询餐厅 → 查看详情 → 查询时段 → 预订 → 支付 → 通知） ==========
        # ========== 用户：完整点餐流程（7步：查询餐厅 → 查看详情 → 查询菜单 → 领取优惠券 → 创建订单 → 支付 → 通知） ==========
        {
            "id": "workflow_full_order",
            "name": "完整点餐流程",
            "description": "完整的外卖点餐流程，包括查询、优惠、下单、支付",
            "business_scenario": "catering",
            "status": "active",
            "user_intents": ["点外卖", "订餐", "外卖", "点餐"],
            "trigger_keywords": ["点外卖", "订餐", "外卖", "点餐"],
            "instruction_variants": ["点外卖", "订餐", "外卖", "点餐", "喂，我要点外卖", "帮我订餐", "点餐怎么弄", "能点外卖吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始点餐"}},
                {"id": "n_restaurant_list", "name": "查询餐厅", "type": "api_call", "description": "查询附近餐厅", "config": {"api_id": "api_restaurant_list", "api_endpoint": "/api/catering/restaurants", "method": "GET", "parameters": {"location": "${location}", "cuisine": "${cuisine}"}}, "outputs": [{"name": "restaurants", "type": "array", "description": "餐厅列表"}], "ai_instructions": {"user_message": "请输入位置和菜系", "action": "查询餐厅"}},
                {"id": "n_restaurant_detail", "name": "查看餐厅详情", "type": "api_call", "description": "查看餐厅详细信息", "config": {"api_id": "api_restaurant_detail", "api_endpoint": "/api/catering/restaurants/{restaurant_id}", "method": "GET", "parameters": {"restaurant_id": "${restaurant_id}"}}, "outputs": [{"name": "restaurant", "type": "object", "description": "餐厅详情"}, {"name": "rating", "type": "float", "description": "评分"}], "ai_instructions": {"user_message": "请选择餐厅", "action": "查看餐厅详情"}},
                {"id": "n_menu", "name": "查询菜单", "type": "api_call", "description": "查询餐厅菜单", "config": {"api_id": "api_menu_list", "api_endpoint": "/api/catering/restaurants/{restaurant_id}/menu", "method": "GET", "parameters": {"restaurant_id": "${restaurant_id}"}}, "outputs": [{"name": "dishes", "type": "array", "description": "菜品列表"}], "ai_instructions": {"user_message": "查询菜单", "action": "查询菜单"}},
                {"id": "n_coupon", "name": "领取优惠券", "type": "api_call", "description": "领取可用优惠券", "config": {"api_id": "api_coupon_claim", "api_endpoint": "/api/catering/coupons/{coupon_id}/claim", "method": "POST", "parameters": {"coupon_id": "${coupon_id}"}}, "outputs": [{"name": "user_coupon_id", "type": "string", "description": "用户优惠券ID"}], "ai_instructions": {"user_message": "请选择优惠券", "action": "领取优惠券"}},
                {"id": "n_create", "name": "创建订单", "type": "api_call", "description": "创建订单", "config": {"api_id": "api_order_create", "api_endpoint": "/api/catering/orders", "method": "POST", "parameters": {"restaurant_id": "${restaurant_id}", "items": "${items}", "delivery_address": "${delivery_address}", "contact_phone": "${contact_phone}", "coupon_id": "${user_coupon_id}"}}, "outputs": [{"name": "order_id", "type": "string", "description": "订单ID"}, {"name": "total_amount", "type": "float", "description": "总金额"}], "ai_instructions": {"user_message": "请选择菜品并填写配送信息", "action": "创建订单"}},
                {"id": "n_pay", "name": "订单支付", "type": "api_call", "description": "支付订单", "config": {"api_id": "api_order_pay", "api_endpoint": "/api/catering/orders/{order_id}/pay", "method": "POST", "parameters": {"order_id": "${order_id}", "payment_method": "${payment_method}"}}, "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}], "ai_instructions": {"user_message": "请选择支付方式", "action": "订单支付"}},
                {"id": "n_notify", "name": "下单通知", "type": "notification", "description": "发送下单成功通知", "config": {"message_template": "下单成功！订单号：${order_id}，总金额：${total_amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "下单成功", "action": "发送下单通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "点餐完成"}}
            ],
            "edges": [{"source": "start", "target": "n_restaurant_list"}, {"source": "n_restaurant_list", "target": "n_restaurant_detail"}, {"source": "n_restaurant_detail", "target": "n_menu"}, {"source": "n_menu", "target": "n_coupon"}, {"source": "n_coupon", "target": "n_create"}, {"source": "n_create", "target": "n_pay"}, {"source": "n_pay", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 用户：预订餐位流程（5步：查询餐厅 → 查询时段 → 预订 → 确认 → 通知） ==========
        {
            "id": "workflow_table_reservation",
            "name": "预订餐位流程",
            "description": "预订餐厅座位",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["预订餐位流程", "订座", "预订餐位", "预约餐厅", "喂，我要订座", "帮我预订", "订座怎么弄", "预约位子"],
            "user_intents": ["订座", "预订餐位", "预约餐厅"],
            "trigger_keywords": ["订座", "预订餐位", "预约餐厅"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始预订"}},
                {"id": "n_restaurant_list", "name": "查询餐厅", "type": "api_call", "description": "查询餐厅", "config": {"api_id": "api_restaurant_list", "api_endpoint": "/api/catering/restaurants", "method": "GET", "parameters": {"location": "${location}"}}, "outputs": [{"name": "restaurants", "type": "array", "description": "餐厅列表"}], "ai_instructions": {"user_message": "请输入位置", "action": "查询餐厅"}},
                {"id": "n_slots", "name": "查询时段", "type": "api_call", "description": "查询可预订时段", "config": {"api_id": "api_table_slots", "api_endpoint": "/api/catering/restaurants/{restaurant_id}/slots", "method": "GET", "parameters": {"restaurant_id": "${restaurant_id}", "date": "${date}"}}, "outputs": [{"name": "slots", "type": "array", "description": "可选时段"}], "ai_instructions": {"user_message": "请选择餐厅和日期", "action": "查询时段"}},
                {"id": "n_reserve", "name": "预订餐位", "type": "api_call", "description": "提交预订", "config": {"api_id": "api_table_reserve", "api_endpoint": "/api/catering/reservations", "method": "POST", "parameters": {"restaurant_id": "${restaurant_id}", "date": "${date}", "time": "${time}", "guests": "${guests}", "contact_name": "${contact_name}", "contact_phone": "${contact_phone}"}}, "outputs": [{"name": "reservation_id", "type": "string", "description": "预订ID"}, {"name": "table_no", "type": "string", "description": "桌号"}], "ai_instructions": {"user_message": "请填写预订信息", "action": "预订餐位"}},
                {"id": "n_notify", "name": "预订通知", "type": "notification", "description": "发送预订成功通知", "config": {"message_template": "预订成功！预订号：${reservation_id}，桌号：${table_no}。"}, "outputs": [], "ai_instructions": {"user_message": "预订成功", "action": "发送预订通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "预订完成"}}
            ],
            "edges": [{"source": "start", "target": "n_restaurant_list"}, {"source": "n_restaurant_list", "target": "n_slots"}, {"source": "n_slots", "target": "n_reserve"}, {"source": "n_reserve", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 用户：订单评价流程（4步：查询订单 → 确认完成 → 提交评价 → 通知） ==========
        {
            "id": "workflow_review",
            "name": "订单评价流程",
            "description": "对已完成订单进行评价",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["订单评价流程", "评价", "写评价", "评分", "喂，我要评价", "帮我写评价", "评价怎么写", "给个评分"],
            "user_intents": ["评价", "写评价", "评分"],
            "trigger_keywords": ["评价", "写评价", "评分"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始评价"}},
                {"id": "n_order", "name": "查询订单", "type": "api_call", "description": "查询订单状态", "config": {"api_id": "api_order_status", "api_endpoint": "/api/catering/orders/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}}, "outputs": [{"name": "status", "type": "string", "description": "订单状态"}], "ai_instructions": {"user_message": "请输入订单号", "action": "查询订单"}},
                {"id": "n_review", "name": "提交评价", "type": "api_call", "description": "提交评价", "config": {"api_id": "api_review_submit", "api_endpoint": "/api/catering/reviews", "method": "POST", "parameters": {"order_id": "${order_id}", "rating": "${rating}", "comment": "${comment}"}}, "outputs": [{"name": "review_id", "type": "string", "description": "评价ID"}], "ai_instructions": {"user_message": "请填写评价", "action": "提交评价"}},
                {"id": "n_notify", "name": "评价通知", "type": "notification", "description": "发送评价成功通知", "config": {"message_template": "评价成功！评价ID：${review_id}。"}, "outputs": [], "ai_instructions": {"user_message": "评价成功", "action": "发送评价通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "评价完成"}}
            ],
            "edges": [{"source": "start", "target": "n_order"}, {"source": "n_order", "target": "n_review"}, {"source": "n_review", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：订单处理流程（6步：查询订单 → 查看详情 → 确认订单 → 出餐 → 分配骑手 → 完成） ==========
        {
            "id": "workflow_admin_order_process",
            "name": "管理员订单处理流程",
            "description": "处理外卖订单",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["管理员订单处理流程", "处理订单", "订单处理", "接单", "喂，我要处理订单", "帮我接单", "订单怎么处理", "处理一下订单"],
            "user_intents": ["处理订单", "订单处理", "接单"],
            "trigger_keywords": ["处理订单", "订单处理", "接单"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理订单"}},
                {"id": "n_list", "name": "查询订单", "type": "api_call", "description": "查询待处理订单", "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/catering/admin/orders", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}], "ai_instructions": {"user_message": "查询待处理订单", "action": "查询订单"}},
                {"id": "n_detail", "name": "查看详情", "type": "api_call", "description": "查看订单详情", "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/catering/admin/orders/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}}, "outputs": [{"name": "order", "type": "object", "description": "订单详情"}], "ai_instructions": {"user_message": "请选择订单", "action": "查看详情"}},
                {"id": "n_confirm", "name": "确认订单", "type": "api_call", "description": "确认接单", "config": {"api_id": "api_admin_order_confirm", "api_endpoint": "/api/catering/admin/orders/{order_id}/confirm", "method": "POST", "parameters": {"order_id": "${order_id}", "estimated_time": "${estimated_time}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请填写预计完成时间", "action": "确认订单"}},
                {"id": "n_ready", "name": "订单出餐", "type": "api_call", "description": "标记出餐", "config": {"api_id": "api_admin_order_ready", "api_endpoint": "/api/catering/admin/orders/{order_id}/ready", "method": "POST", "parameters": {"order_id": "${order_id}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "确认出餐", "action": "订单出餐"}},
                {"id": "n_assign", "name": "分配骑手", "type": "api_call", "description": "分配配送骑手", "config": {"api_id": "api_admin_rider_assign", "api_endpoint": "/api/catering/admin/orders/{order_id}/assign", "method": "POST", "parameters": {"order_id": "${order_id}", "rider_id": "${rider_id}"}}, "outputs": [{"name": "rider_name", "type": "string", "description": "骑手姓名"}], "ai_instructions": {"user_message": "请选择骑手", "action": "分配骑手"}},
                {"id": "n_notify", "name": "处理通知", "type": "notification", "description": "发送处理完成通知", "config": {"message_template": "订单${order_id}已分配给${rider_name}配送。"}, "outputs": [], "ai_instructions": {"user_message": "处理完成", "action": "发送处理通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "订单处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_detail"}, {"source": "n_detail", "target": "n_confirm"}, {"source": "n_confirm", "target": "n_ready"}, {"source": "n_ready", "target": "n_assign"}, {"source": "n_assign", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：退款处理流程（4步：查询退款 → 查看详情 → 处理退款 → 通知） ==========
        {
            "id": "workflow_admin_refund",
            "name": "管理员退款处理流程",
            "description": "处理订单退款",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["管理员退款处理流程", "处理退款", "退款处理", "审核退款", "喂，我要处理退款", "帮我审核退款", "退款怎么处理", "审批退款"],
            "user_intents": ["处理退款", "退款处理", "审核退款"],
            "trigger_keywords": ["处理退款", "退款处理", "审核退款"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理退款"}},
                {"id": "n_list", "name": "查询退款", "type": "api_call", "description": "查询待处理退款", "config": {"api_id": "api_admin_refund_list", "api_endpoint": "/api/catering/admin/refunds", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "refunds", "type": "array", "description": "退款列表"}], "ai_instructions": {"user_message": "查询待处理退款", "action": "查询退款"}},
                {"id": "n_process", "name": "处理退款", "type": "api_call", "description": "处理退款申请", "config": {"api_id": "api_admin_refund_process", "api_endpoint": "/api/catering/admin/refunds/{order_id}/process", "method": "POST", "parameters": {"order_id": "${order_id}", "action": "${action}", "refund_amount": "${refund_amount}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择退款并填写处理结果", "action": "处理退款"}},
                {"id": "n_notify", "name": "退款通知", "type": "notification", "description": "发送退款处理通知", "config": {"message_template": "退款处理完成！订单${order_id}，退款金额：${refund_amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "处理完成", "action": "发送退款通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退款处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_process"}, {"source": "n_process", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：预订管理流程（4步：查询预订 → 签到确认 → 安排桌位 → 通知） ==========
        {
            "id": "workflow_admin_reservation",
            "name": "管理员预订管理流程",
            "description": "管理餐位预订",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["管理员预订管理流程", "预订管理", "管理预订", "预订签到", "喂，我要管理预订", "帮我处理预订", "预订怎么管理", "签到管理"],
            "user_intents": ["预订管理", "管理预订", "预订签到"],
            "trigger_keywords": ["预订管理", "管理预订", "预订签到"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始预订管理"}},
                {"id": "n_list", "name": "查询预订", "type": "api_call", "description": "查询今日预订", "config": {"api_id": "api_admin_reservation_list", "api_endpoint": "/api/catering/admin/reservations", "method": "GET", "parameters": {"date": "${today}"}}, "outputs": [{"name": "reservations", "type": "array", "description": "预订列表"}], "ai_instructions": {"user_message": "查询今日预订", "action": "查询预订"}},
                {"id": "n_checkin", "name": "签到确认", "type": "api_call", "description": "确认客户签到", "config": {"api_id": "api_admin_reservation_checkin", "api_endpoint": "/api/catering/admin/reservations/{reservation_id}/checkin", "method": "POST", "parameters": {"reservation_id": "${reservation_id}"}}, "outputs": [{"name": "table_no", "type": "string", "description": "桌号"}], "ai_instructions": {"user_message": "请选择预订进行签到", "action": "签到确认"}},
                {"id": "n_notify", "name": "签到通知", "type": "notification", "description": "发送签到成功通知", "config": {"message_template": "签到成功！预订号${reservation_id}，桌号：${table_no}。"}, "outputs": [], "ai_instructions": {"user_message": "签到成功", "action": "发送签到通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "预订管理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_checkin"}, {"source": "n_checkin", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：投诉处理流程（4步：查询投诉 → 查看详情 → 处理投诉 → 通知） ==========
        {
            "id": "workflow_admin_complaint",
            "name": "管理员投诉处理流程",
            "description": "处理客户投诉",
            "business_scenario": "catering",
            "status": "active",
            "instruction_variants": ["管理员投诉处理流程", "处理投诉", "投诉处理", "解决投诉", "喂，我要处理投诉", "帮我解决投诉", "投诉怎么处理", "处理客诉"],
            "user_intents": ["处理投诉", "投诉处理", "解决投诉"],
            "trigger_keywords": ["处理投诉", "投诉处理", "解决投诉"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理投诉"}},
                {"id": "n_list", "name": "查询投诉", "type": "api_call", "description": "查询待处理投诉", "config": {"api_id": "api_admin_complaint_list", "api_endpoint": "/api/catering/admin/complaints", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "complaints", "type": "array", "description": "投诉列表"}], "ai_instructions": {"user_message": "查询待处理投诉", "action": "查询投诉"}},
                {"id": "n_handle", "name": "处理投诉", "type": "api_call", "description": "处理投诉", "config": {"api_id": "api_admin_complaint_handle", "api_endpoint": "/api/catering/admin/complaints/{complaint_id}/handle", "method": "POST", "parameters": {"complaint_id": "${complaint_id}", "result": "${result}", "compensation": "${compensation}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择投诉并填写处理结果", "action": "处理投诉"}},
                {"id": "n_notify", "name": "处理通知", "type": "notification", "description": "发送处理完成通知", "config": {"message_template": "投诉处理完成！投诉单号${complaint_id}，赔偿金额：${compensation}元。"}, "outputs": [], "ai_instructions": {"user_message": "处理完成", "action": "发送处理通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "投诉处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_handle"}, {"source": "n_handle", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        }
    ]
}
