#!/bin/bash -l
#SBATCH --job-name=committed-lora
#SBATCH --partition=gpu            # EDIT: your Explorer GPU partition
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"   # uv installs here

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

: "${HF_TOKEN:?export HF_TOKEN before sbatch}"
export WANDB_PROJECT=committed
export WANDB_MODE=offline

# 1) Env (fast if the interactive build already populated .venv); skip the
#    compiler-only serving dep we don't need for training.
uv sync --group train --no-install-package llama-cpp-python

# 2) GPU + correct torch build?
nvidia-smi
uv run --no-sync python -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda); assert torch.cuda.is_available(), 'no CUDA'; print('GPU:', torch.cuda.get_device_name(0))"

# 3) Import smoke check.
uv run --no-sync python -c "import transformers, peft, trl, bitsandbytes, accelerate, datasets; print('imports ok')"

# 4) Launch.
uv run --no-sync python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml