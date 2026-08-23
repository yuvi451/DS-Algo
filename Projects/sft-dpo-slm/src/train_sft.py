"""Day 3 — LoRA SFT.

Usage (from repo root, or as a Kaggle notebook cell):
    python -m src.train_sft
"""
import torch
from huggingface_hub import login as hf_login
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

from . import config as C
from .data import load_sft_splits, print_formatted_examples
from .model_utils import load_base_model, load_tokenizer


def main():
    assert torch.cuda.is_available(), "no GPU visible — check the T4 accelerator is enabled"
    print("GPU:", torch.cuda.get_device_name(0))

    tokenizer = load_tokenizer()
    train_dataset, eval_prompts = load_sft_splits(tokenizer)

    print(f"SFT train examples: {len(train_dataset)}, held-out eval prompts: {len(eval_prompts)}")
    print_formatted_examples(train_dataset, n=5)

    model = load_base_model()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=C.LORA_R,
        lora_alpha=C.LORA_ALPHA,
        lora_dropout=C.LORA_DROPOUT,
        target_modules=C.LORA_TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )

    sft_config = SFTConfig(
        output_dir=C.SFT_ADAPTER_DIR,
        per_device_train_batch_size=C.SFT_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=C.SFT_GRAD_ACCUM_STEPS,
        num_train_epochs=C.SFT_EPOCHS,
        learning_rate=C.SFT_LEARNING_RATE,
        fp16=True,  # T4 is Turing: no bf16 support (§2 table)
        max_seq_length=C.SFT_MAX_SEQ_LENGTH,
        warmup_ratio=C.SFT_WARMUP_RATIO,
        lr_scheduler_type=C.SFT_LR_SCHEDULER,
        dataset_text_field="text",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    trainer.train()

    trainer.model.save_pretrained(C.SFT_ADAPTER_DIR)
    tokenizer.save_pretrained(C.SFT_ADAPTER_DIR)
    print(f"SFT adapter saved to {C.SFT_ADAPTER_DIR}")

    # Push to Hub immediately — Kaggle sessions die, adapters are ~50MB (§2).
    try:
        hf_login()  # picks up token from `huggingface-cli login` / HF_TOKEN env
        trainer.model.push_to_hub(C.SFT_ADAPTER_REPO)
        tokenizer.push_to_hub(C.SFT_ADAPTER_REPO)
        print(f"Pushed SFT adapter to https://huggingface.co/{C.SFT_ADAPTER_REPO}")
    except Exception as e:
        print(f"WARNING: push to Hub failed ({e}). Adapter is still saved locally at {C.SFT_ADAPTER_DIR}.")


if __name__ == "__main__":
    main()
