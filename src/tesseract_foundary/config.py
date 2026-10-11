from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import yaml


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1
    max_batch_size: int = 32
    timeout_seconds: int = 30


class AppConfig(BaseModel):
    name: str = "tesseract-foundary"
    version: str = "2.0.0"
    debug: bool = False
    logging: LoggingConfig = LoggingConfig()
    server: ServerConfig = ServerConfig()
    model_dir: str = "./models"
    model_name: str = "default"
    cache_dir: str = "./cache"
    backend: str = "default"
    device: str = "cpu"
    api_key_enabled: bool = False


def load_config(path: str = "config.yaml") -> AppConfig:
    p = Path(path)
    if p.exists():
        with open(p) as f:
            data = yaml.safe_load(f)
        if data:
            return AppConfig(**data)
    return AppConfig()
