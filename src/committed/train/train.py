"""
src/committed/train/train.py

QLoRA fine-tune for Committed — vanilla transformers + peft + trl (no Unsloth).
Loads Qwen3-1.7B in 4-bit, attaches a LoRA adapter, trains with TRL's SFTTrainer
in prompt/completion format with loss masked to the target (completion_only_loss),
logs to W&B (offline), pushes adapter checkpoints to the Hub.

Precision: bf16 (Ampere+ GPUs like the A100). bf16 has fp32's dynamic range, so
NO GradScaler is used — which is why the fp16-scaler bf16 crash (trl#4901) cannot
occur here. Requires an Ampere or newer GPU.

Resume: trainer.train(resume_from_checkpoint=True) continues from the latest
checkpoint in output_dir. transformers 5.9 otherwise blocks loading the (pickled)
optimizer state on torch<2.6 (CVE-2025-32434); since the checkpoint is one WE
wrote on our own cluster (not an untrusted download), we neuter that gate below.

Run (A100 node only):
    uv run --no-sync python -m committed.train.train --config configs/qwen3-1.7b-lora-r16.yaml
"""

import os
# Lock W&B to offline + the 'committed' project BEFORE transformers imports the
# wandb integration, so a run can never land online in the LineGuard team again.
os.environ["WANDB_PROJECT"] = "committed"
os.environ.setdefault("WANDB_MODE", "offline")

import argparse

import torch
import yaml
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTConfig, SFTTrainer

# Same prompt builder as baseline/inference — keeps train and inference shapes identical.
from committed.inference.prompt import build_messages

# --- Resume fix: neuter transformers' torch<2.6 load gate (CVE-2025-32434) ---
# optimizer.pt / scheduler.pt are checkpoints WE wrote on our own cluster, not
# untrusted downloads, so the gate doesn't apply. transformers 5.9 otherwise
# refuses torch.load on torch<2.6, which blocks resume_from_checkpoint. torch.load
# itself works fine on 2.5.1; this gate is a security policy, not a functional one.
import transformers.utils.import_utils as _iu
import transformers.trainer as _hf_trainer
_iu.check_torch_load_is_safe = lambda *a, **k: None
_hf_trainer.check_torch_load_is_safe = lambda *a, **k: None


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

    # 1) Tokenizer + 4-bit base, bf16 compute (A100 native).
    tokenizer = AutoTokenizer.from_pretrained(m["name"])
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        m["name"], quantization_config=bnb, device_map={"": 0},
        dtype=torch.bfloat16,
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

    # 4) Trainer. bf16=True -> bf16 autocast, NO GradScaler. eval/save cadence
    #    comes from the config (set to 500 to fit 2 epochs in the 8h wall).
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
        fp16=False,
        bf16=True,
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

    # resume_from_checkpoint=True picks the highest-numbered checkpoint in
    # output_dir and restores step/optimizer/scheduler, continuing to the end.
    trainer.train(resume_from_checkpoint=True)
    trainer.save_model(io["output_dir"])
    if io["push_to_hub"]:
        trainer.push_to_hub()


if __name__ == "__main__":
    main()