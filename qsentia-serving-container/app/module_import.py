import importlib
import importlib.util
import sys
from pathlib import Path


def import_bundle_module(bundle_path: Path, module_name: str):
    code_path = bundle_path / "code"
    module_file = code_path / f"{module_name}.py"

    if module_file.exists():
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to import module from {module_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    if code_path.exists():
        sys.path.insert(0, str(code_path))

    return importlib.import_module(module_name)

