"""录音服务 - 业务流程编排

负责处理录音列表查询、音频获取、文本获取等业务逻辑。
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from parse.interfaces.asr_interface import ASRInterface
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
    
    def get_or_transcribe_text(
        self,
        elder_id: int,
        record_id: str,
        asr: ASRInterface,
    ) -> Tuple[RecordTextResult, Optional[str]]:
        """
        获取录音文本，如果不存在则先转写再返回
        
        流程：
        1. 检查文本是否已存在
        2. 如果存在，直接返回
        3. 如果不存在，获取音频路径，调用 ASR 转写，保存文本，然后返回
        
        Args:
            elder_id: 老人 ID
            record_id: 录音 ID
            asr: ASR 服务实例（实现 ASRInterface）
            
        Returns:
            Tuple[RecordTextResult, Optional[str]]: 
                - 录音文本结果
                - 错误信息（如有）
        """
        logger.info(f"获取或转写录音文本: elder_id={elder_id}, record_id={record_id}")
        
        # 1. 先检查文本是否已存在
        existing_result = self._repository.get_record_text(elder_id, record_id)
        if existing_result.found and existing_result.text:
            logger.info(f"文本已存在，直接返回: elder_id={elder_id}, record_id={record_id}")
            return existing_result, None
        
        # 2. 文本不存在，获取音频路径
        audio_path = self._repository.get_audio_path(elder_id, record_id)
        if audio_path is None:
            error_msg = "音频文件不存在，无法转写"
            logger.warning(f"{error_msg}: elder_id={elder_id}, record_id={record_id}")
            return RecordTextResult(
                elder_id=elder_id,
                record_id=record_id,
                text="",
                found=False,
            ), error_msg
        
        # 3. 调用 ASR 转写
        logger.info(f"开始转写音频: {audio_path}")
        asr_result = asr.transcribe(audio_path)
        
        if not asr_result.success or asr_result.text is None:
            error_msg = asr_result.error_message or "ASR 转写失败"
            logger.error(f"转写失败: elder_id={elder_id}, record_id={record_id}, error={error_msg}")
            return RecordTextResult(
                elder_id=elder_id,
                record_id=record_id,
                text="",
                found=False,
            ), error_msg
        
        # 4. 保存转写文本
        text = asr_result.text
        save_success = self._repository.save_record_text(elder_id, record_id, text)
        
        if not save_success:
            logger.warning(f"文本保存失败，但转写成功: elder_id={elder_id}, record_id={record_id}")
        
        logger.info(f"转写成功: elder_id={elder_id}, record_id={record_id}")
        
        return RecordTextResult(
            elder_id=elder_id,
            record_id=record_id,
            text=text,
            found=True,
        ), None
