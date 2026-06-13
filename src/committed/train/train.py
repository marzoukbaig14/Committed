"""
src/committed/train/train.py

QLoRA fine-tune for Committed — vanilla transformers + peft + trl (no Unsloth,
V100/Volta compatible). Loads Qwen3-1.7B in 4-bit, attaches a LoRA adapter,
trains with TRL's SFTTrainer in prompt/completion format with loss masked to the
target message (completion_only_loss), logs to W&B, pushes checkpoints to the Hub.

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

    # 1) Tokenizer + 4-bit base. V100 has no bf16 -> fp16 compute dtype.
    tokenizer = AutoTokenizer.from_pretrained(m["name"])
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    # dtype=float16 is REQUIRED: without it the non-quantized modules (and so the
    # LoRA grads) load in Qwen3's config-default bfloat16, which the fp16 grad
    # scaler can't unscale on a V100 -> "_amp_foreach...not implemented for BFloat16".
    model = AutoModelForCausalLM.from_pretrained(
        m["name"], quantization_config=bnb, device_map={"": 0},
        dtype=torch.float16,
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

    # 4) Trainer. completion_only_loss masks the prompt; fp16 (NOT bf16 — V100).
    sft_config = SFTConfig(
        output_dir=io["output_dir"],
        max_length=m["max_seq_length"],
        completion_only_loss=True,
        packing=False,
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