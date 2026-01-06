"""本地文件存储实现

实现 AudioStorageInterface，将音频文件存储到本地磁盘。
存储路径结构: {AUDIO_STORAGE_ROOT}/audio/{elder_id}/YYYY-MM-DD/{uuid}.{ext}

audio_path 存储相对路径的原因：
1. 跨环境迁移：相对路径在不同部署环境下只需修改根目录配置，无需更新数据库记录
2. 数据库简洁：相对路径更短，数据库存储更高效
3. 灵活性：未来可能迁移到云存储，相对路径作为 key 更通用
"""

import uuid
from datetime import date
from pathlib import Path

from config import AUDIO_STORAGE_ROOT, AUDIO_SUBDIR
from listen.interfaces.storage import AudioStorageInterface, StorageError


class LocalAudioStorage(AudioStorageInterface):
    """本地音频存储实现"""

    def __init__(self, root_path: Path | None = None):
        """
        初始化本地存储

        Args:
            root_path: 存储根目录，默认使用配置文件中的 AUDIO_STORAGE_ROOT
        """
        self.root_path = root_path or AUDIO_STORAGE_ROOT
        self.root_path.mkdir(parents=True, exist_ok=True)

    def save_audio(
        self,
        elder_id: int,
        file_content: bytes,
        original_filename: str,
    ) -> str:
        """
        保存音频文件到本地磁盘

        返回相对路径，格式: audio/{elder_id}/YYYY-MM-DD/{uuid}.{ext}
        """
        # 提取扩展名
        ext = Path(original_filename).suffix.lstrip(".").lower()
        if not ext:
            ext = "bin"

        # 生成目标路径
        today = date.today().isoformat()  # YYYY-MM-DD
        unique_name = f"{uuid.uuid4().hex}.{ext}"

        # 相对路径
        relative_path = Path(AUDIO_SUBDIR) / str(elder_id) / today / unique_name

        # 完整路径
        full_path = self.root_path / relative_path

        try:
            # 确保目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            full_path.write_bytes(file_content)

            # 返回相对路径（使用正斜杠以保证跨平台一致性）
            return relative_path.as_posix()

        except OSError as e:
            raise StorageError(f"保存音频文件失败: {e}") from e

    def get_full_path(self, relative_path: str) -> Path:
        """获取完整的文件系统路径"""
        return self.root_path / relative_path



