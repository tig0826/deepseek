from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

app = FastAPI()

# Trino の接続設定
TRINO_HOST = "trino.mynet"
TRINO_PORT = 80
TRINO_USER = "tig"
TRINO_CATALOG = "iceberg"
TRINO_SCHEMA = "dqx"

# Trino に接続する SQLAlchemy エンジン
engine = create_engine(f"trino://{TRINO_USER}@{TRINO_HOST}:{TRINO_PORT}/{TRINO_CATALOG}/{TRINO_SCHEMA}")
db = SQLDatabase(engine)

# LLM のセットアップ
llm = OllamaLLM(model="yuma/DeepSeek-R1-Distill-Qwen-Japanese:14b")

# LLM に SQL クエリを生成させる
sql_chain = create_sql_query_chain(llm, db)


# リクエスト用のデータモデル
class QueryRequest(BaseModel):
    question: str


@app.post("/query")
async def run_query(request: QueryRequest):
    """ ユーザーの質問から SQL を生成し、Trino でクエリを実行する """
    try:
        sql_query = sql_chain.invoke({"question": request.question})
        print(sql_query)

        with engine.connect() as connection:
            result = connection.execute(sql_query).fetchall()

        return {"query": sql_query, "result": result}

    except Exception as e:
        return {"error": str(e)}
