# What fine-tuning taught — nodrix-llm

The goal was to learn fine-tuning end to end, not to ship the best assistant. Three
runs did that. This is what they established, with the evidence.

## The three runs

| run | base | data | key config | result |
|-----|------|------|-----------|--------|
| v1 | Qwen2.5-Coder-1.5B | 167 tr | 3 epochs, 63 steps | form fixed, facts not |
| v2 | Qwen2.5-Coder-7B | 183 tr (+20 downlink) | 3 epochs, 69 steps, eval attached | overfit past ~step 24; one symbol fixed |
| v3 | Qwen2.5-Coder-7B | 193 tr (+14 targeted) | 2 epochs, 50 steps | one disease cured, one refuted |

Adapters live in `~/.unsloth/studio/outputs/`. v3 = `Qwen_..._7B-Instruct_1784924723`.

## Loss lessons

- **Loss measures predictability, not competence.** Baseline perplexity on plain English
  (91) was *worse* than on boilerplate Arduino (3.4) — the code is more predictable, not
  better understood. Ranking texts by loss is close to noise.
- **Loss is only comparable on identical text.** v3's eval floor (1.83) looked lower than
  v2's (2.04), but the validation set had changed (20 → 22 examples), so the comparison is
  confounded. Trust the *shape* of a curve, not cross-run numbers.
- **The eval curve is the overfitting detector, and nothing else is.** v2: train fell
  1.79 → 1.20 while eval flatlined at ~2.04 and the train/eval gap widened to −0.85. Lower
  train loss bought zero generalization. Without the eval set you cannot see this — v1 had
  none and its "better" train loss meant nothing.
- **train_on_completions masks the prompt.** Studio does this by default; loss lands on
  assistant turns only. It was the main silent-failure risk and it was handled.

## The two-diseases framework

v2/v3 exposed two distinct failure modes that look identical (a wrong API) but need
different cures:

**Prior-conflict** — the model must abandon a structural habit. `NODRIX_WRITE("x") { }` is
a file-scope macro; the base model's prior insists on method calls, so it invented
`wasWrite()` / `valueAsBool()`. **Cured in v3** by 7 examples mapping the exact user
phrasing ("widget bound to variable X") to the macro, plus explicit "there is no
`addWidget`" corrections. Generalized to the held-out `led` prompt — fixed with
`pump`/`fan`/`speed`, never `led`.

**Minority-class / decision-against-default** — the model must *infer* a choice that
fights a dominant pattern. "Device sleeps → use `beginHTTP`+`poll`" lost to `begin`+`run`,
which dominates the whole corpus. **Not cured** by rebalancing 4:1 → 2.3:1; a house style
needs more pressure than that, or a sharper cue than an abstract inference.

Rule of thumb: **targeted data fixes phrasal mappings well and decisions-against-a-default
poorly.**

## Two phenomena worth naming

- **Over-application.** After learning `NODRIX_WRITE` strongly, v3 used it where it didn't
  belong — stuffing a deep-sleep loop inside a write handler. Strengthening a pattern has
  blast radius; you can over-move a propensity into neighboring contexts.
- **Residual hallucination floor.** v3 still invented `WAKEUP_RTD_DEEP`, mixed `ESP.deepSleep`
  (ESP8266) into an ESP32 sketch, and typo'd `NODRIX.send`. ~250 examples at 7B cannot
  reliably suppress specific invented facts, at any epoch count.

## The boundary, learned empirically

Fine-tuning reliably buys **form, voice, output-format routing, and crisply-cued
patterns**. It does not reliably buy **fact suppression or architectural decisions against
a dominant prior**. That residual floor is the seam where retrieval belongs: ground the
*facts* (the API surface, per-board specifics) in RAG, let the fine-tune own the *form*.
The project deliberately learned fine-tuning first; this is where the two meet.

## Governing principle

**Fine-tuning adjusts propensities; it cannot install capabilities.** Buy capability with
the base model (why Coder-7B, not a general 0.5B); spend the data on propensity. Every
result above is a corollary of this.
