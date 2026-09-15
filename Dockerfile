FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face Spaces (Docker SDK) mặc định expose cổng 7860
ENV PORT=7860
EXPOSE 7860

CMD ["python", "app.py"]
