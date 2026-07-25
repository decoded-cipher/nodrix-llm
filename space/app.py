import spaces
import torch
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

SYSTEM = (
    "You are the Nodrix build assistant. You help ESP32 and Arduino developers "
    "build projects with the Nodrix library. Use only real Nodrix APIs."
)

BASE_7B = "Qwen/Qwen2.5-Coder-7B-Instruct"
BASE_15B = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

tok7 = AutoTokenizer.from_pretrained(BASE_7B)
m7 = AutoModelForCausalLM.from_pretrained(BASE_7B, torch_dtype=torch.bfloat16).to("cuda")
m7 = PeftModel.from_pretrained(m7, "decoded-cipher/nodrix-coder-7b-lora-v2", adapter_name="v2")
m7.load_adapter("decoded-cipher/nodrix-coder-7b-lora-v3", adapter_name="v3")

_m15 = None


def base15():
    global _m15
    if _m15 is None:
        tok = AutoTokenizer.from_pretrained(BASE_15B)
        model = AutoModelForCausalLM.from_pretrained(BASE_15B, torch_dtype=torch.bfloat16).to("cuda")
        model = PeftModel.from_pretrained(model, "decoded-cipher/nodrix-coder-1.5b-lora-v1", adapter_name="v1")
        _m15 = (model, tok)
    return _m15


MODELS = {
    "Base 7B (no fine-tune)": ("7b", None),
    "v2 · 7B": ("7b", "v2"),
    "v3 · 7B  ★": ("7b", "v3"),
    "Base 1.5B (no fine-tune)": ("15b", None),
    "v1 · 1.5B": ("15b", "v1"),
}
CHOICES = list(MODELS)


@spaces.GPU(duration=120)
def run(choice, question):
    which, adapter = MODELS[choice]
    model, tok = (m7, tok7) if which == "7b" else base15()

    ids = tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}],
        add_generation_prompt=True, return_tensors="pt",
    ).to("cuda")

    def gen():
        out = model.generate(ids, max_new_tokens=400, do_sample=True,
                             temperature=0.7, top_p=0.9, pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)

    if adapter is None:
        with model.disable_adapter():
            return gen()
    model.set_adapter(adapter)
    return gen()


def compare(question, left, right):
    return run(left, question), run(right, question)


EXAMPLES = [
    "How do I control a relay from the dashboard?",
    "Write a Nodrix sketch: dim an LED from a slider widget bound to \"brightness\".",
    "How do I build a battery sensor that sleeps between readings?",
    "Is nodrix suitable for commercial or industrial projects?",
]

with gr.Blocks(title="Nodrix build assistant — base vs fine-tuned") as demo:
    gr.Markdown(
        "# Nodrix build assistant — base vs fine-tuned\n"
        "Three LoRA fine-tunes of Qwen2.5-Coder for the Nodrix ESP32/Arduino library, "
        "side by side with the base model. Pick a model per column and ask the same "
        "question. `★` v3 is the best run. Free ZeroGPU — the first call cold-starts."
    )
    question = gr.Textbox(label="Question", lines=2, value=EXAMPLES[0])
    with gr.Row():
        left = gr.Dropdown(CHOICES, value="Base 7B (no fine-tune)", label="Left model")
        right = gr.Dropdown(CHOICES, value="v3 · 7B  ★", label="Right model")
    go = gr.Button("Compare", variant="primary")
    with gr.Row():
        out_l = gr.Markdown()
        out_r = gr.Markdown()
    gr.Examples(EXAMPLES, inputs=question)
    go.click(compare, [question, left, right], [out_l, out_r])

demo.queue().launch()
