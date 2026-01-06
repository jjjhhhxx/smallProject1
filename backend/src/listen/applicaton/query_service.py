"""查询服务

编排查询录音记录的流程。
只依赖 interfaces 层，不直接依赖 infra 实现。
"""

from listen.interfaces.dtos import RecordItem, RecordsQueryResponse
from listen.interfaces.repository import ListenRecordRepositoryInterface


class QueryService:
    """查询服务"""

    def __init__(self, repository: ListenRecordRepositoryInterface):
        """
        初始化查询服务

        Args:
            repository: 记录仓库实现
        """
        self.repository = repository

    def list_records(
        self,
        elder_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> RecordsQueryResponse:
        """
        查询某 elder_id 的记录列表

        Args:
            elder_id: 老人ID
            limit: 返回数量限制，默认 20
            offset: 偏移量，默认 0

        Returns:
            RecordsQueryResponse: 查询结果
        """
        records = self.repository.list_by_elder_id(elder_id, limit, offset)
        total = self.repository.count_by_elder_id(elder_id)

        items = [
            RecordItem(
                id=r.id,
                elder_id=r.elder_id,
                context=r.context,
                status=r.status,
                audio_path=r.audio_path,
                error_message=r.error_message,
                created_at=r.created_at,
                updated_at=r.updated_at,
                summary=r.summary,
                summary_status=r.summary_status,
            )
            for r in records
        ]

        return RecordsQueryResponse(records=items, total=total)

