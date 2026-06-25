from typing import Any, Literal

from pydantic import BaseModel, Field


Environment = Literal["prod", "staging"]


class PredictRequest(BaseModel):
    modelname: str
    env: Environment = "prod"
    data: dict[str, Any] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    data: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    prod_models: list[str]
    staging_models: list[str]
