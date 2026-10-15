# Tesseract RunPod Benchmark Results

Campaign date: 2026-10-14

Models:

- `Qwen/Qwen2.5-3B-Instruct` (`aa8e72537993ba99e69dfaafa59ed015b17504d1`)
- `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`)

This page consolidates the budget-bounded RunPod GPU Pod and Serverless campaign. Every figure is backed by committed JSON, CSV or captured environment output. Unavailable measurements are marked **NOT TESTED**.

## Campaign status

| Stage | Status | Result |
|---|---|---|
| Dedicated GPU Pod | Completed | Full 3B/7B inference matrix, traffic probes, soak, restart and co-residency tests |
| Serverless 3B | Partial | Cold smoke request completed |
| Serverless 7B | Partial | Model verified and 12-request warm matrix completed |
| Instant Cluster | NOT TESTED | No selectable capacity was available in the owning account's console |

## Dedicated Pod environment

| Item | Measured value |
|---|---|
| GPU | 1× NVIDIA GeForce RTX 3090, 24,576 MiB |
| Allocation | 32 vCPU, 125 GB RAM |
| Region | EU-CZ-1 |
| Driver / CUDA | 580.159.03 / 12.8 |
| PyTorch / Transformers | 2.8.0+cu128 / 4.48.3 |
| Precision | BF16 |
| Runtime | Hugging Face Transformers eager generation, one serial worker |

## Dedicated Pod headline comparison

| Metric | 3B | 7B |
|---|---:|---:|
| Combined first download/load/CUDA | 56.12 s | 114.92 s |
| Cached fresh-process model-ready P50 | 2.75 s | 7.24 s |
| Restart-to-first-token P50 | 3.46 s | 7.96 s |
| Warm TTFT P50, 128-token input | 41.8 ms | 36.7 ms |
| Output throughput range | 24.13–25.53 tok/s | 28.45–31.35 tok/s |
| Worst matrix E2E P95 | 23.19 s | 19.13 s |
| Peak single-model VRAM | 6.32 GiB | 15.00 GiB |
| Matrix requests | 30/30 successful | 30/30 successful |
| Soak | 676/676 in 901.10 s | 625/625 in 608.41 s, partial interval |
| Sustained output throughput | 24.0 tok/s | 32.9 tok/s |
| Highest offered concurrency without queue timeout | 10 | 10 |
| Estimated cost per million output tokens | $2.55 Community / $5.79 Secure | $1.98 Community / $4.50 Secure |

The 7B model was faster than the 3B model in this exact runtime despite being larger. This is an observed property of the tested model/kernel combination, not a general claim about model sizes.

## Dedicated Pod inference matrix

Five repetitions were run in each cell.

| Model | Input / output target | TTFT P50 / P95 | E2E P50 / P95 | Output tok/s P50 | Peak VRAM |
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

## Dedicated Pod traffic results

Traffic used one deliberately serial worker, 128 input tokens and 16 output tokens. Offered requests beyond capacity waited in a bounded queue; “500 clients” does not mean 500 GPU executions at once.

| Model | Offered clients | Completed | Timed out |
|---|---:|---:|---:|
| 3B | 1 / 10 / 25 / 50 / 100 / 250 / 500 | 1 / 10 / 16 / 16 / 15 / 17 / 17 | 0 / 0 / 9 / 34 / 85 / 233 / 483 |
| 7B | 1 / 10 / 25 / 50 / 100 / 250 / 500 | 1 / 10 / 19 / 19 / 18 / 20 / 19 | 0 / 0 / 6 / 31 / 82 / 230 / 481 |

Sudden 100-client bursts completed 18 requests at 1.71 req/s for 3B and 20 requests at 1.90 req/s for 7B before the safety timeout. Queue cancellation cancelled 17/20 offered 3B requests and 16/20 offered 7B requests. Active CUDA generation was not pre-empted.

## Multi-model result

Both models fit concurrently on the 24 GB RTX 3090:

- 3B after load: 5.85 GiB
- 3B + 7B after load: 20.10 GiB
- Concurrent peak: 20.12 GiB
- Short concurrent probe: 2.83 s total; 7B 2.61 s and 3B 2.83 s

