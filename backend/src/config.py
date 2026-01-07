"""全局配置模块

所有配置项优先从环境变量读取，若未设置则使用默认值。
"""

import os
from pathlib import Path

# ========== 音频存储配置 ==========

# 音频存储根目录，支持跨平台
# 优先读取环境变量 AUDIO_STORAGE_ROOT
# 若未设置，Windows 本地默认为 D:\project\store
AUDIO_STORAGE_ROOT: Path = Path(
    os.getenv("AUDIO_STORAGE_ROOT", r"D:\project\store")
).resolve()

# 音频文件子目录（相对于 AUDIO_STORAGE_ROOT）
AUDIO_SUBDIR = "audio"

# 允许的音频文件扩展名（不含点号）
ALLOWED_AUDIO_EXTENSIONS: set[str] = {"wav", "mp3", "m4a", "amr"}

# 最大文件大小（字节），默认 20MB
MAX_AUDIO_SIZE_BYTES: int = int(os.getenv("MAX_AUDIO_SIZE_BYTES", 20 * 1024 * 1024))


# ========== Parse 模块配置 ==========

# 音频文件根目录（用于转写）
# 优先读取环境变量 AUDIO_ROOT
PARSE_AUDIO_ROOT: Path = Path(
    os.getenv("AUDIO_ROOT", r"D:\project\store\audio")
).resolve()

# 转写文本输出根目录
# 优先读取环境变量 CONTEXT_ROOT
PARSE_CONTEXT_ROOT: Path = Path(
    os.getenv("CONTEXT_ROOT", r"D:\project\store\context")
).resolve()

# 摘要输出根目录
# 优先读取环境变量 PARSE_SUMMARY_ROOT
PARSE_SUMMARY_ROOT: Path = Path(
    os.getenv("PARSE_SUMMARY_ROOT", r"D:\project\store\summary")
).resolve()

# 启动时确保摘要目录存在
PARSE_SUMMARY_ROOT.mkdir(parents=True, exist_ok=True)


# ========== 数据库配置 ==========

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")


# ========== 微信小程序配置 ==========

# 微信小程序 AppID
WECHAT_APPID: str = os.getenv("WECHAT_APPID", "")

# 微信小程序 AppSecret（注意：不要在日志中打印此值）
WECHAT_APPSECRET: str = os.getenv("WECHAT_APPSECRET", "")


# ========== JWT 配置 ==========

# JWT 签名密钥（注意：生产环境务必设置强密钥）
JWT_SECRET: str = os.getenv("JWT_SECRET", "")

# JWT 过期时间（分钟），默认 43200 分钟 = 30 天
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))
