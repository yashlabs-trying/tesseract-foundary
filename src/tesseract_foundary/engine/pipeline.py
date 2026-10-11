from .base import InferenceEngine, ModelSpec, InferenceResult, BackendType
from .models import DefaultEngine, create_engine
from ..utils.logger import get_logger
from typing import Any
import asyncio
import uuid
import time


class InferencePipeline:
    def __init__(self, backend: BackendType = BackendType.DEFAULT):
        self._engine: InferenceEngine = create_engine(backend)
        self._loaded = False
        self._log = get_logger("pipeline")

    def load_model(self, spec: ModelSpec) -> None:
        self._engine.load(spec)
        self._loaded = True
        self._log.info(f"Pipeline ready: {spec.name}:{spec.version}")

    def run(self, inputs: Any) -> InferenceResult:
        if not self._loaded:
            raise RuntimeError("No model loaded")
        return self._engine.predict(inputs)

    def run_batch(self, inputs: list[Any]) -> list[InferenceResult]:
        if not self._loaded:
            raise RuntimeError("No model loaded")
        return self._engine.predict_batch(inputs)

    async def run_async(self, inputs: Any) -> InferenceResult:
        return await asyncio.to_thread(self.run, inputs)

    async def run_batch_async(self, inputs: list[Any]) -> list[InferenceResult]:
        return await asyncio.to_thread(self.run_batch, inputs)

    def shutdown(self) -> None:
        self._engine.unload()
        self._loaded = False
        self._log.info("Pipeline shut down")

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._engine.health()


class BatchedPipeline:
    def __init__(self, max_batch_size: int = 32, max_wait_ms: float = 10.0):
        self._pipeline: InferencePipeline | None = None
        self._max_batch_size = max_batch_size
        self._max_wait_ms = max_wait_ms
        self._queue: list[tuple[Any, int]] = []
        self._running = False

    def load_model(self, spec: ModelSpec) -> None:
        self._pipeline = InferencePipeline(spec.backend)
        self._pipeline.load_model(spec)

    async def submit(self, inputs: Any) -> InferenceResult:
        if not self._pipeline:
            raise RuntimeError("No model loaded")
        future_id = id(inputs)
        self._queue.append((inputs, future_id))
        if len(self._queue) >= self._max_batch_size:
            return await self._flush()
        await asyncio.sleep(self._max_wait_ms / 1000)
        if (inputs, future_id) in [(q[0], q[1]) for q in self._queue]:
            return await self._flush_one(inputs)
        return InferenceResult(
            outputs=None, model_name="unknown", latency_ms=0, success=False, error="timeout"
        )

    async def _flush(self) -> InferenceResult:
        batch = self._queue[:self._max_batch_size]
        self._queue.clear()
        inputs = [b[0] for b in batch]
        results = await self._pipeline.run_batch_async(inputs)
        return results[0] if results else InferenceResult(
            outputs=None, model_name="unknown", latency_ms=0, success=False, error="empty batch"
        )

    async def _flush_one(self, inputs: Any) -> InferenceResult:
        self._queue = [q for q in self._queue if q[0] is not inputs]
        return await self._pipeline.run_async(inputs)

    def shutdown(self) -> None:
        if self._pipeline:
            self._pipeline.shutdown()