Co-residency was measured, but sustained combined throughput and matched solo-versus-concurrent interference were **NOT TESTED**.

## Serverless results

| Test | Result | Queue/start delay | Execution |
|---|---|---:|---:|
| 3B cold smoke | `SERVERLESS_OK` | 188.038 s | 579 ms |
| 7B warm identity | `SERVERLESS_7B_OK` | 52 ms | 900 ms |

The 7B endpoint returned model identifier `qwen/qwen2.5-7b-instruct` and vLLM fingerprint `vllm-0.31.0-97aafd4e`.

### Serverless 7B warm matrix

Two requests were run per cell. The endpoint tokenizer reported prompts one token below the requested target.

| Reported input | Output target | Successful | Client E2E median | Output throughput |
|---:|---:|---:|---:|---:|
| 127 | 128 | 2/2 | 8.092 s | 18.06–23.66 tok/s |
| 127 | 512 | 2/2 | 21.156 s | 25.40–25.48 tok/s |
| 1,023 | 128 | 2/2 | 6.433 s | 22.56–23.17 tok/s |
| 1,023 | 512 | 2/2 | 21.402 s | 24.97–25.07 tok/s |
| 4,095 | 128 | 2/2 | 7.294 s | 19.93–20.07 tok/s |
| 4,095 | 512 | 2/2 | 22.104 s | 23.72–23.89 tok/s |

All 12 requests completed. Normal warm queue delay was 52–60 ms. Serverless TTFT was **NOT TESTED** because the response did not expose token timestamps; queue delay is not TTFT.

## Cost record

- Dedicated Pod observed campaign window: approximately 62.2 minutes.
- Dedicated Pod estimated charge: $0.23 Community or $0.52 Secure, based on catalog pricing rather than an invoice.
- Serverless public 24 GB pool price observed during testing: $0.69 per running GPU-hour.
- Exact Serverless billable worker-seconds and invoice charge: **NOT TESTED**.
- No Cluster or persistent paid volume was created.

## Top observed bottlenecks

1. Serial inference saturated between 10 and 25 offered clients.
2. Long-output decode dominated latency: 512 output tokens required 16–23 seconds.
3. Long-context prefill increased TTFT substantially, especially for 7B.
4. Extreme offered load caused queue timeouts rather than additional throughput.
5. 7B and dual-model residency left limited VRAM for KV-cache growth.
6. Cached restart-to-first-token varied materially between processes.
7. Initial model download/load/CUDA readiness took 56–115 seconds on the Pod and 188 seconds for the 3B Serverless smoke request.
8. The 3B soak used only 33% median GPU utilization, indicating batching headroom.
9. The 30 GB Pod disk left only about 9.9 GB free before extended testing.
10. Request cancellation removed queued work but did not interrupt active GPU generation.

These observations point directly at Tesseract Fusion batching/scheduling, Adaptive Quantization memory headroom, Ignite readiness/autoscaling/backpressure, and Foundry stage-level telemetry.

## Full reports and evidence

- [Dedicated Pod report](RUNPOD_POD_3B_7B_BASELINE.md)
- [Serverless report](RUNPOD_SERVERLESS_3B_7B_BASELINE.md)
- [Extended Pod raw JSON/CSV](results/20261014T083122Z-extended)
- [Serverless raw JSON/CSV](results/20261014T131633Z-serverless)
- [Initial cold-load report](results/20261014T081346Z/REPORT.md)
- [SHA-256 checksums](results/20261014T083122Z-extended/SHA256SUMS.txt)

## Explicitly NOT TESTED

- Pod provisioning/boot and container-start timestamps.
- Separately isolated cold download versus deserialization/device loading.
- General network throughput.
- Full 15-minute 7B Pod soak; the completed interval was 608.41 seconds.
- Full Serverless production concurrency, burst, soak and autoscaling campaign.
- Five repeated Serverless cold starts per model.
- Serverless TTFT, inter-token latency, VRAM, utilization and power.
- End-to-end crash recovery and replay semantics.
- Exact invoice charges and cost per SLO-compliant request.
- Instant Cluster performance because no selectable capacity was available.

No metric was fabricated for an untested item.
