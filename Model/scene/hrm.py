# hrm.py - 人力资源场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

HRM_SCENE = {
    "domain": "hrm",
    "apis": [
        # ========== 员工自助 API ==========
        {"id": "api_employee_query", "path": "/api/hrm/employees/{emp_id}", "method": "GET", "desc": "查询员工信息",
         "instruction_variants": ["查询员工信息", "查看员工资料", "我的员工信息", "个人档案", "帮我查员工信息", "员工资料怎么查", "员工信息", "查看个人信息"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "employee", "type": "object", "desc": "员工信息"}, {"name": "emp_id", "type": "string", "desc": "员工ID"}, {"name": "emp_name", "type": "string", "desc": "员工姓名"}, {"name": "department", "type": "string", "desc": "部门"}]},
        {"id": "api_leave_balance", "path": "/api/hrm/leaves/balance", "method": "GET", "desc": "查询假期余额",
         "instruction_variants": ["查询假期余额", "还有多少假", "年假余额", "假期余额", "帮我看看假期", "假期还剩多少", "请假余额", "我的假期"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "annual_leave", "type": "integer", "desc": "年假余额"}, {"name": "sick_leave", "type": "integer", "desc": "病假余额"}, {"name": "personal_leave", "type": "integer", "desc": "事假余额"}]},
        {"id": "api_leave_apply", "workflow_only": True, "path": "/api/hrm/leaves", "method": "POST", "desc": "请假申请",
         "instruction_variants": ["请假申请", "我要请假", "申请请假", "帮我请假", "请个假", "请假怎么申请", "提交请假", "请假流程"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "leave_type", "type": "string", "label": "请假类型", "required": True}, {"name": "start_date", "type": "date", "label": "开始日期", "required": True}, {"name": "end_date", "type": "date", "label": "结束日期", "required": True}, {"name": "reason", "type": "string", "label": "请假原因", "required": True}],
         "response": [{"name": "leave_id", "type": "string", "desc": "请假单号"}, {"name": "status", "type": "string", "desc": "审批状态"}, {"name": "leave_days", "type": "integer", "desc": "请假天数"}]},
        {"id": "api_leave_query", "path": "/api/hrm/leaves", "method": "GET", "desc": "查询请假记录",
         "instruction_variants": ["查询请假记录", "我的请假记录", "请假记录", "请过哪些假", "帮我查请假", "请假历史", "请假明细", "请假情况"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": False}],
         "response": [{"name": "leaves", "type": "array", "desc": "请假记录"}, {"name": "total_days", "type": "integer", "desc": "已请假天数"}]},
        {"id": "api_attendance_query", "path": "/api/hrm/attendance", "method": "GET", "desc": "查询考勤记录",
         "instruction_variants": ["查询考勤记录", "考勤记录", "我的考勤", "打卡记录", "帮我查考勤", "考勤情况", "迟到次数", "考勤查询"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "month", "type": "string", "label": "月份", "required": False}],
         "response": [{"name": "records", "type": "array", "desc": "考勤记录"}, {"name": "late_count", "type": "integer", "desc": "迟到次数"}, {"name": "absent_count", "type": "integer", "desc": "缺勤次数"}]},
        {"id": "api_clock_in", "workflow_only": True, "path": "/api/hrm/clock", "method": "POST", "desc": "打卡",
         "instruction_variants": ["打卡", "上班打卡", "下班打卡", "我要打卡", "帮我打卡", "考勤打卡", "打卡签到", "打卡一下"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "type", "type": "string", "label": "打卡类型", "required": True}, {"name": "location", "type": "string", "label": "打卡地点", "required": False}],
         "response": [{"name": "clock_time", "type": "datetime", "desc": "打卡时间"}, {"name": "status", "type": "string", "desc": "打卡状态"}]},
        {"id": "api_salary_query", "path": "/api/hrm/salary", "method": "GET", "desc": "查询工资单",
         "instruction_variants": ["查询工资单", "工资单", "查工资", "薪资明细", "帮我查工资", "工资条", "工资情况", "查看薪资"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "month", "type": "string", "label": "月份", "required": False}],
         "response": [{"name": "salary", "type": "object", "desc": "工资详情"}, {"name": "base_salary", "type": "float", "desc": "基本工资"}, {"name": "bonus", "type": "float", "desc": "奖金"}, {"name": "deduction", "type": "float", "desc": "扣款"}, {"name": "net_salary", "type": "float", "desc": "实发工资"}]},
        {"id": "api_reimbursement_check", "workflow_only": True, "path": "/api/hrm/reimbursements/check", "method": "POST", "desc": "报销预检查",
         "instruction_variants": ["报销预检查", "报销能不能报", "报销额度检查", "报销前确认", "帮我看看能报多少", "报销资格检查", "报销前审核", "报销额度"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "type", "type": "string", "label": "报销类型", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}],
         "response": [{"name": "can_apply", "type": "boolean", "desc": "是否可申请"}, {"name": "monthly_limit", "type": "float", "desc": "月度限额"}, {"name": "used_amount", "type": "float", "desc": "已用额度"}]},
        {"id": "api_reimbursement_apply", "workflow_only": True, "path": "/api/hrm/reimbursements", "method": "POST", "desc": "报销申请",
         "instruction_variants": ["报销申请", "我要报销", "提交报销", "帮我报销", "报销怎么弄", "申请报销", "报销提交", "费用报销"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "type", "type": "string", "label": "报销类型", "required": True}, {"name": "amount", "type": "float", "label": "金额", "required": True}, {"name": "description", "type": "string", "label": "说明", "required": True}, {"name": "receipts", "type": "array", "label": "发票附件", "required": False}],
         "response": [{"name": "reimbursement_id", "type": "string", "desc": "报销单号"}, {"name": "status", "type": "string", "desc": "审批状态"}]},
        {"id": "api_reimbursement_query", "path": "/api/hrm/reimbursements", "method": "GET", "desc": "查询报销记录",
         "instruction_variants": ["查询报销记录", "报销记录", "我的报销", "报销进度", "帮我查报销", "报销历史", "报销状态", "报销明细"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": False}],
         "response": [{"name": "reimbursements", "type": "array", "desc": "报销记录"}]},
        {"id": "api_meeting_room_list", "path": "/api/hrm/meeting-rooms", "method": "GET", "desc": "查询会议室列表",
         "instruction_variants": ["查询会议室列表", "会议室列表", "会议室有哪些", "查会议室", "帮我找会议室", "会议室情况", "会议室查询", "看看会议室"],
         "request": [{"name": "date", "type": "date", "label": "日期", "required": False}, {"name": "capacity", "type": "integer", "label": "容纳人数", "required": False}],
         "response": [{"name": "rooms", "type": "array", "desc": "会议室列表"}]},
        {"id": "api_meeting_room_check", "workflow_only": True, "path": "/api/hrm/meeting-rooms/check", "method": "POST", "desc": "检查会议室可用性",
         "instruction_variants": ["检查会议室可用性", "会议室可用吗", "查会议室空闲", "会议室是否空", "帮我查会议室", "会议室占用情况", "会议室能用吗", "会议室冲突检查"],
         "request": [{"name": "room_id", "type": "string", "label": "会议室ID", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}, {"name": "start_time", "type": "time", "label": "开始时间", "required": True}, {"name": "end_time", "type": "time", "label": "结束时间", "required": True}],
         "response": [{"name": "available", "type": "boolean", "desc": "是否可用"}, {"name": "conflict_meetings", "type": "array", "desc": "冲突会议"}]},
        {"id": "api_meeting_book", "workflow_only": True, "path": "/api/hrm/meetings", "method": "POST", "desc": "预订会议室",
         "instruction_variants": ["预订会议室", "预约会议室", "订会议室", "帮我订会议室", "会议室预定", "会议室怎么订", "申请会议室", "订个会议室"],
         "request": [{"name": "room_id", "type": "string", "label": "会议室ID", "required": True}, {"name": "date", "type": "date", "label": "日期", "required": True}, {"name": "start_time", "type": "time", "label": "开始时间", "required": True}, {"name": "end_time", "type": "time", "label": "结束时间", "required": True}, {"name": "subject", "type": "string", "label": "会议主题", "required": True}, {"name": "attendees", "type": "array", "label": "参会人员", "required": False}],
         "response": [{"name": "booking_id", "type": "string", "desc": "预订单号"}, {"name": "room_name", "type": "string", "desc": "会议室名称"}]},
        {"id": "api_overtime_check", "workflow_only": True, "path": "/api/hrm/overtime/check", "method": "POST", "desc": "加班预检查",
         "instruction_variants": ["加班预检查", "能不能加班", "加班资格检查", "加班前确认", "帮我查加班", "加班限制", "加班是否可申请", "加班预审"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "date", "type": "date", "label": "加班日期", "required": True}],
         "response": [{"name": "can_apply", "type": "boolean", "desc": "是否可申请"}, {"name": "monthly_hours", "type": "float", "desc": "本月已加班时长"}, {"name": "max_hours", "type": "float", "desc": "月度上限"}]},
        {"id": "api_overtime_apply", "workflow_only": True, "path": "/api/hrm/overtime", "method": "POST", "desc": "加班申请",
         "instruction_variants": ["加班申请", "我要加班", "申请加班", "帮我加班申请", "加班怎么申请", "提交加班", "加班申请表", "申请加班单"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "date", "type": "date", "label": "加班日期", "required": True}, {"name": "start_time", "type": "time", "label": "开始时间", "required": True}, {"name": "end_time", "type": "time", "label": "结束时间", "required": True}, {"name": "reason", "type": "string", "label": "加班原因", "required": True}],
         "response": [{"name": "overtime_id", "type": "string", "desc": "加班单号"}, {"name": "hours", "type": "float", "desc": "加班时长"}]},
        {"id": "api_training_list", "path": "/api/hrm/trainings", "method": "GET", "desc": "查询培训列表",
         "instruction_variants": ["查询培训列表", "培训有哪些", "培训列表", "查看培训", "帮我查培训", "培训课程", "培训项目", "培训信息"],
         "request": [{"name": "category", "type": "string", "label": "培训类别", "required": False}],
         "response": [{"name": "trainings", "type": "array", "desc": "培训列表"}]},
        {"id": "api_training_detail", "workflow_only": True, "path": "/api/hrm/trainings/{training_id}", "method": "GET", "desc": "查询培训详情",
         "instruction_variants": ["查询培训详情", "培训详情", "查看培训信息", "这培训怎么样", "帮我看培训", "培训内容", "课程详情", "培训介绍"],
         "request": [{"name": "training_id", "type": "string", "label": "培训ID", "required": True}],
         "response": [{"name": "training", "type": "object", "desc": "培训详情"}, {"name": "training_name", "type": "string", "desc": "培训名称"}, {"name": "available_seats", "type": "integer", "desc": "剩余名额"}]},
        {"id": "api_training_enroll", "workflow_only": True, "path": "/api/hrm/trainings/enroll", "method": "POST", "desc": "培训报名",
         "instruction_variants": ["培训报名", "报名培训", "参加培训", "帮我报培训", "培训报名申请", "我要报名", "报名课程", "报名培训班"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "training_id", "type": "string", "label": "培训ID", "required": True}],
         "response": [{"name": "enrollment_id", "type": "string", "desc": "报名ID"}, {"name": "training_name", "type": "string", "desc": "培训名称"}]},
        {"id": "api_performance_query", "path": "/api/hrm/performance", "method": "GET", "desc": "查询绩效",
         "instruction_variants": ["查询绩效", "绩效查询", "我的绩效", "绩效评分", "帮我查绩效", "绩效结果", "绩效情况", "绩效考核"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "year", "type": "string", "label": "年份", "required": False}],
         "response": [{"name": "performance", "type": "object", "desc": "绩效详情"}, {"name": "score", "type": "float", "desc": "绩效分数"}, {"name": "rank", "type": "string", "desc": "绩效等级"}]},
        {"id": "api_contract_query", "path": "/api/hrm/contracts", "method": "GET", "desc": "查询劳动合同",
         "instruction_variants": ["查询劳动合同", "查看合同", "我的劳动合同", "合同信息", "帮我查合同", "合同详情", "劳动合同查询", "合同状态"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "contract", "type": "object", "desc": "合同详情"}, {"name": "start_date", "type": "date", "desc": "合同开始日期"}, {"name": "end_date", "type": "date", "desc": "合同结束日期"}]},

        # ========== 管理员审批 API ==========
        {"id": "api_admin_leave_list", "workflow_only": True, "path": "/api/hrm/admin/leaves", "method": "GET", "desc": "查询待审批请假",
         "instruction_variants": ["查询待审批请假", "待审请假", "请假审批列表", "请假待办", "帮我看请假审批", "请假待审核", "请假申请列表", "待批请假"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "department", "type": "string", "label": "部门", "required": False}],
         "response": [{"name": "leaves", "type": "array", "desc": "请假列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数量"}]},
        {"id": "api_admin_leave_detail", "workflow_only": True, "path": "/api/hrm/admin/leaves/{leave_id}", "method": "GET", "desc": "查询请假详情",
         "instruction_variants": ["查询请假详情", "请假详情", "查看请假申请", "请假单详情", "帮我看请假", "请假信息", "请假内容", "请假申请详情"],
         "request": [{"name": "leave_id", "type": "string", "label": "请假单号", "required": True}],
         "response": [{"name": "leave", "type": "object", "desc": "请假详情"}, {"name": "emp_name", "type": "string", "desc": "员工姓名"}, {"name": "leave_type", "type": "string", "desc": "请假类型"}, {"name": "leave_days", "type": "integer", "desc": "请假天数"}]},
        {"id": "api_admin_leave_approve", "workflow_only": True, "path": "/api/hrm/admin/leaves/{leave_id}/approve", "method": "POST", "desc": "审批请假",
         "instruction_variants": ["审批请假", "请假审批", "批准请假", "帮我审批请假", "请假审核", "请假单审批", "审批请假申请", "请假批复"],
         "request": [{"name": "leave_id", "type": "string", "label": "请假单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "leave_id", "type": "string", "desc": "请假单号"}]},
        {"id": "api_admin_reimbursement_list", "workflow_only": True, "path": "/api/hrm/admin/reimbursements", "method": "GET", "desc": "查询待审批报销",
         "instruction_variants": ["查询待审批报销", "待审报销", "报销审批列表", "报销待办", "帮我看报销审批", "报销待审核", "报销申请列表", "待批报销"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "min_amount", "type": "float", "label": "最小金额", "required": False}],
         "response": [{"name": "reimbursements", "type": "array", "desc": "报销列表"}, {"name": "total_amount", "type": "float", "desc": "待审批总金额"}]},
        {"id": "api_admin_reimbursement_detail", "workflow_only": True, "path": "/api/hrm/admin/reimbursements/{id}", "method": "GET", "desc": "查询报销详情",
         "instruction_variants": ["查询报销详情", "报销详情", "查看报销申请", "报销单详情", "帮我看报销", "报销信息", "报销内容", "报销申请详情"],
         "request": [{"name": "reimbursement_id", "type": "string", "label": "报销单号", "required": True}],
         "response": [{"name": "reimbursement", "type": "object", "desc": "报销详情"}, {"name": "emp_name", "type": "string", "desc": "员工姓名"}, {"name": "amount", "type": "float", "desc": "报销金额"}, {"name": "receipts", "type": "array", "desc": "发票附件"}]},
        {"id": "api_admin_reimbursement_approve", "workflow_only": True, "path": "/api/hrm/admin/reimbursements/{id}/approve", "method": "POST", "desc": "审批报销",
         "instruction_variants": ["审批报销", "报销审批", "批准报销", "帮我审批报销", "报销审核", "报销单审批", "审批报销申请", "报销批复"],
         "request": [{"name": "reimbursement_id", "type": "string", "label": "报销单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "approved_amount", "type": "float", "label": "批准金额", "required": False}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "reimbursement_id", "type": "string", "desc": "报销单号"}]},
        {"id": "api_admin_overtime_list", "workflow_only": True, "path": "/api/hrm/admin/overtime", "method": "GET", "desc": "查询待审批加班",
         "instruction_variants": ["查询待审批加班", "待审加班", "加班审批列表", "加班待办", "帮我看加班审批", "加班待审核", "加班申请列表", "待批加班"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "overtime_list", "type": "array", "desc": "加班列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数量"}]},
        {"id": "api_admin_overtime_detail", "workflow_only": True, "path": "/api/hrm/admin/overtime/{id}", "method": "GET", "desc": "查询加班详情",
         "instruction_variants": ["查询加班详情", "加班详情", "查看加班申请", "加班单详情", "帮我看加班", "加班信息", "加班内容", "加班申请详情"],
         "request": [{"name": "overtime_id", "type": "string", "label": "加班单号", "required": True}],
         "response": [{"name": "overtime", "type": "object", "desc": "加班详情"}, {"name": "emp_name", "type": "string", "desc": "员工姓名"}, {"name": "hours", "type": "float", "desc": "加班时长"}]},
        {"id": "api_admin_overtime_approve", "workflow_only": True, "path": "/api/hrm/admin/overtime/{id}/approve", "method": "POST", "desc": "审批加班",
         "instruction_variants": ["审批加班", "加班审批", "批准加班", "帮我审批加班", "加班审核", "加班单审批", "审批加班申请", "加班批复"],
         "request": [{"name": "overtime_id", "type": "string", "label": "加班单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_candidate_list", "workflow_only": True, "path": "/api/hrm/admin/candidates", "method": "GET", "desc": "查询待入职候选人",
         "instruction_variants": ["查询待入职候选人", "候选人列表", "待入职名单", "候选人查询", "帮我看候选人", "候选人信息", "待入职候选", "候选人清单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "candidates", "type": "array", "desc": "候选人列表"}]},
        {"id": "api_admin_candidate_detail", "workflow_only": True, "path": "/api/hrm/admin/candidates/{id}", "method": "GET", "desc": "查询候选人详情",
         "instruction_variants": ["查询候选人详情", "候选人详情", "查看候选人", "候选人信息", "帮我看候选人详情", "候选人资料", "候选人简历", "候选人情况"],
         "request": [{"name": "candidate_id", "type": "string", "label": "候选人ID", "required": True}],
         "response": [{"name": "candidate", "type": "object", "desc": "候选人详情"}, {"name": "name", "type": "string", "desc": "姓名"}, {"name": "position", "type": "string", "desc": "应聘职位"}]},
        {"id": "api_admin_employee_create", "workflow_only": True, "path": "/api/hrm/admin/employees", "method": "POST", "desc": "创建员工账号",
         "instruction_variants": ["创建员工账号", "新建员工", "开通员工账号", "帮我创建员工", "入职建档", "创建员工档案", "新增员工", "开员工账号"],
         "request": [{"name": "name", "type": "string", "label": "姓名", "required": True}, {"name": "id_card", "type": "string", "label": "身份证号", "required": True}, {"name": "phone", "type": "string", "label": "手机号", "required": True}, {"name": "department", "type": "string", "label": "部门", "required": True}, {"name": "position", "type": "string", "label": "职位", "required": True}],
         "response": [{"name": "emp_id", "type": "string", "desc": "员工ID"}, {"name": "email", "type": "string", "desc": "企业邮箱"}]},
        {"id": "api_admin_contract_create", "workflow_only": True, "path": "/api/hrm/admin/contracts", "method": "POST", "desc": "创建劳动合同",
         "instruction_variants": ["创建劳动合同", "生成劳动合同", "签合同", "帮我建合同", "创建合同", "劳动合同生成", "合同创建", "签订劳动合同"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "contract_type", "type": "string", "label": "合同类型", "required": True}, {"name": "start_date", "type": "date", "label": "开始日期", "required": True}, {"name": "end_date", "type": "date", "label": "结束日期", "required": True}, {"name": "salary", "type": "float", "label": "薪资", "required": True}],
         "response": [{"name": "contract_id", "type": "string", "desc": "合同ID"}]},
        {"id": "api_admin_asset_assign", "workflow_only": True, "path": "/api/hrm/admin/assets/assign", "method": "POST", "desc": "分配办公资产",
         "instruction_variants": ["分配办公资产", "发放办公资产", "分配设备", "帮我发资产", "资产分配", "办公资产分配", "发放设备", "资产发放"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "assets", "type": "array", "label": "资产列表", "required": True}],
         "response": [{"name": "assign_id", "type": "string", "desc": "分配单号"}, {"name": "assigned_assets", "type": "array", "desc": "已分配资产"}]},
        {"id": "api_admin_onboard_complete", "workflow_only": True, "path": "/api/hrm/admin/onboard/complete", "method": "POST", "desc": "完成入职",
         "instruction_variants": ["完成入职", "入职完成", "入职办理完成", "帮我完成入职", "入职结案", "员工入职完成", "完成入职流程", "入职确认"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_offboard_list", "workflow_only": True, "path": "/api/hrm/admin/offboard", "method": "GET", "desc": "查询待离职员工",
         "instruction_variants": ["查询待离职员工", "待离职名单", "离职待办", "离职人员列表", "帮我看离职", "待办离职", "离职申请列表", "离职清单"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "employees", "type": "array", "desc": "待离职员工列表"}]},
        {"id": "api_admin_offboard_detail", "workflow_only": True, "path": "/api/hrm/admin/offboard/{emp_id}", "method": "GET", "desc": "查询离职详情",
         "instruction_variants": ["查询离职详情", "离职详情", "查看离职信息", "离职单详情", "帮我看离职", "离职信息", "离职资料", "离职记录"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "employee", "type": "object", "desc": "员工信息"}, {"name": "leave_date", "type": "date", "desc": "离职日期"}, {"name": "handover_status", "type": "string", "desc": "交接状态"}]},
        {"id": "api_admin_handover_check", "workflow_only": True, "path": "/api/hrm/admin/handover/check", "method": "POST", "desc": "检查工作交接",
         "instruction_variants": ["检查工作交接", "交接检查", "查看交接情况", "帮我查交接", "交接是否完成", "交接确认", "交接核验", "交接检查一下"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "handover_complete", "type": "boolean", "desc": "交接是否完成"}, {"name": "pending_items", "type": "array", "desc": "待交接事项"}]},
        {"id": "api_admin_asset_return", "workflow_only": True, "path": "/api/hrm/admin/assets/return", "method": "POST", "desc": "资产归还",
         "instruction_variants": ["资产归还", "归还资产", "收回设备", "帮我收回资产", "资产回收", "设备归还", "资产归还登记", "收回办公资产"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "assets", "type": "array", "label": "归还资产", "required": True}],
         "response": [{"name": "return_id", "type": "string", "desc": "归还单号"}, {"name": "returned_assets", "type": "array", "desc": "已归还资产"}]},
        {"id": "api_admin_salary_settle", "workflow_only": True, "path": "/api/hrm/admin/salary/settle", "method": "POST", "desc": "工资结算",
         "instruction_variants": ["工资结算", "离职工资结算", "结算工资", "帮我结算工资", "薪资结算", "工资结算处理", "结算薪资", "离职结算"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "settlement_amount", "type": "float", "desc": "结算金额"}, {"name": "settlement_id", "type": "string", "desc": "结算单号"}]},
        {"id": "api_admin_offboard_complete", "workflow_only": True, "path": "/api/hrm/admin/offboard/complete", "method": "POST", "desc": "完成离职",
         "instruction_variants": ["完成离职", "离职完成", "离职办理完成", "帮我完成离职", "离职结案", "员工离职完成", "完成离职流程", "离职确认"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_salary_list", "workflow_only": True, "path": "/api/hrm/admin/salary/adjust/list", "method": "GET", "desc": "查询待调薪员工",
         "instruction_variants": ["查询待调薪员工", "待调薪名单", "调薪列表", "调薪候选", "帮我查调薪员工", "调薪员工查询", "待调薪人员", "调薪待办"],
         "request": [{"name": "department", "type": "string", "label": "部门", "required": False}],
         "response": [{"name": "employees", "type": "array", "desc": "员工列表"}]},
        {"id": "api_admin_salary_history", "workflow_only": True, "path": "/api/hrm/admin/salary/history/{emp_id}", "method": "GET", "desc": "查询薪资历史",
         "instruction_variants": ["查询薪资历史", "薪资历史", "薪资记录", "历史工资", "帮我查薪资历史", "工资历史", "薪资变动", "薪资记录查询"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}],
         "response": [{"name": "history", "type": "array", "desc": "薪资历史"}, {"name": "current_salary", "type": "float", "desc": "当前薪资"}]},
        {"id": "api_admin_salary_adjust", "workflow_only": True, "path": "/api/hrm/admin/salary/adjust", "method": "POST", "desc": "调薪申请",
         "instruction_variants": ["调薪申请", "提交调薪", "申请调薪", "帮我调薪", "调薪怎么申请", "发起调薪", "调薪单", "薪资调整申请"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "new_salary", "type": "float", "label": "新薪资", "required": True}, {"name": "effective_date", "type": "date", "label": "生效日期", "required": True}, {"name": "reason", "type": "string", "label": "调薪原因", "required": True}],
         "response": [{"name": "adjust_id", "type": "string", "desc": "调薪单号"}]},
        {"id": "api_admin_salary_approve", "workflow_only": True, "path": "/api/hrm/admin/salary/adjust/{id}/approve", "method": "POST", "desc": "调薪审批",
         "instruction_variants": ["调薪审批", "审批调薪", "批准调薪", "帮我审批调薪", "调薪审核", "调薪单审批", "调薪批复", "调薪审批处理"],
         "request": [{"name": "adjust_id", "type": "string", "label": "调薪单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_transfer_list", "workflow_only": True, "path": "/api/hrm/admin/transfer/list", "method": "GET", "desc": "查询待调岗员工",
         "instruction_variants": ["查询待调岗员工", "待调岗名单", "调岗列表", "调岗候选", "帮我查调岗员工", "调岗员工查询", "待调岗人员", "调岗待办"],
         "request": [{"name": "department", "type": "string", "label": "部门", "required": False}],
         "response": [{"name": "employees", "type": "array", "desc": "员工列表"}]},
        {"id": "api_admin_transfer_apply", "workflow_only": True, "path": "/api/hrm/admin/transfer", "method": "POST", "desc": "员工调岗",
         "instruction_variants": ["员工调岗", "发起调岗", "申请调岗", "帮我调岗", "调岗申请", "岗位调整", "部门调动", "调岗办理"],
         "request": [{"name": "emp_id", "type": "string", "label": "员工ID", "required": True}, {"name": "new_department", "type": "string", "label": "新部门", "required": True}, {"name": "new_position", "type": "string", "label": "新职位", "required": True}, {"name": "effective_date", "type": "date", "label": "生效日期", "required": True}, {"name": "reason", "type": "string", "label": "调岗原因", "required": True}],
         "response": [{"name": "transfer_id", "type": "string", "desc": "调岗单号"}]},
        {"id": "api_admin_transfer_approve", "workflow_only": True, "path": "/api/hrm/admin/transfer/{id}/approve", "method": "POST", "desc": "调岗审批",
         "instruction_variants": ["调岗审批", "审批调岗", "批准调岗", "帮我审批调岗", "调岗审核", "调岗单审批", "调岗批复", "调岗审批处理"],
         "request": [{"name": "transfer_id", "type": "string", "label": "调岗单号", "required": True}, {"name": "action", "type": "string", "label": "审批动作", "required": True}, {"name": "comment", "type": "string", "label": "审批意见", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        # ========== 管理员统计 API ==========
        {"id": "api_admin_attendance_stats", "path": "/api/hrm/admin/attendance/stats", "method": "GET", "desc": "查询考勤统计", "name": "考勤统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询考勤统计", "考勤统计", "考勤数据", "出勤统计", "帮我看考勤", "考勤报表", "考勤趋势", "考勤情况"],
         "request": [], "response": [{"name": "today_count", "type": "integer", "desc": "今日出勤"}, {"name": "daily_trend", "type": "array", "desc": "每日趋势"}]},
        {"id": "api_admin_dept_stats", "path": "/api/hrm/admin/dept/stats", "method": "GET", "desc": "查询部门统计", "name": "部门统计", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询部门统计", "部门统计", "部门人数", "部门分布", "帮我看部门数据", "部门人数统计", "部门统计报表", "部门情况"],
         "request": [], "response": [{"name": "departments", "type": "array", "desc": "部门"}, {"name": "counts", "type": "array", "desc": "人数"}]},
        {"id": "api_admin_leave_stats", "path": "/api/hrm/admin/leave/stats", "method": "GET", "desc": "查询请假统计", "name": "请假统计", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询请假统计", "请假统计", "请假数据", "请假类型统计", "帮我看请假", "请假报表", "请假情况", "请假人次"],
         "request": [], "response": [{"name": "types", "type": "array", "desc": "请假类型"}, {"name": "counts", "type": "array", "desc": "请假人次"}]},
        {"id": "api_admin_salary_stats", "path": "/api/hrm/admin/salary/stats", "method": "GET", "desc": "查询薪资统计", "name": "薪资统计", "response_type": "chart", "chart_type": "line",
         "instruction_variants": ["查询薪资统计", "薪资统计", "薪资数据", "薪资总额", "帮我看薪资", "薪资报表", "薪资趋势", "工资统计"],
         "request": [], "response": [{"name": "months", "type": "array", "desc": "月份"}, {"name": "total_salary", "type": "array", "desc": "薪资总额"}]},
    ],

    "workflows": [
        # ========== 员工请假流程（6步：查询余额 → 选择类型 → 填写申请 → 提交 → 等待审批 → 通知） ==========
        {
            "id": "workflow_leave_apply",
            "name": "请假申请流程",
            "description": "员工请假申请完整流程，包括假期余额查询、类型选择、申请提交和审批通知",
            "instruction_variants": ["请假流程", "我要请假", "请假申请流程", "帮我请假", "请假怎么办", "请假流程走一下", "请假申请", "请个假"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["请假", "休假", "年假", "病假", "事假", "调休"],
            "trigger_keywords": ["请假", "休假", "年假", "病假"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始请假申请流程"}},
                {
                    "id": "balance_query",
                    "name": "查询假期余额",
                    "type": "api_call",
                    "description": "查询员工各类假期余额",
                    "config": {"api_id": "api_leave_balance", "api_endpoint": "/api/hrm/leaves/balance", "method": "GET", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "annual_leave", "type": "integer", "description": "年假余额"}, {"name": "sick_leave", "type": "integer", "description": "病假余额"}, {"name": "personal_leave", "type": "integer", "description": "事假余额"}],
                    "ai_instructions": {"user_message": "正在查询您的假期余额", "action": "查询假期余额"}
                },
                {
                    "id": "leave_apply",
                    "name": "填写请假申请",
                    "type": "api_call",
                    "description": "填写请假类型、日期和原因",
                    "config": {"api_id": "api_leave_apply", "api_endpoint": "/api/hrm/leaves", "method": "POST", "parameters": {"emp_id": "${emp_id}", "leave_type": "${leave_type}", "start_date": "${start_date}", "end_date": "${end_date}", "reason": "${reason}"}},
                    "outputs": [{"name": "leave_id", "type": "string", "description": "请假单号"}, {"name": "status", "type": "string", "description": "审批状态"}, {"name": "leave_days", "type": "integer", "description": "请假天数"}],
                    "ai_instructions": {"user_message": "请选择请假类型并填写请假日期和原因", "action": "提交请假申请"}
                },
                {
                    "id": "leave_notification",
                    "name": "申请提交通知",
                    "type": "notification",
                    "description": "发送请假申请提交成功通知",
                    "config": {"message_template": "请假申请已提交！单号：${leave_id}，请假${leave_days}天，等待主管审批。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "请假申请已提交", "action": "发送申请通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "请假申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "balance_query"},
                {"source": "balance_query", "target": "leave_apply"},
                {"source": "leave_apply", "target": "leave_notification"},
                {"source": "leave_notification", "target": "end"}
            ]
        },
        # ========== 员工报销流程（6步：预检查 → 填写申请 → 上传发票 → 提交 → 等待审批 → 通知） ==========
        {
            "id": "workflow_reimbursement_apply",
            "name": "报销申请流程",
            "description": "员工报销申请完整流程，包括额度检查、申请填写、发票上传和审批通知",
            "instruction_variants": ["报销流程", "我要报销", "报销申请流程", "帮我报销", "报销怎么走", "报销全流程", "提交报销", "报销申请"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["报销", "费用报销", "差旅报销", "交通报销"],
            "trigger_keywords": ["报销", "费用", "差旅"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始报销申请流程"}},
                {
                    "id": "reimbursement_check",
                    "name": "报销预检查",
                    "type": "api_call",
                    "description": "检查报销额度和限制",
                    "config": {"api_id": "api_reimbursement_check", "api_endpoint": "/api/hrm/reimbursements/check", "method": "POST", "parameters": {"emp_id": "${emp_id}", "type": "${type}", "amount": "${amount}"}},
                    "outputs": [{"name": "can_apply", "type": "boolean", "description": "是否可申请"}, {"name": "monthly_limit", "type": "float", "description": "月度限额"}, {"name": "used_amount", "type": "float", "description": "已用额度"}],
                    "ai_instructions": {"user_message": "请选择报销类型和金额进行预检查", "action": "检查报销额度"}
                },
                {
                    "id": "reimbursement_apply",
                    "name": "填写报销申请",
                    "type": "api_call",
                    "description": "填写报销详情和上传发票",
                    "config": {"api_id": "api_reimbursement_apply", "api_endpoint": "/api/hrm/reimbursements", "method": "POST", "parameters": {"emp_id": "${emp_id}", "type": "${type}", "amount": "${amount}", "description": "${description}", "receipts": "${receipts}"}},
                    "outputs": [{"name": "reimbursement_id", "type": "string", "description": "报销单号"}, {"name": "status", "type": "string", "description": "审批状态"}],
                    "ai_instructions": {"user_message": "请填写报销说明并上传发票", "action": "提交报销申请"}
                },
                {
                    "id": "reimbursement_notification",
                    "name": "申请提交通知",
                    "type": "notification",
                    "description": "发送报销申请提交成功通知",
                    "config": {"message_template": "报销申请已提交！单号：${reimbursement_id}，金额：${amount}元，等待审批。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "报销申请已提交", "action": "发送申请通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报销申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "reimbursement_check"},
                {"source": "reimbursement_check", "target": "reimbursement_apply"},
                {"source": "reimbursement_apply", "target": "reimbursement_notification"},
                {"source": "reimbursement_notification", "target": "end"}
            ]
        },
        # ========== 员工加班申请流程（5步：预检查 → 填写申请 → 提交 → 等待审批 → 通知） ==========
        {
            "id": "workflow_overtime_apply",
            "name": "加班申请流程",
            "description": "员工加班申请完整流程，包括加班时长检查、申请填写和审批通知",
            "instruction_variants": ["加班流程", "我要加班", "加班申请流程", "帮我申请加班", "加班怎么申请", "加班全流程", "提交加班", "申请加班"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["加班", "加班申请", "申请加班"],
            "trigger_keywords": ["加班", "加班申请"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始加班申请流程"}},
                {
                    "id": "overtime_check",
                    "name": "加班预检查",
                    "type": "api_call",
                    "description": "检查本月加班时长限制",
                    "config": {"api_id": "api_overtime_check", "api_endpoint": "/api/hrm/overtime/check", "method": "POST", "parameters": {"emp_id": "${emp_id}", "date": "${date}"}},
                    "outputs": [{"name": "can_apply", "type": "boolean", "description": "是否可申请"}, {"name": "monthly_hours", "type": "float", "description": "本月已加班时长"}, {"name": "max_hours", "type": "float", "description": "月度上限"}],
                    "ai_instructions": {"user_message": "正在检查您的加班时长限制", "action": "检查加班限制"}
                },
                {
                    "id": "overtime_apply",
                    "name": "填写加班申请",
                    "type": "api_call",
                    "description": "填写加班日期、时间和原因",
                    "config": {"api_id": "api_overtime_apply", "api_endpoint": "/api/hrm/overtime", "method": "POST", "parameters": {"emp_id": "${emp_id}", "date": "${date}", "start_time": "${start_time}", "end_time": "${end_time}", "reason": "${reason}"}},
                    "outputs": [{"name": "overtime_id", "type": "string", "description": "加班单号"}, {"name": "hours", "type": "float", "description": "加班时长"}],
                    "ai_instructions": {"user_message": "请填写加班日期、时间和原因", "action": "提交加班申请"}
                },
                {
                    "id": "overtime_notification",
                    "name": "申请提交通知",
                    "type": "notification",
                    "description": "发送加班申请提交成功通知",
                    "config": {"message_template": "加班申请已提交！单号：${overtime_id}，加班${hours}小时，等待主管审批。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "加班申请已提交", "action": "发送申请通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "加班申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "overtime_check"},
                {"source": "overtime_check", "target": "overtime_apply"},
                {"source": "overtime_apply", "target": "overtime_notification"},
                {"source": "overtime_notification", "target": "end"}
            ]
        },
        # ========== 会议室预订流程（5步：查询列表 → 检查可用性 → 填写预订 → 提交 → 通知） ==========
        {
            "id": "workflow_meeting_book",
            "name": "会议室预订流程",
            "description": "会议室预订完整流程，包括会议室查询、可用性检查和预订确认",
            "instruction_variants": ["会议室预订流程", "订会议室流程", "我要订会议室", "帮我订会议室", "会议室怎么订", "预约会议室流程", "预订会议室", "会议室预约"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["预订会议室", "订会议室", "会议室"],
            "trigger_keywords": ["会议室", "预订会议"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始会议室预订流程"}},
                {
                    "id": "room_list",
                    "name": "查询会议室",
                    "type": "api_call",
                    "description": "查询可用会议室列表",
                    "config": {"api_id": "api_meeting_room_list", "api_endpoint": "/api/hrm/meeting-rooms", "method": "GET", "parameters": {"date": "${date}", "capacity": "${capacity}"}},
                    "outputs": [{"name": "rooms", "type": "array", "description": "会议室列表"}],
                    "ai_instructions": {"user_message": "请选择日期和所需容纳人数查询会议室", "action": "查询会议室"}
                },
                {
                    "id": "room_check",
                    "name": "检查可用性",
                    "type": "api_call",
                    "description": "检查选定会议室的时间段是否可用",
                    "config": {"api_id": "api_meeting_room_check", "api_endpoint": "/api/hrm/meeting-rooms/check", "method": "POST", "parameters": {"room_id": "${room_id}", "date": "${date}", "start_time": "${start_time}", "end_time": "${end_time}"}},
                    "outputs": [{"name": "available", "type": "boolean", "description": "是否可用"}, {"name": "conflict_meetings", "type": "array", "description": "冲突会议"}],
                    "ai_instructions": {"user_message": "请选择会议室和时间段检查可用性", "action": "检查可用性"}
                },
                {
                    "id": "meeting_book",
                    "name": "预订会议室",
                    "type": "api_call",
                    "description": "填写会议信息并预订",
                    "config": {"api_id": "api_meeting_book", "api_endpoint": "/api/hrm/meetings", "method": "POST", "parameters": {"room_id": "${room_id}", "date": "${date}", "start_time": "${start_time}", "end_time": "${end_time}", "subject": "${subject}", "attendees": "${attendees}"}},
                    "outputs": [{"name": "booking_id", "type": "string", "description": "预订单号"}, {"name": "room_name", "type": "string", "description": "会议室名称"}],
                    "ai_instructions": {"user_message": "请填写会议主题和参会人员", "action": "预订会议室"}
                },
                {
                    "id": "booking_notification",
                    "name": "预订成功通知",
                    "type": "notification",
                    "description": "发送会议室预订成功通知",
                    "config": {"message_template": "会议室预订成功！${room_name}，${date} ${start_time}-${end_time}，预订号：${booking_id}"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "会议室预订成功", "action": "发送预订通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "会议室预订完成"}}
            ],
            "edges": [
                {"source": "start", "target": "room_list"},
                {"source": "room_list", "target": "room_check"},
                {"source": "room_check", "target": "meeting_book"},
                {"source": "meeting_book", "target": "booking_notification"},
                {"source": "booking_notification", "target": "end"}
            ]
        },
        # ========== 培训报名流程（5步：查询列表 → 查看详情 → 报名 → 确认 → 通知） ==========
        {
            "id": "workflow_training_enroll",
            "name": "培训报名流程",
            "description": "员工培训报名完整流程，包括培训查询、详情查看和报名确认",
            "instruction_variants": ["培训报名流程", "报名培训流程", "我要报名培训", "帮我报名培训", "培训怎么报名", "培训报名", "报名课程流程", "培训报名申请"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["培训报名", "报名培训", "参加培训"],
            "trigger_keywords": ["培训", "报名培训"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始培训报名流程"}},
                {
                    "id": "training_list",
                    "name": "查询培训列表",
                    "type": "api_call",
                    "description": "查询可报名的培训课程",
                    "config": {"api_id": "api_training_list", "api_endpoint": "/api/hrm/trainings", "method": "GET", "parameters": {"category": "${category}"}},
                    "outputs": [{"name": "trainings", "type": "array", "description": "培训列表"}],
                    "ai_instructions": {"user_message": "请选择培训类别查询可报名课程", "action": "查询培训列表"}
                },
                {
                    "id": "training_detail",
                    "name": "查看培训详情",
                    "type": "api_call",
                    "description": "查看培训课程详细信息",
                    "config": {"api_id": "api_training_detail", "api_endpoint": "/api/hrm/trainings/{training_id}", "method": "GET", "parameters": {"training_id": "${training_id}"}},
                    "outputs": [{"name": "training", "type": "object", "description": "培训详情"}, {"name": "training_name", "type": "string", "description": "培训名称"}, {"name": "available_seats", "type": "integer", "description": "剩余名额"}],
                    "ai_instructions": {"user_message": "请选择要查看的培训课程", "action": "查看培训详情"}
                },
                {
                    "id": "training_enroll",
                    "name": "报名培训",
                    "type": "api_call",
                    "description": "确认报名培训课程",
                    "config": {"api_id": "api_training_enroll", "api_endpoint": "/api/hrm/trainings/enroll", "method": "POST", "parameters": {"emp_id": "${emp_id}", "training_id": "${training_id}"}},
                    "outputs": [{"name": "enrollment_id", "type": "string", "description": "报名ID"}, {"name": "training_name", "type": "string", "description": "培训名称"}],
                    "ai_instructions": {"user_message": "确认报名该培训课程", "action": "报名培训"}
                },
                {
                    "id": "enroll_notification",
                    "name": "报名成功通知",
                    "type": "notification",
                    "description": "发送培训报名成功通知",
                    "config": {"message_template": "培训报名成功！课程：${training_name}，报名号：${enrollment_id}，请按时参加。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "培训报名成功", "action": "发送报名通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "培训报名完成"}}
            ],
            "edges": [
                {"source": "start", "target": "training_list"},
                {"source": "training_list", "target": "training_detail"},
                {"source": "training_detail", "target": "training_enroll"},
                {"source": "training_enroll", "target": "enroll_notification"},
                {"source": "enroll_notification", "target": "end"}
            ]
        },

        # ========== 管理员：请假审批流程（6步：查询待审批 → 查看详情 → 审核信息 → 审批决定 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_leave_approve",
            "name": "请假审批流程",
            "description": "管理员请假审批完整流程，包括待审批列表查询、详情查看、审批决定和通知",
            "instruction_variants": ["请假审批流程", "审批请假流程", "我要审批请假", "请假审核流程", "处理请假申请", "请假审批", "审批请假单", "请假审批处理"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["审批请假", "请假审批", "处理请假"],
            "trigger_keywords": ["审批请假", "请假审批"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始请假审批流程"}},
                {
                    "id": "leave_list",
                    "name": "查询待审批请假",
                    "type": "api_call",
                    "description": "查询待审批的请假申请列表",
                    "config": {"api_id": "api_admin_leave_list", "api_endpoint": "/api/hrm/admin/leaves", "method": "GET", "parameters": {"status": "pending", "department": "${department}"}},
                    "outputs": [{"name": "leaves", "type": "array", "description": "请假列表"}, {"name": "pending_count", "type": "integer", "description": "待审批数量"}],
                    "ai_instructions": {"user_message": "正在查询待审批的请假申请", "action": "查询待审批请假"}
                },
                {
                    "id": "leave_detail",
                    "name": "查看请假详情",
                    "type": "api_call",
                    "description": "查看请假申请详细信息",
                    "config": {"api_id": "api_admin_leave_detail", "api_endpoint": "/api/hrm/admin/leaves/{leave_id}", "method": "GET", "parameters": {"leave_id": "${leave_id}"}},
                    "outputs": [{"name": "leave", "type": "object", "description": "请假详情"}, {"name": "emp_name", "type": "string", "description": "员工姓名"}, {"name": "leave_type", "type": "string", "description": "请假类型"}, {"name": "leave_days", "type": "integer", "description": "请假天数"}],
                    "ai_instructions": {"user_message": "请选择要查看的请假申请", "action": "查看请假详情"}
                },
                {
                    "id": "leave_approve",
                    "name": "审批请假",
                    "type": "api_call",
                    "description": "对请假申请进行审批",
                    "config": {"api_id": "api_admin_leave_approve", "api_endpoint": "/api/hrm/admin/leaves/{leave_id}/approve", "method": "POST", "parameters": {"leave_id": "${leave_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "leave_id", "type": "string", "description": "请假单号"}],
                    "ai_instructions": {"user_message": "请选择审批动作（通过/拒绝）并填写审批意见", "action": "审批请假"}
                },
                {
                    "id": "approve_notification",
                    "name": "审批结果通知",
                    "type": "notification",
                    "description": "发送审批结果通知给员工",
                    "config": {"message_template": "请假审批完成！单号：${leave_id}，员工：${emp_name}，审批结果已通知员工。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "请假审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "leave_list"},
                {"source": "leave_list", "target": "leave_detail"},
                {"source": "leave_detail", "target": "leave_approve"},
                {"source": "leave_approve", "target": "approve_notification"},
                {"source": "approve_notification", "target": "end"}
            ]
        },
        # ========== 管理员：报销审批流程（6步：查询待审批 → 查看详情 → 核对发票 → 审批决定 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_reimbursement_approve",
            "name": "报销审批流程",
            "description": "管理员报销审批完整流程，包括待审批列表查询、详情查看、发票核对、审批决定和通知",
            "instruction_variants": ["报销审批流程", "审批报销流程", "我要审批报销", "报销审核流程", "处理报销申请", "报销审批", "审批报销单", "报销审批处理"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["审批报销", "报销审批", "处理报销"],
            "trigger_keywords": ["审批报销", "报销审批"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始报销审批流程"}},
                {
                    "id": "reimbursement_list",
                    "name": "查询待审批报销",
                    "type": "api_call",
                    "description": "查询待审批的报销申请列表",
                    "config": {"api_id": "api_admin_reimbursement_list", "api_endpoint": "/api/hrm/admin/reimbursements", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "reimbursements", "type": "array", "description": "报销列表"}, {"name": "total_amount", "type": "float", "description": "待审批总金额"}],
                    "ai_instructions": {"user_message": "正在查询待审批的报销申请", "action": "查询待审批报销"}
                },
                {
                    "id": "reimbursement_detail",
                    "name": "查看报销详情",
                    "type": "api_call",
                    "description": "查看报销申请详细信息和发票",
                    "config": {"api_id": "api_admin_reimbursement_detail", "api_endpoint": "/api/hrm/admin/reimbursements/{id}", "method": "GET", "parameters": {"reimbursement_id": "${reimbursement_id}"}},
                    "outputs": [{"name": "reimbursement", "type": "object", "description": "报销详情"}, {"name": "emp_name", "type": "string", "description": "员工姓名"}, {"name": "amount", "type": "float", "description": "报销金额"}, {"name": "receipts", "type": "array", "description": "发票附件"}],
                    "ai_instructions": {"user_message": "请选择要查看的报销申请", "action": "查看报销详情"}
                },
                {
                    "id": "reimbursement_approve",
                    "name": "审批报销",
                    "type": "api_call",
                    "description": "对报销申请进行审批",
                    "config": {"api_id": "api_admin_reimbursement_approve", "api_endpoint": "/api/hrm/admin/reimbursements/{id}/approve", "method": "POST", "parameters": {"reimbursement_id": "${reimbursement_id}", "action": "${action}", "approved_amount": "${approved_amount}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "reimbursement_id", "type": "string", "description": "报销单号"}],
                    "ai_instructions": {"user_message": "请选择审批动作、批准金额并填写审批意见", "action": "审批报销"}
                },
                {
                    "id": "approve_notification",
                    "name": "审批结果通知",
                    "type": "notification",
                    "description": "发送审批结果通知给员工",
                    "config": {"message_template": "报销审批完成！单号：${reimbursement_id}，员工：${emp_name}，批准金额：${approved_amount}元。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报销审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "reimbursement_list"},
                {"source": "reimbursement_list", "target": "reimbursement_detail"},
                {"source": "reimbursement_detail", "target": "reimbursement_approve"},
                {"source": "reimbursement_approve", "target": "approve_notification"},
                {"source": "approve_notification", "target": "end"}
            ]
        },
        # ========== 管理员：加班审批流程（5步：查询待审批 → 查看详情 → 审批决定 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_overtime_approve",
            "name": "加班审批流程",
            "description": "管理员加班审批完整流程，包括待审批列表查询、详情查看、审批决定和通知",
            "instruction_variants": ["加班审批流程", "审批加班流程", "我要审批加班", "加班审核流程", "处理加班申请", "加班审批", "审批加班单", "加班审批处理"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["审批加班", "加班审批", "处理加班"],
            "trigger_keywords": ["审批加班", "加班审批"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始加班审批流程"}},
                {
                    "id": "overtime_list",
                    "name": "查询待审批加班",
                    "type": "api_call",
                    "description": "查询待审批的加班申请列表",
                    "config": {"api_id": "api_admin_overtime_list", "api_endpoint": "/api/hrm/admin/overtime", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "overtime_list", "type": "array", "description": "加班列表"}, {"name": "pending_count", "type": "integer", "description": "待审批数量"}],
                    "ai_instructions": {"user_message": "正在查询待审批的加班申请", "action": "查询待审批加班"}
                },
                {
                    "id": "overtime_detail",
                    "name": "查看加班详情",
                    "type": "api_call",
                    "description": "查看加班申请详细信息",
                    "config": {"api_id": "api_admin_overtime_detail", "api_endpoint": "/api/hrm/admin/overtime/{id}", "method": "GET", "parameters": {"overtime_id": "${overtime_id}"}},
                    "outputs": [{"name": "overtime", "type": "object", "description": "加班详情"}, {"name": "emp_name", "type": "string", "description": "员工姓名"}, {"name": "hours", "type": "float", "description": "加班时长"}],
                    "ai_instructions": {"user_message": "请选择要查看的加班申请", "action": "查看加班详情"}
                },
                {
                    "id": "overtime_approve",
                    "name": "审批加班",
                    "type": "api_call",
                    "description": "对加班申请进行审批",
                    "config": {"api_id": "api_admin_overtime_approve", "api_endpoint": "/api/hrm/admin/overtime/{id}/approve", "method": "POST", "parameters": {"overtime_id": "${overtime_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择审批动作并填写审批意见", "action": "审批加班"}
                },
                {
                    "id": "approve_notification",
                    "name": "审批结果通知",
                    "type": "notification",
                    "description": "发送审批结果通知给员工",
                    "config": {"message_template": "加班审批完成！员工：${emp_name}，加班${hours}小时，审批结果已通知员工。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "加班审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "overtime_list"},
                {"source": "overtime_list", "target": "overtime_detail"},
                {"source": "overtime_detail", "target": "overtime_approve"},
                {"source": "overtime_approve", "target": "approve_notification"},
                {"source": "approve_notification", "target": "end"}
            ]
        },
        # ========== 管理员：员工入职流程（8步：查询候选人 → 查看详情 → 创建账号 → 签订合同 → 分配资产 → 开通权限 → 完成入职 → 通知） ==========
        {
            "id": "workflow_admin_onboard",
            "name": "员工入职流程",
            "description": "管理员办理员工入职完整流程，包括候选人确认、账号创建、合同签订、资产分配和权限开通",
            "instruction_variants": ["员工入职流程", "入职办理流程", "办理入职", "新员工入职", "入职全流程", "员工入职办理", "入职流程走一下", "入职处理"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["办理入职", "员工入职", "新员工入职"],
            "trigger_keywords": ["入职", "办理入职", "新员工"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始员工入职流程"}},
                {
                    "id": "candidate_list",
                    "name": "查询待入职候选人",
                    "type": "api_call",
                    "description": "查询待入职的候选人列表",
                    "config": {"api_id": "api_admin_candidate_list", "api_endpoint": "/api/hrm/admin/candidates", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "candidates", "type": "array", "description": "候选人列表"}],
                    "ai_instructions": {"user_message": "正在查询待入职的候选人", "action": "查询待入职候选人"}
                },
                {
                    "id": "candidate_detail",
                    "name": "查看候选人详情",
                    "type": "api_call",
                    "description": "查看候选人详细信息",
                    "config": {"api_id": "api_admin_candidate_detail", "api_endpoint": "/api/hrm/admin/candidates/{id}", "method": "GET", "parameters": {"candidate_id": "${candidate_id}"}},
                    "outputs": [{"name": "candidate", "type": "object", "description": "候选人详情"}, {"name": "name", "type": "string", "description": "姓名"}, {"name": "position", "type": "string", "description": "应聘职位"}],
                    "ai_instructions": {"user_message": "请选择要办理入职的候选人", "action": "查看候选人详情"}
                },
                {
                    "id": "employee_create",
                    "name": "创建员工账号",
                    "type": "api_call",
                    "description": "为新员工创建系统账号",
                    "config": {"api_id": "api_admin_employee_create", "api_endpoint": "/api/hrm/admin/employees", "method": "POST", "parameters": {"name": "${name}", "id_card": "${id_card}", "phone": "${phone}", "department": "${department}", "position": "${position}"}},
                    "outputs": [{"name": "emp_id", "type": "string", "description": "员工ID"}, {"name": "email", "type": "string", "description": "企业邮箱"}],
                    "ai_instructions": {"user_message": "正在创建员工账号", "action": "创建员工账号"}
                },
                {
                    "id": "contract_create",
                    "name": "签订劳动合同",
                    "type": "api_call",
                    "description": "创建并签订劳动合同",
                    "config": {"api_id": "api_admin_contract_create", "api_endpoint": "/api/hrm/admin/contracts", "method": "POST", "parameters": {"emp_id": "${emp_id}", "contract_type": "${contract_type}", "start_date": "${start_date}", "end_date": "${end_date}", "salary": "${salary}"}},
                    "outputs": [{"name": "contract_id", "type": "string", "description": "合同ID"}],
                    "ai_instructions": {"user_message": "请填写合同信息", "action": "签订劳动合同"}
                },
                {
                    "id": "asset_assign",
                    "name": "分配办公资产",
                    "type": "api_call",
                    "description": "为新员工分配办公设备和资产",
                    "config": {"api_id": "api_admin_asset_assign", "api_endpoint": "/api/hrm/admin/assets/assign", "method": "POST", "parameters": {"emp_id": "${emp_id}", "assets": "${assets}"}},
                    "outputs": [{"name": "assign_id", "type": "string", "description": "分配单号"}, {"name": "assigned_assets", "type": "array", "description": "已分配资产"}],
                    "ai_instructions": {"user_message": "请选择要分配的办公资产", "action": "分配办公资产"}
                },
                {
                    "id": "onboard_complete",
                    "name": "完成入职",
                    "type": "api_call",
                    "description": "完成入职流程",
                    "config": {"api_id": "api_admin_onboard_complete", "api_endpoint": "/api/hrm/admin/onboard/complete", "method": "POST", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "正在完成入职流程", "action": "完成入职"}
                },
                {
                    "id": "onboard_notification",
                    "name": "入职完成通知",
                    "type": "notification",
                    "description": "发送入职完成通知",
                    "config": {"message_template": "员工入职完成！员工：${name}，工号：${emp_id}，邮箱：${email}，已分配资产并开通权限。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "入职办理完成", "action": "发送入职通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "员工入职完成"}}
            ],
            "edges": [
                {"source": "start", "target": "candidate_list"},
                {"source": "candidate_list", "target": "candidate_detail"},
                {"source": "candidate_detail", "target": "employee_create"},
                {"source": "employee_create", "target": "contract_create"},
                {"source": "contract_create", "target": "asset_assign"},
                {"source": "asset_assign", "target": "onboard_complete"},
                {"source": "onboard_complete", "target": "onboard_notification"},
                {"source": "onboard_notification", "target": "end"}
            ]
        },

        # ========== 管理员：员工离职流程（8步：查询待离职 → 查看详情 → 检查交接 → 资产归还 → 工资结算 → 权限回收 → 完成离职 → 通知） ==========
        {
            "id": "workflow_admin_offboard",
            "name": "员工离职流程",
            "description": "管理员办理员工离职完整流程，包括工作交接检查、资产归还、工资结算和权限回收",
            "instruction_variants": ["员工离职流程", "离职办理流程", "办理离职", "员工离职处理", "离职全流程", "离职手续", "离职流程走一下", "离职处理"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["办理离职", "员工离职", "离职手续"],
            "trigger_keywords": ["离职", "办理离职", "离职手续"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始员工离职流程"}},
                {
                    "id": "offboard_list",
                    "name": "查询待离职员工",
                    "type": "api_call",
                    "description": "查询待办理离职的员工列表",
                    "config": {"api_id": "api_admin_offboard_list", "api_endpoint": "/api/hrm/admin/offboard", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "employees", "type": "array", "description": "待离职员工列表"}],
                    "ai_instructions": {"user_message": "正在查询待离职的员工", "action": "查询待离职员工"}
                },
                {
                    "id": "offboard_detail",
                    "name": "查看离职详情",
                    "type": "api_call",
                    "description": "查看员工离职详细信息",
                    "config": {"api_id": "api_admin_offboard_detail", "api_endpoint": "/api/hrm/admin/offboard/{emp_id}", "method": "GET", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "employee", "type": "object", "description": "员工信息"}, {"name": "leave_date", "type": "date", "description": "离职日期"}, {"name": "handover_status", "type": "string", "description": "交接状态"}],
                    "ai_instructions": {"user_message": "请选择要办理离职的员工", "action": "查看离职详情"}
                },
                {
                    "id": "handover_check",
                    "name": "检查工作交接",
                    "type": "api_call",
                    "description": "检查员工工作交接情况",
                    "config": {"api_id": "api_admin_handover_check", "api_endpoint": "/api/hrm/admin/handover/check", "method": "POST", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "handover_complete", "type": "boolean", "description": "交接是否完成"}, {"name": "pending_items", "type": "array", "description": "待交接事项"}],
                    "ai_instructions": {"user_message": "正在检查工作交接情况", "action": "检查工作交接"}
                },
                {
                    "id": "asset_return",
                    "name": "资产归还",
                    "type": "api_call",
                    "description": "办理办公资产归还",
                    "config": {"api_id": "api_admin_asset_return", "api_endpoint": "/api/hrm/admin/assets/return", "method": "POST", "parameters": {"emp_id": "${emp_id}", "assets": "${assets}"}},
                    "outputs": [{"name": "return_id", "type": "string", "description": "归还单号"}, {"name": "returned_assets", "type": "array", "description": "已归还资产"}],
                    "ai_instructions": {"user_message": "请确认归还的办公资产", "action": "资产归还"}
                },
                {
                    "id": "salary_settle",
                    "name": "工资结算",
                    "type": "api_call",
                    "description": "办理工资结算",
                    "config": {"api_id": "api_admin_salary_settle", "api_endpoint": "/api/hrm/admin/salary/settle", "method": "POST", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "settlement_amount", "type": "float", "description": "结算金额"}, {"name": "settlement_id", "type": "string", "description": "结算单号"}],
                    "ai_instructions": {"user_message": "正在办理工资结算", "action": "工资结算"}
                },
                {
                    "id": "offboard_complete",
                    "name": "完成离职",
                    "type": "api_call",
                    "description": "完成离职流程",
                    "config": {"api_id": "api_admin_offboard_complete", "api_endpoint": "/api/hrm/admin/offboard/complete", "method": "POST", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "正在完成离职流程", "action": "完成离职"}
                },
                {
                    "id": "offboard_notification",
                    "name": "离职完成通知",
                    "type": "notification",
                    "description": "发送离职完成通知",
                    "config": {"message_template": "员工离职完成！工资结算金额：${settlement_amount}元，资产已归还，权限已回收。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "离职办理完成", "action": "发送离职通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "员工离职完成"}}
            ],
            "edges": [
                {"source": "start", "target": "offboard_list"},
                {"source": "offboard_list", "target": "offboard_detail"},
                {"source": "offboard_detail", "target": "handover_check"},
                {"source": "handover_check", "target": "asset_return"},
                {"source": "asset_return", "target": "salary_settle"},
                {"source": "salary_settle", "target": "offboard_complete"},
                {"source": "offboard_complete", "target": "offboard_notification"},
                {"source": "offboard_notification", "target": "end"}
            ]
        },
        # ========== 管理员：调薪流程（6步：查询员工 → 查看薪资历史 → 填写调薪 → 提交审批 → 审批 → 通知） ==========
        {
            "id": "workflow_admin_salary_adjust",
            "name": "调薪流程",
            "description": "管理员调薪完整流程，包括员工查询、薪资历史查看、调薪申请和审批",
            "instruction_variants": ["调薪流程", "薪资调整流程", "发起调薪", "帮我调薪", "调薪怎么走", "调薪审批流程", "调薪申请流程", "薪资调整"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["调薪", "涨工资", "薪资调整"],
            "trigger_keywords": ["调薪", "涨工资", "薪资调整"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始调薪流程"}},
                {
                    "id": "employee_list",
                    "name": "查询待调薪员工",
                    "type": "api_call",
                    "description": "查询待调薪的员工列表",
                    "config": {"api_id": "api_admin_salary_list", "api_endpoint": "/api/hrm/admin/salary/adjust/list", "method": "GET", "parameters": {"department": "${department}"}},
                    "outputs": [{"name": "employees", "type": "array", "description": "员工列表"}],
                    "ai_instructions": {"user_message": "请选择部门查询员工", "action": "查询待调薪员工"}
                },
                {
                    "id": "salary_history",
                    "name": "查看薪资历史",
                    "type": "api_call",
                    "description": "查看员工薪资历史记录",
                    "config": {"api_id": "api_admin_salary_history", "api_endpoint": "/api/hrm/admin/salary/history/{emp_id}", "method": "GET", "parameters": {"emp_id": "${emp_id}"}},
                    "outputs": [{"name": "history", "type": "array", "description": "薪资历史"}, {"name": "current_salary", "type": "float", "description": "当前薪资"}],
                    "ai_instructions": {"user_message": "请选择要调薪的员工", "action": "查看薪资历史"}
                },
                {
                    "id": "salary_adjust",
                    "name": "填写调薪申请",
                    "type": "api_call",
                    "description": "填写调薪信息并提交",
                    "config": {"api_id": "api_admin_salary_adjust", "api_endpoint": "/api/hrm/admin/salary/adjust", "method": "POST", "parameters": {"emp_id": "${emp_id}", "new_salary": "${new_salary}", "effective_date": "${effective_date}", "reason": "${reason}"}},
                    "outputs": [{"name": "adjust_id", "type": "string", "description": "调薪单号"}],
                    "ai_instructions": {"user_message": "请填写新薪资、生效日期和调薪原因", "action": "填写调薪申请"}
                },
                {
                    "id": "salary_approve",
                    "name": "调薪审批",
                    "type": "api_call",
                    "description": "对调薪申请进行审批",
                    "config": {"api_id": "api_admin_salary_approve", "api_endpoint": "/api/hrm/admin/salary/adjust/{id}/approve", "method": "POST", "parameters": {"adjust_id": "${adjust_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请审批调薪申请", "action": "调薪审批"}
                },
                {
                    "id": "adjust_notification",
                    "name": "调薪通知",
                    "type": "notification",
                    "description": "发送调薪结果通知",
                    "config": {"message_template": "调薪完成！调薪单号：${adjust_id}，新薪资将于${effective_date}生效。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "调薪完成", "action": "发送调薪通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "调薪流程完成"}}
            ],
            "edges": [
                {"source": "start", "target": "employee_list"},
                {"source": "employee_list", "target": "salary_history"},
                {"source": "salary_history", "target": "salary_adjust"},
                {"source": "salary_adjust", "target": "salary_approve"},
                {"source": "salary_approve", "target": "adjust_notification"},
                {"source": "adjust_notification", "target": "end"}
            ]
        },
        # ========== 管理员：调岗流程（6步：查询员工 → 选择员工 → 填写调岗 → 提交审批 → 审批 → 通知） ==========
        {
            "id": "workflow_admin_transfer",
            "name": "调岗流程",
            "description": "管理员调岗完整流程，包括员工查询、调岗申请和审批",
            "instruction_variants": ["调岗流程", "岗位调整流程", "发起调岗", "帮我调岗", "调岗怎么走", "调岗审批流程", "调岗申请流程", "部门调动流程"],
            "business_scenario": "hrm",
            "status": "active",
            "user_intents": ["调岗", "换部门", "岗位调整"],
            "trigger_keywords": ["调岗", "换部门", "岗位调整"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始调岗流程"}},
                {
                    "id": "employee_list",
                    "name": "查询待调岗员工",
                    "type": "api_call",
                    "description": "查询待调岗的员工列表",
                    "config": {"api_id": "api_admin_transfer_list", "api_endpoint": "/api/hrm/admin/transfer/list", "method": "GET", "parameters": {"department": "${department}"}},
                    "outputs": [{"name": "employees", "type": "array", "description": "员工列表"}],
                    "ai_instructions": {"user_message": "请选择部门查询员工", "action": "查询待调岗员工"}
                },
                {
                    "id": "transfer_apply",
                    "name": "填写调岗申请",
                    "type": "api_call",
                    "description": "填写调岗信息并提交",
                    "config": {"api_id": "api_admin_transfer_apply", "api_endpoint": "/api/hrm/admin/transfer", "method": "POST", "parameters": {"emp_id": "${emp_id}", "new_department": "${new_department}", "new_position": "${new_position}", "effective_date": "${effective_date}", "reason": "${reason}"}},
                    "outputs": [{"name": "transfer_id", "type": "string", "description": "调岗单号"}],
                    "ai_instructions": {"user_message": "请填写新部门、新职位、生效日期和调岗原因", "action": "填写调岗申请"}
                },
                {
                    "id": "transfer_approve",
                    "name": "调岗审批",
                    "type": "api_call",
                    "description": "对调岗申请进行审批",
                    "config": {"api_id": "api_admin_transfer_approve", "api_endpoint": "/api/hrm/admin/transfer/{id}/approve", "method": "POST", "parameters": {"transfer_id": "${transfer_id}", "action": "${action}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请审批调岗申请", "action": "调岗审批"}
                },
                {
                    "id": "transfer_notification",
                    "name": "调岗通知",
                    "type": "notification",
                    "description": "发送调岗结果通知",
                    "config": {"message_template": "调岗完成！调岗单号：${transfer_id}，新岗位将于${effective_date}生效。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "调岗完成", "action": "发送调岗通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "调岗流程完成"}}
            ],
            "edges": [
                {"source": "start", "target": "employee_list"},
                {"source": "employee_list", "target": "transfer_apply"},
                {"source": "transfer_apply", "target": "transfer_approve"},
                {"source": "transfer_approve", "target": "transfer_notification"},
                {"source": "transfer_notification", "target": "end"}
            ]
        }
    ]
}
