import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


class LoadedBundle:
    def __init__(self, bundle_path: Path, manifest: dict[str, Any], adapter: Any):
        self.bundle_path = bundle_path
        self.manifest = manifest
        self.adapter = adapter


def load_bundle(bundle_path: Path) -> LoadedBundle:
    manifest = load_manifest(bundle_path)
    adapter = load_adapter(bundle_path=bundle_path, manifest=manifest)
    adapter.load(str(bundle_path))
    return LoadedBundle(bundle_path=bundle_path, manifest=manifest, adapter=adapter)


def load_manifest(bundle_path: Path) -> dict[str, Any]:
    manifest_path = bundle_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found at {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def load_adapter(bundle_path: Path, manifest: dict[str, Any]) -> Any:
    adapter_config = manifest.get("adapter", {})
    module_name = adapter_config.get("module", "model_adapter")
    class_name = adapter_config.get("class", "ModelAdapter")
    code_path = bundle_path / "code"
    module_path = code_path / f"{module_name}.py"

    if not module_path.exists():
        raise FileNotFoundError(f"adapter module not found at {module_path}")

    sys.path.insert(0, str(code_path))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load adapter module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    adapter_class = getattr(module, class_name)
    return adapter_class(manifest)

