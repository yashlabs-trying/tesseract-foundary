class Server:
    def __init__(self, config):
        self.config = config

    def start(self) -> None:
        import uvicorn
        from .routes import create_app
        app = create_app(self.config)
        uvicorn.run(
            app,
            host=self.config.server.host,
            port=self.config.server.port,
            workers=self.config.server.workers,
        )
