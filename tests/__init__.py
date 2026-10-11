from ..engine import InferenceEngine, ModelSpec, InferenceResult
from ..engine.models import DefaultEngine

def test_default_engine_load():
    engine = DefaultEngine()
    spec = ModelSpec(name="test-model", version="1.0", path="/tmp/test")
    engine.load(spec)
    assert engine.health() is True
    engine.unload()
    assert engine.health() is False
