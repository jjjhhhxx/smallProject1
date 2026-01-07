"""listen 模块 API 路由

只负责 HTTP 路由/参数校验/返回，不包含业务逻辑。
通过依赖注入获取 application 层服务。
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from db import get_db
from listen.applicaton.query_service import QueryService
from listen.applicaton.upload_service import (
    UploadService,
    UploadServiceError,
    UploadValidationError,
)
from listen.api.deps import get_current_elder_id
from listen.infra.listen_repository import ListenRecordRepository
from listen.infra.local_storage import LocalAudioStorage
from listen.interfaces.dtos import RecordsQueryResponse, UploadResponse

router = APIRouter(prefix="/listen", tags=["listen"])


def get_upload_service(db: Session = Depends(get_db)) -> UploadService:
    """依赖注入：获取上传服务"""
    storage = LocalAudioStorage()
    repository = ListenRecordRepository(db)
    return UploadService(storage, repository)


def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    """依赖注入：获取查询服务"""
    repository = ListenRecordRepository(db)
    return QueryService(repository)


@router.post("/upload", response_model=UploadResponse)
async def upload_audio(
    audio_file: UploadFile = File(..., description="音频文件"),
    elder_id: int = Depends(get_current_elder_id),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    """
    上传录音文件

    - **audio_file**: 音频文件（multipart/form-data，支持 wav/mp3/m4a/amr，最大 20MB）
    - **Authorization**: Bearer <token>（从 /auth/wx/login 获取；仅老人端 ELDER 可调用）

    返回创建的记录信息。
    """
    try:
        # 读取文件内容
        file_content = await audio_file.read()

        # 调用 application 层服务
        return service.upload_audio(
            elder_id=elder_id,
            file_content=file_content,
            filename=audio_file.filename or "",
        )

    except UploadValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except UploadServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/records", response_model=RecordsQueryResponse)
async def list_records(
    elder_id: int = Query(..., gt=0, description="老人ID"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    service: QueryService = Depends(get_query_service),
) -> RecordsQueryResponse:
    """
    查询录音记录列表

    - **elder_id**: 老人ID（必填）
    - **limit**: 返回数量限制（默认 20，最大 100）
    - **offset**: 偏移量（默认 0）

    返回按 created_at 倒序排列的记录列表。
    """
    try:
        return service.list_records(elder_id=elder_id, limit=limit, offset=offset)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")

