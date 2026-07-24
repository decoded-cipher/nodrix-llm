# Base vs fine-tuned — Model Arena prompts

All five are from `data/test.jsonl` (held out, never trained on).

Set this system prompt on **both** sides, identical to training:

```
You are the Nodrix build assistant. You help ESP32 and Arduino developers build
projects with the Nodrix library. Use only real Nodrix APIs.
```

## Prompts

1. Write a Nodrix sketch: Control the on-board LED from a Nodrix toggle widget bound to the variable "led".
2. How do I connect an ESP32 with a BME280 to the cloud over HTTPS with the certificate pinned?
3. How do I build a battery sensor that sleeps between readings?
4. How often should I call Nodrix.send()?
5. Is nodrix suitable for commercial or industrial projects like Ubidots?

## What each probes

| # | probes | correct answer uses |
|---|---|---|
| 1 | downlink — the weakest area in the corpus | `NODRIX_WRITE("led")`, `value.asBool()` |
| 2 | uplink + TLS pinning | `setCACert()` before `begin()`, `run()` in `loop()` |
| 3 | HTTP vs WebSocket mode | `beginHTTP()`, `flush()`, `poll()` — **not** `run()` |
| 4 | API idiom | `millis()` gate around `send()` |
| 5 | voice, no code | opinionated prose, guide tone |

## The real API surface

Anything outside this list is a hallucination.

```
Nodrix.addAP  begin  beginHTTP  run  poll  send  flush  event
              onConnect  onDisconnect  connected
              setInsecure  setCACert  setFingerprint  setDebug
NODRIX_WRITE("var") { ... value ... }
NodrixValue: asBool asInt asLong asFloat asDouble asString isNull
```

## Scoring

Per answer, mark:

- **invented API** — anything not in the list above. `Nodrix.connect()`, `.publish()`,
  `.subscribe()`, `.on()` are the likely inventions; the base model reaches for MQTT shapes.
- **mode error** — `run()` paired with `beginHTTP()`, or `poll()` with `begin()`.
- **downlink shape** — did it use the `NODRIX_WRITE` macro, or invent a callback registration?
- **emitted code** — did it produce a sketch at all when one was asked for?
- **voice** — reads like the guides, or like generic IoT filler?

Expect the base to be fluent, confident and wrong on 1–4. That confident wrongness is the
baseline the fine-tune has to beat.
