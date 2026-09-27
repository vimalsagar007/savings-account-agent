FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY README.md .
COPY savings_account_agent/ ./savings_account_agent/
COPY app.py .

RUN pip install --no-cache-dir . uvicorn

EXPOSE 8080

CMD ["uvicorn", "app:api", "--host", "0.0.0.0", "--port", "8080"]
