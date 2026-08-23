"""Day 4 — run the base-vs-SFT eval as soon as the SFT adapter exists, not
later. Base -> SFT should show a large, obvious win rate; if it doesn't,
something upstream (chat template, data formatting) is wrong and you want
to know that with five days of runway left, not on Day 6.
"""
import json

from . import config as C
from .data import load_sft_splits
from .generate import generate_batch
from .judge import judge_pair, load_local_judge, summarize_results
from .model_utils import free_model, load_base_model, load_tokenizer, load_with_adapter


def main():
    tokenizer = load_tokenizer()
    _, eval_prompts = load_sft_splits(tokenizer)

    print("Generating from base model...")
    base_model = load_base_model()
    base_gens = generate_batch(base_model, tokenizer, eval_prompts)
    free_model(base_model)

    print("Generating from SFT model...")
    sft_model = load_with_adapter(C.SFT_ADAPTER_DIR)
    sft_gens = generate_batch(sft_model, tokenizer, eval_prompts)
    free_model(sft_model)

    print("Judging base vs SFT...")
    judge_model = judge_tokenizer = openai_client = None
    if C.JUDGE_BACKEND == "hf_local":
        judge_model, judge_tokenizer = load_local_judge()
    elif C.JUDGE_BACKEND == "openai":
        import openai

        openai_client = openai.OpenAI()

    results = []
    for prompt, base_g, sft_g in zip(eval_prompts, base_gens, sft_gens):
        r = judge_pair(
            prompt,
            base_g["response"],
            sft_g["response"],
            backend=C.JUDGE_BACKEND,
            judge_model=judge_model,
            judge_tokenizer=judge_tokenizer,
            openai_client=openai_client,
        )
        r["prompt"] = prompt
        results.append(r)

    summary = summarize_results(results, name_a="base", name_b="sft")
    print(json.dumps(summary, indent=2))

    import os

    os.makedirs(C.EVAL_DIR, exist_ok=True)
    with open(f"{C.EVAL_DIR}/base_vs_sft.json", "w") as f:
        json.dump({"summary": summary, "raw": results}, f, indent=2)
    print(f"Raw judgments logged to {C.EVAL_DIR}/base_vs_sft.json")


if __name__ == "__main__":
    main()
