import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from app.adapters.base import ModelAdapter
from app.adapters.catboost import CatBoostAdapter
from app.adapters.lightgbm import LightGBMAdapter
from app.adapters.pytorch import PyTorchAdapter


BUILT_IN_ADAPTERS: dict[str, type[ModelAdapter]] = {
    "catboost": CatBoostAdapter,
    "lightgbm": LightGBMAdapter,
    "pytorch": PyTorchAdapter,
}


class ModelBundle:
    def __init__(self, bundle_path: Path, manifest: dict[str, Any], adapter: ModelAdapter):
        self.bundle_path = bundle_path
        self.manifest = manifest
        self.adapter = adapter


def load_model_bundle(bundle_path: Path) -> ModelBundle:
    manifest = load_manifest(bundle_path)
    adapter = build_adapter(bundle_path, manifest)
    adapter.load(str(bundle_path))
    return ModelBundle(bundle_path=bundle_path, manifest=manifest, adapter=adapter)


def load_manifest(bundle_path: Path) -> dict[str, Any]:
    manifest_path = bundle_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Model manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def build_adapter(bundle_path: Path, manifest: dict[str, Any]) -> ModelAdapter:
    adapter_config = manifest.get("adapter", {})
    adapter_type = adapter_config.get("type", "custom")

    if adapter_type in BUILT_IN_ADAPTERS:
        return BUILT_IN_ADAPTERS[adapter_type](manifest=manifest)

    if adapter_type != "custom":
        raise ValueError(f"Unsupported adapter type: {adapter_type}")

    module_name = adapter_config.get("module", "model_adapter")
    class_name = adapter_config.get("class", "ModelAdapter")
    module = import_custom_adapter_module(bundle_path, module_name)
    adapter_class = getattr(module, class_name)
    return adapter_class(manifest=manifest)


def import_custom_adapter_module(bundle_path: Path, module_name: str):
    code_path = bundle_path / "code"
    module_file = code_path / f"{module_name}.py"

    if module_file.exists():
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to import adapter module from {module_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    if code_path.exists():
        sys.path.insert(0, str(code_path))

    return importlib.import_module(module_name)

