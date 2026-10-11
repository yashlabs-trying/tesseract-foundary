\"\"\"Basic inference example.\"\"\"
from tesseract_foundary.engine import ModelSpec
from tesseract_foundary.engine.pipeline import InferencePipeline

pipeline = InferencePipeline()
spec = ModelSpec(name="demo", version="1.0", path="./models/demo")

pipeline.load_model(spec)
result = pipeline.run("hello world")
print(f"Result: {result}")
pipeline.shutdown()
