# RunPod Small Baseline

Budget-constrained, single-GPU baseline for a RunPod Pod. The suite records the
environment, model download/load time, warm-up time, latency, approximate TTFT,
generated tokens per second, and peak CUDA memory for pinned 3B and 7B models.

## Scope

- One GPU Pod only
- Qwen2.5-3B-Instruct and Qwen2.5-7B-Instruct
- BF16 inference with plain Hugging Face Transformers/PyTorch
- Two repetitions over three fixed prompts
- Hard outer timeout of 50 minutes

This is a smoke/performance baseline, not a saturation, Serverless, Cluster, or
production-capacity benchmark.

## Run

```bash
cd /workspace/runpod-baseline
bash run_pod_baseline.sh
```

Artifacts are placed under `results/<UTC timestamp>/`. The manifest and each
request are written before moving to the next experiment, so partial runs remain
usable if the time limit is reached.

## Models

The model revisions are intentionally explicit. Update them only as a separate
experiment so results remain attributable.

- `Qwen/Qwen2.5-3B-Instruct` at `aa8e72537993ba99e69dfaafa59ed015b17504d1`
- `Qwen/Qwen2.5-7B-Instruct` at `a09a35458c702b33eeacc393d103063234e8bc28`

