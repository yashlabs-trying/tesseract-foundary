# RunPod GPU Pod — Qwen2.5 3B and 7B Baseline

Test date: 2026-10-14 UTC

Pod region: EU-CZ-1

Result directory: [`results/20261014T083122Z-extended`](results/20261014T083122Z-extended)

Earlier cold-load run: [`results/20261014T081346Z/REPORT.md`](results/20261014T081346Z/REPORT.md)

## Executive result

Both BF16 models ran successfully on one RTX 3090. The 7B model was faster than the 3B model in this exact Transformers/PyTorch implementation, but used 2.37× the peak VRAM. All 60 matrix requests succeeded without an OOM. Both models remained reliable in the completed soak interval, but the deliberately unbatched single-worker service saturated between 10 and 25 offered clients and timed out most queued requests at extreme offered concurrency.

These are Pod/runtime baseline results, not claims about RunPod Serverless or Clusters. Values are labelled **MEASURED**, **ESTIMATED**, or **NOT TESTED**. No value has been inferred and presented as measured.

## Test system

| Item | Result | Status |
|---|---:|---|
| GPU | 1× NVIDIA GeForce RTX 3090 | MEASURED |
| VRAM | 24,576 MiB | MEASURED |
| RunPod allocation | 32 vCPU, 125 GB RAM | MEASURED from Pod environment |
| Driver / CUDA / PyTorch | 580.159.03 / 12.8 / 2.8.0+cu128 | MEASURED |
| Transformers | 4.48.3 | MEASURED |
| Precision | BF16 | MEASURED |
| Disk | 30 GB container disk; about 9.9 GB free before the extended run | MEASURED |
| Region | EU-CZ-1 | MEASURED |
| Runtime | Hugging Face Transformers eager generation on PyTorch; one inference worker, no continuous batching | MEASURED |
| 3B model | `Qwen/Qwen2.5-3B-Instruct`, cached snapshot used by the harness | MEASURED; exact snapshot files retained in cache, revision was not separately printed |
| 7B model | `Qwen/Qwen2.5-7B-Instruct`, cached snapshot used by the harness | MEASURED; exact snapshot files retained in cache, revision was not separately printed |
| Catalog GPU price | $0.22/h Community; $0.50/h Secure for RTX 3090 | ESTIMATED from live public catalog; this Pod's tier/rate could not be verified |
| General network throughput | — | NOT TESTED |

The host exposed more CPUs and RAM than the allocation, so the allocation values above are used for reproducibility. Raw environment captures are in the result directory.

## Startup and loading

| Measurement | 3B | 7B | Status |
|---|---:|---:|---|
| Pod provision and boot | — | — | NOT TESTED; no creation timestamp instrumentation |
| Container startup | — | — | NOT TESTED; no container hook instrumentation |
| First cold download + load + CUDA | 56.12 s | 114.92 s | MEASURED combined in the earlier run; cannot be safely split afterward |
| Separate cold model download | — | — | NOT TESTED |
| Cached in-process load in extended phase | 3.61 s | 8.57 s | MEASURED |
| Cached fresh-process model-ready, median of 5 | 2.75 s | 7.24 s | MEASURED |
| Cached fresh-process restart-to-first-token, median | 3.46 s | 7.96 s | MEASURED |
| Cached restart-to-first-token range | 3.39–5.45 s | 4.96–9.02 s | MEASURED, five repetitions |
| Warm TTFT, 128-token input, median | 41.8 ms | 36.7 ms | MEASURED |

Each fresh-process restart cleared the Python process and CUDA context. Hugging Face weights remained cached on disk. The original cold run used an empty model cache, but recorded download, deserialization, loading and CUDA initialization as one interval. Therefore a separate cold-download number is intentionally not reported.

## Final comparison

| Metric | 3B | 7B | Status / interpretation |
|---|---:|---:|---|
| Cold start | 56.12 s combined | 114.92 s combined | MEASURED, download + load + CUDA |
| Warm TTFT P50, 128 input | 41.8 ms | 36.7 ms | MEASURED |
| Worst matrix E2E P95 | 23.19 s | 19.13 s | MEASURED at 4,096 input / 512 output |
| Sustained throughput | 0.750 req/s; 24.0 output tok/s | 1.027 req/s; 32.9 output tok/s | MEASURED; 3B full 15 min, 7B partial 10.1 min |
| Highest offered concurrency with zero queue timeouts | 10 | 10 | MEASURED for this harness; not a universal SLO |
| Peak single-model VRAM | 6.32 GiB | 15.00 GiB | MEASURED |
| GPU utilization | P50 33%, P95 43.75% | — | 3B MEASURED during full soak; 7B distribution NOT TESTED because cutoff interrupted final sampler aggregation |
| Matrix inference error rate | 0/30 (0%) | 0/30 (0%) | MEASURED |
| Soak inference error rate | 0/676 (0%) | 0/625 (0%) | MEASURED; 7B interval partial |
| Cost per million output tokens | $2.55 Community / $5.79 Secure | $1.98 Community / $4.50 Secure | ESTIMATED from phase time and catalog price, not an invoice |
| Cost per SLO-compliant request | — | — | NOT TESTED; no SLO was supplied |

