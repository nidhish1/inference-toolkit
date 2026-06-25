import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from app.loader import LoadedBundle, load_bundle


MODEL_BUNDLE_PATH = Path(os.getenv("MODEL_BUNDLE_PATH", "/models/model_bundle"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bundle = load_bundle(MODEL_BUNDLE_PATH)
    yield


app = FastAPI(
    title="Qsentia Serving Runtime",
    version="0.1.0",
    lifespan=lifespan,
)


def get_bundle(request: Request) -> LoadedBundle:
    bundle = getattr(request.app.state, "bundle", None)
    if bundle is None:
        raise HTTPException(status_code=503, detail="model bundle is not loaded")
    return bundle


@app.get("/health")
def health(request: Request) -> dict[str, Any]:
    bundle = get_bundle(request)
    return {
        "status": "ok",
        "model_name": bundle.manifest.get("model_name"),
        "model_version": bundle.manifest.get("model_version"),
    }


@app.get("/model-info")
def model_info(request: Request) -> dict[str, Any]:
    return get_bundle(request).manifest


@app.post("/predict")
def predict(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    bundle = get_bundle(request)
    return bundle.adapter.predict(data)

