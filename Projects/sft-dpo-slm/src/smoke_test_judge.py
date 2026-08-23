"""Day 2 — build the eval harness FIRST and smoke-test it before you have
anything real to judge. Generates two independently-sampled response sets
from the untuned base model and judges them against each other.

Expected result: roughly 50/50 with lots of ties. If you get 90/10, the
order-randomization in judge_pair is broken. If this crashes, better to
find out now than on Day 6.
"""
import json

from . import config as C
from .data import load_sft_splits
from .generate import generate_batch
from .judge import judge_pair, load_local_judge, summarize_results
from .model_utils import load_base_model, load_tokenizer


def main():
    tokenizer = load_tokenizer()
    _, eval_prompts = load_sft_splits(tokenizer)

    model = load_base_model()
    gens_a = generate_batch(model, tokenizer, eval_prompts)
    gens_b = generate_batch(model, tokenizer, eval_prompts)  # independent sampling, same model

    judge_model = judge_tokenizer = openai_client = None
    if C.JUDGE_BACKEND == "hf_local":
        judge_model, judge_tokenizer = load_local_judge()
    elif C.JUDGE_BACKEND == "openai":
        import openai

        openai_client = openai.OpenAI()

    results = []
    for prompt, ga, gb in zip(eval_prompts, gens_a, gens_b):
        r = judge_pair(
            prompt,
            ga["response"],
            gb["response"],
            backend=C.JUDGE_BACKEND,
            judge_model=judge_model,
            judge_tokenizer=judge_tokenizer,
            openai_client=openai_client,
        )
        results.append(r)

    summary = summarize_results(results, name_a="base_sample1", name_b="base_sample2")
    print(json.dumps(summary, indent=2))
    n_unparsed = sum(1 for r in results if not r["parsed_ok"])
    print(f"Unparseable judge responses (logged as ties): {n_unparsed}/{len(results)}")
    print("Sanity check: this should land close to 50/50 with a healthy number of ties.")


if __name__ == "__main__":
    main()
