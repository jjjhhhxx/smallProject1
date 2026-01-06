"""ASR 抽象接口定义

定义语音识别（ASR）服务的抽象接口，供 infra 层实现。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ASRResult:
    """ASR 转写结果"""
    
    success: bool
    text: Optional[str] = None
    error_message: Optional[str] = None


class ASRInterface(ABC):
    """ASR 服务抽象接口"""
    
    @abstractmethod
    def transcribe(self, audio_path: Path) -> ASRResult:
        """
        将音频文件转写为文本
        
        Args:
            audio_path: 音频文件的绝对路径
            
        Returns:
            ASRResult: 包含转写结果或错误信息
        """
        pass

