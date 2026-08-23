# Instruction-Tuned SLM: SFT + DPO

Takes a raw pretrained model that generates fluent text but doesn't reliably
follow instructions, and turns it into a small instruction-tuned assistant
in two stages:

1. **SFT** — teach it the *shape* of a good response (instruction in, helpful answer out)
2. **DPO** — teach it *which* of two responses a human would prefer

...then measures the improvement with numbers: **base vs. SFT vs. SFT+DPO**,
scored by an LLM judge plus an objective, judge-independent metric.

**Preference axis targeted:** conciseness — DPO is expected to reduce mean
response length / padding while holding or improving judge win rate (see
`src/config.py::PREFERENCE_AXIS`). Fill in the "Results" section below once
you've run this on Kaggle.

## Stack

PyTorch, Hugging Face `transformers`, `peft`, `trl`, `datasets`, `bitsandbytes`.

**Base model:** `Qwen/Qwen2.5-1.5B`
**Compute:** Kaggle T4 x1 (16GB VRAM), free tier — 30 GPU-hrs/week quota

## Pinned versions

```
transformers==4.46.*
trl==0.12.*
peft==0.13.*
datasets==3.0.*
accelerate==1.0.*
bitsandbytes==0.44.*
```

TRL's API has churned repeatedly across minor versions — `DPOTrainer`
moved its config into `DPOConfig`, `tokenizer=` became `processing_class=`.
Don't bump these without re-checking the trainer signatures.

## T4-specific constraints

| Thing | Value | Why |
|---|---|---|
| Mixed precision | `fp16=True` | T4 is Turing — no bf16 support. |
| FlashAttention 2 | Not available | Requires Ampere+. Uses `attn_implementation="sdpa"` instead. |
| Gradient checkpointing | On for SFT/DPO | Trades ~20% speed for headroom; paired with `use_reentrant=False`. |

## Project layout

```
sft-dpo-slm/
├── requirements.txt          # pinned deps
├── src/
│   ├── config.py             # every hyperparameter and dataset/model choice, in one place
│   ├── data.py                # SFT/DPO dataset loading, held-out splits (carved out BEFORE subsampling), chat-template formatting
│   ├── model_utils.py          # T4-safe model loading (fp16, sdpa)
│   ├── generate.py             # generation helper, tracks EOS-termination for format adherence
│   ├── judge.py                # LLM-judge pipeline: prompt template, order randomization, defensive JSON parsing
│   ├── smoke_test_judge.py       # Day 2: base-vs-base judge smoke test — expect ~50/50
│   ├── train_sft.py             # Day 3: LoRA SFT
│   ├── sanity_check.py           # Day 3: manual eyeball check of the SFT adapter
│   ├── eval_base_vs_sft.py        # Day 4: bank the base->SFT win rate early
│   ├── train_dpo.py              # Day 5: LoRA DPO, ref_model=None (adapter-disable trick)
│   ├── eval_three_way.py          # Day 6: base vs SFT vs SFT+DPO, + objective metrics
│   └── objective_metrics.py        # §6: reward accuracy, mean length, format adherence
├── eval/
│   └── judge_prompt.txt         # the judge prompt template, standalone for reference
└── notebooks/
    └── kaggle_sft_dpo_pipeline.ipynb   # <-- single self-contained notebook to upload to Kaggle
```

## Running on Kaggle

Upload `notebooks/kaggle_sft_dpo_pipeline.ipynb` directly — it's
self-contained (no dependency on cloning this repo) and runs the full
pipeline end to end: setup → data → eval harness → SFT → sanity check →
base-vs-SFT eval → DPO → three-way eval → objective metrics.

Before running:
1. Enable the **GPU T4 x1** accelerator on the notebook.
2. Add a Kaggle secret named `HF_TOKEN` (your Hugging Face write token) so
   the notebook can push LoRA adapters after each stage — Kaggle sessions
   die, adapters are ~50MB, don't rely on `/kaggle/working` alone.
3. Set `HF_USERNAME` and `JUDGE_BACKEND` in the config cell. Default judge
   backend is `hf_local` (loads `Qwen/Qwen2.5-7B-Instruct` in 4-bit purely
   for judging, after the policy models are freed from VRAM) — no external
   API key required. Set `JUDGE_BACKEND="openai"` and add an `OPENAI_API_KEY`
   secret instead if you'd rather use an API judge.

## Running locally / as scripts

Each `src/*.py` module is also a standalone script (mirrors the notebook
cells 1:1, useful for local dev, code review, or a CI smoke test on CPU-only
config validation):

```bash
pip install -r requirements.txt
huggingface-cli login   # or export HF_TOKEN
python -m src.smoke_test_judge
python -m src.train_sft
python -m src.sanity_check
python -m src.eval_base_vs_sft
python -m src.train_dpo
python -m src.eval_three_way
```

## Hyperparameters

**LoRA:** `r=16, lora_alpha=32, lora_dropout=0.05`, targeting
`q_proj, k_proj, v_proj, o_proj`.

