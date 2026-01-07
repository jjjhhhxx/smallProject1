"""auth 模块 API 路由

只负责 HTTP 路由/参数校验/返回，不包含业务逻辑。
通过依赖注入获取 application 层服务。

注意：此 router 使用 prefix="/auth"，不要挂载到 listen_router 上，
而是直接在 main.py 中 include_router，以确保最终路径是 /auth/wx/login
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from listen.applicaton.auth_service import (
    AuthService,
    RoleConflictError,
    WxApiError,
    WxNetworkError,
)
from listen.infra.user_repository import UserRepository
from listen.interfaces.auth_dtos import WxLoginRequest, WxLoginResponse

# 注意：这是独立的 auth_router，不是 listen_router 的子路由
auth_router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """依赖注入：获取认证服务"""
    user_repository = UserRepository(db)
    return AuthService(user_repository)


@auth_router.post("/wx/login", response_model=WxLoginResponse)
def wx_login(
    request: WxLoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> WxLoginResponse:
    """
    微信小程序登录

    通过 uni.login() 获取的 code 换取 openid，并创建/查询用户，签发 JWT token。

    - **code**: uni.login() 返回的 code（必填）
    - **role**: 用户角色，ELDER（老人端）或 CHILD（子女端）（必填）

    返回 JWT token 和用户信息。
    """
    try:
        return service.wx_login(code=request.code, role=request.role)

    except WxApiError as e:
        # 微信 API 返回错误（如 code 无效）
        raise HTTPException(
            status_code=401,
            detail=f"微信登录失败: {e.errmsg}（错误码: {e.errcode}）",
        )

    except WxNetworkError as e:
        # 网络请求失败
        raise HTTPException(
            status_code=502,
            detail=f"微信服务暂时不可用，请稍后重试",
        )

    except RoleConflictError as e:
        # 角色冲突
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    except Exception as e:
        # 其他未知错误
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误",
        )
