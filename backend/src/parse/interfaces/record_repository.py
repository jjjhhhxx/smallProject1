"""录音仓库接口定义

定义录音数据访问的抽象接口。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from parse.interfaces.dto import RecordItem, RecordListResult, RecordTextResult


class RecordRepositoryInterface(ABC):
    """录音仓库接口"""
    
    @abstractmethod
    def list_records(self, elder_id: int) -> RecordListResult:
        """
        获取指定老人的所有录音列表
        
        Args:
            elder_id: 老人 ID
            
        Returns:
            RecordListResult: 录音列表结果
        """
        pass
    
    @abstractmethod
    def get_audio_path(self, elder_id: int, record_id: str) -> Optional[Path]:
        """
        获取指定录音的音频文件路径
        
        Args:
            elder_id: 老人 ID
            record_id: 录音 ID（格式: {date}/{filename_without_ext}）
            
        Returns:
            Optional[Path]: 音频文件路径，不存在返回 None
        """
        pass
    
    @abstractmethod
    def get_record_text(self, elder_id: int, record_id: str) -> RecordTextResult:
        """
        获取指定录音的转写文本
        
        Args:
            elder_id: 老人 ID
            record_id: 录音 ID（格式: {date}/{filename_without_ext}）
            
        Returns:
            RecordTextResult: 录音文本结果
        """
        pass
    
    @abstractmethod
    def save_record_text(self, elder_id: int, record_id: str, text: str) -> bool:
        """
        保存指定录音的转写文本
        
        Args:
            elder_id: 老人 ID
            record_id: 录音 ID（格式: {date}/{filename_without_ext}）
            text: 转写文本内容
            
        Returns:
            bool: 保存是否成功
        """
        pass
