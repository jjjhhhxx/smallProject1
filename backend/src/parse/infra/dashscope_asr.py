"""DashScope ASR 实现

使用阿里云 DashScope 的 qwen3-asr-flash 模型进行语音转写。
"""

import os
from pathlib import Path

import dashscope

from parse.interfaces.asr_interface import ASRInterface, ASRResult

# 设置北京地域 API 端点
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"


class DashScopeASR(ASRInterface):
    """DashScope ASR 服务实现"""
    
    def __init__(self, api_key: str | None = None):
        """
        初始化 DashScope ASR 服务
        
        Args:
            api_key: DashScope API Key，若为 None 则从环境变量 DASHSCOPE_API_KEY 读取
        """
        self._api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self._api_key:
            raise ValueError(
                "DashScope API Key 未设置。"
                "请设置环境变量 DASHSCOPE_API_KEY 或在初始化时传入 api_key 参数。"
            )
    
    def transcribe(self, audio_path: Path) -> ASRResult:
        """
        将音频文件转写为文本
        
        Args:
            audio_path: 音频文件的绝对路径
            
        Returns:
            ASRResult: 包含转写结果或错误信息
        """
        try:
            # 确保使用绝对路径的字符串形式
            abs_path = str(audio_path.resolve())
            
            messages = [
                {"role": "system", "content": [{"text": ""}]},
                {"role": "user", "content": [{"audio": abs_path}]},
            ]
            
            resp = dashscope.MultiModalConversation.call(
                api_key=self._api_key,
                model="qwen3-asr-flash",
                messages=messages,
                result_format="message",
                asr_options={"enable_itn": False},
            )
            
            # 健壮地提取转写文本
            text = self._extract_text(resp)
            
            if text is not None:
                return ASRResult(success=True, text=text)
            else:
                return ASRResult(
                    success=False,
                    error_message="无法从响应中提取转写文本，响应结构可能不符合预期"
                )
                
        except Exception as e:
            return ASRResult(success=False, error_message=str(e))
    
    def _extract_text(self, resp: dict) -> str | None:
        """
        从 DashScope 响应中提取转写文本
        
        健壮处理字段缺失的情况。
        预期路径: response["output"]["choices"][0]["message"]["content"][0]["text"]
        
        Args:
            resp: DashScope API 响应
            
        Returns:
            提取的文本，若路径不完整则返回 None
        """
        try:
            output = resp.get("output")
            if not output:
                return None
            
            choices = output.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                return None
            
            message = choices[0].get("message")
            if not message:
                return None
            
            content = message.get("content")
            if not content or not isinstance(content, list) or len(content) == 0:
                return None
            
            text = content[0].get("text")
            return text
            
        except (TypeError, KeyError, IndexError):
            return None

