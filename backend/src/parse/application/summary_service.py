"""摘要服务 - 业务流程编排

负责读取文本、拼接内容、调用 LLM 生成摘要、保存结果。
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from parse.interfaces.llm_interface import LLMInterface
from typing import Any

def _to_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list):
        items = [str(x).strip() for x in v if str(x).strip()]
        if not items:
            return ""
        # 拼成 markdown 的 bullet，前端直接展示也好看
        return "- " + "\n- ".join(items)
    # 兜底：避免再炸
    return str(v).strip()

logger = logging.getLogger(__name__)

# 最大拼接字符数
MAX_CHARS = 30000

# 摘要系统提示词（要求输出 JSON 格式）
SUMMARY_SYSTEM_PROMPT = """你是一位专业的老人关怀助手。你需要根据老人的语音转写文本，生成结构化摘要。

请严格按照以下 JSON 格式输出，不要输出任何 Markdown 标题、代码块标记或其他解释文字，只输出纯 JSON 对象：

{
  "summary": "讲话内容摘要（要点列表，用中文描述）",
  "physical_status": "可能的身体状况（必须使用'可能'、'疑似'、'需核实'、'无法诊断'等措辞，不能当作医疗诊断。如无相关信息，写'无明显异常提及，待确认'）",
  "psychological_needs": "可能的心理需求（必须使用'可能'、'推测'、'需核实'等措辞。如无相关信息，写'待确认'）",
  "advice": "建议子女下一步（可执行的建议，必要时建议就医/联系家人等，用中文描述）"
}

输出要求：
1. 只输出 JSON 对象，不要包裹在 ```json 代码块中
2. 不要输出 Markdown 标题（如 ## 讲话内容摘要）
3. 使用中文
4. 不要编造原文没有的信息
5. 不确定的内容写"待确认"
6. 身体状况和心理需求的描述必须谨慎，避免下定论
7. 四个字段的值必须是字符串，不允许输出 JSON 数组；如果需要分点，请在字符串里用换行和 '-' 表示"""


@dataclass
class SummaryResult:
    """摘要生成结果"""
    
    elder_id: int
    date: str
    summary: str
    physical_status: str
    psychological_needs: str
    advice: str
    message: str


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
        summary_path = summary_dir / "_summary.json"
        
        # 检查缓存
        if not force:
            cached_data = self._load_cached_summary(summary_path)
            if cached_data is not None:
                logger.info(f"使用缓存摘要: {summary_path}")
                return SummaryResult(
                    elder_id=elder_id,
                    date=date,
                    summary=cached_data.get("summary", ""),
                    physical_status=cached_data.get("physical_status", ""),
                    psychological_needs=cached_data.get("psychological_needs", ""),
                    advice=cached_data.get("advice", ""),
                    message="cached",
                ), None
        
        # 读取并拼接文本
        merged_text, file_count = self._read_and_merge_texts(context_dir)
        
        if not merged_text:
            logger.info(f"无可用文件: {context_dir}")
            return SummaryResult(
                elder_id=elder_id,
                date=date,
                summary="",
                physical_status="",
                psychological_needs="",
                advice="",
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
                physical_status="",
                psychological_needs="",
                advice="",
                message="llm error",
            ), error_msg
        
        # 解析 LLM 返回的 JSON
        llm_content = llm_result.content or ""
        parsed_data = self._parse_llm_json(llm_content)
        
        if parsed_data is None:
            error_msg = "LLM 返回的不是有效的 JSON 格式"
            logger.error(f"{error_msg}: {llm_content[:200]}")
            return SummaryResult(
                elder_id=elder_id,
                date=date,
                summary="",
                physical_status="",
                psychological_needs="",
                advice="",
                message="llm error",
            ), error_msg
        
        # 归一化：确保所有字段都是字符串（兼容 LLM 返回 list 的情况）
        normalized = {
            "summary": _to_text(parsed_data.get("summary")),
            "physical_status": _to_text(parsed_data.get("physical_status")),
            "psychological_needs": _to_text(parsed_data.get("psychological_needs")),
            "advice": _to_text(parsed_data.get("advice")),
        }
        
        # 保存归一化后的摘要到 JSON 文件
        self._save_summary_json(summary_path, normalized)
        logger.info(f"摘要已保存: {summary_path}")
        
        return SummaryResult(
            elder_id=elder_id,
            date=date,
            summary=normalized["summary"],
            physical_status=normalized["physical_status"],
            psychological_needs=normalized["psychological_needs"],
            advice=normalized["advice"],
            message="generated",
        ), None
    
    def _load_cached_summary(self, summary_path: Path) -> Optional[Dict[str, str]]:
        """
        加载缓存的摘要 JSON 文件，并归一化所有字段为字符串
        
        Args:
            summary_path: 摘要 JSON 文件路径
            
        Returns:
            Optional[Dict[str, str]]: 归一化后的数据，如果文件不存在或解析失败则返回 None
        """
        if not summary_path.exists():
            return None
        
        try:
            if summary_path.stat().st_size == 0:
                return None
            
            content = summary_path.read_text(encoding="utf-8")
            data = json.loads(content)
            
            # 验证必需字段
            required_fields = ["summary", "physical_status", "psychological_needs", "advice"]
            if not all(field in data for field in required_fields):
                logger.warning(f"缓存文件缺少必需字段: {summary_path}")
                return None
            
            # 归一化：确保所有字段都是字符串（兼容旧缓存中存的是 list 的情况）
            normalized = {
                "summary": _to_text(data.get("summary")),
                "physical_status": _to_text(data.get("physical_status")),
                "psychological_needs": _to_text(data.get("psychological_needs")),
                "advice": _to_text(data.get("advice")),
            }
            
            # 检查是否需要修复旧缓存（如果原数据中有 list 类型）
            needs_fix = any(
                isinstance(data.get(f), list) for f in required_fields
            )
            if needs_fix:
                logger.info(f"修复旧缓存文件（包含 list 字段）: {summary_path}")
                self._save_summary_json(summary_path, normalized)
            
            return normalized
            
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"读取缓存文件失败: {summary_path}, error: {e}")
            return None
    
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
    
    def _parse_llm_json(self, content: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 返回的 JSON 内容
        
        尝试从输出中提取第一个 {...} 作为 JSON。
        
        Args:
            content: LLM 返回的原始内容
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的 JSON 数据，解析失败返回 None
        """
        if not content:
            return None
        
        # 首先尝试直接解析
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        
        # 尝试提取第一个 {...} 作为 JSON
        # 找到第一个 { 的位置
        start_idx = content.find('{')
        if start_idx == -1:
            return None
        
        # 从第一个 { 开始，找到匹配的最后一个 }
        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx != -1:
            json_str = content[start_idx:end_idx + 1]
            try:
                data = json.loads(json_str)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _save_summary_json(self, summary_path: Path, data: Dict[str, Any]) -> None:
        """
        保存摘要到 JSON 文件
        
        Args:
            summary_path: 摘要 JSON 文件路径
            data: 摘要数据字典
        """
        # 确保父目录存在
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入 UTF-8 编码的 JSON
        summary_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

