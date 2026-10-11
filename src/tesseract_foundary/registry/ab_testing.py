from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class ABTestConfig:
    model_a: str
    model_b: str
    traffic_split_a: float = 0.5
    name: str = "ab_test"


class ABTestRouter:
    def __init__(self, config: ABTestConfig):
        self.config = config
        self._results_a: list[dict] = []
        self._results_b: list[dict] = []

    def select_model(self, trace_id: Optional[str] = None) -> str:
        if trace_id:
            choice = hash(trace_id) % 100 / 100.0
        else:
            choice = random.random()
        return self.config.model_a if choice < self.config.traffic_split_a else self.config.model_b

    def record_result(self, model: str, latency_ms: float, success: bool, trace_id: Optional[str] = None) -> None:
        entry = {"latency_ms": latency_ms, "success": success, "trace_id": trace_id}
        if model == self.config.model_a:
            self._results_a.append(entry)
        else:
            self._results_b.append(entry)

    def stats(self) -> dict:
        def _summarize(results: list[dict]) -> dict:
            if not results:
                return {"count": 0, "avg_latency": 0, "success_rate": 0}
            latencies = [r["latency_ms"] for r in results]
            successes = sum(1 for r in results if r["success"])
            return {
                "count": len(results),
                "avg_latency": sum(latencies) / len(latencies),
                "success_rate": successes / len(results),
            }
        return {
            "model_a": _summarize(self._results_a),
            "model_b": _summarize(self._results_b),
            "config": {
                "model_a": self.config.model_a,
                "model_b": self.config.model_b,
                "traffic_split_a": self.config.traffic_split_a,
            },
        }

    def reset(self) -> None:
        self._results_a.clear()
        self._results_b.clear()