The 7B result being faster is a real observation for these exact models, kernels and settings; it is not a general statement that 7B models are faster than 3B models.

## Inference matrix

Five warm repetitions were run for each cell. The raw records contain TTFT P50/P95/P99, inter-token P50/P95, E2E P50/P95/P99, token rates, memory, failures and traces.

| Model | Input / target output | TTFT P50 / P95 | E2E P50 / P95 | Output tok/s P50 | Peak VRAM |
|---|---:|---:|---:|---:|---:|
| 3B | 128 / 128 | 41.8 / 537.1 ms | 5.64 / 5.85 s | 24.28 | 5.88 GiB |
| 3B | 128 / 512 | 38.7 / 48.4 ms | 20.85 / 22.06 s | 24.56 | 5.89 GiB |
| 3B | 1,024 / 128 | 127.0 / 129.7 ms | 5.10 / 5.39 s | 25.53 | 5.98 GiB |
| 3B | 1,024 / 512 | 129.1 / 133.6 ms | 21.31 / 21.59 s | 24.13 | 5.98 GiB |
| 3B | 4,096 / 128 | 432.2 / 444.5 ms | 5.56 / 5.79 s | 24.84 | 6.32 GiB |
| 3B | 4,096 / 512 | 433.4 / 433.6 ms | 21.35 / 23.19 s | 24.43 | 6.32 GiB |
| 7B | 128 / 128 | 36.7 / 547.8 ms | 4.35 / 4.65 s | 29.46 | 14.26 GiB |
| 7B | 128 / 512 | 35.8 / 40.6 ms | 16.34 / 16.49 s | 31.35 | 14.28 GiB |
| 7B | 1,024 / 128 | 228.7 / 229.1 ms | 4.37 / 4.49 s | 30.68 | 14.43 GiB |
| 7B | 1,024 / 512 | 229.3 / 229.4 ms | 16.70 / 17.36 s | 31.02 | 14.43 GiB |
| 7B | 4,096 / 128 | 881.0 / 882.5 ms | 5.21 / 5.38 s | 29.36 | 15.00 GiB |
| 7B | 4,096 / 512 | 880.6 / 881.1 ms | 18.84 / 19.13 s | 28.45 | 15.00 GiB |

The first repetition in the 128/128 cell caused the high P95 TTFT for both models; all samples remain in the raw JSON rather than being discarded as warm-up outliers.

## Production-style traffic

Traffic used one intentionally simple serial worker, 128 input tokens and 16 generated tokens. Offered clients above capacity became queued work. A 10-second wall limit stopped overload levels safely; consequently, “500 clients” means 500 offered/queued requests, never 500 simultaneous GPU executions.

| Model | Offered clients | Completed | Timed out | Throughput |
|---|---:|---:|---:|---:|
| 3B | 1 / 10 / 25 / 50 / 100 / 250 / 500 | 1 / 10 / 16 / 16 / 15 / 17 / 17 | 0 / 0 / 9 / 34 / 85 / 233 / 483 | 1.40–1.66 req/s |
| 7B | 1 / 10 / 25 / 50 / 100 / 250 / 500 | 1 / 10 / 19 / 19 / 18 / 20 / 19 | 0 / 0 / 6 / 31 / 82 / 230 / 481 | 1.80–1.98 req/s |
| 3B, sudden 10× burst | 100 | 18 | 82 | 1.71 req/s |
| 7B, sudden 10× burst | 100 | 20 | 80 | 1.90 req/s |

The cancellation probe cancelled queued requests after two seconds: 17/20 for 3B and 16/20 for 7B. In-flight CUDA generation was not pre-empted, so true in-flight request cancellation is **NOT TESTED**. Mixed prompt lengths were measured in the inference matrix but not mixed within one production traffic stream. Process restart timing was measured with five clean processes; routing, replay and in-flight recovery during a crash are **NOT TESTED**.

The 3B soak completed 901.10 seconds with 676/676 successes and 21,632 output tokens. The 7B soak was cut off by the campaign safety deadline after 608.41 seconds with 625/625 successes and 20,000 output tokens; it must not be represented as a complete 15-minute test.

## Multi-model behavior

