FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    librdf0-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# 下载 Ollama 模型
RUN curl -fsSL https://ollama.ai/install.sh | sh

# 复制应用代码
COPY src/ ./src/
COPY data/ ./data/
COPY prompts/ ./prompts/
COPY .env.example .env

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
