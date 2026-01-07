FROM python:3.11-slim

# 更少坑：避免 Python 输出缓存
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 先装依赖，利用 Docker 缓存加速二次构建
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 再复制代码
COPY . /app

# 你的 main.py 在 src 里，所以切到 src 运行
WORKDIR /app/src

EXPOSE 8000

# 线上不要 --reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
