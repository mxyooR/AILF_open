"""
统一响应格式工具类
确保所有API响应格式一致,HTTP状态码与业务码保持一致
"""
from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import time


class ResponseMeta:
    """响应元数据"""
    def __init__(
        self,
        timestamp: Optional[int] = None,
        execution_time: Optional[int] = None,
        request_id: Optional[str] = None
    ):
        self.timestamp = timestamp or int(time.time() * 1000)
        self.execution_time = execution_time
        self.request_id = request_id
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"timestamp": self.timestamp}
        if self.execution_time is not None:
            result["execution_time"] = self.execution_time
        if self.request_id:
            result["request_id"] = self.request_id
        return result


class UnifiedResponse:
    """统一响应格式类"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        status_code: int = 200,
        meta: Optional[ResponseMeta] = None
    ) -> JSONResponse:
        """
        成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            status_code: HTTP状态码(200, 201等)
            meta: 响应元数据
            
        Returns:
            JSONResponse对象
        """
        if meta is None:
            meta = ResponseMeta()
        
        return JSONResponse(
            status_code=status_code,
            content={
                "code": status_code,
                "message": message,
                "data": data,
                "meta": meta.to_dict()
            }
        )
    
    @staticmethod
    def error(
        message: str = "操作失败",
        status_code: int = 400,
        error_type: Optional[str] = None,
        details: Any = None,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> HTTPException:
        """
        错误响应
        
        Args:
            message: 错误消息
            status_code: HTTP状态码(400, 404, 500等)
            error_type: 错误类型标识
            details: 详细错误信息
            suggestion: 建议信息
            error_code: 错误代码
            
        Returns:
            HTTPException对象
        """
        error_data = {}
        if error_type:
            error_data["error"] = error_type
        if details:
            error_data["details"] = details
        if suggestion:
            error_data["suggestion"] = suggestion
        if error_code:
            error_data["error_code"] = error_code
            
        return HTTPException(
            status_code=status_code,
            detail={
                "code": status_code,
                "message": message,
                "data": error_data if error_data else None,
                "meta": ResponseMeta().to_dict()
            }
        )
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "创建成功",
        meta: Optional[ResponseMeta] = None
    ) -> JSONResponse:
        """创建成功响应(201)"""
        return UnifiedResponse.success(data=data, message=message, status_code=201, meta=meta)
    
    @staticmethod
    def bad_request(
        message: str = "请求参数错误",
        error_type: str = "bad_request",
        details: Any = None,
        suggestion: Optional[str] = None
    ) -> HTTPException:
        """错误请求响应(400)"""
        return UnifiedResponse.error(
            message=message,
            status_code=400,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )
    
    @staticmethod
    def unauthorized(
        message: str = "未授权",
        error_type: str = "unauthorized",
        details: Any = None,
        suggestion: Optional[str] = None
    ) -> HTTPException:
        """未授权响应(401)"""
        return UnifiedResponse.error(
            message=message,
            status_code=401,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )
    
    @staticmethod
    def forbidden(
        message: str = "禁止访问",
        error_type: str = "forbidden",
        details: Any = None,
        suggestion: Optional[str] = None
    ) -> HTTPException:
        """禁止访问响应(403)"""
        return UnifiedResponse.error(
            message=message,
            status_code=403,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )
    
    @staticmethod
    def not_found(
        message: str = "资源不存在",
        error_type: str = "not_found",
        details: Any = None,
        suggestion: Optional[str] = None
    ) -> HTTPException:
        """资源不存在响应(404)"""
        return UnifiedResponse.error(
            message=message,
            status_code=404,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )
    
    @staticmethod
    def conflict(
        message: str = "资源冲突",
        error_type: str = "conflict",
        details: Any = None,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> HTTPException:
        """资源冲突响应(409)"""
        return UnifiedResponse.error(
            message=message,
            status_code=409,
            error_type=error_type,
            details=details,
            suggestion=suggestion,
            error_code=error_code
        )
    
    @staticmethod
    def payload_too_large(
        message: str = "请求体过大",
        error_type: str = "payload_too_large",
        details: Any = None,
        suggestion: Optional[str] = None
    ) -> HTTPException:
        """请求体过大响应(413)"""
        return UnifiedResponse.error(
            message=message,
            status_code=413,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )
    
    @staticmethod
    def internal_error(
        message: str = "服务器内部错误",
        error_type: str = "internal_error",
        details: Any = None,
        suggestion: Optional[str] = None
    ) -> HTTPException:
        """服务器内部错误响应(500)"""
        return UnifiedResponse.error(
            message=message,
            status_code=500,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )

