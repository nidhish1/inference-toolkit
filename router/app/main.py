from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

from app.config import get_settings
from app.registry import RegistryMaps, load_registry_maps
from app.schemas import HealthResponse, PredictRequest, PredictResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.registry_maps = load_registry_maps(
        table_name=settings.model_registry_table,
        region_name=settings.aws_region,
    )
    yield


app = FastAPI(
    title="Qsentia Model Router",
    version="0.1.0",
    lifespan=lifespan,
)


def get_registry_maps(request: Request) -> RegistryMaps:
    registry_maps = getattr(request.app.state, "registry_maps", None)
    if registry_maps is None:
        raise HTTPException(status_code=503, detail="Model registry is not loaded")
    return registry_maps


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    registry_maps = get_registry_maps(request)
    return HealthResponse(
        status="ok",
        prod_models=sorted(registry_maps.prod.keys()),
        staging_models=sorted(registry_maps.staging.keys()),
    )


@app.post("/reload")
def reload_registry(request: Request) -> dict[str, Any]:
    settings = get_settings()
    request.app.state.registry_maps = load_registry_maps(
        table_name=settings.model_registry_table,
        region_name=settings.aws_region,
    )
    registry_maps = get_registry_maps(request)
    return {
        "status": "reloaded",
        "prod_count": len(registry_maps.prod),
        "staging_count": len(registry_maps.staging),
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: Request, body: PredictRequest) -> PredictResponse:
    registry_maps = get_registry_maps(request)
    route = registry_maps.get_route(body.modelname, body.env)
    if route is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active {body.env} route found for model {body.modelname}",
        )

    settings = get_settings()
    predict_url = f"{route.endpoint_url}/predict"

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(predict_url, json=body.data)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text,
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return PredictResponse(data=response.json())
