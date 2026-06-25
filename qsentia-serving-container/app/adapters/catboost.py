from pathlib import Path
from typing import Any

from app.adapters.base import ModelAdapter


class CatBoostAdapter(ModelAdapter):
    def load(self, bundle_path: str) -> None:
        try:
            from catboost import CatBoostRanker
        except ImportError as exc:
            raise RuntimeError("Install catboost to use the CatBoost adapter") from exc

        model_path = self.manifest.get("artifacts", {}).get("catboost_model")
        if not model_path:
            raise ValueError("manifest.artifacts.catboost_model is required")

        self.model = CatBoostRanker()
        self.model.load_model(str(Path(bundle_path) / model_path))

    def predict(self, request: dict[str, Any]) -> dict[str, Any]:
        features = request.get("features")
        if features is None:
            raise ValueError("CatBoost adapter expects request.features")

        scores = self.model.predict(features)
        return {"scores": scores.tolist() if hasattr(scores, "tolist") else scores}

