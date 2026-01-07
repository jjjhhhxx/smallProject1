"""auth 模块 Application 层服务

处理微信登录的业务逻辑，包括：
- 调用微信 jscode2session 接口获取 openid
- 创建或查询用户
- 签发 JWT token
"""

import os
from datetime import datetime, timedelta
from typing import Literal

import requests
from jose import jwt

from listen.interfaces.auth_dtos import WxLoginResponse
from listen.interfaces.auth_repository import IUserRepository


class AuthServiceError(Exception):
    """认证服务通用错误"""
    pass


class WxApiError(AuthServiceError):
    """微信 API 调用错误"""
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"微信 API 错误: {errcode} - {errmsg}")


class WxNetworkError(AuthServiceError):
    """微信 API 网络错误"""
    pass


class RoleConflictError(AuthServiceError):
    """角色冲突错误：该微信号已注册为另一角色"""
    pass


class AuthService:
    """认证服务"""

    # 微信 jscode2session 接口地址
    WX_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
        
        # 从环境变量读取配置（不写死）
        self._appid = os.getenv("WECHAT_APPID", "")
        self._appsecret = os.getenv("WECHAT_APPSECRET", "")
        self._jwt_secret = os.getenv("JWT_SECRET", "")
        self._jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))  # 默认 30 天

    def wx_login(self, code: str, role: Literal["ELDER", "CHILD"]) -> WxLoginResponse:
        """微信小程序登录
        
        Args:
            code: uni.login 返回的 code
            role: 用户角色 ELDER/CHILD
            
        Returns:
            WxLoginResponse 包含 token、user_id、role 等信息
            
        Raises:
            WxApiError: 微信 API 返回错误
            WxNetworkError: 网络请求失败
            RoleConflictError: 该微信号已注册为另一角色
        """
        # 1. 调用微信 jscode2session 接口获取 openid
        openid = self._get_openid_from_wx(code)

        # 2. 查询或创建用户
        user = self._user_repository.find_by_openid(openid)
        
        if user is None:
            # 新用户，创建
            user = self._user_repository.create(role=role, wx_openid=openid)
        else:
            # 已存在用户，检查角色是否一致
            if user.role != role:
                raise RoleConflictError(
                    f"该微信号已注册为 {user.role}，不能切换为 {role}"
                )

        # 3. 生成 JWT token
        token = self._generate_jwt(user_id=user.id, role=user.role)

        # 4. 构建响应
        response = WxLoginResponse(
            token=token,
            user_id=user.id,
            role=user.role,
            elder_id=user.id if user.role == "ELDER" else None,
            child_id=user.id if user.role == "CHILD" else None,
        )

        return response

    def _get_openid_from_wx(self, code: str) -> str:
        """调用微信 jscode2session 接口获取 openid
        
        Args:
            code: uni.login 返回的 code
            
        Returns:
            用户的 openid
            
        Raises:
            WxApiError: 微信 API 返回错误码
            WxNetworkError: 网络请求失败
        """
        params = {
            "appid": self._appid,
            "secret": self._appsecret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            response = requests.get(
                self.WX_CODE2SESSION_URL,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise WxNetworkError(f"微信 API 网络请求失败: {e}")

        # 检查微信返回的错误
        if "errcode" in data and data["errcode"] != 0:
            raise WxApiError(
                errcode=data.get("errcode", -1),
                errmsg=data.get("errmsg", "未知错误"),
            )

        openid = data.get("openid")
        if not openid:
            raise WxApiError(errcode=-1, errmsg="微信返回数据中缺少 openid")

        return openid

    def _generate_jwt(self, user_id: int, role: str) -> str:
        """生成 JWT token
        
        Args:
            user_id: 用户ID
            role: 用户角色
            
        Returns:
            JWT token 字符串
        """
        expire = datetime.utcnow() + timedelta(minutes=self._jwt_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "role": role,
            "exp": expire,
        }

        token = jwt.encode(payload, self._jwt_secret, algorithm="HS256")
        return token
