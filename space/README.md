---
title: Nodrix Build Assistant
emoji: 🔌
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.9.1
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Base vs fine-tuned Qwen2.5-Coder for Nodrix
models:
  - decoded-cipher/nodrix-coder-1.5b-lora-v1
  - decoded-cipher/nodrix-coder-7b-lora-v2
  - decoded-cipher/nodrix-coder-7b-lora-v3
---

Compare the base Qwen2.5-Coder against three LoRA fine-tunes for the Nodrix
ESP32/Arduino library. Runs on free ZeroGPU.
