# finance.py - 财务场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

FINANCE_SCENE = {
    "domain": "finance",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_invoice_query", "path": "/api/finance/invoices", "method": "GET", "desc": "查询发票",
         "instruction_variants": ["查询发票", "查看发票", "我的发票", "发票在哪", "喂，帮我查查发票", "发票怎么查", "有哪些发票", "发票记录呢"],
         "request": [{"name": "invoice_no", "type": "string", "label": "发票号", "required": False}, {"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "invoices", "type": "array", "desc": "发票列表"}]},
        {"id": "api_invoice_apply", "workflow_only": True, "path": "/api/finance/invoices", "method": "POST", "desc": "申请开票",
         "instruction_variants": ["申请开票", "我要开发票", "开票申请", "帮我开发票", "喂，怎么开发票", "发票怎么开", "能开发票吗", "开个发票"],
         "request": [{"name": "order_id", "type": "string", "label": "订单号", "required": True}, {"name": "title", "type": "string", "label": "发票抬头", "required": True}, {"name": "tax_no", "type": "string", "label": "税号", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "type", "type": "string", "label": "发票类型", "required": True}],
         "response": [{"name": "invoice_id", "type": "string", "desc": "发票ID"}]},
        {"id": "api_budget_query", "path": "/api/finance/budgets", "method": "GET", "desc": "查询预算",
         "instruction_variants": ["查询预算", "查看预算", "预算还有多少", "预算情况", "喂，帮我看看预算", "预算怎么查", "还剩多少预算", "预算够不够"],
         "request": [{"name": "dept_id", "type": "string", "label": "部门ID", "required": False}, {"name": "year", "type": "string", "label": "年份", "required": False}],
         "response": [{"name": "budgets", "type": "array", "desc": "预算列表"}, {"name": "total_budget", "type": "float", "desc": "总预算"}, {"name": "used_budget", "type": "float", "desc": "已用预算"}]},
        {"id": "api_expense_apply", "workflow_only": True, "path": "/api/finance/expenses", "method": "POST", "desc": "费用申请",
         "instruction_variants": ["费用申请", "申请费用", "我要申请费用", "提交费用", "喂，怎么申请费用", "费用怎么报", "能申请费用吗", "申请个费用"],
         "request": [{"name": "type", "type": "string", "label": "费用类型", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "description", "type": "string", "label": "说明", "required": True}, {"name": "dept_id", "type": "string", "label": "部门ID", "required": True}],
         "response": [{"name": "expense_id", "type": "string", "desc": "费用单号"}]},
        {"id": "api_reimbursement_apply", "workflow_only": True, "path": "/api/finance/reimbursements", "method": "POST", "desc": "报销申请",
         "instruction_variants": ["报销申请", "申请报销", "我要报销", "提交报销", "喂，怎么报销", "报销怎么弄", "能报销吗", "报个销"],
         "request": [{"name": "type", "type": "string", "label": "报销类型", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "invoices", "type": "array", "label": "发票列表", "required": True}, {"name": "description", "type": "string", "label": "说明", "required": True}],
         "response": [{"name": "reimbursement_id", "type": "string", "desc": "报销单号"}]},
        {"id": "api_payment_apply", "workflow_only": True, "path": "/api/finance/payments", "method": "POST", "desc": "付款申请",
         "instruction_variants": ["付款申请", "申请付款", "我要付款", "提交付款", "喂，怎么申请付款", "付款怎么办", "能付款吗", "申请个付款"],
         "request": [{"name": "payee_name", "type": "string", "label": "收款人", "required": True}, {"name": "payee_account", "type": "string", "label": "收款账号", "required": True}, {"name": "payee_bank", "type": "string", "label": "开户行", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "reason", "type": "string", "label": "付款原因", "required": True}],
         "response": [{"name": "payment_id", "type": "string", "desc": "付款单号"}]},
        {"id": "api_salary_query", "path": "/api/finance/salary", "method": "GET", "desc": "查询工资",
         "instruction_variants": ["查询工资", "查看工资", "我的工资", "工资多少", "喂，帮我查查工资", "工资怎么查", "这个月工资", "工资发了吗"],
         "request": [{"name": "employee_id", "type": "string", "label": "员工ID", "required": True}, {"name": "month", "type": "string", "label": "月份", "required": False}],
         "response": [{"name": "salary", "type": "object", "desc": "工资详情"}, {"name": "deductions", "type": "array", "desc": "扣款明细"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_expense_list", "workflow_only": True, "path": "/api/finance/admin/expenses", "method": "GET", "desc": "查询费用申请列表（管理员）",
         "instruction_variants": ["查询费用申请列表", "查看费用申请", "费用列表", "待审批费用", "喂，有哪些费用要审", "帮我看看费用申请", "费用申请在哪", "要审批的费用"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "expenses", "type": "array", "desc": "费用列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数"}]},
        {"id": "api_admin_expense_approve", "workflow_only": True, "path": "/api/finance/admin/expenses/{expense_id}/approve", "method": "POST", "desc": "审批费用",
         "instruction_variants": ["审批费用", "费用审批", "批准费用", "审核费用", "喂，这个费用怎么审", "帮我审批费用", "费用能批吗", "审一下费用"],
         "request": [{"name": "expense_id", "type": "string", "label": "费用单号", "required": True}, {"name": "result", "type": "string", "label": "审批结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_reimbursement_list", "workflow_only": True, "path": "/api/finance/admin/reimbursements", "method": "GET", "desc": "查询报销申请列表（管理员）",
         "instruction_variants": ["查询报销申请列表", "查看报销申请", "报销列表", "待审批报销", "喂，有哪些报销要审", "帮我看看报销申请", "报销申请在哪", "要审批的报销"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "reimbursements", "type": "array", "desc": "报销列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数"}]},
        {"id": "api_admin_reimbursement_approve", "workflow_only": True, "path": "/api/finance/admin/reimbursements/{reimbursement_id}/approve", "method": "POST", "desc": "审批报销",
         "instruction_variants": ["审批报销", "报销审批", "批准报销", "审核报销", "喂，这个报销怎么审", "帮我审批报销", "报销能批吗", "审一下报销"],
         "request": [{"name": "reimbursement_id", "type": "string", "label": "报销单号", "required": True}, {"name": "result", "type": "string", "label": "审批结果", "required": True}, {"name": "approved_amount", "type": "float", "label": "批准金额", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_payment_list", "workflow_only": True, "path": "/api/finance/admin/payments", "method": "GET", "desc": "查询付款申请列表（管理员）",
         "instruction_variants": ["查询付款申请列表", "查看付款申请", "付款列表", "待审批付款", "喂，有哪些付款要审", "帮我看看付款申请", "付款申请在哪", "要审批的付款"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "payments", "type": "array", "desc": "付款列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数"}]},
        {"id": "api_admin_payment_approve", "workflow_only": True, "path": "/api/finance/admin/payments/{payment_id}/approve", "method": "POST", "desc": "审批付款",
         "instruction_variants": ["审批付款", "付款审批", "批准付款", "审核付款", "喂，这个付款怎么审", "帮我审批付款", "付款能批吗", "审一下付款"],
         "request": [{"name": "payment_id", "type": "string", "label": "付款单号", "required": True}, {"name": "result", "type": "string", "label": "审批结果", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_payment_execute", "workflow_only": True, "path": "/api/finance/admin/payments/{payment_id}/execute", "method": "POST", "desc": "执行付款",
         "instruction_variants": ["执行付款", "付款执行", "打款", "转账", "喂，这个款怎么打", "帮我执行付款", "能打款吗", "转账怎么办"],
         "request": [{"name": "payment_id", "type": "string", "label": "付款单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "transaction_no", "type": "string", "desc": "交易流水号"}]},
        {"id": "api_admin_invoice_list", "workflow_only": True, "path": "/api/finance/admin/invoices", "method": "GET", "desc": "查询开票申请列表（管理员）",
         "instruction_variants": ["查询开票申请列表", "查看开票申请", "开票列表", "待开票申请", "喂，有哪些要开票", "帮我看看开票申请", "开票申请在哪", "要开的发票"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "invoices", "type": "array", "desc": "开票列表"}, {"name": "pending_count", "type": "integer", "desc": "待开票数"}]},
        {"id": "api_admin_invoice_issue", "workflow_only": True, "path": "/api/finance/admin/invoices/{invoice_id}/issue", "method": "POST", "desc": "开具发票",
         "instruction_variants": ["开具发票", "开发票", "发票开具", "出票", "喂，这个发票怎么开", "帮我开发票", "能开票吗", "开一下发票"],
         "request": [{"name": "invoice_id", "type": "string", "label": "发票ID", "required": True}, {"name": "invoice_no", "type": "string", "label": "发票号码", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "invoice_url", "type": "string", "desc": "发票链接"}]},

        # ========== 管理员统计 API ==========
        {"id": "api_admin_finance_overview", "path": "/api/finance/admin/stats/overview", "method": "GET", "desc": "查询财务概览", "name": "财务概览", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询财务概览", "财务概览", "财务总览", "财务情况", "喂，帮我看看财务", "财务怎么样", "财务数据", "财务报表"],
         "request": [], "response": [{"name": "total_income", "type": "float", "desc": "总收入"}, {"name": "monthly_trend", "type": "array", "desc": "月度趋势"}]},
        {"id": "api_admin_expense_analysis", "path": "/api/finance/admin/stats/expense", "method": "GET", "desc": "查询费用分析", "name": "费用分析", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询费用分析", "费用分析", "费用统计", "费用情况", "喂，帮我看看费用", "费用怎么样", "费用数据", "费用报表"],
         "request": [], "response": [{"name": "categories", "type": "array", "desc": "费用类别"}, {"name": "amounts", "type": "array", "desc": "金额"}]},
    ],

    "workflows": [
        # ========== 用户：完整报销流程（5步：查询预算 → 查询发票 → 提交报销 → 确认 → 通知） ==========
        {
            "id": "workflow_full_reimbursement",
            "name": "完整报销流程",
            "description": "完整的报销申请流程",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["报销", "申请报销", "费用报销"],
            "trigger_keywords": ["报销", "申请报销", "费用报销"],
            "instruction_variants": ["报销", "申请报销", "我要报销", "费用报销", "喂，怎么报销", "帮我报销", "报销怎么弄", "能报销吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始报销"}},
                {"id": "n_budget", "name": "查询预算", "type": "api_call", "description": "查询部门预算", "config": {"api_id": "api_budget_query", "api_endpoint": "/api/finance/budgets", "method": "GET", "parameters": {"dept_id": "${dept_id}"}}, "outputs": [{"name": "total_budget", "type": "float", "description": "总预算"}, {"name": "used_budget", "type": "float", "description": "已用预算"}], "ai_instructions": {"user_message": "请输入部门ID查询预算", "action": "查询预算"}},
                {"id": "n_invoice", "name": "查询发票", "type": "api_call", "description": "查询可用发票", "config": {"api_id": "api_invoice_query", "api_endpoint": "/api/finance/invoices", "method": "GET", "parameters": {"status": "unused"}}, "outputs": [{"name": "invoices", "type": "array", "description": "发票列表"}], "ai_instructions": {"user_message": "查询可用发票", "action": "查询发票"}},
                {"id": "n_apply", "name": "提交报销", "type": "api_call", "description": "提交报销申请", "config": {"api_id": "api_reimbursement_apply", "api_endpoint": "/api/finance/reimbursements", "method": "POST", "parameters": {"type": "${type}", "amount": "${amount}", "invoices": "${invoices}", "description": "${description}"}}, "outputs": [{"name": "reimbursement_id", "type": "string", "description": "报销单号"}], "ai_instructions": {"user_message": "请选择发票并填写报销信息", "action": "提交报销"}},
                {"id": "n_notify", "name": "报销通知", "type": "notification", "description": "发送报销申请通知", "config": {"message_template": "报销申请已提交！报销单号：${reimbursement_id}，金额：${amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "报销已提交", "action": "发送报销通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报销申请完成"}}
            ],
            "edges": [{"source": "start", "target": "n_budget"}, {"source": "n_budget", "target": "n_invoice"}, {"source": "n_invoice", "target": "n_apply"}, {"source": "n_apply", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 用户：付款申请流程（4步：查询预算 → 填写付款 → 提交 → 通知） ==========
        {
            "id": "workflow_payment",
            "name": "付款申请流程",
            "description": "申请付款",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["付款", "付款申请", "申请付款"],
            "trigger_keywords": ["付款", "付款申请", "申请付款"],
            "instruction_variants": ["付款", "付款申请", "申请付款", "我要付款", "喂，怎么付款", "帮我付款", "付款怎么办", "能付款吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始付款申请"}},
                {"id": "n_budget", "name": "查询预算", "type": "api_call", "description": "查询部门预算", "config": {"api_id": "api_budget_query", "api_endpoint": "/api/finance/budgets", "method": "GET", "parameters": {"dept_id": "${dept_id}"}}, "outputs": [{"name": "total_budget", "type": "float", "description": "总预算"}], "ai_instructions": {"user_message": "请输入部门ID", "action": "查询预算"}},
                {"id": "n_apply", "name": "提交付款", "type": "api_call", "description": "提交付款申请", "config": {"api_id": "api_payment_apply", "api_endpoint": "/api/finance/payments", "method": "POST", "parameters": {"payee_name": "${payee_name}", "payee_account": "${payee_account}", "payee_bank": "${payee_bank}", "amount": "${amount}", "reason": "${reason}"}}, "outputs": [{"name": "payment_id", "type": "string", "description": "付款单号"}], "ai_instructions": {"user_message": "请填写付款信息", "action": "提交付款"}},
                {"id": "n_notify", "name": "付款通知", "type": "notification", "description": "发送付款申请通知", "config": {"message_template": "付款申请已提交！付款单号：${payment_id}，金额：${amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "付款已提交", "action": "发送付款通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "付款申请完成"}}
            ],
            "edges": [{"source": "start", "target": "n_budget"}, {"source": "n_budget", "target": "n_apply"}, {"source": "n_apply", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 用户：开票申请流程（3步：填写开票信息 → 提交 → 通知） ==========
        {
            "id": "workflow_invoice",
            "name": "开票申请流程",
            "description": "申请开具发票",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["开票", "开发票", "申请发票"],
            "trigger_keywords": ["开票", "开发票", "申请发票"],
            "instruction_variants": ["开票", "开发票", "申请发票", "我要开票", "喂，怎么开票", "帮我开发票", "开票怎么办", "能开票吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始开票申请"}},
                {"id": "n_apply", "name": "提交开票", "type": "api_call", "description": "提交开票申请", "config": {"api_id": "api_invoice_apply", "api_endpoint": "/api/finance/invoices", "method": "POST", "parameters": {"order_id": "${order_id}", "title": "${title}", "tax_no": "${tax_no}", "amount": "${amount}", "type": "${type}"}}, "outputs": [{"name": "invoice_id", "type": "string", "description": "发票ID"}], "ai_instructions": {"user_message": "请填写开票信息", "action": "提交开票"}},
                {"id": "n_notify", "name": "开票通知", "type": "notification", "description": "发送开票申请通知", "config": {"message_template": "开票申请已提交！发票ID：${invoice_id}。"}, "outputs": [], "ai_instructions": {"user_message": "开票已提交", "action": "发送开票通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "开票申请完成"}}
            ],
            "edges": [{"source": "start", "target": "n_apply"}, {"source": "n_apply", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：报销审批流程（4步：查询报销列表 → 查看详情 → 审批 → 通知） ==========
        {
            "id": "workflow_admin_reimbursement",
            "name": "管理员报销审批流程",
            "description": "审批报销申请",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["审批报销", "报销审批", "处理报销"],
            "trigger_keywords": ["审批报销", "报销审批", "处理报销"],
            "instruction_variants": ["审批报销", "报销审批", "处理报销", "审核报销", "喂，怎么审批报销", "帮我审报销", "报销怎么审", "能审批吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审批报销"}},
                {"id": "n_list", "name": "查询报销列表", "type": "api_call", "description": "查询待审批报销", "config": {"api_id": "api_admin_reimbursement_list", "api_endpoint": "/api/finance/admin/reimbursements", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "reimbursements", "type": "array", "description": "报销列表"}], "ai_instructions": {"user_message": "查询待审批报销", "action": "查询报销列表"}},
                {"id": "n_approve", "name": "审批报销", "type": "api_call", "description": "审批报销申请", "config": {"api_id": "api_admin_reimbursement_approve", "api_endpoint": "/api/finance/admin/reimbursements/{reimbursement_id}/approve", "method": "POST", "parameters": {"reimbursement_id": "${reimbursement_id}", "result": "${result}", "approved_amount": "${approved_amount}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择报销并填写审批结果", "action": "审批报销"}},
                {"id": "n_notify", "name": "审批通知", "type": "notification", "description": "发送审批结果通知", "config": {"message_template": "报销审批完成！报销单号${reimbursement_id}，批准金额：${approved_amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报销审批完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_approve"}, {"source": "n_approve", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：付款审批执行流程（5步：查询付款列表 → 审批付款 → 执行付款 → 确认 → 通知） ==========
        {
            "id": "workflow_admin_payment",
            "name": "管理员付款审批执行流程",
            "description": "审批并执行付款",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["审批付款", "付款审批", "执行付款"],
            "trigger_keywords": ["审批付款", "付款审批", "执行付款"],
            "instruction_variants": ["审批付款", "付款审批", "执行付款", "处理付款", "喂，怎么审批付款", "帮我审付款", "付款怎么审", "能执行付款吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审批付款"}},
                {"id": "n_list", "name": "查询付款列表", "type": "api_call", "description": "查询待审批付款", "config": {"api_id": "api_admin_payment_list", "api_endpoint": "/api/finance/admin/payments", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "payments", "type": "array", "description": "付款列表"}], "ai_instructions": {"user_message": "查询待审批付款", "action": "查询付款列表"}},
                {"id": "n_approve", "name": "审批付款", "type": "api_call", "description": "审批付款申请", "config": {"api_id": "api_admin_payment_approve", "api_endpoint": "/api/finance/admin/payments/{payment_id}/approve", "method": "POST", "parameters": {"payment_id": "${payment_id}", "result": "${result}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择付款并填写审批结果", "action": "审批付款"}},
                {"id": "n_execute", "name": "执行付款", "type": "api_call", "description": "执行付款", "config": {"api_id": "api_admin_payment_execute", "api_endpoint": "/api/finance/admin/payments/{payment_id}/execute", "method": "POST", "parameters": {"payment_id": "${payment_id}"}}, "outputs": [{"name": "transaction_no", "type": "string", "description": "交易流水号"}], "ai_instructions": {"user_message": "确认执行付款", "action": "执行付款"}},
                {"id": "n_notify", "name": "付款通知", "type": "notification", "description": "发送付款完成通知", "config": {"message_template": "付款完成！付款单号${payment_id}，交易流水号：${transaction_no}。"}, "outputs": [], "ai_instructions": {"user_message": "付款完成", "action": "发送付款通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "付款审批完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_approve"}, {"source": "n_approve", "target": "n_execute"}, {"source": "n_execute", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：开票处理流程（4步：查询开票列表 → 查看详情 → 开具发票 → 通知） ==========
        {
            "id": "workflow_admin_invoice",
            "name": "管理员开票处理流程",
            "description": "处理开票申请",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["处理开票", "开票处理", "开具发票"],
            "trigger_keywords": ["处理开票", "开票处理", "开具发票"],
            "instruction_variants": ["处理开票", "开票处理", "开具发票", "审核开票", "喂，怎么处理开票", "帮我开票", "开票怎么办", "能开票吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理开票"}},
                {"id": "n_list", "name": "查询开票列表", "type": "api_call", "description": "查询待开票申请", "config": {"api_id": "api_admin_invoice_list", "api_endpoint": "/api/finance/admin/invoices", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "invoices", "type": "array", "description": "开票列表"}], "ai_instructions": {"user_message": "查询待开票申请", "action": "查询开票列表"}},
                {"id": "n_issue", "name": "开具发票", "type": "api_call", "description": "开具发票", "config": {"api_id": "api_admin_invoice_issue", "api_endpoint": "/api/finance/admin/invoices/{invoice_id}/issue", "method": "POST", "parameters": {"invoice_id": "${invoice_id}", "invoice_no": "${invoice_no}"}}, "outputs": [{"name": "invoice_url", "type": "string", "description": "发票链接"}], "ai_instructions": {"user_message": "请选择申请并填写发票号码", "action": "开具发票"}},
                {"id": "n_notify", "name": "开票通知", "type": "notification", "description": "发送开票完成通知", "config": {"message_template": "发票开具成功！发票ID${invoice_id}，发票号码：${invoice_no}。"}, "outputs": [], "ai_instructions": {"user_message": "开票完成", "action": "发送开票通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "开票处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_issue"}, {"source": "n_issue", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：费用审批流程（4步：查询费用列表 → 审批费用 → 确认 → 通知） ==========
        {
            "id": "workflow_admin_expense",
            "name": "管理员费用审批流程",
            "description": "审批费用申请",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["审批费用", "费用审批", "处理费用"],
            "trigger_keywords": ["审批费用", "费用审批", "处理费用"],
            "instruction_variants": ["审批费用", "费用审批", "处理费用", "审核费用", "喂，怎么审批费用", "帮我审费用", "费用怎么审", "能审批费用吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审批费用"}},
                {"id": "n_list", "name": "查询费用列表", "type": "api_call", "description": "查询待审批费用", "config": {"api_id": "api_admin_expense_list", "api_endpoint": "/api/finance/admin/expenses", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "expenses", "type": "array", "description": "费用列表"}], "ai_instructions": {"user_message": "查询待审批费用", "action": "查询费用列表"}},
                {"id": "n_approve", "name": "审批费用", "type": "api_call", "description": "审批费用申请", "config": {"api_id": "api_admin_expense_approve", "api_endpoint": "/api/finance/admin/expenses/{expense_id}/approve", "method": "POST", "parameters": {"expense_id": "${expense_id}", "result": "${result}", "remark": "${remark}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择费用并填写审批结果", "action": "审批费用"}},
                {"id": "n_notify", "name": "审批通知", "type": "notification", "description": "发送审批结果通知", "config": {"message_template": "费用审批完成！费用单号${expense_id}，审批结果：${result}。"}, "outputs": [], "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "费用审批完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_approve"}, {"source": "n_approve", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 用户：费用申请流程（5步：查询预算 → 选择类型 → 填写费用 → 提交 → 通知） ==========
        {
            "id": "workflow_expense_apply",
            "name": "费用申请流程",
            "description": "申请费用",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["费用申请", "申请费用", "费用报销"],
            "trigger_keywords": ["费用申请", "申请费用", "费用报销"],
            "instruction_variants": ["费用申请", "申请费用", "我要申请费用", "费用报销", "喂，怎么申请费用", "帮我申请费用", "费用怎么办", "能申请费用吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始费用申请"}},
                {"id": "n_budget", "name": "查询预算", "type": "api_call", "description": "查询部门预算", "config": {"api_id": "api_budget_query", "api_endpoint": "/api/finance/budgets", "method": "GET", "parameters": {"dept_id": "${dept_id}"}}, "outputs": [{"name": "total_budget", "type": "float", "description": "总预算"}, {"name": "used_budget", "type": "float", "description": "已用预算"}], "ai_instructions": {"user_message": "请输入部门ID查询预算", "action": "查询预算"}},
                {"id": "n_apply", "name": "提交费用", "type": "api_call", "description": "提交费用申请", "config": {"api_id": "api_expense_apply", "api_endpoint": "/api/finance/expenses", "method": "POST", "parameters": {"type": "${type}", "amount": "${amount}", "description": "${description}", "dept_id": "${dept_id}"}}, "outputs": [{"name": "expense_id", "type": "string", "description": "费用单号"}], "ai_instructions": {"user_message": "请填写费用信息", "action": "提交费用"}},
                {"id": "n_notify", "name": "费用通知", "type": "notification", "description": "发送费用申请通知", "config": {"message_template": "费用申请已提交！费用单号：${expense_id}，金额：${amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "费用已提交", "action": "发送费用通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "费用申请完成"}}
            ],
            "edges": [{"source": "start", "target": "n_budget"}, {"source": "n_budget", "target": "n_apply"}, {"source": "n_apply", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 用户：工资查询流程（3步：选择月份 → 查询工资 → 显示明细） ==========
        {
            "id": "workflow_salary_query",
            "name": "工资查询流程",
            "description": "查询工资明细",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["查工资", "工资查询", "查询工资"],
            "trigger_keywords": ["查工资", "工资查询", "查询工资"],
            "instruction_variants": ["查工资", "工资查询", "查询工资", "我的工资", "喂，帮我查查工资", "工资怎么查", "工资多少", "工资发了吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始查询工资"}},
                {"id": "n_query", "name": "查询工资", "type": "api_call", "description": "查询工资明细", "config": {"api_id": "api_salary_query", "api_endpoint": "/api/finance/salary", "method": "GET", "parameters": {"employee_id": "${employee_id}", "month": "${month}"}}, "outputs": [{"name": "salary", "type": "object", "description": "工资详情"}, {"name": "deductions", "type": "array", "description": "扣款明细"}], "ai_instructions": {"user_message": "请输入员工ID和月份", "action": "查询工资"}},
                {"id": "n_notify", "name": "工资通知", "type": "notification", "description": "显示工资明细", "config": {"message_template": "工资查询完成！基本工资：${salary.base}元，实发工资：${salary.actual}元。"}, "outputs": [], "ai_instructions": {"user_message": "工资查询完成", "action": "显示工资明细"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "工资查询完成"}}
            ],
            "edges": [{"source": "start", "target": "n_query"}, {"source": "n_query", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：预算编制流程（6步：查询历史 → 分析数据 → 编制预算 → 提交审批 → 审批 → 发布） ==========
        {
            "id": "workflow_admin_budget_plan",
            "name": "管理员预算编制流程",
            "description": "编制年度预算",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["编制预算", "预算编制", "制定预算"],
            "trigger_keywords": ["编制预算", "预算编制", "制定预算"],
            "instruction_variants": ["编制预算", "预算编制", "制定预算", "做预算", "喂，怎么编制预算", "帮我做预算", "预算怎么弄", "能编预算吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始编制预算"}},
                {"id": "n_history", "name": "查询历史预算", "type": "api_call", "description": "查询历史预算数据", "config": {"api_id": "api_budget_query", "api_endpoint": "/api/finance/budgets", "method": "GET", "parameters": {"year": "${last_year}"}}, "outputs": [{"name": "budgets", "type": "array", "description": "历史预算"}], "ai_instructions": {"user_message": "查询历史预算数据", "action": "查询历史预算"}},
                {"id": "n_analysis", "name": "费用分析", "type": "api_call", "description": "分析费用数据", "config": {"api_id": "api_admin_expense_analysis", "api_endpoint": "/api/finance/admin/stats/expense", "method": "GET", "parameters": {}}, "outputs": [{"name": "categories", "type": "array", "description": "费用类别"}], "ai_instructions": {"user_message": "分析费用数据", "action": "费用分析"}},
                {"id": "n_create", "name": "创建预算", "type": "form", "description": "填写预算信息", "config": {"fields": [{"name": "dept_id", "type": "string", "label": "部门ID", "required": True}, {"name": "year", "type": "string", "label": "年份", "required": True}, {"name": "amount", "type": "float", "label": "预算金额", "required": True}]}, "outputs": [{"name": "budget_data", "type": "object", "description": "预算数据"}], "ai_instructions": {"user_message": "请填写预算信息", "action": "创建预算"}},
                {"id": "n_notify", "name": "预算通知", "type": "notification", "description": "发送预算编制通知", "config": {"message_template": "预算编制完成！部门${dept_id}，${year}年预算：${amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "预算编制完成", "action": "发送预算通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "预算编制完成"}}
            ],
            "edges": [{"source": "start", "target": "n_history"}, {"source": "n_history", "target": "n_analysis"}, {"source": "n_analysis", "target": "n_create"}, {"source": "n_create", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：财务对账流程（5步：查询收入 → 查询支出 → 核对差异 → 调整 → 确认） ==========
        {
            "id": "workflow_admin_reconciliation",
            "name": "管理员财务对账流程",
            "description": "财务对账",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["财务对账", "对账", "账务核对"],
            "trigger_keywords": ["财务对账", "对账", "账务核对"],
            "instruction_variants": ["财务对账", "对账", "账务核对", "核对账务", "喂，怎么对账", "帮我对账", "对账怎么办", "能对账吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始财务对账"}},
                {"id": "n_overview", "name": "查询财务概览", "type": "api_call", "description": "查询财务概览", "config": {"api_id": "api_admin_finance_overview", "api_endpoint": "/api/finance/admin/stats/overview", "method": "GET", "parameters": {}}, "outputs": [{"name": "total_income", "type": "float", "description": "总收入"}, {"name": "monthly_trend", "type": "array", "description": "月度趋势"}], "ai_instructions": {"user_message": "查询财务概览", "action": "查询财务概览"}},
                {"id": "n_expense", "name": "查询费用分析", "type": "api_call", "description": "查询费用分析", "config": {"api_id": "api_admin_expense_analysis", "api_endpoint": "/api/finance/admin/stats/expense", "method": "GET", "parameters": {}}, "outputs": [{"name": "categories", "type": "array", "description": "费用类别"}], "ai_instructions": {"user_message": "查询费用分析", "action": "查询费用分析"}},
                {"id": "n_confirm", "name": "确认对账", "type": "form", "description": "确认对账结果", "config": {"fields": [{"name": "confirm", "type": "boolean", "label": "确认对账", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}]}, "outputs": [{"name": "confirm_result", "type": "boolean", "description": "确认结果"}], "ai_instructions": {"user_message": "请确认对账结果", "action": "确认对账"}},
                {"id": "n_notify", "name": "对账通知", "type": "notification", "description": "发送对账完成通知", "config": {"message_template": "财务对账完成！总收入：${total_income}元。"}, "outputs": [], "ai_instructions": {"user_message": "对账完成", "action": "发送对账通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "财务对账完成"}}
            ],
            "edges": [{"source": "start", "target": "n_overview"}, {"source": "n_overview", "target": "n_expense"}, {"source": "n_expense", "target": "n_confirm"}, {"source": "n_confirm", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },
        # ========== 管理员：工资发放流程（6步：查询员工 → 计算工资 → 审核 → 批量发放 → 生成凭证 → 通知） ==========
        {
            "id": "workflow_admin_salary_pay",
            "name": "管理员工资发放流程",
            "description": "批量发放工资",
            "business_scenario": "finance",
            "status": "active",
            "user_intents": ["发工资", "工资发放", "发放工资"],
            "trigger_keywords": ["发工资", "工资发放", "发放工资"],
            "instruction_variants": ["发工资", "工资发放", "发放工资", "批量发工资", "喂，怎么发工资", "帮我发工资", "工资怎么发", "能发工资吗"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始工资发放"}},
                {"id": "n_query", "name": "查询工资单", "type": "api_call", "description": "查询待发工资", "config": {"api_id": "api_salary_query", "api_endpoint": "/api/finance/salary", "method": "GET", "parameters": {"month": "${month}"}}, "outputs": [{"name": "salary_list", "type": "array", "description": "工资列表"}], "ai_instructions": {"user_message": "请输入发放月份", "action": "查询工资单"}},
                {"id": "n_review", "name": "审核工资", "type": "form", "description": "审核工资数据", "config": {"fields": [{"name": "confirm", "type": "boolean", "label": "确认审核", "required": True}]}, "outputs": [{"name": "review_result", "type": "boolean", "description": "审核结果"}], "ai_instructions": {"user_message": "请审核工资数据", "action": "审核工资"}},
                {"id": "n_pay", "name": "执行发放", "type": "form", "description": "执行工资发放", "config": {"fields": [{"name": "pay_date", "type": "string", "label": "发放日期", "required": True}]}, "outputs": [{"name": "pay_result", "type": "boolean", "description": "发放结果"}], "ai_instructions": {"user_message": "请确认发放日期", "action": "执行发放"}},
                {"id": "n_notify", "name": "发放通知", "type": "notification", "description": "发送工资发放通知", "config": {"message_template": "${month}月工资已发放完成！"}, "outputs": [], "ai_instructions": {"user_message": "工资发放完成", "action": "发送发放通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "工资发放完成"}}
            ],
            "edges": [{"source": "start", "target": "n_query"}, {"source": "n_query", "target": "n_review"}, {"source": "n_review", "target": "n_pay"}, {"source": "n_pay", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        }
    ]
}
