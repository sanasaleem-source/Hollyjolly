# 🎬 AI Production Studio

A desktop application that takes a story prompt and turns it into a fully produced video — planned, cast, rendered, validated, and exported, with almost no manual work. It runs entirely on your own machine. No servers, no subscriptions, no hosting. Once installed, it's yours.

This started after watching a video essay from the YouTube channel **Slow English** and thinking: *can this be better, and can it be automated end to end?* That question became this project.

**Special thanks to Ayyan**, who gave the original idea its scope and direction before any of this was built.

---

## What it actually does

You type a story idea. From there, the studio:

1. **Plans it** — breaks your idea into individual shots, each with its own camera angle, lighting, characters, and action (the *Director*)
2. **Remembers everything** — tracks every character's appearance, clothing, injuries, and history across the entire project so nothing is ever inconsistent shot to shot (the *World State*)
3. **Builds the assets** — generates character art, props, and environments, reusing what already exists instead of regenerating it every time (the *Asset Manager*)
4. **Assembles the scene** — positions cameras, characters, and lighting into a real 3D scene (the *Scene Composer*, using OpenUSD)
5. **Renders it** — spawns Godot 4 headless to render actual frames
6. **Checks its own work** — four separate validators check character consistency, story continuity, visual style, and basic physics
7. **Fixes what's broken** — if something fails validation, only that specific problem gets repaired, not the whole shot
8. **Exports it** — assembles the final video with FFmpeg, plus a professional timeline (OpenTimelineIO) you can import into Premiere, DaVinci Resolve, or Final Cut

You watch all of this happen in a two-panel interface: one side shows your prompt, your asset library, and the current state of every character. The other side is a CapCut-style timeline showing every shot as it gets built, with failed shots clearly flagged so you know exactly where to step in.

---

## Why this is different

Most AI video tools work like this: prompt → generate → hope it stays consistent.

This works like this: prompt → plan → remember → build → assemble → generate → validate → repair → export.

The AI models are not the product here — they're interchangeable specialists that plug into the pipeline. The software itself, with its memory of every character and every decision, is what you actually own.

---

## Model flexibility — bring your own, or run locally

You are never locked into one AI provider, and you don't need to pay for anything to use this.

There are **three independent model slots**, each configurable separately:

| Slot | Job | Options |
|---|---|---|
| **Text** | Story planning, continuity, repair | Gemini (cloud) · Any HuggingFace model (local) · Ollama (local) |
| **Vision** | Checks rendered frames against the script | Gemini (cloud) · HuggingFace (local, limited) · Ollama / LLaVA (local) |
| **Image** | Generates character, object, and environment art | Imagen (cloud) · Any Stable Diffusion model via HuggingFace (local) |

Mix and match freely. Use Gemini for everything, or run a local HuggingFace model for text and stay fully offline, or use cloud for images but local for text — any combination works. Each slot can even use a **different API key** if you want to separate billing or rate limits.

No API key? No problem. Paste any HuggingFace repo ID into the local model field and the app will download and run it on your own machine — no internet required after that point, no cost, full privacy.

---

## Requirements

- **Python 3.11 or newer**
- **Windows, macOS, or Linux**
- Roughly 5–10 GB free disk space if using local models (more for larger models)
- A GPU is recommended for local models but not required — CPU mode works, just slower

---

## Installation

### Option 1 — One-click setup (recommended)

```bash
git clone https://github.com/sanasaleem-source/Hollyjolly.git
cd Hollyjolly
python setup.py
```

`setup.py` will:
- Check your Python version
- Install every Python dependency automatically
- Download and install Godot 4 and FFmpeg into a local `bin/` folder
- Ask you to choose Cloud (Gemini) or Local (HuggingFace) for your AI model
- Write your `config.yaml` automatically
- Run a self-test to confirm everything is working

### Option 2 — Manual setup

```bash
git clone https://github.com/sanasaleem-source/Hollyjolly.git
cd Hollyjolly
pip install -r requirements.txt --break-system-packages
```

Then manually:
- Install [Godot 4](https://godotengine.org/download) and make sure it's on your PATH, or set `godot_path` in `config.yaml`
- Install [FFmpeg](https://ffmpeg.org/download.html) the same way
- (Optional) Install [Blender](https://www.blender.org/download/) if you want advanced 3D asset rigging
- Copy `config.yaml` and fill in your model choice — see Configuration below

---

## Running it

```bash
python main.py
```

The first time you launch, a setup screen will ask you to configure your Text, Vision, and Image models if you skipped that step during `setup.py`. After that, it remembers your settings — just run `python main.py` from then on.

You can change your model configuration at any time from **Settings → Change AI Model** inside the app.

### Building a standalone .exe (Windows)

If you want a single installable application instead of running from source:

```bash
build.bat
```

This uses PyInstaller to bundle everything — including FFmpeg — into `dist/AIProductionStudio/`. An Inno Setup script (`installer.iss`) is also included if you want to produce a proper Windows installer `.exe`.

On macOS/Linux, use `build.sh` instead.

---

## Configuration

All settings live in `config.yaml`, generated automatically by `setup.py`. Key sections:

```yaml
text_provider: gemini          # gemini | huggingface | ollama
gemini_api_key: YOUR_KEY_HERE
hf_repo_id: ""                 # used if text_provider: huggingface

vision_provider: gemini
vision_gemini_api_key: ""      # optional — separate key for vision only

image_provider: imagen         # imagen | diffusers
hf_image_repo_id: ""           # used if image_provider: diffusers

godot_path: godot
blender_path: blender
ffmpeg_path: ./bin/ffmpeg

max_repair_attempts: 3
render_fps: 24
```

Get a free Gemini API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

Browse local models at [huggingface.co/models](https://huggingface.co/models).

---

## How the interface works

**Left panel:**
- Type your story prompt, or target a specific shot if something needs fixing
- Browse every asset you've generated, organized by character/object/environment and version
- See the current state of every character — clothing, injuries, last seen

**Right panel:**
- A horizontal timeline of every shot, shown as placeholders until rendered
- Completed shots show their thumbnail; failed shots are outlined in red so you immediately know what needs attention
- Click any shot to see its frames, the prompt that generated it, and its validation results
- A preview player for the final assembled video, with an export button

---

## Project structure

```
src/
  core/            — Director, World State, Asset Manager, Orchestrator, Validators, Repair Engine
  providers/        — All AI provider integrations (Gemini, HuggingFace, Ollama, Imagen, Diffusers)
  integrations/     — Godot, Blender, FFmpeg, OpenUSD, OpenTimelineIO bridges
  ui/               — PyQt6 desktop interface
storage/            — Your projects, generated assets, and local model cache (not committed to git)
godot/              — The headless rendering script Godot runs
tests/              — Unit tests for World State and core logic
```

---

## Status

This is an actively developed personal project, not a finished commercial product. Core systems — story planning, World State memory, asset versioning, validation, and repair — are built and tested. Rendering quality depends entirely on the AI models you connect, and is expected to improve as those models do.

---

## Credits

Inspired by a video from **Slow English** on YouTube, and built after wondering whether the idea behind it could be pushed further into something fully automated.

Original idea and scope shaped with **Ayyan** — thank you for getting this started.
