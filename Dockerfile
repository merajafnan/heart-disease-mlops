ARG PYTHON_VERSION=3.14
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements-api.txt ./
RUN python -m pip install --no-cache-dir -r requirements-api.txt
COPY heart_mlops ./heart_mlops
COPY artifacts/model.joblib ./artifacts/model.joblib
COPY artifacts/model_metadata.json ./artifacts/model_metadata.json

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "heart_mlops.api:app", "--host", "0.0.0.0", "--port", "8000"]
