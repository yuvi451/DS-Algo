"""Central config for the SFT+DPO project. Import this everywhere instead of
re-declaring magic numbers so the notebook and the scripts can never drift
apart on a hyperparameter.
"""
import os

# ---------------------------------------------------------------------------
# Preference axis (decide this before you start — see project breakdown §1)
# ---------------------------------------------------------------------------
PREFERENCE_AXIS = "conciseness"  # what DPO is supposed to change; used in the judge prompt

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
BASE_MODEL = "Qwen/Qwen2.5-1.5B"
JUDGE_BACKEND = os.environ.get("JUDGE_BACKEND", "hf_local")  # "hf_local" or "openai"
JUDGE_MODEL_HF = "Qwen/Qwen2.5-7B-Instruct"  # local judge, loaded 4-bit, only during eval
JUDGE_MODEL_OPENAI = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
SFT_DATASET = "tatsu-lab/alpaca"
DPO_DATASET = "Intel/orca_dpo_pairs"

SFT_TRAIN_SIZE = 2500
DPO_TRAIN_SIZE = 1500
EVAL_PROMPTS_SIZE = 40          # held out from SFT dataset, never trained on
PREF_HOLDOUT_SIZE = 200         # held out from DPO dataset, for reward-accuracy metric

SEED = 42

# ---------------------------------------------------------------------------
# LoRA
# ---------------------------------------------------------------------------
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]

# ---------------------------------------------------------------------------
# SFT hyperparameters (Day 3)
# ---------------------------------------------------------------------------
SFT_LEARNING_RATE = 2e-4
SFT_TRAIN_BATCH_SIZE = 4
SFT_GRAD_ACCUM_STEPS = 4
SFT_EPOCHS = 2
SFT_MAX_SEQ_LENGTH = 512
SFT_WARMUP_RATIO = 0.03
SFT_LR_SCHEDULER = "cosine"

# ---------------------------------------------------------------------------
# DPO hyperparameters (Day 5)
# ---------------------------------------------------------------------------
DPO_BETA = 0.1
DPO_LEARNING_RATE = 5e-6
DPO_TRAIN_BATCH_SIZE = 2
DPO_GRAD_ACCUM_STEPS = 4
DPO_EPOCHS = 1
DPO_MAX_LENGTH = 1024
DPO_MAX_PROMPT_LENGTH = 512

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
GEN_MAX_NEW_TOKENS = 256
GEN_TEMPERATURE = 0.7
GEN_TOP_P = 0.9

# ---------------------------------------------------------------------------
# HF Hub push targets — override via env vars, never hardcode a token.
# ---------------------------------------------------------------------------
HF_USERNAME = os.environ.get("HF_USERNAME", "your-hf-username")
SFT_ADAPTER_REPO = f"{HF_USERNAME}/qwen2.5-1.5b-sft-alpaca-lora"
DPO_ADAPTER_REPO = f"{HF_USERNAME}/qwen2.5-1.5b-sft-dpo-orca-lora"

# ---------------------------------------------------------------------------
# Local paths
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.environ.get("SFT_DPO_OUTPUT_DIR", "/kaggle/working" if os.path.isdir("/kaggle/working") else "./outputs")
SFT_ADAPTER_DIR = f"{OUTPUT_DIR}/sft_adapter"
DPO_ADAPTER_DIR = f"{OUTPUT_DIR}/dpo_adapter"
EVAL_DIR = f"{OUTPUT_DIR}/eval"
