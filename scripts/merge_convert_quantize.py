#!/usr/bin/env python3
"""
merge_convert_quantize.py — SCAFFOLD (not runnable yet).

Turns a trained LoRA adapter into the served GGUF artifacts. No adapter exists yet,
so this documents and stubs the pipeline rather than running it. It uses the GPU
`train` dependency group (peft/torch) plus llama.cpp's conversion tooling, so it is
meant for the cluster/Colab, not the CPU serving environment.

Pipeline:
  1. Merge   — load Qwen/Qwen3-1.7B + the LoRA adapter, merge_and_unload, save FP16 HF.
  2. Convert — llama.cpp convert_hf_to_gguf.py            -> fp16 GGUF.
  3. Quantize— llama-quantize                              -> Q4_K_M (primary served
               artifact), Q8_0, and keep fp16, for the quality-vs-latency table (MASTER).
  4. Upload  — push each GGUF to the Hub (model registry), the source of truth for artifacts.

OWED DECISION: the final served quant for the fine-tuned model is pinned by an
outstanding ADR the human finalizes (MASTER Serving Plan: Q4_K_M primary; Q8/fp16
for comparison). This script targets all three; it does not decide the pin.
"""

from __future__ import annotations

import argparse

BASE_MODEL = "Qwen/Qwen3-1.7B"
QUANTS = ["Q4_K_M", "Q8_0", "F16"]


def merge_adapter(base_model: str, adapter: str, out_dir: str) -> str:
    """Merge the LoRA adapter into the base and save a merged FP16 HF model.

    TODO(adapter): implement once an adapter exists. Sketch:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype="auto")
        model = PeftModel.from_pretrained(model, adapter).merge_and_unload()
        model.save_pretrained(out_dir)
        AutoTokenizer.from_pretrained(base_model).save_pretrained(out_dir)
    """
    raise NotImplementedError("merge step is scaffolded; no adapter exists yet")


def convert_to_gguf(hf_dir: str, gguf_fp16: str) -> str:
    """Convert the merged HF model to an fp16 GGUF via llama.cpp convert_hf_to_gguf.py.

    TODO: shell out to
        python llama.cpp/convert_hf_to_gguf.py {hf_dir} --outfile {gguf_fp16} --outtype f16
    """
    raise NotImplementedError("convert step is scaffolded")


def quantize(gguf_fp16: str, quant: str, out_path: str) -> str:
    """Quantize the fp16 GGUF to `quant` via llama.cpp `llama-quantize`.

    TODO: shell out to  llama-quantize {gguf_fp16} {out_path} {quant}
    """
    raise NotImplementedError("quantize step is scaffolded")


def main() -> None:
    p = argparse.ArgumentParser(description="Scaffold: merge LoRA -> GGUF -> quantize.")
    p.add_argument("--adapter", required=True, help="path or Hub id of the LoRA adapter")
    p.add_argument("--out-dir", default="models/merged")
    p.add_argument("--quants", nargs="+", default=QUANTS)
    p.add_argument("--upload-repo", default=None, help="Hub repo to push GGUFs to")
    args = p.parse_args()

    raise SystemExit(
        f"merge_convert_quantize.py is a scaffold: no adapter exists yet "
        f"(asked for {args.adapter}). Implement the TODOs and remove this guard "
        f"once training has produced an adapter."
    )


if __name__ == "__main__":
    main()
