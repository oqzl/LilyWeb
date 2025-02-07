FROM python:3.9-slim

# OSパッケージと LilyPond のインストール
RUN apt-get update && apt-get install -y lilypond && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係のコピーとインストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . /app

# フォントのコピー
COPY fonts/ /usr/local/share/fonts/custom/
# フォントキャッシュの更新
RUN fc-cache -fv

# コンテナ起動時に uvicorn で FastAPI を起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
