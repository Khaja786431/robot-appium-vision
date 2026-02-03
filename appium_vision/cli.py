import os
import sys
import subprocess
import venv


def _venv_python(venv_dir):
    """Return python executable path inside venv."""
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def setup():
    """
    Creates a virtual environment and installs robot-appium-vision into it.
    """
    venv_dir = ".venv"

    if not os.path.exists(venv_dir):
        print("📦 Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    else:
        print("ℹ️ Virtual environment already exists")

    python = _venv_python(venv_dir)

    print("📥 Installing robot-appium-vision into virtual environment...")
    subprocess.check_call([
        python, "-m", "pip", "install", "--upgrade", "pip"
    ])
    subprocess.check_call([
        python, "-m", "pip", "install", "robot-appium-vision"
    ])

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    if os.name == "nt":
        print(r"  Activate venv: .\.venv\Scripts\Activate.ps1")
    else:
        print("  Activate venv: source .venv/bin/activate")


def main():
    if len(sys.argv) < 2:
        print("Usage: appium-vision setup")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "setup":
        setup()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup")
