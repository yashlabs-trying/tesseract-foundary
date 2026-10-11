from dataclasses import dataclass, field
from typing import Any, Optional
from abc import ABC, abstractmethod


@dataclass
class ModelSpec:
    name: str
    version: str
    path: str
    backend: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResult:
    outputs: Any
    model_name: str
    latency_ms: float
    success: bool = True
    error: Optional[str] = None


class InferenceEngine(ABC):
    @abstractmethod
    def load(self, spec: ModelSpec) -> None: ...

    @abstractmethod
    def predict(self, inputs: Any) -> InferenceResult: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def health(self) -> bool: ...
