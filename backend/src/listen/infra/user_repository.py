"""用户 Repository 实现

实现 IUserRepository 接口，提供用户数据访问功能。
"""

from typing import Optional

from sqlalchemy.orm import Session

from listen.interfaces.auth_repository import IUserRepository
from models.user import User


class UserRepository(IUserRepository):
    """用户 Repository 实现"""

    def __init__(self, db: Session):
        self._db = db

    def find_by_openid(self, openid: str) -> Optional[User]:
        """根据微信 openid 查询用户"""
        return self._db.query(User).filter(User.wx_openid == openid).first()

    def create(self, role: str, wx_openid: str) -> User:
        """创建新用户"""
        user = User(role=role, wx_openid=wx_openid)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
