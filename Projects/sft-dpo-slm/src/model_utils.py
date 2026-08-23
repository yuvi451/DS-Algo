"""Shared model-loading helpers. Centralized so every script uses the same
T4-safe settings (fp16, sdpa attention) — see project breakdown §2 table.
"""
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_tokenizer():
    from . import config as C

    tokenizer = AutoTokenizer.from_pretrained(C.BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def load_base_model():
    from . import config as C

    model = AutoModelForCausalLM.from_pretrained(
        C.BASE_MODEL,
        torch_dtype=torch.float16,
        attn_implementation="sdpa",
        device_map="auto",
    )
    return model


def load_with_adapter(adapter_path):
    """Base model + a LoRA adapter, for inference (sanity check / eval)."""
    base = load_base_model()
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()
    return model


def free_model(model):
    import gc

    del model
    gc.collect()
    torch.cuda.empty_cache()
