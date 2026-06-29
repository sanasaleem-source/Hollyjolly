"""
AI Production Studio — One-click setup script.
Downloads and installs all dependencies and tools, writes config.yaml, runs self-test.
Run with: python setup.py
"""
import os
import sys
import platform
import subprocess
import zipfile
import tarfile
import shutil
import json
import urllib.request
from pathlib import Path

SYSTEM = platform.system()  # Windows / Darwin / Linux

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
    print("  ✅ All pip dependencies installed")


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

    # Find the executable
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


def get_api_key():
    banner("Gemini API Key")
    print("  Get your free key at: https://aistudio.google.com/app/apikey")
    key = input("  Enter your Gemini API key: ").strip()
    return key


def write_config(godot_path, ffmpeg_path, api_key):
    banner("Writing config.yaml")
    config = f"""# AI Production Studio — Configuration
llm_provider: gemini
image_provider: imagen
gemini_api_key: {api_key}
gemini_model: gemini-1.5-pro

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


def self_test(api_key):
    banner("Running self-test")
    errors = []

    # Python deps
    for pkg in ["PyQt6", "pydantic", "yaml", "requests"]:
        try:
            __import__(pkg.lower().replace("pyqt6", "PyQt6"))
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} missing")
            errors.append(pkg)

    # Gemini connection
    if api_key and api_key != "GEMINI_API_KEY_HERE":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-pro")
            r = model.generate_content("Reply with just: OK")
            if "OK" in r.text:
                print("  ✅ Gemini API connected")
            else:
                print("  ⚠️  Gemini responded unexpectedly")
        except Exception as e:
            print(f"  ❌ Gemini API error: {e}")
            errors.append("Gemini API")
    else:
        print("  ⚠️  Skipping Gemini test — no API key")

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
    godot_path  = install_godot()
    ffmpeg_path = install_ffmpeg()
    api_key     = get_api_key()
    write_config(godot_path, ffmpeg_path, api_key)
    ok = self_test(api_key)

    banner("Setup Complete")
    if ok:
        print("  Run the studio with:")
        print("  python main.py")
    else:
        print("  Setup finished with warnings. Check above and fix before running.")


if __name__ == "__main__":
    main()
