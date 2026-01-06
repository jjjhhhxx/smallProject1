"""存储接口定义

定义音频文件存储的抽象接口，infra 层提供具体实现。
"""

from abc import ABC, abstractmethod
from pathlib import Path


class AudioStorageInterface(ABC):
    """音频存储抽象接口"""

    @abstractmethod
    def save_audio(
        self,
        elder_id: int,
        file_content: bytes,
        original_filename: str,
    ) -> str:
        """
        保存音频文件

        Args:
            elder_id: 老人ID
            file_content: 文件二进制内容
            original_filename: 原始文件名（用于提取扩展名）

        Returns:
            str: 相对路径（相对于存储根目录），例如 "audio/123/2026-01-06/uuid.wav"

        Raises:
            StorageError: 存储失败时抛出
        """
        pass

    @abstractmethod
    def get_full_path(self, relative_path: str) -> Path:
        """
        获取完整路径

        Args:
            relative_path: 相对路径

        Returns:
            Path: 完整的文件系统路径
        """
        pass


class StorageError(Exception):
    """存储异常"""
    pass

