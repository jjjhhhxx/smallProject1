"""Parse 模块 API 路由

提供触发转写任务和摘要生成的 HTTP 接口。
"""

import logging
import re
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import PARSE_AUDIO_ROOT, PARSE_CONTEXT_ROOT, PARSE_SUMMARY_ROOT
from parse.application.record_service import RecordService
from parse.application.summary_service import SummaryService
from parse.application.transcribe_service import TranscribeService
from parse.infra.dashscope_asr import DashScopeASR
from parse.infra.dashscope_llm import DashScopeLLM
from parse.infra.file_lock import FileLock
from parse.infra.file_record_repository import FileSystemRecordRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["parse"])


class TranscribeAllResponse(BaseModel):
    """转写任务启动响应"""
    
    started: bool
    audio_root: str
    context_root: str
    skipped_existing_txt: bool
    message: str


class SummaryResponse(BaseModel):
    """摘要生成响应"""
    
    elder_id: int
    date: str
    summary: str
    physical_status: str
    psychological_needs: str
    advice: str
    message: str


class RecordItemResponse(BaseModel):
    """单条录音响应"""
    
    id: str
    filename: str
    date: str
    has_text: bool


class RecordListResponse(BaseModel):
    """录音列表响应"""
    
    elder_id: int
    records: List[RecordItemResponse]
    total: int


class RecordTextResponse(BaseModel):
    """录音文本响应"""
    
    elder_id: int
    record_id: str
    text: str
    found: bool


# 日期格式正则：YYYY-MM-DD
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    elder_id: int = Query(..., description="老人 ID，必须是正整数", gt=0),
    date: str = Query(..., description="日期，格式 YYYY-MM-DD"),
    force: bool = Query(False, description="是否强制重新生成摘要"),
) -> dict[str, Any]:
    """
    生成指定老人在指定日期的摘要
    
    - 读取当天所有转写文本
    - 调用 LLM 生成结构化摘要
    - 支持缓存复用（force=true 可强制重新生成）
    
    Args:
        elder_id: 老人 ID（正整数）
        date: 日期（YYYY-MM-DD 格式）
        force: 是否强制重新生成
        
    Returns:
        SummaryResponse: 摘要结果
        
    Raises:
        400: 参数校验失败
        500: 读取文件异常
        502: LLM 调用失败
    """
    # 校验日期格式
    if not DATE_PATTERN.match(date):
        raise HTTPException(
            status_code=400,
            detail=f"日期格式错误，必须为 YYYY-MM-DD，实际为: {date}",
        )
    
    try:
        # 创建 LLM 服务
        llm = DashScopeLLM()
        
        # 创建摘要服务
        service = SummaryService(
            llm=llm,
            context_root=PARSE_CONTEXT_ROOT,
            summary_root=PARSE_SUMMARY_ROOT,
        )
        
        # 生成摘要
        result, error = service.generate_summary(
            elder_id=elder_id,
            date=date,
            force=force,
        )
        
        if error:
            # LLM 调用失败
            logger.error(f"摘要生成失败: elder_id={elder_id}, date={date}, error={error}")
            raise HTTPException(
                status_code=502,
                detail="LLM调用失败",
            )
        
        return {
            "elder_id": result.elder_id,
            "date": result.date,
            "summary": result.summary,
            "physical_status": result.physical_status,
            "psychological_needs": result.psychological_needs,
            "advice": result.advice,
            "message": result.message,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"摘要接口异常: {e}")
        raise HTTPException(
            status_code=500,
            detail="读取文件异常",
        )


# ========== 录音相关路由 ==========


def _get_record_service() -> RecordService:
    """创建录音服务实例"""
    repository = FileSystemRecordRepository(
        audio_root=PARSE_AUDIO_ROOT,
        context_root=PARSE_CONTEXT_ROOT,
    )
    return RecordService(record_repository=repository)


@router.get("/records", response_model=RecordListResponse)
async def get_records(
    elder_id: int = Query(..., description="老人 ID，必须是正整数", gt=0),
) -> dict[str, Any]:
    """
    获取指定老人的所有录音列表
    
    Args:
        elder_id: 老人 ID（正整数）
        
    Returns:
        RecordListResponse: 录音列表
    """
    try:
        service = _get_record_service()
        result = service.get_records(elder_id)
        
        return {
            "elder_id": result.elder_id,
            "records": [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "date": r.date,
                    "has_text": r.has_text,
                }
                for r in result.records
            ],
            "total": result.total,
        }
        
    except Exception as e:
        logger.exception(f"获取录音列表异常: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取录音列表失败",
        )


@router.get("/records/{elder_id}/{record_id:path}/audio")
async def get_record_audio(
    elder_id: int,
    record_id: str,
) -> FileResponse:
    """
    获取指定录音的音频文件
    
    Args:
        elder_id: 老人 ID
        record_id: 录音 ID（格式: {date}/{filename_without_ext}）
        
    Returns:
        FileResponse: 音频文件
        
    Raises:
        404: 音频文件不存在
    """
    if elder_id <= 0:
        raise HTTPException(status_code=400, detail="老人ID必须是正整数")
    
    try:
        service = _get_record_service()
        audio_path = service.get_audio_path(elder_id, record_id)
        
        if audio_path is None:
            raise HTTPException(
                status_code=404,
                detail="音频文件不存在",
            )
        
        # 根据扩展名确定 media_type
        ext = audio_path.suffix.lower()
        media_type_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".amr": "audio/amr",
        }
        media_type = media_type_map.get(ext, "audio/wav")
        
        return FileResponse(
            path=audio_path,
            media_type=media_type,
            filename=audio_path.name,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取音频文件异常: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取音频文件失败",
        )


@router.get("/records/{elder_id}/{record_id:path}/text", response_model=RecordTextResponse)
async def get_record_text(
    elder_id: int,
    record_id: str,
) -> dict[str, Any]:
    """
    获取指定录音的转写文本
    
    如果文本不存在，会自动触发转写后返回。
    
    Args:
        elder_id: 老人 ID
        record_id: 录音 ID（格式: {date}/{filename_without_ext}）
        
    Returns:
        RecordTextResponse: 录音文本
        
    Raises:
        400: 参数校验失败
        404: 音频文件不存在
        502: ASR 转写失败
        500: 其他异常
    """
    if elder_id <= 0:
        raise HTTPException(status_code=400, detail="老人ID必须是正整数")
    
    try:
        # 创建 ASR 服务
        asr = DashScopeASR()
        
        # 获取录音服务
        service = _get_record_service()
        
        # 获取或转写文本
        result, error = service.get_or_transcribe_text(elder_id, record_id, asr)
        
        if error:
            # 根据错误类型返回不同状态码
            if "音频文件不存在" in error:
                raise HTTPException(status_code=404, detail=error)
            else:
                # ASR 转写失败
                raise HTTPException(status_code=502, detail=f"转写失败: {error}")
        
        return {
            "elder_id": result.elder_id,
            "record_id": result.record_id,
            "text": result.text,
            "found": result.found,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取录音文本异常: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取录音文本失败",
        )

