from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Position(BaseModel):
    symbol: str
    weight: float


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    as_of_date: str
    universe: list[str] = Field(default_factory=list)
    positions: list[Position] = Field(default_factory=list)
    market_data: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    model_name: str | None = None
    model_version: str | None = None


class ModelInfoResponse(BaseModel):
    model_name: str | None = None
    model_version: str | None = None
    adapter: dict[str, Any]
    feature_columns: list[str]
    manifest: dict[str, Any]

