# ---- Step 1: モデルを事前にダウンロードしたベースイメージを作成 ----
FROM python:3.9 AS ollama-base

WORKDIR /app

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ollama のインストール
RUN curl -fsSL https://ollama.com/install.sh | sh

# モデルをダウンロード
RUN ollama serve & sleep 5 && ollama pull yuma/DeepSeek-R1-Distill-Qwen-Japanese:14b

# ---- Step 2: アプリケーションをビルド ----
FROM python:3.9

WORKDIR /app

# 事前にダウンロードしたモデルをコピー
COPY --from=ollama-base /root/.ollama /root/.ollama

# アプリケーションのコードをコピー
COPY ./app /app

# コンテナ起動時に Ollama サーバーと FastAPI を起動
CMD sh -c "ollama serve & sleep 5 && uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug"
