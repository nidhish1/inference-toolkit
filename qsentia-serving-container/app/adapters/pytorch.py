from pathlib import Path
from typing import Any

from app.adapters.base import ModelAdapter
from app.module_import import import_bundle_module


class PyTorchAdapter(ModelAdapter):
    def load(self, bundle_path: str) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("Install torch to use the PyTorch adapter") from exc

        artifacts = self.manifest.get("artifacts", {})
        model_path = artifacts.get("pytorch_state_dict") or artifacts.get("pytorch_model")
        if not model_path:
            raise ValueError("manifest.artifacts.pytorch_state_dict or pytorch_model is required")

        self.torch = torch
        self.device = torch.device(self.manifest.get("device", "cpu"))
        self.model = self._build_model(bundle_path, Path(bundle_path) / model_path)
        self.model.to(self.device)
        self.model.eval()

    def _build_model(self, bundle_path: str, model_path: Path):
        model_config = self.manifest.get("model", {})
        if not model_config:
            return self.torch.load(model_path, map_location=self.device)

        module_name = model_config["module"]
        class_name = model_config["class"]
        kwargs = model_config.get("kwargs", {})
        module = import_bundle_module(Path(bundle_path), module_name)
        model_class = getattr(module, class_name)
        model = model_class(**kwargs)
        state_dict = self.torch.load(model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        return model

    def predict(self, request: dict[str, Any]) -> dict[str, Any]:
        features = request.get("features")
        if features is None:
            raise ValueError("PyTorch adapter expects request.features")

        tensor = self.torch.as_tensor(features, dtype=self.torch.float32, device=self.device)
        with self.torch.no_grad():
            output = self.model(tensor)

        scores = output.detach().cpu().numpy()
        return {"scores": scores.tolist()}
