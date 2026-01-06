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


# ========== 数据库配置 ==========

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

