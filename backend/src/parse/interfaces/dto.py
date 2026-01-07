"""DTO 定义 - 数据传输对象"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


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


# ========== 录音相关 DTO ==========


@dataclass
class RecordItem:
    """单条录音信息"""
    
    id: str  # 唯一标识，格式: {date}/{filename_without_ext}
    filename: str  # 文件名（不含路径）
    date: str  # 日期 YYYY-MM-DD
    has_text: bool  # 是否有转写文本


@dataclass
class RecordListResult:
    """录音列表查询结果"""
    
    elder_id: int
    records: List[RecordItem]
    total: int


@dataclass
class RecordTextResult:
    """录音文本查询结果"""
    
    elder_id: int
    record_id: str
    text: str
    found: bool

