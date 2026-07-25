#!/usr/bin/env bash
# Auth first:  uvx --from huggingface_hub hf auth login   (write token)
# Then:        bash scripts/push_to_hf.sh
# Repos are private; make them public in the HF web UI when ready.
set -euo pipefail

HF_USER="${HF_USER:-decoded-cipher}"
SRC="${SRC:-/tmp/nodrix-adapters}"
HF="uvx --from huggingface_hub hf"

push() {
  $HF upload "$HF_USER/$2" "$SRC/$1" . --repo-type model --private
}

push v1-qwen1.5b nodrix-coder-1.5b-lora-v1
push v2-qwen7b   nodrix-coder-7b-lora-v2
push v3-qwen7b   nodrix-coder-7b-lora-v3

echo "done -> https://huggingface.co/$HF_USER"
