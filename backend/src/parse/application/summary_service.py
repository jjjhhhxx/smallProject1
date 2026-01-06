"""摘要服务 - 业务流程编排

负责读取文本、拼接内容、调用 LLM 生成摘要、保存结果。
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from parse.interfaces.llm_interface import LLMInterface

logger = logging.getLogger(__name__)

# 最大拼接字符数
MAX_CHARS = 30000

# 摘要系统提示词
SUMMARY_SYSTEM_PROMPT = """你是一位专业的老人关怀助手。你需要根据老人的语音转写文本，生成结构化摘要。

请严格按照以下格式输出摘要：

## 讲话内容摘要
- （要点1）
- （要点2）
- ...

## 可能的身体状况
（基于文本推测老人可能的身体状况。必须使用"可能"、"疑似"、"需核实"、"无法诊断"等措辞，不能当作医疗诊断。如无相关信息，写"无明显异常提及，待确认"）

## 可能的心理需求
（推测老人可能的心理需求。必须使用"可能"、"推测"、"需核实"等措辞。如无相关信息，写"待确认"）

## 建议子女下一步
- （可执行的建议1）
- （可执行的建议2，必要时建议就医/联系家人等）
- ...

输出要求：
1. 使用中文
2. 分点清晰
3. 不要编造原文没有的信息
4. 不确定的内容写"待确认"
5. 身体状况和心理需求的描述必须谨慎，避免下定论"""


@dataclass
class SummaryResult:
    """摘要生成结果"""
    
    elder_id: int
    date: str
    summary: str
    message: str
    from_cache: bool = False


class SummaryService:
    """摘要服务"""
    
    def __init__(
        self,
        llm: LLMInterface,
        context_root: Path,
        summary_root: Path,
    ):
        """
        初始化摘要服务
        
        Args:
            llm: LLM 服务实例
            context_root: 转写文本根目录
            summary_root: 摘要输出根目录
        """
        self._llm = llm
        self._context_root = context_root.resolve()
        self._summary_root = summary_root.resolve()
    
    def generate_summary(
        self,
        elder_id: int,
        date: str,
        force: bool = False,
    ) -> Tuple[SummaryResult, Optional[str]]:
        """
        生成指定老人在指定日期的摘要
        
        Args:
            elder_id: 老人 ID
            date: 日期（YYYY-MM-DD 格式）
            force: 是否强制重新生成
            
        Returns:
            Tuple[SummaryResult, Optional[str]]: 
                - 摘要结果
                - 错误信息（如有）
        """
        # 构建路径
        context_dir = self._context_root / str(elder_id) / date
        summary_dir = self._summary_root / str(elder_id) / date
        summary_path = summary_dir / "_summary.txt"
        
        # 检查缓存
        if not force and self._has_valid_cache(summary_path):
            cached_summary = summary_path.read_text(encoding="utf-8")
            logger.info(f"使用缓存摘要: {summary_path}")
            return SummaryResult(
                elder_id=elder_id,
                date=date,
                summary=cached_summary,
                message="from cache",
                from_cache=True,
            ), None
        
        # 读取并拼接文本
        merged_text, file_count = self._read_and_merge_texts(context_dir)
        
        if not merged_text:
            logger.info(f"无可用文件: {context_dir}")
            return SummaryResult(
                elder_id=elder_id,
                date=date,
                summary="",
                message="no files",
            ), None
        
        logger.info(f"拼接了 {file_count} 个文件，共 {len(merged_text)} 字符")
        
        # 调用 LLM 生成摘要
        llm_result = self._llm.generate_summary(merged_text, SUMMARY_SYSTEM_PROMPT)
        
        if not llm_result.success:
            error_msg = llm_result.error_message or "LLM 调用失败"
            logger.error(f"LLM 调用失败: {error_msg}")
            return SummaryResult(
                elder_id=elder_id,
                date=date,
                summary="",
                message="llm error",
            ), error_msg
        
        summary_text = llm_result.content or ""
        
        # 保存摘要
        self._save_summary(summary_path, summary_text)
        logger.info(f"摘要已保存: {summary_path}")
        
        return SummaryResult(
            elder_id=elder_id,
            date=date,
            summary=summary_text,
            message="generated",
        ), None
    
    def _has_valid_cache(self, summary_path: Path) -> bool:
        """检查摘要缓存是否存在且有效"""
        if not summary_path.exists():
            return False
        
        try:
            return summary_path.stat().st_size > 0
        except OSError:
            return False
    
    def _read_and_merge_texts(self, context_dir: Path) -> Tuple[str, int]:
        """
        读取目录下的文本文件并拼接
        
        策略：从排序后的列表末尾开始向前拼接，保留最新内容
        
        Args:
            context_dir: 文本目录
            
        Returns:
            Tuple[str, int]: (拼接后的文本, 文件数量)
        """
        if not context_dir.exists():
            return "", 0
        
        # 获取所有 .txt 文件，排除 "_" 开头的文件
        txt_files = self._get_valid_txt_files(context_dir)
        
        if not txt_files:
            return "", 0
        
        # 按路径字典序排序
        txt_files = sorted(txt_files)
        
        # 从末尾向前读取，直到达到最大长度
        contents: List[str] = []
        total_chars = 0
        file_count = 0
        
        for txt_file in reversed(txt_files):
            try:
                content = txt_file.read_text(encoding="utf-8").strip()
                
                # 忽略空文件
                if not content:
                    continue
                
                # 检查是否超过最大长度
                content_len = len(content)
                if total_chars + content_len + 2 > MAX_CHARS:  # +2 for "\n\n"
                    break
                
                contents.append(content)
                total_chars += content_len + 2
                file_count += 1
                
            except Exception as e:
                logger.warning(f"读取文件失败 {txt_file}: {e}")
                continue
        
        # 反转回正序（因为是从末尾开始收集的）
        contents.reverse()
        
        return "\n\n".join(contents), file_count
    
    def _get_valid_txt_files(self, directory: Path) -> List[Path]:
        """
        获取目录下所有有效的 .txt 文件
        
        排除 "_" 开头的文件
        
        Args:
            directory: 目录路径
            
        Returns:
            List[Path]: 有效的 txt 文件列表
        """
        txt_files = []
        
        for txt_file in directory.glob("*.txt"):
            # 忽略 "_" 开头的文件
            if txt_file.name.startswith("_"):
                continue
            
            txt_files.append(txt_file)
        
        return txt_files
    
    def _save_summary(self, summary_path: Path, summary_text: str) -> None:
        """
        保存摘要到文件
        
        Args:
            summary_path: 摘要文件路径
            summary_text: 摘要内容
        """
        # 确保父目录存在
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入 UTF-8 编码
        summary_path.write_text(summary_text, encoding="utf-8")

