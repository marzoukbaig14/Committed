#!/bin/bash -l
#SBATCH --job-name=committed-lora
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

: "${HF_TOKEN:?export HF_TOKEN before sbatch}"
export WANDB_PROJECT=committed
export WANDB_MODE=offline

# Env (fast no-op — the .venv already exists; CUDA wheels are multi-arch so the
# V100-built venv runs fine on the A100). Skip the compiler-only serving dep.
uv sync --group train --no-install-package llama-cpp-python

# GPU + correct torch build?
nvidia-smi
uv run --no-sync python -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda); assert torch.cuda.is_available(), 'no CUDA'; print('GPU:', torch.cuda.get_device_name(0)); print('bf16 ok:', torch.cuda.is_bf16_supported())"

# Import smoke check.
uv run --no-sync python -c "import transformers, peft, trl, bitsandbytes, accelerate, datasets; print('imports ok')"

# Launch.
uv run --no-sync python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml