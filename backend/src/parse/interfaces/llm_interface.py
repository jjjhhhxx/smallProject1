"""LLM 抽象接口定义

定义大语言模型（LLM）服务的抽象接口，供 infra 层实现。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResult:
    """LLM 调用结果"""
    
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None


class LLMInterface(ABC):
    """LLM 服务抽象接口"""
    
    @abstractmethod
    def generate_summary(self, text: str, prompt: str) -> LLMResult:
        """
        基于输入文本和提示词生成摘要
        
        Args:
            text: 待摘要的文本内容
            prompt: 系统提示词
            
        Returns:
            LLMResult: 包含生成结果或错误信息
        """
        pass

