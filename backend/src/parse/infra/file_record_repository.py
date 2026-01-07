"""文件系统录音仓库实现

基于文件系统实现录音数据的读取操作。
"""

import logging
from pathlib import Path
from typing import List, Optional

from parse.interfaces.dto import RecordItem, RecordListResult, RecordTextResult
from parse.interfaces.record_repository import RecordRepositoryInterface

logger = logging.getLogger(__name__)

# 支持的音频扩展名
AUDIO_EXTENSIONS = {".wav", ".WAV", ".Wav", ".mp3", ".MP3", ".m4a", ".M4A", ".amr", ".AMR"}


class FileSystemRecordRepository(RecordRepositoryInterface):
    """基于文件系统的录音仓库实现"""
    
    def __init__(self, audio_root: Path, context_root: Path):
        """
        初始化仓库
        
        Args:
            audio_root: 音频文件根目录
            context_root: 转写文本根目录
        """
        self._audio_root = audio_root.resolve()
        self._context_root = context_root.resolve()
    
    def list_records(self, elder_id: int) -> RecordListResult:
        """
        获取指定老人的所有录音列表
        
        遍历 audio_root/{elder_id}/ 下所有日期目录中的音频文件
        """
        records: List[RecordItem] = []
        
        elder_audio_dir = self._audio_root / str(elder_id)
        
        if not elder_audio_dir.exists():
            logger.info(f"老人音频目录不存在: {elder_audio_dir}")
            return RecordListResult(elder_id=elder_id, records=[], total=0)
        
        # 遍历所有日期目录
        for date_dir in sorted(elder_audio_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            date_str = date_dir.name  # 假设目录名就是日期 YYYY-MM-DD
            
            # 遍历该日期下的所有音频文件
            for audio_file in sorted(date_dir.iterdir(), reverse=True):
                if not audio_file.is_file():
                    continue
                
                # 检查是否是音频文件
                if audio_file.suffix not in AUDIO_EXTENSIONS:
                    continue
                
                filename = audio_file.name
                filename_without_ext = audio_file.stem
                
                # 生成 record_id: date/filename_without_ext
                record_id = f"{date_str}/{filename_without_ext}"
                
                # 检查是否有对应的转写文本
                text_path = self._context_root / str(elder_id) / date_str / f"{filename_without_ext}.txt"
                has_text = text_path.exists() and text_path.stat().st_size > 0
                
                records.append(RecordItem(
                    id=record_id,
                    filename=filename,
                    date=date_str,
                    has_text=has_text,
                ))
        
        logger.info(f"找到 {len(records)} 条录音记录: elder_id={elder_id}")
        
        return RecordListResult(
            elder_id=elder_id,
            records=records,
            total=len(records),
        )
    
    def get_audio_path(self, elder_id: int, record_id: str) -> Optional[Path]:
        """
        获取指定录音的音频文件路径
        
        record_id 格式: {date}/{filename_without_ext}
        """
        try:
            parts = record_id.split("/", 1)
            if len(parts) != 2:
                logger.warning(f"无效的 record_id 格式: {record_id}")
                return None
            
            date_str, filename_without_ext = parts
            
            # 构建音频目录路径
            audio_dir = self._audio_root / str(elder_id) / date_str
            
            if not audio_dir.exists():
                logger.warning(f"音频目录不存在: {audio_dir}")
                return None
            
            # 尝试各种扩展名
            for ext in AUDIO_EXTENSIONS:
                audio_path = audio_dir / f"{filename_without_ext}{ext}"
                if audio_path.exists():
                    return audio_path
            
            logger.warning(f"音频文件不存在: elder_id={elder_id}, record_id={record_id}")
            return None
            
        except Exception as e:
            logger.error(f"获取音频路径失败: {e}")
            return None
    
    def get_record_text(self, elder_id: int, record_id: str) -> RecordTextResult:
        """
        获取指定录音的转写文本
        
        record_id 格式: {date}/{filename_without_ext}
        """
        try:
            parts = record_id.split("/", 1)
            if len(parts) != 2:
                logger.warning(f"无效的 record_id 格式: {record_id}")
                return RecordTextResult(
                    elder_id=elder_id,
                    record_id=record_id,
                    text="",
                    found=False,
                )
            
            date_str, filename_without_ext = parts
            
            # 构建文本文件路径
            text_path = self._context_root / str(elder_id) / date_str / f"{filename_without_ext}.txt"
            
            if not text_path.exists():
                logger.info(f"文本文件不存在: {text_path}")
                return RecordTextResult(
                    elder_id=elder_id,
                    record_id=record_id,
                    text="",
                    found=False,
                )
            
            # 读取文本内容
            text = text_path.read_text(encoding="utf-8").strip()
            
            return RecordTextResult(
                elder_id=elder_id,
                record_id=record_id,
                text=text,
                found=True,
            )
            
        except Exception as e:
            logger.error(f"读取录音文本失败: {e}")
            return RecordTextResult(
                elder_id=elder_id,
                record_id=record_id,
                text="",
                found=False,
            )
