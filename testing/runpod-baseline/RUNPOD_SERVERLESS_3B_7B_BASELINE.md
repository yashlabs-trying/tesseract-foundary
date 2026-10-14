# RunPod Serverless — Qwen2.5 3B and 7B Baseline

Test date: 2026-10-14 UTC

Raw results: [`results/20261014T131633Z-serverless`](results/20261014T131633Z-serverless)

Related GPU Pod report: [`RUNPOD_POD_3B_7B_BASELINE.md`](RUNPOD_POD_3B_7B_BASELINE.md)

## Executive result

The 3B Serverless endpoint completed a cold smoke request after a 188.038-second managed queue/start delay. The 7B endpoint was verified as `qwen/qwen2.5-7b-instruct` and completed a 12-request warm inference matrix with 12/12 successes. Its warm queue delay was normally 52–60 ms, and measured output throughput ranged from 19.93 to 25.48 tokens/s.

This was a budget-bounded baseline. Repeated cold starts, production concurrency, autoscaling and worker-recovery testing were stopped rather than leaving extra workers billable. Cluster testing was not run because no selectable Cluster capacity was available in the user's RunPod console.

Results below are explicitly labelled **MEASURED**, **ESTIMATED**, or **NOT TESTED**.

## Endpoint smoke tests

| Model | Result | Queue/start delay | Execution time | Evidence status |
|---|---|---:|---:|---|
| Qwen2.5 3B Instruct | `SERVERLESS_OK` | 188.038 s | 579 ms | MEASURED, one cold smoke request |
| Qwen2.5 7B Instruct | `SERVERLESS_7B_OK` | 52 ms | 900 ms | MEASURED, warm identity request |

The 3B worker reported `qwen/qwen2.5-3b-instruct` on vLLM `0.31.0-d239bef3`. The 7B worker reported `qwen/qwen2.5-7b-instruct` on vLLM `0.31.0-97aafd4e`.

An earlier 7B smoke attempt remained `IN_QUEUE` while the endpoint exposed three workers. It was cancelled deliberately, and no duplicate request was submitted. After the endpoint drained to one worker, the succeeding identity request completed normally. Both attempts remain in the raw evidence.

## 7B warm inference matrix

Two requests were run for each cell on one worker. Prompts requested as 128, 1,024 and 4,096 tokens were reported by the serving tokenizer as 127, 1,023 and 4,095 tokens. Each request forced the full target output length with `ignore_eos`.

| Reported input | Output target | Successful | Client E2E median | Execution range | Output throughput range |
|---:|---:|---:|---:|---:|---:|
| 127 | 128 | 2/2 | 8.092 s | 5.409–7.088 s | 18.06–23.66 tok/s |
| 127 | 512 | 2/2 | 21.156 s | 20.097–20.157 s | 25.40–25.48 tok/s |
| 1,023 | 128 | 2/2 | 6.433 s | 5.524–5.675 s | 22.56–23.17 tok/s |
| 1,023 | 512 | 2/2 | 21.402 s | 20.425–20.508 s | 24.97–25.07 tok/s |
| 4,095 | 128 | 2/2 | 7.294 s | 6.377–6.423 s | 19.93–20.07 tok/s |
| 4,095 | 512 | 2/2 | 22.104 s | 21.430–21.589 s | 23.72–23.89 tok/s |

Across all 12 heterogeneous requests, client E2E P50 was 15.147 seconds and P95/P99 were 22.123 seconds. These aggregate percentiles mix prompt/output shapes and have only 12 samples; the per-cell raw observations are the reproducible result and should be preferred.

The first 127/128 request had 1,300 ms queue delay and 7.088 seconds execution. The other warm requests normally had 52–60 ms queue delay, except one at 107 ms. No request failed, timed out or reported an OOM.

## Pod versus Serverless context

| Metric | GPU Pod 7B | Serverless 7B | Interpretation |
|---|---:|---:|---|
| Runtime | Transformers/PyTorch eager | vLLM 0.31.0 | Different inference engines; not an engine-isolated comparison |
| 4,096 input / 512 output | 18.84 s E2E P50 | 22.10 s client median | MEASURED |
| Output throughput at 4,096 / 512 | 28.45 tok/s median | 23.72–23.89 tok/s | MEASURED |
| Warm request queue delay / TTFT proxy | Pod TTFT 880.6 ms | Serverless queue 52–60 ms, TTFT not exposed | Not directly comparable |
| Cold readiness | 114.92 s combined first download/load/CUDA | 3B smoke delay 188.04 s; 7B cold not isolated | Partial measurement only |

Serverless `delayTime` measures RunPod queue/start delay, not model TTFT. The worker response did not expose first-token timestamps, so Serverless TTFT is **NOT TESTED** and must not be inferred from queue delay.

## Costs and budget protection

The public 24 GB Serverless pool price observed during the campaign was $0.69 per running GPU-hour. Exact endpoint GPU type, billable worker-seconds and invoice charges were not available through the authenticated runtime API, so actual Serverless cost is **NOT TESTED**.

Budget protections applied:

- Only one identity job was submitted at a time.
- The stuck 7B job was cancelled rather than duplicated.
- Load testing did not start while three workers were exposed.
- The warm matrix ran only after the endpoint drained to one worker.
- Testing stopped when one worker remained continuously ready, because scale-to-zero had not been verified.
- No persistent volume or additional paid resource was created.

## Raw evidence

- [`smoke-3b.json`](results/20261014T131633Z-serverless/smoke-3b.json): 3B cold smoke job, worker state and token counts.
- [`smoke-7b-attempt.json`](results/20261014T131633Z-serverless/smoke-7b-attempt.json): bounded queued attempt and confirmed cancellation.
- [`smoke-7b-success.json`](results/20261014T131633Z-serverless/smoke-7b-success.json): verified 7B model identity and output.
- [`7b-matrix.json`](results/20261014T131633Z-serverless/7b-matrix.json): complete request and response records.
- [`7b-matrix.csv`](results/20261014T131633Z-serverless/7b-matrix.csv): flattened analysis table.
- [`serverless_probe.py`](serverless_probe.py): reproducible budget-bounded client harness. It reads the credential from `RUNPOD_API_KEY`; no API key is stored in the repository.

## NOT TESTED

- Five cold-start repetitions for either model.
- A separately measured 7B cold start.
- Serverless TTFT and inter-token latency; the response schema did not expose token timestamps.
- Concurrency 10–500, burst traffic and a 15-minute Serverless soak.
- Autoscaling from zero to multiple workers.
- Controlled worker termination and recovery.
- Mixed-length concurrent traffic and in-flight cancellation.
- Exact GPU utilization, VRAM and power inside managed workers.
- Exact Serverless invoice cost and cost per SLO-compliant request.
- RunPod Cluster performance: **NOT TESTED — no selectable capacity was available in the owning account's console.**

No metrics were invented for these items.
