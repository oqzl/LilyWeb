import os
import sys
import subprocess
import tempfile

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

# テンプレートファイルのパス
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "form3.html")


def load_template() -> str:
    """HTMLテンプレートファイルの内容を読み込む"""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = load_template()
    return HTMLResponse(content=html_content, status_code=200)


@app.post("/generate")
async def generate_pdf(
    title: str = Form(...),
    composer: str = Form(...),
    arranger: str = Form(default=""),  # 任意入力
    part_name: str = Form(...),
    clef: str = Form(...),
    key_signature: str = Form(...),
    ly_source: str = Form(...)
):
    if not ly_source:
        raise HTTPException(status_code=400, detail="楽譜の内容が入力されていません。")

    arranger_line = f'  arranger = "{arranger}"\n' if arranger.strip() else ""

    # ユーザーの入力値をもとに LilyPond ソースを生成
    final_source = f'''\\version "2.24.1"

#(ly:set-option 'point-and-click #f)
#(set-global-staff-size 17)

\paper {{
    ragged-bottom = ##t
    ragged-last-bottom = ##t
    ragged-last = ##f
    indent = #15
    line-width = #180
    top-margin = #15
    bottom-margin = #20
    system-system-spacing.basic-distance = #13
    top-system-spacing.basic-distance = #15
    last-bottom-spacing.basic-distance = #10
    top-margin-spacing.basic-distance = #20
    markup-system-spacing.basic-distance = #20
    print-page-number = ##f
}}

\\header {{
  title = "{title}"
  composer = "{composer}"
{arranger_line}
  tagline = "Generate by LilyWeb https://lilyweb.onrender.com/"
}}

score_body = {{
  \\new Staff \\with {{
    instrumentName = "{part_name}"
  }} {{
    \\clef {clef}
    \\relative c {{
      {ly_source}
    }}
  }}
}}

\\score {{
  \\score_body
  \\layout {{
  }}
}}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.ly")
        output_path = os.path.join(tmpdir, "input.pdf")

        # 入力された LilyPond ソースを一時ファイルに保存
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(final_source)

        try:
            result = subprocess.run(
                ["lilypond", "--pdf", input_path],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # タイムアウトの設定
            )
            if result.returncode != 0:
                error_message = result.stderr.decode("utf-8")
                # エラー時に処理中のファイル内容を標準エラーに出力
                with open(input_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                sys.stderr.write("LilyPond 実行エラー時の処理中ファイルの内容:\n" + file_content + "\n")
                raise HTTPException(status_code=500, detail=f"LilyPond実行エラー：\n{error_message}")
        except Exception as e:
            # 例外発生時にも処理中のファイル内容を標準エラーに出力
            with open(input_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            sys.stderr.write("例外発生時の処理中ファイルの内容:\n" + file_content + "\n")
            raise HTTPException(status_code=500, detail=f"エラーが発生しました：{str(e)}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="PDFが生成されませんでした。")

        return StreamingResponse(
            open(output_path, "rb"),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=score.pdf"}
        )
