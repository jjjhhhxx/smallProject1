"""仓库接口定义

定义 ListenRecord 数据访问的抽象接口，infra 层提供具体实现。
"""

from abc import ABC, abstractmethod
from typing import Optional

from models.listen_record import ListenRecord


class ListenRecordRepositoryInterface(ABC):
    """ListenRecord 仓库抽象接口"""

    @abstractmethod
    def create(
        self,
        elder_id: int,
        audio_path: str,
        status: str = "PENDING",
        context: str = "",
    ) -> ListenRecord:
        """
        创建新的 ListenRecord

        Args:
            elder_id: 老人ID
            audio_path: 音频文件相对路径
            status: 状态，默认 PENDING
            context: 上下文内容，默认为空

        Returns:
            ListenRecord: 创建的记录对象
        """
        pass

    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[ListenRecord]:
        """
        根据ID获取记录

        Args:
            record_id: 记录ID

        Returns:
            ListenRecord | None: 记录对象，不存在则返回 None
        """
        pass

    @abstractmethod
    def list_by_elder_id(
        self,
        elder_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ListenRecord]:
        """
        根据 elder_id 查询记录列表，按 created_at 倒序

        Args:
            elder_id: 老人ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            list[ListenRecord]: 记录列表
        """
        pass

    @abstractmethod
    def count_by_elder_id(self, elder_id: int) -> int:
        """
        统计某 elder_id 的记录总数

        Args:
            elder_id: 老人ID

        Returns:
            int: 记录总数
        """
        pass

    @abstractmethod
    def update_error(self, record_id: int, error_message: str) -> None:
        """
        更新记录的错误信息并将状态设为 ERROR

        Args:
            record_id: 记录ID
            error_message: 错误信息
        """
        pass

