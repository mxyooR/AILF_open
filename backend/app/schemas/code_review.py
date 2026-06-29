"""
代码审查相关的Pydantic Schema
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ReviewRequest(BaseModel):
    """代码审查请求"""
    generation_id: str = Field(..., description="代码生成ID")


class CheckResult(BaseModel):
    """检查结果"""
    score: int = Field(..., description="评分 (0-100)")
    issues: List[str] = Field(..., description="问题列表")
    status: str = Field(..., description="状态 (pass/warning/fail/error)")


class ReviewResult(BaseModel):
    """审查结果"""
    review_id: str = Field(..., description="审查ID")
    generation_id: str = Field(..., description="生成ID")
    started_at: str = Field(..., description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    status: str = Field(..., description="状态")
    checks: Dict[str, CheckResult] = Field(..., description="各项检查结果")
    overall_score: int = Field(..., description="总体评分")
    recommendation: str = Field(..., description="推荐意见")
    approval: Optional[Dict[str, Any]] = Field(None, description="批准信息")


class ReviewResponse(BaseModel):
    """审查响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[ReviewResult] = Field(None, description="审查结果")
    error: Optional[str] = Field(None, description="错误信息")


class ApprovalRequest(BaseModel):
    """批准请求"""
    review_id: str = Field(..., description="审查ID")
    approver: str = Field(..., description="批准人")
    comments: Optional[str] = Field(None, description="批准意见")


class RejectionRequest(BaseModel):
    """拒绝请求"""
    review_id: str = Field(..., description="审查ID")
    reviewer: str = Field(..., description="审查人")
    reason: str = Field(..., description="拒绝原因")


class ApprovalResponse(BaseModel):
    """批准/拒绝响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    error: Optional[str] = Field(None, description="错误信息")


class ReviewStatusResponse(BaseModel):
    """审查状态响应"""
    success: bool = Field(..., description="是否成功")
    current_review: Optional[ReviewResult] = Field(None, description="当前审查")
    recent_reviews: Optional[List[ReviewResult]] = Field(None, description="最近的审查")
    error: Optional[str] = Field(None, description="错误信息")
