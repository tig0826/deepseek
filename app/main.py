from fastapi import FastAPI
from vllm import LLM, SamplingParams

app = FastAPI()

# DeepSeek モデルのロード
model_path = "/models/deepseek"
llm = LLM(model=model_path)

@app.get("/")
async def root():
    return {"message": "DeepSeek API is running"}

@app.post("/generate/")
async def generate(prompt: str):
    sampling_params = SamplingParams(temperature=1.0, top_p=1.0, max_tokens=300)
    outputs = llm.generate([prompt], sampling_params)
    return {"response": outputs[0].outputs[0].text.strip()}
