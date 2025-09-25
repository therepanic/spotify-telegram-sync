FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        gcc \
        build-essential \
        libglib2.0-0 \
        libgl1 \
        libx11-6 \
        libxcb1 \
        libxext6 \
        libxrender1 \
        libfontconfig1 \
        python3-pyqt5 \
    && pip install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/spotify-telegram-sync/main.py"]
