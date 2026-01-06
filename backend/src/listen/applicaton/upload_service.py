"""上传服务

编排上传录音的完整流程：校验 -> 存储文件 -> 创建数据库记录
只依赖 interfaces 层，不直接依赖 infra 实现。
"""

from config import ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_SIZE_BYTES
from listen.interfaces.dtos import UploadResponse
from listen.interfaces.repository import ListenRecordRepositoryInterface
from listen.interfaces.storage import AudioStorageInterface, StorageError


class UploadValidationError(Exception):
    """上传参数校验异常（400 错误）"""
    pass


class UploadServiceError(Exception):
    """上传服务内部异常（500 错误）"""
    pass


class UploadService:
    """上传服务"""

    def __init__(
        self,
        storage: AudioStorageInterface,
        repository: ListenRecordRepositoryInterface,
    ):
        """
        初始化上传服务

        Args:
            storage: 音频存储实现
            repository: 记录仓库实现
        """
        self.storage = storage
        self.repository = repository

    def upload_audio(
        self,
        elder_id: int,
        file_content: bytes,
        filename: str,
    ) -> UploadResponse:
        """
        上传音频文件

        Args:
            elder_id: 老人ID
            file_content: 文件二进制内容
            filename: 原始文件名

        Returns:
            UploadResponse: 上传结果

        Raises:
            UploadValidationError: 参数校验失败（400）
            UploadServiceError: 内部错误（500）
        """
        # 1. 参数校验
        self._validate_elder_id(elder_id)
        self._validate_file(file_content, filename)

        # 2. 保存文件
        try:
            audio_path = self.storage.save_audio(elder_id, file_content, filename)
        except StorageError as e:
            raise UploadServiceError(f"保存文件失败: {e}") from e

        # 3. 创建数据库记录
        try:
            record = self.repository.create(
                elder_id=elder_id,
                audio_path=audio_path,
                status="PENDING",
                context="",
            )
        except Exception as e:
            # 数据库写入失败，尝试记录错误（但此时记录可能还不存在）
            raise UploadServiceError(f"数据库写入失败: {e}") from e

        return UploadResponse(
            record_id=record.id,
            status=record.status,
            audio_path=record.audio_path,
        )

    def _validate_elder_id(self, elder_id: int) -> None:
        """校验 elder_id"""
        if elder_id is None or elder_id <= 0:
            raise UploadValidationError("elder_id 必须为正整数")

    def _validate_file(self, file_content: bytes, filename: str) -> None:
        """校验上传文件"""
        # 检查文件是否为空
        if not file_content:
            raise UploadValidationError("上传文件不能为空")

        # 检查文件大小
        if len(file_content) > MAX_AUDIO_SIZE_BYTES:
            max_mb = MAX_AUDIO_SIZE_BYTES / (1024 * 1024)
            raise UploadValidationError(f"文件大小超过限制（最大 {max_mb:.0f}MB）")

        # 检查文件扩展名
        if not filename:
            raise UploadValidationError("文件名不能为空")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
            raise UploadValidationError(f"不支持的文件格式，允许的格式: {allowed}")

