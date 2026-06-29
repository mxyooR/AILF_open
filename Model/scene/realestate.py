# realestate.py - 房产场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

REALESTATE_SCENE = {
    "domain": "realestate",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_house_search", "path": "/api/realestate/houses", "method": "GET", "desc": "搜索房源",
         "instruction_variants": ["搜索房源", "找房源", "我要找房", "查房源", "帮我找房子", "房源搜索", "查租房/买房", "房源列表"],
         "request": [{"name": "city", "type": "string", "label": "城市", "required": True}, {"name": "district", "type": "string", "label": "区域", "required": False}, {"name": "type", "type": "string", "label": "交易类型", "required": True}, {"name": "rooms", "type": "integer", "label": "户型", "required": False}, {"name": "price_max", "type": "float", "label": "最高价格", "required": False}],
         "response": [{"name": "houses", "type": "array", "desc": "房源列表"}]},
        {"id": "api_house_detail", "path": "/api/realestate/houses/{house_id}", "method": "GET", "desc": "查询房源详情",
         "instruction_variants": ["查询房源详情", "查看房源信息", "房源详情", "看看这套房", "房源信息", "帮我看房源", "房源图片", "经纪人信息"],
         "request": [{"name": "house_id", "type": "string", "label": "房源ID", "required": True}],
         "response": [{"name": "house", "type": "object", "desc": "房源详情"}, {"name": "images", "type": "array", "desc": "房源图片"}, {"name": "agent", "type": "object", "desc": "经纪人信息"}]},
        {"id": "api_viewing_slots", "path": "/api/realestate/houses/{house_id}/slots", "method": "GET", "desc": "查询看房时段",
         "instruction_variants": ["查询看房时段", "看房时间", "看房时间段", "有哪些看房时间", "帮我查看房时间", "看房预约时间", "可选看房时段", "看房时段查询"],
         "request": [{"name": "house_id", "type": "string", "label": "房源ID", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}],
         "response": [{"name": "slots", "type": "array", "desc": "可选时段"}]},
        {"id": "api_viewing_appointment", "workflow_only": True, "path": "/api/realestate/viewings", "method": "POST", "desc": "预约看房",
         "instruction_variants": ["预约看房", "我要看房", "预约看房时间", "帮我约看房", "看房预约", "约看房", "安排看房", "预约看房流程"],
         "request": [{"name": "house_id", "type": "string", "label": "房源ID", "required": True}, {"name": "date", "type": "date", "label": "看房日期", "required": True}, {"name": "time", "type": "time", "label": "看房时间", "required": True}, {"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "phone", "type": "string", "label": "联系电话", "required": True}],
         "response": [{"name": "viewing_id", "type": "string", "desc": "预约ID"}, {"name": "agent_name", "type": "string", "desc": "经纪人姓名"}, {"name": "agent_phone", "type": "string", "desc": "经纪人电话"}]},
        {"id": "api_viewing_cancel", "workflow_only": True, "path": "/api/realestate/viewings/{viewing_id}/cancel", "method": "POST", "desc": "取消看房预约",
         "instruction_variants": ["取消看房预约", "取消预约看房", "不看房了", "帮我取消看房", "看房预约取消", "退约看房", "取消看房", "取消约看房"],
         "request": [{"name": "viewing_id", "type": "string", "label": "预约ID", "required": True}, {"name": "reason", "type": "string", "label": "取消原因", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_rent_apply", "workflow_only": True, "path": "/api/realestate/rent/apply", "method": "POST", "desc": "租房申请",
         "instruction_variants": ["租房申请", "申请租房", "我要租房", "帮我租房", "租房怎么申请", "提交租房申请", "租房申请表", "租房办理"],
         "request": [{"name": "house_id", "type": "string", "label": "房源ID", "required": True}, {"name": "start_date", "type": "date", "label": "起租日期", "required": True}, {"name": "duration", "type": "integer", "label": "租期", "required": True}, {"name": "tenant_name", "type": "string", "label": "租客姓名", "required": True}, {"name": "tenant_id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "tenant_phone", "type": "string", "label": "联系电话", "required": True}],
         "response": [{"name": "application_id", "type": "string", "desc": "申请编号"}, {"name": "monthly_rent", "type": "float", "desc": "月租金"}, {"name": "deposit", "type": "float", "desc": "押金"}]},
        {"id": "api_deposit_pay", "workflow_only": True, "path": "/api/realestate/rent/deposit", "method": "POST", "desc": "缴纳押金",
         "instruction_variants": ["缴纳押金", "交押金", "支付押金", "帮我交押金", "押金怎么交", "押金支付", "缴押金", "押金付款"],
         "request": [{"name": "application_id", "type": "string", "label": "申请编号", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "receipt_no", "type": "string", "desc": "收据号"}]},
        {"id": "api_contract_sign", "workflow_only": True, "path": "/api/realestate/contracts/sign", "method": "POST", "desc": "签署合同",
         "instruction_variants": ["签署合同", "签合同", "租房签约", "帮我签合同", "合同签署", "签约", "签租房合同", "合同签字"],
         "request": [{"name": "application_id", "type": "string", "label": "申请编号", "required": True}, {"name": "signature", "type": "string", "label": "电子签名", "required": True}],
         "response": [{"name": "contract_id", "type": "string", "desc": "合同ID"}, {"name": "contract_no", "type": "string", "desc": "合同编号"}]},
        {"id": "api_contract_query", "path": "/api/realestate/contracts/{contract_id}", "method": "GET", "desc": "查询合同",
         "instruction_variants": ["查询合同", "查看合同", "合同详情", "合同信息", "帮我查合同", "合同状态", "租房合同查询", "合同查看"],
         "request": [{"name": "contract_id", "type": "string", "label": "合同ID", "required": True}],
         "response": [{"name": "contract", "type": "object", "desc": "合同详情"}, {"name": "status", "type": "string", "desc": "合同状态"}]},
        {"id": "api_rent_pay", "workflow_only": True, "path": "/api/realestate/rent/pay", "method": "POST", "desc": "缴纳房租",
         "instruction_variants": ["缴纳房租", "交房租", "付房租", "帮我交房租", "房租怎么交", "房租支付", "交租", "房租付款"],
         "request": [{"name": "contract_id", "type": "string", "label": "合同ID", "required": True}, {"name": "month", "type": "string", "label": "月份", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "receipt_no", "type": "string", "desc": "收据号"}]},
        {"id": "api_contract_renew", "workflow_only": True, "path": "/api/realestate/contracts/{contract_id}/renew", "method": "POST", "desc": "续租申请",
         "instruction_variants": ["续租申请", "申请续租", "我要续租", "帮我续租", "续租怎么申请", "提交续租", "续租办理", "续租申请表"],
         "request": [{"name": "contract_id", "type": "string", "label": "合同ID", "required": True}, {"name": "duration", "type": "integer", "label": "续租期限", "required": True}],
         "response": [{"name": "renew_id", "type": "string", "desc": "续租申请ID"}, {"name": "new_rent", "type": "float", "desc": "新租金"}]},
        {"id": "api_contract_terminate", "workflow_only": True, "path": "/api/realestate/contracts/{contract_id}/terminate", "method": "POST", "desc": "退租申请",
         "instruction_variants": ["退租申请", "申请退租", "我要退租", "帮我退租", "退租怎么申请", "提前退租", "退租办理", "退租申请表"],
         "request": [{"name": "contract_id", "type": "string", "label": "合同ID", "required": True}, {"name": "end_date", "type": "date", "label": "退租日期", "required": True}, {"name": "reason", "type": "string", "label": "退租原因", "required": True}],
         "response": [{"name": "terminate_id", "type": "string", "desc": "退租申请ID"}, {"name": "refund_amount", "type": "float", "desc": "预计退款"}]},
        {"id": "api_property_fee_query", "path": "/api/realestate/property/fees", "method": "GET", "desc": "查询物业费",
         "instruction_variants": ["查询物业费", "物业费查询", "物业费账单", "帮我查物业费", "物业费明细", "物业费欠费", "物业费情况", "物业费账单查询"],
         "request": [{"name": "house_id", "type": "string", "label": "房屋ID", "required": True}],
         "response": [{"name": "fees", "type": "array", "desc": "物业费账单"}, {"name": "total_unpaid", "type": "float", "desc": "未缴总额"}]},
        {"id": "api_property_fee_pay", "workflow_only": True, "path": "/api/realestate/property/fees/pay", "method": "POST", "desc": "缴纳物业费",
         "instruction_variants": ["缴纳物业费", "交物业费", "支付物业费", "帮我交物业费", "物业费怎么交", "物业费付款", "缴物业费", "物业费支付"],
         "request": [{"name": "fee_id", "type": "string", "label": "账单ID", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}]},
        {"id": "api_repair_request", "workflow_only": True, "path": "/api/realestate/property/repairs", "method": "POST", "desc": "报修申请",
         "instruction_variants": ["报修申请", "我要报修", "提交报修", "帮我报修", "维修申请", "报修怎么申请", "房屋报修", "报修单"],
         "request": [{"name": "house_id", "type": "string", "label": "房屋ID", "required": True}, {"name": "type", "type": "string", "label": "报修类型", "required": True}, {"name": "description", "type": "string", "label": "问题描述", "required": True}, {"name": "contact_name", "type": "string", "label": "联系人", "required": True}, {"name": "contact_phone", "type": "string", "label": "联系电话", "required": True}, {"name": "images", "type": "string", "label": "图片", "required": False}],
         "response": [{"name": "repair_id", "type": "string", "desc": "报修单号"}]},
        {"id": "api_repair_query", "path": "/api/realestate/property/repairs/{repair_id}", "method": "GET", "desc": "查询报修进度",
         "instruction_variants": ["查询报修进度", "报修进度", "维修进度", "帮我查报修", "报修状态", "维修状态", "报修情况", "报修查询"],
         "request": [{"name": "repair_id", "type": "string", "label": "报修单号", "required": True}],
         "response": [{"name": "repair", "type": "object", "desc": "报修详情"}, {"name": "status", "type": "string", "desc": "处理状态"}]},
        {"id": "api_complaint_submit", "workflow_only": True, "path": "/api/realestate/property/complaints", "method": "POST", "desc": "物业投诉",
         "instruction_variants": ["物业投诉", "我要投诉物业", "提交投诉", "帮我投诉", "物业投诉建议", "投诉物业", "物业投诉单", "提交物业投诉"],
         "request": [{"name": "house_id", "type": "string", "label": "房屋ID", "required": True}, {"name": "type", "type": "string", "label": "投诉类型", "required": True}, {"name": "content", "type": "string", "label": "投诉内容", "required": True}, {"name": "contact_phone", "type": "string", "label": "联系电话", "required": True}],
         "response": [{"name": "complaint_id", "type": "string", "desc": "投诉单号"}]},
        {"id": "api_house_publish", "workflow_only": True, "path": "/api/realestate/houses/publish", "method": "POST", "desc": "发布房源",
         "instruction_variants": ["发布房源", "我要发布房源", "发布房子", "帮我发房源", "房源发布", "发布租房/卖房", "上架房源", "提交房源"],
         "request": [{"name": "title", "type": "string", "label": "标题", "required": True}, {"name": "type", "type": "string", "label": "交易类型", "required": True}, {"name": "address", "type": "string", "label": "地址", "required": True}, {"name": "area", "type": "float", "label": "面积", "required": True}, {"name": "rooms", "type": "integer", "label": "户型", "required": True}, {"name": "price", "type": "float", "label": "价格", "required": True}, {"name": "description", "type": "string", "label": "描述", "required": True}],
         "response": [{"name": "house_id", "type": "string", "desc": "房源ID"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_viewing_list", "workflow_only": True, "path": "/api/realestate/admin/viewings", "method": "GET", "desc": "查询看房预约列表",
         "instruction_variants": ["查询看房预约列表", "看房预约列表", "预约看房列表", "帮我查预约", "今日看房预约", "看房安排", "预约清单", "看房预约管理"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "date", "type": "date", "label": "日期", "required": False}],
         "response": [{"name": "viewings", "type": "array", "desc": "预约列表"}, {"name": "today_count", "type": "integer", "desc": "今日预约数"}]},
        {"id": "api_admin_viewing_confirm", "workflow_only": True, "path": "/api/realestate/admin/viewings/{viewing_id}/confirm", "method": "POST", "desc": "确认看房",
         "instruction_variants": ["确认看房", "确认预约", "看房确认", "帮我确认看房", "安排经纪人看房", "确认看房安排", "预约确认", "看房预约确认"],
         "request": [{"name": "viewing_id", "type": "string", "label": "预约ID", "required": True}, {"name": "agent_id", "type": "string", "label": "经纪人ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_viewing_complete", "workflow_only": True, "path": "/api/realestate/admin/viewings/{viewing_id}/complete", "method": "POST", "desc": "完成看房",
         "instruction_variants": ["完成看房", "看房完成", "结束看房", "帮我完成看房", "看房已完成", "看房结束", "完成预约看房", "看房结案"],
         "request": [{"name": "viewing_id", "type": "string", "label": "预约ID", "required": True}, {"name": "feedback", "type": "string", "label": "反馈", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_agent_list", "workflow_only": True, "path": "/api/realestate/admin/agents", "method": "GET", "desc": "查询经纪人列表",
         "instruction_variants": ["查询经纪人列表", "经纪人列表", "中介列表", "帮我查经纪人", "可用经纪人", "经纪人情况", "经纪人查询", "经纪人清单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "agents", "type": "array", "desc": "经纪人列表"}, {"name": "available_count", "type": "integer", "desc": "可用人数"}]},
        {"id": "api_admin_application_list", "workflow_only": True, "path": "/api/realestate/admin/applications", "method": "GET", "desc": "查询租房申请列表",
         "instruction_variants": ["查询租房申请列表", "租房申请列表", "待审核租房", "帮我查租房申请", "租房申请管理", "租房申请清单", "待处理申请", "租房申请查询"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "applications", "type": "array", "desc": "申请列表"}, {"name": "pending_count", "type": "integer", "desc": "待审核数"}]},
        {"id": "api_admin_application_detail", "workflow_only": True, "path": "/api/realestate/admin/applications/{application_id}", "method": "GET", "desc": "查询申请详情",
         "instruction_variants": ["查询申请详情", "申请详情", "租房申请详情", "帮我看申请", "申请信息", "申请内容", "申请详情查看", "租房申请信息"],
         "request": [{"name": "application_id", "type": "string", "label": "申请编号", "required": True}],
         "response": [{"name": "application", "type": "object", "desc": "申请详情"}, {"name": "tenant", "type": "object", "desc": "租客信息"}, {"name": "house", "type": "object", "desc": "房源信息"}]},
        {"id": "api_admin_application_review", "workflow_only": True, "path": "/api/realestate/admin/applications/{application_id}/review", "method": "POST", "desc": "审核租房申请",
         "instruction_variants": ["审核租房申请", "审批租房申请", "租房申请审核", "帮我审核申请", "审核租房", "租房审核", "申请审核", "审核申请单"],
         "request": [{"name": "application_id", "type": "string", "label": "申请编号", "required": True}, {"name": "result", "type": "string", "label": "审核结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_contract_generate", "workflow_only": True, "path": "/api/realestate/admin/contracts/generate", "method": "POST", "desc": "生成合同",
         "instruction_variants": ["生成合同", "生成租房合同", "制作合同", "帮我生成合同", "合同生成", "出合同", "生成合同文档", "合同制作"],
         "request": [{"name": "application_id", "type": "string", "label": "申请编号", "required": True}],
         "response": [{"name": "contract_id", "type": "string", "desc": "合同ID"}, {"name": "contract_url", "type": "string", "desc": "合同链接"}]},
        {"id": "api_admin_renew_list", "workflow_only": True, "path": "/api/realestate/admin/renews", "method": "GET", "desc": "查询续租申请列表",
         "instruction_variants": ["查询续租申请列表", "续租申请列表", "待审核续租", "帮我查续租", "续租申请管理", "续租申请清单", "续租申请查询", "待处理续租"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "renews", "type": "array", "desc": "续租列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_renew_approve", "workflow_only": True, "path": "/api/realestate/admin/renews/{renew_id}/approve", "method": "POST", "desc": "审批续租",
         "instruction_variants": ["审批续租", "续租审批", "审核续租", "帮我审批续租", "续租申请审批", "续租审核", "批准续租", "续租批复"],
         "request": [{"name": "renew_id", "type": "string", "label": "续租申请ID", "required": True}, {"name": "result", "type": "string", "label": "审批结果", "required": True}, {"name": "new_rent", "type": "float", "label": "新租金", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_terminate_list", "workflow_only": True, "path": "/api/realestate/admin/terminates", "method": "GET", "desc": "查询退租申请列表",
         "instruction_variants": ["查询退租申请列表", "退租申请列表", "待处理退租", "帮我查退租", "退租申请管理", "退租申请清单", "退租申请查询", "待审核退租"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "terminates", "type": "array", "desc": "退租列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_terminate_process", "workflow_only": True, "path": "/api/realestate/admin/terminates/{terminate_id}/process", "method": "POST", "desc": "处理退租",
         "instruction_variants": ["处理退租", "退租处理", "退租办理", "帮我处理退租", "退租审核处理", "退租流程处理", "处理退租申请", "退租结算"],
         "request": [{"name": "terminate_id", "type": "string", "label": "退租申请ID", "required": True}, {"name": "check_result", "type": "string", "label": "验房结果", "required": True}, {"name": "deduction", "type": "float", "label": "扣款金额", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "refund_amount", "type": "float", "desc": "实际退款"}]},
        {"id": "api_admin_deposit_refund", "workflow_only": True, "path": "/api/realestate/admin/deposits/{contract_id}/refund", "method": "POST", "desc": "退还押金",
         "instruction_variants": ["退还押金", "押金退还", "退押金", "帮我退押金", "押金退款", "退还押金流程", "退押金处理", "押金返还"],
         "request": [{"name": "contract_id", "type": "string", "label": "合同ID", "required": True}, {"name": "amount", "type": "float", "label": "退款金额", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "transaction_no", "type": "string", "desc": "交易流水号"}]},
        {"id": "api_admin_repair_list", "workflow_only": True, "path": "/api/realestate/admin/repairs", "method": "GET", "desc": "查询报修列表",
         "instruction_variants": ["查询报修列表", "报修列表", "待处理报修", "帮我查报修", "报修管理", "报修清单", "维修工单", "报修记录"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "repairs", "type": "array", "desc": "报修列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_worker_list", "workflow_only": True, "path": "/api/realestate/admin/workers", "method": "GET", "desc": "查询维修工列表",
         "instruction_variants": ["查询维修工列表", "维修工列表", "维修人员列表", "帮我查维修工", "可用维修工", "维修工情况", "维修工查询", "维修工清单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "workers", "type": "array", "desc": "维修工列表"}, {"name": "available_count", "type": "integer", "desc": "可用人数"}]},
        {"id": "api_admin_repair_assign", "workflow_only": True, "path": "/api/realestate/admin/repairs/{repair_id}/assign", "method": "POST", "desc": "分配维修",
         "instruction_variants": ["分配维修", "派维修工", "安排维修", "帮我分配维修", "维修派单", "维修分配", "分配维修工", "维修指派"],
         "request": [{"name": "repair_id", "type": "string", "label": "报修单号", "required": True}, {"name": "worker_id", "type": "string", "label": "维修工ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "worker_name", "type": "string", "desc": "维修工姓名"}]},
        {"id": "api_admin_repair_complete", "workflow_only": True, "path": "/api/realestate/admin/repairs/{repair_id}/complete", "method": "POST", "desc": "完成维修",
         "instruction_variants": ["完成维修", "维修完成", "修好确认", "帮我完成维修", "维修结案", "完成报修", "维修完成确认", "维修结束"],
         "request": [{"name": "repair_id", "type": "string", "label": "报修单号", "required": True}, {"name": "result", "type": "string", "label": "维修结果", "required": True}, {"name": "cost", "type": "float", "label": "维修费用", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_complaint_list", "workflow_only": True, "path": "/api/realestate/admin/complaints", "method": "GET", "desc": "查询投诉列表",
         "instruction_variants": ["查询投诉列表", "物业投诉列表", "待处理投诉", "帮我看投诉", "投诉管理", "投诉记录", "投诉清单", "投诉情况"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "complaints", "type": "array", "desc": "投诉列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_complaint_handle", "workflow_only": True, "path": "/api/realestate/admin/complaints/{complaint_id}/handle", "method": "POST", "desc": "处理投诉",
         "instruction_variants": ["处理投诉", "物业投诉处理", "处理业主投诉", "帮我处理投诉", "投诉处理", "投诉解决", "处理投诉单", "投诉处理流程"],
         "request": [{"name": "complaint_id", "type": "string", "label": "投诉单号", "required": True}, {"name": "result", "type": "string", "label": "处理结果", "required": True}, {"name": "reply", "type": "string", "label": "回复内容", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_house_list", "workflow_only": True, "path": "/api/realestate/admin/houses", "method": "GET", "desc": "查询房源列表（管理员）",
         "instruction_variants": ["查询房源列表", "房源列表", "待审核房源", "帮我查房源", "房源管理", "房源清单", "房源查询", "房源情况"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "houses", "type": "array", "desc": "房源列表"}, {"name": "pending_count", "type": "integer", "desc": "待审核数"}]},
        {"id": "api_admin_house_audit", "workflow_only": True, "path": "/api/realestate/admin/houses/{house_id}/audit", "method": "POST", "desc": "审核房源",
         "instruction_variants": ["审核房源", "房源审核", "审批房源", "帮我审核房源", "房源审核处理", "审核发布房源", "房源审批", "房源审查"],
         "request": [{"name": "house_id", "type": "string", "label": "房源ID", "required": True}, {"name": "result", "type": "string", "label": "审核结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},

        # ========== 管理员统计 API ==========
        {"id": "api_admin_house_stats", "path": "/api/realestate/admin/stats/house", "method": "GET", "desc": "查询房源统计", "name": "房源统计", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询房源统计", "房源统计", "房源数据", "房源类型占比", "帮我看房源统计", "房源统计报表", "房源分布", "房源数量"],
         "request": [], "response": [{"name": "types", "type": "array", "desc": "房源类型"}, {"name": "counts", "type": "array", "desc": "数量"}]},
        {"id": "api_admin_deal_analysis", "path": "/api/realestate/admin/stats/deal", "method": "GET", "desc": "查询成交分析", "name": "成交分析", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询成交分析", "成交分析", "成交数据", "区域成交情况", "帮我看成交分析", "成交统计", "成交分布", "成交报表"],
         "request": [], "response": [{"name": "districts", "type": "array", "desc": "区域"}, {"name": "deals", "type": "array", "desc": "成交量"}]},
        {"id": "api_admin_rent_trend", "path": "/api/realestate/admin/stats/rent", "method": "GET", "desc": "查询租金趋势", "name": "租金趋势", "response_type": "chart", "chart_type": "line",
         "instruction_variants": ["查询租金趋势", "租金趋势", "租金走势", "租金变化", "帮我看租金趋势", "租金统计", "租金趋势图", "租金趋势数据"],
         "request": [], "response": [{"name": "months", "type": "array", "desc": "月份"}, {"name": "avg_rent", "type": "array", "desc": "平均租金"}]},
    ],

    "workflows": [
        # ========== 用户：完整租房流程（8步：搜索房源 → 查看详情 → 查询时段 → 预约看房 → 提交申请 → 缴纳押金 → 签署合同 → 通知） ==========
        {
            "id": "workflow_full_rent",
            "name": "完整租房流程",
            "description": "完整的租房流程，包括搜索、看房、申请、签约",
            "instruction_variants": ["完整租房流程", "租房流程", "我要租房", "帮我租房", "租房全流程", "找房到签约流程", "租房怎么走", "租房办理流程"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["租房", "找房租", "租房子"],
            "trigger_keywords": ["租房", "找房租", "租房子"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始租房"}},
                {"id": "n_search", "name": "搜索房源", "type": "api_call", "description": "搜索房源", "config": {"api_id": "api_house_search", "api_endpoint": "/api/realestate/houses", "method": "GET", "parameters": {"city": "${city}", "type": "租房", "district": "${district}", "rooms": "${rooms}"}}, "outputs": [{"name": "houses", "type": "array", "description": "房源列表"}], "ai_instructions": {"user_message": "请输入城市和筛选条件", "action": "搜索房源"}},
                {"id": "n_detail", "name": "查看详情", "type": "api_call", "description": "查看房源详情", "config": {"api_id": "api_house_detail", "api_endpoint": "/api/realestate/houses/{house_id}", "method": "GET", "parameters": {"house_id": "${house_id}"}}, "outputs": [{"name": "house", "type": "object", "description": "房源详情"}], "ai_instructions": {"user_message": "请选择房源", "action": "查看详情"}},
                {"id": "n_slots", "name": "查询看房时段", "type": "api_call", "description": "查询可预约时段", "config": {"api_id": "api_viewing_slots", "api_endpoint": "/api/realestate/houses/{house_id}/slots", "method": "GET", "parameters": {"house_id": "${house_id}", "date": "${date}"}}, "outputs": [{"name": "slots", "type": "array", "description": "可选时段"}], "ai_instructions": {"user_message": "请选择看房日期", "action": "查询看房时段"}},
                {"id": "n_viewing", "name": "预约看房", "type": "api_call", "description": "预约看房", "config": {"api_id": "api_viewing_appointment", "api_endpoint": "/api/realestate/viewings", "method": "POST", "parameters": {"house_id": "${house_id}", "date": "${date}", "time": "${time}", "name": "${name}", "phone": "${phone}"}}, "outputs": [{"name": "viewing_id", "type": "string", "description": "预约ID"}, {"name": "agent_name", "type": "string", "description": "经纪人姓名"}], "ai_instructions": {"user_message": "请选择时段并填写联系信息", "action": "预约看房"}},
                {"id": "n_apply", "name": "提交申请", "type": "api_call", "description": "提交租房申请", "config": {"api_id": "api_rent_apply", "api_endpoint": "/api/realestate/rent/apply", "method": "POST", "parameters": {"house_id": "${house_id}", "start_date": "${start_date}", "duration": "${duration}", "tenant_name": "${tenant_name}", "tenant_id_card": "${tenant_id_card}", "tenant_phone": "${tenant_phone}"}}, "outputs": [{"name": "application_id", "type": "string", "description": "申请编号"}, {"name": "monthly_rent", "type": "float", "description": "月租金"}, {"name": "deposit", "type": "float", "description": "押金"}], "ai_instructions": {"user_message": "请填写租房申请信息", "action": "提交申请"}},
                {"id": "n_deposit", "name": "缴纳押金", "type": "api_call", "description": "缴纳押金", "config": {"api_id": "api_deposit_pay", "api_endpoint": "/api/realestate/rent/deposit", "method": "POST", "parameters": {"application_id": "${application_id}", "amount": "${deposit}", "payment_method": "${payment_method}"}}, "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}], "ai_instructions": {"user_message": "请选择支付方式缴纳押金", "action": "缴纳押金"}},
                {"id": "n_sign", "name": "签署合同", "type": "api_call", "description": "签署租房合同", "config": {"api_id": "api_contract_sign", "api_endpoint": "/api/realestate/contracts/sign", "method": "POST", "parameters": {"application_id": "${application_id}", "signature": "${signature}"}}, "outputs": [{"name": "contract_id", "type": "string", "description": "合同ID"}, {"name": "contract_no", "type": "string", "description": "合同编号"}], "ai_instructions": {"user_message": "请签署电子合同", "action": "签署合同"}},
                {"id": "n_notify", "name": "租房通知", "type": "notification", "description": "发送租房成功通知", "config": {"message_template": "租房成功！合同编号：${contract_no}，月租金：${monthly_rent}元，经纪人：${agent_name}。"}, "outputs": [], "ai_instructions": {"user_message": "租房成功", "action": "发送租房通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "租房完成"}}
            ],
            "edges": [{"source": "start", "target": "n_search"}, {"source": "n_search", "target": "n_detail"}, {"source": "n_detail", "target": "n_slots"}, {"source": "n_slots", "target": "n_viewing"}, {"source": "n_viewing", "target": "n_apply"}, {"source": "n_apply", "target": "n_deposit"}, {"source": "n_deposit", "target": "n_sign"}, {"source": "n_sign", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 用户：续租流程（5步：查询合同 → 确认续租 → 提交申请 → 签署新合同 → 通知） ==========
        {
            "id": "workflow_renew",
            "name": "续租流程",
            "description": "租房续租流程",
            "instruction_variants": ["续租流程", "我要续租", "续租申请流程", "帮我续租", "续租怎么走", "续租办理", "续租流程走一下", "续租申请"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["续租", "续签", "续约"],
            "trigger_keywords": ["续租", "续签", "续约"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始续租"}},
                {"id": "n_contract", "name": "查询合同", "type": "api_call", "description": "查询当前合同", "config": {"api_id": "api_contract_query", "api_endpoint": "/api/realestate/contracts/{contract_id}", "method": "GET", "parameters": {"contract_id": "${contract_id}"}}, "outputs": [{"name": "contract", "type": "object", "description": "合同详情"}], "ai_instructions": {"user_message": "请输入合同ID", "action": "查询合同"}},
                {"id": "n_apply", "name": "提交续租", "type": "api_call", "description": "提交续租申请", "config": {"api_id": "api_contract_renew", "api_endpoint": "/api/realestate/contracts/{contract_id}/renew", "method": "POST", "parameters": {"contract_id": "${contract_id}", "duration": "${duration}"}}, "outputs": [{"name": "renew_id", "type": "string", "description": "续租申请ID"}, {"name": "new_rent", "type": "float", "description": "新租金"}], "ai_instructions": {"user_message": "请选择续租期限", "action": "提交续租"}},
                {"id": "n_notify", "name": "续租通知", "type": "notification", "description": "发送续租申请通知", "config": {"message_template": "续租申请已提交！申请ID：${renew_id}，新租金：${new_rent}元/月，请等待审批。"}, "outputs": [], "ai_instructions": {"user_message": "续租已提交", "action": "发送续租通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "续租申请完成"}}
            ],
            "edges": [{"source": "start", "target": "n_contract"}, {"source": "n_contract", "target": "n_apply"}, {"source": "n_apply", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 用户：退租流程（5步：查询合同 → 提交退租 → 确认验房 → 等待退款 → 通知） ==========
        {
            "id": "workflow_terminate",
            "name": "退租流程",
            "description": "租房退租流程",
            "instruction_variants": ["退租流程", "我要退租", "退租申请流程", "帮我退租", "退租怎么走", "退租办理", "退租流程走一下", "退租申请"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["退租", "退房", "解约"],
            "trigger_keywords": ["退租", "退房", "解约"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始退租"}},
                {"id": "n_contract", "name": "查询合同", "type": "api_call", "description": "查询当前合同", "config": {"api_id": "api_contract_query", "api_endpoint": "/api/realestate/contracts/{contract_id}", "method": "GET", "parameters": {"contract_id": "${contract_id}"}}, "outputs": [{"name": "contract", "type": "object", "description": "合同详情"}], "ai_instructions": {"user_message": "请输入合同ID", "action": "查询合同"}},
                {"id": "n_apply", "name": "提交退租", "type": "api_call", "description": "提交退租申请", "config": {"api_id": "api_contract_terminate", "api_endpoint": "/api/realestate/contracts/{contract_id}/terminate", "method": "POST", "parameters": {"contract_id": "${contract_id}", "end_date": "${end_date}", "reason": "${reason}"}}, "outputs": [{"name": "terminate_id", "type": "string", "description": "退租申请ID"}, {"name": "refund_amount", "type": "float", "description": "预计退款"}], "ai_instructions": {"user_message": "请填写退租日期和原因", "action": "提交退租"}},
                {"id": "n_notify", "name": "退租通知", "type": "notification", "description": "发送退租申请通知", "config": {"message_template": "退租申请已提交！申请ID：${terminate_id}，预计退款：${refund_amount}元，请等待验房。"}, "outputs": [], "ai_instructions": {"user_message": "退租已提交", "action": "发送退租通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退租申请完成"}}
            ],
            "edges": [{"source": "start", "target": "n_contract"}, {"source": "n_contract", "target": "n_apply"}, {"source": "n_apply", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 用户：房租缴纳流程（4步：查询合同 → 查询账单 → 缴纳房租 → 通知） ==========
        {
            "id": "workflow_rent_pay",
            "name": "房租缴纳流程",
            "description": "缴纳房租",
            "instruction_variants": ["交房租流程", "缴房租流程", "我要交房租", "帮我交房租", "房租支付流程", "交租流程", "房租怎么交", "房租缴纳"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["交房租", "缴纳房租", "付房租"],
            "trigger_keywords": ["交房租", "缴纳房租", "付房租"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始缴纳房租"}},
                {"id": "n_contract", "name": "查询合同", "type": "api_call", "description": "查询租房合同", "config": {"api_id": "api_contract_query", "api_endpoint": "/api/realestate/contracts/{contract_id}", "method": "GET", "parameters": {"contract_id": "${contract_id}"}}, "outputs": [{"name": "contract", "type": "object", "description": "合同详情"}], "ai_instructions": {"user_message": "请输入合同ID", "action": "查询合同"}},
                {"id": "n_pay", "name": "缴纳房租", "type": "api_call", "description": "缴纳房租", "config": {"api_id": "api_rent_pay", "api_endpoint": "/api/realestate/rent/pay", "method": "POST", "parameters": {"contract_id": "${contract_id}", "month": "${month}", "amount": "${amount}", "payment_method": "${payment_method}"}}, "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "receipt_no", "type": "string", "description": "收据号"}], "ai_instructions": {"user_message": "请选择月份和支付方式", "action": "缴纳房租"}},
                {"id": "n_notify", "name": "缴费通知", "type": "notification", "description": "发送缴费成功通知", "config": {"message_template": "房租缴纳成功！收据号：${receipt_no}，金额：${amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "缴费成功", "action": "发送缴费通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "房租缴纳完成"}}
            ],
            "edges": [{"source": "start", "target": "n_contract"}, {"source": "n_contract", "target": "n_pay"}, {"source": "n_pay", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 用户：物业费缴纳流程（4步：查询物业费 → 选择账单 → 缴费 → 通知） ==========
        {
            "id": "workflow_property_fee",
            "name": "物业费缴纳流程",
            "description": "缴纳物业费",
            "instruction_variants": ["物业费缴纳流程", "交物业费流程", "我要交物业费", "帮我交物业费", "物业费支付流程", "缴物业费", "物业费怎么交", "物业费缴纳"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["交物业费", "缴纳物业费", "物业费"],
            "trigger_keywords": ["交物业费", "缴纳物业费", "物业费"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始缴费"}},
                {"id": "n_query", "name": "查询物业费", "type": "api_call", "description": "查询物业费账单", "config": {"api_id": "api_property_fee_query", "api_endpoint": "/api/realestate/property/fees", "method": "GET", "parameters": {"house_id": "${house_id}"}}, "outputs": [{"name": "fees", "type": "array", "description": "物业费账单"}, {"name": "total_unpaid", "type": "float", "description": "未缴总额"}], "ai_instructions": {"user_message": "请输入房屋ID", "action": "查询物业费"}},
                {"id": "n_pay", "name": "缴纳物业费", "type": "api_call", "description": "缴纳物业费", "config": {"api_id": "api_property_fee_pay", "api_endpoint": "/api/realestate/property/fees/pay", "method": "POST", "parameters": {"fee_id": "${fee_id}", "amount": "${amount}", "payment_method": "${payment_method}"}}, "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}], "ai_instructions": {"user_message": "请选择账单并支付", "action": "缴纳物业费"}},
                {"id": "n_notify", "name": "缴费通知", "type": "notification", "description": "发送缴费成功通知", "config": {"message_template": "物业费缴纳成功！金额：${amount}元。"}, "outputs": [], "ai_instructions": {"user_message": "缴费成功", "action": "发送缴费通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "缴费完成"}}
            ],
            "edges": [{"source": "start", "target": "n_query"}, {"source": "n_query", "target": "n_pay"}, {"source": "n_pay", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 用户：报修流程（4步：填写报修 → 上传图片 → 提交 → 通知） ==========
        {
            "id": "workflow_repair",
            "name": "报修流程",
            "description": "提交物业报修",
            "instruction_variants": ["报修流程", "我要报修", "报修申请流程", "帮我报修", "维修报修流程", "报修怎么走", "报修处理流程", "报修申请"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["报修", "维修", "物业报修"],
            "trigger_keywords": ["报修", "维修", "物业报修"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始报修"}},
                {"id": "n_request", "name": "提交报修", "type": "api_call", "description": "提交报修申请", "config": {"api_id": "api_repair_request", "api_endpoint": "/api/realestate/property/repairs", "method": "POST", "parameters": {"house_id": "${house_id}", "type": "${type}", "description": "${description}", "contact_name": "${contact_name}", "contact_phone": "${contact_phone}", "images": "${images}"}}, "outputs": [{"name": "repair_id", "type": "string", "description": "报修单号"}], "ai_instructions": {"user_message": "请填写报修信息", "action": "提交报修"}},
                {"id": "n_notify", "name": "报修通知", "type": "notification", "description": "发送报修成功通知", "config": {"message_template": "报修申请已提交！报修单号：${repair_id}，我们将尽快处理。"}, "outputs": [], "ai_instructions": {"user_message": "报修已提交", "action": "发送报修通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报修完成"}}
            ],
            "edges": [{"source": "start", "target": "n_request"}, {"source": "n_request", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 用户：发布房源流程（4步：填写信息 → 上传图片 → 提交审核 → 通知） ==========
        {
            "id": "workflow_publish",
            "name": "发布房源流程",
            "description": "发布出租/出售房源",
            "instruction_variants": ["发布房源流程", "我要发布房源", "房源发布流程", "帮我发房源", "上架房源流程", "发布房子流程", "房源上架", "发布房源"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["发布房源", "出租房子", "卖房"],
            "trigger_keywords": ["发布房源", "出租房子", "卖房"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始发布房源"}},
                {"id": "n_publish", "name": "发布房源", "type": "api_call", "description": "填写房源信息并发布", "config": {"api_id": "api_house_publish", "api_endpoint": "/api/realestate/houses/publish", "method": "POST", "parameters": {"title": "${title}", "type": "${type}", "address": "${address}", "area": "${area}", "rooms": "${rooms}", "price": "${price}", "description": "${description}"}}, "outputs": [{"name": "house_id", "type": "string", "description": "房源ID"}], "ai_instructions": {"user_message": "请填写房源信息", "action": "发布房源"}},
                {"id": "n_notify", "name": "发布通知", "type": "notification", "description": "发送发布成功通知", "config": {"message_template": "房源发布成功！房源ID：${house_id}，请等待审核。"}, "outputs": [], "ai_instructions": {"user_message": "发布成功", "action": "发送发布通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "发布完成"}}
            ],
            "edges": [{"source": "start", "target": "n_publish"}, {"source": "n_publish", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：看房预约管理流程（6步：查询预约 → 查看详情 → 查询经纪人 → 分配经纪人 → 确认预约 → 通知） ==========
        {
            "id": "workflow_admin_viewing",
            "name": "管理员看房预约管理流程",
            "description": "管理看房预约，分配经纪人",
            "instruction_variants": ["看房预约管理流程", "管理员看房管理", "看房安排流程", "确认看房流程", "看房预约处理", "看房预约管理", "预约看房处理", "看房管理"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["管理预约", "预约管理", "分配看房"],
            "trigger_keywords": ["管理预约", "预约管理", "分配看房"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始管理预约"}},
                {"id": "n_list", "name": "查询预约", "type": "api_call", "description": "查询看房预约列表", "config": {"api_id": "api_admin_viewing_list", "api_endpoint": "/api/realestate/admin/viewings", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "viewings", "type": "array", "description": "预约列表"}, {"name": "today_count", "type": "integer", "description": "今日预约数"}], "ai_instructions": {"user_message": "查询待确认预约", "action": "查询预约"}},
                {"id": "n_agents", "name": "查询经纪人", "type": "api_call", "description": "查询可用经纪人", "config": {"api_id": "api_admin_agent_list", "api_endpoint": "/api/realestate/admin/agents", "method": "GET", "parameters": {"status": "available"}}, "outputs": [{"name": "agents", "type": "array", "description": "经纪人列表"}], "ai_instructions": {"user_message": "查询可用经纪人", "action": "查询经纪人"}},
                {"id": "n_confirm", "name": "确认预约", "type": "api_call", "description": "确认看房预约并分配经纪人", "config": {"api_id": "api_admin_viewing_confirm", "api_endpoint": "/api/realestate/admin/viewings/{viewing_id}/confirm", "method": "POST", "parameters": {"viewing_id": "${viewing_id}", "agent_id": "${agent_id}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择预约并分配经纪人", "action": "确认预约"}},
                {"id": "n_notify", "name": "确认通知", "type": "notification", "description": "发送确认通知", "config": {"message_template": "预约${viewing_id}已确认，今日共${today_count}个预约。"}, "outputs": [], "ai_instructions": {"user_message": "确认成功", "action": "发送确认通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "预约管理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_agents"}, {"source": "n_agents", "target": "n_confirm"}, {"source": "n_confirm", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：租房申请审核流程（6步：查询申请 → 查看详情 → 审核申请 → 生成合同 → 发送合同 → 通知） ==========
        {
            "id": "workflow_admin_application",
            "name": "管理员租房申请审核流程",
            "description": "审核租房申请并生成合同",
            "instruction_variants": ["租房申请审核流程", "审核租房申请", "处理租房申请", "租房审批流程", "申请审核流程", "租房申请处理", "租房审核", "租房申请审核"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["审核申请", "申请审核", "处理申请"],
            "trigger_keywords": ["审核申请", "申请审核", "处理申请"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审核申请"}},
                {"id": "n_list", "name": "查询申请", "type": "api_call", "description": "查询租房申请列表", "config": {"api_id": "api_admin_application_list", "api_endpoint": "/api/realestate/admin/applications", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "applications", "type": "array", "description": "申请列表"}, {"name": "pending_count", "type": "integer", "description": "待审核数"}], "ai_instructions": {"user_message": "查询待审核申请", "action": "查询申请"}},
                {"id": "n_detail", "name": "查看详情", "type": "api_call", "description": "查看申请详情", "config": {"api_id": "api_admin_application_detail", "api_endpoint": "/api/realestate/admin/applications/{application_id}", "method": "GET", "parameters": {"application_id": "${application_id}"}}, "outputs": [{"name": "application", "type": "object", "description": "申请详情"}, {"name": "tenant", "type": "object", "description": "租客信息"}], "ai_instructions": {"user_message": "请选择要审核的申请", "action": "查看详情"}},
                {"id": "n_review", "name": "审核申请", "type": "api_call", "description": "审核租房申请", "config": {"api_id": "api_admin_application_review", "api_endpoint": "/api/realestate/admin/applications/{application_id}/review", "method": "POST", "parameters": {"application_id": "${application_id}", "result": "${result}", "remark": "${remark}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请填写审核结果", "action": "审核申请"}},
                {"id": "n_generate", "name": "生成合同", "type": "api_call", "description": "生成租房合同", "config": {"api_id": "api_admin_contract_generate", "api_endpoint": "/api/realestate/admin/contracts/generate", "method": "POST", "parameters": {"application_id": "${application_id}"}}, "outputs": [{"name": "contract_id", "type": "string", "description": "合同ID"}, {"name": "contract_url", "type": "string", "description": "合同链接"}], "ai_instructions": {"user_message": "生成合同", "action": "生成合同"}},
                {"id": "n_notify", "name": "审核通知", "type": "notification", "description": "发送审核结果通知", "config": {"message_template": "申请${application_id}审核完成，合同ID：${contract_id}。"}, "outputs": [], "ai_instructions": {"user_message": "审核完成", "action": "发送审核通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "审核完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_detail"}, {"source": "n_detail", "target": "n_review"}, {"source": "n_review", "target": "n_generate"}, {"source": "n_generate", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：续租审批流程（5步：查询续租 → 查看详情 → 审批续租 → 更新合同 → 通知） ==========
        {
            "id": "workflow_admin_renew",
            "name": "管理员续租审批流程",
            "description": "审批续租申请",
            "instruction_variants": ["续租审批流程", "审核续租流程", "处理续租申请", "续租审核流程", "续租审批", "续租处理", "续租申请审批", "续租审批处理"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["审批续租", "续租审批", "处理续租"],
            "trigger_keywords": ["审批续租", "续租审批", "处理续租"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审批续租"}},
                {"id": "n_list", "name": "查询续租", "type": "api_call", "description": "查询续租申请列表", "config": {"api_id": "api_admin_renew_list", "api_endpoint": "/api/realestate/admin/renews", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "renews", "type": "array", "description": "续租列表"}], "ai_instructions": {"user_message": "查询待审批续租", "action": "查询续租"}},
                {"id": "n_approve", "name": "审批续租", "type": "api_call", "description": "审批续租申请", "config": {"api_id": "api_admin_renew_approve", "api_endpoint": "/api/realestate/admin/renews/{renew_id}/approve", "method": "POST", "parameters": {"renew_id": "${renew_id}", "result": "${result}", "new_rent": "${new_rent}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择续租并填写审批结果", "action": "审批续租"}},
                {"id": "n_notify", "name": "审批通知", "type": "notification", "description": "发送审批结果通知", "config": {"message_template": "续租${renew_id}审批完成，新租金：${new_rent}元/月。"}, "outputs": [], "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "续租审批完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_approve"}, {"source": "n_approve", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：退租处理流程（6步：查询退租 → 查看详情 → 验房处理 → 计算退款 → 退还押金 → 通知） ==========
        {
            "id": "workflow_admin_terminate",
            "name": "管理员退租处理流程",
            "description": "处理退租申请，验房退款",
            "instruction_variants": ["退租处理流程", "处理退租申请", "退租审核流程", "退租办理流程", "退租审批处理", "退租结算流程", "退租处理", "退租流程处理"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["处理退租", "退租处理", "验房退款"],
            "trigger_keywords": ["处理退租", "退租处理", "验房退款"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理退租"}},
                {"id": "n_list", "name": "查询退租", "type": "api_call", "description": "查询退租申请列表", "config": {"api_id": "api_admin_terminate_list", "api_endpoint": "/api/realestate/admin/terminates", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "terminates", "type": "array", "description": "退租列表"}], "ai_instructions": {"user_message": "查询待处理退租", "action": "查询退租"}},
                {"id": "n_process", "name": "验房处理", "type": "api_call", "description": "验房并处理退租", "config": {"api_id": "api_admin_terminate_process", "api_endpoint": "/api/realestate/admin/terminates/{terminate_id}/process", "method": "POST", "parameters": {"terminate_id": "${terminate_id}", "check_result": "${check_result}", "deduction": "${deduction}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "refund_amount", "type": "float", "description": "实际退款"}], "ai_instructions": {"user_message": "请选择退租并填写验房结果", "action": "验房处理"}},
                {"id": "n_refund", "name": "退还押金", "type": "api_call", "description": "退还押金", "config": {"api_id": "api_admin_deposit_refund", "api_endpoint": "/api/realestate/admin/deposits/{contract_id}/refund", "method": "POST", "parameters": {"contract_id": "${contract_id}", "amount": "${refund_amount}"}}, "outputs": [{"name": "transaction_no", "type": "string", "description": "交易流水号"}], "ai_instructions": {"user_message": "确认退还押金", "action": "退还押金"}},
                {"id": "n_notify", "name": "退租通知", "type": "notification", "description": "发送退租完成通知", "config": {"message_template": "退租处理完成！退款金额：${refund_amount}元，交易流水号：${transaction_no}。"}, "outputs": [], "ai_instructions": {"user_message": "退租完成", "action": "发送退租通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "退租处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_process"}, {"source": "n_process", "target": "n_refund"}, {"source": "n_refund", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：报修处理流程（6步：查询报修 → 查看详情 → 查询维修工 → 分配维修 → 完成维修 → 通知） ==========
        {
            "id": "workflow_admin_repair",
            "name": "管理员报修处理流程",
            "description": "处理物业报修，分配维修工",
            "instruction_variants": ["报修处理流程", "处理报修", "分配维修流程", "维修处理流程", "报修工单处理", "维修派单流程", "报修处理", "维修处理"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["处理报修", "报修处理", "分配维修"],
            "trigger_keywords": ["处理报修", "报修处理", "分配维修"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理报修"}},
                {"id": "n_list", "name": "查询报修", "type": "api_call", "description": "查询报修列表", "config": {"api_id": "api_admin_repair_list", "api_endpoint": "/api/realestate/admin/repairs", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "repairs", "type": "array", "description": "报修列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数"}], "ai_instructions": {"user_message": "查询待处理报修", "action": "查询报修"}},
                {"id": "n_workers", "name": "查询维修工", "type": "api_call", "description": "查询可用维修工", "config": {"api_id": "api_admin_worker_list", "api_endpoint": "/api/realestate/admin/workers", "method": "GET", "parameters": {"status": "available"}}, "outputs": [{"name": "workers", "type": "array", "description": "维修工列表"}], "ai_instructions": {"user_message": "查询可用维修工", "action": "查询维修工"}},
                {"id": "n_assign", "name": "分配维修", "type": "api_call", "description": "分配维修工", "config": {"api_id": "api_admin_repair_assign", "api_endpoint": "/api/realestate/admin/repairs/{repair_id}/assign", "method": "POST", "parameters": {"repair_id": "${repair_id}", "worker_id": "${worker_id}"}}, "outputs": [{"name": "worker_name", "type": "string", "description": "维修工姓名"}], "ai_instructions": {"user_message": "请选择报修并分配维修工", "action": "分配维修"}},
                {"id": "n_complete", "name": "完成维修", "type": "api_call", "description": "完成维修", "config": {"api_id": "api_admin_repair_complete", "api_endpoint": "/api/realestate/admin/repairs/{repair_id}/complete", "method": "POST", "parameters": {"repair_id": "${repair_id}", "result": "${result}", "cost": "${cost}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请填写维修结果", "action": "完成维修"}},
                {"id": "n_notify", "name": "维修通知", "type": "notification", "description": "发送维修完成通知", "config": {"message_template": "报修${repair_id}已完成，维修工：${worker_name}，费用：${cost}元。"}, "outputs": [], "ai_instructions": {"user_message": "维修完成", "action": "发送维修通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报修处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_workers"}, {"source": "n_workers", "target": "n_assign"}, {"source": "n_assign", "target": "n_complete"}, {"source": "n_complete", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：房源审核流程（4步：查询房源 → 查看详情 → 审核房源 → 通知） ==========
        {
            "id": "workflow_admin_house_audit",
            "name": "管理员房源审核流程",
            "description": "审核发布的房源",
            "instruction_variants": ["房源审核流程", "审核房源流程", "房源审批流程", "发布审核流程", "房源审核处理", "审核发布房源", "房源审查流程", "房源审核"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["审核房源", "房源审核", "审核发布"],
            "trigger_keywords": ["审核房源", "房源审核", "审核发布"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审核房源"}},
                {"id": "n_list", "name": "查询房源", "type": "api_call", "description": "查询待审核房源", "config": {"api_id": "api_admin_house_list", "api_endpoint": "/api/realestate/admin/houses", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "houses", "type": "array", "description": "房源列表"}, {"name": "pending_count", "type": "integer", "description": "待审核数"}], "ai_instructions": {"user_message": "查询待审核房源", "action": "查询房源"}},
                {"id": "n_audit", "name": "审核房源", "type": "api_call", "description": "审核房源", "config": {"api_id": "api_admin_house_audit", "api_endpoint": "/api/realestate/admin/houses/{house_id}/audit", "method": "POST", "parameters": {"house_id": "${house_id}", "result": "${result}", "remark": "${remark}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择房源并填写审核结果", "action": "审核房源"}},
                {"id": "n_notify", "name": "审核通知", "type": "notification", "description": "发送审核结果通知", "config": {"message_template": "房源${house_id}审核完成，结果：${result}。"}, "outputs": [], "ai_instructions": {"user_message": "审核完成", "action": "发送审核通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "房源审核完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_audit"}, {"source": "n_audit", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        },

        # ========== 管理员：投诉处理流程（4步：查询投诉 → 查看详情 → 处理投诉 → 通知） ==========
        {
            "id": "workflow_admin_complaint",
            "name": "管理员投诉处理流程",
            "description": "处理物业投诉",
            "instruction_variants": ["投诉处理流程", "物业投诉处理流程", "处理投诉", "投诉处理流程走一下", "投诉处理", "投诉处理流程", "投诉解决流程", "投诉处理操作"],
            "business_scenario": "realestate",
            "status": "active",
            "user_intents": ["处理投诉", "投诉处理", "解决投诉"],
            "trigger_keywords": ["处理投诉", "投诉处理", "解决投诉"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始处理投诉"}},
                {"id": "n_list", "name": "查询投诉", "type": "api_call", "description": "查询投诉列表", "config": {"api_id": "api_admin_complaint_list", "api_endpoint": "/api/realestate/admin/complaints", "method": "GET", "parameters": {"status": "pending"}}, "outputs": [{"name": "complaints", "type": "array", "description": "投诉列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数"}], "ai_instructions": {"user_message": "查询待处理投诉", "action": "查询投诉"}},
                {"id": "n_handle", "name": "处理投诉", "type": "api_call", "description": "处理投诉", "config": {"api_id": "api_admin_complaint_handle", "api_endpoint": "/api/realestate/admin/complaints/{complaint_id}/handle", "method": "POST", "parameters": {"complaint_id": "${complaint_id}", "result": "${result}", "reply": "${reply}"}}, "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}], "ai_instructions": {"user_message": "请选择投诉并填写处理结果", "action": "处理投诉"}},
                {"id": "n_notify", "name": "处理通知", "type": "notification", "description": "发送处理完成通知", "config": {"message_template": "投诉${complaint_id}已处理完成。"}, "outputs": [], "ai_instructions": {"user_message": "处理完成", "action": "发送处理通知"}},
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "投诉处理完成"}}
            ],
            "edges": [{"source": "start", "target": "n_list"}, {"source": "n_list", "target": "n_handle"}, {"source": "n_handle", "target": "n_notify"}, {"source": "n_notify", "target": "end"}]
        }
    ]
}
