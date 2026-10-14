#!/usr/bin/env python3
"""Long-context, traffic-ladder, and soak tests for raw PyTorch inference."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.streamers import BaseStreamer


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


class TimestampStreamer(BaseStreamer):
    def __init__(self) -> None:
        self.seen_prompt = False
        self.token_times: list[float] = []

    def put(self, value: torch.Tensor) -> None:
        if not self.seen_prompt:
            self.seen_prompt = True
            return
        self.token_times.append(time.perf_counter())

    def end(self) -> None:
        return


class GpuSampler:
    def __init__(self) -> None:
        self.samples: list[dict[str, float]] = []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                output = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=utilization.gpu,memory.used,power.draw",
                        "--format=csv,noheader,nounits",
                    ],
                    text=True,
                    timeout=2,
                ).strip()
                util, memory, power = [float(part) for part in output.split(", ")]
                self.samples.append(
                    {"gpu_util_percent": util, "memory_used_mib": memory, "power_watts": power}
                )
            except Exception:
                pass
            self.stop_event.wait(0.2)

    def __enter__(self) -> "GpuSampler":
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop_event.set()
        self.thread.join(timeout=3)


def exact_input(tokenizer: Any, length: int) -> dict[str, torch.Tensor]:
    seed = tokenizer.encode(
        "Benchmark production inference request with deterministic tokens. ",
        add_special_tokens=False,
    )
    ids = (seed * ((length // len(seed)) + 1))[:length]
    return {
        "input_ids": torch.tensor([ids], dtype=torch.long, device="cuda"),
        "attention_mask": torch.ones((1, length), dtype=torch.long, device="cuda"),
    }


def generate_once(
    model: Any,
    tokenizer: Any,
    input_length: int,
    output_length: int,
) -> dict[str, Any]:
    inputs = exact_input(tokenizer, input_length)
    streamer = TimestampStreamer()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    started = time.perf_counter()
    try:
        with torch.inference_mode():
            result = model.generate(
                **inputs,
                streamer=streamer,
                min_new_tokens=output_length,
                max_new_tokens=output_length,
                do_sample=False,
                eos_token_id=None,
                pad_token_id=tokenizer.eos_token_id,
                use_cache=True,
            )
        torch.cuda.synchronize()
        finished = time.perf_counter()
        output_tokens = int(result.shape[-1] - input_length)
        ttft = streamer.token_times[0] - started if streamer.token_times else None
        itls = [
            streamer.token_times[index] - streamer.token_times[index - 1]
            for index in range(1, len(streamer.token_times))
        ]
        return {
            "success": True,
            "input_tokens": input_length,
            "output_tokens": output_tokens,
            "ttft_seconds": ttft,
            "itl_seconds": itls,
            "e2e_seconds": finished - started,
            "input_tokens_per_second": input_length / ttft if ttft else None,
            "output_tokens_per_second": (
                (output_tokens - 1) / (streamer.token_times[-1] - streamer.token_times[0])
                if len(streamer.token_times) > 1
                else None
            ),
            "peak_cuda_memory_gib": torch.cuda.max_memory_allocated() / 2**30,
        }
    except torch.cuda.OutOfMemoryError as error:
        torch.cuda.empty_cache()
        return {
            "success": False,
            "error_type": "CUDA_OUT_OF_MEMORY",
            "error": str(error),
            "input_tokens": input_length,
            "target_output_tokens": output_length,
        }
    except Exception as error:
        return {
            "success": False,
            "error_type": type(error).__name__,
            "error": str(error),
            "input_tokens": input_length,
            "target_output_tokens": output_length,
        }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    good = [record for record in records if record.get("success")]
    ttft = [record["ttft_seconds"] for record in good if record.get("ttft_seconds")]
    e2e = [record["e2e_seconds"] for record in good]
    itl = [value for record in good for value in record.get("itl_seconds", [])]
    return {
        "requests": len(records),
        "successful": len(good),
        "failed": len(records) - len(good),
        "ttft_p50_seconds": percentile(ttft, 0.50),
        "ttft_p95_seconds": percentile(ttft, 0.95),
        "ttft_p99_seconds": percentile(ttft, 0.99),
        "itl_p50_seconds": percentile(itl, 0.50),
        "itl_p95_seconds": percentile(itl, 0.95),
        "e2e_p50_seconds": percentile(e2e, 0.50),
        "e2e_p95_seconds": percentile(e2e, 0.95),
        "e2e_p99_seconds": percentile(e2e, 0.99),
        "output_tokens_per_second_p50": percentile(
            [r["output_tokens_per_second"] for r in good if r.get("output_tokens_per_second")],
            0.50,
        ),
        "peak_cuda_memory_gib": max(
            (r["peak_cuda_memory_gib"] for r in good), default=None
        ),
    }


def traffic_wave(
    model: Any,
    tokenizer: Any,
    clients: int,
    mode: str,
    wall_seconds: float,
) -> dict[str, Any]:
    request_count = clients
    now = time.perf_counter()
    if mode == "steady":
        scheduled = deque(now + (index * 5.0 / max(request_count, 1)) for index in range(request_count))
    else:
        scheduled = deque(now for _ in range(request_count))
    deadline = now + wall_seconds
    records: list[dict[str, Any]] = []
    while scheduled and time.perf_counter() < deadline:
        due = scheduled[0]
        if due > time.perf_counter():
            time.sleep(min(0.01, due - time.perf_counter()))
            continue
        scheduled.popleft()
        queue_started = due
        result = generate_once(model, tokenizer, 128, 16)
        result["queue_wait_seconds"] = max(0.0, time.perf_counter() - queue_started - result.get("e2e_seconds", 0.0))
        records.append(result)
    timed_out = len(scheduled)
    elapsed = time.perf_counter() - now
    output_tokens = sum(record.get("output_tokens", 0) for record in records)
    return {
        "mode": mode,
        "offered_clients": clients,
        "completed": len(records),
        "timed_out_or_cancelled": timed_out,
        "elapsed_seconds": elapsed,
        "requests_per_second": len(records) / elapsed if elapsed else None,
        "output_tokens_per_second": output_tokens / elapsed if elapsed else None,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--soak-seconds", type=int, default=900)
    args = parser.parse_args()

    result: dict[str, Any] = {
        "schema_version": 1,
        "model": args.model,
        "revision": args.revision,
        "label": args.label,
        "precision": "bfloat16",
        "runtime": "transformers-pytorch-single-worker",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "matrix": [],
        "traffic": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, revision=args.revision, local_files_only=True
    )
    load_started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        revision=args.revision,
        torch_dtype=torch.bfloat16,
        device_map={"": "cuda:0"},
        low_cpu_mem_usage=True,
        local_files_only=True,
    ).eval()
    torch.cuda.synchronize()
    result["cached_weight_load_seconds"] = time.perf_counter() - load_started

    with GpuSampler() as sampler:
        for input_length in (128, 1024, 4096):
            for output_length in (128, 512):
                records = [
                    generate_once(model, tokenizer, input_length, output_length)
                    for _ in range(5)
                ]
                result["matrix"].append(
                    {
                        "input_tokens": input_length,
                        "target_output_tokens": output_length,
                        "records": records,
                        "summary": summarize(records),
                    }
                )
                args.output.write_text(json.dumps(result, indent=2) + "\n")

        for clients in (1, 10, 25, 50, 100, 250, 500):
            result["traffic"].append(
                traffic_wave(model, tokenizer, clients, "steady", wall_seconds=10.0)
            )
            args.output.write_text(json.dumps(result, indent=2) + "\n")

        result["traffic"].append(
            traffic_wave(model, tokenizer, 100, "sudden_10x_burst", wall_seconds=10.0)
        )

        cancellation = traffic_wave(model, tokenizer, 20, "cancellation", wall_seconds=2.0)
        cancellation["note"] = "Requests still queued after two seconds were cancelled."
        result["traffic"].append(cancellation)

        soak_started = time.perf_counter()
        soak_records: list[dict[str, Any]] = []
        while time.perf_counter() - soak_started < args.soak_seconds:
            soak_records.append(generate_once(model, tokenizer, 128, 32))
            if len(soak_records) % 25 == 0:
                result["soak_partial"] = {
                    "elapsed_seconds": time.perf_counter() - soak_started,
                    "summary": summarize(soak_records),
                }
                args.output.write_text(json.dumps(result, indent=2) + "\n")
        soak_elapsed = time.perf_counter() - soak_started
        result["soak"] = {
            "target_seconds": args.soak_seconds,
            "elapsed_seconds": soak_elapsed,
            "summary": summarize(soak_records),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in soak_records),
            "requests_per_second": len(soak_records) / soak_elapsed,
            "records": soak_records,
        }

    result["gpu_samples"] = sampler.samples
    result["gpu_summary"] = {
        "sample_count": len(sampler.samples),
        "utilization_p50_percent": percentile(
            [s["gpu_util_percent"] for s in sampler.samples], 0.50
        ),
        "utilization_p95_percent": percentile(
            [s["gpu_util_percent"] for s in sampler.samples], 0.95
        ),
        "max_memory_used_mib": max(
            (s["memory_used_mib"] for s in sampler.samples), default=None
        ),
        "power_p50_watts": percentile([s["power_watts"] for s in sampler.samples], 0.50),
    }
    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    result["status"] = "completed"
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"label": args.label, "status": "completed", "gpu": result["gpu_summary"]}, indent=2))


if __name__ == "__main__":
    main()

