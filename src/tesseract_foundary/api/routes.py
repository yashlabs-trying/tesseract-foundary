from fastapi import FastAPI
from ..config import AppConfig
from .. import __version__


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(
        title="Tesseract Foundry",
        version=__version__,
        description="AI inference API by Foundry AI",
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__}

    @app.get("/v1/models")
    def list_models():
        return {"models": []}

    @app.post("/v1/predict")
    def predict():
        return {"prediction": None}

    return app
