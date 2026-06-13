"""
src/committed/train/train.py

QLoRA fine-tune for Committed — vanilla transformers + peft + trl (no Unsloth,
for V100/Volta compatibility). Loads Qwen3-1.7B in 4-bit, attaches a LoRA
adapter, trains with TRL's SFTTrainer with loss masked to the target message,
logs to W&B, pushes adapter checkpoints to the Hub.

Run (GPU node only):
    uv run --no-sync python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml
"""

import argparse

import torch
import yaml
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTConfig, SFTTrainer, DataCollatorForCompletionOnlyLM

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
    model = AutoModelForCausalLM.from_pretrained(
        m["name"], quantization_config=bnb, device_map="auto", torch_dtype=torch.float16,
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

    # 3) Render system+user(diff) -> assistant(message), thinking off.
    def to_text(example):
        messages = build_messages(example["diff"]) + [
            {"role": "assistant", "content": example["message"]},
        ]
        return {"text": tokenizer.apply_chat_template(
            messages, tokenize=False, enable_thinking=False)}

    raw_train = load_dataset(data["dataset"], split=data["train_split"])
    train_ds = raw_train.map(to_text, remove_columns=raw_train.column_names)
    raw_eval = load_dataset(data["dataset"], split=data["eval_split"])
    eval_ds = raw_eval.map(to_text, remove_columns=raw_eval.column_names)

    # 4) Loss masked to the assistant turn only — everything up to and including
    #    this response template is ignored in the loss.
    collator = DataCollatorForCompletionOnlyLM(
        response_template="<|im_start|>assistant\n", tokenizer=tokenizer,
    )

    # 5) Trainer. fp16 (NOT bf16 — V100). effective batch = per_device x grad_accum.
    sft_config = SFTConfig(
        output_dir=io["output_dir"],
        dataset_text_field="text",
        max_seq_length=m["max_seq_length"],
        packing=False,                      # must stay off — the collator needs intact turns
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
        data_collator=collator,
    )

    trainer.train()
    trainer.save_model(io["output_dir"])
    if io["push_to_hub"]:
        trainer.push_to_hub()


if __name__ == "__main__":
    main()