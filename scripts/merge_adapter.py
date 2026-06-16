"""
merge_adapter.py — Stage 1 of the fine-tune eval pipeline.

Takes the base model (Qwen/Qwen3-1.7B) and the trained LoRA adapter
(marzoukbaig14/committed-qwen3-1.7b-lora), fuses the adapter's learned
weights permanently into the base, and writes a single self-contained
model to ./committed-merged/.

Why this step exists:
  The QLoRA fine-tune did NOT retrain the whole model. It trained a small
  adapter (~17M params) that sits on top of the frozen 1.7B base. To run
  the model through llama.cpp later, we need ONE standalone model file --
  not a base + a separate adapter. merge_and_unload() bakes the adapter
  into the base weights so the result behaves as a normal model with no
  adapter dependency.

Memory note:
  Loaded in fp16 with low_cpu_mem_usage=True to keep the peak around
  5-6 GB, comfortably inside the Codespace's available RAM. This runs
  entirely on CPU; no GPU is required or used.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# --- Identifiers -----------------------------------------------------------
BASE_MODEL = "Qwen/Qwen3-1.7B"                          # the frozen base
ADAPTER = "marzoukbaig14/committed-qwen3-1.7b-lora"     # our trained adapter
OUTPUT_DIR = "committed-merged"                         # where the fused model lands


def main():
    # 1. Load the base model.
    #    torch_dtype=fp16 halves the memory vs the default fp32.
    #    low_cpu_mem_usage streams weights in instead of building a full
    #    copy in RAM first -- this is what keeps the peak manageable.
    print(f"Loading base model: {BASE_MODEL} ...")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )

    # 2. Attach the trained adapter on top of the base.
    #    At this point the model is "base + adapter": the adapter is still
    #    a separate set of weights layered over the frozen base.
    print(f"Attaching adapter: {ADAPTER} ...")
    model = PeftModel.from_pretrained(base, ADAPTER)

    # 3. Fuse them. merge_and_unload() folds the adapter's deltas into the
    #    base weights and removes the adapter wrapper, leaving a plain model.
    print("Merging adapter into base weights ...")
    model = model.merge_and_unload()

    # 4. Save the merged model plus the tokenizer. The tokenizer must travel
    #    with the model so the next stage (GGUF conversion) has everything
    #    it needs in one folder.
    print(f"Saving merged model to: {OUTPUT_DIR}/ ...")
    model.save_pretrained(OUTPUT_DIR)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("Done. Merged model written to", OUTPUT_DIR)


if __name__ == "__main__":
    main()