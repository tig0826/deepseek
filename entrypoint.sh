#!/bin/sh

# Ollama サーバーをバックグラウンドで起動
ollama serve &

# 少し待機してからモデルをダウンロード
sleep 5
ollama pull yuma/DeepSeek-R1-Distill-Qwen-Japanese:14b

# FastAPI（Uvicorn）を起動
exec uvicorn main:app --host 0.0.0.0 --port 8000
