from .base import InferenceEngine, ModelSpec, InferenceResult, BackendType
from ..utils.logger import get_logger
from typing import Any
import time
import uuid


class DefaultEngine(InferenceEngine):
    def __init__(self):
        self._loaded = False
        self._spec: ModelSpec | None = None
        self._log = get_logger("default-engine")

    def load(self, spec: ModelSpec) -> None:
        self._spec = spec
        self._loaded = True
        self._log.info(f"Loaded model {spec.name}:{spec.version} on {spec.device}")

    def predict(self, inputs: Any) -> InferenceResult:
        start = time.perf_counter()
        try:
            outputs = inputs
            elapsed = (time.perf_counter() - start) * 1000
            return InferenceResult(
                outputs=outputs,
                model_name=self._spec.name if self._spec else "unknown",
                latency_ms=round(elapsed, 2),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return InferenceResult(
                outputs=None,
                model_name=self._spec.name if self._spec else "unknown",
                latency_ms=round(elapsed, 2),
                success=False,
                error=str(e),
            )

    def predict_batch(self, inputs: list[Any]) -> list[InferenceResult]:
        batch_id = str(uuid.uuid4())[:8]
        results = []
        for i, inp in enumerate(inputs):
            result = self.predict(inp)
            result.batch_id = batch_id
            results.append(result)
        return results

    def unload(self) -> None:
        self._loaded = False
        self._spec = None
        self._log.info("Engine unloaded")

    def health(self) -> bool:
        return self._loaded


class ONNXEngine(InferenceEngine):
    def __init__(self):
        self._loaded = False
        self._spec: ModelSpec | None = None
        self._log = get_logger("onnx-engine")

    def load(self, spec: ModelSpec) -> None:
        self._spec = spec
        self._loaded = True
        self._log.info(f"Loaded ONNX model {spec.name}:{spec.version}")

    def predict(self, inputs: Any) -> InferenceResult:
        try:
            import numpy as np
            start = time.perf_counter()
            outputs = np.array(inputs) if not isinstance(inputs, np.ndarray) else inputs
            elapsed = (time.perf_counter() - start) * 1000
            return InferenceResult(
                outputs=outputs.tolist(),
                model_name=self._spec.name if self._spec else "unknown",
                latency_ms=round(elapsed, 2),
            )
        except ImportError:
            return InferenceResult(
                outputs=None,
                model_name=self._spec.name if self._spec else "unknown",
                latency_ms=0,
                success=False,
                error="numpy not installed",
            )

    def predict_batch(self, inputs: list[Any]) -> list[InferenceResult]:
        import numpy as np
        batch_id = str(uuid.uuid4())[:8]
        batch = np.array(inputs)
        result = self.predict(batch)
        result.batch_id = batch_id
        return [result]

    def unload(self) -> None:
        self._loaded = False
        self._spec = None

    def health(self) -> bool:
        return self._loaded


def create_engine(backend: BackendType) -> InferenceEngine:
    engines = {
        BackendType.DEFAULT: DefaultEngine,
        BackendType.ONNX: ONNXEngine,
    }
    cls = engines.get(backend, DefaultEngine)
    return cls()
