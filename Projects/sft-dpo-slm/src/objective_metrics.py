"""§6 — objective metrics, independent of the LLM judge's opinion.

- reward_accuracy: on the 200-pair preference holdout, the fraction of
  pairs where the DPO-tuned policy's implicit reward for "chosen" beats
  "rejected". A tuned model should clear 50%. Uses the standard DPO
  implicit reward: beta * log(pi_theta(y|x) / pi_ref(y|x)).
- mean_response_length: word count, base / SFT / DPO — the honest check
  on whether a win rate is just rewarding verbosity.
- format_adherence_rate: fraction of generations that stopped on EOS
  rather than running to max_new_tokens.
"""
import torch
import torch.nn.functional as F

from . import config as C


def _sequence_logprob(model, tokenizer, prompt, completion, device):
    full_text = prompt + completion
    prompt_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    full_ids = tokenizer(full_text, return_tensors="pt").input_ids.to(device)

    with torch.no_grad():
        logits = model(full_ids).logits

    # logits[i] predicts token i+1
    completion_start = prompt_ids.shape[1]
    shift_logits = logits[:, completion_start - 1 : -1, :]
    shift_labels = full_ids[:, completion_start:]

    log_probs = F.log_softmax(shift_logits.float(), dim=-1)
    token_log_probs = log_probs.gather(-1, shift_labels.unsqueeze(-1)).squeeze(-1)
    return token_log_probs.sum().item()


def reward_accuracy(dpo_model, tokenizer, pref_holdout, beta=None):
    """dpo_model must be a PeftModel with the DPO adapter active — reference
    logprobs are computed by disabling the adapter (same trick DPOTrainer
    uses with ref_model=None).
    """
    beta = beta or C.DPO_BETA
    device = next(dpo_model.parameters()).device
    correct = 0

    for pair in pref_holdout:
        prompt, chosen, rejected = pair["prompt"], pair["chosen"], pair["rejected"]

        policy_chosen = _sequence_logprob(dpo_model, tokenizer, prompt, chosen, device)
        policy_rejected = _sequence_logprob(dpo_model, tokenizer, prompt, rejected, device)

        with dpo_model.disable_adapter():
            ref_chosen = _sequence_logprob(dpo_model, tokenizer, prompt, chosen, device)
            ref_rejected = _sequence_logprob(dpo_model, tokenizer, prompt, rejected, device)

        reward_chosen = beta * (policy_chosen - ref_chosen)
        reward_rejected = beta * (policy_rejected - ref_rejected)

        if reward_chosen > reward_rejected:
            correct += 1

    return correct / len(pref_holdout)


def mean_response_length(generations):
    """generations: list of dicts with a "response" key (from generate_batch)."""
    lengths = [len(g["response"].split()) for g in generations]
    return sum(lengths) / len(lengths) if lengths else float("nan")


def format_adherence_rate(generations):
    hits = [g["hit_eos"] for g in generations]
    return sum(hits) / len(hits) if hits else float("nan")
