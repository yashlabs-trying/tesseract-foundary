#!/usr/bin/env python3
"""Budget-bounded RunPod Serverless latency probe using only the Python stdlib."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}


def request_json(method: str, url: str, key: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def run_job(endpoint: str, key: str, input_tokens: int, output_tokens: int) -> dict:
    prompt = "Benchmark input:" + " token" * max(1, input_tokens - 4)
    payload = {
        "input": {
            "prompt": prompt,
            "sampling_params": {
                "max_tokens": output_tokens,
                "min_tokens": output_tokens,
                "temperature": 0.0,
                "ignore_eos": True,
            },
        }
    }
    started = time.perf_counter()
    submitted = request_json("POST", f"https://api.runpod.ai/v2/{endpoint}/run", key, payload)
    job_id = submitted["id"]
    deadline = time.monotonic() + 180
    while True:
        status = request_json("GET", f"https://api.runpod.ai/v2/{endpoint}/status/{job_id}", key)
        if status.get("status") in TERMINAL:
            break
        if time.monotonic() >= deadline:
            request_json("POST", f"https://api.runpod.ai/v2/{endpoint}/cancel/{job_id}", key)
            status = {"id": job_id, "status": "CANCELLED_BY_PROBE_TIMEOUT"}
            break
        time.sleep(0.5)
    elapsed = time.perf_counter() - started
    output = status.get("output") or []
    first = output[0] if output and isinstance(output, list) else output
    usage = first.get("usage", {}) if isinstance(first, dict) else {}
    return {
        "requested_input_tokens": input_tokens,
        "requested_output_tokens": output_tokens,
        "client_e2e_seconds": elapsed,
        "job": status,
        "reported_prompt_tokens": usage.get("prompt_tokens"),
        "reported_completion_tokens": usage.get("completion_tokens"),
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * fraction + 0.999999)))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        raise SystemExit("RUNPOD_API_KEY is required")

    result = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint_id": args.endpoint,
        "repeats": args.repeats,
        "tests": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        for input_tokens in (128, 1024, 4096):
            for output_tokens in (128, 512):
                for repetition in range(1, args.repeats + 1):
                    record = run_job(args.endpoint, key, input_tokens, output_tokens)
                    record["repetition"] = repetition
                    result["tests"].append(record)
                    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
                    print(
                        json.dumps(
                            {
                                "input": input_tokens,
                                "output": output_tokens,
                                "repetition": repetition,
                                "status": record["job"].get("status"),
                                "e2e_seconds": round(record["client_e2e_seconds"], 3),
                            }
                        ),
                        flush=True,
                    )
    finally:
        result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        completed = [x for x in result["tests"] if x["job"].get("status") == "COMPLETED"]
        latencies = [x["client_e2e_seconds"] for x in completed]
        result["summary"] = {
            "attempted": len(result["tests"]),
            "completed": len(completed),
            "failed": len(result["tests"]) - len(completed),
            "client_e2e_p50_seconds": statistics.median(latencies) if latencies else None,
            "client_e2e_p95_seconds": percentile(latencies, 0.95),
            "client_e2e_p99_seconds": percentile(latencies, 0.99),
        }
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
