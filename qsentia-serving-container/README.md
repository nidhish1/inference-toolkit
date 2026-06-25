# Qsentia Serving Container

Generic FastAPI model-serving shell for swappable Qsentia model bundles.

The container does not need to know whether a bundle uses LightGBM, CatBoost,
PyTorch, sklearn, or custom portfolio logic. It loads `manifest.json`, imports
the configured adapter, calls `adapter.load(...)`, and delegates prediction to
`adapter.predict(...)`.

## Runtime Contract

```text
container starts
-> reads MODEL_BUNDLE_PATH
-> loads manifest.json
-> imports adapter
-> adapter.load(model_bundle)
-> starts FastAPI
-> POST /predict calls adapter.predict(...)
```

## Endpoints

```text
GET  /health
GET  /model-info
POST /predict
```

## Model Bundle Shape

```text
model_bundle/
  manifest.json
  artifacts/
    lgb_model.txt
    catboost_model.cbm
    pytorch_model.pt
    scaler.joblib
    imputer.joblib
  code/
    model_adapter.py
  schemas/
    input_schema.json
    output_schema.json
  config/
    config.json
```

## Manifest Example

```json
{
  "model_name": "qsentia-finance-ranker",
  "model_version": "0.1.0",
  "adapter": {
    "type": "pytorch"
  },
  "model": {
    "module": "model_architecture",
    "class": "RankerModel",
    "kwargs": {
      "num_features": 2
    }
  },
  "artifacts": {
    "pytorch_state_dict": "artifacts/pytorch_model.pt"
  },
  "feature_columns": ["momentum_20d", "volatility_20d"],
  "python_version": "3.11"
}
```

For PyTorch bundles, prefer providing architecture code plus a state dict. The
built-in PyTorch adapter instantiates the configured class, calls
`load_state_dict(...)`, moves the model to the target device, and calls
`model.eval()` before serving.

## Local Run

```bash
export MODEL_BUNDLE_PATH=./sample_model_bundle
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Docker

```bash
docker build -t qsentia-serving:latest .

docker run \
  -p 8080:8080 \
  -e MODEL_BUNDLE_PATH=/models/model_bundle \
  -v /local/model_bundle:/models/model_bundle \
  qsentia-serving:latest
```

## Prediction Request Example

```json
{
  "as_of_date": "2026-06-24",
  "universe": ["AAPL", "MSFT"],
  "positions": [
    {"symbol": "AAPL", "weight": 0.05}
  ],
  "market_data": {
    "AAPL": {"close": 200.0},
    "MSFT": {"close": 420.0}
  }
}
```

## Prediction Response Example

```json
{
  "as_of_date": "2026-06-24",
  "scores": [
    {"symbol": "AAPL", "score": 1.42}
  ],
  "target_weights": [
    {"symbol": "AAPL", "weight": 0.1}
  ],
  "orders": [
    {"symbol": "AAPL", "delta_weight": 0.05}
  ]
}
```

## Research Bundle Requirements

The research team must provide model files plus the serving logic around them:

```text
1. model files
2. model architecture code if PyTorch
3. preprocessing code/artifacts
4. postprocessing code
5. feature column order
6. sample input JSON
7. sample output JSON
8. requirements/dependencies
9. manifest.json
10. model version
```
