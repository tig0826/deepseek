# FROM nvidia/cuda:12.1.1-base-ubuntu22.04
FROM python:3.11.6-slim

RUN pip install poetry

# 必要なライブラリをインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpq-dev \
    gcc \
    fonts-noto-cjk \
    kmod \
    && rm -rf /var/lib/apt/lists/*

# 必要なPythonパッケージをインストール
# ENV PATH="$POETRY_HOME/bin:$PATH"
# COPY pyproject.toml pyproject.toml
# RUN poetry install --no-root
RUN python3 -m pip install --no-cache-dir --upgrade pip

# 依存関係の事前インストール
RUN pip install --no-cache-dir numpy

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# PyTorch の CPU バージョンをインストール
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# vLLM（CPUで動作するようにインストール）
RUN pip install --no-cache-dir vllm

# モデルのダウンロード（or ローカルマウント）
RUN git clone https://huggingface.co/deepseek-ai/DeepSeek-R1 /models/deepseek

# 作業ディレクトリ
WORKDIR /app

# FastAPI アプリのコピー
COPY app /app

# FastAPI サーバーの起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
