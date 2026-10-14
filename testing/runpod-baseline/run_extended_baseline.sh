#!/usr/bin/env bash
set -Eeuo pipefail

export HF_HOME="${HF_HOME:-/workspace/hf-cache}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME/hub}"
export TOKENIZERS_PARALLELISM=false
unset HF_HUB_ENABLE_HF_TRANSFER

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RESULT_DIR="${RESULT_DIR:-results/$RUN_ID-extended}"
mkdir -p "$RESULT_DIR"

date -u --iso-8601=seconds > "$RESULT_DIR/started_at.txt"
nvidia-smi -q > "$RESULT_DIR/nvidia-smi-before.txt"
lscpu > "$RESULT_DIR/lscpu.txt"
free -b > "$RESULT_DIR/memory.txt"
df -B1 > "$RESULT_DIR/disk.txt"
env | grep -E '^RUNPOD_(POD_ID|DC_ID|GPU_COUNT|CPU_COUNT|MEM_GB|VOLUME_PATH)=' \
  | sort > "$RESULT_DIR/runpod-environment.txt"

for spec in \
  '3b|Qwen/Qwen2.5-3B-Instruct|aa8e72537993ba99e69dfaafa59ed015b17504d1' \
  '7b|Qwen/Qwen2.5-7B-Instruct|a09a35458c702b33eeacc393d103063234e8bc28'; do
  IFS='|' read -r label model revision <<< "$spec"
  : > "$RESULT_DIR/${label}-cached-restarts.jsonl"
  for repetition in 1 2 3 4 5; do
    python3 load_probe.py --model "$model" --revision "$revision" \
      | tee -a "$RESULT_DIR/${label}-cached-restarts.jsonl"
  done
done

python3 extended_benchmark.py \
  --label qwen2.5-3b-instruct \
  --model Qwen/Qwen2.5-3B-Instruct \
  --revision aa8e72537993ba99e69dfaafa59ed015b17504d1 \
  --soak-seconds 900 \
  --output "$RESULT_DIR/qwen2.5-3b-extended.json" \
  2>&1 | tee "$RESULT_DIR/qwen2.5-3b-extended.log"

python3 extended_benchmark.py \
  --label qwen2.5-7b-instruct \
  --model Qwen/Qwen2.5-7B-Instruct \
  --revision a09a35458c702b33eeacc393d103063234e8bc28 \
  --soak-seconds 900 \
  --output "$RESULT_DIR/qwen2.5-7b-extended.json" \
  2>&1 | tee "$RESULT_DIR/qwen2.5-7b-extended.log"

python3 multi_model_probe.py \
  > "$RESULT_DIR/multi-model.json" \
  2> "$RESULT_DIR/multi-model.stderr.log" || true

nvidia-smi -q > "$RESULT_DIR/nvidia-smi-after.txt"
date -u --iso-8601=seconds > "$RESULT_DIR/completed_at.txt"
echo "$RESULT_DIR"