The models fit concurrently in 24 GB VRAM. Loading 3B used 5.85 GiB; after loading 7B, the pair used 20.10 GiB and peaked at 20.12 GiB. A concurrent short-generation probe completed both requests in 2.83 seconds (7B: 2.61 s, 3B: 2.83 s). Co-residency is therefore **MEASURED**. A matched solo-vs-concurrent trial and long sustained multi-model queue test were **NOT TESTED**, so interference percentage and sustainable combined throughput are not claimed.

## Costs and evidence inventory

The extended phases served 1,604 successful requests and at least 64,720 output tokens. The 3B phase served 33,040 known output tokens; the 7B phase served 31,680. These totals exclude tokenizer/control tokens and the earlier smoke run.

The observed session window from the earlier cold run through completion of the multi-model probe was approximately 62.2 minutes. At current public RTX 3090 catalog rates, that is approximately **$0.23 Community or $0.52 Secure**. The exact Pod tier, time before/after the observed window, billable duration and invoice charge are **NOT TESTED** because the RunPod control connector is authenticated to a different account than the SSH Pod. No extra GPU, network volume, Serverless endpoint or Cluster was provisioned.

Evidence:

- [`qwen2.5-3b-extended.json`](results/20261014T083122Z-extended/qwen2.5-3b-extended.json) and [`qwen2.5-7b-extended.json`](results/20261014T083122Z-extended/qwen2.5-7b-extended.json): raw request, latency, soak and failure records.
- [`matrix-summary.csv`](results/20261014T083122Z-extended/matrix-summary.csv), [`traffic-summary.csv`](results/20261014T083122Z-extended/traffic-summary.csv), and [`cached-restarts.csv`](results/20261014T083122Z-extended/cached-restarts.csv): derived tabular data.
- [`multi-model.json`](results/20261014T083122Z-extended/multi-model.json): co-residency probe.
- Environment captures: `nvidia-smi-before.txt`, `lscpu.txt`, `memory.txt`, `disk.txt`, and `runpod-environment.txt`.
- Exact harness and configuration: `extended_benchmark.py`, `load_probe.py`, `multi_model_probe.py`, and `run_extended_baseline.sh` in this directory.

Primary commands:

```bash
timeout --signal=INT --kill-after=30s 42m bash run_extended_baseline.sh
python3 multi_model_probe.py
```

## Top 10 observed bottlenecks Tesseract could improve

1. **No continuous batching:** the serial worker plateaued around 1.4–2.0 req/s and queue timeouts began between 10 and 25 offered clients. Fusion can batch compatible prefill/decode work.
2. **Decode-dominated long outputs:** 512 output tokens required 16–23 seconds. Fusion scheduling and optimized kernels should target decode efficiency.
3. **Long-context prefill:** median TTFT rose from about 39–42 ms to 433 ms for 3B and from 36 ms to 881 ms for 7B between 128 and 4,096 input tokens. Prompt packing and prefill optimization are high-value targets.
4. **Overload queue collapse:** at 500 offered clients, 3B timed out 483/500 and 7B timed out 481/500. Ignite needs admission control, bounded queues and backpressure.
5. **7B memory pressure:** 7B peaked at 15.00 GiB; both models peaked at 20.12 GiB, leaving little space for larger KV caches or batched traffic. Adaptive quantization can trade precision for KV/batch headroom.
6. **Restart variance:** cached restart-to-first-token ranged 3.39–5.45 seconds for 3B and 4.96–9.02 seconds for 7B. Ignite can use warm pools, readiness gates and deterministic cache placement.
7. **Large initial readiness delay:** combined first download/load/CUDA was 56.12 seconds and 114.92 seconds. Foundry should separately trace artifact download, deserialization, device transfer and kernel initialization.
8. **Under-utilized 3B GPU:** the completed 3B soak showed 33% median and 43.75% P95 utilization. Dynamic batching and concurrent scheduling have substantial unused capacity to recover.
9. **Small local disk/cache margin:** only about 9.9 GB of the 30 GB container disk remained before the extended campaign. Shared artifact caching and cache eviction policies are necessary for reliable multi-model deployment.
10. **Cancellation is queue-only:** queued requests were cancelled, but active GPU generation remained non-preemptive. Cooperative cancellation and token-budget enforcement would reduce wasted compute during disconnects and timeouts.

## Explicitly not completed

Pod provisioning/boot timing, container startup timing, separately timed cold downloads, general network throughput, a full 15-minute 7B soak, mixed-length traffic in one stream, in-flight GPU cancellation, end-to-end crash recovery semantics, matched multi-model interference, exact invoice charges, and SLO-cost accounting remain **NOT TESTED**. They require a newly instrumented Pod lifecycle, a supplied SLO, a production serving engine, or more paid runtime; none was invented or extended beyond the safety cutoff.
