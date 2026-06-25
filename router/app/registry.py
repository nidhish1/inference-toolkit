from dataclasses import dataclass
from typing import Literal

import boto3
from boto3.dynamodb.types import TypeDeserializer


Environment = Literal["prod", "staging"]


@dataclass(frozen=True)
class ModelRoute:
    model_name: str
    model_version: str
    env: Environment
    endpoint_url: str


@dataclass(frozen=True)
class RegistryMaps:
    prod: dict[str, ModelRoute]
    staging: dict[str, ModelRoute]

    def get_route(self, model_name: str, env: Environment) -> ModelRoute | None:
        routes = self.prod if env == "prod" else self.staging
        return routes.get(model_name)


def load_registry_maps(table_name: str, region_name: str) -> RegistryMaps:
    client = boto3.client("dynamodb", region_name=region_name)
    paginator = client.get_paginator("scan")
    deserializer = TypeDeserializer()

    prod: dict[str, ModelRoute] = {}
    staging: dict[str, ModelRoute] = {}

    for page in paginator.paginate(TableName=table_name):
        for raw_item in page.get("Items", []):
            item = {
                key: deserializer.deserialize(value)
                for key, value in raw_item.items()
            }

            if item.get("status") != "active":
                continue

            env = item.get("env") or item.get("stage")
            if env not in ("prod", "staging"):
                continue

            route = ModelRoute(
                model_name=item["model_name"],
                model_version=item["model_version"],
                env=env,
                endpoint_url=item["endpoint_url"].rstrip("/"),
            )

            if env == "prod":
                prod[route.model_name] = route
            else:
                staging[route.model_name] = route

    return RegistryMaps(prod=prod, staging=staging)
