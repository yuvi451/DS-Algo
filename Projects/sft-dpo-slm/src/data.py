"""Dataset loading, splitting and chat-template formatting for SFT + DPO.

Split order matters (see project breakdown §3 / Day 1): held-out slices are
carved out FIRST, before any subsampling of the training data, so there is
no leakage between what the model trains on and what it's judged on.
"""
import random

from datasets import load_dataset

from . import config as C


def _format_instruction(example):
    if example.get("input"):
        return f"{example['instruction']}\n\n{example['input']}"
    return example["instruction"]


def load_sft_splits(tokenizer):
    """Returns (train_dataset, eval_prompts) for SFT.

    train_dataset has a precomputed "text" column (fully chat-templated,
    prompt + response + eos) ready for SFTTrainer(dataset_text_field="text").
    eval_prompts is a list of plain instruction strings, held out before
    subsampling, used later for generation-based evaluation (Day 2/4/6).
    """
    raw = load_dataset(C.SFT_DATASET, split="train")
    raw = raw.filter(lambda ex: len(ex["output"].strip()) > 0)

    rng = random.Random(C.SEED)
    indices = list(range(len(raw)))
    rng.shuffle(indices)

    eval_indices = indices[: C.EVAL_PROMPTS_SIZE]
    remaining = indices[C.EVAL_PROMPTS_SIZE :]
    train_indices = remaining[: C.SFT_TRAIN_SIZE]

    eval_prompts = [_format_instruction(raw[i]) for i in eval_indices]

    train_raw = raw.select(train_indices)

    def to_text(example):
        messages = [
            {"role": "user", "content": _format_instruction(example)},
            {"role": "assistant", "content": example["output"]},
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    train_dataset = train_raw.map(to_text, remove_columns=train_raw.column_names)
    return train_dataset, eval_prompts


def load_dpo_splits(tokenizer):
    """Returns (train_dataset, pref_holdout) for DPO.

    train_dataset has "prompt" / "chosen" / "rejected" string columns, where
    "prompt" is chat-templated with add_generation_prompt=True and
    chosen/rejected are the raw continuation text (what DPOTrainer expects).
    pref_holdout is a list of dicts with the same three keys, held out
    before subsampling, used for the reward-accuracy metric (§6).
    """
    raw = load_dataset(C.DPO_DATASET, split="train")

    def build(example):
        system = example.get("system") or ""
        question = example["question"]
        messages = []
        if system.strip():
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": question})
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return {"prompt": prompt, "chosen": example["chosen"], "rejected": example["rejected"]}

    formatted = raw.map(build, remove_columns=raw.column_names)

    rng = random.Random(C.SEED)
    indices = list(range(len(formatted)))
    rng.shuffle(indices)

    holdout_indices = indices[: C.PREF_HOLDOUT_SIZE]
    remaining = indices[C.PREF_HOLDOUT_SIZE :]
    train_indices = remaining[: C.DPO_TRAIN_SIZE]

    pref_holdout = [formatted[i] for i in holdout_indices]
    train_dataset = formatted.select(train_indices)
    return train_dataset, pref_holdout


def print_formatted_examples(train_dataset, n=5):
    """Day 1 sanity step: print n formatted examples in full so you can
    verify special tokens, EOS placement, and the prompt/response boundary
    by eye before spending any GPU time.
    """
    for i in range(min(n, len(train_dataset))):
        print(f"===== example {i} =====")
        print(repr(train_dataset[i]["text"]))
        print()
