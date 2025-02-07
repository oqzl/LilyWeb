import os
import subprocess
import tempfile

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

# テンプレートファイルのパス
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "form2.html")


def load_template() -> str:
    """HTMLテンプレートファイルの内容を読み込む"""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = load_template()
    return HTMLResponse(content=html_content, status_code=200)


@app.post("/generate")
async def generate_pdf(ly_source: str = Form(...)):
    if not ly_source:
        raise HTTPException(status_code=400, detail="Lyソースが入力されていません。")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.ly")
        output_path = os.path.join(tmpdir, "input.pdf")

        # 入力されたLyソースを一時ファイルに保存
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(ly_source)

        # LilyPond を実行してPDFを生成
        try:
            result = subprocess.run(
                ["lilypond", "--pdf", input_path],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # タイムアウトを設定
            )
            if result.returncode != 0:
                error_message = result.stderr.decode("utf-8")
                raise HTTPException(status_code=500, detail=f"LilyPond実行エラー：\n{error_message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"エラーが発生しました：{str(e)}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="PDFが生成されませんでした。")

        # 生成されたPDFをストリームとして返す
        return StreamingResponse(
            open(output_path, "rb"),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=score.pdf"}
        )
