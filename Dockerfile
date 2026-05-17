FROM python:3.12-slim

WORKDIR /app

COPY main.py ./
COPY digital_twin_pkg/ ./digital_twin_pkg/

CMD ["python", "main.py"]
