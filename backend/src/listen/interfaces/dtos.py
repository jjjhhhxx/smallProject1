"""listen 模块 DTOs（数据传输对象）

定义 API 层与 application 层之间传递的数据结构。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    """上传录音请求 DTO"""
    elder_id: int = Field(..., gt=0, description="老人ID，必须为正整数")


class UploadResponse(BaseModel):
    """上传录音响应 DTO"""
    record_id: int
    status: str
    audio_path: str


class RecordItem(BaseModel):
    """单条记录 DTO"""
    id: int
    elder_id: int
    context: str
    status: str
    audio_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str]
    summary_status: str

    class Config:
        from_attributes = True


class RecordsQueryResponse(BaseModel):
    """查询记录列表响应 DTO"""
    records: list[RecordItem]
    total: int


class ErrorResponse(BaseModel):
    """错误响应 DTO"""
    detail: str

