import os
import dashscope

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"  # 北京地域

audio_path = os.path.abspath(r"D:\project\store\audio\123\2026-01-06\699285abca2b4d56a24abb69b2892b92.wav")  # 必须是绝对路径

messages = [
    {"role": "system", "content": [{"text": ""}]},
    {"role": "user", "content": [{"audio": audio_path}]},
]

resp = dashscope.MultiModalConversation.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
    asr_options={"enable_itn": False},
)

# 取出转写文本（文档里的响应结构就是这么给的）
text = resp["output"]["choices"][0]["message"]["content"][0]["text"]
print(text)
