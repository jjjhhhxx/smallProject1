"""Parse 模块 API 路由

提供触发转写任务的 HTTP 接口。
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from config import PARSE_AUDIO_ROOT, PARSE_CONTEXT_ROOT
from parse.application.transcribe_service import TranscribeService
from parse.infra.dashscope_asr import DashScopeASR
from parse.infra.file_lock import FileLock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["parse"])


class TranscribeAllResponse(BaseModel):
    """转写任务启动响应"""
    
    started: bool
    audio_root: str
    context_root: str
    skipped_existing_txt: bool
    message: str


def _get_lock_path() -> Path:
    """获取锁文件路径"""
    return PARSE_CONTEXT_ROOT / "_transcribe.lock"


def _run_transcribe_task(lock: FileLock) -> None:
    """
    执行转写任务（在后台线程中运行）
    
    任务结束后（无论成功失败）释放锁。
    
    Args:
        lock: 文件锁实例（已获取锁）
    """
    try:
        # 创建 ASR 服务
        asr = DashScopeASR()
        
        # 创建转写服务
        service = TranscribeService(
            asr=asr,
            audio_root=PARSE_AUDIO_ROOT,
            context_root=PARSE_CONTEXT_ROOT,
        )
        
        # 执行转写
        service.run()
        
    except Exception as e:
        logger.exception(f"转写任务执行异常: {e}")
        
    finally:
        # 无论成功失败，都要释放锁
        lock.release()
        logger.info("转写任务结束，已释放锁")


@router.get("/transcribe_all", response_model=TranscribeAllResponse)
async def transcribe_all(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    触发一次遍历转写任务
    
    - 后台执行：接口立即返回，不等待全部完成
    - 防止重复触发：如果任务正在运行，返回 started=false
    - 已存在且非空的 txt 文件会被跳过
    
    Returns:
        TranscribeAllResponse: 任务启动状态
    """
    lock_path = _get_lock_path()
    lock = FileLock(lock_path)
    
    # 尝试获取锁
    if not lock.acquire():
        # 锁已被持有，任务正在运行
        logger.info("转写任务已在运行中，跳过本次请求")
        return {
            "started": False,
            "audio_root": str(PARSE_AUDIO_ROOT),
            "context_root": str(PARSE_CONTEXT_ROOT),
            "skipped_existing_txt": True,
            "message": "already running",
        }
    
    # 获取锁成功，添加后台任务
    # 注意：锁的释放在 _run_transcribe_task 的 finally 中进行
    background_tasks.add_task(_run_transcribe_task, lock)
    
    logger.info(f"转写任务已启动，音频目录: {PARSE_AUDIO_ROOT}")
    
    return {
        "started": True,
        "audio_root": str(PARSE_AUDIO_ROOT),
        "context_root": str(PARSE_CONTEXT_ROOT),
        "skipped_existing_txt": True,
        "message": "started",
    }

