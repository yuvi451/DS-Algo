"""Day 6 — full three-way evaluation: base, SFT, SFT+DPO.

Runs three pairings through the judge (base vs SFT, SFT vs DPO, base vs
DPO), reports wins/(wins+losses) with ties separate, logs raw judgments,
and computes the §6 objective metrics (reward accuracy, mean response
length, format adherence).
"""
import json
import os

from . import config as C
from .data import load_dpo_splits, load_sft_splits
from .generate import generate_batch
from .judge import judge_pair, load_local_judge, summarize_results
from .model_utils import free_model, load_base_model, load_tokenizer, load_with_adapter
from .objective_metrics import format_adherence_rate, mean_response_length, reward_accuracy


def run_pairing(prompts, gens_a, gens_b, name_a, name_b, judge_kwargs):
    results = []
    for prompt, ga, gb in zip(prompts, gens_a, gens_b):
        r = judge_pair(prompt, ga["response"], gb["response"], **judge_kwargs)
        r["prompt"] = prompt
        results.append(r)
    summary = summarize_results(results, name_a=name_a, name_b=name_b)
    return summary, results


def main():
    os.makedirs(C.EVAL_DIR, exist_ok=True)
    tokenizer = load_tokenizer()
    _, eval_prompts = load_sft_splits(tokenizer)
    _, pref_holdout = load_dpo_splits(tokenizer)

    print("Generating from base...")
    base_model = load_base_model()
    base_gens = generate_batch(base_model, tokenizer, eval_prompts)
    free_model(base_model)

    print("Generating from SFT...")
    sft_model = load_with_adapter(C.SFT_ADAPTER_DIR)
    sft_gens = generate_batch(sft_model, tokenizer, eval_prompts)
    free_model(sft_model)

    print("Generating from SFT+DPO...")
    dpo_model = load_with_adapter(C.DPO_ADAPTER_DIR)
    dpo_gens = generate_batch(dpo_model, tokenizer, eval_prompts)

    print("Computing reward accuracy on the preference holdout...")
    r_acc = reward_accuracy(dpo_model, tokenizer, pref_holdout)
    free_model(dpo_model)

    print("Loading judge...")
    judge_model = judge_tokenizer = openai_client = None
    if C.JUDGE_BACKEND == "hf_local":
        judge_model, judge_tokenizer = load_local_judge()
    elif C.JUDGE_BACKEND == "openai":
        import openai

        openai_client = openai.OpenAI()

    judge_kwargs = dict(
        backend=C.JUDGE_BACKEND,
        judge_model=judge_model,
        judge_tokenizer=judge_tokenizer,
        openai_client=openai_client,
    )

    print("Judging base vs SFT...")
    base_vs_sft, base_vs_sft_raw = run_pairing(eval_prompts, base_gens, sft_gens, "base", "sft", judge_kwargs)
    print("Judging SFT vs DPO...")
    sft_vs_dpo, sft_vs_dpo_raw = run_pairing(eval_prompts, sft_gens, dpo_gens, "sft", "dpo", judge_kwargs)
    print("Judging base vs DPO...")
    base_vs_dpo, base_vs_dpo_raw = run_pairing(eval_prompts, base_gens, dpo_gens, "base", "dpo", judge_kwargs)

    objective = {
        "reward_accuracy_pref_holdout": r_acc,
        "mean_response_length": {
            "base": mean_response_length(base_gens),
            "sft": mean_response_length(sft_gens),
            "dpo": mean_response_length(dpo_gens),
        },
        "format_adherence_rate": {
            "base": format_adherence_rate(base_gens),
            "sft": format_adherence_rate(sft_gens),
            "dpo": format_adherence_rate(dpo_gens),
        },
    }

    report = {
        "win_rates": {
            "base_vs_sft": base_vs_sft,
            "sft_vs_dpo": sft_vs_dpo,
            "base_vs_dpo": base_vs_dpo,
        },
        "objective_metrics": objective,
    }

    print(json.dumps(report, indent=2))

    with open(f"{C.EVAL_DIR}/three_way_summary.json", "w") as f:
        json.dump(report, f, indent=2)
    with open(f"{C.EVAL_DIR}/three_way_raw_judgments.json", "w") as f:
        json.dump(
            {
                "base_vs_sft": base_vs_sft_raw,
                "sft_vs_dpo": sft_vs_dpo_raw,
                "base_vs_dpo": base_vs_dpo_raw,
            },
            f,
            indent=2,
        )
    print(f"Results written to {C.EVAL_DIR}/three_way_summary.json and three_way_raw_judgments.json")


if __name__ == "__main__":
    main()
