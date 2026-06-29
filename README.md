# Hollyjolly — AI Production Studio

A desktop application that takes a story prompt and produces a complete video. You describe the story; the pipeline handles planning, asset generation, scene assembly, validation, repair, and final export — automatically.

**The AI models are not the product. The pipeline is.**

---

## What It Does

Most AI video tools give you isolated generations with no memory between shots. Hollyjolly runs a full production pipeline with persistent world state, so every shot knows what happened in every previous shot. Characters stay consistent. Objects remember who owns them and what condition they're in. Continuity is tracked automatically.

You interact through a two-panel desktop UI. The left panel gives you an asset browser, a prompt area, a world state viewer, and a live task queue. The right panel is a CapCut-style timeline showing every shot as a thumbnail — grey placeholders for ungenerated shots, rendered frames when ready, red outlines on anything that failed validation. Click any shot to inspect its frames, its prompt, and which asset versions were used. Click regenerate to fix it.

---

## Architecture

### Five Tools (All Process-Managed)

| Tool | Role |
|------|------|
| **Godot 4** | Scene runtime, cameras, physics, animation, rendering — spawned headless, renders frames, exits |
| **Blender** | 3D asset creation, rigging, hair, cloth simulation — spawned headless for asset work |
| **OpenUSD** | Universal scene format shared between all tools (`usd-core` Python library) |
| **FFmpeg** | Final frame assembly and video encoding |
| **OpenTimelineIO** | Timeline interchange and EDL export for Premiere / DaVinci Resolve |

### Four Core Systems

**Director** — Receives your story prompt, breaks it into shots (camera angle, duration, lighting, character positions), and produces a validated JSON production plan. Reads World State before every decision.

**World State Engine** — The permanent memory of the project. Tracks characters (appearance, clothing, injuries, history per shot), objects (owner, condition, location, version), world conditions (time, weather, lighting, damage), and per-shot records. Every system reads from and writes to it.

**Asset Manager** — Checks if an asset exists before generating anything. Reuses existing assets wherever possible. Creates versioned assets when something changes (e.g. `john_v1` → `john_v2` with broken arm). Maintains a fast lookup index.

**Orchestrator** — Sits between the Director and everything else. Manages the task queue, handles failures, decides retry vs repair vs skip.

```
Director → Task List
             ↓
         Orchestrator
             ↓
Asset Manager → Scene Composer → Godot Render → Validators
             ↓
         Repair Engine (on failure) → Re-validate
             ↓
         Flag shot in UI if repair fails (red outline) → Continue
```

### Validation & Repair

Four validators, each checking one thing:
- **CharacterValidator** — appearance and clothing consistency across shots
- **StoryValidator** — checks for contradictions with earlier events
- **StyleValidator** — color and tone consistency
- **PhysicsValidator** — basic sanity (no floating, no clipping)

The Repair Engine receives an exact failure report, fixes only the specific problem, and re-runs only the relevant validator. Every repair attempt is logged in World State.

### AI Provider Abstraction

All models connect through a single abstract interface. Swap providers by changing one line in `config.yaml` — no code changes required.

```
BaseLLM          → generate(prompt) → str
BaseImageModel   → generate(prompt, style) → image
BaseVisionModel  → analyze(image, question) → str
```

V1 default: Gemini (LLM + Vision) via Google AI Studio, Gemini Imagen for image generation, with Ollama as a local fallback. Claude, GPT-4, and other providers drop in without changing anything else.

---

## Prerequisites

Before running the app, you need:

