"""auth 模块 DTOs（数据传输对象）

定义微信登录 API 层与 application 层之间传递的数据结构。
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class WxLoginRequest(BaseModel):
    """微信登录请求 DTO"""
    code: str = Field(..., min_length=1, description="uni.login 返回的 code")
    role: Literal["ELDER", "CHILD"] = Field(..., description="用户角色：ELDER 老人端 / CHILD 子女端")


class WxLoginResponse(BaseModel):
    """微信登录响应 DTO"""
    token: str = Field(..., description="JWT token")
    user_id: int = Field(..., description="用户ID")
    role: Literal["ELDER", "CHILD"] = Field(..., description="用户角色")
    elder_id: Optional[int] = Field(None, description="老人ID（role=ELDER 时返回）")
    child_id: Optional[int] = Field(None, description="子女ID（role=CHILD 时返回）")


class WxLoginErrorResponse(BaseModel):
    """微信登录错误响应 DTO"""
    detail: str = Field(..., description="错误信息")
