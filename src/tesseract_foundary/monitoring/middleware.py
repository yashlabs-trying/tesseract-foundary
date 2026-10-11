import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .metrics import MetricsCollector


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        collector = MetricsCollector()
        collector.record_request(request.url.path, elapsed, response.status_code)
        response.headers["X-Request-Time-Ms"] = str(round(elapsed, 2))
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[{request.method}] {request.url.path} -> {response.status_code} ({elapsed:.1f}ms)")
        return response
