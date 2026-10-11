from .base import InferenceEngine, ModelSpec, InferenceResult
from typing import Any
import time


class DefaultEngine(InferenceEngine):
    def __init__(self):
        self._loaded = False
        self._spec: ModelSpec | None = None

    def load(self, spec: ModelSpec) -> None:
        self._spec = spec
        self._loaded = True

    def predict(self, inputs: Any) -> InferenceResult:
        start = time.perf_counter()
        try:
            outputs = inputs
            elapsed = (time.perf_counter() - start) * 1000
            return InferenceResult(
                outputs=outputs,
                model_name=self._spec.name if self._spec else "unknown",
                latency_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return InferenceResult(
                outputs=None,
                model_name=self._spec.name if self._spec else "unknown",
                latency_ms=elapsed,
                success=False,
                error=str(e),
            )

    def unload(self) -> None:
        self._loaded = False
        self._spec = None

    def health(self) -> bool:
        return self._loaded
