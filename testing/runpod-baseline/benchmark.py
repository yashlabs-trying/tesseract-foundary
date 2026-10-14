#!/usr/bin/env python3
"""Small, reproducible Transformers inference benchmark for one CUDA GPU."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer


PROMPTS = [
    "Explain in two sentences why batching improves GPU inference throughput.",
    "A production inference API receives a sudden traffic burst. List three metrics an operator should inspect first and briefly explain why each matters.",
    "Compare cold-start latency and warm-request latency for an LLM service. Describe model download, weight loading, CUDA initialization, prefill, and decoding in a concise engineering explanation.",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gpu_snapshot() -> dict[str, Any]:
    fields = "name,uuid,memory.total,memory.used,utilization.gpu,power.draw,temperature.gpu,driver_version"
    cmd = [
        "nvidia-smi",
        f"--query-gpu={fields}",
        "--format=csv,noheader,nounits",
    ]
    values = subprocess.check_output(cmd, text=True).strip().split(", ")
    keys = fields.split(",")
    return dict(zip(keys, values, strict=True))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()

    torch.manual_seed(20261014)
    started = time.perf_counter()
    document: dict[str, Any] = {
        "schema_version": 1,
        "status": "starting",
        "started_at": utc_now(),
        "model": args.model,
        "revision": args.revision,
        "label": args.label,
        "dtype": "bfloat16",
        "repetitions": args.repetitions,
        "max_new_tokens": args.max_new_tokens,
        "environment": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "cuda_runtime": torch.version.cuda,
            "gpu_before": gpu_snapshot(),
        },
        "requests": [],
    }
    write_json(args.output, document)

    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        revision=args.revision,
        torch_dtype=torch.bfloat16,
        device_map={"": "cuda:0"},
        low_cpu_mem_usage=True,
    )
    model.eval()
    torch.cuda.synchronize()
    document["model_load_seconds"] = time.perf_counter() - load_started
    document["model_memory_gib"] = torch.cuda.memory_allocated() / 2**30
    write_json(args.output, document)

    warm_inputs = tokenizer("GPU inference warmup", return_tensors="pt").to("cuda")
    warm_started = time.perf_counter()
    with torch.inference_mode():
        model.generate(**warm_inputs, max_new_tokens=8, do_sample=False, use_cache=True)
    torch.cuda.synchronize()
    document["warmup_seconds"] = time.perf_counter() - warm_started
    write_json(args.output, document)

    for repetition in range(args.repetitions):
        for prompt_index, prompt in enumerate(PROMPTS):
            messages = [{"role": "user", "content": prompt}]
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(rendered, return_tensors="pt").to("cuda")
            input_tokens = int(inputs.input_ids.shape[-1])
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
            generation_args = dict(
                **inputs,
                streamer=streamer,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                use_cache=True,
                pad_token_id=tokenizer.eos_token_id,
            )
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            request_started = time.perf_counter()
            worker = threading.Thread(target=model.generate, kwargs=generation_args, daemon=True)
            worker.start()
            pieces: list[str] = []
            first_text_seconds: float | None = None
            for piece in streamer:
                if first_text_seconds is None and piece:
                    first_text_seconds = time.perf_counter() - request_started
                pieces.append(piece)
            worker.join()
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - request_started
            output_text = "".join(pieces)
            output_tokens = len(tokenizer.encode(output_text, add_special_tokens=False))
            record = {
                "repetition": repetition + 1,
                "prompt_index": prompt_index,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_seconds": elapsed,
                "first_text_seconds": first_text_seconds,
                "output_tokens_per_second": output_tokens / elapsed if elapsed else None,
                "peak_cuda_memory_gib": torch.cuda.max_memory_allocated() / 2**30,
                "success": bool(output_text),
            }
            document["requests"].append(record)
            write_json(args.output, document)

    successful = [r for r in document["requests"] if r["success"]]
    document["summary"] = {
        "request_count": len(document["requests"]),
        "successful_requests": len(successful),
        "median_latency_seconds": statistics.median(r["latency_seconds"] for r in successful),
        "median_first_text_seconds": statistics.median(r["first_text_seconds"] for r in successful),
        "median_output_tokens_per_second": statistics.median(
            r["output_tokens_per_second"] for r in successful
        ),
        "max_peak_cuda_memory_gib": max(r["peak_cuda_memory_gib"] for r in successful),
    }
    document["environment"]["gpu_after"] = gpu_snapshot()
    document["elapsed_seconds"] = time.perf_counter() - started
    document["completed_at"] = utc_now()
    document["status"] = "completed"
    write_json(args.output, document)
    print(json.dumps(document["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()

