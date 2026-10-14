#!/usr/bin/env bash
set -Eeuo pipefail

export HF_HOME="${HF_HOME:-/workspace/hf-cache}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME/hub}"
export TOKENIZERS_PARALLELISM=false
# Some RunPod templates enable the optional transfer backend without installing
# its Python package. Standard HTTP downloads are reliable for this small run.
unset HF_HUB_ENABLE_HF_TRANSFER

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RESULT_DIR="${RESULT_DIR:-results/$RUN_ID}"
mkdir -p "$RESULT_DIR"

date -u --iso-8601=seconds > "$RESULT_DIR/started_at.txt"
nvidia-smi -q > "$RESULT_DIR/nvidia-smi-before.txt"
python3 -m pip install --disable-pip-version-check -r requirements.txt 2>&1 | tee "$RESULT_DIR/install.log"
python3 -m pip freeze > "$RESULT_DIR/pip-freeze.txt"

python3 benchmark.py \
  --label qwen2.5-3b-instruct \
  --model Qwen/Qwen2.5-3B-Instruct \
  --revision aa8e72537993ba99e69dfaafa59ed015b17504d1 \
  --output "$RESULT_DIR/qwen2.5-3b-instruct.json" \
  2>&1 | tee "$RESULT_DIR/qwen2.5-3b-instruct.log"

python3 benchmark.py \
  --label qwen2.5-7b-instruct \
  --model Qwen/Qwen2.5-7B-Instruct \
  --revision a09a35458c702b33eeacc393d103063234e8bc28 \
  --output "$RESULT_DIR/qwen2.5-7b-instruct.json" \
  2>&1 | tee "$RESULT_DIR/qwen2.5-7b-instruct.log"

nvidia-smi -q > "$RESULT_DIR/nvidia-smi-after.txt"
date -u --iso-8601=seconds > "$RESULT_DIR/completed_at.txt"
echo "$RESULT_DIR"

