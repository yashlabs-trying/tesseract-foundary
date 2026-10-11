from .base import InferenceEngine, ModelSpec, InferenceResult
from .models import DefaultEngine
from typing import Any
import time


class InferencePipeline:
    def __init__(self):
        self._engine: InferenceEngine = DefaultEngine()
        self._loaded = False

    def load_model(self, spec: ModelSpec) -> None:
        self._engine.load(spec)
        self._loaded = True

    def run(self, inputs: Any) -> InferenceResult:
        return self._engine.predict(inputs)

    def shutdown(self) -> None:
        self._engine.unload()
        self._loaded = False

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._engine.health()
