from .routes import create_app
from ..config import AppConfig


class Server:
    def __init__(self, config: AppConfig):
        self.config = config

    def start(self) -> None:
        import uvicorn
        uvicorn.run(
            "tesseract_foundary.api.routes:create_app",
            host=self.config.server.host,
            port=self.config.server.port,
            workers=self.config.server.workers,
            factory=True,
            log_level="info",
        )
