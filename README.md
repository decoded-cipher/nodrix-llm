# nodrix-llm

Fine-tune a small LLM into a Nodrix build assistant. This repo holds the data pipeline
and eval harness; training runs in Unsloth Studio.

## Layout

    build.py                      builds the dataset from sibling repos
    data/seed_api.jsonl           curated Q&A written from Nodrix.h
    data/seed_guide_code.jsonl    curated code tasks from guide code blocks
    data/{train,valid,test}.jsonl generated — chatml, upload straight to Studio
    eval/compare_prompts.md       base-vs-tuned prompts + scoring rubric

## Sources

- `../nodrix-internal/promo/src/content` — 34 guides, 163 frontmatter FAQ pairs
- `../nodrix-sdk` — `Nodrix.h`, 5 `.ino` examples

## Build

    uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python pyyaml
    .venv/bin/python build.py

212 examples — 163 FAQ pairs, 24 guide code blocks, 20 API pairs, 5 SDK sketches —
split 167 train / 18 valid / 27 test, stratified by kind, `random.seed(0)`.

`seed_*.jsonl` are `{q, a}` and hand-written — the only irreplaceable files here.
The splits are `{messages}` and regenerate byte-for-byte from `build.py`.

`valid.jsonl` is read repeatedly during training to decide when to stop, so it
degrades as you tune against it. `test.jsonl` is read once, at the end, and is the
only honest number. **Do not inspect `test.jsonl` while curating.**

## Training

Unsloth Studio, native on Apple Silicon (`unsloth studio -p 8888`).
Dataset format `chatml`. Studio sets `train_on_completions: true` by default,
so loss lands on assistant turns only.

Verified config: r 16, alpha 16, dropout 0, all seven target modules,
seq 512, batch 2 x accum 4, LR 2e-4, linear schedule, 3 epochs = 63 steps.

## Status

Smoke run on Qwen2.5-Coder-1.5B-Instruct: loss 2.99 -> 1.84 over 3 epochs, 167s.
Fine-tune fixed form (real C++, correct `begin`/`run`/`send`, prose-vs-code routing)
but not facts — it still invents `Nodrix.var()`, `Nodrix_SSL.h`, and mixes
`begin()` with `poll()`. No eval set was attached, so overfitting is unmeasured.

Next: fill the downlink gap (`NODRIX_WRITE`, `NodrixValue`, `onConnect`, `addAP`,
`setCACert`), attach the eval set, move to the 7B.
