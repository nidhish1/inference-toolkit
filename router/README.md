# Qsentia Router

Small FastAPI service that routes prediction requests to model containers.

It loads active model routes from DynamoDB into two maps:

```text
prod[modelname]
staging[modelname]
```

## DynamoDB Item

```json
{
  "model_name": "portfolio-ranker",
  "model_version": "2026-06-24-001",
  "env": "prod",
  "status": "active",
  "endpoint_url": "http://portfolio-ranker-prod.internal:8080"
}
```

## Env Vars

```bash
export AWS_REGION=us-east-2
export MODEL_REGISTRY_TABLE=qsentia-model-registry
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
```

## Run

```bash
docker compose up --build
```

## Endpoints

```text
GET  /health
POST /predict
POST /reload
```

## Predict

```json
{
  "modelname": "portfolio-ranker",
  "env": "prod",
  "data": {}
}
```

Response:

```json
{
  "data": {}
}
```
