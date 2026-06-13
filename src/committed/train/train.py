"""
src/committed/train/train.py

QLoRA fine-tune for Committed — vanilla transformers + peft + trl (no Unsloth,
V100/Volta compatible). Loads Qwen3-1.7B in 4-bit, attaches a LoRA adapter,
trains with TRL's SFTTrainer in prompt/completion format with loss masked to the
target message (completion_only_loss), logs to W&B, pushes checkpoints to the Hub.

Mixed precision done the correct way for V100: the model loads in fp32 (master
weights) and fp16=True runs the *compute* in fp16 via autocast. Grads stay fp32,
so the GradScaler never sees bf16/fp16 grads (avoids the trl#4901 crash) while
matmuls still use the V100's fp16 tensor cores. The model must NOT be loaded in
bf16/fp16, or the scaler breaks.

Run (GPU node only):
    uv run --no-sync python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml
"""

import argparse

import torch
import yaml
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTConfig, SFTTrainer

# Same prompt builder as baseline/inference — keeps train and inference shapes identical.
from committed.inference.prompt import build_messages


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = load_config(ap.parse_args().config)
    m, lora, data, opt, sch, io = (
        cfg["model"], cfg["lora"], cfg["data"], cfg["optim"], cfg["schedule"], cfg["io"]
    )

    # 1) Tokenizer + 4-bit base. compute_dtype=fp16 so the base matmuls use the
    #    V100's fp16 tensor cores; the model itself loads in fp32 (master weights).
    tokenizer = AutoTokenizer.from_pretrained(m["name"])
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        m["name"], quantization_config=bnb, device_map={"": 0},
        dtype=torch.float32,
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # 2) LoRA adapter — the only trainable weights.
    peft_config = LoraConfig(
        r=lora["r"],
        lora_alpha=lora["alpha"],
        lora_dropout=lora["dropout"],
        bias=lora["bias"],
        target_modules=lora["target_modules"],
        use_rslora=lora["use_rslora"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Guarantee the trainable (and any other) params are fp32, never bf16 — fp32
    # master weights are what make the fp16 GradScaler work. 4-bit weights are
    # uint8-backed and untouched.
    for _, p in model.named_parameters():
        if p.dtype == torch.bfloat16:
            p.data = p.data.to(torch.float32)

    # 3) Prompt/completion format. prompt = the EXACT baseline render (system+user,
    #    /no_think, thinking off); completion = the target message. TRL tokenizes
    #    both, masks the prompt, trains only on the completion.
    def to_pc(example):
        prompt = tokenizer.apply_chat_template(
            build_messages(example["diff"]),
            tokenize=False, add_generation_prompt=True, enable_thinking=False,
        )
        return {"prompt": prompt, "completion": example["message"]}

    raw_train = load_dataset(data["dataset"], split=data["train_split"])
    train_ds = raw_train.map(to_pc, remove_columns=raw_train.column_names)
    raw_eval = load_dataset(data["dataset"], split=data["eval_split"])
    eval_ds = raw_eval.map(to_pc, remove_columns=raw_eval.column_names)

    # 4) Trainer. fp16=True = autocast fp16 compute on fp32 master weights (the
    #    correct V100 mixed-precision setup). group_by_length batches similar-
    #    length sequences to cut padding waste (huge here: p50~459, cap 2432).
    sft_config = SFTConfig(
        output_dir=io["output_dir"],
        max_length=m["max_seq_length"],
        completion_only_loss=True,
        packing=False,
        group_by_length=True,
        per_device_train_batch_size=sch["per_device_train_batch_size"],
        gradient_accumulation_steps=sch["gradient_accumulation_steps"],
        num_train_epochs=sch["num_train_epochs"],
        learning_rate=float(opt["learning_rate"]),
        lr_scheduler_type=opt["lr_scheduler_type"],
        warmup_ratio=opt["warmup_ratio"],
        optim=opt["optimizer"],
        weight_decay=opt["weight_decay"],
        max_grad_norm=opt["max_grad_norm"],
        seed=sch["seed"],
        fp16=True,
        bf16=False,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=io["logging_steps"],
        eval_strategy=io["eval_strategy"],
        eval_steps=io["eval_steps"],
        save_strategy="steps",
        save_steps=io["save_steps"],
        push_to_hub=io["push_to_hub"],
        hub_model_id=io["hub_model_id"],
        hub_strategy="every_save",
        report_to=io["report_to"],
        run_name=io["run_name"],
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=sft_config,
    )

    trainer.train()
    trainer.save_model(io["output_dir"])
    if io["push_to_hub"]:
        trainer.push_to_hub()


if __name__ == "__main__":
    main()