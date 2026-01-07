"""FastAPI 应用入口

启动命令（在 backend 目录下执行）:
    cd src && uvicorn main:app --reload --host 0.0.0.0 --port 8000

或者使用 --app-dir 参数:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir src
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from listen.api.auth_routes import auth_router
from listen.api.routes import router as listen_router
from parse.api.routes import router as parse_router
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(
    title="Listen API",
    description="语音录入模块 MVP",
    version="0.1.0",
)

# CORS 配置（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)  # /auth/* 认证相关路由
app.include_router(listen_router)
app.include_router(parse_router)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Listen API is running", "docs": "/docs"}

