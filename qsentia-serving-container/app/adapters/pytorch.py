from pathlib import Path
from typing import Any

from app.adapters.base import ModelAdapter


class PyTorchAdapter(ModelAdapter):
    def load(self, bundle_path: str) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("Install torch to use the PyTorch adapter") from exc

        model_path = self.manifest.get("artifacts", {}).get("pytorch_model")
        if not model_path:
            raise ValueError("manifest.artifacts.pytorch_model is required")

        self.torch = torch
        self.device = torch.device(self.manifest.get("device", "cpu"))
        self.model = torch.load(Path(bundle_path) / model_path, map_location=self.device)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, request: dict[str, Any]) -> dict[str, Any]:
        features = request.get("features")
        if features is None:
            raise ValueError("PyTorch adapter expects request.features")

        tensor = self.torch.as_tensor(features, dtype=self.torch.float32, device=self.device)
        with self.torch.no_grad():
            output = self.model(tensor)

        scores = output.detach().cpu().numpy()
        return {"scores": scores.tolist()}

