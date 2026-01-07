"""录音服务 - 业务流程编排

负责处理录音列表查询、音频获取、文本获取等业务逻辑。
"""

import logging
from pathlib import Path
from typing import Optional

from parse.interfaces.dto import RecordListResult, RecordTextResult
from parse.interfaces.record_repository import RecordRepositoryInterface

logger = logging.getLogger(__name__)


class RecordService:
    """录音服务"""
    
    def __init__(self, record_repository: RecordRepositoryInterface):
        """
        初始化录音服务
        
        Args:
            record_repository: 录音仓库实例（实现 RecordRepositoryInterface）
        """
        self._repository = record_repository
    
    def get_records(self, elder_id: int) -> RecordListResult:
        """
        获取指定老人的所有录音列表
        
        Args:
            elder_id: 老人 ID
            
        Returns:
            RecordListResult: 录音列表结果
        """
        logger.info(f"查询老人录音列表: elder_id={elder_id}")
        return self._repository.list_records(elder_id)
    
    def get_audio_path(self, elder_id: int, record_id: str) -> Optional[Path]:
        """
        获取指定录音的音频文件路径
        
        Args:
            elder_id: 老人 ID
            record_id: 录音 ID
            
        Returns:
            Optional[Path]: 音频文件路径，不存在返回 None
        """
        logger.info(f"获取音频路径: elder_id={elder_id}, record_id={record_id}")
        return self._repository.get_audio_path(elder_id, record_id)
    
    def get_record_text(self, elder_id: int, record_id: str) -> RecordTextResult:
        """
        获取指定录音的转写文本
        
        Args:
            elder_id: 老人 ID
            record_id: 录音 ID
            
        Returns:
            RecordTextResult: 录音文本结果
        """
        logger.info(f"获取录音文本: elder_id={elder_id}, record_id={record_id}")
        return self._repository.get_record_text(elder_id, record_id)
