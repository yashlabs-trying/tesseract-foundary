from pydantic import BaseModel
from typing import Optional
import os
import secrets


class AuthConfig(BaseModel):
    enabled: bool = False
    api_key: Optional[str] = None


class APIKeyAuth:
    def __init__(self, config: AuthConfig):
        self._config = config
        if config.enabled and not config.api_key:
            self._config.api_key = os.environ.get("TESSERACT_API_KEY", secrets.token_hex(32))

    def verify(self, api_key: str) -> bool:
        if not self._config.enabled:
            return True
        return secrets.compare_digest(api_key, self._config.api_key or "")
