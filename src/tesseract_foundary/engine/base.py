from dataclasses import dataclass, field
from typing import Any, Optional
from abc import ABC, abstractmethod
from enum import Enum


class BackendType(str, Enum):
    DEFAULT = "default"
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    OPENVINO = "openvino"


@dataclass
class ModelSpec:
    name: str
    version: str
    path: str
    backend: BackendType = BackendType.DEFAULT
    metadata: dict[str, Any] = field(default_factory=dict)
    device: str = "cpu"
    batch_size: int = 1
    precision: str = "fp32"


@dataclass
class InferenceResult:
    outputs: Any
    model_name: str
    latency_ms: float
    success: bool = True
    error: Optional[str] = None
    batch_id: Optional[str] = None


class InferenceEngine(ABC):
    @abstractmethod
    def load(self, spec: ModelSpec) -> None: ...

    @abstractmethod
    def predict(self, inputs: Any) -> InferenceResult: ...

    @abstractmethod
    def predict_batch(self, inputs: list[Any]) -> list[InferenceResult]: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def health(self) -> bool: ...
