# common_options.py - 通用选项 API 定义
# 这些 API 用于获取下拉选项，所有场景共用

COMMON_OPTIONS_APIS = [
    # 支付方式
    {"id": "api_options_payment_methods", "path": "/api/options/payment-methods", "method": "GET", 
     "desc": "获取支付方式列表", "is_options_api": True, "options_for": "payment_method",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "支付方式列表"}]},
    
    # 证件类型
    {"id": "api_options_id_types", "path": "/api/options/id-types", "method": "GET",
     "desc": "获取证件类型列表", "is_options_api": True, "options_for": "id_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "证件类型列表"}]},
    
    # 乘客类型
    {"id": "api_options_passenger_types", "path": "/api/options/passenger-types", "method": "GET",
     "desc": "获取乘客类型列表", "is_options_api": True, "options_for": "passenger_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "乘客类型列表"}]},
    
    # 席别类型
    {"id": "api_options_seat_types", "path": "/api/options/seat-types", "method": "GET",
     "desc": "获取席别类型列表", "is_options_api": True, "options_for": "seat_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "席别类型列表"}]},
    
    # 请假类型
    {"id": "api_options_leave_types", "path": "/api/options/leave-types", "method": "GET",
     "desc": "获取请假类型列表", "is_options_api": True, "options_for": "leave_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "请假类型列表"}]},
    
    # 费用类型
    {"id": "api_options_expense_types", "path": "/api/options/expense-types", "method": "GET",
     "desc": "获取费用类型列表", "is_options_api": True, "options_for": "expense_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "费用类型列表"}]},
    
    # 证明类型
    {"id": "api_options_cert_types", "path": "/api/options/cert-types", "method": "GET",
     "desc": "获取证明类型列表", "is_options_api": True, "options_for": "cert_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "证明类型列表"}]},
    
    # 房型
    {"id": "api_options_room_types", "path": "/api/options/room-types", "method": "GET",
     "desc": "获取房型列表", "is_options_api": True, "options_for": "room_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "房型列表"}]},
    
    # 房屋类型
    {"id": "api_options_house_types", "path": "/api/options/house-types", "method": "GET",
     "desc": "获取房屋类型列表", "is_options_api": True, "options_for": "house_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "房屋类型列表"}]},
    
    # 投诉类型
    {"id": "api_options_complaint_types", "path": "/api/options/complaint-types", "method": "GET",
     "desc": "获取投诉类型列表", "is_options_api": True, "options_for": "complaint_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "投诉类型列表"}]},
    
    # 服务类型
    {"id": "api_options_service_types", "path": "/api/options/service-types", "method": "GET",
     "desc": "获取服务类型列表", "is_options_api": True, "options_for": "service_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "服务类型列表"}]},
    
    # 订单状态
    {"id": "api_options_order_statuses", "path": "/api/options/order-statuses", "method": "GET",
     "desc": "获取订单状态列表", "is_options_api": True, "options_for": "order_status",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "订单状态列表"}]},
    
    # 发票类型
    {"id": "api_options_invoice_types", "path": "/api/options/invoice-types", "method": "GET",
     "desc": "获取发票类型列表", "is_options_api": True, "options_for": "invoice_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "发票类型列表"}]},
    
    # 报销类型
    {"id": "api_options_reimbursement_types", "path": "/api/options/reimbursement-types", "method": "GET",
     "desc": "获取报销类型列表", "is_options_api": True, "options_for": "reimbursement_type",
     "request": [],
     "response": [{"name": "options", "type": "array", "desc": "报销类型列表"}]},
]

# 字段名到选项 API 的映射
FIELD_TO_OPTIONS_API = {api["options_for"]: api for api in COMMON_OPTIONS_APIS}
