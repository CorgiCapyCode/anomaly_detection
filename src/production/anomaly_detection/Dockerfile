FROM python:3.12-slim-bookworm

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5001

CMD ["python", "anomaly_detection.py"]