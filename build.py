import json, random, re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT.parent / "nodrix-internal/promo/src/content"
SDK = ROOT.parent / "nodrix-sdk"
OUT = ROOT / "data"

SYSTEM = (
    "You are the Nodrix build assistant. You help ESP32 and Arduino developers "
    "build projects with the Nodrix library. Use only real Nodrix APIs."
)


def pair(kind, user, assistant):
    return kind, [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user.strip()},
        {"role": "assistant", "content": assistant.strip()},
    ]


def from_faqs():
    for f in sorted(CONTENT.rglob("*.md")):
        m = re.match(r"^---\n(.*?)\n---\n", f.read_text(), re.S)
        fm = yaml.safe_load(m.group(1)) if m else {}
        for q in (fm or {}).get("faqs") or []:
            if q.get("q") and q.get("a"):
                yield pair("faq", q["q"], q["a"])


def from_examples():
    for f in sorted(SDK.glob("examples/*/*.ino")):
        code = f.read_text()
        desc = " ".join(l.lstrip("/ ").strip() for l in code.splitlines() if l.startswith("//"))
        body = "\n".join(l for l in code.splitlines() if not l.startswith("//"))
        yield pair("sketch", f"Write a Nodrix sketch: {desc}", f"```cpp\n{body.strip()}\n```")


def from_seed(name, kind):
    for d in map(json.loads, (OUT / name).read_text().splitlines()):
        yield pair(kind, d["q"], d["a"])


def write(name, rows):
    (OUT / name).write_text("".join(json.dumps({"messages": m}) + "\n" for _, m in rows))
    print(f"  {name:<12} {len(rows):>4}")


def main():
    rows = [
        *from_faqs(),
        *from_examples(),
        *from_seed("seed_guide_code.jsonl", "guide_code"),
        *from_seed("seed_api.jsonl", "api"),
        *from_seed("seed_downlink.jsonl", "downlink"),
        *from_seed("seed_targeted.jsonl", "targeted"),
    ]
    by_kind = {}
    for kind, m in rows:
        by_kind.setdefault(kind, []).append((kind, m))

    print("collected:")
    for k, v in by_kind.items():
        print(f"  {k:<12} {len(v):>4}")

    random.seed(0)
    test, rest = [], []
    for v in by_kind.values():
        random.shuffle(v)
        n = max(2, round(len(v) * 0.12))
        test += v[:n]
        rest += v[n:]
    random.shuffle(rest)
    n_valid = round(len(rest) * 0.1)

    print("split:")
    write("test.jsonl", test)
    write("valid.jsonl", rest[:n_valid])
    write("train.jsonl", rest[n_valid:])


if __name__ == "__main__":
    main()
