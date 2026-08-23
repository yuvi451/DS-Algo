"""Day 3 (later) — manual sanity check of the SFT adapter on a handful of
hand-picked prompts. If output is broken (garbage, repetition, parroting
the prompt back), the cause is almost always a chat-template mismatch
between training and inference, not a bad learning rate (§4, §7) — check
that first.
"""
from . import config as C
from .generate import generate_batch
from .model_utils import load_tokenizer, load_with_adapter

HAND_PICKED_PROMPTS = [
    "Explain what a hash map is to someone who has never programmed before.",
    "Write a short poem about the ocean.",
    "What are three tips for staying focused while studying?",
    "Translate 'good morning' into French, Spanish, and German.",
    "Summarize the plot of Romeo and Juliet in two sentences.",
    "List the first five prime numbers.",
    "Give me a recipe idea using chicken, rice, and broccoli.",
    "What is the capital of Australia?",
    "Write a one-line joke about programmers.",
    "Explain the difference between a list and a tuple in Python.",
]


def main():
    tokenizer = load_tokenizer()
    model = load_with_adapter(C.SFT_ADAPTER_DIR)

    results = generate_batch(model, tokenizer, HAND_PICKED_PROMPTS)

    for r in results:
        print("=" * 80)
        print("PROMPT:  ", r["prompt"])
        print("RESPONSE:", r["response"])
        print("hit_eos:", r["hit_eos"])

    n_eos = sum(r["hit_eos"] for r in results)
    print(f"\n{n_eos}/{len(results)} generations stopped on EOS (rest ran to max_new_tokens).")
    print("Eyeball check: on-topic? no prompt-parroting? no repetition loops?")


if __name__ == "__main__":
    main()
