# nodrix-llm

**Fine-tuning a small LLM into a build assistant for the [Nodrix](https://nodrix.live) ESP32/Arduino library — end to end, as a way to actually learn fine-tuning.**

The goal was never to ship the best assistant. It was to learn the craft — LoRA, data
curation, the training loop, reading loss curves, evaluation — by doing every step and
looking hard at what each one changed. This repo is the data pipeline, the eval harness,
and an honest write-up of what worked and what didn't.

**[▶ Try the live demo](https://huggingface.co/spaces/decoded-cipher/nodrix-build-assistant)** · **[📊 Findings](FINDINGS.md)** · **Models:** [v1 1.5B](https://huggingface.co/decoded-cipher/nodrix-coder-1.5b-lora-v1) · [v2 7B](https://huggingface.co/decoded-cipher/nodrix-coder-7b-lora-v2) · [v3 7B](https://huggingface.co/decoded-cipher/nodrix-coder-7b-lora-v3)

---

## The result, in one comparison

Same prompt, base model vs the v3 fine-tune (both Qwen2.5-Coder-7B):

> **Prompt:** How do I control a relay from the dashboard?

| Base Qwen2.5-Coder-7B | Fine-tuned (v3) |
|---|---|
| Generic prose about "set up a button in the dashboard," no real API. | ` ``cpp `<br>`NODRIX_WRITE("relay") {`<br>`  digitalWrite(RELAY_PIN, value.asBool());`<br>`}` |

The base model has never heard of Nodrix and invents plausible-looking APIs. The fine-tune
learned the real ones. Try both side by side in the [Space](https://huggingface.co/spaces/decoded-cipher/nodrix-build-assistant).

## What was learned (the interesting part)

Three LoRA runs (v1 → v3), each diagnosed against a held-out test set. The findings, in short:

- **Fine-tuning fixes *form*, not *facts*.** Very quickly the model learned to answer in the
  right voice, emit real C++, and route prose-vs-code by question type. Installing specific
  API facts was much harder and never fully reliable.
- **Two failure modes that look identical but need different cures.** A wrong API can come
  from a *prior-conflict* (the model's habit fights the target — cured with targeted
  phrasing data) or from *minority-class dominance* (a correct-but-rare pattern loses to a
  common one — not cured by mild rebalancing). Same symptom, different fix.
- **There's a floor.** ~250 examples at 7B can't suppress every invented fact — that residual
  is exactly where retrieval (RAG) belongs, and fine-tuning owns the form.

Full write-up with the loss curves and transcripts: **[FINDINGS.md](FINDINGS.md)**.

Governing principle throughout: **fine-tuning adjusts propensities; it cannot install
capabilities.** So buy capability with the base model (Qwen2.5-**Coder**, which already
writes embedded C++) and spend the small dataset on propensity (voice, the Nodrix API).

## The pipeline

**Data** — [`build.py`](build.py) assembles 246 chat examples from the Nodrix corpus:

| source | count |
|---|---|
| FAQ pairs (guide frontmatter) | 163 |
| curated code tasks (guide code blocks) | 24 |
| API Q&A (hand-written from `Nodrix.h`) | 20 |
| downlink examples (`NODRIX_WRITE`, `NodrixValue`, …) | 20 |
| failure-targeted examples (from observed v2 errors) | 14 |
| SDK sketches | 5 |

Split **193 train / 22 valid / 31 test**, stratified by kind with `random.seed(0)`.
Only the `seed_*.jsonl` files are hand-written; the splits regenerate byte-for-byte.
`test.jsonl` is sealed — never inspected during curation, so its number is honest.

**Training** — [Unsloth Studio](https://unsloth.ai/docs/new/studio), native on Apple Silicon
(MLX). LoRA r=16, α=16, all seven linear modules, seq 512, LR 2e-4, 2–3 epochs.
`chatml` format; loss masked to assistant turns only.

**Evaluation** — [`eval/compare_prompts.md`](eval/compare_prompts.md) holds the held-out
prompts, the real API surface, and a scoring rubric. The comparison harness is the Space's
Model Arena: base and fine-tuned loaded together, adapter toggled — same weights, two
behaviors.

## Reproduce

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python pyyaml
.venv/bin/python build.py          # regenerates data/{train,valid,test}.jsonl
```

Then upload `data/train.jsonl` + `data/valid.jsonl` to Unsloth Studio (`chatml`), or use
any LoRA trainer — the format is standard OpenAI-style `messages`.

## Layout

    build.py                       builds the dataset from the sibling Nodrix repos
    data/seed_*.jsonl              hand-written Q&A (API, guide code, downlink, targeted)
    data/{train,valid,test}.jsonl  generated splits, chatml
    eval/compare_prompts.md        base-vs-tuned prompts + scoring rubric
    space/                         the Gradio comparison app (deployed to HF Spaces)
    FINDINGS.md                    the retrospective — what three runs established

## Gotchas worth knowing

Two that cost real time and are easy to hit:

- **MLX-trained adapters don't load into `peft` as-is.** Unsloth Studio (Apple Silicon) saves
  LoRA as `…lora_a/lora_b` with transposed shapes; `peft`/`transformers` want
  `base_model.model.…lora_A.weight` and a real `LoraConfig`. Loaded raw, `peft` silently
  applies *nothing* — the giveaway is that greedy decoding with the adapter on vs off is
  byte-identical. Conversion (transpose + rename + config) is in the commit history.
- **An adapter that loads without erroring is not proof it's applied.** Always verify with
  greedy decoding, adapter toggled on/off.

## License

Code: MIT. Adapters inherit Apache-2.0 from the Qwen2.5-Coder base models.
