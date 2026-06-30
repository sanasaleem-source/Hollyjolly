"""
AI Production Studio — One-click setup script.
Installs all dependencies and tools, lets the user choose Cloud or Local AI,
writes config.yaml, runs self-test.
Run with: python setup.py
"""
import os
import sys
import platform
import subprocess
import zipfile
import tarfile
import shutil
import urllib.request
from pathlib import Path

SYSTEM = platform.system()

GODOT_URLS = {
    "Windows": "https://github.com/godotengine/godot/releases/download/4.2.1-stable/Godot_v4.2.1-stable_win64.exe.zip",
    "Darwin":  "https://github.com/godotengine/godot/releases/download/4.2.1-stable/Godot_v4.2.1-stable_macos.universal.zip",
    "Linux":   "https://github.com/godotengine/godot/releases/download/4.2.1-stable/Godot_v4.2.1-stable_linux.x86_64.zip",
}

FFMPEG_URLS = {
    "Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "Darwin":  "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip",
    "Linux":   "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
}

ROOT = Path(__file__).parent
BIN  = ROOT / "bin"


def banner(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, **kwargs)


def download(url, dest):
    print(f"  Downloading {Path(dest).name}...")
    urllib.request.urlretrieve(url, dest)
    print(f"  ✅ Saved to {dest}")


def check_python():
    banner("Checking Python version")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        print(f"  ❌ Python 3.11+ required. You have {v.major}.{v.minor}")
        sys.exit(1)
    print(f"  ✅ Python {v.major}.{v.minor}.{v.micro}")


def install_pip_deps():
    banner("Installing Python dependencies")
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt"), "-q"])
    print("  ✅ All pip dependencies installed (this includes torch + transformers for local models)")


