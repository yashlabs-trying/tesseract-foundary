from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import json
import time


@dataclass
class ModelVersion:
    version: str
    path: str
    backend: str = "default"
    precision: str = "fp32"
    created_at: float = 0.0
    metrics: dict = field(default_factory=dict)
    is_active: bool = False


@dataclass
class ModelRecord:
    name: str
    versions: list[ModelVersion] = field(default_factory=list)
    created_at: float = 0.0
    description: str = ""

    @property
    def active_version(self) -> Optional[ModelVersion]:
        for v in self.versions:
            if v.is_active:
                return v
        return None

    @property
    def latest_version(self) -> Optional[ModelVersion]:
        return self.versions[-1] if self.versions else None


class ModelRegistry:
    def __init__(self, store_path: str = "./model_registry"):
        self._store = Path(store_path)
        self._store.mkdir(parents=True, exist_ok=True)
        self._models: dict[str, ModelRecord] = {}
        self._load()

    def register(self, name: str, path: str, backend: str = "default",
                 precision: str = "fp32", description: str = "") -> ModelVersion:
        record = self._models.get(name)
        if not record:
            record = ModelRecord(name=name, created_at=time.time(), description=description)
            self._models[name] = record

        ver_num = f"v{len(record.versions) + 1}"
        for v in record.versions:
            v.is_active = False

        version = ModelVersion(
            version=ver_num, path=path, backend=backend,
            precision=precision, created_at=time.time(), is_active=True,
        )
        record.versions.append(version)
        self._save()
        return version

    def get(self, name: str, version: Optional[str] = None) -> Optional[ModelRecord]:
        record = self._models.get(name)
        if not record:
            return None
        if version:
            for v in record.versions:
                if v.version == version:
                    return record
            return None
        return record

    def activate(self, name: str, version: str) -> bool:
        record = self._models.get(name)
        if not record:
            return False
        found = False
        for v in record.versions:
            v.is_active = (v.version == version)
            if v.version == version:
                found = True
        if found:
            self._save()
        return found

    def list_models(self) -> list[str]:
        return list(self._models.keys())

    def remove(self, name: str) -> bool:
        if name in self._models:
            del self._models[name]
            self._save()
            return True
        return False

    def _save(self) -> None:
        data = {}
        for name, record in self._models.items():
            data[name] = {
                "name": record.name,
                "description": record.description,
                "created_at": record.created_at,
                "versions": [
                    {
                        "version": v.version, "path": v.path,
                        "backend": v.backend, "precision": v.precision,
                        "created_at": v.created_at, "metrics": v.metrics,
                        "is_active": v.is_active,
                    }
                    for v in record.versions
                ],
            }
        with open(self._store / "registry.json", "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        reg_file = self._store / "registry.json"
        if not reg_file.exists():
            return
        with open(reg_file) as f:
            data = json.load(f)
        for name, item in data.items():
            versions = [ModelVersion(**v) for v in item["versions"]]
            self._models[name] = ModelRecord(
                name=item["name"], versions=versions,
                created_at=item["created_at"],
                description=item.get("description", ""),
            )
