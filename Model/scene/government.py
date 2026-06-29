# government.py - 政务场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

GOVERNMENT_SCENE = {
    "domain": "government",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_user_info", "path": "/api/gov/user/info", "method": "GET", "desc": "查询个人信息",
         "instruction_variants": ["查询个人信息", "查看个人信息", "我的信息", "个人资料", "喂，帮我查查个人信息", "个人信息怎么查", "我的资料在哪", "个人信息呢"],
         "request": [{"name": "id_card", "type": "string", "label": "身份证号", "required": True}],
         "response": [{"name": "name", "type": "string", "desc": "姓名"}, {"name": "address", "type": "string", "desc": "户籍地址"}, {"name": "phone", "type": "string", "desc": "联系电话"}]},
        {"id": "api_id_card_apply", "workflow_only": True, "path": "/api/gov/id-card", "method": "POST", "desc": "身份证办理",
         "instruction_variants": ["身份证办理", "办身份证", "申请身份证", "我要办身份证", "喂，怎么办身份证", "帮我办身份证", "身份证怎么办", "能办身份证吗"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "address", "type": "string", "label": "户籍地址", "required": True}, {"name": "reason", "type": "string", "label": "办理原因", "required": True}, {"name": "photo", "type": "string", "label": "照片", "required": False}],
         "response": [{"name": "application_id", "type": "string", "desc": "申请单号"}, {"name": "estimated_days", "type": "integer", "desc": "预计办理天数"}]},
        {"id": "api_passport_apply", "workflow_only": True, "path": "/api/gov/passport", "method": "POST", "desc": "护照办理",
         "instruction_variants": ["护照办理", "办护照", "申请护照", "我要办护照", "喂，怎么办护照", "帮我办护照", "护照怎么办", "能办护照吗"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "phone", "type": "string", "label": "手机号", "required": True}, {"name": "destination", "type": "string", "label": "出行目的地", "required": False}],
         "response": [{"name": "application_id", "type": "string", "desc": "申请单号"}, {"name": "appointment_time", "type": "string", "desc": "预约时间"}]},
        {"id": "api_social_security_query", "path": "/api/gov/social-security", "method": "GET", "desc": "查询社保",
         "instruction_variants": ["查询社保", "查看社保", "我的社保", "社保记录", "喂，帮我查查社保", "社保怎么查", "社保缴了多少", "社保情况"],
         "request": [{"name": "id_card", "type": "string", "label": "身份证号", "required": True}],
         "response": [{"name": "records", "type": "array", "desc": "社保记录"}, {"name": "total_months", "type": "integer", "desc": "累计缴纳月数"}, {"name": "balance", "type": "float", "desc": "账户余额"}]},
        {"id": "api_tax_query", "path": "/api/gov/tax", "method": "GET", "desc": "查询纳税记录",
         "instruction_variants": ["查询纳税记录", "查看纳税", "我的纳税", "纳税记录", "喂，帮我查查纳税", "纳税怎么查", "交了多少税", "纳税情况"],
         "request": [{"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "year", "type": "string", "label": "年份", "required": False}],
         "response": [{"name": "records", "type": "array", "desc": "纳税记录"}, {"name": "total_tax", "type": "float", "desc": "累计纳税"}]},
        {"id": "api_license_types", "path": "/api/gov/license/types", "method": "GET", "desc": "查询证照类型",
         "instruction_variants": ["查询证照类型", "查看证照类型", "有哪些证照", "证照类型", "喂，有什么证照", "帮我看看证照", "证照都有啥", "能办什么证"],
         "request": [],
         "response": [{"name": "types", "type": "array", "desc": "证照类型列表"}]},
        {"id": "api_license_apply", "workflow_only": True, "path": "/api/gov/licenses", "method": "POST", "desc": "证照办理",
         "instruction_variants": ["证照办理", "办证照", "申请证照", "我要办证", "喂，怎么办证照", "帮我办证", "证照怎么办", "能办证吗"],
         "request": [{"name": "license_type", "type": "string", "label": "证照类型", "required": True}, {"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "materials", "type": "string", "label": "材料说明", "required": True}],
         "response": [{"name": "application_id", "type": "string", "desc": "申请单号"}, {"name": "required_materials", "type": "array", "desc": "所需材料"}]},
        {"id": "api_application_query", "path": "/api/gov/applications/{application_id}", "method": "GET", "desc": "查询申请进度",
         "instruction_variants": ["查询申请进度", "查看进度", "我的申请", "办到哪了", "喂，帮我查查进度", "进度怎么样", "申请办好了吗", "进度在哪看"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}],
         "response": [{"name": "status", "type": "string", "desc": "申请状态"}, {"name": "progress", "type": "array", "desc": "办理进度"}]},
        {"id": "api_appointment_slots", "path": "/api/gov/appointment/slots", "method": "GET", "desc": "查询预约时段",
         "instruction_variants": ["查询预约时段", "查看时段", "有哪些时段", "预约时间", "喂，什么时候能预约", "帮我看看时段", "时段怎么选", "有空位吗"],
         "request": [{"name": "service_type", "type": "string", "label": "服务类型", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}],
         "response": [{"name": "slots", "type": "array", "desc": "可选时段"}]},
        {"id": "api_appointment_book", "workflow_only": True, "path": "/api/gov/appointment", "method": "POST", "desc": "预约办理",
         "instruction_variants": ["预约办理", "我要预约", "预约", "预约服务", "喂，怎么预约", "帮我预约", "预约怎么办", "能预约吗"],
         "request": [{"name": "service_type", "type": "string", "label": "服务类型", "required": True}, {"name": "date", "type": "date", "label": "预约日期", "required": True}, {"name": "slot", "type": "string", "label": "预约时段", "required": True}, {"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}],
         "response": [{"name": "appointment_id", "type": "string", "desc": "预约号"}, {"name": "queue_no", "type": "string", "desc": "排队号"}]},
        {"id": "api_complaint_submit", "workflow_only": True, "path": "/api/gov/complaints", "method": "POST", "desc": "投诉建议",
         "instruction_variants": ["投诉建议", "我要投诉", "提交投诉", "投诉", "喂，怎么投诉", "帮我投诉", "投诉怎么办", "能投诉吗"],
         "request": [{"name": "type", "type": "string", "label": "类型", "required": True}, {"name": "content", "type": "string", "label": "内容", "required": True}, {"name": "contact_phone", "type": "string", "label": "联系电话", "required": True}, {"name": "attachments", "type": "string", "label": "附件", "required": False}],
         "response": [{"name": "complaint_id", "type": "string", "desc": "投诉单号"}]},
        {"id": "api_material_upload", "workflow_only": True, "path": "/api/gov/materials/upload", "method": "POST", "desc": "上传材料",
         "instruction_variants": ["上传材料", "提交材料", "上传文件", "交材料", "喂，怎么上传材料", "帮我上传", "材料怎么传", "能上传吗"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}, {"name": "material_type", "type": "string", "label": "材料类型", "required": True}, {"name": "file", "type": "file", "label": "文件", "required": True}],
         "response": [{"name": "material_id", "type": "string", "desc": "材料ID"}, {"name": "upload_success", "type": "boolean", "desc": "上传是否成功"}]},
        {"id": "api_fee_query", "path": "/api/gov/fees/{application_id}", "method": "GET", "desc": "查询费用",
         "instruction_variants": ["查询费用", "查看费用", "要交多少钱", "费用多少", "喂，帮我查查费用", "费用怎么查", "需要交多少", "费用是多少"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}],
         "response": [{"name": "fee", "type": "float", "desc": "应缴费用"}, {"name": "fee_items", "type": "array", "desc": "费用明细"}]},
        {"id": "api_fee_pay", "workflow_only": True, "path": "/api/gov/fees/{application_id}/pay", "method": "POST", "desc": "缴费",
         "instruction_variants": ["缴费", "支付费用", "付款", "交钱", "喂，怎么缴费", "帮我缴费", "缴费怎么办", "能付款吗"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "receipt_no", "type": "string", "desc": "收据号"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_application_list", "workflow_only": True, "path": "/api/gov/admin/applications", "method": "GET", "desc": "查询申请列表（管理员）",
         "instruction_variants": ["查询申请列表", "查看申请", "申请列表", "待审核申请", "喂，有哪些申请", "帮我看看申请", "申请在哪", "要审核的申请"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "type", "type": "string", "label": "类型", "required": False}, {"name": "date", "type": "date", "label": "日期", "required": False}],
         "response": [{"name": "applications", "type": "array", "desc": "申请列表"}, {"name": "pending_count", "type": "integer", "desc": "待审核数"}]},
        {"id": "api_admin_application_detail", "workflow_only": True, "path": "/api/gov/admin/applications/{application_id}", "method": "GET", "desc": "查询申请详情（管理员）",
         "instruction_variants": ["查询申请详情", "查看详情", "申请详情", "详细信息", "喂，帮我看看详情", "详情怎么查", "申请信息", "详情在哪"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}],
         "response": [{"name": "application", "type": "object", "desc": "申请详情"}, {"name": "applicant", "type": "object", "desc": "申请人信息"}, {"name": "materials", "type": "array", "desc": "提交材料"}]},
        {"id": "api_admin_material_review", "workflow_only": True, "path": "/api/gov/admin/materials/{material_id}/review", "method": "POST", "desc": "审核材料",
         "instruction_variants": ["审核材料", "材料审核", "审查材料", "检查材料", "喂，怎么审核材料", "帮我审材料", "材料怎么审", "能审核吗"],
         "request": [{"name": "material_id", "type": "string", "label": "材料ID", "required": True}, {"name": "result", "type": "string", "label": "审核结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_application_approve", "workflow_only": True, "path": "/api/gov/admin/applications/{application_id}/approve", "method": "POST", "desc": "审批申请",
         "instruction_variants": ["审批申请", "申请审批", "批准申请", "审核申请", "喂，怎么审批", "帮我审批", "申请怎么审", "能批准吗"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}, {"name": "result", "type": "string", "label": "审批结果", "required": True}, {"name": "remark", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "next_step", "type": "string", "desc": "下一步操作"}]},
        {"id": "api_admin_license_issue", "workflow_only": True, "path": "/api/gov/admin/licenses/issue", "method": "POST", "desc": "发放证照",
         "instruction_variants": ["发放证照", "证照发放", "发证", "颁发证照", "喂，怎么发证", "帮我发证照", "证照怎么发", "能发证吗"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}, {"name": "license_no", "type": "string", "label": "证照编号", "required": True}, {"name": "valid_from", "type": "date", "label": "生效日期", "required": True}, {"name": "valid_to", "type": "date", "label": "失效日期", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "license_id", "type": "string", "desc": "证照ID"}]},
        {"id": "api_admin_complaint_list", "workflow_only": True, "path": "/api/gov/admin/complaints", "method": "GET", "desc": "查询投诉列表（管理员）",
         "instruction_variants": ["查询投诉列表", "查看投诉", "投诉列表", "待处理投诉", "喂，有哪些投诉", "帮我看看投诉", "投诉在哪", "要处理的投诉"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "complaints", "type": "array", "desc": "投诉列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_complaint_handle", "workflow_only": True, "path": "/api/gov/admin/complaints/{complaint_id}/handle", "method": "POST", "desc": "处理投诉",
         "instruction_variants": ["处理投诉", "投诉处理", "回复投诉", "处理", "喂，怎么处理投诉", "帮我处理", "投诉怎么办", "能处理吗"],
         "request": [{"name": "complaint_id", "type": "string", "label": "投诉单号", "required": True}, {"name": "result", "type": "string", "label": "处理结果", "required": True}, {"name": "reply", "type": "string", "label": "回复内容", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_appointment_list", "workflow_only": True, "path": "/api/gov/admin/appointments", "method": "GET", "desc": "查询预约列表（管理员）",
         "instruction_variants": ["查询预约列表", "查看预约", "预约列表", "今天的预约", "喂，有哪些预约", "帮我看看预约", "预约在哪", "今天有多少预约"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "appointments", "type": "array", "desc": "预约列表"}, {"name": "today_count", "type": "integer", "desc": "今日预约数"}]},
        {"id": "api_admin_checkin", "workflow_only": True, "path": "/api/gov/admin/appointments/{appointment_id}/checkin", "method": "POST", "desc": "签到确认",
         "instruction_variants": ["签到确认", "确认签到", "签到", "办理签到", "喂，怎么签到", "帮我签到", "签到怎么办", "能签到吗"],
         "request": [{"name": "appointment_id", "type": "string", "label": "预约号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "window_no", "type": "string", "desc": "窗口号"}]},
        {"id": "api_admin_service_complete", "workflow_only": True, "path": "/api/gov/admin/services/{appointment_id}/complete", "method": "POST", "desc": "完成服务",
         "instruction_variants": ["完成服务", "服务完成", "办理完成", "结束服务", "喂，怎么完成服务", "帮我完成", "服务怎么结束", "能完成吗"],
         "request": [{"name": "appointment_id", "type": "string", "label": "预约号", "required": True}, {"name": "result", "type": "string", "label": "办理结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},

        # ========== 管理员统计 API ==========
        {"id": "api_admin_service_stats", "path": "/api/gov/admin/stats/service", "method": "GET", "desc": "查询服务统计", "name": "服务统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询服务统计", "服务统计", "服务数据", "统计情况", "喂，帮我看看统计", "服务怎么样", "统计数据", "服务报表"],
         "request": [],
         "response": [{"name": "today_count", "type": "integer", "desc": "今日办理"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_type_analysis", "path": "/api/gov/admin/stats/type", "method": "GET", "desc": "查询业务分析", "name": "业务分析", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询业务分析", "业务分析", "业务统计", "业务情况", "喂，帮我看看业务", "业务怎么样", "业务数据", "业务报表"],
         "request": [],
         "response": [{"name": "types", "type": "array", "desc": "业务类型"}, {"name": "counts", "type": "array", "desc": "办理量"}]},
        {"id": "api_admin_satisfaction_stats", "path": "/api/gov/admin/stats/satisfaction", "method": "GET", "desc": "查询满意度统计", "name": "满意度统计", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询满意度统计", "满意度统计", "满意度分析", "满意度情况", "喂，帮我看看满意度", "满意度怎么样", "满意度数据", "满意度报表"],
         "request": [],
         "response": [{"name": "ratings", "type": "array", "desc": "评分分布"}, {"name": "avg_score", "type": "float", "desc": "平均分"}]},
    ],

    "workflows": [
        # ========== 用户：身份证办理流程（7步：查询个人信息 → 选择办理原因 → 预约时段 → 提交申请 → 上传材料 → 缴费 → 通知） ==========
        {
            "id": "workflow_id_card_full",
            "name": "身份证办理流程",
            "description": "完整的身份证办理流程，包括预约、申请、缴费",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["办身份证", "身份证办理", "补办身份证", "换身份证"],
            "trigger_keywords": ["办身份证", "身份证办理", "补办身份证"],
            "instruction_variants": ["办身份证", "身份证办理", "补办身份证", "换身份证", "喂，怎么办身份证", "帮我办身份证", "身份证怎么办", "能办身份证吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始身份证办理"}},
                {
                    "id": "n_user_info",
                    "name": "查询个人信息",
                    "type": "api_call",
                    "description": "查询申请人基本信息",
                    "config": {"api_id": "api_user_info", "api_endpoint": "/api/gov/user/info", "method": "GET", "parameters": {"id_card": "${id_card}"}},
                    "outputs": [{"name": "name", "type": "string", "description": "姓名"}, {"name": "address", "type": "string", "description": "户籍地址"}],
                    "ai_instructions": {"user_message": "请输入身份证号查询个人信息", "action": "查询个人信息"}
                },
                {
                    "id": "n_slots",
                    "name": "查询预约时段",
                    "type": "api_call",
                    "description": "查询可预约的时段",
                    "config": {"api_id": "api_appointment_slots", "api_endpoint": "/api/gov/appointment/slots", "method": "GET", "parameters": {"service_type": "身份证办理", "date": "${date}"}},
                    "outputs": [{"name": "slots", "type": "array", "description": "可选时段"}],
                    "ai_instructions": {"user_message": "请选择预约日期", "action": "查询预约时段"}
                },
                {
                    "id": "n_appointment",
                    "name": "预约办理",
                    "type": "api_call",
                    "description": "预约办理时间",
                    "config": {"api_id": "api_appointment_book", "api_endpoint": "/api/gov/appointment", "method": "POST", "parameters": {"service_type": "身份证办理", "date": "${date}", "slot": "${slot}", "name": "${name}", "id_card": "${id_card}"}},
                    "outputs": [{"name": "appointment_id", "type": "string", "description": "预约号"}, {"name": "queue_no", "type": "string", "description": "排队号"}],
                    "ai_instructions": {"user_message": "请选择预约时段", "action": "预约办理"}
                },
                {
                    "id": "n_apply",
                    "name": "提交申请",
                    "type": "api_call",
                    "description": "提交身份证办理申请",
                    "config": {"api_id": "api_id_card_apply", "api_endpoint": "/api/gov/id-card", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "address": "${address}", "reason": "${reason}", "photo": "${photo}"}},
                    "outputs": [{"name": "application_id", "type": "string", "description": "申请单号"}, {"name": "estimated_days", "type": "integer", "description": "预计办理天数"}],
                    "ai_instructions": {"user_message": "请选择办理原因并上传照片", "action": "提交申请"}
                },
                {
                    "id": "n_fee_query",
                    "name": "查询费用",
                    "type": "api_call",
                    "description": "查询应缴费用",
                    "config": {"api_id": "api_fee_query", "api_endpoint": "/api/gov/fees/{application_id}", "method": "GET", "parameters": {"application_id": "${application_id}"}},
                    "outputs": [{"name": "fee", "type": "float", "description": "应缴费用"}],
                    "ai_instructions": {"user_message": "查询费用", "action": "查询费用"}
                },
                {
                    "id": "n_pay",
                    "name": "缴费",
                    "type": "api_call",
                    "description": "缴纳办理费用",
                    "config": {"api_id": "api_fee_pay", "api_endpoint": "/api/gov/fees/{application_id}/pay", "method": "POST", "parameters": {"application_id": "${application_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "receipt_no", "type": "string", "description": "收据号"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "缴费"}
                },
                {
                    "id": "n_notify",
                    "name": "办理通知",
                    "type": "notification",
                    "description": "发送办理成功通知",
                    "config": {"message_template": "身份证办理申请成功！申请单号：${application_id}，预约号：${queue_no}，预计${estimated_days}个工作日办结。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "申请成功", "action": "发送办理通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "身份证办理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_user_info"},
                {"source": "n_user_info", "target": "n_slots"},
                {"source": "n_slots", "target": "n_appointment"},
                {"source": "n_appointment", "target": "n_apply"},
                {"source": "n_apply", "target": "n_fee_query"},
                {"source": "n_fee_query", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：护照办理流程（7步：查询个人信息 → 预约时段 → 提交申请 → 上传材料 → 缴费 → 查询进度 → 通知） ==========
        {
            "id": "workflow_passport_full",
            "name": "护照办理流程",
            "description": "完整的护照办理流程",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["办护照", "护照办理", "申请护照", "换护照"],
            "trigger_keywords": ["办护照", "护照办理", "申请护照"],
            "instruction_variants": ["办护照", "护照办理", "申请护照", "换护照", "喂，怎么办护照", "帮我办护照", "护照怎么办", "能办护照吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始护照办理"}},
                {
                    "id": "n_user_info",
                    "name": "查询个人信息",
                    "type": "api_call",
                    "description": "查询申请人基本信息",
                    "config": {"api_id": "api_user_info", "api_endpoint": "/api/gov/user/info", "method": "GET", "parameters": {"id_card": "${id_card}"}},
                    "outputs": [{"name": "name", "type": "string", "description": "姓名"}, {"name": "address", "type": "string", "description": "户籍地址"}],
                    "ai_instructions": {"user_message": "请输入身份证号", "action": "查询个人信息"}
                },
                {
                    "id": "n_slots",
                    "name": "查询预约时段",
                    "type": "api_call",
                    "description": "查询可预约的时段",
                    "config": {"api_id": "api_appointment_slots", "api_endpoint": "/api/gov/appointment/slots", "method": "GET", "parameters": {"service_type": "护照办理", "date": "${date}"}},
                    "outputs": [{"name": "slots", "type": "array", "description": "可选时段"}],
                    "ai_instructions": {"user_message": "请选择预约日期", "action": "查询预约时段"}
                },
                {
                    "id": "n_appointment",
                    "name": "预约办理",
                    "type": "api_call",
                    "description": "预约办理时间",
                    "config": {"api_id": "api_appointment_book", "api_endpoint": "/api/gov/appointment", "method": "POST", "parameters": {"service_type": "护照办理", "date": "${date}", "slot": "${slot}", "name": "${name}", "id_card": "${id_card}"}},
                    "outputs": [{"name": "appointment_id", "type": "string", "description": "预约号"}],
                    "ai_instructions": {"user_message": "请选择预约时段", "action": "预约办理"}
                },
                {
                    "id": "n_apply",
                    "name": "提交申请",
                    "type": "api_call",
                    "description": "提交护照办理申请",
                    "config": {"api_id": "api_passport_apply", "api_endpoint": "/api/gov/passport", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "phone": "${phone}", "destination": "${destination}"}},
                    "outputs": [{"name": "application_id", "type": "string", "description": "申请单号"}],
                    "ai_instructions": {"user_message": "请填写联系电话和出行目的地", "action": "提交申请"}
                },
                {
                    "id": "n_upload",
                    "name": "上传材料",
                    "type": "api_call",
                    "description": "上传所需材料",
                    "config": {"api_id": "api_material_upload", "api_endpoint": "/api/gov/materials/upload", "method": "POST", "parameters": {"application_id": "${application_id}", "material_type": "照片", "file": "${file}"}},
                    "outputs": [{"name": "material_id", "type": "string", "description": "材料ID"}],
                    "ai_instructions": {"user_message": "请上传证件照", "action": "上传材料"}
                },
                {
                    "id": "n_pay",
                    "name": "缴费",
                    "type": "api_call",
                    "description": "缴纳办理费用",
                    "config": {"api_id": "api_fee_pay", "api_endpoint": "/api/gov/fees/{application_id}/pay", "method": "POST", "parameters": {"application_id": "${application_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "receipt_no", "type": "string", "description": "收据号"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "缴费"}
                },
                {
                    "id": "n_notify",
                    "name": "办理通知",
                    "type": "notification",
                    "description": "发送办理成功通知",
                    "config": {"message_template": "护照办理申请成功！申请单号：${application_id}，收据号：${receipt_no}，请按预约时间到场办理。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "申请成功", "action": "发送办理通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "护照办理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_user_info"},
                {"source": "n_user_info", "target": "n_slots"},
                {"source": "n_slots", "target": "n_appointment"},
                {"source": "n_appointment", "target": "n_apply"},
                {"source": "n_apply", "target": "n_upload"},
                {"source": "n_upload", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：社保证明办理流程（6步：查询社保 → 查询纳税 → 选择证照类型 → 提交申请 → 缴费 → 通知） ==========
        {
            "id": "workflow_social_license",
            "name": "社保证明办理流程",
            "description": "查询社保后办理相关证明",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["社保证明", "社保办证", "查社保办证"],
            "trigger_keywords": ["社保证明", "社保办证", "查社保办证"],
            "instruction_variants": ["社保证明", "社保办证", "查社保办证", "我要社保证明", "喂，怎么办社保证明", "帮我办证明", "社保证明怎么办", "能办证明吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始社保证明办理"}},
                {
                    "id": "n_query_social",
                    "name": "查询社保",
                    "type": "api_call",
                    "description": "查询社保缴纳记录",
                    "config": {"api_id": "api_social_security_query", "api_endpoint": "/api/gov/social-security", "method": "GET", "parameters": {"id_card": "${id_card}"}},
                    "outputs": [{"name": "records", "type": "array", "description": "社保记录"}, {"name": "total_months", "type": "integer", "description": "累计缴纳月数"}],
                    "ai_instructions": {"user_message": "请输入身份证号查询社保", "action": "查询社保"}
                },
                {
                    "id": "n_license_types",
                    "name": "查询证照类型",
                    "type": "api_call",
                    "description": "查询可办理的证照类型",
                    "config": {"api_id": "api_license_types", "api_endpoint": "/api/gov/license/types", "method": "GET", "parameters": {}},
                    "outputs": [{"name": "types", "type": "array", "description": "证照类型列表"}],
                    "ai_instructions": {"user_message": "查询可办理证照", "action": "查询证照类型"}
                },
                {
                    "id": "n_apply",
                    "name": "提交申请",
                    "type": "api_call",
                    "description": "提交证明申请",
                    "config": {"api_id": "api_license_apply", "api_endpoint": "/api/gov/licenses", "method": "POST", "parameters": {"license_type": "${license_type}", "name": "${name}", "id_card": "${id_card}", "materials": "${materials}"}},
                    "outputs": [{"name": "application_id", "type": "string", "description": "申请单号"}],
                    "ai_instructions": {"user_message": "请选择证照类型并填写信息", "action": "提交申请"}
                },
                {
                    "id": "n_pay",
                    "name": "缴费",
                    "type": "api_call",
                    "description": "缴纳办理费用",
                    "config": {"api_id": "api_fee_pay", "api_endpoint": "/api/gov/fees/{application_id}/pay", "method": "POST", "parameters": {"application_id": "${application_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "缴费"}
                },
                {
                    "id": "n_notify",
                    "name": "办理通知",
                    "type": "notification",
                    "description": "发送办理成功通知",
                    "config": {"message_template": "社保证明申请成功！申请单号：${application_id}，累计缴纳${total_months}个月。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "申请成功", "action": "发送办理通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "社保证明办理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query_social"},
                {"source": "n_query_social", "target": "n_license_types"},
                {"source": "n_license_types", "target": "n_apply"},
                {"source": "n_apply", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：投诉建议流程（4步：填写投诉 → 上传附件 → 提交 → 通知） ==========
        {
            "id": "workflow_complaint",
            "name": "投诉建议流程",
            "description": "提交投诉建议",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["投诉", "建议", "反馈", "举报"],
            "trigger_keywords": ["投诉", "建议", "反馈"],
            "instruction_variants": ["投诉", "建议", "反馈", "举报", "喂，我要投诉", "帮我投诉", "投诉怎么办", "能投诉吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始投诉"}},
                {
                    "id": "n_submit",
                    "name": "提交投诉",
                    "type": "api_call",
                    "description": "填写并提交投诉",
                    "config": {"api_id": "api_complaint_submit", "api_endpoint": "/api/gov/complaints", "method": "POST", "parameters": {"type": "${type}", "content": "${content}", "contact_phone": "${contact_phone}", "attachments": "${attachments}"}},
                    "outputs": [{"name": "complaint_id", "type": "string", "description": "投诉单号"}],
                    "ai_instructions": {"user_message": "请选择投诉类型并填写内容", "action": "提交投诉"}
                },
                {
                    "id": "n_notify",
                    "name": "投诉通知",
                    "type": "notification",
                    "description": "发送投诉提交通知",
                    "config": {"message_template": "投诉已提交！投诉单号：${complaint_id}，我们将在3个工作日内处理。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "投诉已提交", "action": "发送投诉通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "投诉完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_submit"},
                {"source": "n_submit", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：申请审批流程（6步：查询待审申请 → 查看详情 → 审核材料 → 审批申请 → 发放证照 → 通知） ==========
        {
            "id": "workflow_admin_approve",
            "name": "管理员申请审批流程",
            "description": "审批用户提交的各类申请",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["审批申请", "审核申请", "处理申请"],
            "trigger_keywords": ["审批申请", "审核申请", "处理申请"],
            "instruction_variants": ["审批申请", "审核申请", "处理申请", "申请审批", "喂，怎么审批", "帮我审批", "审批怎么办", "能审批吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审批"}},
                {
                    "id": "n_list",
                    "name": "查询待审申请",
                    "type": "api_call",
                    "description": "查询待审批的申请列表",
                    "config": {"api_id": "api_admin_application_list", "api_endpoint": "/api/gov/admin/applications", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "applications", "type": "array", "description": "申请列表"}, {"name": "pending_count", "type": "integer", "description": "待审核数"}],
                    "ai_instructions": {"user_message": "查询待审批申请", "action": "查询待审申请"}
                },
                {
                    "id": "n_detail",
                    "name": "查看申请详情",
                    "type": "api_call",
                    "description": "查看申请详细信息",
                    "config": {"api_id": "api_admin_application_detail", "api_endpoint": "/api/gov/admin/applications/{application_id}", "method": "GET", "parameters": {"application_id": "${application_id}"}},
                    "outputs": [{"name": "application", "type": "object", "description": "申请详情"}, {"name": "materials", "type": "array", "description": "提交材料"}],
                    "ai_instructions": {"user_message": "请选择要审批的申请", "action": "查看申请详情"}
                },
                {
                    "id": "n_review",
                    "name": "审核材料",
                    "type": "api_call",
                    "description": "审核提交的材料",
                    "config": {"api_id": "api_admin_material_review", "api_endpoint": "/api/gov/admin/materials/{material_id}/review", "method": "POST", "parameters": {"material_id": "${material_id}", "result": "${review_result}", "remark": "${review_remark}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请审核材料并填写审核意见", "action": "审核材料"}
                },
                {
                    "id": "n_approve",
                    "name": "审批申请",
                    "type": "api_call",
                    "description": "审批申请",
                    "config": {"api_id": "api_admin_application_approve", "api_endpoint": "/api/gov/admin/applications/{application_id}/approve", "method": "POST", "parameters": {"application_id": "${application_id}", "result": "${approve_result}", "remark": "${approve_remark}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "next_step", "type": "string", "description": "下一步操作"}],
                    "ai_instructions": {"user_message": "请选择审批结果", "action": "审批申请"}
                },
                {
                    "id": "n_notify",
                    "name": "审批通知",
                    "type": "notification",
                    "description": "发送审批结果通知",
                    "config": {"message_template": "申请${application_id}审批完成，结果：${approve_result}，下一步：${next_step}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_detail"},
                {"source": "n_detail", "target": "n_review"},
                {"source": "n_review", "target": "n_approve"},
                {"source": "n_approve", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：证照发放流程（5步：查询已审批申请 → 查看详情 → 生成证照 → 发放证照 → 通知） ==========
        {
            "id": "workflow_admin_license_issue",
            "name": "管理员证照发放流程",
            "description": "为已审批通过的申请发放证照",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["发放证照", "制证", "出证"],
            "trigger_keywords": ["发放证照", "制证", "出证"],
            "instruction_variants": ["发放证照", "制证", "出证", "颁发证照", "喂，怎么发证", "帮我发证", "证照怎么发", "能发证吗"],
            "trigger_keywords": ["发放证照", "制证", "出证"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始发放证照"}},
                {
                    "id": "n_list",
                    "name": "查询待发放申请",
                    "type": "api_call",
                    "description": "查询已审批待发放的申请",
                    "config": {"api_id": "api_admin_application_list", "api_endpoint": "/api/gov/admin/applications", "method": "GET", "parameters": {"status": "approved"}},
                    "outputs": [{"name": "applications", "type": "array", "description": "申请列表"}],
                    "ai_instructions": {"user_message": "查询待发放申请", "action": "查询待发放申请"}
                },
                {
                    "id": "n_detail",
                    "name": "查看申请详情",
                    "type": "api_call",
                    "description": "查看申请详细信息",
                    "config": {"api_id": "api_admin_application_detail", "api_endpoint": "/api/gov/admin/applications/{application_id}", "method": "GET", "parameters": {"application_id": "${application_id}"}},
                    "outputs": [{"name": "application", "type": "object", "description": "申请详情"}],
                    "ai_instructions": {"user_message": "请选择要发放的申请", "action": "查看申请详情"}
                },
                {
                    "id": "n_issue",
                    "name": "发放证照",
                    "type": "api_call",
                    "description": "发放证照",
                    "config": {"api_id": "api_admin_license_issue", "api_endpoint": "/api/gov/admin/licenses/issue", "method": "POST", "parameters": {"application_id": "${application_id}", "license_no": "${license_no}", "valid_from": "${valid_from}", "valid_to": "${valid_to}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "license_id", "type": "string", "description": "证照ID"}],
                    "ai_instructions": {"user_message": "请填写证照信息", "action": "发放证照"}
                },
                {
                    "id": "n_notify",
                    "name": "发放通知",
                    "type": "notification",
                    "description": "发送证照发放通知",
                    "config": {"message_template": "证照发放成功！申请${application_id}，证照编号：${license_no}，有效期：${valid_from}至${valid_to}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "发放成功", "action": "发送发放通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "证照发放完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_detail"},
                {"source": "n_detail", "target": "n_issue"},
                {"source": "n_issue", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：窗口服务流程（5步：查询今日预约 → 签到确认 → 办理业务 → 完成服务 → 通知） ==========
        {
            "id": "workflow_admin_window_service",
            "name": "管理员窗口服务流程",
            "description": "窗口办理业务流程",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["窗口服务", "办理业务", "叫号服务"],
            "trigger_keywords": ["窗口服务", "办理业务", "叫号服务"],
            "instruction_variants": ["窗口服务", "办理业务", "叫号服务", "服务办理", "喂，怎么办理", "帮我办理", "办理怎么弄", "能办理吗"],
            "trigger_keywords": ["窗口服务", "办理业务", "叫号服务"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始窗口服务"}},
                {
                    "id": "n_list",
                    "name": "查询今日预约",
                    "type": "api_call",
                    "description": "查询今日预约列表",
                    "config": {"api_id": "api_admin_appointment_list", "api_endpoint": "/api/gov/admin/appointments", "method": "GET", "parameters": {"date": "${today}", "status": "pending"}},
                    "outputs": [{"name": "appointments", "type": "array", "description": "预约列表"}, {"name": "today_count", "type": "integer", "description": "今日预约数"}],
                    "ai_instructions": {"user_message": "查询今日预约", "action": "查询今日预约"}
                },
                {
                    "id": "n_checkin",
                    "name": "签到确认",
                    "type": "api_call",
                    "description": "确认用户签到",
                    "config": {"api_id": "api_admin_checkin", "api_endpoint": "/api/gov/admin/appointments/{appointment_id}/checkin", "method": "POST", "parameters": {"appointment_id": "${appointment_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "window_no", "type": "string", "description": "窗口号"}],
                    "ai_instructions": {"user_message": "请选择签到的预约", "action": "签到确认"}
                },
                {
                    "id": "n_complete",
                    "name": "完成服务",
                    "type": "api_call",
                    "description": "完成窗口服务",
                    "config": {"api_id": "api_admin_service_complete", "api_endpoint": "/api/gov/admin/services/{appointment_id}/complete", "method": "POST", "parameters": {"appointment_id": "${appointment_id}", "result": "${service_result}", "remark": "${remark}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请填写办理结果", "action": "完成服务"}
                },
                {
                    "id": "n_notify",
                    "name": "服务通知",
                    "type": "notification",
                    "description": "发送服务完成通知",
                    "config": {"message_template": "窗口服务完成！预约号${appointment_id}，窗口${window_no}，办理结果：${service_result}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "服务完成", "action": "发送服务通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "窗口服务完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_checkin"},
                {"source": "n_checkin", "target": "n_complete"},
                {"source": "n_complete", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：投诉处理流程（5步：查询投诉列表 → 查看详情 → 处理投诉 → 回复用户 → 通知） ==========
        {
            "id": "workflow_admin_complaint_handle",
            "name": "管理员投诉处理流程",
            "description": "处理用户投诉建议",
            "business_scenario": "government",
            "status": "active",
            "user_intents": ["处理投诉", "投诉处理", "回复投诉"],
            "trigger_keywords": ["处理投诉", "投诉处理", "回复投诉"],
            "instruction_variants": ["处理投诉", "投诉处理", "回复投诉", "处理", "喂，怎么处理投诉", "帮我处理", "投诉怎么办", "能处理吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理投诉"}},
                {
                    "id": "n_list",
                    "name": "查询投诉列表",
                    "type": "api_call",
                    "description": "查询待处理的投诉",
                    "config": {"api_id": "api_admin_complaint_list", "api_endpoint": "/api/gov/admin/complaints", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "complaints", "type": "array", "description": "投诉列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数"}],
                    "ai_instructions": {"user_message": "查询待处理投诉", "action": "查询投诉列表"}
                },
                {
                    "id": "n_handle",
                    "name": "处理投诉",
                    "type": "api_call",
                    "description": "处理投诉并回复",
                    "config": {"api_id": "api_admin_complaint_handle", "api_endpoint": "/api/gov/admin/complaints/{complaint_id}/handle", "method": "POST", "parameters": {"complaint_id": "${complaint_id}", "result": "${handle_result}", "reply": "${reply}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择投诉并填写处理结果", "action": "处理投诉"}
                },
                {
                    "id": "n_notify",
                    "name": "处理通知",
                    "type": "notification",
                    "description": "发送处理结果通知",
                    "config": {"message_template": "投诉处理完成！投诉单号${complaint_id}，处理结果：${handle_result}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "处理完成", "action": "发送处理通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "投诉处理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_handle"},
                {"source": "n_handle", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
