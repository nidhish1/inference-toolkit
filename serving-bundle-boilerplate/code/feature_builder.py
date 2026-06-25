from typing import Any


def build_features(data: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "as_of_date": data.get("as_of_date"),
        "ohlcv_rows": len(data.get("ohlcv", [])),
        "text_rows": len(data.get("texts", [])),
    }

