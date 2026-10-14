# RunPod Pod Small Baseline

Run date: 2026-10-14 13:43–13:47 IST  
Pod: `m0tgp9d15cf8av`  
GPU: NVIDIA GeForce RTX 3090, 24 GiB  
Runtime: PyTorch 2.8.0+cu128, Transformers 4.48.3, BF16

## Results

| Metric | Qwen2.5 3B | Qwen2.5 7B |
| --- | ---: | ---: |
| Successful requests | 6/6 | 6/6 |
| Model load, including download | 56.12 s | 114.92 s |
| Warm-up | 1.04 s | 0.98 s |
| Median request latency | 2.737 s | 2.250 s |
| Approximate median first text | 137.6 ms | 106.7 ms |
| Median output throughput | 22.14 tok/s | 28.15 tok/s |
| Peak CUDA allocation | 5.88 GiB | 14.26 GiB |

Each model used two repetitions of three fixed prompts and generated at most 64
tokens per request. This is a small sequential inference baseline, not a
concurrency, saturation, serving-runtime, Serverless, or Cluster result.

The 7B result being faster than the 3B result is plausible for these particular
short deterministic generations because the generated texts and stopping points
differ. It must not be generalized into a claim that the 7B model is intrinsically
faster. A matched fixed-output-token benchmark with more repetitions is required
for that conclusion.

## Outcome

Both pinned models loaded and generated successfully on the 24 GiB RTX 3090.
The 7B BF16 model consumed about 14.26 GiB at peak, leaving limited headroom for
large KV caches or substantial concurrency. The next comparable RunPod Serverless
test should reuse the same model revision, prompts, output cap, and runtime family.

