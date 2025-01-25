FROM python:3.12-slim-bookworm

WORKDIR /app


COPY . .


RUN pip3 install --no-cache-dir -r requirements.txt


EXPOSE 5002

CMD ["gunicorn", "-w", "1", "--threads", "1",  "-b", "0.0.0.0:5002", "dashboard:dashboard_app"]
