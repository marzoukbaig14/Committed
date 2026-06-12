#!/bin/bash
#SBATCH --job-name=committed-lora
#SBATCH --partition=gpu            # EDIT: your Explorer GPU partition
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail

# EDIT module loads for Explorer if needed, e.g.:
# module load cuda/12.4

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

: "${HF_TOKEN:?export HF_TOKEN before sbatch}"
: "${WANDB_API_KEY:?export WANDB_API_KEY before sbatch}"

# 1) Install the GPU training stack; skip the serving-only llama-cpp-python.
uv sync --group train --no-install-package llama-cpp-python

# 2) GPU visible?
nvidia-smi
uv run --no-sync python -c "import torch; assert torch.cuda.is_available(), 'no CUDA'; print('GPU:', torch.cuda.get_device_name(0))"

# 3) Import smoke check — fail fast before the long run.
uv run --no-sync python -c "import unsloth, trl, peft, bitsandbytes, transformers, datasets; print('imports ok')"

# 4) Launch.
uv run --no-sync python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml