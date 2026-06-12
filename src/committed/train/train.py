"""
src/committed/train/train.py

QLoRA fine-tune for Committed. Reads a YAML config, loads Qwen3-1.7B in 4-bit via
Unsloth, attaches a LoRA adapter, trains with TRL's SFTTrainer on
marzoukbaig14/committed-train, masks loss to the target message only, logs to
W&B, and pushes adapter checkpoints to the Hub.

Run (GPU machine only):
    uv run python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml
"""

import argparse

import yaml
# Unsloth must be imported before transformers/trl so its patches apply.
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

# Same prompt builder the baseline/inference path uses — keeps the train and
# inference input shapes identical. prompt.py exposes build_messages(diff).
from committed.inference.prompt import build_messages


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="path to the YAML training config")
    cfg = load_config(ap.parse_args().config)
    m, lora, data, opt, sch, io = (
        cfg["model"], cfg["lora"], cfg["data"], cfg["optim"], cfg["schedule"], cfg["io"]
    )

    # 1) Base model in 4-bit (QLoRA). dtype=None -> bf16 on Ampere+, fp16 on T4.
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=m["name"],
        max_seq_length=m["max_seq_length"],
        load_in_4bit=m["load_in_4bit"],
        dtype=None,
    )

    # 2) Attach the LoRA adapter — the only trainable weights.
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora["r"],
        lora_alpha=lora["alpha"],
        lora_dropout=lora["dropout"],
        bias=lora["bias"],
        target_modules=lora["target_modules"],
        use_rslora=lora["use_rslora"],
        use_gradient_checkpointing="unsloth",  # saves VRAM on long sequences
        random_state=sch["seed"],
    )

    # 3) Render each row as system+user(diff) -> assistant(message), thinking off.
    #    No add_generation_prompt: the assistant turn is present (training, not generation).
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

    # 4) Trainer config. effective batch = per_device x grad_accum x num_gpus.
    sft_config = SFTConfig(
        output_dir=io["output_dir"],
        dataset_text_field="text",
        max_seq_length=m["max_seq_length"],
        packing=io["packing"],
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
        logging_steps=io["logging_steps"],
        eval_strategy=io["eval_strategy"],   # newer transformers; older used evaluation_strategy
        eval_steps=io["eval_steps"],
        save_strategy="steps",
        save_steps=io["save_steps"],
        push_to_hub=io["push_to_hub"],
        hub_model_id=io["hub_model_id"],
        hub_strategy="every_save",           # push each checkpoint — cluster jobs can die
        report_to=io["report_to"],
        run_name=io["run_name"],
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,          # newer TRL renamed `tokenizer` -> `processing_class`
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=sft_config,
    )

    # 5) Mask loss to the assistant turn only — the target is ~5% of the sequence.
    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|im_start|>user\n",
        response_part="<|im_start|>assistant\n",
    )

    trainer.train()

    trainer.save_model(io["output_dir"])
    if io["push_to_hub"]:
        trainer.push_to_hub()


if __name__ == "__main__":
    main()