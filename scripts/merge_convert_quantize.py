#!/usr/bin/env python3
"""
merge_convert_quantize.py — fine-tune -> GGUF serving artifacts (ADR 0044).

Turns a trained LoRA adapter into the served GGUF. Three shell-out stages, all
CPU-only (no GPU needed for a 0.6B/1.7B model):

  1. Merge   — load the base model + the LoRA adapter, merge_and_unload, save FP16 HF.
  2. Convert — llama.cpp `convert_hf_to_gguf.py`  -> fp16 GGUF.
  3. Quantize— llama.cpp `llama-quantize`         -> Q4_K_M (the serving quant of
               record, ADR 0048). Pass extra quants with --quants for the
               quality-vs-latency table.

v2-i1 (ADR 0049) repointed this to Qwen3-0.6B. It produced the artifacts in
`marzoukbaig14/committed-gguf-0.6b` (committed-0.6b-finetuned-Q4_K_M.gguf). The
baseline GGUF for the 0.6B-vs-0.6B comparison is the un-fine-tuned base run
through stages 2-3 only (--no-adapter).

llama.cpp: this needs a llama.cpp checkout for the convert script and the built
`llama-quantize` binary. Point at it with --llamacpp (or the LLAMACPP_DIR env
var). Build the tool once with:
    cmake -B build -DLLAMA_CURL=OFF llama.cpp && cmake --build build --target llama-quantize -j
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE_MODEL = "Qwen/Qwen3-0.6B"
QUANTS_DEFAULT = ["Q4_K_M"]


def merge_adapter(base_model: str, adapter: str, out_dir: str) -> str:
    """Merge the LoRA adapter into the base and save a merged FP16 HF model."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(f"[merge] base={base_model} adapter={adapter} -> {out_dir}")
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.float16, low_cpu_mem_usage=True
    )
    model = PeftModel.from_pretrained(model, adapter).merge_and_unload()
    model.save_pretrained(out_dir)
    AutoTokenizer.from_pretrained(base_model).save_pretrained(out_dir)
    return out_dir


def convert_to_gguf(hf_dir: str, gguf_fp16: str, llamacpp: Path) -> str:
    """Convert a merged HF model to an fp16 GGUF via llama.cpp convert_hf_to_gguf.py."""
    script = llamacpp / "convert_hf_to_gguf.py"
    if not script.exists():
        sys.exit(f"[convert] {script} not found; pass --llamacpp at a llama.cpp checkout")
    print(f"[convert] {hf_dir} -> {gguf_fp16}")
    subprocess.run(
        [sys.executable, str(script), hf_dir, "--outfile", gguf_fp16, "--outtype", "f16"],
        check=True,
    )
    return gguf_fp16


def quantize(gguf_fp16: str, quant: str, out_path: str, llamacpp: Path) -> str:
    """Quantize an fp16 GGUF to `quant` via llama.cpp `llama-quantize`."""
    binary = llamacpp / "build" / "bin" / "llama-quantize"
    if not binary.exists():
        sys.exit(f"[quantize] {binary} not built; see the build command in the module docstring")
    print(f"[quantize] {gguf_fp16} -> {out_path} ({quant})")
    subprocess.run([str(binary), gguf_fp16, out_path, quant], check=True)
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(description="merge LoRA -> GGUF -> quantize (ADR 0044).")
    p.add_argument("--adapter", default="marzoukbaig14/committed-qwen3-0.6b-lora",
                   help="path or Hub id of the LoRA adapter (ignored with --no-adapter)")
    p.add_argument("--no-adapter", action="store_true",
                   help="skip the merge: convert/quantize the bare base model (the eval baseline)")
    p.add_argument("--base", default=BASE_MODEL)
    p.add_argument("--out-dir", default="models")
    p.add_argument("--name", default="committed-0.6b-finetuned",
                   help="artifact stem, e.g. committed-0.6b-finetuned / committed-0.6b-baseline")
    p.add_argument("--quants", nargs="+", default=QUANTS_DEFAULT)
    p.add_argument("--llamacpp", default=os.environ.get("LLAMACPP_DIR", "llama.cpp"),
                   help="path to a llama.cpp checkout (convert script + built llama-quantize)")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    llamacpp = Path(args.llamacpp)

    # Stage 1 (skipped for the baseline): produce a merged HF model directory.
    if args.no_adapter:
        from huggingface_hub import snapshot_download
        hf_dir = snapshot_download(args.base, local_dir=str(out_dir / f"{args.name}-hf"))
    else:
        hf_dir = merge_adapter(args.base, args.adapter, str(out_dir / f"{args.name}-merged"))

    # Stage 2: fp16 GGUF.
    fp16 = str(out_dir / f"{args.name}-f16.gguf")
    convert_to_gguf(hf_dir, fp16, llamacpp)

    # Stage 3: quantize.
    for q in args.quants:
        quantize(fp16, q, str(out_dir / f"{args.name}-{q}.gguf"), llamacpp)

    print("done.")


if __name__ == "__main__":
    main()
