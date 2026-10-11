from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class PredictRequest(BaseModel):
    inputs: Any
    model: str = "default"
    version: Optional[str] = None
    parameters: dict[str, Any] = {}


class PredictResponse(BaseModel):
    outputs: Any
    model: str
    version: str
    latency_ms: float
    success: bool


class ModelInfo(BaseModel):
    name: str
    version: str
    backend: str
    device: str
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
