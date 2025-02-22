from fastapi import FastAPI, UploadFile, File
import torch
import torchvision.transforms as transforms
import cv2
import numpy as np
import io
from PIL import Image
import ffmpeg

app = FastAPI()

# モデルのロード
model = torch.hub.load("deepseek-ai/deepseek-vision", "deepseek_model")
model.eval()

def preprocess_video(video_bytes):
    # FFmpegでフレームを抽出
    process = (
        ffmpeg
        .input("pipe:0")
        .filter("fps", fps=1)  # 1秒ごとに1フレーム取得
        .output("pipe:1", format="rawvideo", pix_fmt="rgb24")
        .run(capture_stdout=True, input=video_bytes)
    )

    # 画像に変換
    images = []
    for i in range(0, len(process[0]), 640*480*3):  # 640x480の解像度を仮定
        img = np.frombuffer(process[0][i:i+640*480*3], np.uint8).reshape(480, 640, 3)
        images.append(img)
    
    return images

@app.post("/analyze_video/")
async def analyze_video(file: UploadFile = File(...)):
    video_bytes = await file.read()
    frames = preprocess_video(video_bytes)

    results = []
    for frame in frames:
        img = Image.fromarray(frame)
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])
        input_tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            result = model(input_tensor)
        results.append(result.tolist())

    return {"results": results}
