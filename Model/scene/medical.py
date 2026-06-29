# medical.py - 医疗场景定义 V5
# 新增：为每个API和Workflow添加多个指令变体，增加训练数据多样性

MEDICAL_SCENE = {
    "domain": "medical",
    "apis": [
        # ========== 患者端 API ==========
        {"id": "api_hospital_list", "path": "/api/v1/hospitals", "method": "GET", "desc": "查询医院列表",
         "instruction_variants": ["查询医院列表", "查看医院", "我想找医院", "附近有哪些医院", "喂，哪里有医院", "帮我查查医院", "医院在哪", "有什么医院"],
         "request": [{"name": "city", "type": "string", "label": "城市", "required": False}],
         "response": [{"name": "hospitals", "type": "array", "desc": "医院列表"}]},
        {"id": "api_dept_list", "path": "/api/v1/departments", "method": "GET", "desc": "查询科室列表",
         "instruction_variants": ["查询科室列表", "查看科室", "有哪些科室", "科室有什么", "喂，这医院有啥科室", "帮我看看科室", "都有什么科", "科室怎么选"],
         "request": [{"name": "hospital_id", "type": "string", "label": "医院ID", "required": False}],
         "response": [{"name": "departments", "type": "array", "desc": "科室列表"}, {"name": "dept_id", "type": "string", "desc": "科室ID"}, {"name": "dept_name", "type": "string", "desc": "科室名称"}]},
        {"id": "api_doc_list", "path": "/api/v1/doctors", "method": "GET", "desc": "查询医生排班",
         "instruction_variants": ["查询医生排班", "查看医生", "有哪些医生", "医生排班表", "喂，今天哪个医生上班", "帮我看看医生", "哪个医生在", "医生怎么选啊"],
         "request": [{"name": "dept_id", "type": "string", "label": "科室ID", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}],
         "response": [{"name": "doctors", "type": "array", "desc": "医生列表"}, {"name": "doctor_id", "type": "string", "desc": "医生ID"}, {"name": "doctor_name", "type": "string", "desc": "医生姓名"}]},
        {"id": "api_doc_detail", "path": "/api/v1/doctors/{doctor_id}", "method": "GET", "desc": "查询医生详情",
         "instruction_variants": ["查询医生详情", "医生信息", "这个医生怎么样", "医生介绍", "喂，这医生靠谱吗", "帮我看看这医生", "医生擅长什么", "这医生行不行啊"],
         "request": [{"name": "doctor_id", "type": "string", "label": "医生ID", "required": True}],
         "response": [{"name": "doctor", "type": "object", "desc": "医生详情"}, {"name": "specialty", "type": "string", "desc": "专长"}, {"name": "available_slots", "type": "array", "desc": "可预约时段"}]},
        {"id": "api_patient_verify", "workflow_only": True, "path": "/api/v1/patients/verify", "method": "POST", "desc": "患者身份验证",
         "instruction_variants": ["患者身份验证", "验证身份", "身份认证", "确认患者信息", "喂，怎么验证身份", "需要填什么信息", "身份怎么确认", "验证一下"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "phone", "type": "string", "label": "手机号", "required": True}],
         "response": [{"name": "patient_id", "type": "string", "desc": "患者ID"}, {"name": "patient_name", "type": "string", "desc": "患者姓名"}, {"name": "medical_card", "type": "string", "desc": "就诊卡号"}]},
        {"id": "api_appt_create", "workflow_only": True, "path": "/api/v1/appointments", "method": "POST", "desc": "提交挂号订单",
         "instruction_variants": ["提交挂号订单", "创建挂号", "我要挂号", "帮我挂号", "喂，我想挂个号", "挂号怎么弄", "给我挂个号", "挂号行不行"],
         "request": [{"name": "doctor_id", "type": "string", "label": "医生ID", "required": True}, {"name": "patient_id", "type": "string", "label": "患者ID", "required": True}, {"name": "time_slot", "type": "time", "label": "就诊时段", "required": True}, {"name": "symptom", "type": "string", "label": "症状描述", "required": False}],
         "response": [{"name": "order_id", "type": "string", "desc": "挂号单号"}, {"name": "queue_number", "type": "integer", "desc": "排队号"}, {"name": "fee", "type": "float", "desc": "挂号费"}]},
        {"id": "api_appt_pay", "workflow_only": True, "path": "/api/v1/appointments/{order_id}/pay", "method": "POST", "desc": "挂号支付",
         "instruction_variants": ["挂号支付", "支付挂号费", "缴费", "付款", "喂，怎么付钱", "我要付款", "支付一下", "付钱怎么弄"],
         "request": [{"name": "order_id", "type": "string", "label": "挂号单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "payment_id", "type": "string", "desc": "支付流水号"}]},
        {"id": "api_appt_query", "path": "/api/v1/appointments/{order_id}", "method": "GET", "desc": "查询挂号订单",
         "instruction_variants": ["查询挂号订单", "查看挂号", "我的挂号", "挂号详情", "喂，我挂的号呢", "帮我查查挂号", "挂号信息在哪", "我挂号了吗"],
         "request": [{"name": "order_id", "type": "string", "label": "挂号单号", "required": True}],
         "response": [{"name": "appointment", "type": "object", "desc": "挂号详情"}, {"name": "status", "type": "string", "desc": "订单状态"}, {"name": "doctor_name", "type": "string", "desc": "医生姓名"}]},
        {"id": "api_appt_list", "path": "/api/v1/appointments", "method": "GET", "desc": "查询挂号列表",
         "instruction_variants": ["查询挂号列表", "我的挂号记录", "挂号历史", "所有挂号", "喂，我挂过哪些号", "帮我看看挂号记录", "之前挂的号", "挂号记录在哪"],
         "request": [{"name": "patient_id", "type": "string", "label": "患者ID", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "appointments", "type": "array", "desc": "挂号列表"}]},
        {"id": "api_appt_cancel", "workflow_only": True, "path": "/api/v1/appointments/{order_id}", "method": "DELETE", "desc": "取消挂号",
         "instruction_variants": ["取消挂号", "退号", "不去了", "取消预约", "喂，我不想去了", "帮我退号", "挂号能退吗", "取消怎么办"],
         "request": [{"name": "order_id", "type": "string", "label": "挂号单号", "required": True}, {"name": "reason", "type": "string", "label": "取消原因", "required": False}],
         "response": [{"name": "refund_amount", "type": "float", "desc": "退款金额"}, {"name": "refund_status", "type": "string", "desc": "退款状态"}]},
        {"id": "api_report_list", "path": "/api/v1/reports", "method": "GET", "desc": "查询检查报告列表",
         "instruction_variants": ["查询检查报告列表", "我的报告", "查看报告", "检查报告", "喂，报告出来了吗", "帮我看看报告", "报告在哪", "检查结果怎么看"],
         "request": [{"name": "patient_id", "type": "string", "label": "患者ID", "required": False}],
         "response": [{"name": "reports", "type": "array", "desc": "报告列表"}]},
        {"id": "api_report_detail", "path": "/api/v1/reports/{report_id}", "method": "GET", "desc": "查询报告详情",
         "instruction_variants": ["查询报告详情", "报告内容", "检查结果", "报告详情", "喂，这报告啥意思", "帮我看看报告", "报告怎么样", "结果正常吗"],
         "request": [{"name": "report_id", "type": "string", "label": "报告ID", "required": True}],
         "response": [{"name": "report", "type": "object", "desc": "报告详情"}, {"name": "result", "type": "string", "desc": "检查结果"}]},
        {"id": "api_prescription_list", "path": "/api/v1/prescriptions", "method": "GET", "desc": "查询处方列表",
         "instruction_variants": ["查询处方列表", "我的处方", "查看处方", "处方记录", "喂，我有处方吗", "帮我看看处方", "处方在哪", "医生开的药"],
         "request": [{"name": "patient_id", "type": "string", "label": "患者ID", "required": False}],
         "response": [{"name": "prescriptions", "type": "array", "desc": "处方列表"}]},
        {"id": "api_prescription_detail", "path": "/api/v1/prescriptions/{prescription_id}", "method": "GET", "desc": "查询处方详情",
         "instruction_variants": ["查询处方详情", "处方内容", "药品清单", "处方详情", "喂，这处方有啥药", "帮我看看处方", "开了什么药", "药品多少钱"],
         "request": [{"name": "prescription_id", "type": "string", "label": "处方ID", "required": True}],
         "response": [{"name": "prescription", "type": "object", "desc": "处方详情"}, {"name": "medicines", "type": "array", "desc": "药品列表"}, {"name": "total_fee", "type": "float", "desc": "总费用"}]},
        {"id": "api_medicine_pay", "workflow_only": True, "path": "/api/v1/prescriptions/{prescription_id}/pay", "method": "POST", "desc": "处方支付",
         "instruction_variants": ["处方支付", "支付药费", "买药付款", "缴药费", "喂，药费怎么付", "我要买药", "付药钱", "药费多少啊"],
         "request": [{"name": "prescription_id", "type": "string", "label": "处方ID", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "pickup_number", "type": "string", "desc": "取药号"}]},
        {"id": "api_checkup_package_list", "path": "/api/v1/checkup/packages", "method": "GET", "desc": "查询体检套餐",
         "instruction_variants": ["查询体检套餐", "体检套餐有哪些", "体检项目", "体检套餐列表", "喂，有啥体检套餐", "帮我看看体检", "体检怎么选", "体检套餐多少钱"],
         "request": [{"name": "category", "type": "string", "label": "套餐类别", "required": False}],
         "response": [{"name": "packages", "type": "array", "desc": "套餐列表"}]},
        {"id": "api_checkup_package_detail", "path": "/api/v1/checkup/packages/{package_id}", "method": "GET", "desc": "查询套餐详情",
         "instruction_variants": ["查询套餐详情", "套餐内容", "套餐包含什么", "套餐详情", "喂，这套餐检查啥", "帮我看看套餐", "套餐有什么项目", "这套餐怎么样"],
         "request": [{"name": "package_id", "type": "string", "label": "套餐ID", "required": True}],
         "response": [{"name": "package", "type": "object", "desc": "套餐详情"}, {"name": "items", "type": "array", "desc": "检查项目"}, {"name": "price", "type": "float", "desc": "价格"}]},
        {"id": "api_checkup_book", "workflow_only": True, "path": "/api/v1/checkup/bookings", "method": "POST", "desc": "预约体检",
         "instruction_variants": ["预约体检", "我要体检", "预订体检", "申请体检", "喂，我想做体检", "帮我约个体检", "体检怎么预约", "体检能约吗"],
         "request": [{"name": "package_id", "type": "string", "label": "套餐ID", "required": True}, {"name": "patient_id", "type": "string", "label": "患者ID", "required": True}, {"name": "date", "type": "date", "label": "体检日期", "required": True}],
         "response": [{"name": "booking_id", "type": "string", "desc": "预约单号"}, {"name": "total_fee", "type": "float", "desc": "总费用"}]},
        {"id": "api_checkup_pay", "workflow_only": True, "path": "/api/v1/checkup/bookings/{booking_id}/pay", "method": "POST", "desc": "体检支付",
         "instruction_variants": ["体检支付", "支付体检费", "缴体检费", "体检付款", "喂，体检费怎么付", "我要付体检费", "体检多少钱", "付款怎么弄"],
         "request": [{"name": "booking_id", "type": "string", "label": "预约单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "payment_id", "type": "string", "desc": "支付流水号"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_appt_list", "workflow_only": True, "path": "/api/v1/admin/appointments", "method": "GET", "desc": "查询挂号列表（管理员）",
         "instruction_variants": ["查询挂号列表", "查看所有挂号", "今日挂号", "挂号管理", "喂，今天有多少挂号", "帮我看看挂号", "挂号情况怎么样", "有哪些人挂号了"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": False}, {"name": "dept_id", "type": "string", "label": "科室ID", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "appointments", "type": "array", "desc": "挂号列表"}, {"name": "total_count", "type": "integer", "desc": "总数"}]},
        {"id": "api_admin_appt_detail", "workflow_only": True, "path": "/api/v1/admin/appointments/{order_id}", "method": "GET", "desc": "查询挂号详情（管理员）",
         "instruction_variants": ["查询挂号详情", "挂号详细信息", "挂号内容", "挂号详情", "喂，这个挂号是谁的", "帮我看看这挂号", "挂号信息怎么样", "这人挂的啥号"],
         "request": [{"name": "order_id", "type": "string", "label": "挂号单号", "required": True}],
         "response": [{"name": "appointment", "type": "object", "desc": "挂号详情"}, {"name": "patient", "type": "object", "desc": "患者信息"}, {"name": "doctor", "type": "object", "desc": "医生信息"}]},
        {"id": "api_admin_appt_checkin", "workflow_only": True, "path": "/api/v1/admin/appointments/{order_id}/checkin", "method": "POST", "desc": "患者签到",
         "instruction_variants": ["患者签到", "办理签到", "签到", "确认到达", "喂，这人来签到了", "帮忙签个到", "签到怎么办", "来了怎么登记"],
         "request": [{"name": "order_id", "type": "string", "label": "挂号单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "queue_number", "type": "integer", "desc": "排队号"}]},
        {"id": "api_admin_appt_call", "workflow_only": True, "path": "/api/v1/admin/appointments/{order_id}/call", "method": "POST", "desc": "叫号",
         "instruction_variants": ["叫号", "呼叫患者", "叫下一位", "通知就诊", "喂，该叫号了", "帮我叫个号", "叫号怎么弄", "下一个是谁"],
         "request": [{"name": "order_id", "type": "string", "label": "挂号单号", "required": True}, {"name": "room", "type": "string", "label": "诊室", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_schedule_list", "workflow_only": True, "path": "/api/v1/admin/schedules", "method": "GET", "desc": "查询排班列表",
         "instruction_variants": ["查询排班列表", "查看排班", "排班表", "医生排班", "喂，今天谁值班", "帮我看看排班", "排班情况怎么样", "哪个医生在"],
         "request": [{"name": "dept_id", "type": "string", "label": "科室ID", "required": False}, {"name": "date_from", "type": "date", "label": "开始日期", "required": False}, {"name": "date_to", "type": "date", "label": "结束日期", "required": False}],
         "response": [{"name": "schedules", "type": "array", "desc": "排班列表"}]},
        {"id": "api_admin_schedule_create", "workflow_only": True, "path": "/api/v1/admin/schedules", "method": "POST", "desc": "创建排班",
         "instruction_variants": ["创建排班", "新建排班", "添加排班", "安排排班", "喂，给医生排个班", "帮我安排排班", "排班怎么弄", "需要排班了"],
         "request": [{"name": "doctor_id", "type": "string", "label": "医生ID", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}, {"name": "time_slots", "type": "array", "label": "时段", "required": True}, {"name": "max_patients", "type": "integer", "label": "最大接诊数", "required": True}],
         "response": [{"name": "schedule_id", "type": "string", "desc": "排班ID"}]},
        {"id": "api_admin_schedule_update", "workflow_only": True, "path": "/api/v1/admin/schedules/{schedule_id}", "method": "PUT", "desc": "更新排班",
         "instruction_variants": ["更新排班", "修改排班", "编辑排班", "调整排班", "喂，排班要改一下", "帮我改改排班", "排班能改吗", "调整一下排班"],
         "request": [{"name": "schedule_id", "type": "string", "label": "排班ID", "required": True}, {"name": "time_slots", "type": "array", "label": "时段", "required": False}, {"name": "max_patients", "type": "integer", "label": "最大接诊数", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_doctor_list", "workflow_only": True, "path": "/api/v1/admin/doctors", "method": "GET", "desc": "查询医生列表（管理员）",
         "instruction_variants": ["查询医生列表", "查看所有医生", "医生管理", "医生名单", "喂，有哪些医生", "帮我看看医生", "医生都有谁", "医生列表在哪"],
         "request": [{"name": "dept_id", "type": "string", "label": "科室ID", "required": False}],
         "response": [{"name": "doctors", "type": "array", "desc": "医生列表"}]},
        {"id": "api_admin_checkup_list", "workflow_only": True, "path": "/api/v1/admin/checkup/bookings", "method": "GET", "desc": "查询体检预约列表",
         "instruction_variants": ["查询体检预约列表", "查看体检预约", "今日体检", "体检预约管理", "喂，今天有多少体检", "帮我看看体检", "体检预约情况", "有哪些人体检"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "bookings", "type": "array", "desc": "预约列表"}, {"name": "total_count", "type": "integer", "desc": "总数"}]},
        {"id": "api_admin_checkup_detail", "workflow_only": True, "path": "/api/v1/admin/checkup/bookings/{booking_id}", "method": "GET", "desc": "查询体检预约详情",
         "instruction_variants": ["查询体检预约详情", "体检预约详细信息", "体检预约内容", "体检预约详情", "喂，这个体检是谁的", "帮我看看这体检", "体检信息怎么样", "这人约的啥体检"],
         "request": [{"name": "booking_id", "type": "string", "label": "预约单号", "required": True}],
         "response": [{"name": "booking", "type": "object", "desc": "预约详情"}, {"name": "patient", "type": "object", "desc": "患者信息"}, {"name": "package", "type": "object", "desc": "套餐信息"}]},
        {"id": "api_admin_checkup_checkin", "workflow_only": True, "path": "/api/v1/admin/checkup/bookings/{booking_id}/checkin", "method": "POST", "desc": "体检签到",
         "instruction_variants": ["体检签到", "办理体检签到", "体检登记", "体检报到", "喂，这人来体检了", "帮忙体检签到", "体检签到怎么办", "来体检怎么登记"],
         "request": [{"name": "booking_id", "type": "string", "label": "预约单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "guide_sheet", "type": "string", "desc": "导检单号"}]},
        {"id": "api_admin_checkup_complete", "workflow_only": True, "path": "/api/v1/admin/checkup/bookings/{booking_id}/complete", "method": "POST", "desc": "完成体检",
         "instruction_variants": ["完成体检", "体检完成", "结束体检", "体检结束", "喂，体检做完了", "帮我完成体检", "体检怎么结束", "检查完了"],
         "request": [{"name": "booking_id", "type": "string", "label": "预约单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "report_id", "type": "string", "desc": "报告ID"}]},
        # ========== 管理员统计 API ==========
        {"id": "api_admin_visit_stats", "path": "/api/v1/medical/admin/visit/stats", "method": "GET", "desc": "查询就诊统计", "name": "就诊统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询就诊统计", "就诊数据", "就诊统计报表", "就诊情况", "喂，今天就诊多少人", "帮我看看就诊统计", "就诊数据怎么样", "就诊量多不多"],
         "request": [], "response": [{"name": "today_visits", "type": "integer", "desc": "今日就诊"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_dept_analysis", "path": "/api/v1/medical/admin/dept/analysis", "method": "GET", "desc": "查询科室分析", "name": "科室分析", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询科室分析", "科室数据", "科室统计", "科室就诊量", "喂，哪个科室人多", "帮我看看科室数据", "科室情况怎么样", "科室分析报表"],
         "request": [], "response": [{"name": "departments", "type": "array", "desc": "科室"}, {"name": "visits", "type": "array", "desc": "就诊量"}]},
        {"id": "api_admin_doctor_workload", "path": "/api/v1/medical/admin/doctor/workload", "method": "GET", "desc": "查询医生工作量", "name": "医生工作量", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询医生工作量", "医生接诊量", "医生工作统计", "医生工作量分析", "喂，哪个医生看的多", "帮我看看医生工作量", "医生业绩怎么样", "医生接诊情况"],
         "request": [], "response": [{"name": "doctors", "type": "array", "desc": "医生"}, {"name": "patients", "type": "array", "desc": "接诊量"}]},
    ],

    "workflows": [
        # ========== 患者：完整挂号流程（8步：选医院 → 选科室 → 选医生 → 身份验证 → 提交挂号 → 支付 → 通知） ==========
        {
            "id": "workflow_full_registration",
            "name": "完整挂号流程",
            "description": "完整的门诊挂号流程，包括医院选择、科室选择、医生选择、身份验证、挂号提交和支付",
            "instruction_variants": ["完整挂号流程", "我要挂号", "帮我挂号", "开始挂号", "喂，我想挂个号", "挂号怎么弄", "预约挂号", "挂号流程"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["挂号", "预约", "看病", "就诊"],
            "trigger_keywords": ["挂号", "预约", "看病", "就诊"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始挂号"}},
                {
                    "id": "n_select_dept",
                    "name": "选择科室",
                    "type": "api_call",
                    "description": "查询并选择就诊科室",
                    "config": {"api_id": "api_dept_list", "api_endpoint": "/api/v1/departments", "method": "GET", "parameters": {"hospital_id": "${hospital_id}"}},
                    "outputs": [{"name": "departments", "type": "array", "description": "科室列表"}, {"name": "dept_id", "type": "string", "description": "科室ID"}, {"name": "dept_name", "type": "string", "description": "科室名称"}],
                    "ai_instructions": {"user_message": "请选择就诊科室", "action": "选择科室"}
                },
                {
                    "id": "n_select_doctor",
                    "name": "选择医生",
                    "type": "api_call",
                    "description": "查询并选择医生和时段",
                    "config": {"api_id": "api_doc_list", "api_endpoint": "/api/v1/doctors", "method": "GET", "parameters": {"dept_id": "${dept_id}", "date": "${date}"}},
                    "outputs": [{"name": "doctors", "type": "array", "description": "医生列表"}, {"name": "doctor_id", "type": "string", "description": "医生ID"}, {"name": "doctor_name", "type": "string", "description": "医生姓名"}],
                    "ai_instructions": {"user_message": "请选择医生和就诊日期", "action": "选择医生"}
                },
                {
                    "id": "n_doctor_detail",
                    "name": "查看医生详情",
                    "type": "api_call",
                    "description": "查看医生详情和可预约时段",
                    "config": {"api_id": "api_doc_detail", "api_endpoint": "/api/v1/doctors/{doctor_id}", "method": "GET", "parameters": {"doctor_id": "${doctor_id}"}},
                    "outputs": [{"name": "doctor", "type": "object", "description": "医生详情"}, {"name": "specialty", "type": "string", "description": "专长"}, {"name": "available_slots", "type": "array", "description": "可预约时段"}, {"name": "time_slot", "type": "string", "description": "选中时段"}],
                    "ai_instructions": {"user_message": "请选择就诊时段", "action": "查看医生详情"}
                },
                {
                    "id": "n_verify",
                    "name": "患者身份验证",
                    "type": "api_call",
                    "description": "验证患者身份信息",
                    "config": {"api_id": "api_patient_verify", "api_endpoint": "/api/v1/patients/verify", "method": "POST", "parameters": {"name": "${patient_name}", "id_card": "${patient_id_card}", "phone": "${patient_phone}"}},
                    "outputs": [{"name": "patient_id", "type": "string", "description": "患者ID"}, {"name": "patient_name", "type": "string", "description": "患者姓名"}, {"name": "medical_card", "type": "string", "description": "就诊卡号"}],
                    "ai_instructions": {"user_message": "请填写患者信息进行身份验证", "action": "患者身份验证"}
                },
                {
                    "id": "n_register",
                    "name": "提交挂号",
                    "type": "api_call",
                    "description": "提交挂号订单",
                    "config": {"api_id": "api_appt_create", "api_endpoint": "/api/v1/appointments", "method": "POST", "parameters": {"doctor_id": "${doctor_id}", "patient_id": "${patient_id}", "time_slot": "${time_slot}", "symptom": "${symptom}"}},
                    "outputs": [{"name": "order_id", "type": "string", "description": "挂号单号"}, {"name": "queue_number", "type": "integer", "description": "排队号"}, {"name": "fee", "type": "float", "description": "挂号费"}],
                    "ai_instructions": {"user_message": "请确认挂号信息", "action": "提交挂号"}
                },
                {
                    "id": "n_pay",
                    "name": "挂号支付",
                    "type": "api_call",
                    "description": "支付挂号费",
                    "config": {"api_id": "api_appt_pay", "api_endpoint": "/api/v1/appointments/{order_id}/pay", "method": "POST", "parameters": {"order_id": "${order_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "payment_id", "type": "string", "description": "支付流水号"}],
                    "ai_instructions": {"user_message": "请选择支付方式完成支付", "action": "挂号支付"}
                },
                {
                    "id": "n_notify",
                    "name": "挂号通知",
                    "type": "notification",
                    "description": "发送挂号成功通知",
                    "config": {"message_template": "挂号成功！挂号单号：${order_id}，科室：${dept_name}，医生：${doctor_name}，排队号：${queue_number}，请按时就诊。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "挂号成功", "action": "发送挂号通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "挂号完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_select_dept"},
                {"source": "n_select_dept", "target": "n_select_doctor"},
                {"source": "n_select_doctor", "target": "n_doctor_detail"},
                {"source": "n_doctor_detail", "target": "n_verify"},
                {"source": "n_verify", "target": "n_register"},
                {"source": "n_register", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 患者：取消挂号流程（5步：查询挂号 → 确认信息 → 取消 → 退款 → 通知） ==========
        {
            "id": "workflow_cancel_appt",
            "name": "取消挂号流程",
            "description": "取消挂号并退款",
            "instruction_variants": ["取消挂号流程", "我要取消挂号", "退号", "不去了", "喂，我不想去了", "帮我退号", "取消预约", "挂号能退吗"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["取消挂号", "退号", "取消预约"],
            "trigger_keywords": ["取消挂号", "退号", "取消预约"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始取消挂号"}},
                {
                    "id": "n_query",
                    "name": "查询挂号",
                    "type": "api_call",
                    "description": "查询要取消的挂号订单",
                    "config": {"api_id": "api_appt_query", "api_endpoint": "/api/v1/appointments/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "appointment", "type": "object", "description": "挂号详情"}, {"name": "status", "type": "string", "description": "订单状态"}, {"name": "doctor_name", "type": "string", "description": "医生姓名"}],
                    "ai_instructions": {"user_message": "请输入要取消的挂号单号", "action": "查询挂号"}
                },
                {
                    "id": "n_cancel",
                    "name": "取消挂号",
                    "type": "api_call",
                    "description": "确认取消挂号",
                    "config": {"api_id": "api_appt_cancel", "api_endpoint": "/api/v1/appointments/{order_id}", "method": "DELETE", "parameters": {"order_id": "${order_id}", "reason": "${reason}"}},
                    "outputs": [{"name": "refund_amount", "type": "float", "description": "退款金额"}, {"name": "refund_status", "type": "string", "description": "退款状态"}],
                    "ai_instructions": {"user_message": "请确认取消挂号并填写原因", "action": "取消挂号"}
                },
                {
                    "id": "n_notify",
                    "name": "取消通知",
                    "type": "notification",
                    "description": "发送取消成功通知",
                    "config": {"message_template": "挂号已取消！退款金额：${refund_amount}元，预计1-3个工作日到账。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "取消成功", "action": "发送取消通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "取消挂号完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_query"},
                {"source": "n_query", "target": "n_cancel"},
                {"source": "n_cancel", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 患者：体检预约流程（6步：查询套餐 → 查看详情 → 身份验证 → 预约 → 支付 → 通知） ==========
        {
            "id": "workflow_checkup_book",
            "name": "体检预约流程",
            "description": "完整的体检预约流程，包括套餐选择、身份验证、预约和支付",
            "instruction_variants": ["体检预约流程", "我要体检", "预约体检", "办理体检", "喂，我想做体检", "帮我约个体检", "健康检查", "体检怎么预约"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["体检", "预约体检", "健康检查"],
            "trigger_keywords": ["体检", "预约体检", "健康检查"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始预约体检"}},
                {
                    "id": "n_package_list",
                    "name": "查询体检套餐",
                    "type": "api_call",
                    "description": "查询可选的体检套餐",
                    "config": {"api_id": "api_checkup_package_list", "api_endpoint": "/api/v1/checkup/packages", "method": "GET", "parameters": {"category": "${category}"}},
                    "outputs": [{"name": "packages", "type": "array", "description": "套餐列表"}, {"name": "package_id", "type": "string", "description": "选中套餐ID"}],
                    "ai_instructions": {"user_message": "请选择体检套餐类别", "action": "查询体检套餐"}
                },
                {
                    "id": "n_package_detail",
                    "name": "查看套餐详情",
                    "type": "api_call",
                    "description": "查看套餐详细项目",
                    "config": {"api_id": "api_checkup_package_detail", "api_endpoint": "/api/v1/checkup/packages/{package_id}", "method": "GET", "parameters": {"package_id": "${package_id}"}},
                    "outputs": [{"name": "package", "type": "object", "description": "套餐详情"}, {"name": "items", "type": "array", "description": "检查项目"}, {"name": "price", "type": "float", "description": "价格"}],
                    "ai_instructions": {"user_message": "请选择要查看的套餐", "action": "查看套餐详情"}
                },
                {
                    "id": "n_verify",
                    "name": "身份验证",
                    "type": "api_call",
                    "description": "验证体检人身份",
                    "config": {"api_id": "api_patient_verify", "api_endpoint": "/api/v1/patients/verify", "method": "POST", "parameters": {"name": "${patient_name}", "id_card": "${patient_id_card}", "phone": "${patient_phone}"}},
                    "outputs": [{"name": "patient_id", "type": "string", "description": "患者ID"}, {"name": "patient_name", "type": "string", "description": "患者姓名"}],
                    "ai_instructions": {"user_message": "请填写体检人信息", "action": "身份验证"}
                },
                {
                    "id": "n_book",
                    "name": "预约体检",
                    "type": "api_call",
                    "description": "提交体检预约",
                    "config": {"api_id": "api_checkup_book", "api_endpoint": "/api/v1/checkup/bookings", "method": "POST", "parameters": {"package_id": "${package_id}", "patient_id": "${patient_id}", "date": "${date}"}},
                    "outputs": [{"name": "booking_id", "type": "string", "description": "预约单号"}, {"name": "total_fee", "type": "float", "description": "总费用"}],
                    "ai_instructions": {"user_message": "请选择体检日期", "action": "预约体检"}
                },
                {
                    "id": "n_pay",
                    "name": "体检支付",
                    "type": "api_call",
                    "description": "支付体检费用",
                    "config": {"api_id": "api_checkup_pay", "api_endpoint": "/api/v1/checkup/bookings/{booking_id}/pay", "method": "POST", "parameters": {"booking_id": "${booking_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "payment_id", "type": "string", "description": "支付流水号"}],
                    "ai_instructions": {"user_message": "请选择支付方式完成支付", "action": "体检支付"}
                },
                {
                    "id": "n_notify",
                    "name": "预约通知",
                    "type": "notification",
                    "description": "发送预约成功通知",
                    "config": {"message_template": "体检预约成功！预约单号：${booking_id}，体检日期：${date}，请空腹前往体检中心。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "预约成功", "action": "发送预约通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "体检预约完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_package_list"},
                {"source": "n_package_list", "target": "n_package_detail"},
                {"source": "n_package_detail", "target": "n_verify"},
                {"source": "n_verify", "target": "n_book"},
                {"source": "n_book", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 患者：处方取药流程（5步：查询处方 → 查看详情 → 支付 → 取药 → 通知） ==========
        {
            "id": "workflow_medicine_pickup",
            "name": "处方取药流程",
            "description": "处方支付和取药流程",
            "instruction_variants": ["处方取药流程", "我要取药", "买药", "拿药", "喂，我来拿药", "帮我取药", "处方缴费", "取药怎么办"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["取药", "买药", "处方"],
            "trigger_keywords": ["取药", "买药", "处方"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始取药流程"}},
                {
                    "id": "n_prescription_list",
                    "name": "查询处方",
                    "type": "api_call",
                    "description": "查询待取药的处方",
                    "config": {"api_id": "api_prescription_list", "api_endpoint": "/api/v1/prescriptions", "method": "GET", "parameters": {"patient_id": "${patient_id}"}},
                    "outputs": [{"name": "prescriptions", "type": "array", "description": "处方列表"}, {"name": "prescription_id", "type": "string", "description": "选中处方ID"}],
                    "ai_instructions": {"user_message": "正在查询您的处方", "action": "查询处方"}
                },
                {
                    "id": "n_prescription_detail",
                    "name": "查看处方详情",
                    "type": "api_call",
                    "description": "查看处方药品详情",
                    "config": {"api_id": "api_prescription_detail", "api_endpoint": "/api/v1/prescriptions/{prescription_id}", "method": "GET", "parameters": {"prescription_id": "${prescription_id}"}},
                    "outputs": [{"name": "prescription", "type": "object", "description": "处方详情"}, {"name": "medicines", "type": "array", "description": "药品列表"}, {"name": "total_fee", "type": "float", "description": "总费用"}],
                    "ai_instructions": {"user_message": "请选择要取药的处方", "action": "查看处方详情"}
                },
                {
                    "id": "n_pay",
                    "name": "处方支付",
                    "type": "api_call",
                    "description": "支付药品费用",
                    "config": {"api_id": "api_medicine_pay", "api_endpoint": "/api/v1/prescriptions/{prescription_id}/pay", "method": "POST", "parameters": {"prescription_id": "${prescription_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "pickup_number", "type": "string", "description": "取药号"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "处方支付"}
                },
                {
                    "id": "n_notify",
                    "name": "取药通知",
                    "type": "notification",
                    "description": "发送取药通知",
                    "config": {"message_template": "支付成功！取药号：${pickup_number}，请到药房窗口取药。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "支付成功", "action": "发送取药通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "取药流程完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_prescription_list"},
                {"source": "n_prescription_list", "target": "n_prescription_detail"},
                {"source": "n_prescription_detail", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：患者签到叫号流程（5步：查询挂号 → 查看详情 → 签到 → 叫号 → 通知） ==========
        {
            "id": "workflow_admin_checkin_call",
            "name": "患者签到叫号流程",
            "description": "管理员办理患者签到和叫号",
            "instruction_variants": ["患者签到叫号流程", "办理签到", "患者签到", "叫号", "喂，这人来签到了", "帮忙签到叫号", "签到叫号", "叫号怎么办"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["签到", "叫号", "患者签到"],
            "trigger_keywords": ["签到", "叫号"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始签到叫号"}},
                {
                    "id": "n_appt_list",
                    "name": "查询今日挂号",
                    "type": "api_call",
                    "description": "查询今日挂号列表",
                    "config": {"api_id": "api_admin_appt_list", "api_endpoint": "/api/v1/admin/appointments", "method": "GET", "parameters": {"date": "${date}", "status": "paid"}},
                    "outputs": [{"name": "appointments", "type": "array", "description": "挂号列表"}, {"name": "total_count", "type": "integer", "description": "总数"}],
                    "ai_instructions": {"user_message": "正在查询今日挂号", "action": "查询今日挂号"}
                },
                {
                    "id": "n_appt_detail",
                    "name": "查看挂号详情",
                    "type": "api_call",
                    "description": "查看挂号详细信息",
                    "config": {"api_id": "api_admin_appt_detail", "api_endpoint": "/api/v1/admin/appointments/{order_id}", "method": "GET", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "appointment", "type": "object", "description": "挂号详情"}, {"name": "patient", "type": "object", "description": "患者信息"}, {"name": "doctor", "type": "object", "description": "医生信息"}],
                    "ai_instructions": {"user_message": "请选择要签到的挂号", "action": "查看挂号详情"}
                },
                {
                    "id": "n_checkin",
                    "name": "患者签到",
                    "type": "api_call",
                    "description": "办理患者签到",
                    "config": {"api_id": "api_admin_appt_checkin", "api_endpoint": "/api/v1/admin/appointments/{order_id}/checkin", "method": "POST", "parameters": {"order_id": "${order_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "queue_number", "type": "integer", "description": "排队号"}],
                    "ai_instructions": {"user_message": "正在办理签到", "action": "患者签到"}
                },
                {
                    "id": "n_call",
                    "name": "叫号",
                    "type": "api_call",
                    "description": "叫号就诊",
                    "config": {"api_id": "api_admin_appt_call", "api_endpoint": "/api/v1/admin/appointments/{order_id}/call", "method": "POST", "parameters": {"order_id": "${order_id}", "room": "${room}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择诊室进行叫号", "action": "叫号"}
                },
                {
                    "id": "n_notify",
                    "name": "叫号通知",
                    "type": "notification",
                    "description": "发送叫号通知",
                    "config": {"message_template": "叫号成功！排队号：${queue_number}，请患者到${room}就诊。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "叫号成功", "action": "发送叫号通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "签到叫号完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_appt_list"},
                {"source": "n_appt_list", "target": "n_appt_detail"},
                {"source": "n_appt_detail", "target": "n_checkin"},
                {"source": "n_checkin", "target": "n_call"},
                {"source": "n_call", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：医生排班管理流程（5步：查询排班 → 选择医生 → 创建排班 → 确认 → 通知） ==========
        {
            "id": "workflow_admin_schedule",
            "name": "医生排班管理流程",
            "description": "管理员创建和管理医生排班",
            "instruction_variants": ["医生排班管理流程", "创建排班", "医生排班", "安排排班", "喂，给医生排个班", "帮我安排排班", "排班管理", "排班怎么弄"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["排班", "医生排班", "创建排班"],
            "trigger_keywords": ["排班", "医生排班"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始排班管理"}},
                {
                    "id": "n_schedule_list",
                    "name": "查询现有排班",
                    "type": "api_call",
                    "description": "查询现有排班情况",
                    "config": {"api_id": "api_admin_schedule_list", "api_endpoint": "/api/v1/admin/schedules", "method": "GET", "parameters": {"dept_id": "${dept_id}", "date_from": "${date_from}", "date_to": "${date_to}"}},
                    "outputs": [{"name": "schedules", "type": "array", "description": "排班列表"}],
                    "ai_instructions": {"user_message": "请选择科室和日期范围查询排班", "action": "查询现有排班"}
                },
                {
                    "id": "n_doctor_list",
                    "name": "选择医生",
                    "type": "api_call",
                    "description": "选择要排班的医生",
                    "config": {"api_id": "api_admin_doctor_list", "api_endpoint": "/api/v1/admin/doctors", "method": "GET", "parameters": {"dept_id": "${dept_id}"}},
                    "outputs": [{"name": "doctors", "type": "array", "description": "医生列表"}, {"name": "doctor_id", "type": "string", "description": "选中医生ID"}],
                    "ai_instructions": {"user_message": "请选择要排班的医生", "action": "选择医生"}
                },
                {
                    "id": "n_create_schedule",
                    "name": "创建排班",
                    "type": "api_call",
                    "description": "创建医生排班",
                    "config": {"api_id": "api_admin_schedule_create", "api_endpoint": "/api/v1/admin/schedules", "method": "POST", "parameters": {"doctor_id": "${doctor_id}", "date": "${date}", "time_slots": "${time_slots}", "max_patients": "${max_patients}"}},
                    "outputs": [{"name": "schedule_id", "type": "string", "description": "排班ID"}],
                    "ai_instructions": {"user_message": "请填写排班日期、时段和最大接诊数", "action": "创建排班"}
                },
                {
                    "id": "n_notify",
                    "name": "排班通知",
                    "type": "notification",
                    "description": "发送排班创建成功通知",
                    "config": {"message_template": "排班创建成功！排班ID：${schedule_id}，已通知相关医生。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "排班创建成功", "action": "发送排班通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "排班管理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_schedule_list"},
                {"source": "n_schedule_list", "target": "n_doctor_list"},
                {"source": "n_doctor_list", "target": "n_create_schedule"},
                {"source": "n_create_schedule", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：体检签到流程（5步：查询预约 → 查看详情 → 签到 → 发导检单 → 通知） ==========
        {
            "id": "workflow_admin_checkup_checkin",
            "name": "体检签到流程",
            "description": "管理员办理体检签到",
            "instruction_variants": ["体检签到流程", "办理体检签到", "体检登记", "体检报到", "喂，这人来体检了", "帮忙体检签到", "体检签到", "体检怎么登记"],
            "business_scenario": "medical",
            "status": "active",
            "user_intents": ["体检签到", "办理体检"],
            "trigger_keywords": ["体检签到", "办理体检"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始体检签到"}},
                {
                    "id": "n_booking_list",
                    "name": "查询今日体检预约",
                    "type": "api_call",
                    "description": "查询今日体检预约列表",
                    "config": {"api_id": "api_admin_checkup_list", "api_endpoint": "/api/v1/admin/checkup/bookings", "method": "GET", "parameters": {"date": "${date}", "status": "paid"}},
                    "outputs": [{"name": "bookings", "type": "array", "description": "预约列表"}, {"name": "total_count", "type": "integer", "description": "总数"}],
                    "ai_instructions": {"user_message": "正在查询今日体检预约", "action": "查询今日体检预约"}
                },
                {
                    "id": "n_booking_detail",
                    "name": "查看预约详情",
                    "type": "api_call",
                    "description": "查看体检预约详细信息",
                    "config": {"api_id": "api_admin_checkup_detail", "api_endpoint": "/api/v1/admin/checkup/bookings/{booking_id}", "method": "GET", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "booking", "type": "object", "description": "预约详情"}, {"name": "patient", "type": "object", "description": "患者信息"}, {"name": "package", "type": "object", "description": "套餐信息"}],
                    "ai_instructions": {"user_message": "请选择要签到的预约", "action": "查看预约详情"}
                },
                {
                    "id": "n_checkin",
                    "name": "体检签到",
                    "type": "api_call",
                    "description": "办理体检签到并发放导检单",
                    "config": {"api_id": "api_admin_checkup_checkin", "api_endpoint": "/api/v1/admin/checkup/bookings/{booking_id}/checkin", "method": "POST", "parameters": {"booking_id": "${booking_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "guide_sheet", "type": "string", "description": "导检单号"}],
                    "ai_instructions": {"user_message": "正在办理签到", "action": "体检签到"}
                },
                {
                    "id": "n_notify",
                    "name": "签到通知",
                    "type": "notification",
                    "description": "发送签到成功通知",
                    "config": {"message_template": "体检签到成功！导检单号：${guide_sheet}，请按导检单顺序进行各项检查。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "签到成功", "action": "发送签到通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "体检签到完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_booking_list"},
                {"source": "n_booking_list", "target": "n_booking_detail"},
                {"source": "n_booking_detail", "target": "n_checkin"},
                {"source": "n_checkin", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
