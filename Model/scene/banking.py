# banking.py - 银行场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

BANKING_SCENE = {
    "domain": "banking",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_account_query", "path": "/api/bank/accounts/{account_id}", "method": "GET", "desc": "查询账户",
         "instruction_variants": ["查询账户", "查看账户", "我的账户", "账户余额", "喂，我账户还有多少钱", "帮我查查账户", "账户信息", "余额多少"],
         "request": [{"name": "account_id", "type": "string", "label": "账户ID", "required": True}],
         "response": [{"name": "balance", "type": "float", "desc": "余额"}, {"name": "account_type", "type": "string", "desc": "账户类型"}, {"name": "account_name", "type": "string", "desc": "账户名称"}]},
        {"id": "api_account_list", "path": "/api/bank/accounts", "method": "GET", "desc": "查询账户列表",
         "instruction_variants": ["查询账户列表", "我的所有账户", "账户列表", "有哪些账户", "喂，我有几个账户", "帮我看看账户", "账户都有啥", "查看账户列表"],
         "request": [{"name": "customer_id", "type": "string", "label": "客户ID", "required": False}],
         "response": [{"name": "accounts", "type": "array", "desc": "账户列表"}]},
        {"id": "api_identity_verify", "workflow_only": True, "path": "/api/bank/identity/verify", "method": "POST", "desc": "身份验证",
         "instruction_variants": ["身份验证", "验证身份", "身份认证", "确认身份", "喂，怎么验证身份", "需要填什么信息", "身份怎么确认", "验证一下"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "phone", "type": "string", "label": "手机号", "required": True}],
         "response": [{"name": "customer_id", "type": "string", "desc": "客户ID"}, {"name": "verified", "type": "boolean", "desc": "是否验证通过"}]},
        {"id": "api_transfer_check", "workflow_only": True, "path": "/api/bank/transfers/check", "method": "POST", "desc": "转账预检查",
         "instruction_variants": ["转账预检查", "检查能不能转", "转账检查", "能转吗", "喂，这能转账吗", "帮我查查能不能转", "转账可以吗", "检查一下"],
         "request": [{"name": "from_account", "type": "string", "label": "转出账户", "required": True}, {"name": "to_account", "type": "string", "label": "转入账户", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}],
         "response": [{"name": "can_transfer", "type": "boolean", "desc": "是否可转账"}, {"name": "fee", "type": "float", "desc": "手续费"}, {"name": "to_name", "type": "string", "desc": "收款人姓名"}]},
        {"id": "api_transfer", "workflow_only": True, "path": "/api/bank/transfers", "method": "POST", "desc": "转账",
         "instruction_variants": ["转账", "我要转账", "汇款", "转钱", "喂，我想转账", "帮我转账", "转账怎么弄", "给别人转钱"],
         "request": [{"name": "from_account", "type": "string", "label": "转出账户", "required": True}, {"name": "to_account", "type": "string", "label": "转入账户", "required": True}, {"name": "to_name", "type": "string", "label": "收款人姓名", "required": True}, {"name": "to_bank", "type": "string", "label": "收款银行", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "transfer_id", "type": "string", "desc": "转账单号"}, {"name": "status", "type": "string", "desc": "转账状态"}]},
        {"id": "api_transfer_confirm", "workflow_only": True, "path": "/api/bank/transfers/{transfer_id}/confirm", "method": "POST", "desc": "转账确认",
         "instruction_variants": ["转账确认", "确认转账", "验证码确认", "输入验证码", "喂，验证码是多少", "帮我确认转账", "转账怎么确认", "确认一下"],
         "request": [{"name": "transfer_id", "type": "string", "label": "转账单号", "required": True}, {"name": "sms_code", "type": "string", "label": "短信验证码", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "new_balance", "type": "float", "desc": "转账后余额"}]},
        {"id": "api_transaction_query", "path": "/api/bank/transactions", "method": "GET", "desc": "查询交易记录",
         "instruction_variants": ["查询交易记录", "交易记录", "流水", "账单", "喂，我的交易记录呢", "帮我查查流水", "交易明细", "账单在哪"],
         "request": [{"name": "account_id", "type": "string", "label": "账户ID", "required": True}, {"name": "start_date", "type": "date", "label": "开始日期", "required": False}, {"name": "end_date", "type": "date", "label": "结束日期", "required": False}],
         "response": [{"name": "transactions", "type": "array", "desc": "交易记录"}]},
        {"id": "api_loan_products", "path": "/api/bank/loans/products", "method": "GET", "desc": "查询贷款产品",
         "instruction_variants": ["查询贷款产品", "贷款产品", "有哪些贷款", "贷款种类", "喂，能贷什么款", "帮我看看贷款", "贷款产品有啥", "贷款怎么选"],
         "request": [{"name": "loan_type", "type": "string", "label": "贷款类型", "required": False}],
         "response": [{"name": "products", "type": "array", "desc": "贷款产品列表"}]},
        {"id": "api_loan_calculate", "workflow_only": True, "path": "/api/bank/loans/calculate", "method": "POST", "desc": "贷款试算",
         "instruction_variants": ["贷款试算", "算算月供", "贷款计算", "月供多少", "喂，贷款要还多少", "帮我算算贷款", "利息多少", "试算一下"],
         "request": [{"name": "amount", "type": "float", "label": "贷款金额", "required": True}, {"name": "term", "type": "integer", "label": "期限(月)", "required": True}, {"name": "rate", "type": "float", "label": "利率", "required": False}],
         "response": [{"name": "monthly_payment", "type": "float", "desc": "月供"}, {"name": "total_interest", "type": "float", "desc": "总利息"}, {"name": "total_payment", "type": "float", "desc": "还款总额"}]},
        {"id": "api_loan_apply", "workflow_only": True, "path": "/api/bank/loans", "method": "POST", "desc": "贷款申请",
         "instruction_variants": ["贷款申请", "我要贷款", "申请贷款", "借钱", "喂，我想贷款", "帮我申请贷款", "贷款怎么办", "能贷款吗"],
         "request": [{"name": "loan_type", "type": "string", "label": "贷款类型", "required": True}, {"name": "amount", "type": "float", "label": "贷款金额", "required": True}, {"name": "term", "type": "integer", "label": "期限(月)", "required": True}, {"name": "purpose", "type": "string", "label": "用途", "required": True}],
         "response": [{"name": "loan_id", "type": "string", "desc": "贷款单号"}, {"name": "status", "type": "string", "desc": "申请状态"}]},
        {"id": "api_loan_query", "path": "/api/bank/loans/{loan_id}", "method": "GET", "desc": "查询贷款状态",
         "instruction_variants": ["查询贷款状态", "贷款进度", "我的贷款", "贷款状态", "喂，我的贷款怎么样了", "帮我查查贷款", "贷款审批了吗", "贷款到哪一步了"],
         "request": [{"name": "loan_id", "type": "string", "label": "贷款单号", "required": True}],
         "response": [{"name": "loan", "type": "object", "desc": "贷款详情"}, {"name": "status", "type": "string", "desc": "贷款状态"}]},
        {"id": "api_card_products", "path": "/api/bank/cards/products", "method": "GET", "desc": "查询银行卡产品",
         "instruction_variants": ["查询银行卡产品", "银行卡产品", "有哪些卡", "卡种类", "喂，能办什么卡", "帮我看看银行卡", "银行卡产品有啥", "卡怎么选"],
         "request": [{"name": "card_type", "type": "string", "label": "卡类型", "required": False}],
         "response": [{"name": "products", "type": "array", "desc": "银行卡产品列表"}]},
        {"id": "api_card_apply", "workflow_only": True, "path": "/api/bank/cards", "method": "POST", "desc": "申请银行卡",
         "instruction_variants": ["申请银行卡", "我要办卡", "办卡", "开卡", "喂，我想办张卡", "帮我申请银行卡", "办卡怎么弄", "能办卡吗"],
         "request": [{"name": "card_type", "type": "string", "label": "卡类型", "required": True}, {"name": "product_id", "type": "string", "label": "产品ID", "required": True}, {"name": "customer_id", "type": "string", "label": "客户ID", "required": True}],
         "response": [{"name": "application_id", "type": "string", "desc": "申请单号"}, {"name": "status", "type": "string", "desc": "申请状态"}]},
        {"id": "api_card_loss", "workflow_only": True, "path": "/api/bank/cards/{card_id}/loss", "method": "POST", "desc": "银行卡挂失",
         "instruction_variants": ["银行卡挂失", "挂失", "卡丢了", "卡不见了", "喂，我的卡丢了", "帮我挂失", "挂失怎么办", "卡被偷了"],
         "request": [{"name": "card_id", "type": "string", "label": "卡号", "required": True}, {"name": "reason", "type": "string", "label": "挂失原因", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "temp_card", "type": "string", "desc": "临时卡号"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_transfer_list", "workflow_only": True, "path": "/api/bank/admin/transfers", "method": "GET", "desc": "查询大额转账列表",
         "instruction_variants": ["查询大额转账列表", "大额转账", "待审批转账", "转账列表", "喂，有哪些大额转账", "帮我看看转账", "转账审批列表", "待审批的转账"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "min_amount", "type": "float", "label": "最小金额", "required": False}],
         "response": [{"name": "transfers", "type": "array", "desc": "转账列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数量"}]},
        {"id": "api_admin_transfer_detail", "workflow_only": True, "path": "/api/bank/admin/transfers/{transfer_id}", "method": "GET", "desc": "查询转账详情",
         "instruction_variants": ["查询转账详情", "转账详细信息", "转账详情", "这笔转账", "喂，这转账是谁的", "帮我看看这转账", "转账信息", "转账内容"],
         "request": [{"name": "transfer_id", "type": "string", "label": "转账单号", "required": True}],
         "response": [{"name": "transfer", "type": "object", "desc": "转账详情"}, {"name": "from_account", "type": "object", "desc": "转出账户信息"}, {"name": "to_account", "type": "object", "desc": "转入账户信息"}]},
        {"id": "api_admin_transfer_approve", "workflow_only": True, "path": "/api/bank/admin/transfers/{transfer_id}/approve", "method": "POST", "desc": "审批大额转账",
         "instruction_variants": ["审批大额转账", "审批转账", "通过转账", "拒绝转账", "喂，这转账批不批", "帮我审批转账", "转账审批", "审批一下"],
         "request": [{"name": "transfer_id", "type": "string", "label": "转账单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_loan_list", "workflow_only": True, "path": "/api/bank/admin/loans", "method": "GET", "desc": "查询贷款申请列表",
         "instruction_variants": ["查询贷款申请列表", "贷款申请", "待审批贷款", "贷款列表", "喂，有哪些贷款要审", "帮我看看贷款", "贷款审批列表", "待审批的贷款"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "loan_type", "type": "string", "label": "贷款类型", "required": False}],
         "response": [{"name": "loans", "type": "array", "desc": "贷款列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数量"}, {"name": "total_amount", "type": "float", "desc": "待审批总金额"}]},
        {"id": "api_admin_loan_detail", "workflow_only": True, "path": "/api/bank/admin/loans/{loan_id}", "method": "GET", "desc": "查询贷款详情",
         "instruction_variants": ["查询贷款详情", "贷款详细信息", "贷款详情", "这笔贷款", "喂，这贷款是谁的", "帮我看看这贷款", "贷款信息", "贷款内容"],
         "request": [{"name": "loan_id", "type": "string", "label": "贷款单号", "required": True}],
         "response": [{"name": "loan", "type": "object", "desc": "贷款详情"}, {"name": "customer", "type": "object", "desc": "客户信息"}, {"name": "credit_score", "type": "integer", "desc": "信用评分"}]},
        {"id": "api_admin_loan_risk_assess", "workflow_only": True, "path": "/api/bank/admin/loans/{loan_id}/risk", "method": "POST", "desc": "贷款风险评估",
         "instruction_variants": ["贷款风险评估", "风险评估", "评估风险", "风险分析", "喂，这贷款风险大吗", "帮我评估风险", "风险怎么样", "评估一下"],
         "request": [{"name": "loan_id", "type": "string", "label": "贷款单号", "required": True}],
         "response": [{"name": "risk_level", "type": "string", "desc": "风险等级"}, {"name": "risk_score", "type": "integer", "desc": "风险评分"}, {"name": "suggestion", "type": "string", "desc": "建议"}]},
        {"id": "api_admin_loan_approve", "workflow_only": True, "path": "/api/bank/admin/loans/{loan_id}/approve", "method": "POST", "desc": "审批贷款",
         "instruction_variants": ["审批贷款", "贷款审批", "通过贷款", "拒绝贷款", "喂，这贷款批不批", "帮我审批贷款", "贷款批准", "审批一下"],
         "request": [{"name": "loan_id", "type": "string", "label": "贷款单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "approved_amount", "type": "float", "label": "批准金额", "required": False}, {"name": "approved_rate", "type": "float", "label": "批准利率", "required": False}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "loan_id", "type": "string", "desc": "贷款单号"}]},
        {"id": "api_admin_loan_disburse", "workflow_only": True, "path": "/api/bank/admin/loans/{loan_id}/disburse", "method": "POST", "desc": "贷款放款",
         "instruction_variants": ["贷款放款", "放款", "发放贷款", "打款", "喂，这贷款可以放了", "帮我放款", "放款怎么办", "执行放款"],
         "request": [{"name": "loan_id", "type": "string", "label": "贷款单号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "disburse_time", "type": "datetime", "desc": "放款时间"}]},
        {"id": "api_admin_card_list", "workflow_only": True, "path": "/api/bank/admin/cards", "method": "GET", "desc": "查询银行卡申请列表",
         "instruction_variants": ["查询银行卡申请列表", "银行卡申请", "待审批银行卡", "办卡申请", "喂，有哪些办卡要审", "帮我看看办卡", "银行卡审批列表", "待审批的办卡"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "card_type", "type": "string", "label": "卡类型", "required": False}],
         "response": [{"name": "applications", "type": "array", "desc": "申请列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数量"}]},
        {"id": "api_admin_card_detail", "workflow_only": True, "path": "/api/bank/admin/cards/{application_id}", "method": "GET", "desc": "查询银行卡申请详情",
         "instruction_variants": ["查询银行卡申请详情", "办卡详细信息", "办卡详情", "这个办卡", "喂，这办卡是谁的", "帮我看看这办卡", "办卡信息", "申请内容"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}],
         "response": [{"name": "application", "type": "object", "desc": "申请详情"}, {"name": "customer", "type": "object", "desc": "客户信息"}]},
        {"id": "api_admin_card_approve", "workflow_only": True, "path": "/api/bank/admin/cards/{application_id}/approve", "method": "POST", "desc": "审批银行卡申请",
         "instruction_variants": ["审批银行卡申请", "审批办卡", "通过办卡", "拒绝办卡", "喂，这办卡批不批", "帮我审批办卡", "办卡审批", "审批一下"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "credit_limit", "type": "float", "label": "信用额度", "required": False}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_card_issue", "workflow_only": True, "path": "/api/bank/admin/cards/{application_id}/issue", "method": "POST", "desc": "制卡发卡",
         "instruction_variants": ["制卡发卡", "发卡", "制卡", "发放银行卡", "喂，这卡可以发了", "帮我发卡", "发卡怎么办", "制作银行卡"],
         "request": [{"name": "application_id", "type": "string", "label": "申请单号", "required": True}],
         "response": [{"name": "card_number", "type": "string", "desc": "卡号"}, {"name": "issue_time", "type": "datetime", "desc": "发卡时间"}]},
        {"id": "api_admin_customer_list", "workflow_only": True, "path": "/api/bank/admin/customers", "method": "GET", "desc": "查询客户列表",
         "instruction_variants": ["查询客户列表", "客户列表", "所有客户", "客户管理", "喂，有哪些客户", "帮我看看客户", "客户都有谁", "客户名单"],
         "request": [{"name": "level", "type": "string", "label": "客户等级", "required": False}],
         "response": [{"name": "customers", "type": "array", "desc": "客户列表"}]},
        {"id": "api_admin_customer_detail", "workflow_only": True, "path": "/api/bank/admin/customers/{customer_id}", "method": "GET", "desc": "查询客户详情",
         "instruction_variants": ["查询客户详情", "客户详细信息", "客户详情", "这个客户", "喂，这客户什么情况", "帮我看看这客户", "客户信息", "客户资产"],
         "request": [{"name": "customer_id", "type": "string", "label": "客户ID", "required": True}],
         "response": [{"name": "customer", "type": "object", "desc": "客户详情"}, {"name": "accounts", "type": "array", "desc": "账户列表"}, {"name": "total_assets", "type": "float", "desc": "总资产"}]},
        {"id": "api_admin_risk_alert_list", "workflow_only": True, "path": "/api/bank/admin/risk/alerts", "method": "GET", "desc": "查询风险预警列表",
         "instruction_variants": ["查询风险预警列表", "风险预警", "风险警报", "预警列表", "喂，有哪些风险", "帮我看看风险", "风险情况", "高风险有哪些"],
         "request": [{"name": "level", "type": "string", "label": "风险等级", "required": False}],
         "response": [{"name": "alerts", "type": "array", "desc": "预警列表"}, {"name": "high_risk_count", "type": "integer", "desc": "高风险数量"}]},
        {"id": "api_admin_risk_alert_handle", "workflow_only": True, "path": "/api/bank/admin/risk/alerts/{alert_id}/handle", "method": "POST", "desc": "处理风险预警",
         "instruction_variants": ["处理风险预警", "处理风险", "风险处理", "解决风险", "喂，这风险怎么处理", "帮我处理风险", "风险怎么办", "处理一下"],
         "request": [{"name": "alert_id", "type": "string", "label": "预警ID", "required": True}, {"name": "action", "type": "string", "label": "处理动作", "required": True}, {"name": "comment", "type": "string", "label": "处理意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        # ========== 管理员统计 API ==========
        {"id": "api_admin_transaction_stats", "path": "/api/bank/admin/transaction/stats", "method": "GET", "desc": "查询交易统计", "name": "交易统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询交易统计", "交易统计", "交易数据", "交易分析", "喂，今天交易多少", "帮我看看交易", "交易情况", "交易量怎么样"],
         "request": [], "response": [{"name": "today_amount", "type": "float", "desc": "今日交易额"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_loan_analysis", "path": "/api/bank/admin/loan/analysis", "method": "GET", "desc": "查询贷款分析", "name": "贷款分析", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询贷款分析", "贷款分析", "贷款数据", "贷款统计", "喂，贷款情况怎么样", "帮我看看贷款数据", "贷款分布", "贷款类型分析"],
         "request": [], "response": [{"name": "types", "type": "array", "desc": "贷款类型"}, {"name": "amounts", "type": "array", "desc": "金额"}]},
        {"id": "api_admin_customer_stats", "path": "/api/bank/admin/customer/stats", "method": "GET", "desc": "查询客户统计", "name": "客户统计", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询客户统计", "客户统计", "客户数据", "客户分析", "喂，客户情况怎么样", "帮我看看客户数据", "客户分布", "客户等级统计"],
         "request": [], "response": [{"name": "levels", "type": "array", "desc": "客户等级"}, {"name": "counts", "type": "array", "desc": "数量"}]},
    ],

    "workflows": [
        # ========== 用户：完整转账流程（7步：身份验证 → 查询账户 → 转账检查 → 填写转账 → 短信验证 → 确认转账 → 通知） ==========
        {
            "id": "workflow_full_transfer",
            "name": "完整转账流程",
            "description": "完整的银行转账流程，包括身份验证、余额查询、转账检查、短信验证和转账确认",
            "instruction_variants": ["完整转账流程", "我要转账", "转账", "汇款", "喂，我想转账", "帮我转账", "转钱", "转账怎么办"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["转账", "汇款", "转钱"],
            "trigger_keywords": ["转账", "汇款", "转钱"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始转账"}},
                {
                    "id": "n_verify",
                    "name": "身份验证",
                    "type": "api_call",
                    "description": "验证用户身份",
                    "config": {"api_id": "api_identity_verify", "api_endpoint": "/api/bank/identity/verify", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "phone": "${phone}"}},
                    "outputs": [{"name": "customer_id", "type": "string", "description": "客户ID"}, {"name": "verified", "type": "boolean", "description": "是否验证通过"}],
                    "ai_instructions": {"user_message": "请填写身份信息进行验证", "action": "身份验证"}
                },
                {
                    "id": "n_query_balance",
                    "name": "查询余额",
                    "type": "api_call",
                    "description": "查询转出账户余额",
                    "config": {"api_id": "api_account_query", "api_endpoint": "/api/bank/accounts/{account_id}", "method": "GET", "parameters": {"account_id": "${from_account}"}},
                    "outputs": [{"name": "balance", "type": "float", "description": "余额"}, {"name": "from_account", "type": "string", "description": "转出账户"}, {"name": "account_name", "type": "string", "description": "账户名称"}],
                    "ai_instructions": {"user_message": "请选择转出账户", "action": "查询账户余额"}
                },
                {
                    "id": "n_transfer_check",
                    "name": "转账检查",
                    "type": "api_call",
                    "description": "检查转账是否可行",
                    "config": {"api_id": "api_transfer_check", "api_endpoint": "/api/bank/transfers/check", "method": "POST", "parameters": {"from_account": "${from_account}", "to_account": "${to_account}", "amount": "${amount}"}},
                    "outputs": [{"name": "can_transfer", "type": "boolean", "description": "是否可转账"}, {"name": "fee", "type": "float", "description": "手续费"}, {"name": "to_name", "type": "string", "description": "收款人姓名"}],
                    "ai_instructions": {"user_message": "请输入收款账户和金额", "action": "转账检查"}
                },
                {
                    "id": "n_transfer",
                    "name": "执行转账",
                    "type": "api_call",
                    "description": "填写转账信息并执行",
                    "config": {"api_id": "api_transfer", "api_endpoint": "/api/bank/transfers", "method": "POST", "parameters": {"from_account": "${from_account}", "to_account": "${to_account}", "to_name": "${to_name}", "to_bank": "${to_bank}", "amount": "${amount}", "remark": "${remark}"}},
                    "outputs": [{"name": "transfer_id", "type": "string", "description": "转账单号"}, {"name": "status", "type": "string", "description": "转账状态"}],
                    "ai_instructions": {"user_message": "请确认转账信息", "action": "执行转账"}
                },
                {
                    "id": "n_confirm",
                    "name": "短信验证确认",
                    "type": "api_call",
                    "description": "输入短信验证码确认转账",
                    "config": {"api_id": "api_transfer_confirm", "api_endpoint": "/api/bank/transfers/{transfer_id}/confirm", "method": "POST", "parameters": {"transfer_id": "${transfer_id}", "sms_code": "${sms_code}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "new_balance", "type": "float", "description": "转账后余额"}],
                    "ai_instructions": {"user_message": "请输入短信验证码确认转账", "action": "短信验证确认"}
                },
                {
                    "id": "n_notify",
                    "name": "转账通知",
                    "type": "notification",
                    "description": "发送转账成功通知",
                    "config": {"message_template": "转账成功！转账单号：${transfer_id}，转账金额：${amount}元，收款人：${to_name}，手续费：${fee}元，账户余额：${new_balance}元。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "转账成功", "action": "发送转账通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "转账完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_verify"},
                {"source": "n_verify", "target": "n_query_balance"},
                {"source": "n_query_balance", "target": "n_transfer_check"},
                {"source": "n_transfer_check", "target": "n_transfer"},
                {"source": "n_transfer", "target": "n_confirm"},
                {"source": "n_confirm", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：贷款申请流程（6步：查询产品 → 贷款试算 → 身份验证 → 提交申请 → 等待审批 → 通知） ==========
        {
            "id": "workflow_loan_apply",
            "name": "贷款申请流程",
            "description": "完整的贷款申请流程，包括产品查询、贷款试算、身份验证和申请提交",
            "instruction_variants": ["贷款申请流程", "我要贷款", "申请贷款", "借钱", "喂，我想贷款", "帮我申请贷款", "贷款", "贷款怎么办"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["贷款", "申请贷款", "借钱"],
            "trigger_keywords": ["贷款", "申请贷款", "借钱"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始贷款申请"}},
                {
                    "id": "n_products",
                    "name": "查询贷款产品",
                    "type": "api_call",
                    "description": "查询可选的贷款产品",
                    "config": {"api_id": "api_loan_products", "api_endpoint": "/api/bank/loans/products", "method": "GET", "parameters": {"loan_type": "${loan_type}"}},
                    "outputs": [{"name": "products", "type": "array", "description": "贷款产品列表"}, {"name": "loan_type", "type": "string", "description": "选中的贷款类型"}],
                    "ai_instructions": {"user_message": "请选择贷款类型", "action": "查询贷款产品"}
                },
                {
                    "id": "n_calculate",
                    "name": "贷款试算",
                    "type": "api_call",
                    "description": "计算月供和利息",
                    "config": {"api_id": "api_loan_calculate", "api_endpoint": "/api/bank/loans/calculate", "method": "POST", "parameters": {"amount": "${amount}", "term": "${term}", "rate": "${rate}"}},
                    "outputs": [{"name": "monthly_payment", "type": "float", "description": "月供"}, {"name": "total_interest", "type": "float", "description": "总利息"}, {"name": "total_payment", "type": "float", "description": "还款总额"}],
                    "ai_instructions": {"user_message": "请输入贷款金额和期限进行试算", "action": "贷款试算"}
                },
                {
                    "id": "n_verify",
                    "name": "身份验证",
                    "type": "api_call",
                    "description": "验证申请人身份",
                    "config": {"api_id": "api_identity_verify", "api_endpoint": "/api/bank/identity/verify", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "phone": "${phone}"}},
                    "outputs": [{"name": "customer_id", "type": "string", "description": "客户ID"}, {"name": "verified", "type": "boolean", "description": "是否验证通过"}],
                    "ai_instructions": {"user_message": "请填写身份信息进行验证", "action": "身份验证"}
                },
                {
                    "id": "n_apply",
                    "name": "提交贷款申请",
                    "type": "api_call",
                    "description": "提交贷款申请",
                    "config": {"api_id": "api_loan_apply", "api_endpoint": "/api/bank/loans", "method": "POST", "parameters": {"loan_type": "${loan_type}", "amount": "${amount}", "term": "${term}", "purpose": "${purpose}"}},
                    "outputs": [{"name": "loan_id", "type": "string", "description": "贷款单号"}, {"name": "status", "type": "string", "description": "申请状态"}],
                    "ai_instructions": {"user_message": "请填写贷款用途并确认申请", "action": "提交贷款申请"}
                },
                {
                    "id": "n_notify",
                    "name": "申请提交通知",
                    "type": "notification",
                    "description": "发送贷款申请提交成功通知",
                    "config": {"message_template": "贷款申请已提交！申请单号：${loan_id}，申请金额：${amount}元，期限：${term}个月，预计月供：${monthly_payment}元，请等待审批。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "贷款申请已提交", "action": "发送申请通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "贷款申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_products"},
                {"source": "n_products", "target": "n_calculate"},
                {"source": "n_calculate", "target": "n_verify"},
                {"source": "n_verify", "target": "n_apply"},
                {"source": "n_apply", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：银行卡申请流程（5步：查询产品 → 身份验证 → 提交申请 → 等待审批 → 通知） ==========
        {
            "id": "workflow_card_apply",
            "name": "银行卡申请流程",
            "description": "完整的银行卡申请流程，包括产品查询、身份验证和申请提交",
            "instruction_variants": ["银行卡申请流程", "我要办卡", "办卡", "申请银行卡", "喂，我想办卡", "帮我办卡", "开卡", "信用卡"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["办卡", "申请银行卡", "开卡", "信用卡"],
            "trigger_keywords": ["办卡", "申请银行卡", "开卡", "信用卡"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始申请银行卡"}},
                {
                    "id": "n_products",
                    "name": "查询银行卡产品",
                    "type": "api_call",
                    "description": "查询可选的银行卡产品",
                    "config": {"api_id": "api_card_products", "api_endpoint": "/api/bank/cards/products", "method": "GET", "parameters": {"card_type": "${card_type}"}},
                    "outputs": [{"name": "products", "type": "array", "description": "银行卡产品列表"}, {"name": "product_id", "type": "string", "description": "选中的产品ID"}, {"name": "card_type", "type": "string", "description": "卡类型"}],
                    "ai_instructions": {"user_message": "请选择银行卡类型", "action": "查询银行卡产品"}
                },
                {
                    "id": "n_verify",
                    "name": "身份验证",
                    "type": "api_call",
                    "description": "验证申请人身份",
                    "config": {"api_id": "api_identity_verify", "api_endpoint": "/api/bank/identity/verify", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "phone": "${phone}"}},
                    "outputs": [{"name": "customer_id", "type": "string", "description": "客户ID"}, {"name": "verified", "type": "boolean", "description": "是否验证通过"}],
                    "ai_instructions": {"user_message": "请填写身份信息进行验证", "action": "身份验证"}
                },
                {
                    "id": "n_apply",
                    "name": "提交申请",
                    "type": "api_call",
                    "description": "提交银行卡申请",
                    "config": {"api_id": "api_card_apply", "api_endpoint": "/api/bank/cards", "method": "POST", "parameters": {"card_type": "${card_type}", "product_id": "${product_id}", "customer_id": "${customer_id}"}},
                    "outputs": [{"name": "application_id", "type": "string", "description": "申请单号"}, {"name": "status", "type": "string", "description": "申请状态"}],
                    "ai_instructions": {"user_message": "请确认申请信息", "action": "提交申请"}
                },
                {
                    "id": "n_notify",
                    "name": "申请提交通知",
                    "type": "notification",
                    "description": "发送银行卡申请提交成功通知",
                    "config": {"message_template": "银行卡申请已提交！申请单号：${application_id}，卡类型：${card_type}，请等待审批，预计3-5个工作日。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "申请已提交", "action": "发送申请通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "银行卡申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_products"},
                {"source": "n_products", "target": "n_verify"},
                {"source": "n_verify", "target": "n_apply"},
                {"source": "n_apply", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 用户：银行卡挂失流程（4步：身份验证 → 挂失 → 临时卡 → 通知） ==========
        {
            "id": "workflow_card_loss",
            "name": "银行卡挂失流程",
            "description": "银行卡挂失流程，包括身份验证和挂失办理",
            "instruction_variants": ["银行卡挂失流程", "挂失", "卡丢了", "银行卡挂失", "喂，我的卡丢了", "帮我挂失", "卡不见了", "挂失怎么办"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["挂失", "银行卡挂失", "卡丢了"],
            "trigger_keywords": ["挂失", "银行卡挂失", "卡丢了"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始挂失"}},
                {
                    "id": "n_verify",
                    "name": "身份验证",
                    "type": "api_call",
                    "description": "验证持卡人身份",
                    "config": {"api_id": "api_identity_verify", "api_endpoint": "/api/bank/identity/verify", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "phone": "${phone}"}},
                    "outputs": [{"name": "customer_id", "type": "string", "description": "客户ID"}, {"name": "verified", "type": "boolean", "description": "是否验证通过"}],
                    "ai_instructions": {"user_message": "请填写身份信息进行验证", "action": "身份验证"}
                },
                {
                    "id": "n_loss",
                    "name": "银行卡挂失",
                    "type": "api_call",
                    "description": "办理银行卡挂失",
                    "config": {"api_id": "api_card_loss", "api_endpoint": "/api/bank/cards/{card_id}/loss", "method": "POST", "parameters": {"card_id": "${card_id}", "reason": "${reason}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "temp_card", "type": "string", "description": "临时卡号"}],
                    "ai_instructions": {"user_message": "请输入卡号和挂失原因", "action": "银行卡挂失"}
                },
                {
                    "id": "n_notify",
                    "name": "挂失通知",
                    "type": "notification",
                    "description": "发送挂失成功通知",
                    "config": {"message_template": "银行卡挂失成功！卡号：${card_id}已冻结，临时卡号：${temp_card}，请尽快到网点补办新卡。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "挂失成功", "action": "发送挂失通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "挂失完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_verify"},
                {"source": "n_verify", "target": "n_loss"},
                {"source": "n_loss", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：大额转账审批流程（5步：查询待审批 → 查看详情 → 风险检查 → 审批 → 通知） ==========
        {
            "id": "workflow_admin_transfer_approve",
            "name": "大额转账审批流程",
            "description": "管理员大额转账审批流程，包括待审批列表查询、详情查看和审批决定",
            "instruction_variants": ["大额转账审批流程", "审批转账", "转账审批", "大额转账", "喂，有转账要审", "帮我审批转账", "转账审批流程", "审批大额转账"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["审批转账", "转账审批", "大额转账"],
            "trigger_keywords": ["审批转账", "转账审批", "大额转账"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始转账审批"}},
                {
                    "id": "n_transfer_list",
                    "name": "查询待审批转账",
                    "type": "api_call",
                    "description": "查询待审批的大额转账列表",
                    "config": {"api_id": "api_admin_transfer_list", "api_endpoint": "/api/bank/admin/transfers", "method": "GET", "parameters": {"status": "pending", "min_amount": "${min_amount}"}},
                    "outputs": [{"name": "transfers", "type": "array", "description": "转账列表"}, {"name": "pending_count", "type": "integer", "description": "待审批数量"}],
                    "ai_instructions": {"user_message": "正在查询待审批的大额转账", "action": "查询待审批转账"}
                },
                {
                    "id": "n_transfer_detail",
                    "name": "查看转账详情",
                    "type": "api_call",
                    "description": "查看转账详细信息",
                    "config": {"api_id": "api_admin_transfer_detail", "api_endpoint": "/api/bank/admin/transfers/{transfer_id}", "method": "GET", "parameters": {"transfer_id": "${transfer_id}"}},
                    "outputs": [{"name": "transfer", "type": "object", "description": "转账详情"}, {"name": "from_account", "type": "object", "description": "转出账户信息"}, {"name": "to_account", "type": "object", "description": "转入账户信息"}],
                    "ai_instructions": {"user_message": "请选择要审批的转账", "action": "查看转账详情"}
                },
                {
                    "id": "n_approve",
                    "name": "审批转账",
                    "type": "api_call",
                    "description": "对大额转账进行审批",
                    "config": {"api_id": "api_admin_transfer_approve", "api_endpoint": "/api/bank/admin/transfers/{transfer_id}/approve", "method": "POST", "parameters": {"transfer_id": "${transfer_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择审批动作并填写审批意见", "action": "审批转账"}
                },
                {
                    "id": "n_notify",
                    "name": "审批结果通知",
                    "type": "notification",
                    "description": "发送审批结果通知",
                    "config": {"message_template": "大额转账审批完成！转账单号：${transfer_id}，审批结果已通知客户。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "转账审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_transfer_list"},
                {"source": "n_transfer_list", "target": "n_transfer_detail"},
                {"source": "n_transfer_detail", "target": "n_approve"},
                {"source": "n_approve", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：贷款审批流程（7步：查询待审批 → 查看详情 → 风险评估 → 审批决定 → 放款 → 通知） ==========
        {
            "id": "workflow_admin_loan_approve",
            "name": "贷款审批流程",
            "description": "管理员贷款审批流程，包括待审批列表查询、详情查看、风险评估、审批决定和放款",
            "instruction_variants": ["贷款审批流程", "审批贷款", "贷款审批", "处理贷款", "喂，有贷款要审", "帮我审批贷款", "贷款审批流程", "审批贷款申请"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["审批贷款", "贷款审批", "处理贷款"],
            "trigger_keywords": ["审批贷款", "贷款审批"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始贷款审批"}},
                {
                    "id": "n_loan_list",
                    "name": "查询待审批贷款",
                    "type": "api_call",
                    "description": "查询待审批的贷款申请列表",
                    "config": {"api_id": "api_admin_loan_list", "api_endpoint": "/api/bank/admin/loans", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "loans", "type": "array", "description": "贷款列表"}, {"name": "pending_count", "type": "integer", "description": "待审批数量"}, {"name": "total_amount", "type": "float", "description": "待审批总金额"}],
                    "ai_instructions": {"user_message": "正在查询待审批的贷款申请", "action": "查询待审批贷款"}
                },
                {
                    "id": "n_loan_detail",
                    "name": "查看贷款详情",
                    "type": "api_call",
                    "description": "查看贷款申请详细信息",
                    "config": {"api_id": "api_admin_loan_detail", "api_endpoint": "/api/bank/admin/loans/{loan_id}", "method": "GET", "parameters": {"loan_id": "${loan_id}"}},
                    "outputs": [{"name": "loan", "type": "object", "description": "贷款详情"}, {"name": "customer", "type": "object", "description": "客户信息"}, {"name": "credit_score", "type": "integer", "description": "信用评分"}],
                    "ai_instructions": {"user_message": "请选择要审批的贷款申请", "action": "查看贷款详情"}
                },
                {
                    "id": "n_risk_assess",
                    "name": "风险评估",
                    "type": "api_call",
                    "description": "进行贷款风险评估",
                    "config": {"api_id": "api_admin_loan_risk_assess", "api_endpoint": "/api/bank/admin/loans/{loan_id}/risk", "method": "POST", "parameters": {"loan_id": "${loan_id}"}},
                    "outputs": [{"name": "risk_level", "type": "string", "description": "风险等级"}, {"name": "risk_score", "type": "integer", "description": "风险评分"}, {"name": "suggestion", "type": "string", "description": "建议"}],
                    "ai_instructions": {"user_message": "正在进行风险评估", "action": "风险评估"}
                },
                {
                    "id": "n_approve",
                    "name": "审批贷款",
                    "type": "api_call",
                    "description": "对贷款申请进行审批",
                    "config": {"api_id": "api_admin_loan_approve", "api_endpoint": "/api/bank/admin/loans/{loan_id}/approve", "method": "POST", "parameters": {"loan_id": "${loan_id}", "action": "${action}", "approved_amount": "${approved_amount}", "approved_rate": "${approved_rate}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "loan_id", "type": "string", "description": "贷款单号"}],
                    "ai_instructions": {"user_message": "请选择审批动作、批准金额和利率", "action": "审批贷款"}
                },
                {
                    "id": "n_disburse",
                    "name": "贷款放款",
                    "type": "api_call",
                    "description": "执行贷款放款",
                    "config": {"api_id": "api_admin_loan_disburse", "api_endpoint": "/api/bank/admin/loans/{loan_id}/disburse", "method": "POST", "parameters": {"loan_id": "${loan_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "disburse_time", "type": "datetime", "description": "放款时间"}],
                    "ai_instructions": {"user_message": "正在执行放款", "action": "贷款放款"}
                },
                {
                    "id": "n_notify",
                    "name": "审批结果通知",
                    "type": "notification",
                    "description": "发送审批结果通知",
                    "config": {"message_template": "贷款审批完成！贷款单号：${loan_id}，批准金额：${approved_amount}元，已放款，审批结果已通知客户。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "贷款审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_loan_list"},
                {"source": "n_loan_list", "target": "n_loan_detail"},
                {"source": "n_loan_detail", "target": "n_risk_assess"},
                {"source": "n_risk_assess", "target": "n_approve"},
                {"source": "n_approve", "target": "n_disburse"},
                {"source": "n_disburse", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：银行卡审批发卡流程（6步：查询待审批 → 查看详情 → 审批 → 制卡 → 发卡 → 通知） ==========
        {
            "id": "workflow_admin_card_approve",
            "name": "银行卡审批发卡流程",
            "description": "管理员银行卡审批发卡流程，包括待审批列表查询、详情查看、审批决定和制卡发卡",
            "instruction_variants": ["银行卡审批发卡流程", "审批银行卡", "银行卡审批", "发卡", "喂，有办卡要审", "帮我审批办卡", "办卡审批流程", "审批发卡"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["审批银行卡", "银行卡审批", "发卡"],
            "trigger_keywords": ["审批银行卡", "银行卡审批", "发卡"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始银行卡审批"}},
                {
                    "id": "n_card_list",
                    "name": "查询待审批申请",
                    "type": "api_call",
                    "description": "查询待审批的银行卡申请列表",
                    "config": {"api_id": "api_admin_card_list", "api_endpoint": "/api/bank/admin/cards", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "applications", "type": "array", "description": "申请列表"}, {"name": "pending_count", "type": "integer", "description": "待审批数量"}],
                    "ai_instructions": {"user_message": "正在查询待审批的银行卡申请", "action": "查询待审批申请"}
                },
                {
                    "id": "n_card_detail",
                    "name": "查看申请详情",
                    "type": "api_call",
                    "description": "查看银行卡申请详细信息",
                    "config": {"api_id": "api_admin_card_detail", "api_endpoint": "/api/bank/admin/cards/{application_id}", "method": "GET", "parameters": {"application_id": "${application_id}"}},
                    "outputs": [{"name": "application", "type": "object", "description": "申请详情"}, {"name": "customer", "type": "object", "description": "客户信息"}],
                    "ai_instructions": {"user_message": "请选择要审批的申请", "action": "查看申请详情"}
                },
                {
                    "id": "n_approve",
                    "name": "审批申请",
                    "type": "api_call",
                    "description": "对银行卡申请进行审批",
                    "config": {"api_id": "api_admin_card_approve", "api_endpoint": "/api/bank/admin/cards/{application_id}/approve", "method": "POST", "parameters": {"application_id": "${application_id}", "action": "${action}", "credit_limit": "${credit_limit}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择审批动作和信用额度", "action": "审批申请"}
                },
                {
                    "id": "n_issue",
                    "name": "制卡发卡",
                    "type": "api_call",
                    "description": "制作并发放银行卡",
                    "config": {"api_id": "api_admin_card_issue", "api_endpoint": "/api/bank/admin/cards/{application_id}/issue", "method": "POST", "parameters": {"application_id": "${application_id}"}},
                    "outputs": [{"name": "card_number", "type": "string", "description": "卡号"}, {"name": "issue_time", "type": "datetime", "description": "发卡时间"}],
                    "ai_instructions": {"user_message": "正在制卡发卡", "action": "制卡发卡"}
                },
                {
                    "id": "n_notify",
                    "name": "发卡通知",
                    "type": "notification",
                    "description": "发送发卡成功通知",
                    "config": {"message_template": "银行卡已发放！卡号：${card_number}，信用额度：${credit_limit}元，已通知客户领取。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "发卡完成", "action": "发送发卡通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "银行卡审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_card_list"},
                {"source": "n_card_list", "target": "n_card_detail"},
                {"source": "n_card_detail", "target": "n_approve"},
                {"source": "n_approve", "target": "n_issue"},
                {"source": "n_issue", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },
        # ========== 管理员：风险预警处理流程（4步：查询预警 → 查看详情 → 处理 → 通知） ==========
        {
            "id": "workflow_admin_risk_handle",
            "name": "风险预警处理流程",
            "description": "管理员风险预警处理流程，包括预警列表查询、详情查看和处理",
            "instruction_variants": ["风险预警处理流程", "处理风险", "风险预警", "风险处理", "喂，有风险要处理", "帮我处理风险", "风险预警处理", "处理风险预警"],
            "business_scenario": "banking",
            "status": "active",
            "user_intents": ["处理风险", "风险预警", "风险处理"],
            "trigger_keywords": ["处理风险", "风险预警"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始风险处理"}},
                {
                    "id": "n_alert_list",
                    "name": "查询风险预警",
                    "type": "api_call",
                    "description": "查询风险预警列表",
                    "config": {"api_id": "api_admin_risk_alert_list", "api_endpoint": "/api/bank/admin/risk/alerts", "method": "GET", "parameters": {"level": "${level}"}},
                    "outputs": [{"name": "alerts", "type": "array", "description": "预警列表"}, {"name": "high_risk_count", "type": "integer", "description": "高风险数量"}],
                    "ai_instructions": {"user_message": "请选择风险等级查询预警", "action": "查询风险预警"}
                },
                {
                    "id": "n_handle",
                    "name": "处理预警",
                    "type": "api_call",
                    "description": "处理风险预警",
                    "config": {"api_id": "api_admin_risk_alert_handle", "api_endpoint": "/api/bank/admin/risk/alerts/{alert_id}/handle", "method": "POST", "parameters": {"alert_id": "${alert_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择处理动作并填写处理意见", "action": "处理预警"}
                },
                {
                    "id": "n_notify",
                    "name": "处理完成通知",
                    "type": "notification",
                    "description": "发送处理完成通知",
                    "config": {"message_template": "风险预警已处理！预警ID：${alert_id}，处理结果已记录。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "处理完成", "action": "发送处理通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "风险处理完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_alert_list"},
                {"source": "n_alert_list", "target": "n_handle"},
                {"source": "n_handle", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
