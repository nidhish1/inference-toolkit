from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from app.config import get_settings
from app.loader import ModelBundle, load_model_bundle
from app.schemas import HealthResponse, ModelInfoResponse, PredictionRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.model_bundle = load_model_bundle(settings.model_bundle_path)
    yield


app = FastAPI(
    title="Qsentia Serving Container",
    version="0.1.0",
    lifespan=lifespan,
)


def get_loaded_bundle(request: Request) -> ModelBundle:
    model_bundle = getattr(request.app.state, "model_bundle", None)
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Model bundle is not loaded")
    return model_bundle


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    model_bundle = get_loaded_bundle(request)
    return HealthResponse(
        status="ok",
        model_name=model_bundle.manifest.get("model_name"),
        model_version=model_bundle.manifest.get("model_version"),
    )


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info(request: Request) -> ModelInfoResponse:
    model_bundle = get_loaded_bundle(request)
    manifest = model_bundle.manifest
    return ModelInfoResponse(
        model_name=manifest.get("model_name"),
        model_version=manifest.get("model_version"),
        adapter=manifest.get("adapter", {}),
        feature_columns=manifest.get("feature_columns", []),
        manifest=manifest,
    )


@app.post("/predict")
def predict(request: Request, payload: PredictionRequest) -> dict[str, Any]:
    model_bundle = get_loaded_bundle(request)
    try:
        return model_bundle.adapter.predict(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

