FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libmagic1 poppler-utils tesseract-ocr && rm -rf /var/lib/apt/lists/*
COPY requirements*.txt ./
RUN pip install --no-cache-dir 'torch<3' 'torchvision<1' --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 10001 cvboost && mkdir -p /app/.cache && chown -R cvboost:cvboost /app
USER cvboost
ENV PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
