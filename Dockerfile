# 軽量な Python ベースのイメージ
FROM python:3.11.6-slim

# 必要なライブラリをインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpq-dev \
    gcc \
    g++ \
    cmake \
    ninja-build \
    fonts-noto-cjk \
    kmod \
    && rm -rf /var/lib/apt/lists/*

# pip のアップグレード
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# **NumPy を事前にインストール**
RUN python3 -m pip install --no-cache-dir numpy

# **PyTorch の CPU バージョンをインストール**
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# vLLM を wheel からインストール
COPY whl_cache/vllm-*.whl /tmp/
RUN pip install --no-cache-dir /tmp/vllm-*.whl

# **vLLM のインストール（プリビルドバイナリを利用）**
# RUN pip install --no-cache-dir --timeout=10000 vllm  # 公式の PyPI バイナリを利用

# 依存関係のインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# **モデルのダウンロード（or ローカルマウント）**
RUN git clone https://huggingface.co/deepseek-ai/DeepSeek-R1 /models/deepseek

# 作業ディレクトリ
WORKDIR /app

# FastAPI アプリのコピー
COPY app /app

# FastAPI サーバーの起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
