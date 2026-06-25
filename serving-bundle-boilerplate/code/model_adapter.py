from pathlib import Path
from typing import Any

from feature_builder import build_features
from postprocess import format_prediction


class ModelAdapter:
    def __init__(self, manifest: dict[str, Any]):
        self.manifest = manifest
        self.bundle_path: Path | None = None
        self.config: dict[str, Any] = {}

    def load(self, bundle_path: str) -> None:
        self.bundle_path = Path(bundle_path)
        self.config = self._load_config()

    def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        features = build_features(data=data, config=self.config)
        raw_prediction = self._predict_features(features)
        return format_prediction(raw_prediction=raw_prediction, data=data, config=self.config)

    def _predict_features(self, features: dict[str, Any]) -> dict[str, Any]:
        return {
            "signal": "hold",
            "target_position": 0.0,
            "confidence": 0.0,
            "features": features,
        }

    def _load_config(self) -> dict[str, Any]:
        return {
            "model_name": self.manifest.get("model_name"),
            "model_version": self.manifest.get("model_version"),
        }

