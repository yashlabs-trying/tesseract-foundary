#!/usr/bin/env python3
"""Attempt a short 3B + 7B co-residency and interference probe."""

from __future__ import annotations

import json
import threading
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODELS = [
    ("3b", "Qwen/Qwen2.5-3B-Instruct", "aa8e72537993ba99e69dfaafa59ed015b17504d1"),
    ("7b", "Qwen/Qwen2.5-7B-Instruct", "a09a35458c702b33eeacc393d103063234e8bc28"),
]


def main() -> None:
    output: dict[str, object] = {"status": "starting", "models": []}
    loaded = []
    try:
        for label, name, revision in MODELS:
            started = time.perf_counter()
            tokenizer = AutoTokenizer.from_pretrained(name, revision=revision, local_files_only=True)
            model = AutoModelForCausalLM.from_pretrained(
                name,
                revision=revision,
                torch_dtype=torch.bfloat16,
                device_map={"": "cuda:0"},
                low_cpu_mem_usage=True,
                local_files_only=True,
            ).eval()
            torch.cuda.synchronize()
            loaded.append((label, tokenizer, model))
            output["models"].append(
                {
                    "label": label,
                    "load_seconds": time.perf_counter() - started,
                    "cuda_memory_after_load_gib": torch.cuda.memory_allocated() / 2**30,
                }
            )

        barrier = threading.Barrier(3)
        timings: dict[str, float] = {}

        def infer(label: str, tokenizer: object, model: object) -> None:
            inputs = tokenizer("Concurrent multi-model inference probe", return_tensors="pt").to("cuda")
            barrier.wait()
            started = time.perf_counter()
            with torch.inference_mode():
                model.generate(
                    **inputs,
                    min_new_tokens=32,
                    max_new_tokens=32,
                    do_sample=False,
                    eos_token_id=None,
                    pad_token_id=tokenizer.eos_token_id,
                )
            torch.cuda.synchronize()
            timings[label] = time.perf_counter() - started

        threads = [threading.Thread(target=infer, args=item) for item in loaded]
        for thread in threads:
            thread.start()
        started = time.perf_counter()
        barrier.wait()
        for thread in threads:
            thread.join()
        output.update(
            {
                "status": "completed",
                "concurrent_e2e_seconds": time.perf_counter() - started,
                "per_model_seconds": timings,
                "peak_cuda_memory_gib": torch.cuda.max_memory_allocated() / 2**30,
            }
        )
    except torch.cuda.OutOfMemoryError as error:
        output.update({"status": "oom", "error": str(error)})
    except Exception as error:
        output.update({"status": "failed", "error_type": type(error).__name__, "error": str(error)})
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

