"""Generation helper shared by the sanity check, base-vs-SFT eval, and the
three-way eval. Reports whether generation stopped on EOS or ran to
max_new_tokens, which feeds the format-adherence metric (§6).
"""
import torch

from . import config as C


@torch.no_grad()
def generate_batch(model, tokenizer, prompts, max_new_tokens=None, temperature=None, top_p=None):
    """prompts: list[str] of raw instructions (not yet chat-templated).

    Returns a list of dicts: {"prompt", "response", "hit_eos"}.
    """
    max_new_tokens = max_new_tokens or C.GEN_MAX_NEW_TOKENS
    temperature = temperature if temperature is not None else C.GEN_TEMPERATURE
    top_p = top_p if top_p is not None else C.GEN_TOP_P

    model.eval()
    device = next(model.parameters()).device
    results = []

    for prompt in prompts:
        messages = [{"role": "user", "content": prompt}]
        templated = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(templated, return_tensors="pt").to(device)
        input_len = inputs["input_ids"].shape[1]

        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )

        new_tokens = output_ids[0][input_len:]
        response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        hit_eos = bool(
            len(new_tokens) < max_new_tokens
            and tokenizer.eos_token_id in new_tokens.tolist()
        )

        results.append({"prompt": prompt, "response": response, "hit_eos": hit_eos})

    return results
