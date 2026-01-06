"""ListenRecord 仓库实现

实现 ListenRecordRepositoryInterface，提供数据库访问操作。
"""

from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from listen.interfaces.repository import ListenRecordRepositoryInterface
from models.listen_record import ListenRecord


class ListenRecordRepository(ListenRecordRepositoryInterface):
    """ListenRecord 仓库实现"""

    def __init__(self, db: Session):
        """
        初始化仓库

        Args:
            db: SQLAlchemy Session 对象
        """
        self.db = db

    def create(
        self,
        elder_id: int,
        audio_path: str,
        status: str = "PENDING",
        context: str = "",
    ) -> ListenRecord:
        """创建新的 ListenRecord"""
        record = ListenRecord(
            elder_id=elder_id,
            audio_path=audio_path,
            status=status,
            context=context,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, record_id: int) -> Optional[ListenRecord]:
        """根据ID获取记录"""
        return self.db.query(ListenRecord).filter(ListenRecord.id == record_id).first()

    def list_by_elder_id(
        self,
        elder_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ListenRecord]:
        """根据 elder_id 查询记录列表，按 created_at 倒序"""
        return (
            self.db.query(ListenRecord)
            .filter(ListenRecord.elder_id == elder_id)
            .order_by(desc(ListenRecord.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_elder_id(self, elder_id: int) -> int:
        """统计某 elder_id 的记录总数"""
        return (
            self.db.query(func.count(ListenRecord.id))
            .filter(ListenRecord.elder_id == elder_id)
            .scalar()
            or 0
        )

    def update_error(self, record_id: int, error_message: str) -> None:
        """更新记录的错误信息并将状态设为 ERROR"""
        record = self.get_by_id(record_id)
        if record:
            record.status = "ERROR"
            record.error_message = error_message
            self.db.commit()

