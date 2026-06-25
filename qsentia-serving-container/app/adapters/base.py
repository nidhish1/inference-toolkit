from abc import ABC, abstractmethod
from typing import Any


class ModelAdapter(ABC):
    def __init__(self, manifest: dict[str, Any]):
        self.manifest = manifest

    @abstractmethod
    def load(self, bundle_path: str) -> None:
        ...

    @abstractmethod
    def predict(self, request: dict[str, Any]) -> dict[str, Any]:
        ...

