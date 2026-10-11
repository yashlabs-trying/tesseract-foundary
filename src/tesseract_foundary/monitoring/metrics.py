import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LatencyHistogram:
    buckets: list[float] = field(default_factory=lambda: [1, 5, 10, 25, 50, 100, 250, 500, 1000])
    counts: list[int] = field(default_factory=list)
    total: float = 0.0
    count: int = 0

    def __post_init__(self):
        if not self.counts:
            self.counts = [0] * len(self.buckets)

    def observe(self, value_ms: float) -> None:
        self.total += value_ms
        self.count += 1
        for i, b in enumerate(self.buckets):
            if value_ms <= b:
                self.counts[i] += 1
                break

    @property
    def avg(self) -> float:
        return self.total / self.count if self.count else 0.0

    @property
    def p50(self) -> float:
        return self._percentile(50)

    @property
    def p99(self) -> float:
        return self._percentile(99)

    def _percentile(self, p: int) -> float:
        if not self.count:
            return 0.0
        target = (self.count * p) / 100
        cumulative = 0
        for i, c in enumerate(self.counts):
            cumulative += c
            if cumulative >= target:
                return self.buckets[i]
        return self.buckets[-1] if self.buckets else 0.0


@dataclass
class RequestCounter:
    total: int = 0
    success: int = 0
    error: int = 0
    by_endpoint: dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._latency: dict[str, LatencyHistogram] = defaultdict(LatencyHistogram)
            self._counters: dict[str, RequestCounter] = defaultdict(RequestCounter)
            self._initialized = True

    def record_request(self, endpoint: str, latency_ms: float, status_code: int) -> None:
        self._latency[endpoint].observe(latency_ms)
        counter = self._counters[endpoint]
        counter.total += 1
        counter.by_endpoint[endpoint] = counter.by_endpoint.get(endpoint, 0) + 1
        if status_code < 500:
            counter.success += 1
        else:
            counter.error += 1

    def snapshot(self) -> dict:
        result = {}
        for endpoint in self._latency:
            lat = self._latency[endpoint]
            cnt = self._counters[endpoint]
            result[endpoint] = {
                "total_requests": cnt.total,
                "success": cnt.success,
                "error": cnt.error,
                "avg_latency_ms": round(lat.avg, 2),
                "p50_ms": lat.p50,
                "p99_ms": lat.p99,
            }
        return result
