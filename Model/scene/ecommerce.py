# ecommerce.py - 电商场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

ECOMMERCE_SCENE = {
    "domain": "ecommerce",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_prod_search", "path": "/api/shop/search", "method": "GET", "desc": "搜索商品",
         "instruction_variants": ["搜索商品", "找商品", "搜索", "查商品", "喂，我要找东西", "帮我搜商品", "搜索怎么用", "查一下商品"],
         "request": [{"name": "keyword", "type": "string", "label": "搜索关键词", "required": True}, {"name": "category", "type": "string", "label": "分类", "required": False}],
         "response": [{"name": "items", "type": "array", "desc": "商品列表"}]},
        {"id": "api_prod_detail", "path": "/api/shop/products/{sku_id}", "method": "GET", "desc": "查询商品详情",
         "instruction_variants": ["查询商品详情", "商品详情", "看详情", "商品信息", "喂，这商品怎么样", "帮我看看详情", "详情在哪", "查一下商品"],
         "request": [{"name": "sku_id", "type": "string", "label": "商品SKU", "required": True}],
         "response": [{"name": "product", "type": "object", "desc": "商品详情"}, {"name": "stock", "type": "integer", "desc": "库存"}, {"name": "price", "type": "float", "desc": "价格"}]},
        {"id": "api_cart_add", "workflow_only": True, "path": "/api/shop/cart", "method": "POST", "desc": "添加到购物车",
         "instruction_variants": ["添加到购物车", "加购物车", "加购", "放购物车", "喂，我要加购", "帮我加购物车", "加购怎么弄", "添加到购物车"],
         "request": [{"name": "sku_id", "type": "string", "label": "商品SKU", "required": True}, {"name": "quantity", "type": "integer", "label": "数量", "required": True}],
         "response": [{"name": "cart_id", "type": "string", "desc": "购物车ID"}, {"name": "cart_count", "type": "integer", "desc": "购物车商品数"}]},
        {"id": "api_cart_list", "path": "/api/shop/cart", "method": "GET", "desc": "查询购物车",
         "instruction_variants": ["查询购物车", "购物车", "我的购物车", "购物车里有啥", "喂，购物车在哪", "帮我看看购物车", "购物车怎么查", "查一下购物车"],
         "request": [], "response": [{"name": "items", "type": "array", "desc": "购物车商品列表"}, {"name": "total_price", "type": "float", "desc": "总价"}]},
        {"id": "api_address_list", "path": "/api/shop/addresses", "method": "GET", "desc": "查询收货地址",
         "instruction_variants": ["查询收货地址", "收货地址", "我的地址", "地址列表", "喂，地址在哪", "帮我看看地址", "地址怎么查", "查一下地址"],
         "request": [], "response": [{"name": "addresses", "type": "array", "desc": "地址列表"}, {"name": "address_id", "type": "string", "desc": "默认地址ID"}]},
        {"id": "api_coupon_list", "path": "/api/shop/coupons", "method": "GET", "desc": "查询可用优惠券",
         "instruction_variants": ["查询可用优惠券", "优惠券", "有什么优惠", "券", "喂，有优惠吗", "帮我看看优惠券", "优惠券怎么领", "查一下优惠"],
         "request": [{"name": "order_amount", "type": "float", "label": "订单金额", "required": False}],
         "response": [{"name": "coupons", "type": "array", "desc": "优惠券列表"}]},
        {"id": "api_coupon_apply", "workflow_only": True, "path": "/api/shop/coupons/apply", "method": "POST", "desc": "使用优惠券",
         "instruction_variants": ["使用优惠券", "用优惠券", "优惠券", "用券", "喂，我要用券", "帮我用优惠券", "优惠券怎么用", "用一下券"],
         "request": [{"name": "coupon_id", "type": "string", "label": "优惠券ID", "required": True}, {"name": "order_amount", "type": "float", "label": "订单金额", "required": True}],
         "response": [{"name": "discount_amount", "type": "float", "desc": "优惠金额"}, {"name": "final_amount", "type": "float", "desc": "最终金额"}]},
        {"id": "api_order_preview", "workflow_only": True, "path": "/api/shop/orders/preview", "method": "POST", "desc": "订单预览",
         "instruction_variants": ["订单预览", "预览订单", "看看价格", "算一下", "喂，多少钱", "帮我算算", "预览怎么看", "查一下价格"],
         "request": [{"name": "sku_id", "type": "string", "label": "商品SKU", "required": True}, {"name": "quantity", "type": "integer", "label": "数量", "required": True}, {"name": "address_id", "type": "string", "label": "地址ID", "required": True}, {"name": "coupon_id", "type": "string", "label": "优惠券ID", "required": False}],
         "response": [{"name": "total_amount", "type": "float", "desc": "商品总额"}, {"name": "shipping_fee", "type": "float", "desc": "运费"}, {"name": "discount_amount", "type": "float", "desc": "优惠金额"}, {"name": "final_amount", "type": "float", "desc": "应付金额"}]},
        {"id": "api_order_create", "workflow_only": True, "path": "/api/shop/orders", "method": "POST", "desc": "创建订单",
         "instruction_variants": ["创建订单", "下单", "提交订单", "我要买", "喂，我要下单", "帮我下单", "下单怎么弄", "提交订单"],
         "request": [{"name": "sku_id", "type": "string", "label": "商品SKU", "required": True}, {"name": "quantity", "type": "integer", "label": "数量", "required": True}, {"name": "address_id", "type": "string", "label": "收货地址ID", "required": True}, {"name": "coupon_id", "type": "string", "label": "优惠券ID", "required": False}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "order_id", "type": "string", "desc": "订单号"}, {"name": "total_amount", "type": "float", "desc": "订单总额"}]},
        {"id": "api_order_pay", "workflow_only": True, "path": "/api/shop/orders/{order_id}/pay", "method": "POST", "desc": "订单支付",
         "instruction_variants": ["订单支付", "支付", "付款", "我要付款", "喂，怎么付钱", "帮我支付", "支付怎么弄", "付钱"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "payment_id", "type": "string", "desc": "支付流水号"}]},
        {"id": "api_order_query", "path": "/api/shop/orders/{order_id}", "method": "GET", "desc": "查询订单详情",
         "instruction_variants": ["查询订单详情", "订单详情", "我的订单", "订单信息", "喂，订单怎么样了", "帮我查查订单", "订单详细", "查一下订单"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "order", "type": "object", "desc": "订单详情"}, {"name": "status", "type": "string", "desc": "订单状态"}, {"name": "total_amount", "type": "float", "desc": "订单金额"}]},
        {"id": "api_order_list", "path": "/api/shop/orders", "method": "GET", "desc": "查询订单列表",
         "instruction_variants": ["查询订单列表", "订单列表", "我的订单", "所有订单", "喂，我的订单呢", "帮我看看订单", "订单怎么查", "查一下订单"],
         "request": [{"name": "status", "type": "string", "label": "订单状态", "required": False}],
         "response": [{"name": "orders", "type": "array", "desc": "订单列表"}]},
        {"id": "api_order_cancel", "workflow_only": True, "path": "/api/shop/orders/{order_id}/cancel", "method": "POST", "desc": "取消订单",
         "instruction_variants": ["取消订单", "取消", "不要了", "退单", "喂，我要取消", "帮我取消订单", "取消怎么办", "不想要了"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}, {"name": "reason", "type": "string", "label": "取消原因", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_order_confirm", "workflow_only": True, "path": "/api/shop/orders/{order_id}/confirm", "method": "POST", "desc": "确认收货",
         "instruction_variants": ["确认收货", "收货", "确认", "收到了", "喂，我收到了", "帮我确认收货", "确认怎么弄", "收货确认"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_refund_check", "workflow_only": True, "path": "/api/shop/refunds/check", "method": "POST", "desc": "退款预检查",
         "instruction_variants": ["退款预检查", "能退款吗", "退款检查", "可以退吗", "喂，能退吗", "帮我查查能不能退", "退款政策", "查一下退款"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "can_refund", "type": "boolean", "desc": "是否可退款"}, {"name": "max_refund_amount", "type": "float", "desc": "最大可退金额"}, {"name": "refund_policy", "type": "string", "desc": "退款政策"}]},
        {"id": "api_refund_apply", "workflow_only": True, "path": "/api/shop/refunds", "method": "POST", "desc": "申请退款",
         "instruction_variants": ["申请退款", "退款", "退货", "我要退款", "喂，怎么退款", "帮我退款", "退款怎么办", "申请退货"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}, {"name": "reason", "type": "string", "label": "退款原因", "required": True}, {"name": "amount", "type": "float", "label": "退款金额", "required": True}, {"name": "images", "type": "array", "label": "凭证图片", "required": False}],
         "response": [{"name": "refund_id", "type": "string", "desc": "退款单号"}, {"name": "status", "type": "string", "desc": "退款状态"}]},
        {"id": "api_refund_query", "path": "/api/shop/refunds/{refund_id}", "method": "GET", "desc": "查询退款状态",
         "instruction_variants": ["查询退款状态", "退款状态", "退款进度", "退款到哪了", "喂，退款怎么样了", "帮我查查退款", "退款查询", "查一下退款"],
         "request": [{"name": "refund_id", "type": "string", "label": "退款单号", "required": True}],
         "response": [{"name": "refund", "type": "object", "desc": "退款详情"}, {"name": "status", "type": "string", "desc": "退款状态"}]},
        {"id": "api_logistics_query", "path": "/api/shop/logistics/{order_id}", "method": "GET", "desc": "查询物流信息",
         "instruction_variants": ["查询物流信息", "物流", "快递", "物流到哪了", "喂，快递到哪了", "帮我查查物流", "物流查询", "查一下快递"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "logistics", "type": "object", "desc": "物流信息"}, {"name": "tracking_number", "type": "string", "desc": "快递单号"}, {"name": "status", "type": "string", "desc": "物流状态"}]},
        {"id": "api_review_submit", "workflow_only": True, "path": "/api/shop/reviews", "method": "POST", "desc": "提交评价",
         "instruction_variants": ["提交评价", "评价", "写评价", "打分", "喂，我要评价", "帮我写评价", "评价怎么写", "给个评分"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}, {"name": "rating", "type": "integer", "label": "评分", "required": True}, {"name": "content", "type": "string", "label": "评价内容", "required": True}, {"name": "images", "type": "array", "label": "图片", "required": False}],
         "response": [{"name": "review_id", "type": "string", "desc": "评价ID"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_order_list", "workflow_only": True, "path": "/api/shop/admin/orders", "method": "GET", "desc": "查询订单列表（管理员）",
         "instruction_variants": ["查询订单列表", "订单列表", "所有订单", "订单管理", "喂，有哪些订单", "帮我看看订单", "订单怎么样", "查一下订单"],
         "request": [{"name": "status", "type": "string", "label": "订单状态", "required": False}, {"name": "date_from", "type": "date", "label": "开始日期", "required": False}, {"name": "date_to", "type": "date", "label": "结束日期", "required": False}],
         "response": [{"name": "orders", "type": "array", "desc": "订单列表"}, {"name": "total_count", "type": "integer", "desc": "订单总数"}]},
        {"id": "api_admin_order_detail", "workflow_only": True, "path": "/api/shop/admin/orders/{order_id}", "method": "GET", "desc": "查询订单详情（管理员）",
         "instruction_variants": ["查询订单详情", "订单详情", "订单信息", "查看订单", "喂，这订单什么情况", "帮我看看详情", "订单详细信息", "查一下订单"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}],
         "response": [{"name": "order", "type": "object", "desc": "订单详情"}, {"name": "customer", "type": "object", "desc": "客户信息"}, {"name": "items", "type": "array", "desc": "商品列表"}]},
        {"id": "api_admin_order_ship", "workflow_only": True, "path": "/api/shop/admin/orders/{order_id}/ship", "method": "POST", "desc": "订单发货",
         "instruction_variants": ["订单发货", "发货", "发快递", "安排发货", "喂，我要发货", "帮我发货", "发货怎么弄", "安排快递"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}, {"name": "logistics_company", "type": "string", "label": "快递公司", "required": True}, {"name": "tracking_number", "type": "string", "label": "快递单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "ship_time", "type": "datetime", "desc": "发货时间"}]},
        {"id": "api_admin_refund_list", "workflow_only": True, "path": "/api/shop/admin/refunds", "method": "GET", "desc": "查询退款申请列表",
         "instruction_variants": ["查询退款申请列表", "退款列表", "退款申请", "退款管理", "喂，有哪些退款", "帮我看看退款", "退款怎么样", "查一下退款"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "refunds", "type": "array", "desc": "退款列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数量"}]},
        {"id": "api_admin_refund_detail", "workflow_only": True, "path": "/api/shop/admin/refunds/{refund_id}", "method": "GET", "desc": "查询退款详情",
         "instruction_variants": ["查询退款详情", "退款详情", "退款信息", "查看退款", "喂，这退款什么情况", "帮我看看退款详情", "退款详细信息", "查一下退款"],
         "request": [{"name": "refund_id", "type": "string", "label": "退款单号", "required": True}],
         "response": [{"name": "refund", "type": "object", "desc": "退款详情"}, {"name": "order", "type": "object", "desc": "订单信息"}, {"name": "customer", "type": "object", "desc": "客户信息"}]},
        {"id": "api_admin_refund_approve", "workflow_only": True, "path": "/api/shop/admin/refunds/{refund_id}/approve", "method": "POST", "desc": "审批退款",
         "instruction_variants": ["审批退款", "退款审批", "审核退款", "批准退款", "喂，我要审批", "帮我审核退款", "审批怎么弄", "批准一下"],
         "request": [{"name": "refund_id", "type": "string", "label": "退款单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "approved_amount", "type": "float", "label": "批准金额", "required": False}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "refund_id", "type": "string", "desc": "退款单号"}]},
        {"id": "api_admin_refund_process", "workflow_only": True, "path": "/api/shop/admin/refunds/{refund_id}/process", "method": "POST", "desc": "处理退款",
         "instruction_variants": ["处理退款", "退款处理", "执行退款", "退款到账", "喂，我要处理退款", "帮我退款", "处理怎么弄", "执行退款"],
         "request": [{"name": "refund_id", "type": "string", "label": "退款单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "refund_time", "type": "datetime", "desc": "退款时间"}]},
        {"id": "api_admin_product_list", "workflow_only": True, "path": "/api/shop/admin/products", "method": "GET", "desc": "查询商品列表（管理员）",
         "instruction_variants": ["查询商品列表", "商品列表", "所有商品", "商品管理", "喂，有哪些商品", "帮我看看商品", "商品怎么样", "查一下商品"],
         "request": [{"name": "category", "type": "string", "label": "分类", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "products", "type": "array", "desc": "商品列表"}]},
        {"id": "api_admin_product_create", "workflow_only": True, "path": "/api/shop/admin/products", "method": "POST", "desc": "创建商品",
         "instruction_variants": ["创建商品", "新增商品", "上架商品", "添加商品", "喂，我要上架", "帮我创建商品", "上架怎么弄", "添加新商品"],
         "request": [{"name": "name", "type": "string", "label": "商品名称", "required": True}, {"name": "category", "type": "string", "label": "分类", "required": True}, {"name": "price", "type": "float", "label": "价格", "required": True}, {"name": "stock", "type": "integer", "label": "库存", "required": True}, {"name": "description", "type": "string", "label": "描述", "required": False}],
         "response": [{"name": "sku_id", "type": "string", "desc": "商品SKU"}]},
        {"id": "api_admin_product_update", "workflow_only": True, "path": "/api/shop/admin/products/{sku_id}", "method": "PUT", "desc": "更新商品",
         "instruction_variants": ["更新商品", "修改商品", "编辑商品", "改商品", "喂，我要改商品", "帮我更新商品", "更新怎么弄", "修改一下"],
         "request": [{"name": "sku_id", "type": "string", "label": "商品SKU", "required": True}, {"name": "price", "type": "float", "label": "价格", "required": False}, {"name": "stock", "type": "integer", "label": "库存", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_stock_check", "workflow_only": True, "path": "/api/shop/admin/stock/check", "method": "GET", "desc": "库存检查",
         "instruction_variants": ["库存检查", "检查库存", "库存预警", "低库存", "喂，库存怎么样", "帮我查查库存", "库存不足", "查一下库存"],
         "request": [{"name": "threshold", "type": "integer", "label": "库存阈值", "required": False}],
         "response": [{"name": "low_stock_items", "type": "array", "desc": "低库存商品"}, {"name": "out_of_stock_count", "type": "integer", "desc": "缺货商品数"}]},
        {"id": "api_admin_stock_replenish", "workflow_only": True, "path": "/api/shop/admin/stock/replenish", "method": "POST", "desc": "库存补货",
         "instruction_variants": ["库存补货", "补货", "进货", "补充库存", "喂，我要补货", "帮我补货", "补货怎么弄", "进点货"],
         "request": [{"name": "sku_id", "type": "string", "label": "商品SKU", "required": True}, {"name": "quantity", "type": "integer", "label": "补货数量", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "new_stock", "type": "integer", "desc": "新库存"}]},
        # ========== 管理员统计 API ==========
        {"id": "api_admin_sales_overview", "path": "/api/shop/admin/sales/overview", "method": "GET", "desc": "查询销售大盘", "name": "销售大盘", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询销售大盘", "销售大盘", "销售数据", "营业额", "喂，今天卖了多少", "帮我看看销售", "销售情况", "查一下营业额"],
         "request": [], "response": [{"name": "today_sales", "type": "float", "desc": "今日销售额"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_category_analysis", "path": "/api/shop/admin/category/analysis", "method": "GET", "desc": "查询品类分析", "name": "品类分析", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询品类分析", "品类分析", "品类数据", "分类统计", "喂，哪个品类卖得好", "帮我看看品类", "品类情况", "查一下分类"],
         "request": [], "response": [{"name": "categories", "type": "array", "desc": "品类"}, {"name": "sales", "type": "array", "desc": "销售额"}]},
        {"id": "api_admin_order_stats", "path": "/api/shop/admin/order/stats", "method": "GET", "desc": "查询订单统计", "name": "订单统计", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询订单统计", "订单统计", "订单数据", "订单分析", "喂，订单情况怎么样", "帮我看看订单统计", "订单分析", "查一下订单"],
         "request": [], "response": [{"name": "statuses", "type": "array", "desc": "状态"}, {"name": "counts", "type": "array", "desc": "数量"}]},
    ],

    "workflows": [
        # ========== 用户：完整购物流程（8步：搜索 → 详情 → 加购物车 → 选地址 → 选优惠券 → 预览订单 → 创建订单 → 支付） ==========
        {
            "id": "workflow_full_checkout",
            "name": "完整购物流程",
            "description": "完整的购物下单流程，包括搜索商品、查看详情、加入购物车、选择地址、使用优惠券、订单预览、创建订单和支付",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["完整购物流程", "买", "购买", "下单", "喂，我要买东西", "帮我买", "购物怎么办", "我要下单"],
            "user_intents": ["买", "购买", "下单", "购物"],
            "trigger_keywords": ["买", "购买", "下单", "购物"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始购物"}},
                {
                    "id": "n_search",
                    "name": "搜索商品",
                    "type": "api_call",
                    "description": "搜索想要购买的商品",
                    "config": {"api_id": "api_prod_search", "api_endpoint": "/api/shop/search", "method": "GET", "parameters": {"keyword": "${keyword}", "category": "${category}"}},
                    "outputs": [{"name": "items", "type": "array", "description": "商品列表"}, {"name": "sku_id", "type": "string", "description": "选中商品SKU"}],
                    "ai_instructions": {"user_message": "请输入要搜索的商品关键词", "action": "搜索商品"}
                },
                {
                    "id": "n_detail",
                    "name": "查看详情",
                    "type": "api_call",
                    "description": "查看商品详情和库存",
                    "config": {"api_id": "api_prod_detail", "api_endpoint": "/api/shop/products/{sku_id}", "method": "GET", "parameters": {"sku_id": "${sku_id}"}},
                    "outputs": [{"name": "product", "type": "object", "description": "商品详情"}, {"name": "stock", "type": "integer", "description": "库存"}, {"name": "price", "type": "float", "description": "价格"}],
                    "ai_instructions": {"user_message": "请选择商品查看详情", "action": "查看商品详情"}
                },
                {
                    "id": "n_add_cart",
                    "name": "加入购物车",
                    "type": "api_call",
                    "description": "将商品加入购物车",
                    "config": {"api_id": "api_cart_add", "api_endpoint": "/api/shop/cart", "method": "POST", "parameters": {"sku_id": "${sku_id}", "quantity": "${quantity}"}},
                    "outputs": [{"name": "cart_id", "type": "string", "description": "购物车ID"}, {"name": "cart_count", "type": "integer", "description": "购物车商品数"}],
                    "ai_instructions": {"user_message": "请输入购买数量", "action": "加入购物车"}
                },
                {
                    "id": "n_select_address",
                    "name": "选择地址",
                    "type": "api_call",
                    "description": "选择收货地址",
                    "config": {"api_id": "api_address_list", "api_endpoint": "/api/shop/addresses", "method": "GET", "parameters": {}},
                    "outputs": [{"name": "addresses", "type": "array", "description": "地址列表"}, {"name": "address_id", "type": "string", "description": "选中地址ID"}],
                    "ai_instructions": {"user_message": "请选择收货地址", "action": "选择地址"}
                },
                {
                    "id": "n_select_coupon",
                    "name": "选择优惠券",
                    "type": "api_call",
                    "description": "查询并选择可用优惠券",
                    "config": {"api_id": "api_coupon_list", "api_endpoint": "/api/shop/coupons", "method": "GET", "parameters": {"order_amount": "${order_amount}"}},
                    "outputs": [{"name": "coupons", "type": "array", "description": "优惠券列表"}, {"name": "coupon_id", "type": "string", "description": "选中优惠券ID"}],
                    "ai_instructions": {"user_message": "请选择要使用的优惠券", "action": "选择优惠券"}
                },
                {
                    "id": "n_preview",
                    "name": "订单预览",
                    "type": "api_call",
                    "description": "预览订单金额",
                    "config": {"api_id": "api_order_preview", "api_endpoint": "/api/shop/orders/preview", "method": "POST", "parameters": {"sku_id": "${sku_id}", "quantity": "${quantity}", "address_id": "${address_id}", "coupon_id": "${coupon_id}"}},
                    "outputs": [{"name": "total_amount", "type": "float", "description": "商品总额"}, {"name": "shipping_fee", "type": "float", "description": "运费"}, {"name": "discount_amount", "type": "float", "description": "优惠金额"}, {"name": "final_amount", "type": "float", "description": "应付金额"}],
                    "ai_instructions": {"user_message": "正在计算订单金额", "action": "订单预览"}
                },
                {
                    "id": "n_create_order",
                    "name": "创建订单",
                    "type": "api_call",
                    "description": "创建订单",
                    "config": {"api_id": "api_order_create", "api_endpoint": "/api/shop/orders", "method": "POST", "parameters": {"sku_id": "${sku_id}", "quantity": "${quantity}", "address_id": "${address_id}", "coupon_id": "${coupon_id}", "remark": "${remark}"}},
                    "outputs": [{"name": "order_id", "type": "string", "description": "订单号"}, {"name": "total_amount", "type": "float", "description": "订单总额"}],
                    "ai_instructions": {"user_message": "请确认订单信息", "action": "创建订单"}
                },
                {
                    "id": "n_pay",
                    "name": "订单支付",
                    "type": "api_call",
                    "description": "支付订单",
                    "config": {"api_id": "api_order_pay", "api_endpoint": "/api/shop/orders/{order_id}/pay", "method": "POST", "parameters": {"order_id": "${order_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "payment_id", "type": "string", "description": "支付流水号"}],
                    "ai_instructions": {"user_message": "请选择支付方式完成支付", "action": "订单支付"}
                },
                {
                    "id": "n_notify",
                    "name": "下单通知",
                    "type": "notification",
                    "description": "发送下单成功通知",
                    "config": {"message_template": "下单成功！订单号：${order_id}，应付金额：${final_amount}元，支付流水号：${payment_id}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "下单成功", "action": "发送下单通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "购物完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_search"},
                {"source": "n_search", "target": "n_detail"},
                {"source": "n_detail", "target": "n_add_cart"},
                {"source": "n_add_cart", "target": "n_select_address"},
                {"source": "n_select_address", "target": "n_select_coupon"},
                {"source": "n_select_coupon", "target": "n_preview"},
                {"source": "n_preview", "target": "n_create_order"},
                {"source": "n_create_order", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：退款申请流程（6步：查询订单 → 退款检查 → 填写申请 → 提交 → 等待审核 → 通知） ==========
        {
            "id": "workflow_refund_apply",
            "name": "退款申请流程",
            "description": "完整的退款申请流程，包括订单查询、退款政策检查、申请提交和审核通知",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["退款申请流程", "退款", "退货", "申请退款", "喂，我要退款", "帮我退款", "退款怎么办", "退货申请"],
            "user_intents": ["退款", "退货", "申请退款"],
            "trigger_keywords": ["退款", "退货", "申请退款"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始退款申请"}},
                {
                    "id": "n_query_order",
                    "name": "查询订单",
                    "type": "api_call",
                    "description": "查询要退款的订单",
                    "config": {"api_id": "api_order_query", "api_endpoint": "/api/shop/orders/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "status", "type": "string", "description": "订单状态"}, {"name": "total_amount", "type": "float", "description": "订单金额"}],
                    "ai_instructions": {"user_message": "请输入要退款的订单号", "action": "查询订单"}
                },
                {
                    "id": "n_refund_check",
                    "name": "退款检查",
                    "type": "api_call",
                    "description": "检查退款政策和可退金额",
                    "config": {"api_id": "api_refund_check", "api_endpoint": "/api/shop/refunds/check", "method": "POST", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "can_refund", "type": "boolean", "description": "是否可退款"}, {"name": "max_refund_amount", "type": "float", "description": "最大可退金额"}, {"name": "refund_policy", "type": "string", "description": "退款政策"}],
                    "ai_instructions": {"user_message": "正在检查退款政策", "action": "退款检查"}
                },
                {
                    "id": "n_submit_refund",
                    "name": "提交退款申请",
                    "type": "api_call",
                    "description": "填写退款原因并提交申请",
                    "config": {"api_id": "api_refund_apply", "api_endpoint": "/api/shop/refunds", "method": "POST", "parameters": {"order_id": "${order_id}", "reason": "${reason}", "amount": "${amount}", "images": "${images}"}},
                    "outputs": [{"name": "refund_id", "type": "string", "description": "退款单号"}, {"name": "status", "type": "string", "description": "退款状态"}],
                    "ai_instructions": {"user_message": "请填写退款原因和金额", "action": "提交退款申请"}
                },
                {
                    "id": "n_notify",
                    "name": "申请提交通知",
                    "type": "notification",
                    "description": "发送退款申请提交成功通知",
                    "config": {"message_template": "退款申请已提交！退款单号：${refund_id}，申请金额：${amount}元，请等待商家审核。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "退款申请已提交", "action": "发送申请通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退款申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query_order"},
                {"source": "n_query_order", "target": "n_refund_check"},
                {"source": "n_refund_check", "target": "n_submit_refund"},
                {"source": "n_submit_refund", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：确认收货并评价流程（5步：查询订单 → 查询物流 → 确认收货 → 提交评价 → 通知） ==========
        {
            "id": "workflow_confirm_review",
            "name": "确认收货并评价",
            "description": "确认收货并提交商品评价",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["确认收货并评价", "确认收货", "收货", "评价", "喂，我要确认收货", "帮我收货", "确认怎么办", "写评价"],
            "user_intents": ["确认收货", "收货", "评价"],
            "trigger_keywords": ["确认收货", "收货", "评价"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始确认收货"}},
                {
                    "id": "n_query_order",
                    "name": "查询订单",
                    "type": "api_call",
                    "description": "查询订单信息",
                    "config": {"api_id": "api_order_query", "api_endpoint": "/api/shop/orders/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "status", "type": "string", "description": "订单状态"}],
                    "ai_instructions": {"user_message": "请输入订单号", "action": "查询订单"}
                },
                {
                    "id": "n_query_logistics",
                    "name": "查询物流",
                    "type": "api_call",
                    "description": "查询物流信息",
                    "config": {"api_id": "api_logistics_query", "api_endpoint": "/api/shop/logistics/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "logistics", "type": "object", "description": "物流信息"}, {"name": "tracking_number", "type": "string", "description": "快递单号"}, {"name": "status", "type": "string", "description": "物流状态"}],
                    "ai_instructions": {"user_message": "正在查询物流信息", "action": "查询物流"}
                },
                {
                    "id": "n_confirm",
                    "name": "确认收货",
                    "type": "api_call",
                    "description": "确认收货",
                    "config": {"api_id": "api_order_confirm", "api_endpoint": "/api/shop/orders/{order_id}/confirm", "method": "POST", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请确认收货", "action": "确认收货"}
                },
                {
                    "id": "n_review",
                    "name": "提交评价",
                    "type": "api_call",
                    "description": "提交商品评价",
                    "config": {"api_id": "api_review_submit", "api_endpoint": "/api/shop/reviews", "method": "POST", "parameters": {"order_id": "${order_id}", "rating": "${rating}", "content": "${content}", "images": "${images}"}},
                    "outputs": [{"name": "review_id", "type": "string", "description": "评价ID"}],
                    "ai_instructions": {"user_message": "请填写评价内容", "action": "提交评价"}
                },
                {
                    "id": "n_notify",
                    "name": "评价完成通知",
                    "type": "notification",
                    "description": "发送评价完成通知",
                    "config": {"message_template": "评价已提交！感谢您的评价，祝您购物愉快。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "评价完成", "action": "发送评价通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "确认收货完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query_order"},
                {"source": "n_query_order", "target": "n_query_logistics"},
                {"source": "n_query_logistics", "target": "n_confirm"},
                {"source": "n_confirm", "target": "n_review"},
                {"source": "n_review", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：订单发货流程（5步：查询待发货 → 查看详情 → 填写物流 → 发货 → 通知） ==========
        {
            "id": "workflow_admin_ship",
            "name": "订单发货流程",
            "description": "管理员订单发货流程，包括待发货订单查询、物流信息填写和发货确认",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["订单发货流程", "发货", "订单发货", "处理发货", "喂，我要发货", "帮我发货", "发货怎么办", "安排发货"],
            "user_intents": ["发货", "订单发货", "处理发货"],
            "trigger_keywords": ["发货", "订单发货"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始发货流程"}},
                {
                    "id": "n_order_list",
                    "name": "查询待发货订单",
                    "type": "api_call",
                    "description": "查询待发货的订单列表",
                    "config": {"api_id": "api_admin_order_list", "api_endpoint": "/api/shop/admin/orders", "method": "GET", "parameters": {"status": "paid"}},
                    "outputs": [{"name": "orders", "type": "array", "description": "订单列表"}, {"name": "total_count", "type": "integer", "description": "订单总数"}],
                    "ai_instructions": {"user_message": "正在查询待发货订单", "action": "查询待发货订单"}
                },
                {
                    "id": "n_order_detail",
                    "name": "查看订单详情",
                    "type": "api_call",
                    "description": "查看订单详细信息",
                    "config": {"api_id": "api_admin_order_detail", "api_endpoint": "/api/shop/admin/orders/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "order", "type": "object", "description": "订单详情"}, {"name": "customer", "type": "object", "description": "客户信息"}, {"name": "items", "type": "array", "description": "商品列表"}],
                    "ai_instructions": {"user_message": "请选择要发货的订单", "action": "查看订单详情"}
                },
                {
                    "id": "n_ship",
                    "name": "填写物流发货",
                    "type": "api_call",
                    "description": "填写物流信息并发货",
                    "config": {"api_id": "api_admin_order_ship", "api_endpoint": "/api/shop/admin/orders/{order_id}/ship", "method": "POST", "parameters": {"order_id": "${order_id}", "logistics_company": "${logistics_company}", "tracking_number": "${tracking_number}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "ship_time", "type": "datetime", "description": "发货时间"}],
                    "ai_instructions": {"user_message": "请填写快递公司和快递单号", "action": "填写物流发货"}
                },
                {
                    "id": "n_notify",
                    "name": "发货通知",
                    "type": "notification",
                    "description": "发送发货成功通知",
                    "config": {"message_template": "订单已发货！订单号：${order_id}，快递单号：${tracking_number}，已通知买家。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "发货成功", "action": "发送发货通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "发货完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_order_list"},
                {"source": "n_order_list", "target": "n_order_detail"},
                {"source": "n_order_detail", "target": "n_ship"},
                {"source": "n_ship", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：退款审批流程（6步：查询待审批 → 查看详情 → 核实信息 → 审批决定 → 处理退款 → 通知） ==========
        {
            "id": "workflow_admin_refund_approve",
            "name": "退款审批流程",
            "description": "管理员退款审批流程，包括待审批列表查询、详情查看、审批决定和退款处理",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["退款审批流程", "审批退款", "退款审批", "处理退款", "喂，我要审批", "帮我审核退款", "审批怎么办", "退款处理"],
            "user_intents": ["审批退款", "退款审批", "处理退款"],
            "trigger_keywords": ["审批退款", "退款审批"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始退款审批"}},
                {
                    "id": "n_refund_list",
                    "name": "查询待审批退款",
                    "type": "api_call",
                    "description": "查询待审批的退款申请列表",
                    "config": {"api_id": "api_admin_refund_list", "api_endpoint": "/api/shop/admin/refunds", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "refunds", "type": "array", "description": "退款列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数量"}],
                    "ai_instructions": {"user_message": "正在查询待审批的退款申请", "action": "查询待审批退款"}
                },
                {
                    "id": "n_refund_detail",
                    "name": "查看退款详情",
                    "type": "api_call",
                    "description": "查看退款申请详细信息",
                    "config": {"api_id": "api_admin_refund_detail", "api_endpoint": "/api/shop/admin/refunds/{refund_id}", "method": "GET", "parameters": {"refund_id": "${refund_id}"}},
                    "outputs": [{"name": "refund", "type": "object", "description": "退款详情"}, {"name": "order", "type": "object", "description": "订单信息"}, {"name": "customer", "type": "object", "description": "客户信息"}],
                    "ai_instructions": {"user_message": "请选择要审批的退款申请", "action": "查看退款详情"}
                },
                {
                    "id": "n_approve",
                    "name": "审批退款",
                    "type": "api_call",
                    "description": "对退款申请进行审批",
                    "config": {"api_id": "api_admin_refund_approve", "api_endpoint": "/api/shop/admin/refunds/{refund_id}/approve", "method": "POST", "parameters": {"refund_id": "${refund_id}", "action": "${action}", "approved_amount": "${approved_amount}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "refund_id", "type": "string", "description": "退款单号"}],
                    "ai_instructions": {"user_message": "请选择审批动作并填写审批意见", "action": "审批退款"}
                },
                {
                    "id": "n_process",
                    "name": "处理退款",
                    "type": "api_call",
                    "description": "处理退款到账",
                    "config": {"api_id": "api_admin_refund_process", "api_endpoint": "/api/shop/admin/refunds/{refund_id}/process", "method": "POST", "parameters": {"refund_id": "${refund_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "refund_time", "type": "datetime", "description": "退款时间"}],
                    "ai_instructions": {"user_message": "正在处理退款", "action": "处理退款"}
                },
                {
                    "id": "n_notify",
                    "name": "审批结果通知",
                    "type": "notification",
                    "description": "发送审批结果通知",
                    "config": {"message_template": "退款审批完成！退款单号：${refund_id}，批准金额：${approved_amount}元，已通知买家。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退款审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_refund_list"},
                {"source": "n_refund_list", "target": "n_refund_detail"},
                {"source": "n_refund_detail", "target": "n_approve"},
                {"source": "n_approve", "target": "n_process"},
                {"source": "n_process", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：商品上架流程（4步：填写信息 → 创建商品 → 设置库存 → 通知） ==========
        {
            "id": "workflow_admin_product_create",
            "name": "商品上架流程",
            "description": "管理员商品上架流程，包括商品信息填写、创建和库存设置",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["商品上架流程", "上架商品", "新增商品", "添加商品", "喂，我要上架", "帮我上架", "上架怎么办", "创建商品"],
            "user_intents": ["上架商品", "新增商品", "添加商品"],
            "trigger_keywords": ["上架", "新增商品", "添加商品"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始商品上架"}},
                {
                    "id": "n_create",
                    "name": "创建商品",
                    "type": "api_call",
                    "description": "填写商品信息并创建",
                    "config": {"api_id": "api_admin_product_create", "api_endpoint": "/api/shop/admin/products", "method": "POST", "parameters": {"name": "${name}", "category": "${category}", "price": "${price}", "stock": "${stock}", "description": "${description}"}},
                    "outputs": [{"name": "sku_id", "type": "string", "description": "商品SKU"}],
                    "ai_instructions": {"user_message": "请填写商品信息", "action": "创建商品"}
                },
                {
                    "id": "n_notify",
                    "name": "上架成功通知",
                    "type": "notification",
                    "description": "发送商品上架成功通知",
                    "config": {"message_template": "商品上架成功！商品名称：${name}，SKU：${sku_id}，价格：${price}元，库存：${stock}件。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "商品上架成功", "action": "发送上架通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "商品上架完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_create"},
                {"source": "n_create", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：库存补货流程（5步：库存检查 → 查看低库存 → 选择商品 → 补货 → 通知） ==========
        {
            "id": "workflow_admin_stock_replenish",
            "name": "库存补货流程",
            "description": "管理员库存补货流程，包括库存检查、低库存商品查看和补货操作",
            "business_scenario": "ecommerce",
            "status": "active",
            "instruction_variants": ["库存补货流程", "补货", "库存补货", "补充库存", "喂，我要补货", "帮我补货", "补货怎么办", "进货"],
            "user_intents": ["补货", "库存补货", "补充库存"],
            "trigger_keywords": ["补货", "库存补货"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始库存补货"}},
                {
                    "id": "n_check",
                    "name": "库存检查",
                    "type": "api_call",
                    "description": "检查低库存商品",
                    "config": {"api_id": "api_admin_stock_check", "api_endpoint": "/api/shop/admin/stock/check", "method": "GET", "parameters": {"threshold": "${threshold}"}},
                    "outputs": [{"name": "low_stock_items", "type": "array", "description": "低库存商品"}, {"name": "out_of_stock_count", "type": "integer", "description": "缺货商品数"}],
                    "ai_instructions": {"user_message": "请设置库存预警阈值", "action": "库存检查"}
                },
                {
                    "id": "n_replenish",
                    "name": "补货",
                    "type": "api_call",
                    "description": "为商品补货",
                    "config": {"api_id": "api_admin_stock_replenish", "api_endpoint": "/api/shop/admin/stock/replenish", "method": "POST", "parameters": {"sku_id": "${sku_id}", "quantity": "${quantity}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "new_stock", "type": "integer", "description": "新库存"}],
                    "ai_instructions": {"user_message": "请选择商品并输入补货数量", "action": "补货"}
                },
                {
                    "id": "n_notify",
                    "name": "补货完成通知",
                    "type": "notification",
                    "description": "发送补货完成通知",
                    "config": {"message_template": "补货完成！商品SKU：${sku_id}，补货${quantity}件，当前库存：${new_stock}件。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "补货完成", "action": "发送补货通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "库存补货完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_check"},
                {"source": "n_check", "target": "n_replenish"},
                {"source": "n_replenish", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
