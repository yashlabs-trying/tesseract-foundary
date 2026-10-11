from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import time

from ..config import AppConfig
from .. import __version__
from ..engine import InferencePipeline, ModelSpec, BackendType
from .schemas import PredictRequest, PredictResponse, ModelInfo, HealthResponse
from .auth import APIKeyAuth, AuthConfig


_start_time = time.time()
_pipeline: InferencePipeline | None = None


def get_auth_header(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    return x_api_key


def create_app(config: AppConfig) -> FastAPI:
    global _pipeline

    auth = APIKeyAuth(AuthConfig(enabled=config.api_key_enabled))

    app = FastAPI(
        title="Tesseract Foundry",
        version=__version__,
        description="AI inference API by Foundry AI",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health(api_key: Optional[str] = Depends(get_auth_header)):
        if api_key and not auth.verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")
        return HealthResponse(
            status="ok",
            version=__version__,
            uptime=time.time() - _start_time,
        )

    @app.get("/v1/models", response_model=list[ModelInfo])
    def list_models(api_key: Optional[str] = Depends(get_auth_header)):
        if api_key and not auth.verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")
        return [
            ModelInfo(
                name=config.model_name or "default",
                version=__version__,
                backend=config.backend or "default",
                device=config.device or "cpu",
                status="ready" if (_pipeline and _pipeline.is_ready) else "not_loaded",
            )
        ]

    @app.post("/v1/predict", response_model=PredictResponse)
    def predict(req: PredictRequest, api_key: Optional[str] = Depends(get_auth_header)):
        if api_key and not auth.verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")
        if not _pipeline or not _pipeline.is_ready:
            raise HTTPException(status_code=503, detail="Model not loaded")

        start = time.perf_counter()
        result = _pipeline.run(req.inputs)
        elapsed = (time.perf_counter() - start) * 1000

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return PredictResponse(
            outputs=result.outputs,
            model=result.model_name,
            version=config.version,
            latency_ms=round(elapsed, 2),
            success=True,
        )

    @app.post("/v1/models/load")
    def load_model(api_key: Optional[str] = Depends(get_auth_header)):
        if api_key and not auth.verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")
        global _pipeline
        _pipeline = InferencePipeline(
            backend=BackendType(config.backend or BackendType.DEFAULT)
        )
        spec = ModelSpec(
            name=config.model_name or "default",
            version=config.version,
            path=config.model_dir,
            device=config.device or "cpu",
        )
        _pipeline.load_model(spec)
        return {"status": "loaded", "model": spec.name}

    @app.post("/v1/models/unload")
    def unload_model(api_key: Optional[str] = Depends(get_auth_header)):
        if api_key and not auth.verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")
        global _pipeline
        if _pipeline:
            _pipeline.shutdown()
            _pipeline = None
        return {"status": "unloaded"}

    return app
