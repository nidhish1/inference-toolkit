FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MODEL_BUNDLE_PATH=/models/model_bundle

WORKDIR /srv/qsentia-serving

COPY serving-bundle-boilerplate/runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY serving-bundle-boilerplate/runtime/app ./app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
