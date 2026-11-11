FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.2" && pip install --no-cache-dir . && useradd --uid 10001 --create-home ledger
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
