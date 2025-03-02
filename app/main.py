from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)

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

# スキーマ情報を取得
schema_info = db.get_table_info()

# LLM のセットアップ（プロンプト強化）
llm = OllamaLLM(
    model="yuma/DeepSeek-R1-Distill-Qwen-Japanese:14b",
    prompt_template="""
あなたは SQL クエリを生成する AI です。
次のデータベースのスキーマ情報を元に、正しい SQL を作成してください。

### データベース情報
対象は以下のテーブルです。
- テーブル名: price_hourly
  このテーブルは、オンラインゲーム、ドラゴンクエストX内のバーザー上でプレイヤーが出品しているアイテムの価格情報を記録しています。
  １つのレコードが一件の出品情報に対応しており、プレイヤーはいくつかのアイテムをまとめて出品して値段をつけることができます。
- カラム:
  - name: string
  出品されたアイテムの名前です。輝晶核、閃輝晶核、魔因細胞、閃魔因細胞、魔因細胞のかけら、閃魔因細胞のかけら、が主なアイテム名です。
  - 価格: int
  プレイヤーが出品しているアイテムの価格です。
  - 1つあたりの価格: int
  プレイヤーが出品しているアイテムの1つあたりの価格です。
  - 個数: int
  プレイヤーが出品しているアイテムの個数です。
  - できのよさ: varchar
  アイテムのクオリティです。武器や防具の場合は☆が多いほど価値が高く、付与できる効果が多くなります。--のばあいはクオリティが設定されていません。
  - 出品開始: varchar
  プレイヤーがアイテムを出品した日時です。
  - 出品終了: string
  出品が自動で取り下げられる日時です。プレイヤーが手動で取り下げることもできます。
  - 出品者: varchar
  アイテムを出品したプレイヤーの名前です。
  - date: varchar
  このレコードが記録された日付です。例: 2025-02-24
  datetime形式でクエリを生成する場合は先にcastして利用してください。
  - hour: varchar
  このレコードが記録された日時の時間帯です。
  時刻を指定してクエリを実行する場合は、先にcastして利用してください。
  例: 03


## ルール:
- 必ず `SELECT` クエリのみを生成してください
- 存在しないテーブルやカラムを使用しないでください
- クエリの出力は SQL のみで、それ以外の文章を含めないでください
- 価格について聞かれたときは、`1つあたりの価格` を使用してください。
- 平均や中央値などの指定がなく、XX日の価格を聞かれた場合は、その日の下位から5パーセンタイルの価格を利用してください。
## 例:
- 輝晶核の現在の平均価格を教えて下さい。
  現在の日付と時間を取得して、以下のクエリを生成してください。
  2025 2/24 12:25の場合は以下のようになります。
  → `SELECT AVG(ひとつあたりの価格) FROM price_hourly WHERE name = '輝晶核' AND date = '2025-02-24' AND hour = '12'`
  今日の日付と現在の時間は、実際の日付と時間に置き換えてください。
- 今月の輝晶核の価格の推移を教えて下さい。
  この場合、各日、各時刻の下位から5パーセンタイルの価格を取得してください。
  2/2 3:00から、2/24 9:00までの価格を取得するクエリは以下のようになります。
    SELECT
        date,
        hour,
        approx_percentile(CAST("1つあたりの価格" AS DOUBLE), 0.05) AS percentile_5
    FROM dqx.price_hourly
    WHERE name = '輝晶核'
    AND (
        (CAST(date AS DATE) = DATE '2025-02-01' AND CAST(hour AS INTEGER) >= 3) -- 取得の開始日と開始時間
        OR (CAST(date AS DATE) > DATE '2025-02-01' AND CAST(date AS DATE) < DATE '2025-02-24') -- 2/2 〜 2/23 の全時間
        OR (CAST(date AS DATE) = DATE '2025-02-24' AND CAST(hour AS INTEGER) <= 9) -- 終了日と終了時刻
    )
    GROUP BY date, hour
    ORDER BY date, hour;
  日付部分は実際にクエリで受け取った日付に直してください。

## 補足:
- ユーザは輝晶核や魔因細胞などのアイテムの価格情報を分析するためにあなたに質問します。
- オンラインゲーム内のアイテム相場は日々変動します。そのため、現在の日付と時間を取得してクエリを生成することが重要です。
- ユーザにとって価値のある情報を提供するために、正確なクエリを生成することが求められます。
"""
)

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
        logger.debug(f"Generated SQL: {sql_query}")

        with engine.connect() as connection:
            result = connection.execute(sql_query).fetchall()

        return {"query": sql_query, "result": result}

    except Exception as e:
        return {"error": str(e)}
