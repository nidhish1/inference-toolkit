from typing import Any


def format_prediction(
    raw_prediction: dict[str, Any],
    data: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "as_of_date": data.get("as_of_date"),
        "signal": raw_prediction["signal"],
        "target_position": raw_prediction["target_position"],
        "confidence": raw_prediction["confidence"],
        "model_name": config.get("model_name"),
        "model_version": config.get("model_version"),
    }

