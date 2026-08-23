"""Day 5 — DPO, starting from the SFT adapter.

With LoRA, ref_model=None makes TRL compute reference logits by temporarily
disabling the adapters on the same frozen base weights — no second copy of
the model in memory (see project breakdown §4 Day 5 and §7 OOM note).

Usage:
    python -m src.train_dpo
"""
import torch
from huggingface_hub import login as hf_login
from peft import PeftModel
from trl import DPOConfig, DPOTrainer

from . import config as C
from .data import load_dpo_splits
from .model_utils import load_base_model, load_tokenizer


def main():
    assert torch.cuda.is_available(), "no GPU visible — check the T4 accelerator is enabled"
    print("GPU:", torch.cuda.get_device_name(0))

    tokenizer = load_tokenizer()
    train_dataset, pref_holdout = load_dpo_splits(tokenizer)
    print(f"DPO train pairs: {len(train_dataset)}, preference holdout: {len(pref_holdout)}")

    base = load_base_model()
    # Load the SFT adapter as the starting policy, and keep it trainable.
    model = PeftModel.from_pretrained(base, C.SFT_ADAPTER_DIR, is_trainable=True)
    model.config.use_cache = False

    dpo_config = DPOConfig(
        output_dir=C.DPO_ADAPTER_DIR,
        beta=C.DPO_BETA,
        learning_rate=C.DPO_LEARNING_RATE,
        per_device_train_batch_size=C.DPO_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=C.DPO_GRAD_ACCUM_STEPS,
        num_train_epochs=C.DPO_EPOCHS,
        fp16=True,
        max_length=C.DPO_MAX_LENGTH,
        max_prompt_length=C.DPO_MAX_PROMPT_LENGTH,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # LoRA: reference logits computed with adapters disabled
        args=dpo_config,
        train_dataset=train_dataset,
        processing_class=tokenizer,
    )

    trainer.train()

    # Watch rewards/accuracies (should climb above 0.5) and rewards/margins
    # (should widen) in the printed logs above — a flatline means DPO isn't
    # learning anything (§4 Day 5, §7).

    trainer.model.save_pretrained(C.DPO_ADAPTER_DIR)
    tokenizer.save_pretrained(C.DPO_ADAPTER_DIR)
    print(f"DPO adapter saved to {C.DPO_ADAPTER_DIR}")

    try:
        hf_login()
        trainer.model.push_to_hub(C.DPO_ADAPTER_REPO)
        tokenizer.push_to_hub(C.DPO_ADAPTER_REPO)
        print(f"Pushed DPO adapter to https://huggingface.co/{C.DPO_ADAPTER_REPO}")
    except Exception as e:
        print(f"WARNING: push to Hub failed ({e}). Adapter is still saved locally at {C.DPO_ADAPTER_DIR}.")


if __name__ == "__main__":
    main()
