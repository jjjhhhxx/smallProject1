"""auth 模块 Repository 接口

定义用户数据访问的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from models.user import User


class IUserRepository(ABC):
    """用户 Repository 抽象接口"""

    @abstractmethod
    def find_by_openid(self, openid: str) -> Optional[User]:
        """根据微信 openid 查询用户
        
        Args:
            openid: 微信 openid
            
        Returns:
            用户对象，不存在则返回 None
        """
        pass

    @abstractmethod
    def create(self, role: str, wx_openid: str) -> User:
        """创建新用户
        
        Args:
            role: 用户角色 ELDER/CHILD
            wx_openid: 微信 openid
            
        Returns:
            创建的用户对象
        """
        pass
