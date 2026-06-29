# education.py - 教育场景定义 V4
# 大幅扩展：增加管理员工作流、更多业务API、更长的流程步骤

EDUCATION_SCENE = {
    "domain": "education",
    "apis": [
        # ========== 用户端 API ==========
        {"id": "api_student_info", "path": "/api/edu/student/info", "method": "GET", "desc": "查询学生信息",
         "instruction_variants": ["查询学生信息", "学生信息", "我的信息", "学生资料", "喂，我的信息呢", "帮我查查学生信息", "学生信息怎么查", "查一下学生"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}],
         "response": [{"name": "name", "type": "string", "desc": "姓名"}, {"name": "class_name", "type": "string", "desc": "班级"}, {"name": "major", "type": "string", "desc": "专业"}]},
        {"id": "api_course_list", "path": "/api/edu/courses", "method": "GET", "desc": "查询课程列表",
         "instruction_variants": ["查询课程列表", "课程列表", "有什么课", "课程", "喂，有哪些课", "帮我看看课程", "课程怎么查", "查一下课"],
         "request": [{"name": "category", "type": "string", "label": "分类", "required": False}, {"name": "semester", "type": "string", "label": "学期", "required": False}],
         "response": [{"name": "courses", "type": "array", "desc": "课程列表"}]},
        {"id": "api_course_detail", "path": "/api/edu/courses/{course_id}", "method": "GET", "desc": "查询课程详情",
         "instruction_variants": ["查询课程详情", "课程详情", "课程信息", "这课怎么样", "喂，这课好吗", "帮我看看课程详情", "课程介绍", "查一下课程"],
         "request": [{"name": "course_id", "type": "string", "label": "课程ID", "required": True}],
         "response": [{"name": "course", "type": "object", "desc": "课程详情"}, {"name": "teacher", "type": "string", "desc": "授课教师"}, {"name": "capacity", "type": "integer", "desc": "容量"}, {"name": "enrolled", "type": "integer", "desc": "已报名"}]},
        {"id": "api_course_enroll", "workflow_only": True, "path": "/api/edu/enrollments", "method": "POST", "desc": "报名课程",
         "instruction_variants": ["报名课程", "选课", "报名", "我要选课", "喂，我要报名", "帮我报名", "报名怎么弄", "选课报名"],
         "request": [{"name": "course_id", "type": "string", "label": "课程ID", "required": True}, {"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "student_name", "type": "string", "label": "学生姓名", "required": True}, {"name": "student_phone", "type": "string", "label": "手机号", "required": True}],
         "response": [{"name": "enrollment_id", "type": "string", "desc": "报名单号"}, {"name": "class_time", "type": "string", "desc": "上课时间"}]},
        {"id": "api_enrollment_pay", "workflow_only": True, "path": "/api/edu/enrollments/{enrollment_id}/pay", "method": "POST", "desc": "缴纳学费",
         "instruction_variants": ["缴纳学费", "交学费", "付学费", "缴费", "喂，怎么交学费", "帮我缴费", "学费怎么交", "付款"],
         "request": [{"name": "enrollment_id", "type": "string", "label": "报名单号", "required": True}, {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}],
         "response": [{"name": "payment_success", "type": "boolean", "desc": "支付是否成功"}, {"name": "receipt_no", "type": "string", "desc": "收据号"}]},
        {"id": "api_grade_query", "path": "/api/edu/grades", "method": "GET", "desc": "查询成绩",
         "instruction_variants": ["查询成绩", "成绩", "我的成绩", "考了多少分", "喂，成绩出来了吗", "帮我查查成绩", "成绩怎么查", "查一下分数"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "semester", "type": "string", "label": "学期", "required": False}],
         "response": [{"name": "grades", "type": "array", "desc": "成绩列表"}, {"name": "gpa", "type": "float", "desc": "平均绩点"}]},
        {"id": "api_schedule_query", "path": "/api/edu/schedules", "method": "GET", "desc": "查询课表",
         "instruction_variants": ["查询课表", "课表", "我的课表", "上课时间", "喂，课表在哪", "帮我查查课表", "课表怎么查", "查一下课表"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "week", "type": "integer", "label": "周次", "required": False}],
         "response": [{"name": "schedules", "type": "array", "desc": "课表"}]},
        {"id": "api_exam_list", "path": "/api/edu/exams", "method": "GET", "desc": "查询考试列表",
         "instruction_variants": ["查询考试列表", "考试列表", "有什么考试", "考试安排", "喂，有哪些考试", "帮我看看考试", "考试怎么查", "查一下考试"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}],
         "response": [{"name": "exams", "type": "array", "desc": "考试列表"}]},
        {"id": "api_exam_register", "workflow_only": True, "path": "/api/edu/exams/register", "method": "POST", "desc": "考试报名",
         "instruction_variants": ["考试报名", "报名考试", "参加考试", "考试", "喂，我要报名考试", "帮我报名", "考试怎么报名", "报名一下"],
         "request": [{"name": "exam_id", "type": "string", "label": "考试ID", "required": True}, {"name": "student_id", "type": "string", "label": "学生ID", "required": True}],
         "response": [{"name": "registration_id", "type": "string", "desc": "报名单号"}, {"name": "exam_time", "type": "string", "desc": "考试时间"}, {"name": "exam_room", "type": "string", "desc": "考场"}]},
        {"id": "api_homework_list", "path": "/api/edu/homework", "method": "GET", "desc": "查询作业列表",
         "instruction_variants": ["查询作业列表", "作业列表", "有什么作业", "作业", "喂，有哪些作业", "帮我看看作业", "作业怎么查", "查一下作业"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "course_id", "type": "string", "label": "课程ID", "required": False}],
         "response": [{"name": "homework", "type": "array", "desc": "作业列表"}]},
        {"id": "api_homework_submit", "workflow_only": True, "path": "/api/edu/homework/submit", "method": "POST", "desc": "提交作业",
         "instruction_variants": ["提交作业", "交作业", "作业提交", "上交作业", "喂，我要交作业", "帮我提交作业", "作业怎么交", "提交一下"],
         "request": [{"name": "homework_id", "type": "string", "label": "作业ID", "required": True}, {"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "content", "type": "string", "label": "作业内容", "required": True}, {"name": "attachments", "type": "string", "label": "附件", "required": False}],
         "response": [{"name": "submission_id", "type": "string", "desc": "提交ID"}, {"name": "submit_time", "type": "datetime", "desc": "提交时间"}]},
        {"id": "api_leave_apply", "workflow_only": True, "path": "/api/edu/leaves", "method": "POST", "desc": "请假申请",
         "instruction_variants": ["请假申请", "请假", "申请请假", "我要请假", "喂，我要请假", "帮我请假", "请假怎么办", "申请一下"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "leave_type", "type": "string", "label": "请假类型", "required": True}, {"name": "start_date", "type": "date", "label": "开始日期", "required": True}, {"name": "end_date", "type": "date", "label": "结束日期", "required": True}, {"name": "reason", "type": "string", "label": "请假原因", "required": True}],
         "response": [{"name": "leave_id", "type": "string", "desc": "请假单号"}]},
        {"id": "api_certificate_apply", "workflow_only": True, "path": "/api/edu/certificates", "method": "POST", "desc": "证明申请",
         "instruction_variants": ["证明申请", "申请证明", "开证明", "证明", "喂，我要开证明", "帮我申请证明", "证明怎么开", "申请一下"],
         "request": [{"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "cert_type", "type": "string", "label": "证明类型", "required": True}, {"name": "purpose", "type": "string", "label": "用途", "required": True}],
         "response": [{"name": "cert_id", "type": "string", "desc": "证明单号"}, {"name": "estimated_days", "type": "integer", "desc": "预计天数"}]},

        # ========== 管理员 API ==========
        {"id": "api_admin_enrollment_list", "workflow_only": True, "path": "/api/edu/admin/enrollments", "method": "GET", "desc": "查询报名列表（管理员）",
         "instruction_variants": ["查询报名列表", "报名列表", "报名管理", "学生报名", "喂，有哪些报名", "帮我看看报名", "报名怎么样", "查一下报名"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}, {"name": "course_id", "type": "string", "label": "课程ID", "required": False}],
         "response": [{"name": "enrollments", "type": "array", "desc": "报名列表"}, {"name": "pending_count", "type": "integer", "desc": "待审核数"}]},
        {"id": "api_admin_enrollment_approve", "workflow_only": True, "path": "/api/edu/admin/enrollments/{enrollment_id}/approve", "method": "POST", "desc": "审核报名",
         "instruction_variants": ["审核报名", "报名审核", "审批报名", "批准报名", "喂，我要审核", "帮我审批报名", "审核怎么弄", "批准一下"],
         "request": [{"name": "enrollment_id", "type": "string", "label": "报名单号", "required": True}, {"name": "result", "type": "string", "label": "审核结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_homework_list", "workflow_only": True, "path": "/api/edu/admin/homework", "method": "GET", "desc": "查询作业提交列表（管理员）",
         "instruction_variants": ["查询作业提交列表", "作业列表", "作业管理", "学生作业", "喂，有哪些作业", "帮我看看作业", "作业怎么样", "查一下作业"],
         "request": [{"name": "course_id", "type": "string", "label": "课程ID", "required": False}, {"name": "homework_id", "type": "string", "label": "作业ID", "required": False}],
         "response": [{"name": "submissions", "type": "array", "desc": "提交列表"}, {"name": "pending_count", "type": "integer", "desc": "待批改数"}]},
        {"id": "api_admin_homework_grade", "workflow_only": True, "path": "/api/edu/admin/homework/{submission_id}/grade", "method": "POST", "desc": "批改作业",
         "instruction_variants": ["批改作业", "改作业", "作业批改", "打分", "喂，我要批改", "帮我改作业", "批改怎么弄", "给个分数"],
         "request": [{"name": "submission_id", "type": "string", "label": "提交ID", "required": True}, {"name": "score", "type": "integer", "label": "分数", "required": True}, {"name": "comment", "type": "string", "label": "评语", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_exam_list", "workflow_only": True, "path": "/api/edu/admin/exams", "method": "GET", "desc": "查询考试列表（管理员）",
         "instruction_variants": ["查询考试列表", "考试列表", "考试管理", "考试安排", "喂，有哪些考试", "帮我看看考试", "考试怎么样", "查一下考试"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "exams", "type": "array", "desc": "考试列表"}]},
        {"id": "api_admin_exam_score_input", "workflow_only": True, "path": "/api/edu/admin/exams/{exam_id}/scores", "method": "POST", "desc": "录入成绩",
         "instruction_variants": ["录入成绩", "成绩录入", "输入成绩", "登记成绩", "喂，我要录入成绩", "帮我录成绩", "录入怎么弄", "输入分数"],
         "request": [{"name": "exam_id", "type": "string", "label": "考试ID", "required": True}, {"name": "student_id", "type": "string", "label": "学生ID", "required": True}, {"name": "score", "type": "integer", "label": "分数", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_exam_score_publish", "workflow_only": True, "path": "/api/edu/admin/exams/{exam_id}/publish", "method": "POST", "desc": "发布成绩",
         "instruction_variants": ["发布成绩", "成绩发布", "公布成绩", "发成绩", "喂，我要发布成绩", "帮我发布", "发布怎么弄", "公布一下"],
         "request": [{"name": "exam_id", "type": "string", "label": "考试ID", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}, {"name": "published_count", "type": "integer", "desc": "发布人数"}]},
        {"id": "api_admin_leave_list", "workflow_only": True, "path": "/api/edu/admin/leaves", "method": "GET", "desc": "查询请假列表（管理员）",
         "instruction_variants": ["查询请假列表", "请假列表", "请假管理", "学生请假", "喂，有哪些请假", "帮我看看请假", "请假怎么样", "查一下请假"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "leaves", "type": "array", "desc": "请假列表"}, {"name": "pending_count", "type": "integer", "desc": "待审批数"}]},
        {"id": "api_admin_leave_approve", "workflow_only": True, "path": "/api/edu/admin/leaves/{leave_id}/approve", "method": "POST", "desc": "审批请假",
         "instruction_variants": ["审批请假", "请假审批", "批准请假", "审核请假", "喂，我要审批", "帮我批准请假", "审批怎么弄", "批准一下"],
         "request": [{"name": "leave_id", "type": "string", "label": "请假单号", "required": True}, {"name": "result", "type": "string", "label": "审批结果", "required": True}, {"name": "remark", "type": "string", "label": "备注", "required": False}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},
        {"id": "api_admin_cert_list", "workflow_only": True, "path": "/api/edu/admin/certificates", "method": "GET", "desc": "查询证明申请列表（管理员）",
         "instruction_variants": ["查询证明申请列表", "证明列表", "证明管理", "学生证明", "喂，有哪些证明", "帮我看看证明", "证明怎么样", "查一下证明"],
         "request": [{"name": "status", "type": "string", "label": "状态", "required": False}],
         "response": [{"name": "certificates", "type": "array", "desc": "证明列表"}, {"name": "pending_count", "type": "integer", "desc": "待处理数"}]},
        {"id": "api_admin_cert_issue", "workflow_only": True, "path": "/api/edu/admin/certificates/{cert_id}/issue", "method": "POST", "desc": "开具证明",
         "instruction_variants": ["开具证明", "开证明", "证明开具", "出证明", "喂，我要开证明", "帮我开具", "开具怎么弄", "出一张证明"],
         "request": [{"name": "cert_id", "type": "string", "label": "证明单号", "required": True}, {"name": "cert_no", "type": "string", "label": "证明编号", "required": True}],
         "response": [{"name": "success", "type": "boolean", "desc": "是否成功"}]},

        # ========== 管理员统计 API ==========
        {"id": "api_admin_enrollment_stats", "path": "/api/edu/admin/stats/enrollment", "method": "GET", "desc": "查询报名统计", "name": "报名统计", "response_type": "chart", "chart_type": "mixed",
         "instruction_variants": ["查询报名统计", "报名统计", "报名数据", "选课统计", "喂，报名情况怎么样", "帮我看看报名统计", "报名趋势", "查一下报名"],
         "request": [],
         "response": [{"name": "total_enrollments", "type": "integer", "desc": "总报名数"}, {"name": "monthly_trend", "type": "array", "desc": "月度趋势"}]},
        {"id": "api_admin_grade_analysis", "path": "/api/edu/admin/stats/grade", "method": "GET", "desc": "查询成绩分析", "name": "成绩分析", "response_type": "chart", "chart_type": "bar",
         "instruction_variants": ["查询成绩分析", "成绩分析", "成绩统计", "分数分布", "喂，成绩怎么样", "帮我看看成绩分析", "成绩分析图", "查一下成绩"],
         "request": [],
         "response": [{"name": "ranges", "type": "array", "desc": "分数段"}, {"name": "counts", "type": "array", "desc": "人数"}]},
        {"id": "api_admin_attendance_stats", "path": "/api/edu/admin/stats/attendance", "method": "GET", "desc": "查询出勤统计", "name": "出勤统计", "response_type": "chart", "chart_type": "pie",
         "instruction_variants": ["查询出勤统计", "出勤统计", "出勤率", "考勤数据", "喂，出勤怎么样", "帮我看看出勤", "出勤情况", "查一下考勤"],
         "request": [],
         "response": [{"name": "attendance_rate", "type": "float", "desc": "出勤率"}, {"name": "leave_rate", "type": "float", "desc": "请假率"}]},
    ],

    "workflows": [
        # ========== 用户：完整选课报名流程（7步：查询学生信息 → 查询课程列表 → 查看课程详情 → 报名课程 → 缴费 → 查询课表 → 通知） ==========
        {
            "id": "workflow_full_enroll",
            "name": "完整选课报名流程",
            "description": "完整的选课报名流程，包括查询、报名、缴费",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["完整选课报名流程", "选课", "报名课程", "选课报名", "喂，我要选课", "帮我报名", "选课怎么办", "报名"],
            "user_intents": ["选课", "报名课程", "选课报名", "报名"],
            "trigger_keywords": ["选课", "报名课程", "选课报名"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始选课报名"}},
                {
                    "id": "n_student_info",
                    "name": "查询学生信息",
                    "type": "api_call",
                    "description": "查询学生基本信息",
                    "config": {"api_id": "api_student_info", "api_endpoint": "/api/edu/student/info", "method": "GET", "parameters": {"student_id": "${student_id}"}},
                    "outputs": [{"name": "name", "type": "string", "description": "姓名"}, {"name": "class_name", "type": "string", "description": "班级"}],
                    "ai_instructions": {"user_message": "请输入学生ID", "action": "查询学生信息"}
                },
                {
                    "id": "n_course_list",
                    "name": "查询课程列表",
                    "type": "api_call",
                    "description": "查询可选课程",
                    "config": {"api_id": "api_course_list", "api_endpoint": "/api/edu/courses", "method": "GET", "parameters": {"category": "${category}", "semester": "${semester}"}},
                    "outputs": [{"name": "courses", "type": "array", "description": "课程列表"}],
                    "ai_instructions": {"user_message": "请选择课程分类", "action": "查询课程列表"}
                },
                {
                    "id": "n_course_detail",
                    "name": "查看课程详情",
                    "type": "api_call",
                    "description": "查看课程详细信息",
                    "config": {"api_id": "api_course_detail", "api_endpoint": "/api/edu/courses/{course_id}", "method": "GET", "parameters": {"course_id": "${course_id}"}},
                    "outputs": [{"name": "course", "type": "object", "description": "课程详情"}, {"name": "teacher", "type": "string", "description": "授课教师"}, {"name": "capacity", "type": "integer", "description": "容量"}],
                    "ai_instructions": {"user_message": "请选择要查看的课程", "action": "查看课程详情"}
                },
                {
                    "id": "n_enroll",
                    "name": "报名课程",
                    "type": "api_call",
                    "description": "提交报名申请",
                    "config": {"api_id": "api_course_enroll", "api_endpoint": "/api/edu/enrollments", "method": "POST", "parameters": {"course_id": "${course_id}", "student_id": "${student_id}", "student_name": "${name}", "student_phone": "${phone}"}},
                    "outputs": [{"name": "enrollment_id", "type": "string", "description": "报名单号"}, {"name": "class_time", "type": "string", "description": "上课时间"}],
                    "ai_instructions": {"user_message": "请确认报名并填写联系电话", "action": "报名课程"}
                },
                {
                    "id": "n_pay",
                    "name": "缴纳学费",
                    "type": "api_call",
                    "description": "缴纳课程学费",
                    "config": {"api_id": "api_enrollment_pay", "api_endpoint": "/api/edu/enrollments/{enrollment_id}/pay", "method": "POST", "parameters": {"enrollment_id": "${enrollment_id}", "payment_method": "${payment_method}"}},
                    "outputs": [{"name": "payment_success", "type": "boolean", "description": "支付是否成功"}, {"name": "receipt_no", "type": "string", "description": "收据号"}],
                    "ai_instructions": {"user_message": "请选择支付方式", "action": "缴纳学费"}
                },
                {
                    "id": "n_notify",
                    "name": "报名通知",
                    "type": "notification",
                    "description": "发送报名成功通知",
                    "config": {"message_template": "选课报名成功！报名单号：${enrollment_id}，课程：${course}，上课时间：${class_time}，收据号：${receipt_no}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "报名成功", "action": "发送报名通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "选课报名完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_student_info"},
                {"source": "n_student_info", "target": "n_course_list"},
                {"source": "n_course_list", "target": "n_course_detail"},
                {"source": "n_course_detail", "target": "n_enroll"},
                {"source": "n_enroll", "target": "n_pay"},
                {"source": "n_pay", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：考试报名流程（5步：查询学生信息 → 查询考试列表 → 报名考试 → 查询课表 → 通知） ==========
        {
            "id": "workflow_exam_register",
            "name": "考试报名流程",
            "description": "考试报名流程",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["考试报名流程", "考试报名", "报名考试", "参加考试", "喂，我要报名考试", "帮我报名", "考试怎么报名", "报名一下"],
            "user_intents": ["考试报名", "报名考试", "参加考试"],
            "trigger_keywords": ["考试报名", "报名考试", "参加考试"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始考试报名"}},
                {
                    "id": "n_student_info",
                    "name": "查询学生信息",
                    "type": "api_call",
                    "description": "查询学生基本信息",
                    "config": {"api_id": "api_student_info", "api_endpoint": "/api/edu/student/info", "method": "GET", "parameters": {"student_id": "${student_id}"}},
                    "outputs": [{"name": "name", "type": "string", "description": "姓名"}],
                    "ai_instructions": {"user_message": "请输入学生ID", "action": "查询学生信息"}
                },
                {
                    "id": "n_exam_list",
                    "name": "查询考试列表",
                    "type": "api_call",
                    "description": "查询可报名的考试",
                    "config": {"api_id": "api_exam_list", "api_endpoint": "/api/edu/exams", "method": "GET", "parameters": {"student_id": "${student_id}"}},
                    "outputs": [{"name": "exams", "type": "array", "description": "考试列表"}],
                    "ai_instructions": {"user_message": "查询可报名考试", "action": "查询考试列表"}
                },
                {
                    "id": "n_register",
                    "name": "报名考试",
                    "type": "api_call",
                    "description": "提交考试报名",
                    "config": {"api_id": "api_exam_register", "api_endpoint": "/api/edu/exams/register", "method": "POST", "parameters": {"exam_id": "${exam_id}", "student_id": "${student_id}"}},
                    "outputs": [{"name": "registration_id", "type": "string", "description": "报名单号"}, {"name": "exam_time", "type": "string", "description": "考试时间"}, {"name": "exam_room", "type": "string", "description": "考场"}],
                    "ai_instructions": {"user_message": "请选择要报名的考试", "action": "报名考试"}
                },
                {
                    "id": "n_notify",
                    "name": "报名通知",
                    "type": "notification",
                    "description": "发送报名成功通知",
                    "config": {"message_template": "考试报名成功！报名单号：${registration_id}，考试时间：${exam_time}，考场：${exam_room}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "报名成功", "action": "发送报名通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "考试报名完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_student_info"},
                {"source": "n_student_info", "target": "n_exam_list"},
                {"source": "n_exam_list", "target": "n_register"},
                {"source": "n_register", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：作业提交流程（5步：查询学生信息 → 查询作业列表 → 填写作业 → 提交作业 → 通知） ==========
        {
            "id": "workflow_homework_submit",
            "name": "作业提交流程",
            "description": "提交课程作业",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["作业提交流程", "交作业", "提交作业", "作业提交", "喂，我要交作业", "帮我提交作业", "作业怎么交", "上交作业"],
            "user_intents": ["交作业", "提交作业", "作业提交"],
            "trigger_keywords": ["交作业", "提交作业", "作业提交"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始提交作业"}},
                {
                    "id": "n_homework_list",
                    "name": "查询作业列表",
                    "type": "api_call",
                    "description": "查询待提交的作业",
                    "config": {"api_id": "api_homework_list", "api_endpoint": "/api/edu/homework", "method": "GET", "parameters": {"student_id": "${student_id}", "course_id": "${course_id}"}},
                    "outputs": [{"name": "homework", "type": "array", "description": "作业列表"}],
                    "ai_instructions": {"user_message": "请输入学生ID查询作业", "action": "查询作业列表"}
                },
                {
                    "id": "n_submit",
                    "name": "提交作业",
                    "type": "api_call",
                    "description": "提交作业内容",
                    "config": {"api_id": "api_homework_submit", "api_endpoint": "/api/edu/homework/submit", "method": "POST", "parameters": {"homework_id": "${homework_id}", "student_id": "${student_id}", "content": "${content}", "attachments": "${attachments}"}},
                    "outputs": [{"name": "submission_id", "type": "string", "description": "提交ID"}, {"name": "submit_time", "type": "datetime", "description": "提交时间"}],
                    "ai_instructions": {"user_message": "请选择作业并填写内容", "action": "提交作业"}
                },
                {
                    "id": "n_notify",
                    "name": "提交通知",
                    "type": "notification",
                    "description": "发送提交成功通知",
                    "config": {"message_template": "作业提交成功！提交ID：${submission_id}，提交时间：${submit_time}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "提交成功", "action": "发送提交通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "作业提交完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_homework_list"},
                {"source": "n_homework_list", "target": "n_submit"},
                {"source": "n_submit", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 用户：请假申请流程（4步：查询学生信息 → 查询课表 → 提交请假 → 通知） ==========
        {
            "id": "workflow_leave_apply",
            "name": "请假申请流程",
            "description": "学生请假申请",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["请假申请流程", "请假", "请假申请", "申请请假", "喂，我要请假", "帮我请假", "请假怎么办", "我要请假"],
            "user_intents": ["请假", "请假申请", "申请请假"],
            "trigger_keywords": ["请假", "请假申请", "申请请假"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始请假申请"}},
                {
                    "id": "n_schedule",
                    "name": "查询课表",
                    "type": "api_call",
                    "description": "查询请假期间的课程安排",
                    "config": {"api_id": "api_schedule_query", "api_endpoint": "/api/edu/schedules", "method": "GET", "parameters": {"student_id": "${student_id}"}},
                    "outputs": [{"name": "schedules", "type": "array", "description": "课表"}],
                    "ai_instructions": {"user_message": "请输入学生ID查询课表", "action": "查询课表"}
                },
                {
                    "id": "n_apply",
                    "name": "提交请假",
                    "type": "api_call",
                    "description": "提交请假申请",
                    "config": {"api_id": "api_leave_apply", "api_endpoint": "/api/edu/leaves", "method": "POST", "parameters": {"student_id": "${student_id}", "leave_type": "${leave_type}", "start_date": "${start_date}", "end_date": "${end_date}", "reason": "${reason}"}},
                    "outputs": [{"name": "leave_id", "type": "string", "description": "请假单号"}],
                    "ai_instructions": {"user_message": "请填写请假信息", "action": "提交请假"}
                },
                {
                    "id": "n_notify",
                    "name": "请假通知",
                    "type": "notification",
                    "description": "发送请假申请通知",
                    "config": {"message_template": "请假申请已提交！请假单号：${leave_id}，请等待审批。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "申请已提交", "action": "发送请假通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "请假申请完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_schedule"},
                {"source": "n_schedule", "target": "n_apply"},
                {"source": "n_apply", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：报名审核流程（5步：查询待审报名 → 查看详情 → 审核报名 → 更新状态 → 通知） ==========
        {
            "id": "workflow_admin_enrollment_approve",
            "name": "管理员报名审核流程",
            "description": "审核学生的课程报名申请",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["管理员报名审核流程", "审核报名", "报名审核", "处理报名", "喂，我要审核", "帮我审批报名", "审核怎么办", "批准报名"],
            "user_intents": ["审核报名", "报名审核", "处理报名"],
            "trigger_keywords": ["审核报名", "报名审核", "处理报名"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审核报名"}},
                {
                    "id": "n_list",
                    "name": "查询待审报名",
                    "type": "api_call",
                    "description": "查询待审核的报名列表",
                    "config": {"api_id": "api_admin_enrollment_list", "api_endpoint": "/api/edu/admin/enrollments", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "enrollments", "type": "array", "description": "报名列表"}, {"name": "pending_count", "type": "integer", "description": "待审核数"}],
                    "ai_instructions": {"user_message": "查询待审核报名", "action": "查询待审报名"}
                },
                {
                    "id": "n_approve",
                    "name": "审核报名",
                    "type": "api_call",
                    "description": "审核报名申请",
                    "config": {"api_id": "api_admin_enrollment_approve", "api_endpoint": "/api/edu/admin/enrollments/{enrollment_id}/approve", "method": "POST", "parameters": {"enrollment_id": "${enrollment_id}", "result": "${result}", "remark": "${remark}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择报名并填写审核结果", "action": "审核报名"}
                },
                {
                    "id": "n_notify",
                    "name": "审核通知",
                    "type": "notification",
                    "description": "发送审核结果通知",
                    "config": {"message_template": "报名审核完成！报名单号${enrollment_id}，审核结果：${result}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审核完成", "action": "发送审核通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "报名审核完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_approve"},
                {"source": "n_approve", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：作业批改流程（5步：查询待批作业 → 查看作业内容 → 批改作业 → 录入成绩 → 通知） ==========
        {
            "id": "workflow_admin_homework_grade",
            "name": "管理员作业批改流程",
            "description": "批改学生提交的作业",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["管理员作业批改流程", "批改作业", "作业批改", "改作业", "喂，我要批改", "帮我改作业", "批改怎么办", "打分"],
            "user_intents": ["批改作业", "作业批改", "改作业"],
            "trigger_keywords": ["批改作业", "作业批改", "改作业"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始批改作业"}},
                {
                    "id": "n_list",
                    "name": "查询待批作业",
                    "type": "api_call",
                    "description": "查询待批改的作业列表",
                    "config": {"api_id": "api_admin_homework_list", "api_endpoint": "/api/edu/admin/homework", "method": "GET", "parameters": {"course_id": "${course_id}"}},
                    "outputs": [{"name": "submissions", "type": "array", "description": "提交列表"}, {"name": "pending_count", "type": "integer", "description": "待批改数"}],
                    "ai_instructions": {"user_message": "查询待批改作业", "action": "查询待批作业"}
                },
                {
                    "id": "n_grade",
                    "name": "批改作业",
                    "type": "api_call",
                    "description": "批改作业并打分",
                    "config": {"api_id": "api_admin_homework_grade", "api_endpoint": "/api/edu/admin/homework/{submission_id}/grade", "method": "POST", "parameters": {"submission_id": "${submission_id}", "score": "${score}", "comment": "${comment}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择作业并填写分数和评语", "action": "批改作业"}
                },
                {
                    "id": "n_notify",
                    "name": "批改通知",
                    "type": "notification",
                    "description": "发送批改完成通知",
                    "config": {"message_template": "作业批改完成！提交ID${submission_id}，分数：${score}分。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "批改完成", "action": "发送批改通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "作业批改完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_grade"},
                {"source": "n_grade", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：成绩录入发布流程（5步：查询考试列表 → 录入成绩 → 审核成绩 → 发布成绩 → 通知） ==========
        {
            "id": "workflow_admin_score_publish",
            "name": "管理员成绩录入发布流程",
            "description": "录入并发布考试成绩",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["管理员成绩录入发布流程", "录入成绩", "发布成绩", "成绩录入", "喂，我要录入成绩", "帮我发布成绩", "录入怎么办", "成绩发布"],
            "user_intents": ["录入成绩", "发布成绩", "成绩录入"],
            "trigger_keywords": ["录入成绩", "发布成绩", "成绩录入"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始成绩录入"}},
                {
                    "id": "n_exam_list",
                    "name": "查询考试列表",
                    "type": "api_call",
                    "description": "查询待录入成绩的考试",
                    "config": {"api_id": "api_admin_exam_list", "api_endpoint": "/api/edu/admin/exams", "method": "GET", "parameters": {"status": "completed"}},
                    "outputs": [{"name": "exams", "type": "array", "description": "考试列表"}],
                    "ai_instructions": {"user_message": "查询待录入成绩的考试", "action": "查询考试列表"}
                },
                {
                    "id": "n_input",
                    "name": "录入成绩",
                    "type": "api_call",
                    "description": "录入学生成绩",
                    "config": {"api_id": "api_admin_exam_score_input", "api_endpoint": "/api/edu/admin/exams/{exam_id}/scores", "method": "POST", "parameters": {"exam_id": "${exam_id}", "student_id": "${student_id}", "score": "${score}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择考试并录入成绩", "action": "录入成绩"}
                },
                {
                    "id": "n_publish",
                    "name": "发布成绩",
                    "type": "api_call",
                    "description": "发布考试成绩",
                    "config": {"api_id": "api_admin_exam_score_publish", "api_endpoint": "/api/edu/admin/exams/{exam_id}/publish", "method": "POST", "parameters": {"exam_id": "${exam_id}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}, {"name": "published_count", "type": "integer", "description": "发布人数"}],
                    "ai_instructions": {"user_message": "确认发布成绩", "action": "发布成绩"}
                },
                {
                    "id": "n_notify",
                    "name": "发布通知",
                    "type": "notification",
                    "description": "发送成绩发布通知",
                    "config": {"message_template": "成绩发布成功！考试${exam_id}，共发布${published_count}人成绩。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "发布成功", "action": "发送发布通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "成绩发布完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_exam_list"},
                {"source": "n_exam_list", "target": "n_input"},
                {"source": "n_input", "target": "n_publish"},
                {"source": "n_publish", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：请假审批流程（4步：查询请假列表 → 查看详情 → 审批请假 → 通知） ==========
        {
            "id": "workflow_admin_leave_approve",
            "name": "管理员请假审批流程",
            "description": "审批学生请假申请",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["管理员请假审批流程", "审批请假", "请假审批", "处理请假", "喂，我要审批", "帮我审核请假", "审批怎么办", "批准请假"],
            "user_intents": ["审批请假", "请假审批", "处理请假"],
            "trigger_keywords": ["审批请假", "请假审批", "处理请假"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始审批请假"}},
                {
                    "id": "n_list",
                    "name": "查询请假列表",
                    "type": "api_call",
                    "description": "查询待审批的请假申请",
                    "config": {"api_id": "api_admin_leave_list", "api_endpoint": "/api/edu/admin/leaves", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "leaves", "type": "array", "description": "请假列表"}, {"name": "pending_count", "type": "integer", "description": "待审批数"}],
                    "ai_instructions": {"user_message": "查询待审批请假", "action": "查询请假列表"}
                },
                {
                    "id": "n_approve",
                    "name": "审批请假",
                    "type": "api_call",
                    "description": "审批请假申请",
                    "config": {"api_id": "api_admin_leave_approve", "api_endpoint": "/api/edu/admin/leaves/{leave_id}/approve", "method": "POST", "parameters": {"leave_id": "${leave_id}", "result": "${result}", "remark": "${remark}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择请假申请并填写审批结果", "action": "审批请假"}
                },
                {
                    "id": "n_notify",
                    "name": "审批通知",
                    "type": "notification",
                    "description": "发送审批结果通知",
                    "config": {"message_template": "请假审批完成！请假单号${leave_id}，审批结果：${result}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "审批完成", "action": "发送审批通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "请假审批完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_approve"},
                {"source": "n_approve", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        },

        # ========== 管理员：证明开具流程（4步：查询证明申请 → 审核申请 → 开具证明 → 通知） ==========
        {
            "id": "workflow_admin_cert_issue",
            "name": "管理员证明开具流程",
            "description": "开具学生证明",
            "business_scenario": "education",
            "status": "active",
            "instruction_variants": ["管理员证明开具流程", "开具证明", "证明开具", "开证明", "喂，我要开证明", "帮我开具", "开具怎么办", "出证明"],
            "user_intents": ["开具证明", "证明开具", "开证明"],
            "trigger_keywords": ["开具证明", "证明开具", "开证明"],
            "nodes": [
                {"id": "start", "name": "开始", "type": "start", "config": {}, "outputs": [], "ai_instructions": {"action": "开始开具证明"}},
                {
                    "id": "n_list",
                    "name": "查询证明申请",
                    "type": "api_call",
                    "description": "查询待处理的证明申请",
                    "config": {"api_id": "api_admin_cert_list", "api_endpoint": "/api/edu/admin/certificates", "method": "GET", "parameters": {"status": "pending"}},
                    "outputs": [{"name": "certificates", "type": "array", "description": "证明列表"}, {"name": "pending_count", "type": "integer", "description": "待处理数"}],
                    "ai_instructions": {"user_message": "查询待处理证明申请", "action": "查询证明申请"}
                },
                {
                    "id": "n_issue",
                    "name": "开具证明",
                    "type": "api_call",
                    "description": "开具证明",
                    "config": {"api_id": "api_admin_cert_issue", "api_endpoint": "/api/edu/admin/certificates/{cert_id}/issue", "method": "POST", "parameters": {"cert_id": "${cert_id}", "cert_no": "${cert_no}"}},
                    "outputs": [{"name": "success", "type": "boolean", "description": "是否成功"}],
                    "ai_instructions": {"user_message": "请选择申请并填写证明编号", "action": "开具证明"}
                },
                {
                    "id": "n_notify",
                    "name": "开具通知",
                    "type": "notification",
                    "description": "发送证明开具通知",
                    "config": {"message_template": "证明开具成功！证明单号${cert_id}，证明编号：${cert_no}。"},
                    "outputs": [],
                    "ai_instructions": {"user_message": "开具成功", "action": "发送开具通知"}
                },
                {"id": "end", "name": "结束", "type": "end", "config": {}, "outputs": [], "ai_instructions": {"action": "证明开具完成"}}
            ],
            "edges": [
                {"source": "start", "target": "n_list"},
                {"source": "n_list", "target": "n_issue"},
                {"source": "n_issue", "target": "n_notify"},
                {"source": "n_notify", "target": "end"}
            ]
        }
    ]
}
