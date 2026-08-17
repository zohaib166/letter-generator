FROM python:3.13-slim

WORKDIR /app

# System dependencies required by WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libharfbuzz-subset0 \
    libfontconfig1 \
    libfreetype6 \
    libjpeg62-turbo \
    libopenjp2-7 \
    libffi8 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/storage/pdfs \
    /app/storage/documents \
    /app/storage/letterhead \
    /app/storage/signatures

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]