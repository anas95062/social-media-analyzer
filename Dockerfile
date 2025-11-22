FROM python:3.9-slim
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]