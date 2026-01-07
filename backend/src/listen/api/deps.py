"""listen API 依赖项

放置与 HTTP 层相关的通用依赖（如认证解析），避免把逻辑散落在路由函数中。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Header, HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from config import JWT_SECRET


def get_current_elder_id(
    authorization: Optional[str] = Header(
        default=None,
        alias="Authorization",
        description="Bearer <token>（从 /auth/wx/login 获取）",
    )
) -> int:
    """从 Authorization Bearer token 中解析当前老人端用户 ID。

    规则：
    - 必须存在 Authorization: Bearer <token>
    - JWT 必须可用且未过期（HS256 + JWT_SECRET）
    - payload["role"] 必须为 "ELDER"
    - elder_id 优先取 payload["user_id"]，否则取 payload["sub"]，且必须为 >0 的整数
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization 请求头",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 格式错误，应为: Bearer <token>",
        )

    if not JWT_SECRET:
        # 服务器未正确配置密钥，避免继续处理（也避免泄漏配置细节）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器配置错误",
        )

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 已过期",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 无效",
        )

    role = payload.get("role")
    if role != "ELDER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅老人端允许上传录音",
        )

    raw_user_id = payload.get("user_id")
    if raw_user_id is None:
        raw_user_id = payload.get("sub")

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 中的 user_id 无效",
        )

    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 中的 user_id 无效",
        )

    return user_id

