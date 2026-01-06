# 1. 进入 backend 目录
cd D:\project\smallProgramme\demo1\backend

# 2. 安装依赖（如果还没安装）
pip install -r requirements.txt

# 3. 设置环境变量（可选，本地开发可用默认值）
$env:DATABASE_URL = "sqlite:///./dev.db"
$env:AUDIO_STORAGE_ROOT = "D:\project\store"

# 4. 启动服务
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000