**SFT:** `learning_rate=2e-4, per_device_train_batch_size=4,
gradient_accumulation_steps=4, num_train_epochs=2, fp16=True,
max_seq_length=512, warmup_ratio=0.03, lr_scheduler_type=cosine`.

**DPO:** `beta=0.1, learning_rate=5e-6, per_device_train_batch_size=2,
gradient_accumulation_steps=4, num_train_epochs=1, fp16=True,
max_length=1024, max_prompt_length=512, ref_model=None` (LoRA adapter-disable
trick — no second copy of the model needed for the reference pass).

## Datasets

| Purpose | Dataset | Size used | Notes |
|---|---|---|---|
| SFT | `tatsu-lab/alpaca` | ~2,500 examples | random shuffled subset, empty-response rows filtered |
| DPO | `Intel/orca_dpo_pairs` | ~1,500 pairs | `prompt`/`chosen`/`rejected` columns |
| Eval prompts | held-out slice of the SFT dataset | 40 | carved out *before* subsampling — no leakage |
| Preference holdout | held-out slice of the DPO dataset | 200 pairs | for the reward-accuracy metric |

## Judge protocol

Both responses are shown **blind and order-randomized per prompt** (never
always A-first — this is the position-bias fix), structured JSON is
requested, and the prompt explicitly states that conciseness counts. See
`eval/judge_prompt.txt` / `src/judge.py::JUDGE_PROMPT_TEMPLATE`. Judge
output is parsed defensively (markdown fences and trailing prose stripped,
one retry, unparseable output logged as a tie rather than crashing the run).

## Objective metrics (§6)

An LLM judge is one subjective instrument — paired with numbers that don't
depend on another model's opinion:

- **Reward accuracy** on the 200-pair preference holdout: fraction of pairs
  where the DPO policy's implicit reward (`beta * log(pi_theta/pi_ref)`)
  ranks `chosen` above `rejected`. A tuned model should clear 50%.
- **Mean response length** (base / SFT / DPO) — the honest check on whether
  a win rate is just rewarding verbosity.
- **Format adherence rate** — fraction of generations that terminate on EOS
  rather than running to `max_new_tokens`.

## Results

*(Fill in after running `notebooks/kaggle_sft_dpo_pipeline.ipynb` on Kaggle
— this repo ships the pipeline, not fabricated numbers.)*

| Pairing | Wins | Losses | Ties | Win rate (excl. ties) |
|---|---|---|---|---|
| base vs. SFT | | | | |
| SFT vs. DPO | | | | |
| base vs. DPO | | | | |

| Metric | base | SFT | SFT+DPO |
|---|---|---|---|
| Mean response length (words) | | | |
| Format adherence rate | | | |

Reward accuracy on preference holdout: `__%`

2–3 side-by-side example outputs (base vs. SFT vs. DPO): _add after running_.

Qualitative note on what DPO changed (tone / verbosity / refusal behavior): _add after running_.

## Common pitfalls (read before debugging blind)

- **`bf16=True` on a T4.** Turing has no bf16. Use `fp16=True`.
- **FlashAttention 2 install failures.** Ampere+ only — use `attn_implementation="sdpa"`.
- **Chat template mismatch between training and inference.** The #1 cause
  of "my SFT model outputs garbage." Check this before touching hyperparameters.
- **DPO makes things worse.** Usually the preference dataset's "chosen" isn't
  a strict improvement over "rejected" *for your SFT model's current
  behavior*, or `beta` is too low (try 0.1–0.3). Don't chase this past one
  retry — a null DPO result is a finding to write up honestly, not a failed
  project.
- **DPO OOM.** Less likely with LoRA + `ref_model=None`. If it happens:
  `per_device_train_batch_size=1`, raise `gradient_accumulation_steps`, drop
  `max_length` to 768, or load 4-bit for this stage only.
- **Judge bias toward longer answers.** Handled in the judge prompt, plus
  the mean-length metric as a cross-check.
- **Kaggle session death mid-run.** Adapters are pushed to the Hub at every
  stage checkpoint, not just at the end.

## Interview prep

Be able to answer these without notes:

- Write the DPO loss. What is `beta` controlling, and what happens as it → 0 and → ∞?
- Why does DPO need a reference model at all? What breaks without it?
- Why DPO instead of PPO/RLHF? What did DPO give up in exchange for dropping the reward model?
- Why does LoRA let you skip a second copy of the model for the reference pass?
- Where does this evaluation remain vulnerable to bias, even with randomized order?

## Deliverables checklist

- [x] Training scripts (SFT + DPO) and pinned `requirements.txt`
- [x] Eval script + judge prompt template
- [x] Self-contained Kaggle notebook
- [ ] LoRA adapter weights pushed to HF Hub (produced by running the notebook)
- [ ] Raw logged judgments (produced by running the notebook, written to `eval/`)
- [ ] Results filled into the README above
- [ ] 2–3 side-by-side example outputs
- [ ] Qualitative note on what DPO changed
