"""DTO 定义 - 数据传输对象"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TranscribeTaskResult:
    """转写任务结果统计"""
    
    total: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class TranscribeStartResponse:
    """转写任务启动响应"""
    
    started: bool
    audio_root: str
    context_root: str
    skipped_existing_txt: bool
    message: str


@dataclass
class TranscribeError:
    """转写错误记录"""
    
    file: str
    error: str
    time: str

