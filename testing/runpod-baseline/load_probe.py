#!/usr/bin/env python3
"""One fresh-process cached-load and first-token probe."""

from __future__ import annotations

import argparse
import json
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    process_started = time.perf_counter()
    tokenizer_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        args.model, revision=args.revision, local_files_only=True
    )
    tokenizer_seconds = time.perf_counter() - tokenizer_started

    model_started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        revision=args.revision,
        torch_dtype=torch.bfloat16,
        device_map={"": "cuda:0"},
        low_cpu_mem_usage=True,
        local_files_only=True,
    ).eval()
    torch.cuda.synchronize()
    weight_load_seconds = time.perf_counter() - model_started
    model_ready_seconds = time.perf_counter() - process_started

    inputs = tokenizer("Cached model restart probe", return_tensors="pt").to("cuda")
    first_token_started = time.perf_counter()
    with torch.inference_mode():
        model.generate(
            **inputs,
            min_new_tokens=1,
            max_new_tokens=1,
            do_sample=False,
            eos_token_id=None,
            pad_token_id=tokenizer.eos_token_id,
        )
    torch.cuda.synchronize()
    first_token_seconds = time.perf_counter() - first_token_started
    print(
        json.dumps(
            {
                "tokenizer_seconds": tokenizer_seconds,
                "weight_load_and_cuda_seconds": weight_load_seconds,
                "model_ready_seconds": model_ready_seconds,
                "first_generated_token_seconds": first_token_seconds,
                "restart_to_first_token_seconds": time.perf_counter() - process_started,
                "peak_cuda_memory_gib": torch.cuda.max_memory_allocated() / 2**30,
            }
        )
    )


if __name__ == "__main__":
    main()