- **Python 3.11+**
- **Godot 4** — [download here](https://godotengine.org/download) — must be accessible as `godot` in PATH, or set the path in `config.yaml`
- **Blender 3.6+** — [download here](https://www.blender.org/download/) — same PATH requirement
- **FFmpeg** — the setup script bundles a copy into `./bin/ffmpeg`, but you can also install system-wide
- **A Gemini API key** — get one free at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## Setup

**Clone the repo:**
```bash
git clone https://github.com/sanasaleem-source/Hollyjolly.git
cd Hollyjolly
```

**Create and activate a virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Run the setup script** (detects Godot/Blender/FFmpeg, creates storage directories, initializes the SQLite database):
```bash
python setup_studio.py
```

**Configure your API key:**

Copy `.env.example` to `.env` and fill in your Gemini key:
```bash
cp .env.example .env
```
Then edit `.env`:
```
GEMINI_API_KEY="your-key-here"
```

Alternatively, set it directly in `config.yaml`:
```yaml
gemini_api_key: your-key-here
```

---

## Running

**Quick start (uses the run scripts):**
```bash
# Windows
run.bat

# macOS / Linux
./run.sh
```

**Or directly:**
```bash
python main.py
```

---

## Configuration

`config.yaml` controls everything:

```yaml
# AI provider — options: gemini | ollama
llm_provider: gemini
image_provider: imagen

# Gemini
gemini_api_key: YOUR_KEY_HERE
gemini_model: gemini-1.5-pro

# Local fallback (Ollama — install from ollama.ai)
ollama_url: http://localhost:11434
ollama_model: llama3

# External tool paths (setup_studio.py fills these in automatically)
godot_path: godot
blender_path: blender
ffmpeg_path: ./bin/ffmpeg

# Storage
storage_path: ./storage

# Pipeline settings
max_repair_attempts: 3
render_timeout_seconds: 300
render_fps: 24
render_width: 1920
render_height: 1080
```

To switch to a local Ollama model, change `llm_provider: ollama` and make sure Ollama is running at the configured URL. No other changes needed.

---

## Storage Layout

```
storage/
  database/       # SQLite — World State (characters, objects, shots, world)
  projects/       # One folder per project
  assets/
    characters/
      john/
        v1/       # appearance.json, image.png, blender_rig.blend
        v2/       # variation (e.g. broken arm)
    objects/
    environments/
  cache/          # Temporary render output
```

---

## Building a Distributable Executable

The repo includes a PyInstaller spec file and build scripts for packaging the app as a standalone executable:

```bash
# Windows
build.bat

# macOS / Linux
./build.sh
```

On Windows, `installer.iss` is an Inno Setup script for generating a proper installer. FFmpeg is bundled automatically.

---

## Running Tests

```bash
pytest tests/
```

---

## Project Structure

```
src/
  core/
    director/         # Prompt → shots → task list
    world_state/      # CharacterDB, ObjectDB, WorldDB, ShotDB
    asset_manager/    # Asset lookup, versioning, index
    orchestrator/     # Task queue, process management, failure handling
    scene_composer/   # Shot builder, USD scene writer
    validator/        # Character, story, style, physics validators
    repair/           # Repair engine
  providers/
    base_llm.py       # Abstract interfaces
    gemini_provider.py
    ollama_provider.py
    imagen_provider.py
  integrations/
    godot/            # Headless render bridge + frame collector
    blender/          # Headless asset bridge
    usd/              # OpenUSD read/write
    otio/             # OpenTimelineIO export
    ffmpeg/           # Frame assembly + encoding
  ui/
    main_window.py    # Two-panel layout
    left_panel/       # Asset browser, prompt panel, world viewer
    right_panel/      # Timeline, shot viewer, preview player
godot/                # Godot 4 project (GDScript scene runner)
storage/              # Data, assets, cache (gitignored contents)
tests/
config.yaml
main.py
requirements.txt
```

---

## Roadmap

- [x] Phase 1–3: Project structure, World State, AI provider layer
- [x] Phase 4–5: Director, Orchestrator, Process Manager
- [x] Phase 6–7: Asset Manager, Scene Composer
- [x] Phase 8: Godot headless integration
- [x] Phase 9: Validators and Repair Engine
- [x] Phase 10: PyQt6 two-panel UI
- [x] Phase 11: FFmpeg export, OpenTimelineIO EDL
- [x] Phase 12: PyInstaller packaging, Inno Setup installer
- [ ] Additional AI provider support (Claude, GPT-4)
- [ ] Audio pipeline
- [ ] Web-based project sharing

---

## License

This project is not affiliated with or endorsed by Google. Gemini API access requires your own key and is subject to Google's terms of service.
