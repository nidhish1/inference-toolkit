from pathlib import Path
from typing import Any

from app.adapters.base import ModelAdapter


class LightGBMAdapter(ModelAdapter):
    def load(self, bundle_path: str) -> None:
        try:
            import lightgbm as lgb
        except ImportError as exc:
            raise RuntimeError("Install lightgbm to use the LightGBM adapter") from exc

        model_path = self.manifest.get("artifacts", {}).get("lightgbm_model")
        if not model_path:
            raise ValueError("manifest.artifacts.lightgbm_model is required")

        self.model = lgb.Booster(model_file=str(Path(bundle_path) / model_path))

    def predict(self, request: dict[str, Any]) -> dict[str, Any]:
        features = request.get("features")
        if features is None:
            raise ValueError("LightGBM adapter expects request.features")

        scores = self.model.predict(features)
        return {"scores": scores.tolist() if hasattr(scores, "tolist") else scores}