def install_godot():
    banner("Installing Godot 4")
    BIN.mkdir(exist_ok=True)
    url = GODOT_URLS.get(SYSTEM)
    if not url:
        print("  ⚠️  Unsupported OS — install Godot manually")
        return ""
    zip_path = BIN / "godot.zip"
    download(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(BIN / "godot_extracted")
    zip_path.unlink()
    for p in (BIN / "godot_extracted").rglob("*"):
        if "godot" in p.name.lower() and p.suffix in (".exe", "") and p.is_file():
            dest = BIN / ("godot.exe" if SYSTEM == "Windows" else "godot")
            shutil.copy2(p, dest)
            if SYSTEM != "Windows":
                dest.chmod(0o755)
            shutil.rmtree(BIN / "godot_extracted")
            print(f"  ✅ Godot installed: {dest}")
            return str(dest)
    print("  ⚠️  Could not locate Godot binary — install manually")
    return ""


def install_ffmpeg():
    banner("Installing FFmpeg")
    BIN.mkdir(exist_ok=True)
    url = FFMPEG_URLS.get(SYSTEM)
    if not url:
        print("  ⚠️  Unsupported OS — install FFmpeg manually")
        return ""
    archive = BIN / ("ffmpeg.zip" if "zip" in url else "ffmpeg.tar.xz")
    download(url, archive)
    if str(archive).endswith(".zip"):
        with zipfile.ZipFile(archive, "r") as z:
            z.extractall(BIN / "ffmpeg_extracted")
    else:
        with tarfile.open(archive) as t:
            t.extractall(BIN / "ffmpeg_extracted")
    archive.unlink()
    for p in (BIN / "ffmpeg_extracted").rglob("*"):
        if p.stem == "ffmpeg" and p.is_file():
            dest = BIN / ("ffmpeg.exe" if SYSTEM == "Windows" else "ffmpeg")
            shutil.copy2(p, dest)
            if SYSTEM != "Windows":
                dest.chmod(0o755)
            shutil.rmtree(BIN / "ffmpeg_extracted")
            print(f"  ✅ FFmpeg installed: {dest}")
            return str(dest)
    print("  ⚠️  Could not locate FFmpeg binary — install manually")
    return ""


def choose_model_setup():
    banner("Choose your AI model")
    print("  1) Cloud — Gemini via Google AI Studio (fast, needs API key + internet)")
    print("  2) Local — HuggingFace model (private, runs on your machine, needs disk/RAM)")
    choice = input("  Enter 1 or 2: ").strip()

    if choice == "2":
        print("\n  Browse models at huggingface.co/models?pipeline_tag=text-generation")
        repo_id = input("  Enter HuggingFace repo ID (e.g. Qwen/Qwen2.5-3B-Instruct): ").strip()
        gemini_key = input("  (Optional) Gemini API key for vision validation, or leave blank: ").strip()
        return {
            "text_provider": "huggingface",
            "hf_repo_id": repo_id,
            "gemini_api_key": gemini_key or "GEMINI_API_KEY_HERE",
        }
    else:
        print("\n  Get a free key at aistudio.google.com/app/apikey")
        key = input("  Enter your Gemini API key: ").strip()
        return {
            "text_provider": "gemini",
            "vision_provider": "gemini",
            "image_provider": "gemini",
            "gemini_api_key": key,
        }


def write_config(godot_path, ffmpeg_path, model_choice):
    banner("Writing config.yaml")
    config = f"""# AI Production Studio — Configuration
text_provider: {model_choice.get("text_provider", "gemini")}
vision_provider: {model_choice.get("vision_provider", "gemini")}
image_provider: {model_choice.get("image_provider", "gemini")}

gemini_api_key: {model_choice.get("gemini_api_key", "GEMINI_API_KEY_HERE")}
gemini_model: gemini-flash-latest
gemini_image_model: gemini-2.5-flash-image

hf_repo_id: {model_choice.get("hf_repo_id", "")}
hf_device: auto
hf_max_new_tokens: 1024

ollama_url: http://localhost:11434
ollama_model: llama3

godot_path: {godot_path or "godot"}
blender_path: blender
ffmpeg_path: {ffmpeg_path or "ffmpeg"}

storage_path: ./storage
max_repair_attempts: 3
render_timeout_seconds: 300
render_fps: 24
render_width: 1920
render_height: 1080
"""
    with open(ROOT / "config.yaml", "w") as f:
        f.write(config)
    print("  ✅ config.yaml written")


def self_test(model_choice):
    banner("Running self-test")
    errors = []

    for pkg in ["PyQt6", "pydantic", "yaml", "requests"]:
        try:
            __import__(pkg.lower().replace("pyqt6", "PyQt6"))
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} missing")
            errors.append(pkg)

    if model_choice.get("text_provider") == "gemini":
        key = model_choice.get("gemini_api_key", "")
        if key and key != "GEMINI_API_KEY_HERE":
            try:
                from google import genai
                client = genai.Client(api_key=key)
                r = client.models.generate_content(model="gemini-flash-latest", contents="Reply with just: OK")
                print("  ✅ Gemini API connected" if "OK" in r.text else "  ⚠️  Gemini responded unexpectedly")
            except Exception as e:
                print(f"  ❌ Gemini API error: {e}")
                errors.append("Gemini API")
        else:
            print("  ⚠️  No Gemini key provided")

    elif model_choice.get("llm_provider") == "huggingface":
        try:
            import transformers, torch
            print(f"  ✅ transformers {transformers.__version__}")
            print(f"  ✅ torch {torch.__version__} (CUDA available: {torch.cuda.is_available()})")
            repo_id = model_choice.get("hf_repo_id", "")
            if repo_id:
                print(f"  ℹ️  Model '{repo_id}' will download on first run (not pre-downloaded by setup)")
            else:
                print("  ⚠️  No HuggingFace repo ID provided")
        except ImportError as e:
            print(f"  ❌ Missing local model dependency: {e}")
            errors.append("transformers/torch")

    if errors:
        print(f"\n  ⚠️  {len(errors)} issue(s) found: {errors}")
    else:
        print("\n  ✅ All checks passed — ready to launch!")
    return len(errors) == 0


def main():
    banner("AI Production Studio — Setup")
    print(f"  System: {SYSTEM}  |  Python: {sys.version.split()[0]}")

    check_python()
    install_pip_deps()
    godot_path   = install_godot()
    ffmpeg_path  = install_ffmpeg()
    model_choice = choose_model_setup()
    write_config(godot_path, ffmpeg_path, model_choice)
    ok = self_test(model_choice)

    banner("Setup Complete")
    if ok:
        print("  Run the studio with:")
        print("  python main.py")
        if model_choice.get("llm_provider") == "huggingface":
            print("\n  Note: your chosen model will download the first time you run the app.")
    else:
        print("  Setup finished with warnings. Check above and fix before running.")


if __name__ == "__main__":
    main()
