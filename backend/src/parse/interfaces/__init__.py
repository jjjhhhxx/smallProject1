"""Interfaces 层 - 抽象接口与 DTO 定义"""

from parse.interfaces.dto import (
    RecordItem,
    RecordListResult,
    RecordTextResult,
    TranscribeError,
    TranscribeStartResponse,
    TranscribeTaskResult,
)
from parse.interfaces.record_repository import RecordRepositoryInterface

__all__ = [
    "RecordItem",
    "RecordListResult",
    "RecordTextResult",
    "RecordRepositoryInterface",
    "TranscribeError",
    "TranscribeStartResponse",
    "TranscribeTaskResult",
]

