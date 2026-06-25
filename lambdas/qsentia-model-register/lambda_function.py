import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote_plus

import boto3


MODEL_REGISTRY_TABLE = os.getenv("MODEL_REGISTRY_TABLE", "qsentia-model-registry")
DEFAULT_ENV = os.getenv("DEFAULT_ENV", "staging")
DEFAULT_STATUS = os.getenv("DEFAULT_STATUS", "inactive")
TRIGGER_FILENAMES = {"manifest.json", "metadata.json"}

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    records = extract_s3_records(event)
    registered = []
    skipped = []

    for record in records:
        bucket = record["bucket"]
        key = record["key"]

        try:
            registration = register_model_bundle(bucket=bucket, key=key)
            registered.append(registration)
        except ValueError as exc:
            skipped.append({"bucket": bucket, "key": key, "reason": str(exc)})

    return {
        "registered_count": len(registered),
        "skipped_count": len(skipped),
        "registered": registered,
        "skipped": skipped,
    }


def register_model_bundle(bucket: str, key: str) -> dict[str, Any]:
    parsed = parse_model_key(key)
    manifest = read_json_object(bucket=bucket, key=key)
    artifact_uri = f"s3://{bucket}/{parsed['artifact_prefix']}"

    item = {
        "model_name": manifest.get("model_name", parsed["model_name"]),
        "model_version": manifest.get("model_version", parsed["model_version"]),
        "env": manifest.get("env", DEFAULT_ENV),
        "status": manifest.get("status", DEFAULT_STATUS),
        "artifact_uri": manifest.get("artifact_uri", artifact_uri),
        "endpoint_url": manifest.get("endpoint_url", ""),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    optional_fields = [
        "framework",
        "description",
        "container_image",
        "adapter_type",
        "owner",
    ]
    for field in optional_fields:
        if field in manifest:
            item[field] = manifest[field]

    table = dynamodb.Table(MODEL_REGISTRY_TABLE)
    table.put_item(Item=item)

    return {
        "model_name": item["model_name"],
        "model_version": item["model_version"],
        "env": item["env"],
        "status": item["status"],
        "artifact_uri": item["artifact_uri"],
    }


def parse_model_key(key: str) -> dict[str, str]:
    parts = key.split("/")

    if len(parts) < 5:
        raise ValueError("key does not match models/{model_name}/versions/{model_version}/{file}")

    if parts[0] != "models" or parts[2] != "versions":
        raise ValueError("key must start with models/{model_name}/versions/{model_version}/")

    filename = parts[-1]
    if filename not in TRIGGER_FILENAMES:
        raise ValueError(f"key must end with one of {sorted(TRIGGER_FILENAMES)}")

    model_name = parts[1]
    model_version = parts[3]
    artifact_prefix = "/".join(parts[:4]) + "/"

    return {
        "model_name": model_name,
        "model_version": model_version,
        "artifact_prefix": artifact_prefix,
    }


def read_json_object(bucket: str, key: str) -> dict[str, Any]:
    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    return json.loads(body)


def extract_s3_records(event: dict[str, Any]) -> list[dict[str, str]]:
    if event.get("source") == "aws.s3" and "detail" in event:
        return [
            {
                "bucket": event["detail"]["bucket"]["name"],
                "key": unquote_plus(event["detail"]["object"]["key"]),
            }
        ]

    records = []
    for record in event.get("Records", []):
        if "s3" not in record:
            continue
        records.append(
            {
                "bucket": record["s3"]["bucket"]["name"],
                "key": unquote_plus(record["s3"]["object"]["key"]),
            }
        )
    return records


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

