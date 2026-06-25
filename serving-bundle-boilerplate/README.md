# Serving Bundle Boilerplate

Template for packaging a model so the Qsentia serving container can load it.

The serving container expects a bundle with:

```text
manifest.json
artifacts/
code/
schemas/
config/
examples/
```

## Structure

```text
serving-bundle-boilerplate/
├── manifest.json
├── artifacts/
│   └── .gitkeep
├── code/
│   ├── model_adapter.py
│   ├── feature_builder.py
│   └── postprocess.py
├── schemas/
│   ├── input_schema.json
│   └── output_schema.json
├── config/
│   └── config.json
└── examples/
    ├── sample_request.json
    └── sample_response.json
```

## Adapter Contract

```python
class ModelAdapter:
    def load(self, bundle_path: str) -> None:
        ...

    def predict(self, data: dict) -> dict:
        ...
```

## How To Use

Copy this folder for a model version:

```text
models/{model_name}/versions/{model_version}/
```

Then add:

```text
1. trained model artifacts into artifacts/
2. runtime loading logic into code/model_adapter.py
3. feature generation into code/feature_builder.py
4. output formatting into code/postprocess.py
5. exact input/output schemas
6. sample request and response
```

Upload `manifest.json` last so the S3/EventBridge registration pipeline only
runs after the bundle is fully uploaded.

## Docker

This boilerplate includes a Dockerfile for the reusable serving image.

Build from repo root:

```bash
docker build \
  -f serving-bundle-boilerplate/Dockerfile \
  -t qsentia-serving:latest \
  .
```

Run with this bundle mounted:

```bash
docker run --rm \
  -p 8080:8080 \
  -e MODEL_BUNDLE_PATH=/models/model_bundle \
  -v "$PWD/serving-bundle-boilerplate:/models/model_bundle:ro" \
  qsentia-serving:latest
```

Or from this folder:

```bash
docker compose up --build
```

The Docker image is reusable. The model bundle is mounted at runtime.
