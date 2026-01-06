"""DashScope LLM 实现

基于阿里云 DashScope 的 LLM 服务实现。
使用 OpenAI 兼容接口调用 qwen 模型。
"""

import logging
import os
from typing import Optional

from openai import OpenAI

from parse.interfaces.llm_interface import LLMInterface, LLMResult

logger = logging.getLogger(__name__)


class DashScopeLLM(LLMInterface):
    """DashScope LLM 服务实现"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-plus",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        """
        初始化 DashScope LLM 客户端
        
        Args:
            api_key: DashScope API Key，默认从环境变量 DASHSCOPE_API_KEY 读取
            model: 模型名称，默认 qwen-plus
            base_url: API 基础 URL
        """
        self._api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self._model = model
        self._base_url = base_url
        
        if not self._api_key:
            logger.warning("DASHSCOPE_API_KEY 未设置，LLM 调用将会失败")
        
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
    
    def generate_summary(self, text: str, prompt: str) -> LLMResult:
        """
        调用 LLM 生成摘要
        
        Args:
            text: 待摘要的文本内容
            prompt: 系统提示词
            
        Returns:
            LLMResult: 包含生成结果或错误信息
        """
        if not self._api_key:
            return LLMResult(
                success=False,
                error_message="DASHSCOPE_API_KEY 未配置",
            )
        
        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ]
            
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
            
            content = completion.choices[0].message.content
            
            return LLMResult(
                success=True,
                content=content,
            )
            
        except Exception as e:
            logger.exception(f"LLM 调用失败: {e}")
            return LLMResult(
                success=False,
                error_message=str(e),
            )

