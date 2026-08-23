"""LLM-judge pipeline (project breakdown §2 Day 2 / §5).

Two backends:
  - "hf_local": loads a separate, stronger instruct model in 4-bit
    (config.JUDGE_MODEL_HF) purely for judging. Call `load_local_judge()`
    once, after you've freed the policy model(s) from VRAM.
  - "openai": calls an OpenAI-compatible chat completions API. Requires
    OPENAI_API_KEY as a Kaggle secret / env var — never hardcode it.

Judging protocol, per the breakdown: present both responses blind and
order-randomized per prompt (never always A-first), request structured
JSON, and be defensive about parsing — a judge will occasionally return
markdown-fenced JSON or trailing prose, and a bare json.loads() will kill
a 40-prompt run at prompt 31.
"""
import json
import random
import re

from . import config as C

JUDGE_PROMPT_TEMPLATE = """You are comparing two responses to the same instruction. Decide which response
is more helpful, accurate, and appropriately concise. A longer response is not
automatically better — penalize padding, restatement, and unnecessary preamble.
Ignore which response is listed first; the order is randomized.

Instruction: {prompt}

Response A: {response_a}

Response B: {response_b}

Respond with JSON only, no markdown fences, no other text:
{{"winner": "A" | "B" | "tie", "reason": "one sentence"}}
"""


def _parse_judge_json(raw_text):
    """Defensive parse: strip markdown fences / leading-trailing prose,
    retry once, and fall back to a tie (logged as unparseable) rather than
    crashing the eval loop.
    """
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def load_local_judge():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )
    tokenizer = AutoTokenizer.from_pretrained(C.JUDGE_MODEL_HF)
    model = AutoModelForCausalLM.from_pretrained(
        C.JUDGE_MODEL_HF,
        quantization_config=bnb_config,
        device_map="auto",
        attn_implementation="sdpa",
    )
    model.eval()
    return model, tokenizer


def _call_local_judge(model, tokenizer, prompt_text):
    import torch

    messages = [{"role": "user", "content": prompt_text}]
    templated = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(templated, return_tensors="pt").to(next(model.parameters()).device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )
    new_tokens = output_ids[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def _call_openai_judge(client, prompt_text):
    resp = client.chat.completions.create(
        model=C.JUDGE_MODEL_OPENAI,
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.0,
    )
    return resp.choices[0].message.content


def judge_pair(prompt, response_a, response_b, backend=None, judge_model=None, judge_tokenizer=None, openai_client=None, rng=None):
    """Judges one (prompt, response_a, response_b) triple with randomized
    A/B order. Returns {"winner": "a"|"b"|"tie", "reason": str, "parsed_ok": bool}
    where "a"/"b" refer to the ORIGINAL (pre-randomization) arguments, not
    the randomized slots shown to the judge.
    """
    backend = backend or C.JUDGE_BACKEND
    rng = rng or random

    swapped = rng.random() < 0.5
    shown_a, shown_b = (response_b, response_a) if swapped else (response_a, response_b)

    prompt_text = JUDGE_PROMPT_TEMPLATE.format(prompt=prompt, response_a=shown_a, response_b=shown_b)

    for attempt in range(2):
        if backend == "hf_local":
            raw = _call_local_judge(judge_model, judge_tokenizer, prompt_text)
        elif backend == "openai":
            raw = _call_openai_judge(openai_client, prompt_text)
        else:
            raise ValueError(f"unknown JUDGE_BACKEND: {backend}")

        parsed = _parse_judge_json(raw)
        if parsed is not None and "winner" in parsed:
            break
    else:
        parsed = None

    if parsed is None:
        return {"winner": "tie", "reason": "unparseable judge output", "parsed_ok": False, "raw": raw}

    shown_winner = str(parsed.get("winner", "tie")).strip().upper()
    if shown_winner == "A":
        winner = "b" if swapped else "a"
    elif shown_winner == "B":
        winner = "a" if swapped else "b"
    else:
        winner = "tie"

    return {"winner": winner, "reason": parsed.get("reason", ""), "parsed_ok": True, "raw": raw}


def summarize_results(results, name_a="A", name_b="B"):
    wins_a = sum(1 for r in results if r["winner"] == "a")
    wins_b = sum(1 for r in results if r["winner"] == "b")
    ties = sum(1 for r in results if r["winner"] == "tie")
    total = len(results)
    decisive = wins_a + wins_b
    win_rate_a = wins_a / decisive if decisive else float("nan")
    return {
        f"{name_a}_wins": wins_a,
        f"{name_b}_wins": wins_b,
        "ties": ties,
        "total": total,
        f"{name_a}_win_rate_excl_ties": win_rate_a,
    }
