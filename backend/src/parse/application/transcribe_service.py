"""转写服务 - 业务流程编排

负责遍历音频文件、调用 ASR 转写、保存结果、记录错误。
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from parse.interfaces.asr_interface import ASRInterface
from parse.interfaces.dto import TranscribeTaskResult

logger = logging.getLogger(__name__)


class TranscribeService:
    """音频转写服务"""
    
    def __init__(
        self,
        asr: ASRInterface,
        audio_root: Path,
        context_root: Path,
    ):
        """
        初始化转写服务
        
        Args:
            asr: ASR 服务实例（实现 ASRInterface）
            audio_root: 音频文件根目录
            context_root: 输出文本根目录
        """
        self._asr = asr
        self._audio_root = audio_root.resolve()
        self._context_root = context_root.resolve()
        self._error_log_path = self._context_root / "_errors.jsonl"
    
    def run(self) -> TranscribeTaskResult:
        """
        执行转写任务
        
        遍历所有 .wav 文件，调用 ASR 转写，保存结果。
        已存在且非空的 txt 文件会被跳过。
        
        Returns:
            TranscribeTaskResult: 任务结果统计
        """
        result = TranscribeTaskResult()
        
        # 确保输出目录存在
        self._context_root.mkdir(parents=True, exist_ok=True)
        
        # 遍历所有 .wav 文件
        for audio_path in self._iter_wav_files():
            result.total += 1
            
            # 计算输出路径
            output_path = self._get_output_path(audio_path)
            
            # 检查是否已存在且非空（去重/断点续跑）
            if self._should_skip(output_path):
                result.skipped += 1
                logger.info(f"跳过（已存在）: {audio_path}")
                continue
            
            # 调用 ASR 转写
            try:
                asr_result = self._asr.transcribe(audio_path)
                
                if asr_result.success and asr_result.text is not None:
                    # 保存转写结果
                    self._save_text(output_path, asr_result.text)
                    result.processed += 1
                    logger.info(f"转写成功: {audio_path}")
                else:
                    # ASR 返回失败
                    error_msg = asr_result.error_message or "未知错误"
                    self._log_error(audio_path, error_msg)
                    result.failed += 1
                    logger.error(f"转写失败: {audio_path} - {error_msg}")
                    
            except Exception as e:
                # 捕获所有异常，确保不中断全局
                error_msg = str(e)
                self._log_error(audio_path, error_msg)
                result.failed += 1
                logger.error(f"转写异常: {audio_path} - {error_msg}")
        
        # 打印进度统计
        logger.info(
            f"转写完成: total={result.total}, processed={result.processed}, "
            f"skipped={result.skipped}, failed={result.failed}"
        )
        print(
            f"\n=== 转写任务完成 ===\n"
            f"total: {result.total}\n"
            f"processed: {result.processed}\n"
            f"skipped: {result.skipped}\n"
            f"failed: {result.failed}\n"
        )
        
        return result
    
    def _iter_wav_files(self) -> Generator[Path, None, None]:
        """
        递归遍历音频根目录下所有 .wav 文件
        
        大小写不敏感。
        
        Yields:
            Path: .wav 文件路径
        """
        if not self._audio_root.exists():
            logger.warning(f"音频根目录不存在: {self._audio_root}")
            return
        
        # 使用 rglob 递归遍历，大小写不敏感
        for ext in ["*.wav", "*.WAV", "*.Wav"]:
            yield from self._audio_root.rglob(ext)
    
    def _get_output_path(self, audio_path: Path) -> Path:
        """
        计算输出文本文件路径
        
        保持相对目录结构一致，将 .wav 扩展名替换为 .txt。
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Path: 对应的文本文件路径
        """
        # 计算相对于音频根目录的相对路径
        rel_path = audio_path.relative_to(self._audio_root)
        
        # 替换扩展名为 .txt
        output_rel = rel_path.with_suffix(".txt")
        
        # 拼接到输出根目录
        return self._context_root / output_rel
    
    def _should_skip(self, output_path: Path) -> bool:
        """
        检查是否应该跳过（目标 txt 已存在且大小 > 0）
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            True 表示应该跳过
        """
        if not output_path.exists():
            return False
        
        try:
            return output_path.stat().st_size > 0
        except OSError:
            return False
    
    def _save_text(self, output_path: Path, text: str) -> None:
        """
        保存转写文本到文件
        
        Args:
            output_path: 输出文件路径
            text: 转写文本（纯文本，无元信息）
        """
        # 确保父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入 UTF-8 编码的纯文本
        output_path.write_text(text, encoding="utf-8")
    
    def _log_error(self, audio_path: Path, error_message: str) -> None:
        """
        将错误追加写入 JSONL 文件
        
        Args:
            audio_path: 出错的音频文件路径
            error_message: 错误信息
        """
        error_record = {
            "file": str(audio_path.resolve()),
            "error": error_message,
            "time": datetime.now(timezone.utc).isoformat(),
        }
        
        # 确保父目录存在
        self._error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 追加写入一行 JSON
        with open(self._error_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_record, ensure_ascii=False) + "\n")

